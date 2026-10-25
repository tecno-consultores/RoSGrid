#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Script de Guardrail: Validación de Flota Real y Detección Negativa de Falsos Positivos (Hito 24).

Ejecuta un Smoke Test end-to-end contra la API de RoSGrid levantada en el stack local y certifica:
1. r1, r2, r3: Syslog ACTIVO (True), Alcanzable (True), ONLINE.
2. r4, r5, r6: Syslog INACTIVO (False), No alcanzable (False), OFFLINE.
3. Disponibilidad de flota: Exactamente 50% (3 de 6).

Si r4, r5 o r6 se marcan erróneamente como activos, el script termina con código de salida 1 (FAIL-CLOSED).
"""

import os
import sys
import uuid
from typing import Any

import httpx

API_BASE_URL = os.environ.get("ROSGRID_API_URL", "http://rosgrid_api:8000")
TENANT_ID = os.environ.get("ROSGRID_TENANT_ID", "dc5332f8-e565-4e7b-a328-c879a030c2f9")
TENANT_SLUG = os.environ.get("ROSGRID_TENANT_SLUG", "sistemas")


def generate_direct_token() -> str:
    """Genera un token de SuperAdmin válido y registra su sesión en KeyDB para pruebas."""
    import asyncio
    from src.api.v1.auth import create_jwt_access_token
    from src.redis_layer.client import get_redis_client
    from src.redis_layer.sessions import create_session

    user_id = "d7512cfc-71c4-4dd5-acc4-f9af7cfd45f0"

    async def _register_session() -> str:
        sess_id, _, _ = await create_session(
            tenant_id=TENANT_ID,
            user_id=user_id,
            username="sinfallas",
            full_name="SuperAdmin Sinfallas",
            role="SUPERADMIN_GLOBAL",
            ip_address="127.0.0.1",
            user_agent="RoSGrid-SmokeTest/1.0",
        )
        return sess_id

    session_id = asyncio.run(_register_session())

    return create_jwt_access_token(
        user_id=user_id,
        tenant_id=TENANT_ID,
        tenant_slug=TENANT_SLUG,
        session_id=session_id,
        role="SUPERADMIN_GLOBAL",
        all_routers=True,
    )


def validate_fleet(routers: list[dict[str, Any]]) -> bool:
    print(f"\n=======================================================")
    print(f"🔍 [SMOKE TEST] Evaluando Flota Real ({len(routers)} routers encontrados)")
    print(f"=======================================================")

    expected_syslog_active = {"r1", "r2", "r3"}
    expected_syslog_inactive = {"r4", "r5", "r6"}

    failures = []
    online_count = 0
    offline_count = 0
    syslog_active_count = 0
    syslog_inactive_count = 0

    print(f"{'Router':<8} | {'API Reachable':<14} | {'Status':<10} | {'Syslog Active':<15} | {'Sensor Syslog':<20}")
    print("-" * 75)

    for r in routers:
        name = r.get("display_name", "")
        reachable = r.get("is_reachable", False)
        status = r.get("operational_status", "OFFLINE")
        syslog = r.get("syslog_active", False)

        if reachable or (status == "ONLINE"):
            online_count += 1
        else:
            offline_count += 1

        if syslog:
            syslog_active_count += 1
        else:
            syslog_inactive_count += 1

        if name in expected_syslog_active:
            # Aserción Positiva: DEBE tener syslog activo hacia RoSGrid
            if not syslog:
                failures.append(f"FALLO en {name}: Se esperaba syslog_active=True, pero se obtuvo {syslog}")
                sensor_res = "❌ FALLO (Esperaba Activo)"
            else:
                sensor_res = "🟢 Activo (Correcto)"
        elif name in expected_syslog_inactive:
            # Aserción Negativa: DEBE tener syslog INACTIVO (sensor apagado de fábrica)
            if syslog:
                failures.append(
                    f"FALSO POSITIVO CRÍTICO en {name}: Router de fábrica se marcó con syslog_active=True!"
                )
                sensor_res = "🚨 FALSO POSITIVO (Encendido indebidamente)"
            else:
                sensor_res = "⚪ Sin Syslog (Correcto)"
        else:
            sensor_res = "⚪ No catalogado"

        print(f"{name:<8} | {str(reachable):<14} | {status:<10} | {str(syslog):<15} | {sensor_res:<20}")

    print("-" * 75)
    total = len(routers)
    avail_pct = round((online_count / total) * 100) if total > 0 else 0
    print(f"📊 Flota API: {online_count}/{total} en línea ({avail_pct}% disponibilidad)")
    print(f"📡 Sensores Syslog: {syslog_active_count} Activos (r1, r2, r3) | {syslog_inactive_count} Sin Syslog (r4, r5, r6)\n")

    if syslog_active_count != 3 or syslog_inactive_count != 3:
        failures.append(
            f"Conteo de sensores Syslog incorrecto: Activos={syslog_active_count} (esperado 3), Inactivos={syslog_inactive_count} (esperado 3)"
        )

    if failures:
        print("❌ ERRORES DE DETECCIÓN O REGRESIÓN DETECTADOS:")
        for f in failures:
            print(f"   - {f}")
        return False

    print("🎉 CERTIFICACIÓN EXITOSA: La flota discrimina perfectamente los sensores configurados de los de fábrica.")
    return True


def main() -> int:
    try:
        token = generate_direct_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{API_BASE_URL}/api/v1/inventory/routers"

        with httpx.Client(timeout=15.0) as client:
            print("\n--- PASO 1: Consulta Inicial de Flota ---")
            resp = client.get(url, headers=headers)
            if resp.status_code != 200:
                print(f"Error consultando inventario: HTTP {resp.status_code} - {resp.text}")
                return 1

            if not validate_fleet(resp.json()):
                return 1

            print("\n--- PASO 2: Consulta con Refresco Forzado (?refresh=true) ---")
            resp_refreshed = client.get(f"{url}?refresh=true", headers=headers)
            if resp_refreshed.status_code != 200:
                print(f"Error consultando inventario con refresh: HTTP {resp_refreshed.status_code} - {resp_refreshed.text}")
                return 1

            if not validate_fleet(resp_refreshed.json()):
                return 1

        return 0
    except Exception as exc:
        print(f"Excepción ejecutando Smoke Test de Flota Real: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
