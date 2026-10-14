# 25 — ESTÁNDAR QA 11X BACKEND: SUITE UNITARIA AISLADA (\*.unit.py \>= 95%), MUTACIÓN (MUTMUT) Y CATÁLOGO DE MOCKS ROUTEROS v7 (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica la estructura obligatoria de la suite de pruebas unitarias del Backend (fastapi/tests/), el catálogo de mocks deterministas de la REST API de RouterOS v7 y las reglas de diseño de *assertions* para aniquilar el 100% de los mutantes generados por **mutmut**. Ninguna prueba unitaria puede conectarse a PostgreSQL real, Redis real ni a un equipo MikroTik real.




## **1. Frontera Estricta de Archivos (Tool Boundary) y Estructura de fastapi/tests/**

Todos los archivos de prueba unitaria DEBEN terminar en .unit.py o .spec.py:


fastapi/tests/


├── conftest.py                                   \# Fixtures globales: AsyncMock DB, FakeRedis en RAM, MockMikrotikTransport


├── mocks/


│   ├── \_\_init\_\_.py


│   └── routeros\_v7\_payloads.py                   \# Diccionario determinista de respuestas JSON de RouterOS v7.16+


├── core/


│   ├── test\_crypto\_aes\_gcm\_argon2.unit.py        \# Cifrado AES-256-GCM con AAD, detección de alteración de tag/AAD y Argon2id


│   ├── test\_csrf\_and\_cookies.unit.py             \# Validación HMAC-SHA256 de X-CSRF-Token y atributos \_\_Host-


│   ├── test\_security\_headers.unit.py             \# Verificación de cabeceras exigidas por OWASP ZAP


│   └── test\_immutable\_audit\_hashchain.unit.py    \# Sanitización \[REDACTED\] y encadenamiento SHA-256 (prev\_record\_hash)


├── redis\_layer/


│   ├── test\_idempotency\_middleware.unit.py       \# Estados IN\_PROGRESS (409), payload mismatch (422) y replay (200)


│   ├── test\_sessions\_and\_killswitch.unit.py      \# Creación de sesión, Reuse Detection de Refresh Token y evento SESSION\_KILLED


│   └── test\_zero\_metrics\_state\_machine.unit.py   \# Transiciones ONLINE -\> OFFLINE (al 3.er fallo), HIGH\_CPU y supresión por mantenimiento


├── rbac/


│   ├── test\_rbac\_11\_roles\_matrix.unit.py         \# Parametrizado (@pytest.mark.parametrize) probando los 11 roles x 19 acciones


│   └── test\_maker\_checker\_interceptor.unit.py    \# Intercepción 202 Accepted en las 7 firmas críticas y bloqueo de auto-aprobación


├── mikrotik/


│   ├── test\_ssl\_tofu\_pinning.unit.py             \# PENDING\_TOFU -\> TRUSTED\_PINNED, y bloqueo inmediato en FINGERPRINT\_MISMATCH


│   ├── test\_rest\_client\_v7.unit.py               \# Llamadas GET/PUT/PATCH/DELETE/POST y fallback a previous\_password en rotación


│   └── test\_safemode\_deadman\_switch.unit.py      \# Inyección de /system/scheduler, commit exitoso y auto-rollback en corte de red


└── api/


    ├── test\_auth\_and\_2fa\_endpoints.unit.py       \# Login Multi-Tenant, bloqueo al 5.º intento, enrolamiento y verificación TOTP


    ├── test\_inventory\_csv\_and\_vault.unit.py      \# Alta de router, CSV dry-run/commit, Step-Up Auth (solo 2 roles altos) y rotación


    ├── test\_webfig\_layer1\_endpoints.unit.py      \# Interfaces, SFP DDM, IP (protección anti-suicidio www-ssl), Firewall move, BGP/OSPF, PPP, Tools


    ├── test\_webfig\_layer2\_universal.unit.py      \# Inferencia de columnas, detección singleton y bloqueo de FORBIDDEN\_L2\_PATHS


    ├── test\_backups\_diff\_and\_bulk\_ops.unit.py    \# Deduplicación SHA-256 de .rsc, cálculo de unified diff y pre-backup obligatorio en upgrade


    └── test\_websockets\_multiplexer.unit.py       \# Activación de poller con 1.er suscriptor y apagado instantáneo cuando SCARD == 0




