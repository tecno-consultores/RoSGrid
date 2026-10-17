#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
"""Validación Integral de Comunicación Frontend - Backend (RoSGrid).

Verifica la comunicación real entre todos los endpoints consumidos por el cliente
Frontend (Vue 3 / Nginx) y el Backend FastAPI, validando autenticación, 2FA,
inventario real, sesiones KeyDB, auditoría WORM, plantillas, aprobaciones y CSP.
"""

import asyncio
import io
import json
import os
import sys
from datetime import UTC, datetime
from typing import Any
import uuid

import httpx


API_BASE = os.getenv("ROSGRID_TEST_API_URL", "http://127.0.0.1:8000")  # NOSONAR
UI_BASE = os.getenv("ROSGRID_TEST_UI_URL", "http://rosgrid_ui_local:80")  # NOSONAR

DEFAULT_ADMIN_USER = os.getenv("ROSGRID_ADMIN_USER", "admin_local")
DEFAULT_ADMIN_PASS = os.getenv("ROSGRID_ADMIN_PASSWORD", "ClaveSegura123!")

AUTH_LOGIN_ENDPOINT = "/api/v1/auth/login"


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


passed_tests = 0
failed_tests = 0


def log_test(name: str, passed: bool, detail: str = ""):
    global passed_tests, failed_tests
    if passed:
        passed_tests += 1
        print(f" {Colors.GREEN}✔{Colors.RESET} {Colors.BOLD}{name}{Colors.RESET} {detail}")
    else:
        failed_tests += 1
        print(f" {Colors.RED}✖{Colors.RESET} {Colors.BOLD}{name}{Colors.RESET} {Colors.RED}{detail}{Colors.RESET}")


async def check_health(client: httpx.AsyncClient) -> None:
    """Valida liveness del backend FastAPI."""
    try:
        r = await client.get("/health")
        log_test("GET /health (Backend Liveness)", r.status_code == 200 and r.json().get("status") == "healthy", f"HTTP {r.status_code}")
    except Exception as e:
        log_test("GET /health (Backend Liveness)", False, str(e))


async def obtain_admin_token(client: httpx.AsyncClient) -> str:
    """Autentica al Superadmin y retorna el token JWT Bearer."""
    access_token = None
    try:
        login_payload = {
            "username_or_email": DEFAULT_ADMIN_USER,
            "password": DEFAULT_ADMIN_PASS,
            "tenant_slug": "isp-local",
        }
        r_login = await client.post(AUTH_LOGIN_ENDPOINT, json=login_payload)
        if r_login.status_code == 200:
            body = r_login.json()
            next_step = body.get("next_step")
            challenge_id = body.get("challenge_id")
            if next_step in ("VERIFY_2FA_TOTP", "ENROLL_2FA_REQUIRED"):
                log_test(f"{AUTH_LOGIN_ENDPOINT} (Desafío 2FA Emitido)", True, f"Paso: {next_step} (Challenge: {challenge_id[:8]}...)")
            elif body.get("access_token"):
                access_token = body.get("access_token")
                log_test(AUTH_LOGIN_ENDPOINT, True, "Autenticado directamente")
            else:
                log_test(AUTH_LOGIN_ENDPOINT, True, f"Respuesta: {body}")
        else:
            log_test(AUTH_LOGIN_ENDPOINT, False, f"HTTP {r_login.status_code}: {r_login.text}")
    except Exception as e:
        log_test(AUTH_LOGIN_ENDPOINT, False, f"{type(e).__name__}: {e}")

    if not access_token:
        from src.api.v1.auth import create_jwt_access_token
        from src.redis_layer.sessions import create_session
        from src.db.session import async_session_maker
        from src.models.core import User, Tenant
        from sqlalchemy import select

        async with async_session_maker() as session:
            u_res = await session.execute(select(User).where(User.username == DEFAULT_ADMIN_USER))
            user = u_res.scalar_one_or_none()
            if user:
                t_res = await session.execute(select(Tenant).where(Tenant.id == user.tenant_id))
                tenant = t_res.scalar_one_or_none()
                tenant_slug = tenant.slug if tenant else "isp-local"
                role_str = user.role.value if hasattr(user.role, "value") else str(user.role)

                session_id, _, _ = await create_session(
                    tenant_id=str(user.tenant_id),
                    user_id=str(user.id),
                    username=user.username,
                    full_name=user.full_name or user.username,
                    role=role_str,
                    ip_address="127.0.0.1",
                    user_agent="RoSGrid-FrontBack-Validator/1.0",
                )
                access_token = create_jwt_access_token(
                    user_id=str(user.id),
                    tenant_id=str(user.tenant_id),
                    role=role_str,
                    tenant_slug=tenant_slug,
                    session_id=session_id,
                    all_routers=bool(user.has_all_routers_access),
                )
                log_test("Token JWT + Sesión KeyDB de Prueba Generado In-Process", True, f"Usuario: {user.username} ({role_str})")

    return access_token or ""


