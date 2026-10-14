# 09 — FASE 1 BACKEND: ESQUELETO FASTAPI, FUSIÓN 11X, OBSERVABILIDAD (/metrics) Y AUTO-MIGRACIONES (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento guía paso a paso la construcción de la **Fase 1 del Backend (fastapi/)**. Debes ejecutar primero el **Paso 0 (Graphify MCP)** y realizar la **Fusión Quirúrgica No Destructiva** de pyproject.toml.example, tox.ini.example, Makefile.example y gitignore.example antes de escribir el código de src/. Todo el código generado DEBE tener tipado estricto (mypy --strict), complejidad ciclomática Grado A (Radon CC \<= 5) y cobertura unitaria \>= 95%.




## **1. Paso 0 y Fusión Quirúrgica de fastapi/pyproject.toml**

AntiGravity DEBE fusionar las dependencias de producción de **RoSGrid** con las dependencias dev obligatorias del blueprint 11X en fastapi/pyproject.toml:


\[project\]


name = "rosgrid-backend"


version = "1.0.0"


description = "Backend Centralizado Multi-Tenant para Gestión de Flotas MikroTik RouterOS v7+ (GPL-3.0-only)"


license = \{ text = "GPL-3.0-only" \}


requires-python = "\>=3.13"


dependencies = \[


    "fastapi\>=0.115.0",


    "uvicorn\[standard\]\>=0.30.0",


    "python-dotenv\>=1.0.1",


    "pydantic\>=2.9.0",


    "pydantic-settings\>=2.5.0",


    "sqlalchemy\[asyncio\]\>=2.0.35",


    "asyncpg\>=0.29.0",


    "psycopg\[binary\]\>=3.2.0",


    "alembic\>=1.13.3",


    "redis\>=5.1.0",


    "httpx\>=0.27.2",


    "cryptography\>=43.0.1",


    "argon2-cffi\>=23.1.0",


    "pyotp\>=2.9.0",


    "PyJWT\>=2.9.0",


    "python-multipart\>=0.0.12"


\]


\[project.optional-dependencies\]


dev = \[


    "pytest\>=8.3.0",


    "pytest-asyncio\>=0.24.0",


    "pytest-cov\>=5.0.0",


    "pytest-mock\>=3.14.0",


    "ruff\>=0.6.0",


    "mypy\>=1.11.0",


    "tox\>=4.18.0",


    "tox-uv\>=1.16.0",


    "bandit\>=1.7.9",


    "mutmut\>=2.5.0",


    "radon\>=6.0.1",


    "py-spy\>=0.3.14",


    "schemathesis\>=3.36.0",


    "locust\>=2.31.0",


    "prometheus-fastapi-instrumentator\>=7.0.0",


    "prometheus-client\>=0.21.0"


\]


\[build-system\]


requires = \["hatchling"\]


build-backend = "hatchling.build"


\[tool.pytest.ini\_options\]


asyncio\_mode = "auto"


testpaths = \["tests"\]


python\_files = \["\*.unit.py", "\*.spec.py"\]


addopts = "--strict-markers --cov=src/ --cov-report=html --cov-report=term-missing"


markers = \[


    "integration: Pruebas internas que requieren servicios reales (deseleccionar en unitarias con '-m \\"not integration\\"')",


\]


\[tool.ruff\]


line-length = 120


target-version = "py313"


\[tool.mypy\]


strict = true


plugins = \["pydantic.mypy"\]


\[tool.mutmut\]


paths\_to\_mutate = "src/"


backup = false


runner = "python -m pytest -x"


tests\_dir = "tests/"




## **2. Instrumentación Obligatoria de Observabilidad y Punto de Entrada (fastapi/src/main.py)**

El archivo fastapi/src/main.py DEBE exponer innegociablemente el endpoint /metrics con prometheus-fastapi-instrumentator y el endpoint /health (validado tanto por el healthcheck de Docker como por Karate Labs en api\_test.feature):


\# SPDX-License-Identifier: GPL-3.0-only


\# Copyright (C) 2026 RoSGrid Contributors


from fastapi import FastAPI


from prometheus\_fastapi\_instrumentator import Instrumentator


from src.api.router import api\_v1\_router


from src.core.csrf import CSRFProtectionMiddleware


from src.core.security\_headers import SecurityHeadersMiddleware


from src.redis\_layer.idempotency import IdempotencyMiddleware



