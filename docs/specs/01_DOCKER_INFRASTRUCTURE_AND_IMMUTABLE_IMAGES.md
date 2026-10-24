# 01 — INFRAESTRUCTURA DOCKER, IMÁGENES INMUTABLES, AUTO-MIGRACIÓN Y PUBLICACIÓN DOCKER HUB (RoSGrid)

**[DIRECTIVA PARA ANTIGRAVITY]:** Este documento especifica la arquitectura de contenedores de **RoSGrid** en tres niveles:
1. **Entornos Efímeros de QA (`fastapi/docker-compose.qa.yml` y `vue3/docker-compose.qa.yml`):** Consumen exclusivamente las imágenes base inmutables del estándar 11X. Está **TERMINANTEMENTE PROHIBIDO** usar `Dockerfile` personalizados dentro de `docker-compose.qa.yml`.
2. **Entorno Local / Laboratorio (`docker-compose.yml`):** Ejecuta el stack completo montando el código fuente sobre las imágenes oficiales.
3. **Imágenes de Producción para Docker Hub (`fastapi/Dockerfile`, `vue3/Dockerfile`, `docker-compose.prod.yml` y `build.sh`):** Construyen y publican las imágenes oficiales inmutables `sinfallas/rosgrid-backend:latest` y `sinfallas/rosgrid-frontend:latest` mediante `docker buildx` (especificadas en la **Sección 7**).

---

## 1. Catálogo de Imágenes Oficiales Inmutables

Toda la infraestructura de RoSGrid DEBE operar consumiendo exclusivamente las siguientes imágenes base y de producción:

| Componente | Imagen Oficial Obligatoria | Propósito en RoSGrid | Volumen de Caché / Datos |
| :--- | :--- | :--- | :--- |
| **Backend Base & QA** | `sinfallas/base-python-uv:3.15` | Base para `fastapi/Dockerfile`, ejecución local de FastAPI (Uvicorn + `uvloop`), migraciones Alembic, workers asíncronos y suite QA Python | `rosgrid_uv_cache:/root/.cache/uv` |
| **Frontend Builder & QA** | `sinfallas/base-node-ionic:26` | Etapa builder de `vue3/Dockerfile`, compilación de activos estáticos Vite/Vue 3 (`dist/`), Linting, Vitest y Stryker en `vue3/docker-compose.qa.yml` | `rosgrid_pnpm_store:/pnpm` |
| **Frontend Web Server** | `nginx:1.27-alpine` / `nginx:alpine` | Base runtime de `vue3/Dockerfile`, servidor HTTP de alta velocidad para el bundle compilado (`vue3/dist`) y proxy inverso | `rosgrid_nginx_logs:/var/log/nginx` |
| **Imagen Producción Backend** | `sinfallas/rosgrid-backend:latest` | Imagen oficial inmutable de producción publicada en Docker Hub mediante `./scripts/build.sh` | `rosgrid_backups_storage:/var/lib/rosgrid/backups` |
| **Imagen Producción Frontend** | `sinfallas/rosgrid-frontend:latest` | Imagen oficial inmutable de producción (Nginx + SPA compilada) publicada en Docker Hub mediante `./scripts/build.sh` | `rosgrid_nginx_logs:/var/log/nginx` |
| **Base de Datos Relacional** | `postgres:17-alpine` | Almacenamiento transaccional Multi-Tenant con RLS, bóveda AES-256-GCM, backups `.rsc` y auditoría inmutable WORM con índice `BRIN` | `rosgrid_pg_data:/var/lib/postgresql/data` |
| **Memoria & Estado Efímero (Predeterminado)** | `eqalpha/keydb:alpine` | Motor en memoria **Multi-Hilo (`--server-threads 2`)** para Idempotencia HTTP, sesiones activas (Kill-Switch), Pub/Sub de gráficas en vivo y pipelines del monitor (~35 MB RAM) | `rosgrid_redis_data:/data` |
| **Memoria Alta Escala (Perfil Opcional ISP)** | `docker.dragonflydb.io/dragonflydb/dragonfly:latest` | Motor *Shared-Nothing* sobre `io_uring` opcional para flotas masivas (> 300–500 routers MikroTik en servidores de 16 GB+ RAM) | `rosgrid_redis_data:/data` |
| **Pruebas E2E / Visuales** | Imagen oficial Playwright (`v1.43.0-jammy` definida en `vue3/docker-compose.qa.yml`) | Ejecución de Playwright, `@axe-core/playwright` y Lighthouse CI (solo en QA) | `rosgrid_pnpm_store:/pnpm` |
| **Pruebas BDD Caja Negra** | `sinfallas/karatelabs:latest` | Escenarios funcionales Gherkin contra API y UI (solo en QA) | Bind mount `./test` |
| **Seguridad Dinámica DAST** | `owasp/zap2docker-stable:latest` | Escaneo dinámico OWASP ZAP Baseline contra el backend vivo (solo en QA) | Bind mount `.:/zap/wrk/:rw` |
| **Ingeniería del Caos** | `gaiaadm/pumba:latest` | Inyección de latencia y jitter a nivel kernel con `--profile chaos` (solo en QA) | Socket Docker `:ro` |
| **Observabilidad** | `prom/prometheus:latest` + `nginx/nginx-prometheus-exporter:latest` | Recolección de métricas RED en `/metrics` (FastAPI) y `/stub_status` (Nginx) | Efímero |
| **Contexto Semántico IA** | `sinfallas/remote-graphify:latest` | Extracción de grafos AST bajo `--profile graphify` (solo en QA) | Bind mount `.:/app` |

