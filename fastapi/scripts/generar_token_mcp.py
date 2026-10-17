#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
"""
Script de Generación de Tokens de Servicio de Larga Duración (Bearer JWT) para Agentes IA MCP.
Permite emitir tokens estables para Hermes Agent y Claude Desktop asociados al rol SERVICE_ACCOUNT,
registrando la sesión activa en KeyDB sin requerir interacción web ni códigos 2FA efímeros.
"""

import argparse
import asyncio
import sys
import time
import uuid

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings
from src.models.core import SystemRoleEnum, Tenant, User
from src.redis_layer.client import get_redis_client


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generar Token Bearer JWT de Larga Duración para Agentes IA MCP (SERVICE_ACCOUNT)"
    )
    parser.add_argument("--username", help="Nombre de usuario del Service Account (ej: mcp-agent)", required=True)
    parser.add_argument("--tenant-slug", help="Slug de la organización (opcional)", default=None)
    parser.add_argument("--expiry-days", help="Días de validez del token (default: 365 días)", type=int, default=365)
    return parser.parse_args()


async def generate_mcp_token(
    session: AsyncSession, username: str, tenant_slug: str | None, expiry_days: int
) -> tuple[str, str, str, str]:
    # 1. Buscar usuario
    stmt = select(User).where(User.username == username)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        print(f"[ERROR] No se encontró el usuario '{username}' en la base de datos.", file=sys.stderr)
        sys.exit(1)

    # 2. Obtener Tenant
    res_t = await session.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = res_t.scalar_one_or_none()
    if not tenant:
        print(f"[ERROR] Organización asociada a '{username}' no encontrada.", file=sys.stderr)
        sys.exit(1)

    if tenant_slug and tenant.slug != tenant_slug:
        print(f"[ERROR] El usuario pertenece al tenant '{tenant.slug}', no a '{tenant_slug}'.", file=sys.stderr)
        sys.exit(1)

    # 3. Advertencia si no es SERVICE_ACCOUNT
    if user.role != SystemRoleEnum.SERVICE_ACCOUNT:
        print(f"[AVISO] El usuario '{username}' tiene rol '{user.role.value}', no 'SERVICE_ACCOUNT'.")
        print("El endpoint MCP /api/v1/mcp rechazará llamadas si el token no pertenece a SERVICE_ACCOUNT.")

    # 4. Generar identificador de sesión y registrar en KeyDB
    session_id = str(uuid.uuid4())
    redis = get_redis_client()
    sess_key = f"rg:{user.tenant_id}:sess:{session_id}"
    now = int(time.time())
    ttl_seconds = expiry_days * 86400

    allowed_ip = (
        user.allowed_cidr_list[0] if (user.allowed_cidr_list and len(user.allowed_cidr_list) > 0) else "127.0.0.1"
    )

    mapping = {
        "user_id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role": user.role.value,
        "created_at": str(now),
        "ip": allowed_ip,
        "user_agent": "RoSGrid-MCP-Daemon/1.0",
        "is_service_account": "true",
    }
    await redis.hset(sess_key, mapping=mapping)
    await redis.expire(sess_key, ttl_seconds)

    # 5. Emitir JWT de larga duración
    payload = {
        "sub": str(user.id),
        "tid": str(user.tenant_id),
        "tslug": tenant.slug,
        "sid": session_id,
        "rol": user.role.value,
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
        )

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
