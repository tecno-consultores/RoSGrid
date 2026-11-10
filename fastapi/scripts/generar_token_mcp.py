#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)
"""
Script de Generación de Tokens de Servicio de Larga Duración (Bearer JWT) para Agentes IA MCP.
Permite emitir tokens estables para Hermes Agent y Claude Desktop asociados al rol SERVICE_ACCOUNT,
registrando la sesión activa en KeyDB sin requerir interacción web ni códigos 2FA efímeros.
"""

import argparse
import asyncio
import json
import secrets
import sys
import time
import uuid

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings
from src.core.crypto import hash_password
from src.models.core import SystemRoleEnum, Tenant, User
from src.redis_layer.client import get_redis_client

DEFAULT_MCP_CIDRS: list[str] = [
    "127.0.0.1/32",
    "172.16.0.0/12",
    "10.0.0.0/8",
    "192.168.0.0/16",
    "::1/128",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generar Token Bearer JWT de Larga Duración para Agentes IA MCP (SERVICE_ACCOUNT)"
    )
    parser.add_argument("--username", help="Nombre de usuario del Service Account (ej: mcp-agent)", required=True)
    parser.add_argument("--tenant-slug", help="Slug de la organización (opcional)", default=None)
    parser.add_argument("--expiry-days", help="Días de validez del token (default: 365 días)", type=int, default=365)
    parser.add_argument(
        "--allowed-cidrs",
        help="Lista de CIDRs separados por coma autorizados para el SERVICE_ACCOUNT",
        default=None,
    )
    parser.add_argument(
        "--raw-token",
        help="Imprimir únicamente la cadena del token JWT en stdout (ideal para pipelines y scripts)",
        action="store_true",
    )
    return parser.parse_args()


async def _resolve_or_provision_service_account(
    session: AsyncSession,
    username: str,
    tenant_slug: str | None,
    allowed_cidrs: str | None,
) -> tuple[User, Tenant]:
    cidrs_list = (
        [c.strip() for c in allowed_cidrs.split(",") if c.strip()]
        if allowed_cidrs
        else list(DEFAULT_MCP_CIDRS)
    )

    stmt = select(User).where(User.username == username)
    user = (await session.execute(stmt)).scalar_one_or_none()

    if user:
        tenant = (await session.execute(select(Tenant).where(Tenant.id == user.tenant_id))).scalar_one_or_none()
        if not tenant:
            print(f"[ERROR] Organización asociada a '{username}' no encontrada.", file=sys.stderr)
            sys.exit(1)
        if tenant_slug and tenant.slug != tenant_slug:
            print(f"[ERROR] El usuario pertenece al tenant '{tenant.slug}', no a '{tenant_slug}'.", file=sys.stderr)
            sys.exit(1)

        if user.role != SystemRoleEnum.SERVICE_ACCOUNT:
            svc_username = f"{username}_mcp"
            print(
                f"[INFO] El usuario '{username}' tiene rol '{user.role.value}'. "
                f"Resolviendo cuenta SERVICE_ACCOUNT dedicada ('{svc_username}') para Zero-Trust MCP...",
                file=sys.stderr,
            )
            svc_stmt = select(User).where(
                User.tenant_id == tenant.id,
                User.username == svc_username,
            )
            svc_user = (await session.execute(svc_stmt)).scalar_one_or_none()
            if not svc_user:
                svc_user = User(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    username=svc_username,
                    email=f"{svc_username}@{tenant.slug}.local",
                    full_name=f"MCP Service Account ({svc_username})",
                    password_hash=hash_password(secrets.token_urlsafe(24)),
                    role=SystemRoleEnum.SERVICE_ACCOUNT,
                    is_active=True,
                    is_locked=False,
                    failed_login_attempts=0,
                    totp_enabled=False,
                    has_all_routers_access=True,
                    allowed_cidr_list=cidrs_list,
                )
                session.add(svc_user)
                await session.commit()
                await session.refresh(svc_user)
            user = svc_user
    else:
        if tenant_slug:
            tenant = (await session.execute(select(Tenant).where(Tenant.slug == tenant_slug))).scalar_one_or_none()
        else:
            tenant = (await session.execute(select(Tenant).limit(1))).scalar_one_or_none()

        if not tenant:
            print(
                f"[ERROR] No se encontró la organización '{tenant_slug or 'principal'}' para aprovisionar '{username}'.",
                file=sys.stderr,
            )
            sys.exit(1)

        print(
            f"[INFO] Aprovisionando cuenta SERVICE_ACCOUNT '{username}' en organización '{tenant.slug}'...",
            file=sys.stderr,
        )
        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            username=username,
            email=f"{username}@{tenant.slug}.local",
            full_name=f"MCP Service Account ({username})",
            password_hash=hash_password(secrets.token_urlsafe(24)),
            role=SystemRoleEnum.SERVICE_ACCOUNT,
            is_active=True,
            is_locked=False,
            failed_login_attempts=0,
            totp_enabled=False,
            has_all_routers_access=True,
            allowed_cidr_list=cidrs_list,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    if not user.allowed_cidr_list or allowed_cidrs is not None:
        user.allowed_cidr_list = cidrs_list
        await session.commit()
        await session.refresh(user)

    return user, tenant


