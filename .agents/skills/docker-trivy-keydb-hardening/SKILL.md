---
name: docker-trivy-keydb-hardening
description: >-
  Docker container hardening (Trivy HIGH/CRITICAL = 0), default multi-threaded KeyDB in-memory engine
  (with optional DragonflyDB profile), backend performance optimizations (orjson, uvloop, TLS Keep-Alive pool,
  KeyDB pipelines, BRIN index), Swagger production suppression, and multi-stage build.sh publication.
  Applies to RoSGrid Sub-task 10.6, Milestone 13.7, and Milestone 16.
---

# Docker/Trivy Hardening, Multi-Threaded KeyDB & Production Optimization

This skill governs infrastructure configuration (`docker-compose*.yml`, `Dockerfile`, `entrypoint.sh`, `nginx/default.conf`, `scripts/build.sh`) and backend performance packaging.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. In-Memory Architecture: Multi-Threaded KeyDB vs DragonflyDB Profile

1. **Default Multi-Threaded KeyDB (`eqalpha/keydb:alpine`):**
   - The `rosgrid-redis` service in `docker-compose.yml`, `docker-compose.prod.yml`, and `fastapi/docker-compose.qa.yml` uses `image: eqalpha/keydb:alpine` with hostname `rosgrid-redis` and port `6379`.
   - Standard execution command: `keydb-server --server-threads 2 --appendonly no --save "" --maxmemory 512mb --maxmemory-policy volatile-lru` with `keydb-cli` healthcheck.
2. **Optional High-Performance Profile (`DragonflyDB`):**
   - Keep documented as a commented-out profile in `docker-compose.yml` and `docker-compose.prod.yml` referencing `docker.dragonflydb.io/dragonflydb/dragonfly:latest` (`--proactor_threads=4 --maxmemory=2gb`) for massive ISP fleets (`> 300` routers on servers with `16 GB+` RAM).

---

## 2. High-Performance Backend Optimizations & Hardening (`fastapi/`)

1. **`ORJSONResponse` & Production Swagger Suppression (`src/main.py`):**
   - Enforce `default_response_class=ORJSONResponse` in `FastAPI(...)` and use `orjson` serialization for WebSocket binary/text frames.
   - If `settings.ROSGRID_ENV == "production"`, force `docs_url=None`, `redoc_url=None`, and `openapi_url=None`.
2. **`uvloop` + `httptools` Boot & Auto-Migration (`scripts/entrypoint.sh`):**
   - Acquire PostgreSQL advisory lock `pg_advisory_lock(948271605)` before running `alembic upgrade head`.
   - Start Uvicorn with `--loop uvloop --http httptools --proxy-headers`.
3. **TLS `Keep-Alive` Pool, KeyDB Pipelines & `BRIN` Index:**
   - In `src/mikrotik/client.py`, configure `httpx.Limits(max_keepalive_connections=20, max_connections=100, keepalive_expiry=60.0)`.
   - In `src/redis_layer/zero_metrics_monitor.py`, batch ephemeral state writes using `pipeline()`.
   - Ensure the `BRIN` index (`ix_audit_logs_created_at_brin`, `postgresql_using="brin"`) exists on `audit_logs(created_at)`.

---

## 3. Trivy IaC Compliance (`./scripts/auditar-infra.sh`) & Release (`./scripts/build.sh`)

1. **Trivy Compliance (`HIGH,CRITICAL = 0`):**
   - Strict IPv4 networks (`driver: bridge`; forbidden: `enable_ipv6: true`).
   - Forbid `privileged: true`, `SYS_PTRACE`, or mounting `/var/run/docker.sock` in compose manifests.
   - In `fastapi/Dockerfile` and `vue3/Dockerfile`, enforce non-root unprivileged users (`USER rosgrid` UID `10001` / `USER nginx`) with explicit `HEALTHCHECK` directives.
   - Only `rosgrid-ui` exposes ports to the host; PostgreSQL and KeyDB remain fully isolated within `rosgrid_internal_net`.
2. **Multi-Stage `./scripts/build.sh` Script:**
   - Enforce non-root execution (`EUID != 0`), initialize `tonistiigi/binfmt` and `docker buildx` (`container-builder`), compile and publish `sinfallas/rosgrid-backend` and `sinfallas/rosgrid-frontend` (`:${VERSION}` and `:latest`), running `prune -af` upon completion.
