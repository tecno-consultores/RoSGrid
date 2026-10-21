# 25 — ESTÁNDAR QA 11X BACKEND: SUITE UNITARIA AISLADA (*.unit.py >= 95%), MUTACIÓN (MUTMUT) Y CATÁLOGO DE MOCKS ROUTEROS v7 (RoSGrid)

**[DIRECTIVA PARA ANTIGRAVITY]:** Este documento especifica la estructura obligatoria de la suite de pruebas unitarias del Backend (`fastapi/tests/`), el catálogo de mocks deterministas de la REST API de RouterOS v7 y las reglas de diseño de *assertions* para aniquilar el 100% de los mutantes generados por **mutmut**. Ninguna prueba unitaria puede conectarse a PostgreSQL real, Redis real ni a un equipo MikroTik real.

## 1. Frontera Estricta de Archivos (Tool Boundary) y Estructura de fastapi/tests/

Todos los archivos de prueba unitaria DEBEN terminar en `.unit.py` o `.spec.py`:

```text
fastapi/tests/
├── conftest.py                                   # Fixtures globales: AsyncMock DB, FakeRedis en RAM, MockMikrotikTransport
├── mocks/
│   ├── __init__.py
│   └── routeros_v7_payloads.py                   # Diccionario determinista de respuestas JSON de RouterOS v7.16+
├── core/
│   ├── test_crypto_aes_gcm_argon2.unit.py        # Cifrado AES-256-GCM con AAD, detección de alteración de tag/AAD y Argon2id
│   ├── test_csrf_and_cookies.unit.py             # Validación HMAC-SHA256 de X-CSRF-Token y atributos __Host-
│   ├── test_security_headers.unit.py             # Verificación de cabeceras exigidas por OWASP ZAP
│   └── test_immutable_audit_hashchain.unit.py    # Sanitización [REDACTED] y encadenamiento SHA-256 (prev_record_hash)
├── redis_layer/
│   ├── test_idempotency_middleware.unit.py       # Estados IN_PROGRESS (409), payload mismatch (422) y replay (200)
│   ├── test_sessions_and_killswitch.unit.py      # Creación de sesión, Reuse Detection de Refresh Token y evento SESSION_KILLED
│   └── test_zero_metrics_state_machine.unit.py   # Transiciones ONLINE -> OFFLINE (al 3.er fallo), HIGH_CPU y supresión por mantenimiento
├── rbac/
│   ├── test_rbac_11_roles_matrix.unit.py         # Parametrizado (@pytest.mark.parametrize) probando los 11 roles x 19 acciones
│   └── test_maker_checker_interceptor.unit.py    # Intercepción 202 Accepted en las 7 firmas críticas y bloqueo de auto-aprobación
├── mikrotik/
│   ├── test_ssl_tofu_pinning.unit.py             # PENDING_TOFU -> TRUSTED_PINNED, y bloqueo inmediato en FINGERPRINT_MISMATCH
│   ├── test_rest_client_v7.unit.py               # Llamadas GET/PUT/PATCH/DELETE/POST y fallback a previous_password en rotación
│   └── test_safemode_deadman_switch.unit.py      # Inyección de /system/scheduler, commit exitoso y auto-rollback en corte de red
└── api/
    ├── test_auth_and_2fa_endpoints.unit.py       # Login Multi-Tenant, bloqueo al 5.º intento, enrolamiento y verificación TOTP
    ├── test_inventory_csv_and_vault.unit.py      # Alta de router, CSV dry-run/commit, Step-Up Auth (solo 2 roles altos) y rotación
    ├── test_webfig_layer1_endpoints.unit.py      # Interfaces, SFP DDM, IP (protección anti-suicidio www-ssl), Firewall move, BGP/OSPF, PPP, Tools
    ├── test_webfig_layer2_universal.unit.py      # Inferencia de columnas, detección singleton y bloqueo de FORBIDDEN_L2_PATHS
    ├── test_backups_diff_and_bulk_ops.unit.py    # Deduplicación SHA-256 de .rsc, cálculo de unified diff y pre-backup obligatorio en upgrade
    ├── test_websockets_multiplexer.unit.py       # Activación de poller con 1.er suscriptor y apagado instantáneo cuando SCARD == 0
    ├── test_hito23_cve_and_syslog.unit.py        # Cruce semver CVEs, catálogo offline, parsing BSD syslog, UDP protocol y RingBuffer KeyDB
    ├── test_hito23_topology_and_fleet.unit.py    # Grafo L2, filtrado por router, DAG PoE inverso, scrape Prometheus y caché KeyDB
    └── test_hito23_mcp_tools.unit.py             # Herramientas semánticas MCP de topología L2, CVEs, syslog y upgrade PoE-aware
```

## 2. Catálogo Oficial de Mocks Deterministas de RouterOS v7 (routeros_v7_payloads.py)