---

## 2. Reglas de Red y Seguridad IaC (Cumplimiento Trivy `scripts/auditar-infra.sh`)

Para superar la barrera pre-push (`./scripts/auditar-infra.sh` con `aquasec/trivy:latest config . --severity HIGH,CRITICAL --exit-code 1`), todos los archivos `docker-compose*.yml`, `Dockerfile` y scripts asociados DEBEN cumplir:

1. **IPv4 Estricto:**
   - Todas las redes declaradas en Docker Compose DEBEN usar `driver: bridge`.
   - Está **prohibido** incluir `enable_ipv6: true`.
2. **Aislamiento de Privilegios Kernel (`SYS_PTRACE`):**
   - Las directivas `cap_add: [SYS_PTRACE]` y `security_opt: [seccomp:unconfined]` están **permitidas únicamente** en `fastapi/docker-compose.qa.yml` para permitir el profiling con `py-spy`.
   - En los archivos `docker-compose.yml` y `docker-compose.prod.yml`, está **prohibido** incluir `SYS_PTRACE`, `privileged: true` o montar `/var/run/docker.sock`.
3. **Ejecución sin Privilegios (`USER non-root`) en `Dockerfile`:**
   - Tanto `fastapi/Dockerfile` como `vue3/Dockerfile` DEBEN declarar explícitamente un usuario sin privilegios (`USER rosgrid` / `USER nginx`) y una instrucción `HEALTHCHECK` para cumplir las reglas `DS002` y `DS026` de Trivy IaC.
4. **Restricción de Puertos Expuestos en Producción:**
   - En `docker-compose.yml` y `docker-compose.prod.yml`, ni `postgres` ni `rosgrid-redis` (KeyDB) deben exponer puertos al host (`ports:`). Solo se comunican dentro de la red interna `rosgrid_internal_net`.
   - Únicamente el contenedor frontal `rosgrid-ui` (Nginx) expone el puerto HTTP/HTTPS hacia el exterior, actuando como punto de entrada unificado.

---

## 3. Mecanismo de Migraciones Automáticas con Bloqueo Atómico (`pg_advisory_lock`) y Arranque `uvloop`

Uno de los requisitos fundamentales de **RoSGrid** es que **las migraciones de base de datos se ejecuten automáticamente al reiniciar después de una actualización**, garantizando que si se levantan múltiples workers o contenedores concurrentes no corrompan el esquema de PostgreSQL.

### 3.1 Especificación de `fastapi/scripts/entrypoint.sh`

Antigravity DEBE crear o actualizar el script `fastapi/scripts/entrypoint.sh` (validado con `shellcheck` y `shfmt`) con la siguiente lógica exacta (incluyendo `--loop uvloop --http httptools` en el arranque de Uvicorn):

~~~bash
#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

LC_ALL=C
set -euo pipefail

