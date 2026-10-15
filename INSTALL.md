# ⚙️ Guía de Instalación y Puesta en Marcha (INSTALL) — RoSGrid

Este documento detalla los requisitos técnicos y el procedimiento paso a paso para instalar, configurar y actualizar **RoSGrid** tanto en entornos de producción (ISP / NOC / Telecom) como en laboratorios de prueba (EVE-NG / GNS3).

---

## 1. Requisitos del Sistema y Red

### 1.1 Requisitos del Servidor Anfitrión (Host Docker)
| Recurso | Estándar con **KeyDB** (Hasta 300 Routers) | Alta Escala con **DragonflyDB** (300 a 2,000+ Routers) |
| :--- | :--- | :--- |
| **Sistema Operativo** | Linux 64-bit (Ubuntu 24.04 / 26.04 LTS, Debian 12+) | Ubuntu Server 24.04 / 26.04 LTS (Kernel `>= 6.2` con soporte `io_uring`) |
| **CPU** | 2 a 4 vCPU (`x86_64` / `amd64`) | 8+ vCPU (`x86_64` / `amd64`) |
| **Memoria RAM** | **4 GB a 8 GB RAM** (KeyDB consume ~35 MB en reposo) | **16 GB+ RAM** (DragonflyDB pre-reserva memoria por cada hilo de CPU) |
| **Almacenamiento** | 20 GB SSD (NVMe recomendado) | 80 GB+ NVMe (para retención de backups `.rsc` y bitácora WORM con índice `BRIN`) |
| **Motor de Contenedores** | Docker Engine `>= 24.0` + Docker Compose `v2.20+` | Docker Engine `>= 26.0` + Docker Compose `v2.27+` |

### 1.2 Requisitos en los Equipos MikroTik
- **Versión de Sistema Operativo:** **RouterOS v7.1 o superior** (arquitecturas `ARM`, `ARM64`, `TILE`, `x86` o `CHR`). *Nota: RouterOS v6 no es compatible por carecer de API REST nativa `/rest/*`.*
- **Conectividad de Red:** El contenedor `rosgrid-api` y `rosgrid-worker` deben alcanzar la IP de gestión de cada MikroTik por el puerto **TCP `443`** (o el puerto personalizado asignado a `/ip/service/www-ssl`).
- **Reloj Sincronizado (NTP):** Tanto el servidor host de RoSGrid como los operadores deben tener la hora sincronizada vía NTP para la validación de códigos **2FA TOTP (RFC 6238)**.

---

## 2. Preparación de Variables de Entorno y Secretos Criptográficos (`.env`)

Nunca utilices las claves de ejemplo en un entorno real. Ejecuta los siguientes comandos en tu terminal Linux para generar un archivo `.env` con entropía criptográfica segura (`256 bits`):

~~~bash
# 1. Copiar la plantilla base
cp .env.example .env

# 2. Generar secretos criptográficos aleatorios e inyectarlos en .env
sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 24)|" .env
sed -i "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=$(openssl rand -hex 24)|" .env
sed -i "s|ROSGRID_MASTER_VAULT_KEY=.*|ROSGRID_MASTER_VAULT_KEY=$(openssl rand -base64 32)|" .env
sed -i "s|ROSGRID_JWT_SECRET_KEY=.*|ROSGRID_JWT_SECRET_KEY=$(openssl rand -base64 48)|" .env
sed -i "s|ROSGRID_CSRF_HMAC_SECRET=.*|ROSGRID_CSRF_HMAC_SECRET=$(openssl rand -base64 48)|" .env

# 3. Proteger los permisos del archivo .env (solo lectura para el propietario)
chmod 600 .env
~~~

> ⚠️ **IMPORTANTE SOBRE `ROSGRID_MASTER_VAULT_KEY`:** Esta llave maestra de 32 bytes (codificada en Base64) cifra las credenciales API de todos tus routers MikroTik mediante `AES-256-GCM`. Guárdala en un gestor de secretos externo seguro; si pierdes esta llave, no podrás descifrar la bóveda `router_credentials_vault`.

---

## 3. Modos de Instalación y Despliegue

### Opción A: Despliegue en Producción desde Docker Hub (Recomendado para ISP / NOC)
Utiliza las imágenes oficiales precompiladas, inmutables y sin privilegios (`non-root`) publicadas en Docker Hub (`sinfallas/rosgrid-backend:latest` y `sinfallas/rosgrid-frontend:latest`). En este modo (`ROSGRID_ENV=production`), la documentación interactiva Swagger/ReDoc está **deshabilitada por seguridad** (consulta `docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md`).

~~~bash
# 1. Descargar las imágenes oficiales más recientes
docker compose -f docker-compose.prod.yml pull

# 2. Iniciar la plataforma en segundo plano
docker compose -f docker-compose.prod.yml up -d

# 3. Verificar que las migraciones automáticas (pg_advisory_lock) hayan finalizado
docker logs -f rosgrid_api
~~~