## **2. Catálogo Oficial de Mocks Deterministas de RouterOS v7 (routeros\_v7\_payloads.py)**

Para que pytest-mock y httpx.MockTransport simulen fielmente un MikroTik con RouterOS v7 sin red real, AntiGravity DEBE implementar este catálogo en fastapi/tests/mocks/routeros\_v7\_payloads.py:


\# SPDX-License-Identifier: GPL-3.0-only


\# Copyright (C) 2026 RoSGrid Contributors


from typing import Any


MOCK\_SYSTEM\_RESOURCE: dict\[str, Any\] = \{


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


\}


MOCK\_SYSTEM\_ROUTERBOARD: dict\[str, Any\] = \{


    "routerboard": "true",


    "model": "RB4011iGS+",


    "serial-number": "D4460B123456",


    "firmware-type": "al2",


    "factory-firmware": "7.8",


    "current-firmware": "7.16.1",


    "upgrade-firmware": "7.16.1",


\}


MOCK\_SYSTEM\_HEALTH: list\[dict\[str, str\]\] = \[


    \{".id": "\*1", "name": "temperature", "value": "44", "type": "C"\},


    \{".id": "\*2", "name": "voltage", "value": "24.2", "type": "V"\},


\]


MOCK\_SFP\_MONITOR: list\[dict\[str, str\]\] = \[


    \{


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


    \}


\]


MOCK\_FIREWALL\_FILTER\_RULES: list\[dict\[str, str\]\] = \[


    \{


        ".id": "\*1",


        "chain": "input",


        "action": "accept",


        "connection-state": "established,related,untracked",


        "bytes": "98451200",


        "packets": "124500",


        "dynamic": "false",


        "invalid": "false",


        "disabled": "false",


        "comment": "Accept established/related",


    \},


    \{


        ".id": "\*2",


        "chain": "input",


        "action": "drop",


        "connection-state": "invalid",


        "bytes": "14200",


        "packets": "310",


        "dynamic": "false",


        "invalid": "false",


        "disabled": "false",


        "comment": "Drop invalid",


    \},


\]


MOCK\_BGP\_SESSIONS: list\[dict\[str, str\]\] = \[


    \{


        ".id": "\*3000001",


        "name": "ISP-Carrier-1-1",


        "remote.address": "186.10.20.1",


        "remote.as": "65001",


        "local.address": "186.10.20.2",


        "local.as": "65500",


        "established": "true",


        "uptime": "2w4d10h12m",


        "prefix-count": "942100",


    \}


\]




## **3. Reglas Anti-Mutantes para Aprobar mutmut (make qa-mutation)**

mutmut altera operadores (== por !=, \< por \<=, + por -, True por False, constantes numéricas y valores de retorno) en fastapi/src/. Para que **ningún mutante sobreviva**:


1. **Pruebas de Valores Límite Exactos (Boundary Value Analysis):**

   - En el monitor de salud (consecutive\_failures \>= 3 para declarar OFFLINE): escribe un test con failures = 2 (verifica que sigue ONLINE) y un test con failures = 3 (verifica que pasa exactamente a OFFLINE). Si solo pruebas con failures = 5, el mutante que cambia \>= 3 por \> 3 sobrevivirá.

   - En salud óptica SFP (sfp\_rx\_power\_dbm \>= -20.0 es OPTIMAL, \< -25.0 es CRITICAL\_LOW\_LIGHT): prueba exactamente con -20.0, -20.01, -25.0 y -25.01.

   - En bloqueo de login al 5.º intento fallido (failed\_login\_attempts \>= 5): prueba el intento 4 (no bloqueado) y el intento 5 (is\_locked == True).

2. **Verificación de Argumentos en Mocks (assert\_called\_once\_with):**

   - No uses únicamente mock\_fn.assert\_called(). Verifica los argumentos exactos pasados al conector de RouterOS, al logger de auditoría y a Redis (mock\_redis.set.assert\_awaited\_once\_with(...)).

3. **Verificación de AAD en Cifrado AES-256-GCM:**

   - Incluye un test que intente desencriptar la clave de un router cambiando el router\_id o tenant\_id en el AAD y verifica que lance InvalidTag. Esto mata cualquier mutante que altere la construcción del AAD.