if [[ "${ROSGRID_IMAGE_PREBUILT:-0}" != "1" ]]; then
    echo "[RoSGrid] Sincronizando dependencias desde volumen uv-cache..."
    uv pip install --system -e "."
else
    echo "[RoSGrid] Imagen de produccion precompilada detectada. Omitiendo uv sync en runtime."
fi

echo "[RoSGrid] Verificando disponibilidad de PostgreSQL y ejecutando migraciones con pg_advisory_lock..."
python3 - << 'PYEOF'
import os
import sys
import time
import subprocess
import psycopg

DB_DSN = os.environ.get("ROSGRID_SYNC_DATABASE_URL", "")
ADVISORY_LOCK_ID = 948271605  # Identificador unico de bloqueo para migraciones de RoSGrid

if not DB_DSN:
    print("[ERROR] Variable ROSGRID_SYNC_DATABASE_URL no definida.", file=sys.stderr)
    sys.exit(1)

for attempt in range(1, 31):
    try:
        with psycopg.connect(DB_DSN, autocommit=True) as conn:
            with conn.cursor() as cur:
                print("[RoSGrid] Adquiriendo pg_advisory_lock para migraciones Alembic...")
                cur.execute("SELECT pg_advisory_lock(%s);", (ADVISORY_LOCK_ID,))
                try:
                    result = subprocess.run(["alembic", "upgrade", "head"], check=False)
                    if result.returncode != 0:
                        sys.exit(result.returncode)
                    print("[RoSGrid] Migraciones aplicadas exitosamente (head).")
                finally:
                    cur.execute("SELECT pg_advisory_unlock(%s);", (ADVISORY_LOCK_ID,))
        break
    except psycopg.OperationalError as exc:
        print(f"[RoSGrid] Esperando a PostgreSQL (intento {attempt}/30): {exc}")
        time.sleep(2)
else:
    print("[ERROR] No se pudo conectar a PostgreSQL tras 30 intentos.", file=sys.stderr)
    sys.exit(1)
PYEOF

echo "[RoSGrid] Iniciando servidor ASGI Uvicorn de alto rendimiento (uvloop + httptools)..."
exec uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --loop uvloop \
    --http httptools \
    --proxy-headers \
    --forwarded-allow-ips="*"
~~~

---

## 4. Especificación Completa de `docker-compose.yml` (Entorno Local / Laboratorio EVE-NG con KeyDB Multi-Hilo)

El archivo `docker-compose.yml` en la raíz del proyecto levanta la pila completa utilizando **KeyDB Multi-Hilo (`eqalpha/keydb:alpine`)** por defecto (manteniendo el nombre de servicio `rosgrid-redis` para transparencia con `ROSGRID_REDIS_URL`):

