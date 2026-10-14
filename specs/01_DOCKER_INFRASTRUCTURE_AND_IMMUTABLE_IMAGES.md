# 01 — INFRAESTRUCTURA DOCKER, IMÁGENES INMUTABLES Y AUTO-MIGRACIÓN (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica la arquitectura de contenedores de **RoSGrid** tanto para despliegue (docker-compose.yml) como para su alineación con los entornos efímeros de QA (fastapi/docker-compose.qa.yml y vue3/docker-compose.qa.yml). Queda **TERMINANTEMENTE PROHIBIDO** crear archivos Dockerfile o usar docker build.




## **1. Catálogo de Imágenes Oficiales Inmutables**

Toda la infraestructura de RoSGrid DEBE operar consumiendo exclusivamente las siguientes imágenes preconstruidas (declaradas en los docker-compose.qa.yml del blueprint 11X y en el docker-compose.yml de producción):


| **Componente** | **Imagen Oficial Obligatoria** | **Propósito en RoSGrid** | **Volumen de Caché / Datos** |
| - | - | - | - |
| **Backend API & Workers** | sinfallas/base-python-uv:3.13 | Ejecución de FastAPI (Uvicorn), migraciones Alembic, workers asíncronos y suite QA Python | rosgrid\_uv\_cache:/root/.cache/uv |
| **Frontend Builder & QA** | sinfallas/base-node-ionic:22 *(o node:20-bookworm-slim en QA)* | Compilación de activos estáticos Vite/Vue 3 (dist/), Linting, Vitest y Stryker | rosgrid\_pnpm\_store:/pnpm |
| **Frontend Web Server** | nginx:alpine | Servidor HTTP de alta velocidad para el bundle compilado (vue3/dist) y proxy inverso | rosgrid\_nginx\_logs:/var/log/nginx |
| **Base de Datos Relacional** | postgres:17-alpine | Almacenamiento transaccional Multi-Tenant con RLS, bóveda AES-256-GCM, backups .rsc y auditoría inmutable | rosgrid\_pg\_data:/var/lib/postgresql/data |
| **Memoria & Estado Efímero** | redis:7-alpine | Idempotencia HTTP, sesiones activas (Kill-Switch), Pub/Sub de gráficas en vivo y estado del monitor | rosgrid\_redis\_data:/data |
| **Pruebas E2E / Visuales** | Imagen oficial Playwright (v1.43.0-jammy definida en vue3/docker-compose.qa.yml) | Ejecución de Playwright, @axe-core/playwright y Lighthouse CI (solo en QA) | rosgrid\_pnpm\_store:/pnpm |
| **Pruebas BDD Caja Negra** | sinfallas/karatelabs:latest | Escenarios funcionales Gherkin contra API y UI (solo en QA) | Bind mount ./test |
| **Seguridad Dinámica DAST** | owasp/zap2docker-stable:latest | Escaneo dinámico OWASP ZAP Baseline contra el backend vivo (solo en QA) | Bind mount .:/zap/wrk/:rw |
| **Ingeniería del Caos** | gaiaadm/pumba:latest | Inyección de latencia y jitter a nivel kernel con --profile chaos (solo en QA) | Socket Docker :ro |
| **Observabilidad** | prom/prometheus:latest + nginx/nginx-prometheus-exporter:latest | Recolección de métricas RED en /metrics (FastAPI) y /stub\_status (Nginx) | Efímero |
| **Contexto Semántico IA** | sinfallas/remote-graphify:latest | Servidor MCP en puerto 8080 bajo --profile graphify (solo en QA) | Bind mount .:/app |




## **2. Reglas de Red y Seguridad IaC (Cumplimiento Trivy auditar-infra.sh)**

Para superar la barrera pre-push (./auditar-infra.sh con aquasec/trivy:latest config . --severity HIGH,CRITICAL --exit-code 1), todos los archivos docker-compose\*.yml y scripts asociados DEBEN cumplir:


1. **IPv4 Estricto:**

   - Todas las redes declaradas en Docker Compose DEBEN usar driver: bridge.

   - Está **prohibido** incluir enable\_ipv6: true.

2. **Aislamiento de Privilegios Kernel (SYS\_PTRACE):**

   - Las directivas cap\_add: \[SYS\_PTRACE\] y security\_opt: \[seccomp:unconfined\] están **permitidas únicamente** en fastapi/docker-compose.qa.yml para permitir el profiling con py-spy.

   - En el archivo docker-compose.yml de producción/despliegue, está **prohibido** incluir SYS\_PTRACE, privileged: true o montar /var/run/docker.sock.

3. **Restricción de Puertos Expuestos en Producción:**

   - En docker-compose.yml, ni postgres ni redis deben exponer puertos al host (ports:). Solo se comunican dentro de la red interna rosgrid\_internal\_net.

   - Únicamente el contenedor frontal rosgrid-ui (Nginx) expone el puerto HTTP/HTTPS hacia el exterior, actuando como punto de entrada unificado.




## **3. Mecanismo de Migraciones Automáticas con Bloqueo Atómico (pg\_advisory\_lock)**

Uno de los requisitos fundamentales de **RoSGrid** es que **las migraciones de base de datos se ejecuten automáticamente al reiniciar después de una actualización**, garantizando que si se levantan múltiples workers o contenedores concurrentes no corrompan el esquema de PostgreSQL.

### **3.1 Especificación de fastapi/scripts/entrypoint.sh**

AntiGravity DEBE crear el script fastapi/scripts/entrypoint.sh (validado con shellcheck y shfmt) con la siguiente lógica exacta:


\#!/usr/bin/env bash


\# SPDX-License-Identifier: GPL-3.0-only


\# Copyright (C) 2026 RoSGrid Contributors


LC\_ALL=C


set -euo pipefail


echo "\[RoSGrid\] Sincronizando dependencias desde volumen uv-cache..."


uv pip install --system -e "."


echo "\[RoSGrid\] Verificando disponibilidad de PostgreSQL y ejecutando migraciones con pg\_advisory\_lock..."


python3 - \<\< 'PYEOF'


import os


import sys


import time


import subprocess


import psycopg


DB\_DSN = os.environ.get("ROSGRID\_SYNC\_DATABASE\_URL", "")


ADVISORY\_LOCK\_ID = 948271605  \# Identificador único de bloqueo para migraciones de RoSGrid


if not DB\_DSN:


    print("\[ERROR\] Variable ROSGRID\_SYNC\_DATABASE\_URL no definida.", file=sys.stderr)


    sys.exit(1)


for attempt in range(1, 31):


    try:


        with psycopg.connect(DB\_DSN, autocommit=True) as conn:


            with conn.cursor() as cur:


                print("\[RoSGrid\] Adquiriendo pg\_advisory\_lock para migraciones Alembic...")


                cur.execute("SELECT pg\_advisory\_lock(%s);", (ADVISORY\_LOCK\_ID,))


                try:


                    result = subprocess.run(\["alembic", "upgrade", "head"\], check=False)


                    if result.returncode != 0:


                        sys.exit(result.returncode)


                    print("\[RoSGrid\] Migraciones aplicadas exitosamente (head).")


                finally:


                    cur.execute("SELECT pg\_advisory\_unlock(%s);", (ADVISORY\_LOCK\_ID,))


        break


    except psycopg.OperationalError as exc:


        print(f"\[RoSGrid\] Esperando a PostgreSQL (intento \{attempt\}/30): \{exc\}")


        time.sleep(2)


else:


    print("\[ERROR\] No se pudo conectar a PostgreSQL tras 30 intentos.", file=sys.stderr)


    sys.exit(1)


PYEOF


echo "\[RoSGrid\] Iniciando servidor ASGI Uvicorn..."


exec uvicorn src.main:app \\


    --host 0.0.0.0 \\


    --port 8000 \\


    --proxy-headers \\


    --forwarded-allow-ips="\*"




## **4. Especificación Completa de docker-compose.yml (Despliegue RoSGrid)**