async def generate_mcp_token(
    session: AsyncSession,
    username: str,
    tenant_slug: str | None,
    expiry_days: int,
    allowed_cidrs: str | None = None,
) -> tuple[str, str, str, str]:
    user, tenant = await _resolve_or_provision_service_account(
        session=session,
        username=username,
        tenant_slug=tenant_slug,
        allowed_cidrs=allowed_cidrs,
    )

    # 4. Generar identificador de sesión y registrar en KeyDB
    session_id = str(uuid.uuid4())
    redis = get_redis_client()
    sess_key = f"rg:{user.tenant_id}:sess:{session_id}"
    now = int(time.time())
    ttl_seconds = expiry_days * 86400

    allowed_ip = (
        user.allowed_cidr_list[0] if (user.allowed_cidr_list and len(user.allowed_cidr_list) > 0) else "127.0.0.1"
    )

    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
    active_sess_key = f"rg:{user.tenant_id}:active_sessions"
    user_sess_key = f"rg:{user.tenant_id}:user_sessions:{user.id}"

    mapping = {
        "session_id": session_id,
        "user_id": str(user.id),
        "username": user.username,
        "full_name": user.full_name or user.username,
        "role": user.role.value,
        "tenant_id": str(user.tenant_id),
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "ip_address": allowed_ip,
        "ip": allowed_ip,
        "user_agent": "RoSGrid-MCP-Daemon/1.0",
        "is_service_account": "true",
        "issued_by_username": "CLI (Terminal)",
        "allowed_cidr_list": json.dumps(user.allowed_cidr_list),
    }
    pipe = redis.pipeline()
    pipe.hset(sess_key, mapping=mapping)  # type: ignore[arg-type]
    pipe.expire(sess_key, ttl_seconds)
    pipe.set(f"rg:sess_idx:{session_id}", str(user.tenant_id), ex=ttl_seconds)
    pipe.zadd(active_sess_key, {session_id: float(now)})
    pipe.sadd(user_sess_key, session_id)
    pipe.expire(user_sess_key, ttl_seconds)
    await pipe.execute()

    # 5. Emitir JWT de larga duración
    payload = {
        "sub": str(user.id),
        "tid": str(user.tenant_id),
        "tslug": tenant.slug,
        "sid": session_id,
        "rol": user.role.value,
        "scope": "mcp_only",
        "preferred_username": user.username,
        "all_r": user.has_all_routers_access,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    token = jwt.encode(payload, settings.ROSGRID_JWT_SECRET_KEY, algorithm="HS256")
    return token, tenant.slug, user.role.value, session_id


async def main() -> None:
    args = parse_args()
    engine = create_async_engine(settings.ROSGRID_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        token, tslug, role, sid = await generate_mcp_token(
            session=session,
            username=args.username,
            tenant_slug=args.tenant_slug,
            expiry_days=args.expiry_days,
            allowed_cidrs=args.allowed_cidrs,
        )

        if args.raw_token:
            print(token)
            return

        print("==============================================================================")
        print("      🤖 Token de Servicio MCP Generado Exitosamente para Agente IA          ")
        print("==============================================================================")
        print(f"  • Usuario (SERVICE_ACCOUNT): {args.username}")
        print(f"  • Organización (Tenant):     {tslug}")
        print(f"  • Rol Validado:              {role}")
        print(f"  • ID de Sesión en KeyDB:     {sid}")
        print(f"  • Vigencia:                  {args.expiry_days} días")
        print("------------------------------------------------------------------------------")
        print("Cabecera HTTP requerida para invocar POST /api/v1/mcp:")
        print(f"Authorization: Bearer {token}")
        print("------------------------------------------------------------------------------")
        print("Ejemplo de configuración en Claude Desktop (claude_desktop_config.json):")
        print('  "rosgrid": {')
        print('    "command": "npx",')
        print('    "args": ["-y", "@modelcontextprotocol/server-fetch", "http://localhost:8000/api/v1/mcp"],')
        print('    "env": {')
        print(f'      "AUTHORIZATION": "Bearer {token}"')
        print("    }")
        print("  }")
        print("==============================================================================")


if __name__ == "__main__":
    asyncio.run(main())