~~~yaml
services:
  rosgrid-db:
    image: postgres:17-alpine
    container_name: rosgrid_db
    hostname: rosgrid_db
    restart: unless-stopped
    environment:
      TZ: "America/Caracas"
      POSTGRES_DB: "${POSTGRES_DB:-rosgrid}"
      POSTGRES_USER: "${POSTGRES_USER:-rosgrid_user}"
      POSTGRES_PASSWORD: "${POSTGRES_PASSWORD:?Debes definir POSTGRES_PASSWORD en .env}"
    volumes:
      - rosgrid_pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER:-rosgrid_user} -d$${POSTGRES_DB:-rosgrid}"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - rosgrid_internal_net

  rosgrid-redis:
    image: eqalpha/keydb:alpine
    container_name: rosgrid_redis
    hostname: rosgrid-redis
    restart: unless-stopped
    environment:
      TZ: "America/Caracas"
    command: >
      keydb-server
      --server-threads 2
      --appendonly no
      --save ""
      --maxmemory 512mb
      --maxmemory-policy volatile-lru
      --requirepass "${REDIS_PASSWORD:?Debes definir REDIS_PASSWORD en .env}" volumes: - rosgrid_redis_data:/data healthcheck: test: ["CMD-SHELL", "keydb-cli -a \"$${REDIS_PASSWORD}\" ping | grep PONG"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - rosgrid_internal_net

  # --- PERFIL OPCIONAL DE ALTO RENDIMIENTO PARA GRANDES FLOTAS ISP (>300 ROUTERS / 16GB+ RAM): DRAGONFLYDB ---
  # Para activarlo en servidores dedicados, reemplaza el bloque rosgrid-redis anterior por:
  # rosgrid-redis:
  #   image: docker.dragonflydb.io/dragonflydb/dragonfly:latest
  #   container_name: rosgrid_redis
  #   hostname: rosgrid-redis
  #   restart: unless-stopped
  #   ulimits:
  #     memlock: -1
  #   command: >
  #     dragonfly
  #     --proactor_threads=4
  #     --maxmemory=2gb
  #     --requirepass=${REDIS_PASSWORD} #     --alsologtostderr #   volumes: #     - rosgrid_redis_data:/data #   healthcheck: #     test: ["CMD-SHELL", "redis-cli -a \"$${REDIS_PASSWORD}\" ping | grep PONG"]
  #     interval: 10s
  #     timeout: 5s
  #     retries: 5
  #   networks:
  #     - rosgrid_internal_net

  rosgrid-api:
    image: sinfallas/base-python-uv:3.15
    container_name: rosgrid_api
    hostname: rosgrid_api
    pull_policy: always
    restart: unless-stopped
    depends_on:
      rosgrid-db:
        condition: service_healthy
      rosgrid-redis:
        condition: service_healthy
    environment:
      TZ: "America/Caracas"
      UV_CACHE_DIR: "/root/.cache/uv"
      ROSGRID_ENV: "${ROSGRID_ENV:-production}"
      ROSGRID_DATABASE_URL: "postgresql+asyncpg://${POSTGRES_USER:-rosgrid_user}:${POSTGRES_PASSWORD}@rosgrid_db:5432/${POSTGRES_DB:-rosgrid}"
      ROSGRID_SYNC_DATABASE_URL: "postgresql://${POSTGRES_USER:-rosgrid_user}:${POSTGRES_PASSWORD}@rosgrid_db:5432/${POSTGRES_DB:-rosgrid}"
      ROSGRID_REDIS_URL: "redis://:${REDIS_PASSWORD}@rosgrid_redis:6379/0"
      ROSGRID_MASTER_VAULT_KEY: "${ROSGRID_MASTER_VAULT_KEY:?Debes definir ROSGRID_MASTER_VAULT_KEY (32 bytes base64)}"
      ROSGRID_JWT_SECRET_KEY: "${ROSGRID_JWT_SECRET_KEY:?Debes definir ROSGRID_JWT_SECRET_KEY}"
      ROSGRID_CSRF_HMAC_SECRET: "${ROSGRID_CSRF_HMAC_SECRET:?Debes definir ROSGRID_CSRF_HMAC_SECRET}"
    volumes:
      - ./fastapi:/app
      - rosgrid_uv_cache:/root/.cache/uv
      - rosgrid_backups_storage:/var/lib/rosgrid/backups
    working_dir: /app
    command: ["bash", "/app/scripts/entrypoint.sh"]
    healthcheck:
      test: ["CMD-SHELL", "curl -fsS http://localhost:8000/health || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - rosgrid_internal_net

  rosgrid-worker:
    image: sinfallas/base-python-uv:3.15
    container_name: rosgrid_worker
    hostname: rosgrid_worker
    pull_policy: always
    restart: unless-stopped
    depends_on:
      rosgrid-api:
        condition: service_healthy
    environment:
      TZ: "America/Caracas"
      UV_CACHE_DIR: "/root/.cache/uv"
      ROSGRID_ENV: "${ROSGRID_ENV:-production}"
      ROSGRID_DATABASE_URL: "postgresql+asyncpg://${POSTGRES_USER:-rosgrid_user}:${POSTGRES_PASSWORD}@rosgrid_db:5432/${POSTGRES_DB:-rosgrid}"
      ROSGRID_REDIS_URL: "redis://:${REDIS_PASSWORD}@rosgrid_redis:6379/0"
      ROSGRID_MASTER_VAULT_KEY: "${ROSGRID_MASTER_VAULT_KEY}"
    volumes:
      - ./fastapi:/app
      - rosgrid_uv_cache:/root/.cache/uv
      - rosgrid_backups_storage:/var/lib/rosgrid/backups
    working_dir: /app
    command: ["bash", "-c", "uv pip install --system -e . && python3 -m src.workers.runner"]
    networks:
      - rosgrid_internal_net

  rosgrid-ui-builder:
    image: sinfallas/base-node-ionic:26
    container_name: rosgrid_ui_builder
    hostname: rosgrid_ui_builder
    pull_policy: if_not_present
    environment:
      TZ: "America/Caracas"
      PNPM_HOME: "/pnpm"
    volumes:
      - ./vue3:/app
      - rosgrid_pnpm_store:/pnpm
      - rosgrid_ui_dist:/app/dist
    working_dir: /app
    command: ["bash", "-c", "pnpm install --frozen-lockfile=false && pnpm run build"]
    networks:
      - rosgrid_internal_net

  rosgrid-ui:
    image: nginx:alpine
    container_name: rosgrid_ui
    hostname: rosgrid_ui
    restart: unless-stopped
    depends_on:
      rosgrid-ui-builder:
        condition: service_completed_successfully
      rosgrid-api:
        condition: service_healthy
    environment:
      TZ: "America/Caracas"
    volumes:
      - rosgrid_ui_dist:/usr/share/nginx/html:ro
      - ./vue3/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
      - rosgrid_nginx_logs:/var/log/nginx
    ports:
      - "${ROSGRID_HTTP_PORT:-8080}:80"
    networks:
      - rosgrid_internal_net

networks:
  rosgrid_internal_net:
    driver: bridge

volumes:
  rosgrid_pg_data:
    name: rosgrid_pg_data
  rosgrid_redis_data:
    name: rosgrid_redis_data
  rosgrid_uv_cache:
    name: fastapi_uv_cache
  rosgrid_pnpm_store:
    name: vue3_pnpm_store_cache
  rosgrid_ui_dist:
    name: rosgrid_ui_dist
  rosgrid_backups_storage:
    name: rosgrid_backups_storage
  rosgrid_nginx_logs:
    name: rosgrid_nginx_logs
~~~

---

## 5. Plantilla Obligatoria `.env.example`

Antigravity DEBE mantener el archivo `.env.example` en la raíz del proyecto usando exclusivamente marcadores ficticios (para no activar jamás la regla `leaks-check` de `lefthook.yml`):

~~~dotenv
# ==============================================================================
# RoSGrid - Plantilla de Variables de Entorno (.env.example)
# Licencia: GPL-3.0-only
# ADVERTENCIA: Nunca hagas commit de un archivo .env real.
# ==============================================================================

ROSGRID_ENV=production
ROSGRID_HTTP_PORT=8080

# --- PostgreSQL 17 ---
POSTGRES_DB=rosgrid
POSTGRES_USER=rosgrid_user
POSTGRES_PASSWORD=cambiar_en_entorno_local

# --- KeyDB Multi-Hilo / DragonflyDB (Protocolo RESP) ---
REDIS_PASSWORD=cambiar_en_entorno_local

# --- Criptografía y Seguridad (Generar con: openssl rand -base64 32) ---
ROSGRID_MASTER_VAULT_KEY=reemplazar_con_32_bytes_base64_para_aes_256_gcm
ROSGRID_JWT_SECRET_KEY=reemplazar_con_secreto_criptografico_jwt
ROSGRID_CSRF_HMAC_SECRET=reemplazar_con_secreto_criptografico_csrf

# --- Parámetros Operativos MikroTik ---
ROSGRID_MIKROTIK_TIMEOUT_SECONDS=10
ROSGRID_SAFEMODE_ROLLBACK_SECONDS=60
ROSGRID_BACKUP_RETENTION_DAYS=30
~~~

---

## 6. Configuración de Nginx (`vue3/nginx/default.conf`) Compatible con OWASP ZAP y Observabilidad

Para que el contenedor Nginx pase tanto la auditoría DAST de **OWASP ZAP** (cabeceras de seguridad estrictas) como la recolección de métricas de `nginx-prometheus-exporter` (`/stub_status`), Antigravity DEBE escribir `vue3/nginx/default.conf` con esta especificación:

~~~nginx
server {
    listen 8080;
    listen 80;
    server_name _;
    server_tokens off;

    root /usr/share/nginx/html;
    index index.html;

    # Cabeceras de Seguridad Obligatorias (Certificación DAST OWASP ZAP)
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' ws: wss:; frame-ancestors 'none'; base-uri 'self'; form-action 'self';" always;

    # Endpoint interno para nginx-prometheus-exporter (Nivel 11X)
    location = /stub_status {
        stub_status;
        allow 127.0.0.1;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        allow 10.0.0.0/8;
        deny all;
    }

    # Proxy inverso hacia FastAPI (REST API)
    location /api/ {
        proxy_pass http://rosgrid-api:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Proxy inverso para WebSockets (Gráficas en Vivo WinBox y Notificaciones NOC)
    location /ws/ {
        proxy_pass http://rosgrid-api:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600s;
    }

    # Soporte de enrutamiento HTML5 History Mode para Vue Router
    location / {
        try_files $uri$uri/ /index.html;
    }
}
~~~

---

## 7. Empaquetado de Imágenes de Producción y Publicación en Docker Hub (`scripts/build.sh`)

Para distribuir **RoSGrid** como imágenes listas para producción en Docker Hub bajo el namespace `sinfallas/`, Antigravity DEBE crear los siguientes 4 artefactos cumpliendo al 100% con el escáner Trivy (`./scripts/auditar-infra.sh`).

### 7.1 `fastapi/Dockerfile` (Hito 10.5)

~~~dockerfile
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
FROM sinfallas/base-python-uv:3.15

ARG BUILD_DATE="unknown"
LABEL org.opencontainers.image.title="RoSGrid Backend API & Workers" \
      org.opencontainers.image.description="Backend Multi-Tenant para Flotas MikroTik RouterOS v7+" \
      org.opencontainers.image.authors="Sinfallas <sinfallas@yahoo.com>" \
      org.opencontainers.image.licenses="GPL-3.0-only" \
      org.opencontainers.image.created="${BUILD_DATE}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ROSGRID_IMAGE_PREBUILT=1 \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

# Crear usuario y grupo sin privilegios (Cumplimiento Trivy DS002)
RUN groupadd -g 10001 rosgrid && \
    useradd -u 10001 -g rosgrid -m -s /usr/sbin/nologin rosgrid && \
    mkdir -p /var/lib/rosgrid/backups && \
    chown -R rosgrid:rosgrid /app /var/lib/rosgrid

COPY --chown=rosgrid:rosgrid pyproject.toml alembic.ini ./
COPY --chown=rosgrid:rosgrid migrations ./migrations
COPY --chown=rosgrid:rosgrid scripts ./scripts
COPY --chown=rosgrid:rosgrid src ./src

RUN chmod +x /app/scripts/entrypoint.sh && \
    uv pip install --system --no-cache .

USER rosgrid

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

ENTRYPOINT ["/usr/bin/env", "bash", "/app/scripts/entrypoint.sh"]
~~~

### 7.2 `vue3/Dockerfile` (Hito 13.7)

~~~dockerfile
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# --- Etapa 1: Compilación de la SPA Vue 3 + TypeScript ---
FROM sinfallas/base-node-ionic:26 AS builder

WORKDIR /app

COPY package.json .npmrc ./
RUN pnpm install --frozen-lockfile=false

COPY . .
RUN pnpm run build

# --- Etapa 2: Servidor Nginx Endurecido (Non-Root) ---
FROM nginx:1.27-alpine

ARG BUILD_DATE="unknown"
LABEL org.opencontainers.image.title="RoSGrid Frontend UI" \
      org.opencontainers.image.description="Consola WebFig Multi-Tenant y Wallboard NOC para MikroTik RouterOS v7+" \
      org.opencontainers.image.authors="Sinfallas <sinfallas@yahoo.com>" \
      org.opencontainers.image.licenses="GPL-3.0-only" \
      org.opencontainers.image.created="${BUILD_DATE}"

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

# Ajustar permisos para ejecución sin root (Cumplimiento Trivy DS002)
RUN chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
~~~

### 7.3 Script `scripts/build.sh` del Proyecto (Hito 13.7 / Hito 16)

Antigravity DEBE crear en `scripts/` el archivo ejecutable `build.sh` (`chmod +x scripts/build.sh`), siguiendo el estándar de construcción `buildx` de Sinfallas:

~~~bash
#!/usr/bin/env bash
# Made by Sinfallas <sinfallas@yahoo.com>
# Licence: GPL-3.0-only

set -euo pipefail

if [[ "$EUID" = "0" ]]; then
	echo -e "\e[00;31mERROR: NO debe ser root.\e[00m"
	exit 1
fi

clear
CURRENT_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VERSION="${1:-1.0.0}"

echo "[RoSGrid] Preparando entorno multi-arquitectura con binfmt y buildx..."
docker run --privileged --rm tonistiigi/binfmt --install all
docker buildx rm container-builder 2>/dev/null || true
docker buildx create --name container-builder --driver docker-container --bootstrap --use

echo "[RoSGrid] Construyendo y publicando sinfallas/rosgrid-backend (${VERSION} y latest)..."
docker buildx build \
	--platform linux/amd64 \
	--build-arg BUILD_DATE="$CURRENT_DATE" \
	--push \
	-t "sinfallas/rosgrid-backend:${VERSION}" \
	-t sinfallas/rosgrid-backend:latest \
	--builder=container-builder \
	-f fastapi/Dockerfile fastapi

echo "[RoSGrid] Construyendo y publicando sinfallas/rosgrid-frontend (${VERSION} y latest)..."
docker buildx build \
	--platform linux/amd64 \
	--build-arg BUILD_DATE="$CURRENT_DATE" \
	--push \
	-t "sinfallas/rosgrid-frontend:${VERSION}" \
	-t sinfallas/rosgrid-frontend:latest \
	--builder=container-builder \
	-f vue3/Dockerfile vue3

docker buildx rm container-builder
docker system prune -af
docker builder prune -af
docker buildx prune -af

echo "finalizado..."
exit 0
~~~

### 7.4 `docker-compose.prod.yml` (Despliegue Directo desde Docker Hub con KeyDB Multi-Hilo)

Para que cualquier operador o ISP despliegue RoSGrid en producción descargando directamente las imágenes compiladas desde Docker Hub sin necesitar el código fuente:

~~~yaml
services:
  rosgrid-db:
    image: postgres:17-alpine
    container_name: rosgrid_db
    hostname: rosgrid_db
    restart: unless-stopped
    environment:
      TZ: "America/Caracas"
      POSTGRES_DB: "${POSTGRES_DB:-rosgrid}"
      POSTGRES_USER: "${POSTGRES_USER:-rosgrid_user}"
      POSTGRES_PASSWORD: "${POSTGRES_PASSWORD:?Debes definir POSTGRES_PASSWORD en .env}"
    volumes:
      - rosgrid_pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER:-rosgrid_user} -d$${POSTGRES_DB:-rosgrid}"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - rosgrid_internal_net

  rosgrid-redis:
    image: eqalpha/keydb:alpine
    container_name: rosgrid_redis
    hostname: rosgrid-redis
    restart: unless-stopped
    environment:
      TZ: "America/Caracas"
    command: >
      keydb-server
      --server-threads 2
      --appendonly no
      --save ""
      --maxmemory 512mb
      --maxmemory-policy volatile-lru
      --requirepass "${REDIS_PASSWORD:?Debes definir REDIS_PASSWORD en .env}" volumes: - rosgrid_redis_data:/data healthcheck: test: ["CMD-SHELL", "keydb-cli -a \"$${REDIS_PASSWORD}\" ping | grep PONG"]
      interval: 5s
      timeout: 3s
      retries: 10
    networks:
      - rosgrid_internal_net

  # --- PERFIL OPCIONAL DE ALTO RENDIMIENTO PARA GRANDES FLOTAS ISP (>300 ROUTERS / 16GB+ RAM): DRAGONFLYDB ---
  # Para activarlo en servidores dedicados, reemplaza el bloque rosgrid-redis anterior por:
  # rosgrid-redis:
  #   image: docker.dragonflydb.io/dragonflydb/dragonfly:latest
  #   container_name: rosgrid_redis
  #   hostname: rosgrid-redis
  #   restart: unless-stopped
  #   ulimits:
  #     memlock: -1
  #   command: >
  #     dragonfly
  #     --proactor_threads=4
  #     --maxmemory=2gb
  #     --requirepass=${REDIS_PASSWORD} #     --alsologtostderr #   volumes: #     - rosgrid_redis_data:/data #   healthcheck: #     test: ["CMD-SHELL", "redis-cli -a \"$${REDIS_PASSWORD}\" ping | grep PONG"]
  #     interval: 10s
  #     timeout: 5s
  #     retries: 5
  #   networks:
  #     - rosgrid_internal_net

  rosgrid-api:
    image: sinfallas/rosgrid-backend:latest
    container_name: rosgrid_api
    hostname: rosgrid_api
    pull_policy: always
    restart: unless-stopped
    depends_on:
      rosgrid-db:
        condition: service_healthy
      rosgrid-redis:
        condition: service_healthy
    environment:
      TZ: "America/Caracas"
      ROSGRID_ENV: "production"
      ROSGRID_DATABASE_URL: "postgresql+asyncpg://${POSTGRES_USER:-rosgrid_user}:${POSTGRES_PASSWORD}@rosgrid_db:5432/${POSTGRES_DB:-rosgrid}"
      ROSGRID_SYNC_DATABASE_URL: "postgresql://${POSTGRES_USER:-rosgrid_user}:${POSTGRES_PASSWORD}@rosgrid_db:5432/${POSTGRES_DB:-rosgrid}"
      ROSGRID_REDIS_URL: "redis://:${REDIS_PASSWORD}@rosgrid_redis:6379/0"
      ROSGRID_MASTER_VAULT_KEY: "${ROSGRID_MASTER_VAULT_KEY:?Debes definir ROSGRID_MASTER_VAULT_KEY}"
      ROSGRID_JWT_SECRET_KEY: "${ROSGRID_JWT_SECRET_KEY:?Debes definir ROSGRID_JWT_SECRET_KEY}"
      ROSGRID_CSRF_HMAC_SECRET: "${ROSGRID_CSRF_HMAC_SECRET:?Debes definir ROSGRID_CSRF_HMAC_SECRET}"
    volumes:
      - rosgrid_backups_storage:/var/lib/rosgrid/backups
    networks:
      - rosgrid_internal_net

  rosgrid-worker:
    image: sinfallas/rosgrid-backend:latest
    container_name: rosgrid_worker
    hostname: rosgrid_worker
    pull_policy: always
    restart: unless-stopped
    depends_on:
      rosgrid-api:
        condition: service_healthy
    environment:
      TZ: "America/Caracas"
      ROSGRID_ENV: "production"
      ROSGRID_DATABASE_URL: "postgresql+asyncpg://${POSTGRES_USER:-rosgrid_user}:${POSTGRES_PASSWORD}@rosgrid_db:5432/${POSTGRES_DB:-rosgrid}"
      ROSGRID_REDIS_URL: "redis://:${REDIS_PASSWORD}@rosgrid_redis:6379/0"
      ROSGRID_MASTER_VAULT_KEY: "${ROSGRID_MASTER_VAULT_KEY}"
    volumes:
      - rosgrid_backups_storage:/var/lib/rosgrid/backups
    entrypoint: ["python3", "-m", "src.workers.runner"]
    networks:
      - rosgrid_internal_net

  rosgrid-ui:
    image: sinfallas/rosgrid-frontend:latest
    container_name: rosgrid_ui
    hostname: rosgrid_ui
    pull_policy: always
    restart: unless-stopped
    depends_on:
      rosgrid-api:
        condition: service_healthy
    environment:
      TZ: "America/Caracas"
    volumes:
      - rosgrid_nginx_logs:/var/log/nginx
    ports:
      - "${ROSGRID_HTTP_PORT:-8080}:8080"
    networks:
      - rosgrid_internal_net

networks:
  rosgrid_internal_net:
    driver: bridge

volumes:
  rosgrid_pg_data:
    name: rosgrid_pg_data
  rosgrid_redis_data:
    name: rosgrid_redis_data
  rosgrid_backups_storage:
    name: rosgrid_backups_storage
  rosgrid_nginx_logs:
    name: rosgrid_nginx_logs
~~~