El archivo docker-compose.yml en la raíz del proyecto levantará la pila completa sin ningún Dockerfile, compilando la interfaz de Vue 3 en un contenedor de inicialización (rosgrid-ui-builder) que deposita los artefactos optimizados en un volumen compartido con nginx:alpine:


services:


  rosgrid-db:


    image: postgres:17-alpine


    container\_name: rosgrid\_db


    hostname: rosgrid\_db


    restart: unless-stopped


    environment:


      TZ: "America/Caracas"


      POSTGRES\_DB: "$\{POSTGRES\_DB:-rosgrid\}"


      POSTGRES\_USER: "$\{POSTGRES\_USER:-rosgrid\_user\}"


      POSTGRES\_PASSWORD: "$\{POSTGRES\_PASSWORD:?Debes definir POSTGRES\_PASSWORD en .env\}"


    volumes:


      - rosgrid\_pg\_data:/var/lib/postgresql/data


    healthcheck:


      test: \["CMD-SHELL", "pg\_isready -U $$\{POSTGRES\_USER:-rosgrid\_user\} -d $$\{POSTGRES\_DB:-rosgrid\}"\]


      interval: 5s


      timeout: 5s


      retries: 10


    networks:


      - rosgrid\_internal\_net


  rosgrid-redis:


    image: redis:7-alpine


    container\_name: rosgrid\_redis


    hostname: rosgrid\_redis


    restart: unless-stopped


    environment:


      TZ: "America/Caracas"


    command: \>


      redis-server


      --appendonly yes


      --maxmemory 512mb


      --maxmemory-policy volatile-lru


      --requirepass "$\{REDIS\_PASSWORD:?Debes definir REDIS\_PASSWORD en .env\}"


    volumes:


      - rosgrid\_redis\_data:/data


    healthcheck:


      test: \["CMD-SHELL", "redis-cli -a \\"$$\{REDIS\_PASSWORD\}\\" ping | grep PONG"\]


      interval: 5s


      timeout: 3s


      retries: 10


    networks:


      - rosgrid\_internal\_net


  rosgrid-api:


    image: sinfallas/base-python-uv:3.13


    container\_name: rosgrid\_api


    hostname: rosgrid\_api


    pull\_policy: always


    restart: unless-stopped


    depends\_on:


      rosgrid-db:


        condition: service\_healthy


      rosgrid-redis:


        condition: service\_healthy


    environment:


      TZ: "America/Caracas"


      UV\_CACHE\_DIR: "/root/.cache/uv"


      ROSGRID\_ENV: "$\{ROSGRID\_ENV:-production\}"


      ROSGRID\_DATABASE\_URL: "postgresql+asyncpg://$\{POSTGRES\_USER:-rosgrid\_user\}:$\{POSTGRES\_PASSWORD\}@rosgrid\_db:5432/$\{POSTGRES\_DB:-rosgrid\}"


      ROSGRID\_SYNC\_DATABASE\_URL: "postgresql://$\{POSTGRES\_USER:-rosgrid\_user\}:$\{POSTGRES\_PASSWORD\}@rosgrid\_db:5432/$\{POSTGRES\_DB:-rosgrid\}"


      ROSGRID\_REDIS\_URL: "redis://:$\{REDIS\_PASSWORD\}@rosgrid\_redis:6379/0"


      ROSGRID\_MASTER\_VAULT\_KEY: "$\{ROSGRID\_MASTER\_VAULT\_KEY:?Debes definir ROSGRID\_MASTER\_VAULT\_KEY (32 bytes base64)\}"


      ROSGRID\_JWT\_SECRET\_KEY: "$\{ROSGRID\_JWT\_SECRET\_KEY:?Debes definir ROSGRID\_JWT\_SECRET\_KEY\}"


      ROSGRID\_CSRF\_HMAC\_SECRET: "$\{ROSGRID\_CSRF\_HMAC\_SECRET:?Debes definir ROSGRID\_CSRF\_HMAC\_SECRET\}"


    volumes:


      - ./fastapi:/app


      - rosgrid\_uv\_cache:/root/.cache/uv


      - rosgrid\_backups\_storage:/var/lib/rosgrid/backups


    working\_dir: /app


    command: \["bash", "/app/scripts/entrypoint.sh"\]


    healthcheck:


      test: \["CMD-SHELL", "curl -fsS http://localhost:8000/health || exit 1"\]


      interval: 10s


      timeout: 5s


      retries: 5


    networks:


      - rosgrid\_internal\_net


  rosgrid-worker:


    image: sinfallas/base-python-uv:3.13


    container\_name: rosgrid\_worker


    hostname: rosgrid\_worker


    pull\_policy: always


    restart: unless-stopped


    depends\_on:


      rosgrid-api:


        condition: service\_healthy


    environment:


      TZ: "America/Caracas"


      UV\_CACHE\_DIR: "/root/.cache/uv"


      ROSGRID\_ENV: "$\{ROSGRID\_ENV:-production\}"


      ROSGRID\_DATABASE\_URL: "postgresql+asyncpg://$\{POSTGRES\_USER:-rosgrid\_user\}:$\{POSTGRES\_PASSWORD\}@rosgrid\_db:5432/$\{POSTGRES\_DB:-rosgrid\}"


      ROSGRID\_REDIS\_URL: "redis://:$\{REDIS\_PASSWORD\}@rosgrid\_redis:6379/0"


      ROSGRID\_MASTER\_VAULT\_KEY: "$\{ROSGRID\_MASTER\_VAULT\_KEY\}"


    volumes:


      - ./fastapi:/app


      - rosgrid\_uv\_cache:/root/.cache/uv


      - rosgrid\_backups\_storage:/var/lib/rosgrid/backups


    working\_dir: /app


    command: \["bash", "-c", "uv pip install --system -e . && python3 -m src.workers.runner"\]


    networks:


      - rosgrid\_internal\_net


  rosgrid-ui-builder:


    image: sinfallas/base-node-ionic:22


    container\_name: rosgrid\_ui\_builder


    hostname: rosgrid\_ui\_builder


    pull\_policy: if\_not\_present


    environment:


      TZ: "America/Caracas"


      PNPM\_HOME: "/pnpm"


    volumes:


      - ./vue3:/app


      - rosgrid\_pnpm\_store:/pnpm


      - rosgrid\_ui\_dist:/app/dist


    working\_dir: /app


    command: \["bash", "-c", "pnpm install --frozen-lockfile=false && pnpm run build"\]


    networks:


      - rosgrid\_internal\_net


  rosgrid-ui:


    image: nginx:alpine


    container\_name: rosgrid\_ui


    hostname: rosgrid\_ui


    restart: unless-stopped


    depends\_on:


      rosgrid-ui-builder:


        condition: service\_completed\_successfully


      rosgrid-api:


        condition: service\_healthy


    environment:


      TZ: "America/Caracas"


    volumes:


      - rosgrid\_ui\_dist:/usr/share/nginx/html:ro


      - ./vue3/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro


      - rosgrid\_nginx\_logs:/var/log/nginx


    ports:


      - "$\{ROSGRID\_HTTP\_PORT:-8080\}:80"


    networks:


      - rosgrid\_internal\_net