def create\_app() -\> FastAPI:


    app = FastAPI(


        title="RoSGrid API",


        version="1.0.0",


        description="Consola Centralizada Multi-Tenant para MikroTik RouterOS v7+",


        docs\_url="/api/docs",


        openapi\_url="/openapi.json",


    )


    \# 1. Observabilidad Innegociable (Estándar 11X)


    Instrumentator().instrument(app).expose(app)


    \# 2. Middlewares de Seguridad e Idempotencia (Orden estricto)


    app.add\_middleware(SecurityHeadersMiddleware)


    app.add\_middleware(IdempotencyMiddleware)


    app.add\_middleware(CSRFProtectionMiddleware)


    \# 3. Ruta de Salud Estandarizada (Requerida por Karate Labs y Docker Healthcheck)


    @app.get("/health", tags=\["Health"\])


    async def health\_check() -\> dict\[str, str\]:


        return \{"status": "healthy"\}


    \# 4. Montaje de Routers de Negocio v1


    app.include\_router(api\_v1\_router, prefix="/api/v1")


    return app



app = create\_app()




## **3. Paso a Paso de Construcción de la Fase 1 para AntiGravity**

AntiGravity DEBE crear los siguientes módulos base en orden secuencial, creando inmediatamente después su archivo de prueba unitaria .unit.py:

### **Paso 1.1: Configuración Tipada (fastapi/src/core/config.py)**

- Usa pydantic\_settings.BaseSettings para cargar:

  - rosgrid\_env, rosgrid\_database\_url, rosgrid\_sync\_database\_url, rosgrid\_redis\_url.

  - rosgrid\_master\_vault\_key (valida que al decodificar de Base64 tenga exactamente 32 bytes para AES-256-GCM).

  - rosgrid\_jwt\_secret\_key y rosgrid\_csrf\_hmac\_secret.

  - rosgrid\_mikrotik\_timeout\_seconds (default=10), rosgrid\_safemode\_rollback\_seconds (default=60), rosgrid\_backup\_retention\_days (default=30).

### **Paso 1.2: Motor Criptográfico de Bóveda (fastapi/src/core/crypto.py)**

- Funciones puras y deterministas (CC \<= 3):

  - encrypt\_aes\_gcm(plaintext: str, aad: str, master\_key: bytes) -\> tuple\[bytes, bytes, bytes\] (devuelve ciphertext, iv\_12b, tag\_16b).

  - decrypt\_aes\_gcm(ciphertext: bytes, iv: bytes, tag: bytes, aad: str, master\_key: bytes) -\> str.

  - hash\_password\_argon2(password: str) -\> str y verify\_password\_argon2(password: str, password\_hash: str) -\> bool.

### **Paso 1.3: Motor de Auditoría Inmutable con Hash-Chain (fastapi/src/core/audit.py)**

- Servicio AuditLoggerService:

  - Sanitiza automáticamente cualquier clave del diccionario (password, secret, totp\_code, current\_password) reemplazándola por "\[REDACTED\]" antes de serializar before\_state y after\_state.

  - Obtiene el record\_sha256\_hash del último registro del mismo tenant\_id (o "0" \* 64 si es el registro génesis del Tenant).

  - Calcula record\_sha256\_hash = sha256(f"\{prev\_hash\}:\{tenant\_id\}:\{actor\_user\_id\}:\{event\_action\}:\{created\_at\_iso\}:\{after\_state\_json\}").

  - Inserta en audit\_logs.

### **Paso 1.4: Configuración de Alembic y Migraciones Automáticas (fastapi/migrations/)**

- Configura migrations/env.py para leer ROSGRID\_SYNC\_DATABASE\_URL desde el entorno.

- Crea las 3 migraciones iniciales correspondientes a los esquemas definidos en los documentos 02, 03 y 04:

  1. 0001\_core\_tenants\_users\_rls.py

  2. 0002\_inventory\_vault\_maintenance.py

  3. 0003\_operations\_backups\_immutable\_audit.py




## **4. Criterio de Aceptación de la Fase 1 (Gate 11X)**

Antes de avanzar a los endpoints del documento 10, AntiGravity DEBE ejecutar:


2. make qa-lint -\> 0 errores en ruff check, mypy --strict y radon cc --min C.

3. make qa-unit -\> Cobertura \>= 95% sobre config.py, crypto.py, csrf.py, security\_headers.py, idempotency.py, audit.py y main.py usando exclusivamente pytest-mock.
