#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
"""
Script de Semilla (Seeder) y Creación del Super Administrador Inicial de RoSGrid.
Permite aprovisionar el primer Tenant y el usuario SUPERADMIN_GLOBAL tanto de forma
interactiva como desatendida mediante variables de entorno o argumentos CLI.
"""

import argparse
import asyncio
import getpass
import hashlib
import secrets
import sys
import uuid

import pyotp
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.core.config import settings
from src.core.crypto import encrypt_aes_gcm, hash_password
from src.models.core import SystemRoleEnum, Tenant, TenantStatusEnum, User


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aprovisionar el Tenant Principal y Super Administrador Inicial de RoSGrid"
    )
    parser.add_argument("--tenant-name", help="Nombre descriptivo de la organización principal", default=None)
    parser.add_argument("--tenant-slug", help="Identificador único (slug) del tenant (ej: master)", default=None)
    parser.add_argument("--username", help="Nombre de usuario del Super Administrador", default=None)
    parser.add_argument("--email", help="Correo electrónico corporativo del Super Administrador", default=None)
    parser.add_argument("--password", help="Contraseña segura (mínimo 12 caracteres)", default=None)
    parser.add_argument("--full-name", help="Nombre completo del Super Administrador", default=None)
    parser.add_argument("--check-only", help="Solo verificar si el sistema ya está inicializado", action="store_true")
    return parser.parse_args()


async def check_is_initialized(session: AsyncSession) -> bool:
    count = await session.scalar(select(func.count(User.id)))
    return (count or 0) > 0


async def create_superadmin(
    session: AsyncSession,
    tenant_name: str,
    tenant_slug: str,
    username: str,
    email: str,
    password: str,
    full_name: str,
) -> tuple[Tenant, User, str, list[str]]:
    # 1. Crear o reutilizar Tenant
    stmt_t = select(Tenant).where(Tenant.slug == tenant_slug)
    res_t = await session.execute(stmt_t)
    tenant = res_t.scalar_one_or_none()
    if not tenant:
        tenant = Tenant(
            id=uuid.uuid4(),
            name=tenant_name,
            slug=tenant_slug,
            status=TenantStatusEnum.ACTIVE,
        )
        session.add(tenant)
        await session.flush()

    # 2. Generar TOTP Secret y Códigos de Respaldo
    totp_secret = pyotp.random_base32()
    backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
    backup_hashes = [hashlib.sha256(c.encode("utf-8")).hexdigest() for c in backup_codes]

    admin_id = uuid.uuid4()
    aad = f"{tenant.id}:{admin_id}".encode("utf-8")
    ct, iv, tag = encrypt_aes_gcm(totp_secret.encode("utf-8"), aad)

    # 3. Crear Usuario Super Administrador
    admin_user = User(
        id=admin_id,
        tenant_id=tenant.id,
        username=username,
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
        role=SystemRoleEnum.SUPERADMIN_GLOBAL,
        is_active=True,
        is_locked=False,
        failed_login_attempts=0,
        totp_enabled=True,
        totp_secret_ciphertext=ct,
        totp_secret_iv=iv,
        totp_secret_tag=tag,
        totp_recovery_codes_hashes=backup_hashes,
        has_all_routers_access=True,
    )
    session.add(admin_user)
    await session.commit()
    await session.refresh(tenant)
    await session.refresh(admin_user)

    return tenant, admin_user, totp_secret, backup_codes


async def main() -> None:
    args = parse_args()
    engine = create_async_engine(settings.ROSGRID_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        is_init = await check_is_initialized(session)
        if args.check_only:
            if is_init:
                print("[RoSGrid Seeder] El sistema ya está inicializado con al menos un usuario.")
                sys.exit(0)
            else:
                print("[RoSGrid Seeder] El sistema NO está inicializado (0 usuarios en base de datos).")
                sys.exit(1)

        if is_init:
            print("[AVISO] Ya existen usuarios registrados en la base de datos de RoSGrid.")
            print("Para crear usuarios adicionales, utiliza la API administrativa o la consola web.")
            sys.exit(0)

        print("==============================================================================")
        print("          🛡️ Asistente de Inicialización de Super Administrador RoSGrid        ")
        print("==============================================================================")

        tenant_name = args.tenant_name or input("Nombre de la Organización Principal [Empresa Principal]: ").strip()
        tenant_name = tenant_name or "Empresa Principal"

        tenant_slug = args.tenant_slug or input("Slug único de la Organización [master]: ").strip().lower()
        tenant_slug = tenant_slug or "master"

        username = args.username or input("Nombre de usuario del Super Administrador [superadmin]: ").strip()
        username = username or "superadmin"

        email = args.email or input("Correo electrónico del Super Administrador [admin@rosgrid.local]: ").strip()
        email = email or "admin@rosgrid.local"

        full_name = args.full_name or input("Nombre completo del Super Administrador [Super Administrador]: ").strip()
        full_name = full_name or "Super Administrador"

        password = args.password
        while not password or len(password) < 12:
            if password and len(password) < 12:
                print("[ERROR] La contraseña debe tener al menos 12 caracteres.")
            password = getpass.getpass("Contraseña del Super Administrador (mínimo 12 caracteres): ")

        print("\nAprovisionando organización y Super Administrador...")
        tenant, user, totp_secret, backup_codes = await create_superadmin(
            session=session,
            tenant_name=tenant_name,
            tenant_slug=tenant_slug,
            username=username,
            email=email,
            password=password,
            full_name=full_name,
        )

        totp = pyotp.totp.TOTP(totp_secret)
        uri = totp.provisioning_uri(name=email, issuer_name="RoSGrid")

        print("==============================================================================")
        print("🎉 ¡Super Administrador Inicial de RoSGrid Aprovisionado Exitosamente!")
        print("==============================================================================")
        print(f"  • Organización (Tenant Name): {tenant.name}")
        print(f"  • Slug de Organización:       {tenant.slug}")
        print(f"  • Usuario (Username):         {user.username}")
        print(f"  • Correo (Email):             {user.email}")
        print(f"  • Rol Asignado:               {user.role.value}")
        print("------------------------------------------------------------------------------")
        print("🔑 Credenciales de Autenticación de Dos Factores (2FA TOTP):")
        print(f"  • Secreto TOTP Manual:        {totp_secret}")
        print(f"  • URI de Aprovisionamiento:   {uri}")
        print("------------------------------------------------------------------------------")
        print("🛡️ Códigos de Respaldo de Emergencia (Guárdalos en un lugar seguro fuera de línea):")
        for i, code in enumerate(backup_codes, 1):
            print(f"    [{i}] {code}")
        print("==============================================================================")
        print("Accede a la interfaz web con el Slug, Usuario y Clave configurados.")


if __name__ == "__main__":
    asyncio.run(main())