Para que pytest-mock y httpx.MockTransport simulen fielmente un MikroTik con RouterOS v7 sin red real, AntiGravity DEBE implementar este catálogo en `fastapi/tests/mocks/routeros_v7_payloads.py`:

```python
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from typing import Any

MOCK_SYSTEM_RESOURCE: dict[str, Any] = {
    "uptime": "14d06h22m15s",
    "version": "7.16.1 (stable)",
    "build-time": "2026-09-10 12:00:00",
    "factory-software": "7.8",
    "free-memory": "784334848",
    "total-memory": "1073741824",
    "cpu": "ARM64",
    "cpu-count": "4",
    "cpu-frequency": "1400",
    "cpu-load": "19",
    "free-hdd-space": "419430400",
    "total-hdd-space": "536870912",
    "architecture-name": "arm64",
    "board-name": "RB4011iGS+",
    "platform": "MikroTik",
}

MOCK_SYSTEM_ROUTERBOARD: dict[str, Any] = {
    "routerboard": "true",
    "model": "RB4011iGS+",
    "serial-number": "D4460B123456",
    "firmware-type": "al2",
    "factory-firmware": "7.8",
    "current-firmware": "7.16.1",
    "upgrade-firmware": "7.16.1",
}

MOCK_SYSTEM_HEALTH: list[dict[str, str]] = [
    {".id": "*1", "name": "temperature", "value": "44", "type": "C"},
    {".id": "*2", "name": "voltage", "value": "24.2", "type": "V"},
]

MOCK_SFP_MONITOR: list[dict[str, str]] = [
    {
        "name": "sfp-sfpplus1",
        "status": "link-ok",
        "auto-negotiation": "done",
        "rate": "10Gbps",
        "full-duplex": "true",
        "sfp-module-present": "true",
        "sfp-vendor-name": "MikroTik",
        "sfp-vendor-part-number": "S+31DLC10D",
        "sfp-wavelength": "1310",
        "sfp-temperature": "42",
        "sfp-supply-voltage": "3.31",
        "sfp-tx-bias-current": "18",
        "sfp-tx-power": "-3.12",
        "sfp-rx-power": "-6.45",
    }
]

MOCK_FIREWALL_FILTER_RULES: list[dict[str, str]] = [
    {
        ".id": "*1",
        "chain": "input",
        "action": "accept",
        "connection-state": "established,related,untracked",
        "bytes": "98451200",
        "packets": "124500",
        "dynamic": "false",
        "invalid": "false",
        "disabled": "false",
        "comment": "Accept established/related",
    },
    {
        ".id": "*2",
        "chain": "input",
        "action": "drop",
        "connection-state": "invalid",
        "bytes": "14200",
        "packets": "310",
        "dynamic": "false",
        "invalid": "false",
        "disabled": "false",
        "comment": "Drop invalid",
    },
]

MOCK_BGP_SESSIONS: list[dict[str, str]] = [
    {
        ".id": "*3000001",
        "name": "ISP-Carrier-1-1",
        "remote.address": "186.10.20.1",
        "remote.as": "65001",
        "local.address": "186.10.20.2",
        "local.as": "65500",
        "established": "true",
        "uptime": "2w4d10h12m",
        "prefix-count": "942100",
    }
]
```

## 3. Reglas Anti-Mutantes para Aprobar mutmut (make qa-mutation)

mutmut altera operadores (`==` por `!=`, `<` por `<=`, `+` por `-`, `True` por `False`, constantes numéricas y valores de retorno) en `fastapi/src/`. Para que **ningún mutante sobreviva**:

1. **Pruebas de Valores Límite Exactos (Boundary Value Analysis):**
   - En el monitor de salud (`consecutive_failures >= 3` para declarar `OFFLINE`): escribe un test con `failures = 2` (verifica que sigue `ONLINE`) y un test con `failures = 3` (verifica que pasa exactamente a `OFFLINE`). Si solo pruebas con `failures = 5`, el mutante que cambia `>= 3` por `> 3` sobrevivirá.
   - En salud óptica SFP (`sfp_rx_power_dbm >= -20.0` es `OPTIMAL`, `< -25.0` es `CRITICAL_LOW_LIGHT`): prueba exactamente con `-20.0`, `-20.01`, `-25.0` y `-25.01`.
   - En bloqueo de login al 5.º intento fallido (`failed_login_attempts >= 5`): prueba el intento 4 (no bloqueado) y el intento 5 (`is_locked == True`).

2. **Verificación de Argumentos en Mocks (`assert_called_once_with`):**
   - No uses únicamente `mock_fn.assert_called()`. Verifica los argumentos exactos pasados al conector de RouterOS, al logger de auditoría y a Redis (`mock_redis.set.assert_awaited_once_with(...)`).

3. **Verificación de AAD en Cifrado AES-256-GCM:**
   - Incluye un test que intente desencriptar la clave de un router cambiando el `router_id` o `tenant_id` en el AAD y verifica que lance `InvalidTag`. Esto mata cualquier mutante que altere la construcción del AAD.