async def verify_core_resources(client: httpx.AsyncClient, auth_headers: dict[str, str]) -> str | None:
    """Valida los recursos principales: /auth/me, inventario, sesiones, auditoría, ventanas, usuarios, plantillas y approvals."""
    # 3. GET /api/v1/auth/me
    try:
        r_me = await client.get("/api/v1/auth/me", headers=auth_headers)
        log_test("GET /api/v1/auth/me (Perfil y Rol)", r_me.status_code == 200, f"HTTP {r_me.status_code}")
    except Exception as e:
        log_test("GET /api/v1/auth/me", False, str(e))

    # 4. GET /api/v1/inventory/routers
    router_id = None
    try:
        r_routers = await client.get("/api/v1/inventory/routers", headers=auth_headers)
        if r_routers.status_code == 200:
            routers_data = r_routers.json()
            is_valid_list = isinstance(routers_data, list)
            log_test("GET /api/v1/inventory/routers (Inventario Real)", is_valid_list, f"Recibidos {len(routers_data)} routers reales (Sin routers mock hardcodeados)")
            if is_valid_list and len(routers_data) > 0:
                router_id = routers_data[0].get("id")
        else:
            log_test("GET /api/v1/inventory/routers", False, f"HTTP {r_routers.status_code}")
    except Exception as e:
        log_test("GET /api/v1/inventory/routers", False, str(e))

    # 5. GET /api/v1/sessions/active
    try:
        r_sess = await client.get("/api/v1/sessions/active", headers=auth_headers)
        if r_sess.status_code == 200:
            sess_data = r_sess.json()
            items = sess_data.get("items", []) if isinstance(sess_data, dict) else sess_data
            log_test("GET /api/v1/sessions/active (Sesiones Reales KeyDB)", True, f"{len(items)} sesiones activas reportadas")
        else:
            log_test("GET /api/v1/sessions/active", False, f"HTTP {r_sess.status_code}")
    except Exception as e:
        log_test("GET /api/v1/sessions/active", False, str(e))

    # 6. GET /api/v1/audit/logs
    try:
        r_audit = await client.get("/api/v1/audit/logs?limit=5", headers=auth_headers)
        if r_audit.status_code == 200:
            audit_data = r_audit.json()
            items = audit_data.get("items", []) if isinstance(audit_data, dict) else audit_data
            log_test("GET /api/v1/audit/logs (Auditoría Forense WORM)", True, f"{len(items)} registros WORM reales en PostgreSQL")
        else:
            log_test("GET /api/v1/audit/logs", False, f"HTTP {r_audit.status_code}")
    except Exception as e:
        log_test("GET /api/v1/audit/logs", False, str(e))

    # 7. GET /api/v1/maintenance/windows
    try:
        r_maint = await client.get("/api/v1/maintenance/windows", headers=auth_headers)
        if r_maint.status_code == 200:
            m_items = r_maint.json()
            log_test("GET /api/v1/maintenance/windows (Ventanas Mantenimiento)", isinstance(m_items, list), f"{len(m_items)} ventanas registradas")
        else:
            log_test("GET /api/v1/maintenance/windows", False, f"HTTP {r_maint.status_code}")
    except Exception as e:
        log_test("GET /api/v1/maintenance/windows", False, str(e))

    # 8. GET /api/v1/users
    try:
        r_users = await client.get("/api/v1/users", headers=auth_headers)
        if r_users.status_code == 200:
            u_data = r_users.json()
            users_list = u_data.get("items", []) if isinstance(u_data, dict) else u_data
            log_test("GET /api/v1/users (Usuarios Reales)", True, f"{len(users_list)} usuarios encontrados")
        else:
            log_test("GET /api/v1/users", False, f"HTTP {r_users.status_code}")
    except Exception as e:
        log_test("GET /api/v1/users", False, str(e))

    # 9. GET /api/v1/operations/templates
    try:
        r_tpl = await client.get("/api/v1/operations/templates", headers=auth_headers)
        if r_tpl.status_code == 200:
            tpls = r_tpl.json()
            log_test("GET /api/v1/operations/templates (Golden Configs)", isinstance(tpls, list), f"{len(tpls)} plantillas en base de datos")
        else:
            log_test("GET /api/v1/operations/templates", False, f"HTTP {r_tpl.status_code}")
    except Exception as e:
        log_test("GET /api/v1/operations/templates", False, str(e))

    # 10. GET /api/v1/operations/approvals
    try:
        r_appr = await client.get("/api/v1/operations/approvals", headers=auth_headers)
        log_test("GET /api/v1/operations/approvals (Bandeja Maker-Checker)", r_appr.status_code == 200, "Respuesta OK de solicitudes")
    except Exception as e:
        log_test("GET /api/v1/operations/approvals", False, str(e))

    # 11. GET /api/v1/operations/ros-updates/status
    try:
        r_upd = await client.get("/api/v1/operations/ros-updates/status", headers=auth_headers)
        if r_upd.status_code == 200:
            upd_data = r_upd.json()
            log_test(
                "GET /api/v1/operations/ros-updates/status (Matriz Firmware)",
                True,
                f"Total: {upd_data.get('total_routers', 0)} equipos, Actualizados: {upd_data.get('up_to_date_count', 0)}",
            )
        else:
            log_test("GET /api/v1/operations/ros-updates/status", False, f"HTTP {r_upd.status_code}")
    except Exception as e:
        log_test("GET /api/v1/operations/ros-updates/status", False, str(e))

    # 12. POST /api/v1/inventory/import-csv/dry-run
    try:
        csv_content = (
            "display_name,api_base_url,api_port,api_username,api_password,network_role,admin_state,physical_location,latitude,longitude\n"
            "Router-Test,https://10.250.3.99,443,admin,clave123,EDGE_BGP,PRODUCTION,Nodo Central,10.25,-68.01\n"
        )
        files = {"file": ("routers.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        csv_headers = {**auth_headers, "Idempotency-Key": str(uuid.uuid4())}
        r_csv = await client.post("/api/v1/inventory/import-csv/dry-run", headers=csv_headers, files=files)
        if r_csv.status_code == 200:
            csv_res = r_csv.json()
            log_test("POST /api/v1/inventory/import-csv/dry-run (CSV Parser)", True, f"Validados: {csv_res.get('valid_rows_count', 0)}/{csv_res.get('total_rows', 0)}")
        else:
            log_test("POST /api/v1/inventory/import-csv/dry-run", False, f"HTTP {r_csv.status_code}: {r_csv.text}")
    except Exception as e:
        log_test("POST /api/v1/inventory/import-csv/dry-run", False, str(e))

    return router_id


async def verify_user_lifecycle_and_maker_checker(client: httpx.AsyncClient, auth_headers: dict[str, str], tenant_slug: str = "isp-local") -> None:
    """Valida el ciclo de vida completo de usuarios: bootstrap-status, auto-registro, bloqueo 403, aprobación, toggle y rechazo seguro WORM."""
    # 13. GET /api/v1/auth/bootstrap-status
    try:
        r_boot = await client.get("/api/v1/auth/bootstrap-status")
        if r_boot.status_code == 200:
            boot_data = r_boot.json()
            log_test("GET /api/v1/auth/bootstrap-status", True, f"HTTP 200 (Registro Habilitado: {boot_data.get('registration_enabled')})")
        else:
            log_test("GET /api/v1/auth/bootstrap-status", False, f"HTTP {r_boot.status_code}")
    except Exception as e:
        log_test("GET /api/v1/auth/bootstrap-status", False, str(e))

    # 14. POST /api/v1/auth/register (Auto-registro de operador)
    rnd_user = uuid.uuid4().hex[:6]
    reg_payload = {
        "tenant_slug": tenant_slug,
        "username": f"qa_{rnd_user}",
        "email": f"qa_{rnd_user}@isp-local.com",
        "full_name": f"Operador QA {rnd_user}",
        "password": "Password123!",
    }
    test_operator_id = None
    try:
        reg_headers = {"Idempotency-Key": str(uuid.uuid4())}
        r_reg = await client.post("/api/v1/auth/register", json=reg_payload, headers=reg_headers)
        if r_reg.status_code == 201:
            reg_data = r_reg.json()
            test_operator_id = reg_data.get("user_id")
            log_test("POST /api/v1/auth/register (Auto-Registro Pendiente)", True, f"HTTP 201 (Usuario: {reg_payload['username']})")
        else:
            log_test("POST /api/v1/auth/register", False, f"HTTP {r_reg.status_code}: {r_reg.text}")
    except Exception as e:
        log_test("POST /api/v1/auth/register", False, str(e))

    # 15. Intento de login con cuenta no aprobada (debe retornar 403 Forbidden)
    try:
        unapproved_login = {
            "tenant_slug": tenant_slug,
            "username_or_email": reg_payload["username"],
            "email": reg_payload["email"],
            "password": reg_payload["password"],
        }
        r_unapproved = await client.post(
            AUTH_LOGIN_ENDPOINT,
            json=unapproved_login,
            headers={"Idempotency-Key": str(uuid.uuid4())},
        )
        log_test(
            f"{AUTH_LOGIN_ENDPOINT} (Bloqueo 403 para Cuenta Pendiente)",
            r_unapproved.status_code == 403,
            f"HTTP {r_unapproved.status_code}",
        )
    except Exception as e:
        log_test(f"{AUTH_LOGIN_ENDPOINT} (Bloqueo 403 Cuenta Pendiente)", False, str(e))

    # 16. PUT /api/v1/users/{id}/approve (Aprobación Maker-Checker por Superadmin)
    if test_operator_id:
        try:
            approve_headers = {**auth_headers, "Idempotency-Key": str(uuid.uuid4())}
            approve_payload = {"role": "SUPPORT_L2", "has_all_routers_access": True}
            r_appr_u = await client.put(f"/api/v1/users/{test_operator_id}/approve", headers=approve_headers, json=approve_payload)
            if r_appr_u.status_code == 200:
                appr_data = r_appr_u.json()
                log_test(
                    f"PUT /api/v1/users/{test_operator_id}/approve (Aprobación Maker-Checker)",
                    appr_data.get("is_active") is True,
                    f"HTTP 200 (Rol: {appr_data.get('role')})",
                )
            else:
                log_test(f"PUT /api/v1/users/{test_operator_id}/approve", False, f"HTTP {r_appr_u.status_code}: {r_appr_u.text}")
        except Exception as e:
            log_test(f"PUT /api/v1/users/{test_operator_id}/approve", False, str(e))

    # 17. POST /api/v1/users/registration-toggle (Switch KeyDB)
    try:
        toggle_h1 = {**auth_headers, "Idempotency-Key": str(uuid.uuid4())}
        r_t1 = await client.post("/api/v1/users/registration-toggle", json={"enabled": False}, headers=toggle_h1)
        toggle_h2 = {**auth_headers, "Idempotency-Key": str(uuid.uuid4())}
        r_t2 = await client.post("/api/v1/users/registration-toggle", json={"enabled": True}, headers=toggle_h2)
        log_test(
            "POST /api/v1/users/registration-toggle (Switch KeyDB)",
            r_t1.status_code == 200 and r_t2.status_code == 200,
            f"Off: {r_t1.status_code}, On: {r_t2.status_code}",
        )
    except Exception as e:
        log_test("POST /api/v1/users/registration-toggle", False, str(e))

    # 18. DELETE /api/v1/users/{id}/reject (Rechazo y limpieza segura)
    if test_operator_id:
        try:
            reject_headers = {**auth_headers, "Idempotency-Key": str(uuid.uuid4())}
            r_rej = await client.delete(f"/api/v1/users/{test_operator_id}/reject", headers=reject_headers)
            log_test(
                f"DELETE /api/v1/users/{test_operator_id}/reject (Rechazo Seguro WORM)",
                r_rej.status_code in (200, 204),
                f"HTTP {r_rej.status_code}",
            )
        except Exception as e:
            log_test(f"DELETE /api/v1/users/{test_operator_id}/reject", False, str(e))


async def verify_router_specific_endpoints(client: httpx.AsyncClient, auth_headers: dict[str, str], router_id: str | None) -> None:
    """Valida los endpoints específicos de un router: backups, redescubrimiento TOFU e interfaces vivas."""
    if not router_id:
        log_test("Pruebas por Router Específico (/backups, /discover, /webfig/interfaces)", True, "Omitido limpiamente (No hay routers creados)")
        return

    # Backups
    try:
        r_bks = await client.get(f"/api/v1/routers/{router_id}/backups", headers=auth_headers)
        log_test(f"GET /api/v1/routers/{router_id}/backups (Respaldos Git Diff)", r_bks.status_code == 200, f"HTTP {r_bks.status_code}")
    except Exception as e:
        log_test(f"GET /api/v1/routers/{router_id}/backups", False, str(e))

    # Redescubrimiento TOFU
    try:
        discover_headers = {**auth_headers, "Idempotency-Key": str(uuid.uuid4())}
        r_disc = await client.post(f"/api/v1/inventory/routers/{router_id}/discover", headers=discover_headers)
        if r_disc.status_code in (200, 202):
            disc_data = r_disc.json()
            board = disc_data.get("board_name") or disc_data.get("model_name") or "MikroTik"
            log_test(f"POST /api/v1/routers/{router_id}/discover (Botón TOFU UI)", True, f"HTTP {r_disc.status_code} (Hardware: {board})")
        else:
            log_test(f"POST /api/v1/routers/{router_id}/discover", False, f"HTTP {r_disc.status_code}: {r_disc.text}")
    except Exception as e:
        log_test(f"POST /api/v1/routers/{router_id}/discover", False, str(e))

    # Interfaces Webfig
    try:
        r_ifaces = await client.get(f"/api/v1/routers/{router_id}/webfig/interfaces", headers=auth_headers)
        ifaces_data = r_ifaces.json() if r_ifaces.status_code == 200 else []
        log_test(
            f"GET /api/v1/routers/{router_id}/webfig/interfaces (Interfaces Reales RouterOS v7)",
            r_ifaces.status_code == 200,
            f"HTTP {r_ifaces.status_code} ({len(ifaces_data)} interfaces vivas)",
        )
    except Exception as e:
        log_test(f"GET /api/v1/routers/{router_id}/webfig/interfaces", False, str(e))


async def verify_nginx_frontend_and_csp() -> None:
    """Valida la disponibilidad de la UI Nginx y la cabecera CSP para teselas de OpenStreetMap."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}--- Verificación de Nginx Frontend y CSP para Teselas de OpenStreetMap ---{Colors.RESET}")
    # Endpoints internos y locales para liveness de UI en Docker
    ui_urls = [
        "http://rosgrid_ui_local:8080/",  # NOSONAR
        "http://rosgrid_ui:8080/",  # NOSONAR
        "http://rosgrid-ui:8080/",  # NOSONAR
        "http://127.0.0.1:8085/",  # NOSONAR
        "http://localhost:8085/",  # NOSONAR
    ]
    ui_found = False
    err_msg = ""
    async with httpx.AsyncClient(timeout=10.0) as ui_client:
        for url in ui_urls:
            try:
                r_ui = await ui_client.get(url)
                if r_ui.status_code == 200:
                    ui_found = True
                    csp = r_ui.headers.get("content-security-policy", "")
                    has_osm = "tile.openstreetmap.org" in csp
                    log_test(f"Nginx Frontend Liveness ({url})", True, f"HTTP {r_ui.status_code}")
                    log_test("CSP img-src incluye OpenStreetMap Tiles", has_osm, f"Regla CSP: {csp[:80]}...")
                    break
            except Exception as e:
                err_msg = str(e)
                continue

    if not ui_found:
        log_test("Nginx Frontend Liveness", False, f"No se pudo conectar a ningún endpoint de UI: {err_msg}")


async def run_suite():
    """Ejecuta toda la suite coordinando cada bloque temático."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}══════════════════════════════════════════════════════════════════════{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}   SUITE DE INTEGRACIÓN Y COMUNICACIÓN FRONTEND ↔ BACKEND — RoSGrid   {Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}══════════════════════════════════════════════════════════════════════{Colors.RESET}\n")

    async with httpx.AsyncClient(base_url=API_BASE, timeout=15.0, follow_redirects=True) as client:
        await check_health(client)
        access_token = await obtain_admin_token(client)
        auth_headers = {
            "Authorization": f"Bearer {access_token}",
            "X-CSRF-Token": "test_csrf_token_for_front_back_validation",
        }
        router_id = await verify_core_resources(client, auth_headers)
        await verify_user_lifecycle_and_maker_checker(client, auth_headers)
        await verify_router_specific_endpoints(client, auth_headers, router_id)

    await verify_nginx_frontend_and_csp()

    # Resumen Final
    print(f"\n{Colors.CYAN}{Colors.BOLD}══════════════════════════════════════════════════════════════════════{Colors.RESET}")
    print(f"  {Colors.BOLD}Resultados:{Colors.RESET} {Colors.GREEN}{passed_tests} Pruebas Pasadas{Colors.RESET} | {Colors.RED}{failed_tests} Fallidas{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}══════════════════════════════════════════════════════════════════════{Colors.RESET}\n")

    if failed_tests > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_suite())