networks:


  rosgrid\_internal\_net:


    driver: bridge


volumes:


  rosgrid\_pg\_data:


    name: rosgrid\_pg\_data


  rosgrid\_redis\_data:


    name: rosgrid\_redis\_data


  rosgrid\_uv\_cache:


    name: fastapi\_uv\_cache


  rosgrid\_pnpm\_store:


    name: vue3\_pnpm\_store\_cache


  rosgrid\_ui\_dist:


    name: rosgrid\_ui\_dist


  rosgrid\_backups\_storage:


    name: rosgrid\_backups\_storage


  rosgrid\_nginx\_logs:


    name: rosgrid\_nginx\_logs




## **5. Plantilla Obligatoria .env.example**

AntiGravity DEBE crear el archivo .env.example en la raíz del proyecto usando exclusivamente marcadores ficticios (para no activar jamás la regla leaks-check de lefthook.yml):


\# ==============================================================================


\# RoSGrid - Plantilla de Variables de Entorno (.env.example)


\# Licencia: GPL-3.0-only


\# ADVERTENCIA: Nunca hagas commit de un archivo .env real.


\# ==============================================================================


ROSGRID\_ENV=production


ROSGRID\_HTTP\_PORT=8080


\# --- PostgreSQL 17 ---


POSTGRES\_DB=rosgrid