### Opción B: Despliegue Local o Laboratorio (EVE-NG / Desarrollo)
Levanta la plataforma montando el código fuente local sobre las imágenes base inmutables (`sinfallas/base-python-uv:3.13` y `sinfallas/base-node-ionic:22`):

~~~bash
# 1. Auditar la configuración con Trivy antes de levantar
./auditar-infra.sh

# 2. Levantar todos los servicios
docker compose up -d

# 3. Verificar el estado de salud de los contenedores
docker compose ps
~~~

### Opción C: Compilación Multi-Etapa Propia con `buildx`
Si deseas construir tus propias imágenes de producción a partir del código fuente auditado:

~~~bash
# Ejecutar como usuario normal (NO root)
./build.sh 1.0.0
~~~

---

## 4. Motor en Memoria: KeyDB Multi-Hilo (Predeterminado) vs. DragonflyDB (Alto Rendimiento)

Para superar la limitación mono-hilo de Redis tradicional en el bus `Pub/Sub` de telemetría WebSocket y en los pipelines del monitor *Zero-Metrics*, RoSGrid utiliza **KeyDB (`eqalpha/keydb:alpine`) con `--server-threads 2`** como motor predeterminado.

### ¿Por qué recomendamos usar KeyDB por defecto?
1. **Eficiencia extrema de memoria RAM:** Consume apenas `~35 MB` en reposo, ideal para servidores VPS de 4 GB / 8 GB de RAM y laboratorios en EVE-NG.
2. **Desempeño Multi-Hilo real:** Triplica el rendimiento de Redis tradicional en canales `Pub/Sub` y hashes efímeros sin exigir permisos especiales del kernel.
3. **Licencia 100% Software Libre (`BSD-3-Clause`):** Totalmente compatible con la filosofía `GPL-3.0-only` de RoSGrid.

### ¿Cuándo y cómo cambiar al Perfil de Alto Rendimiento con DragonflyDB?
**Recomendación oficial:** Utiliza **KeyDB** a menos que tu entorno opere una flota masiva (**más de 300 a 500 routers MikroTik con decenas de operadores y pantallas NOC conectadas simultáneamente a gráficas en vivo**) sobre un servidor dedicado con **16 GB+ de RAM**.

Si tu operación requiere el motor *Shared-Nothing* sobre `io_uring` de **DragonflyDB**, reemplaza el bloque del servicio `rosgrid-redis` en tu `docker-compose.prod.yml` por el siguiente perfil (no requiere ningún cambio en el código de FastAPI):

~~~yaml
  rosgrid-redis:
    image: docker.dragonflydb.io/dragonflydb/dragonfly:latest
    container_name: rosgrid_redis
    restart: unless-stopped
    ulimits:
      memlock: -1
    command: >
      dragonfly
      --proactor_threads=4
      --maxmemory=2gb
      --requirepass=${REDIS_PASSWORD} --alsologtostderr networks: - rosgrid_internal_net healthcheck: test: ["CMD-SHELL", "redis-cli -a $${REDIS_PASSWORD} ping | grep PONG"]
      interval: 10s
      timeout: 5s
      retries: 5
~~~

---

## 5. Preparación Rápida de tus Equipos MikroTik (RouterOS v7.1+)

Antes de registrar un router en el inventario de RoSGrid (individualmente o por lote CSV), ejecuta estos comandos en la terminal del MikroTik para habilitar `www-ssl` con un certificado TLS para fijación **TOFU (*Trust On First Use*)**:

~~~routeros
# 1. Generar y firmar certificado TLS autofirmado en el MikroTik
/certificate add name="rosgrid-tofu-cert" common-name="rosgrid.local" key-size=2048 days-valid=3650 key-usage=digital-signature,key-encipherment,tls-server
/certificate sign "rosgrid-tofu-cert"

# 2. Habilitar REST API v7 sobre HTTPS (puerto 443) y desactivar HTTP plano
/ip service set www-ssl certificate="rosgrid-tofu-cert" port=443 disabled=no
/ip service set www disabled=yes

# 3. Crear usuario dedicado para RoSGrid
/user add name="rosgrid_api" password="CambiarPorClaveInicialFuerte2026!" group=full comment="Managed by RoSGrid Vault"
~~~

---

## 6. Actualización de Versiones y Migraciones Automáticas

RoSGrid incluye un mecanismo de auto-migración protegido por bloqueo atómico en PostgreSQL (`pg_advisory_lock` ID `948271605` en `entrypoint.sh`). Para actualizar tu instalación a una nueva versión sin corromper el esquema:

~~~bash
# 1. Consultar cambios relevantes en CHANGELOG.md
less CHANGELOG.md

# 2. Descargar la nueva versión de las imágenes y recrear contenedores
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
~~~

El contenedor `rosgrid_api` adquirirá automáticamente el bloqueo en PostgreSQL 17, ejecutará `alembic upgrade head`, liberará el bloqueo e iniciará el servidor ASGI Uvicorn (`--loop uvloop --http httptools`) sin intervención manual.