POSTGRES\_USER=rosgrid\_user


POSTGRES\_PASSWORD=cambiar\_en\_entorno\_local


\# --- Redis 7 ---


REDIS\_PASSWORD=cambiar\_en\_entorno\_local


\# --- Criptografía y Seguridad (Generar con: openssl rand -base64 32) ---


ROSGRID\_MASTER\_VAULT\_KEY=reemplazar\_con\_32\_bytes\_base64\_para\_aes\_256\_gcm


ROSGRID\_JWT\_SECRET\_KEY=reemplazar\_con\_secreto\_criptografico\_jwt


ROSGRID\_CSRF\_HMAC\_SECRET=reemplazar\_con\_secreto\_criptografico\_csrf


\# --- Parámetros Operativos MikroTik ---


ROSGRID\_MIKROTIK\_TIMEOUT\_SECONDS=10


ROSGRID\_SAFEMODE\_ROLLBACK\_SECONDS=60


ROSGRID\_BACKUP\_RETENTION\_DAYS=30




## **6. Configuración de Nginx (vue3/nginx/default.conf) Compatible con OWASP ZAP y Observabilidad**

Para que el contenedor nginx:alpine pase tanto la auditoría DAST de **OWASP ZAP** (cabeceras de seguridad estrictas) como la recolección de métricas de nginx-prometheus-exporter (/stub\_status), AntiGravity DEBE escribir vue3/nginx/default.conf con esta especificación:


server \{


    listen 80;


    server\_name \_;


    server\_tokens off;


    root /usr/share/nginx/html;


    index index.html;


    \# Cabeceras de Seguridad Obligatorias (Certificación DAST OWASP ZAP)


    add\_header X-Frame-Options "DENY" always;


    add\_header X-Content-Type-Options "nosniff" always;


    add\_header Referrer-Policy "strict-origin-when-cross-origin" always;


    add\_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;


    add\_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' ws: wss:; frame-ancestors 'none'; base-uri 'self'; form-action 'self';" always;


    \# Endpoint interno para nginx-prometheus-exporter (Nivel 11X)


    location = /stub\_status \{


        stub\_status;


        allow 127.0.0.1;


        allow 172.16.0.0/12;


        allow 192.168.0.0/16;


        allow 10.0.0.0/8;


        deny all;


    \}


    \# Proxy inverso hacia FastAPI (REST API)


    location /api/ \{


        proxy\_pass http://rosgrid-api:8000/api/;


        proxy\_http\_version 1.1;


        proxy\_set\_header Host $host;


        proxy\_set\_header X-Real-IP $remote\_addr;


        proxy\_set\_header X-Forwarded-For $proxy\_add\_x\_forwarded\_for;


        proxy\_set\_header X-Forwarded-Proto $scheme;


    \}


    \# Proxy inverso para WebSockets (Gráficas en Vivo WinBox y Notificaciones NOC)


    location /ws/ \{


        proxy\_pass http://rosgrid-api:8000/ws/;


        proxy\_http\_version 1.1;


        proxy\_set\_header Upgrade $http\_upgrade;


        proxy\_set\_header Connection "upgrade";


        proxy\_set\_header Host $host;


        proxy\_set\_header X-Real-IP $remote\_addr;


        proxy\_read\_timeout 3600s;


    \}


    \# Soporte de enrutamiento HTML5 History Mode para Vue Router


    location / \{


        try\_files $uri $uri/ /index.html;


    \}


\}
