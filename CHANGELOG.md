# 📋 Historial de Cambios (Changelog) — RoSGrid

Todos los cambios notables en las versiones oficiales de **RoSGrid** (y en sus imágenes inmutables de Docker Hub `sinfallas/rosgrid-backend` y `sinfallas/rosgrid-frontend`) se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/), y este proyecto se adhiere a [Semantic Versioning (SemVer)](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- **Implementación Frontend (Vue 3 + Pinia) — Topología L2, Matriz CVE, Syslog Live y PoE-Aware (Hito 23.5):**
  - **Vista interactiva de Topología Física Layer 2 (`L2TopologyView.vue`):** Canvas 2D interactivo a 60 FPS con Pan/Zoom suave, badges dinámicos de consumo PoE en tiempo real (`⚡ W`), indicadores de estado Online/Offline, selector de modo Sólo-PoE, drawer lateral táctico y fallback accesible para screen readers.
  - **Matriz de Vulnerabilidades CVE de Flota (`FleetCveMatrix.vue`):** Panel táctico con 4 tarjetas KPI evaluadas (Evaluados, Vulnerables, Críticos, Versión Recomendada), filtros reactivos por severidad (CRITICAL, HIGH, MEDIUM, LOW), sincronización remota contra NIST NVD y enlace directo al orquestador de actualización masiva.
  - **Acceso Directo CVE en Inventario (`RouterInventoryView.vue`):** Botón táctico `[ 🛡️ Matriz de CVEs ]` para auditoría inmediata de vulnerabilidades de toda la flota.
  - **Terminal Syslog en Vivo en WebFig (`RouterSyslogTerminalView.vue`):** Consola embebida en la vista de router que consume en tiempo real el RingBuffer efímero de KeyDB (500 eventos) sin persistencia en base de datos, con alertas visuales de severidad crítica, auto-scroll inteligente y modal con plantilla CLI de enrolamiento MikroTik.
  - **Orquestador de Actualización Masiva PoE-Aware con Safety Stop (`BulkOperationsAndUpdatesView.vue`):** Conmutador táctico PoE-Aware para actualización de clientes PD antes que switches PSE y selector de umbral Safety Stop (1%, 2%, 5%).
  - **Navegación Táctica:** Enlace a Topología L2 y Matriz CVE en el shell responsive principal (`RgResponsiveShell.vue`) y acceso a Syslog Live en el menú lateral de WebFig (`RouterSidebarMenu.vue`).
  - **Certificación QA 11X:** 297 tests unitarios Vitest (100% pasando en 43 suites), 20 escenarios BDD Karate Labs UI, cero errores en `vue-tsc --noEmit` y cero violaciones ESLint / SonarJS.

- **Planificación y Diseño Arquitectónico: Automatización de Flota, Topología L2, Syslog Efímero, Exportador Prometheus y Seguridad CVE (Hito 23):**
  - **Especificación Técnica y Arquitectura de Datos (`specs/35` y `docs/12`):** Diseño formal de estructuras en memoria para preservar estrictamente el modelo *Zero-Metrics Storage* (cero almacenamiento de series de tiempo en PostgreSQL 17).
  - **Motor de Actualizaciones Masivas PoE-Aware con Safety Stop:** Modelado de Grafo Acíclico Dirigido (DAG) de dependencias eléctricas PoE para ordenar la actualización de dispositivos cliente (PD) antes que los conmutadores/routers alimentadores (PSE), evitando cortes eléctricos durante el flasheo de firmware. Incluye circuito de corte de emergencia (*Safety Stop Circuit-Breaker*) que congela el lote si la tasa de fallos post-reinicio supera el 1%.
  - **Cruce Proactivo de Vulnerabilidades CVE en Inventario:** Catálogo embebido local (`cve_catalog_ros.json`) para cruce automático contra la versión instalada (`ros_version`) con cálculo de nivel de riesgo CVSS e insignias en interfaz, sin fuga de telemetría ni consultas a servicios en la nube externa.
  - **Receptor Syslog Centralizado Efímero (UDP/TCP 5514) con Alertas en Vuelo:** Colector asíncrono sobre puerto no privilegiado 5514 que almacena únicamente los últimos 500 eventos por router en un RingBuffer en la memoria RAM de KeyDB (cero bytes en disco), con evaluador regex en vuelo para despacho inmediato de caídas de interfaz (*linkDown*) y tormentas de acceso al Wallboard NOC vía WebSockets.
  - **Plantilla Masiva de Enrolamiento Syslog:** Script predefinido de configuración para RouterOS v7 (`/system/logging/action` y `/system/logging`) listo para aprovisionamiento desatendido mediante *Bulk Ops*.
  - **Descubrimiento y Visualización de Topología Física Capa 2:** Motor de correlación de adyacencias puerto a puerto a partir de `/rest/ip/neighbor` (MNDP, LLDP y CDP) y diseño de interfaz gráfica interactiva en Canvas/SVG con físicas suaves sin guardar históricos.
  - **Puente de Telemetría hacia Prometheus (`GET /api/v1/metrics/fleet`):** Exposición de métricas de flota en formato estándar de Prometheus a partir de la memoria de KeyDB para graficación a largo plazo en Grafana, sin persistencia de métricas en PostgreSQL.
  - **Ampliación del Servidor MCP y de la Skill `rosgrid-noc-operator`:** Incorporación de 4 nuevas herramientas semánticas (`rosgrid_get_l2_topology`, `rosgrid_check_fleet_cves`, `rosgrid_get_recent_syslog` y `rosgrid_execute_poe_aware_upgrade`), alcanzando 18 herramientas operativas, y adición de SOP-6 y SOP-7 a la Skill oficial.
  - **Marco de Ciberseguridad y Mitigación de Riesgos:** Prevención de suplantación UDP en Syslog mediante validación estricta de IP contra el inventario del tenant, rate-limiting contra inundación de logs, autenticación de scrape para Prometheus y salvaguardas anti-SSRF.

- **Skill Oficial de Operaciones NOC para Agentes IA (`rosgrid-noc-operator`) (Hito 22.15):**
  - **Skill Portable de Operación Autónoma (`.agents/skills/rosgrid-noc-operator/SKILL.md`):** Arquitectura y manual operativo completo para capacitar a agentes de Inteligencia Artificial (Antigravity, Claude Desktop, Claude Code, Hermes Agent) como Ingenieros NOC Tier-2/Tier-3 certificados sobre flotas MikroTik RouterOS v7.
  - **5 Playbooks Operativos Estándar (SOP):** Procedimientos guiados paso a paso para:
    1. *SOP-1 (Degradación de Abonado):* Diagnóstico 360°, pruebas multi-MTU (64B vs 1472B DF-bit), potencia óptica SFP DDM y reconexión limpia de PPPoE.
    2. *SOP-2 (Cortes Masivos de Fibra):* Correlación espacial de caídas masivas agrupando ONUs por puerto PON o caja NAP.
    3. *SOP-3 (Inestabilidad BGP/OSPF):* Inspección de adyacencias, Looking Glass FIB y comparación Git-style contra la configuración previa.
    4. *SOP-4 (Auditoría CIS y Drift):* Evaluación de seguridad (Score 0-100), detección de desvíos contra la Golden Baseline y propuestas de hardening.
    5. *SOP-5 (Aislamiento Preventivo):* Contención inmediata e idempotente de clientes comprometidos con cola 64k/64k y lista `AISLADOS_TECNICO`.
  - **Catálogo Exhaustivo de Herramientas MCP (`references/mcp_tools.md`):** Especificación completa de parámetros, tipos, precondiciones y restricciones operativas para las 14 herramientas del servidor MCP `/api/v1/mcp`.
  - **Guía de Banderas RouterOS v7 (`references/routeros_flags.md`):** Interpretación estricta de banderas nativas (`[D]`, `[X]`, `[I]`, `[R]`) e identificadores internos hexadecimales (`*1`, `*1A`).
  - **Plantillas de Configuración Listas para Producción (`configs/`):** Manifiestos de despliegue para Claude Desktop (`claude_desktop.json`) y Hermes Agent (`hermes_agent.yaml`).
  - **Distribución Multicanal para Despliegues Remotos y Frontend:**
    - **Endpoint Público REST (`GET /api/v1/mcp/skill`):** Exposición de las directrices y playbooks de la Skill con empaquetado autocontenido en la imagen Docker (`fastapi/src/api/v1/SKILL.md`) soportando salida Markdown o JSON (`?format=json`).
    - **Botones de Descarga y Copiado en Interfaz Web (`RgMcpTokenModal.vue`):** Integración en el modal del token MCP de botones para copiar el System Prompt al portapapeles y descargar el archivo `SKILL.md` con 1 clic sin necesidad de consola.
    - **Descarga Automatizada en Instalación Remota (`instalar-rosgrid.sh`):** Aprovisionamiento desatendido de los manifiestos, esquemas y configuraciones de la Skill en `/opt/rosgrid/skills/rosgrid-noc-operator/` y documentación en el banner final de instalación.
  - **Sincronización Global Antigravity:** Replicación en `~/.gemini/config/skills/rosgrid-noc-operator/` para disponibilidad universal entre workspaces.
  - **Sincronización Documental:** Actualización integral de `specs/30_BACKEND_MCP_PROTECTED_ENDPOINT.md` y `docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md`.

- **Generador de Tokens MCP, Supervisión de Sesiones IA con Kill-Switch y Panel de Notificaciones (Hito 22.14):**
  - **Generador Visual de Tokens MCP (`RgMcpTokenModal.vue`):** Modal interactivo integrado en la pantalla de Usuarios y Permisos (`UsersAndPermissionsView.vue`) para la emisión de Bearer Tokens de larga duración (30 a 730 días) para cuentas de servicio (`SERVICE_ACCOUNT`, `TENANT_ADMIN`, `SUPERADMIN_GLOBAL`). Muestra metadatos de sesión, advertencias de gobernanza y snippets de configuración de 1-clic para Claude Desktop (`claude_desktop_config.json`) y Hermes Agent (`config.yaml`).
  - **Supervisión y Kill-Switch de Agentes IA (`ActiveSessionsKillSwitchView.vue`):** Pestañas de filtrado táctico (*Todas*, *Operadores Humanos*, *Agentes IA MCP*), badges distintivos de cuenta de servicio, linaje del operador que autorizó el token (`Por: @usuario`), lista blanca CIDR y botón de revocación en caliente en tiempo real en KeyDB/Redis.
  - **Endpoint Backend `POST /api/v1/users/{user_id}/mcp-token`:** Emisión criptográfica firmada con JWT HS256, validación de pertenencia al tenant, registro de sesión en KeyDB (`rg:{tenant}:sess:{sid}`) sincronizado con `active_sessions` y auditoría inmutable WORM (`MCP_TOKEN_ISSUED`).
  - **Sincronización del Script CLI (`generar_token_mcp.py`):** Vinculación de tokens generados desde terminal al registro de sesiones activas con metadatos de autoría (`CLI (Terminal)`), permitiendo su revocación inmediata desde la interfaz web.
  - **Panel de Canales de Alerta y Notificación Multicanal (`NotificationChannelsPanel.vue`):** Interfaz completa para el módulo de API de notificaciones (`fastapi/src/api/v1/notification_channels.py`), integrado como 7ª pestaña en la pantalla de Cumplimiento Normativo (`EnterpriseComplianceView.vue`). Permite creación, edición, alternado activo/inactivo, prueba de despacho interactiva (`POST /{id}/test`) y eliminación de canales Telegram Bot, Servidores SMTP y Webhooks genéricos cifrados con AES-256-GCM.
  - **Certificación QA 11X:** 406 pruebas de backend aprobadas con 95% de cobertura global, 278 pruebas unitarias frontend en 40 archivos aprobadas al 100%, 0 errores en ESLint y Vue-TSC.

- **Consolidación de Calidad, Resolución Integral de Diagnósticos y Robustecimiento DevOps (Hito 22.13):**
  - **Sintaxis y Linter de Documentación (`markdownlint-cli`):** Corrección y certificación de 0 errores y 0 advertencias en la totalidad de especificaciones (`specs/30`, `specs/31`, `specs/32`, `specs/33`, `specs/34`), manuales operativos (`docs/01`, `docs/03`, `docs/04`, `docs/05`, `docs/06`, `docs/07`, `docs/10`, `docs/11`) y guías de contribución (`CONTRIBUTING.md`), estandarizando viñetas (`MD004`), espaciado en encabezados (`MD022`), listas (`MD032`), bloques de código (`MD031`), tablas compactas (`MD060`) y eliminación de puntuación en títulos (`MD026`).
  - **Diagramas de Arquitectura Mermaid Modernizados:** Actualización integral de sintaxis Mermaid obsoleta `graph TD` / `graph LR` a `flowchart TD` / `flowchart LR` en especificaciones y manuales, habilitando control de dirección por subgrafos y compatibilidad con versiones modernas de renderizadores.
  - **Tipado Estricto Frontend (`vue3/src/utils/security.ts`):** Refactorización de la función de sanitización DOM `escapeHtml` mediante discriminación de tipos (*Type Narrowing*), eliminando la advertencia `@typescript-eslint/no-base-to-string` y protegiendo la conversión contra objetos con prototipo nulo (`Object.create(null)`).
  - **Limpieza de Arquitectura de Pruebas Frontend:** Eliminación de la carpeta huérfana de scaffolding `vue3/tests/` consolidando la arquitectura oficial de pruebas unitarias co-localizadas en `src/` (`*.unit.ts`, 38 archivos y 267 pruebas unitarias 100% aprobadas) y actualización de patrones en `vue3/package.json`.
  - **Prevención de Secretos en Git Hooks (`lefthook.yml` y `verificar-secretos.sh`):** Extracción del comando de detección preventiva de secretos hardcodeados al script ejecutable independiente `verificar-secretos.sh` con auditoría ShellCheck aprobada (`0` errores, `0` advertencias) y normalización de sintaxis YAML en `lefthook.yml`.
  - **Certificación de Cobertura Backend:** Suite de backend en 404 pruebas unitarias aprobadas (`pytest`) con `95.07%` de cobertura de código fuente en `src/` y 0 errores en `ruff` y `mypy --strict`.
- **Auditoría Integral de Ciberseguridad y Mitigación de Vulnerabilidades (FastAPI + Vue 3):**
  - **Desacoplamiento y Robustecimiento de Middleware Anti-CSRF:** Refactorización de `CSRFProtectionMiddleware` (`fastapi/src/core/csrf.py`) para extraer la sesión directamente de las cookies (`__Host-rg_at` / `rg_at`) de forma independiente del ciclo de inyección `request.state`, previniendo omisiones (*bypasses*). Se alinea con las directrices OWASP CSRF Prevention eximiendo de validación CSRF a las peticiones con cabecera `Authorization: Bearer` (usadas por clientes no basados en navegador como agentes IA, scripts de automatización o el endpoint MCP `/api/v1/mcp`).
  - **Sanitización Estricta Anti-XSS en Capa Cartográfica Leaflet / OpenStreetMap:** Creación de la utilidad `escapeHtml` (`vue3/src/utils/security.ts`) con 18 pruebas unitarias y aplicación obligatoria en `OsmRouterMap.vue` y `OsmOnuMap.vue`, sanitizando cualquier metadato dinámico (`display_name`, `ros_identity`, `serial_number`, `physical_location`) antes de asignarlo a `popupContent.innerHTML`.
  - **Validación Anti-SSRF en Direccionamiento de Routers MikroTik:** Implementación de `validate_router_target_url` en esquemas Pydantic (`CreateRouterRequest`, `UpdateRouterRequest`, `CsvCommitRowItem`) y en el asistente CSV masivo (`validate_single_csv_row`), bloqueando de forma exhaustiva loopback (`127.0.0.0/8`, `::1`), metadatos de nube y link-local (`169.254.0.0/16`, `fe80::/10`) y nombres de contenedor Docker internos (`localhost`, `rosgrid-db`, `rosgrid-redis`, `rosgrid-keydb`, `rosgrid-api`, `rosgrid-worker`).
  - **Tolerancia a Carreras Concurrentes (*Grace Period Leeway*) en Rotación de Refresh Tokens:** Incorporación del parámetro `ROSGRID_REFRESH_TOKEN_GRACE_PERIOD_SECONDS` (5 segundos por defecto) en `rotate_refresh_token` (`src/redis_layer/sessions.py`) y `.env.example`, eliminando falsos positivos de `REUSE_DETECTED` y revocaciones accidentales de sesión ante refrescos simultáneos o pestañas múltiples en el navegador.
  - **Aislamiento Multi-Tenant y por Operador en Llaves de Idempotencia:** Refactorización de `IdempotencyMiddleware` para decodificar los claims de tenant y usuario del JWT (`rg:{tenant_id}:{user_id}:idemp:{key}`), previniendo cualquier colisión o interferencia cruzada entre empresas u operadores.
  - **Endurecimiento de CORS en Desarrollo:** Restricción de la expresión regular de desarrollo a `^https?://(localhost|127\.0\.0\.1)(:\d+)?$`.
- **Exposición, Armonización y Documentación de Variables de Entorno en Docker Compose y `.env.example`:**
  - Inclusión explícita de `ROSGRID_INSTALL_DIR` (`/opt/rosgrid` por defecto) en `.env.example`, permitiendo personalizar el directorio de instalación desatendida en modo standalone vía `instalar-rosgrid.sh`.
  - Incorporación en `.env.example` de `POSTGRES_HOST` (`rosgrid_db`), `POSTGRES_PORT` (`5432`), `REDIS_HOST` (`rosgrid_redis`), `REDIS_PORT` (`6379`) y `VITE_API_BASE_URL` (`http://localhost:8080`), habilitando la conexión nativa a bases de datos o clústeres Redis externos sin alterar los manifiestos YAML.
  - Armonización e inyección bidireccional en `docker-compose.yml`, `docker-compose.prod.yml` y `docker-compose.prod.local.yml` de los parámetros operativos de FastAPI y Celery/Worker (`ROSGRID_MIKROTIK_TIMEOUT_SECONDS`, `ROSGRID_SAFEMODE_ROLLBACK_SECONDS`, `ROSGRID_BACKUP_RETENTION_DAYS`, `ROSGRID_MCP_ENABLED`, `ROSGRID_MCP_RATE_LIMIT_PER_MIN`, `ROSGRID_CORS_ORIGINS`, `ROSGRID_CROSS_ORIGIN_COOKIES`, `TZDATA`, `restart`).
  - Detección inteligente de entorno en el script de instalación (`instalar-rosgrid.sh`): en modo local busca y carga automáticamente el archivo `.env` previo (respetando personalizaciones del operador), mientras que en modo remoto standalone (`curl | bash`) opera limpiamente con los valores por defecto del sistema.
  - Sincronización exhaustiva de la tabla 2.1 del *Catálogo Completo de Variables* en `docs/01_GUIA_DESPLIEGUE_Y_ENTORNO.md` e `INSTALL.md`.
- **Migración Integral de Runtime a Python 3.15 y Node.js 26 LTS (Hito 22.11):**
  - **Backend (`fastapi/`):** Migración oficial a la imagen base corporativa inmutable `sinfallas/base-python-uv:3.15`, soporte de CPython Free-Threaded (PEP 703 Tier-1), PEP 649 (evaluación diferida de anotaciones) y actualización de metadatos en `pyproject.toml` (`requires-python = ">=3.15"`).
  - **Frontend (`vue3/`):** Migración oficial a la imagen base corporativa inmutable `sinfallas/base-node-ionic:26`, adopción del motor V8 14.x y declaración de gobernanza en `package.json` (`"engines": { "node": ">=26.0.0", "pnpm": ">=9.0.0" }`).
  - **Orquestadores y Manifiestos:** Sincronización de `docker-compose.yml`, `fastapi/docker-compose.qa.yml`, `vue3/docker-compose.qa.yml`, `examples/` y Dockerfiles de producción.
  - **Documentación de Investigación:** Actualización de `docs/10_REPORTE_INVESTIGACION_PYTHON_3_15.md` y `docs/11_REPORTE_INVESTIGACION_NODE_26.md` a estado *"Migración Ejecutada e Implementada en RoSGrid"*.
- **Consolidación y Completitud del Registro Histórico de Certificación en `TESTING.md`:**
  - Incorporación en la tabla del *Registro Histórico de Certificación por Hitos* (Sección 4) de todos los hitos previamente no desglosados (Hitos 4 al 10, Hito 14, Hito 15B, Hitos 16 al 20, y sub-hitos 22.1 a 22.11), alcanzando una cobertura histórica continua del 100% de la plataforma.
  - Adición de las secciones de detalle estructural faltantes (Secciones 6 a 10 y Sección 21), certificando:
    - Sección 6: Hitos 4 al 6 (Conector RouterOS v7, SSL TOFU, Safe Mode 60s, Inventario, Asistente CSV y Bóveda Step-Up 30s).
    - Sección 7: Hitos 7 y 8 (Consola WebFig Capa 1: Interfaces, SFP DDM, IP, Firewall Drag & Drop, Routing BGP/OSPF, PPPoE y Queues).
    - Sección 8: Hitos 9 y 10 (Motor Universal WebFig Capa 2, Maker-Checker, Backups Git Diff, WebSockets y Optimización KeyDB Multi-Hilo).
    - Sección 9: Hitos 11 al 13 (Frontend Vue 3 Base, Stores Pinia `shallowRef`, Sistema de Diseño WinBox WCAG 2.1 AA, Canvas 2D y Endpoint MCP).
    - Sección 10: Hitos 14 y 15B (Documentación Técnica `docs/`, Graphify AST y Estabilización en Hardware Real RouterOS v7.21.5).
    - Sección 21: Hito 22.11 (Certificación Integral de Runtime Python 3.15 y Node.js 26 LTS).
  - Eliminación de discontinuidades numéricas en la bitácora y actualización de todas las referencias de imágenes efímeras de QA y producción.
- **Suite Completa de Pruebas BDD Karate Labs para el 100% de la Interfaz Web:**
  - Expansión de `vue3/test/ui_business_flow.feature` de 1 a **16 escenarios BDD exhaustivos** que cubren de extremo a extremo todas las pantallas, funcionalidades y flujos de usuario del sistema:
    1. Login Zero-Trust & Enrolamiento Obligatorio 2FA TOTP (`/login`).
    2. Tablero Principal NOC, Franja de KPIs y Refresco de Flota (`/`, `/dashboard`).
    3. Inventario Centralizado de Routers, Búsqueda Táctica y Filtros (`/inventory`).
    4. Consola WebFig v7 de Doble Capa, Pestañas `<KeepAlive :max="5">` y Telemetría en Vivo (`/routers/:id/webfig/live`).
    5. Bandeja de Aprobaciones Maker-Checker con Intercepción HTTP 202 (`/operations/approvals`).
    6. Historial de Backups Cifrados, Descarga Binaria `.backup` y Comparador Git Diff `.rsc` (`/backups`).
    7. Operaciones Masivas, Golden Templates y Actualizador de Paquetes (`/bulk-ops`).
    8. Wallboard NOC "Mission Control", Mapa OSM y Alertas Sonoras en Vivo (`/noc-wallboard`).
    9. Bitácora Inmutable WORM, Hashchain SHA-256 y Certificación Forense (`/audit-logs`).
    10. Gestión Multi-Tenant, Cuotas de Routers y Feature Flags Modulares (`/admin/tenants`).
    11. Matriz de Permisos RBAC por Técnico y Control de Auto-Registro (`/users`).
    12. Monitor de Sesiones Activas y Kill-Switch de Expulsión en Tiempo Real (`/sessions`).
    13. Gestión de Direccionamiento IPAM Universal Dual-Stack IPv4/IPv6 (`/ipam`).
    14. Toolkit de Campo Móvil Responsive para Técnicos e Instaladores (`/field-ops`).
    15. Mapa Cartográfico Táctico de Abonados y Detección de Caída Masiva (`/subscribers/map`).
    16. Suite de Cumplimiento Normativo Corporativo (CIS Benchmark, Config Drift y SD-WAN) (`/enterprise/compliance`).
  - Sincronización idéntica de la suite en `examples/vue3/test/ui_business_flow.feature`.
  - Agregado del botón táctico de refresco de flota y su indicador reactivo en `DashboardHomeView.vue`.
  - Validación completa en contenedor QA (`vue-tsc --noEmit` = 0 errores, Prettier = 100% aprobado, Vitest = 38 suites y 262 pruebas pasadas).
- **Suite Completa de Pruebas BDD Karate Labs para el 100% de la API REST FastAPI:**
  - Expansión de `fastapi/test/api_test.feature` de 11 a **54 escenarios BDD exhaustivos** que cubren la totalidad de los 35 submódulos y endpoints de la API REST de RoSGrid:
    - Observabilidad y salud del sistema (`/health`, `/metrics`, `/users/me`).
    - Ciclo de vida de autenticación, bootstrap, 2FA TOTP y rotación de tokens (`/api/v1/auth/*`).
    - Gestión de empresas multi-tenant y panel de feature flags modulares (`/api/v1/tenants/*`).
    - Administración de usuarios, aprobación Maker-Checker y switch de registro (`/api/v1/users/*`).
    - Sesiones activas y kill-switch de revocación en tiempo real (`/api/v1/sessions/*`).
    - Inventario de routers, redescubrimiento TOFU, roles y asistente CSV (`/api/v1/inventory/*`).
    - Bóveda de credenciales con Step-Up 2FA (30s) y rotación de claves (`/api/v1/inventory/routers/{id}/vault/*`).
    - Direccionamiento IPAM dual-stack IPv4/IPv6 y gestión de pools (`/api/v1/ipam/*`).
    - Perfiles de ancho de banda QoS y dispositivos abonados ONUs (`/api/v1/bandwidth-profiles/*`, `/subscriber-devices/*`).
    - Aprovisionamiento técnico de red con cabecera obligatoria `Idempotency-Key` UUIDv7 (`/api/v1/network-services/*`).
    - Operaciones de campo móvil y telemetría óptica láser SFP DDM (`/api/v1/field-ops/*`).
    - Programación de ventanas de mantenimiento para silenciado de alertas (`/api/v1/maintenance-windows/*`).
    - Consola WebFig v7 de Capa 1 y Capa 2 (Interfaces, IP, Firewall Drag & Drop, Routing BGP/OSPF, PPP, Queues, System, Tools y Layer 2 dynamic proxy).
    - Bandeja de aprobaciones Maker-Checker con intercepción HTTP 202 (`/api/v1/operations/approvals/*`).
    - Respaldos históricos de 30 días, comparador Git Diff y descarga binaria `.backup` (`/api/v1/routers/{id}/backups/*`).
    - Operaciones masivas con plantillas maestras y actualización de paquetes (`/api/v1/operations/bulk/*`).
    - Canales de notificación con webhooks salientes firmados HMAC-SHA256 (`/api/v1/notifications/channels/*`).
    - Bitácora inmutable WORM y verificación matemática de cadena SHA-256 (`/api/v1/audit/*`).
    - Servidor MCP protegido para agentes IA con validación JSON-RPC 2.0 y límite de tasa (`/api/v1/mcp`).
    - Diagnóstico 360°, BGP Looking Glass y analítica de anomalías IPFIX (`/api/v1/diagnostics/*`, `/bgp/*`, `/traffic-flow/*`).
    - Suite corporativa de ciberseguridad: CIS Benchmark, Config Drift, SD-WAN WireGuard, Switching Rogue DHCP, SLA de carriers y WiFi CAPsMAN (`/api/v1/compliance/*`, `/sdwan/*`, `/switching/*`, `/sla/*`, `/wifi/*`, `/rbac/*`).
  - Sincronización idéntica de la suite en `examples/fastapi/test/api_test.feature`.
- **Integración Exhaustiva de Diagramas Mermaid en Toda la Documentación Oficial:**
  - Inserción de diagramas Mermaid en `README.md` (arquitectura de alto nivel), `INSTALL.md` (árbol de instalación y despliegue), `SECURITY.md` (8 capas de defensa en profundidad) y los manuales técnicos del sistema (`docs/01` al `docs/09`), clarificando topologías de red, protocolos criptográficos (Safe Mode 60s, WORM SHA-256 con índice BRIN, TOFU Pinning, Split-Credential 2FA, Kill-Switch, WebSockets Pub/Sub y compuertas UAT 11X).
- **Reportes Técnicos de Investigación sobre Próximas Versiones Corporativas:**
  - `docs/10_REPORTE_INVESTIGACION_PYTHON_3_15.md`: Análisis técnico sobre CPython Free-Threaded (No-GIL PEP 703 Tier-1), compilador Tier-2 JIT Copy-and-Patch, PEP 649 (evaluación diferida de anotaciones de tipo) y hoja de ruta de adopción de la imagen `sinfallas/base-python-uv:3.15`.
  - `docs/11_REPORTE_INVESTIGACION_NODE_26.md`: Análisis técnico sobre Node.js 26 LTS (Native Type Stripping, motor V8 14.x, Temporal API nativa, Corepack desacoplado) y hoja de ruta de adopción de la imagen `sinfallas/base-node-ionic:26`.
- **Asistente de Instalación Standalone Remoto (`instalar-rosgrid.sh` vía `curl | bash`):**
  - Soporte para instalación turnkey en 1 solo comando: `curl -fsSL https://raw.githubusercontent.com/tecno-consultores/RoSGrid/main/instalar-rosgrid.sh | bash`.
  - Modo dual inteligente: detección automática entre repositorio local clonado y entorno remoto standalone.
  - Aprovisionamiento automático y seguro del directorio `/opt/rosgrid` (o `$ROSGRID_INSTALL_DIR`) con privilegios mínimos y asignación exclusiva al usuario no-root.
  - Descarga desatendida de manifiestos oficiales de producción (`.env.example` y `docker-compose.prod.yml`) desde la rama `main` de GitHub.
  - Compatibilidad de terminal interactiva mediante lectura directa desde `/dev/tty` para soportar prompts y asistente de creación de Super Administrador sobre tuberías estándar.
  - Generación de entropía y secretos criptográficos de 256 bits para PostgreSQL, KeyDB, Bóveda AES-256-GCM, JWT y CSRF con permisos estrictos `chmod 600 .env`.
  - Auditoría estática con ShellCheck (`koalaman/shellcheck:stable`) con 0 errores y 0 advertencias.
- **Endurecimiento de Seguridad Híbrida (FastAPI + Vue 3) y Protección contra Vectores de Ataque:**
  - **Mitigación de Cross-Site WebSocket Hijacking (CSWSH):** Validación previa obligatoria de la cabecera `Origin` (`_verify_ws_origin`) en los canales de telemetría (`/ws/v1/routers/{id}/live-telemetry`) y eventos (`/ws/v1/tenant/events`) antes de aceptar el socket (`ws.accept()`), rechazando orígenes no autorizados o ausentes en producción con código `4403`.
  - **Sanitización de Errores de Validación Pydantic (Anti-Enumeración 422):** Manejador de excepciones `RequestValidationError` en FastAPI que en entornos de producción oculta rutas internas de campos, nombres de columnas y expresiones regulares, devolviendo un mensaje genérico sanitizado.
  - **Consultas Parametrizadas Seguras en Servidor MCP:** Eliminación de interpolación cruda `f-string` en consultas SQL de cambio de contexto de inquilino (`SET LOCAL app.current_tenant_id`), sustituyéndola por llamadas enlazadas a `set_tenant_context()`.
  - **Protección Anti-SSRF en Despacho de Webhooks:** Validador `is_safe_webhook_url()` en `alert_dispatcher_worker.py` bloqueando loopback, rangos de IP privadas RFC 1918 e IPs de metadatos de nube (`169.254.169.254`).
  - **Límite de Carga de Archivos (Anti-DoS en Memoria):** Validación estricta de tamaño máximo de 2 MB en cargas CSV de onboarding (`/inventory/import-csv/commit`).
  - **Endurecimiento de CORS en Producción:** Bloqueo de combinaciones laxas de wildcard con credenciales (`allow_origins=[]`, `allow_credentials=False`) en entornos productivos.
  - **Sincronización de Proxy Inverso Nginx:** Inclusión de `X-Forwarded-For` y `X-Forwarded-Proto` en la directiva `location /ws/` de `vue3/nginx/default.conf`.
  - **Plantilla Predefinida de Cliente NTP:** Configuración masiva de sincronización horaria mediante NTP en routers MikroTik.
- **Auditoría Forense de Intentos Fallidos y Política de Sesión Única:**
  - Registro forense inmutable WORM HMAC-SHA256 para todos los eventos e intentos fallidos de autenticación (`LOGIN_FAILED_USER_NOT_FOUND`, `LOGIN_FAILED_INVALID_PASSWORD`, `LOGIN_FAILED_ACCOUNT_LOCKED`, `LOGIN_FAILED_USER_INACTIVE`, `2FA_VERIFICATION_FAILED`) con IP y User-Agent del actor.
  - Forzado estricto de la política de sesión única en KeyDB: revocación automática de sesiones activas anteriores ante un nuevo inicio de sesión con emisión de evento forense `SESSION_KILLED_DUPLICATE_LOGIN` y notificación vía WebSockets.
  - Registro de auditoría `LOGIN_SUCCESSFUL` al establecer exitosamente la sesión.
- **Gobernanza de Empresas / Tenants y Navegación:**
  - Reubicación de la sección "Empresas (Tenants)" en el menú lateral principal (`RgResponsiveShell.vue`) directamente debajo de "Auditoría WORM" accesible exclusivamente para `SUPERADMIN_GLOBAL`.
  - Protección y desacoplamiento de la acción `+ Registrar Empresa` (`#btn-open-create-tenant`) en `TenantsManagementView.vue` condicionado al rol `SUPERADMIN_GLOBAL`.
  - Sincronización y documentación exhaustiva de los endpoints CRUD de Tenants (`GET /api/v1/tenants`, `POST /api/v1/tenants`, `PATCH /api/v1/tenants/{tenant_id}`) en la especificación de la API REST (`docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md`).
- **Servidor MCP Ampliado para Agentes IA (Hito 21):**
  - Expansión del catálogo de herramientas semánticas del servidor Model Context Protocol integrado (`POST /api/v1/mcp`) de 8 a 16 herramientas con esquemas Pydantic v2 y validación JSON-RPC 2.0 *Streamable HTTP*.
  - 8 nuevas herramientas semánticas para agentes inteligentes (Hermes Agent, Claude Code / Desktop, NOC Autónomo):
    1. `rosgrid_run_360_diagnostics`: Suite diagnóstica 360° (Ping multi-MTU con DF-bit, análisis de causas de desconexión en logs de RouterOS y muestreo Torch en vivo).
    2. `rosgrid_isolate_subscriber`: Aislamiento técnico idempotente de servicios de red en firewall `AISLADOS_TECNICO` o cola 64k.
    3. `rosgrid_restore_subscriber`: Restauración técnica idempotente y reanudación de perfiles de velocidad nominales.
    4. `rosgrid_change_rate_limit` (alias `rosgrid_change_subscriber_rate_limit`): Conmutación en caliente de perfiles QoS / Simple Queue sin desconexión física.
    5. `rosgrid_query_bgp_looking_glass`: Consulta no interactiva de tablas de rutas BGP v7 y prefijos anunciados a peers de tránsito.
    6. `rosgrid_check_config_drift`: Comparación y detección semántica de desviación de configuración contra Golden Baseline Templates.
    7. `rosgrid_run_cis_audit`: Auditoría automatizada de directivas críticas CIS Benchmark con cálculo de Security Score (0-100).
    8. `rosgrid_detect_mass_outage`: Motor de correlación de cortes de fibra óptica y caídas masivas en ramas PON y cajas NAP.
  - Certificación integral QA 11X en Docker: 389 pruebas unitarias de backend con 95.0% de cobertura de código fuente, 99.0% de cobertura en `src/api/v1/mcp.py` y complejidad ciclomática Radon Grado A (promedio 2.9, máxima CC <= 5 por función).
- **Hub de Monitoreo Táctico "Mission Control":**
  - Panel integrado en Wallboard con telemetría en vivo, consumo agregado de ancho de banda (Tx/Rx), distribución de flota por roles de red y latencia de sondas.
  - Transiciones cinemáticas fluidas aceleradas por hardware entre vistas (Wallboard, Inventario, WebFig).
  - Integración de apertura directa de WebFig desde el popup del mapa geográfico de Wallboard.
- **Gestión Avanzada de Respaldos y Comparador Visual Diff:**
  - Selección interactiva directa sobre cualquier tarjeta de respaldo de los últimos 30 días para comparaciones base/objetivo con badges de estado `[🔵 BASE]` y `[🟢 OBJETIVO]`.
  - Detección precisa de archivos `.backup` binarios vs scripts `.rsc` y descarga con encoding binario `application/octet-stream`.
- **Roles de Red Personalizados y Auto-Registro Dinámico en CSV:**
  - Endpoint `POST /api/v1/inventory/roles` para crear y listar roles personalizados de infraestructura MikroTik.
  - Auto-registro seguro en base de datos (`tenant_custom_roles`) de roles de red no predefinidos cuando se importan equipos por archivo CSV.
- **Suite Corporativa — Cumplimiento Normativo, SD-WAN y WiFi (Hito 20):**
  - **Detección y Reversión de Config Drift:** Comparador semántico contra Plantilla Maestra (*Golden Baseline Template*), visor de diferencias Git Diff interactivo en rojo/verde y remediación en 1 clic (*Auto-Revert*) bajo Safe Mode (60s) con registro de auditoría WORM HMAC-SHA256.
  - **Orquestador SD-WAN WireGuard Hub & Spoke:** Aprovisionamiento dinámico de enlaces con subredes `/31` o `/30`, inserción automática de llaves públicas/privadas y conmutación de fallos Multi-WAN recursiva mediante scripts `netwatch` en RouterOS v7.
  - **Auditoría de Seguridad & Endurecimiento CIS Benchmark:** Evaluación automatizada de 10 directivas críticas de seguridad para RouterOS, cálculo de Security Score (0-100), determinación de grado de cumplimiento (A-F) y auto-endurecimiento (*Auto-Hardening*) preventivo.
  - **Detección de Rogue DHCP & Seguridad L2:** Monitoreo y telemetría de eventos de DHCP Snooping en bridges MikroTik, mapeo de puertos de confianza/desconfianza, alertas de servidores rogue no autorizados con dirección MAC y aislamiento de puerto en 1 clic bajo Safe Mode.
  - **Monitor de Cumplimiento de SLA para Enlaces Dedicados:** Ejecución de ciclos de sondeo recursivos de latencia mínima/promedio/máxima/p95/p99, cálculo de jitter según RFC 3550, evaluación de umbral de cumplimiento contractual y exportador de informes oficiales de SLA en formato estructurado para reclamos de penalización a carriers.
  - **Gestión Centralizada de WiFi Corporativo (CAPsMAN / WiFiWave2):** Visión general de radios y APs gestionados, orquestación de perfiles SSID (WPA3-Enterprise 802.1X, Invitados, IoT) y telemetría de clientes en tiempo real con niveles de señal RSSI, SNR y trazabilidad de fast roaming 802.11r/k/v.
  - **Interfaz de Usuario Táctica (`EnterpriseComplianceView.vue`):** Nueva vista unificada en `/enterprise/compliance` con 6 pestañas interactivas, integración completa con el selector de flota, badge de Safe Mode de 60s y soporte de internacionalización (i18n).
- **Mapas Separados, Telemetría Efímera de Última Milla e i18n (Hito 19):**
  - **Mapa Exclusivo de Clientes/ONUs (`/subscribers/map`):** Componente `OsmOnuMap.vue` desacoplado del mapa de infraestructura, con telemetría Zero-Metrics (🟢 Óptimo < 40ms 0% pérdida, 🟠 Degradado 40-120ms o 1-20% pérdida, 🔴 Caído > 20% pérdida o timeout), spiderfier interactivo para cajas NAP / coordenadas agrupadas, y accesos rápidos a *Test 1-Click* y *Diagnóstico 360°*.
  - **Alerta de Caída Masiva (Mass Outage Alert):** Detección en segundo plano según `tenant.mass_outage_threshold` (por defecto 10), aviso prioritario en tiempo real al Wallboard NOC mediante WebSockets y sintetizador sonoro Web Audio API, con registro en auditoría WORM inmutable encadenada con HMAC-SHA256.
  - **Rediseño Responsive Táctico de Calle (`FieldTechMobileView.vue`):** Supresión de la restricción fija de 480px a favor de un layout 100% fluido en móvil (<768px), tablet (2 columnas) y laptop/desktop (3 columnas con diagnóstico 360° integrado), captura GPS prominente con georreferenciación de ONUs activadas y firma digital en canvas.
  - **Internacionalización Modular (i18n):** Composable reactivo `useI18n()` con diccionarios `es.json` y `en.json`, conmutador táctico en la cabecera del shell (`#btn-global-lang-toggle`), sincronización con `document.documentElement.lang` y persistencia en `localStorage`.
- **Facilidad de Instalación y Documentación de Almacenamiento S3:**
  - Mejoras en `instalar-rosgrid.sh` para detección y muestra exacta del puerto asignado en modo producción local (8085) vs oficial (8080).
  - Documentación técnica sobre arquitectura de almacenamiento de respaldos en base de datos PostgreSQL vs AWS S3 / MinIO con cifrado `AES-256-GCM` del lado del cliente.

### Fixed

- **Descarga de Respaldos Binarios `.backup`:** Corrección del endpoint para evitar servir scripts `.rsc` renombrados cuando no existe respaldo binario nativo, y configuración de `responseType: 'blob'` en frontend para prevenir corrupción de bytes.
- **Botón "Abrir WebFig" en Wallboard:** Conexión del evento `@open-webfig` entre `OsmRouterMap` y el enrutador de Vue para navegación inmediata al router seleccionado.

### Pendiente para publicación oficial

- Auditoría final de vulnerabilidades Trivy (`CRITICAL,HIGH = 0`) en imágenes Docker de producción (Hito 16).
- Publicación multi-arquitectura con `./build.sh` hacia Docker Hub (`sinfallas/rosgrid-backend:1.0.0` y `sinfallas/rosgrid-frontend:1.0.0`).

---

## [1.0.0-rc.2] - 2026-10-17

### Added (v1.0.0-rc.2)

- **Flujo de Auto-Registro Web de Operadores y Aprobación Maker-Checker:**
  - Formulario público accesible en `LoginView.vue` para solicitar acceso (`POST /api/v1/auth/register`).
  - Bloqueo preventivo HTTP 403 a usuarios con estado `PENDING_APPROVAL`.
  - Pestaña de "Solicitudes Pendientes" en `UsersAndPermissionsView.vue` con aprobación (`PUT /api/v1/users/{id}/approve`) y asignación de rol por Superadmin.
  - Switch global de activación/desactivación de auto-registro en KeyDB (`rosgrid:registration_enabled`).
- **Botón de Redescubrimiento Dinámico TOFU:**
  - Botón táctil en la grilla de Inventario que invoca `POST /api/v1/inventory/routers/{id}/discover`.
  - Detección en vivo de hardware, arquitectura, versión de RouterOS y fijación de huella SSL TOFU SHA-256 sin recargar página.
- **Suite Automatizada de Validación Front-Back (`validar_comunicacion_front_back.py`):**
  - 24 contratos de prueba verificando exhaustivamente que todas las rutas y funciones de la UI se comunican con FastAPI y con el MikroTik físico/CHR (100% de éxito).

### Fixed (v1.0.0-rc.2)

- **Compatibilidad con RouterOS v7.13+ (`rest-api` Policy):**
  - Detección y normalización de error HTTP 401 debido a la ausencia del flag `rest-api` en el grupo de usuarios de RouterOS v7.13+.
  - Documentación detallada en manuales operativos.
- **Visualización de Mapas OpenStreetMap:**
  - Corrección de cabeceras Content Security Policy (CSP) en Nginx para permitir la carga de teselas cartográficas de `*.tile.openstreetmap.org`.
  - Ajuste de estilos CSS en Leaflet para evitar estiramiento vertical infinito en pantallas de gran resolución.
- **Resiliencia de Inmutabilidad WORM en Rechazo de Usuarios:**
  - Modificación del flujo de rechazo (`DELETE /api/v1/users/{id}/reject`) para aplicar soft-revocación segura en caso de que existan eventos en `audit_logs` con clave foránea, impidiendo violaciones del trigger inmutable de PostgreSQL.
- **Telemetría y Pestañas de WebFig en Hardware Real:**
  - Corrección de mapeo de métricas reales de CPU, memoria y lectura de 10 interfaces vivas desde el router físico/CHR.

---

## [1.0.0] - 2026-10-15

### Added (Nuevas Características)

- **Arquitectura Multi-Tenant con Aislamiento RLS e Índice BRIN:** Esquema en PostgreSQL 17 con `FORCE ROW LEVEL SECURITY` inyectando `app.current_tenant_id` por sesión transaccional, índice `BRIN` de alta velocidad sobre `audit_logs(created_at)` y migraciones automáticas protegidas por `pg_advisory_lock`.
- **Motor en Memoria KeyDB Multi-Hilo y Perfil DragonflyDB:** Configuración predeterminada con `eqalpha/keydb:alpine` (`--server-threads 2`), serialización rápida en Rust con `ORJSONResponse`, event loop `uvloop` + `httptools`, pipelines en lote y soporte documentado para **DragonflyDB** en despliegues ISP de gran escala.
- **Matriz RBAC de 11 Roles y Asignación Granular:** Soporte nativo para `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`, `SUPERVISOR`, `SUPPORT_L3`, `SUPPORT_L2`, `SUPPORT_L1`, `FIELD_TECH`, `INVENTORY_MANAGER`, `AUDITOR`, `NOC_MONITOR` y `SERVICE_ACCOUNT`.
- **Conector Asíncrono RouterOS v7 (`/rest/*`) con Pool TLS Keep-Alive:** Cliente `httpx` sobre TLS con reutilización de conexiones persistentes, fijación de certificados autofirmados *Trust On First Use* (`SHA-256` TOFU) y protección anti-bloqueo **Safe Mode (*Dead Man's Switch*)** mediante `/system/scheduler` a 60 segundos.
- **Inventario Georreferenciado e Importador Masivo CSV:** Autodescubrimiento de hardware RouterBOARD, mapa interactivo gratuito con **Leaflet + OpenStreetMap** y asistente de importación CSV en 2 etapas (`dry-run` y `commit`).
- **Consola WebFig de Doble Capa (RouterOS v7.1+):**
  - **Capa 1 Especializada:** Interfaces, diagnóstico óptico **SFP/SFP+ DDM** (`dBm`), VLANs, Bridges, WireGuard, IP/Routes ECMP, DHCP Leases, Firewall con reordenamiento *Drag & Drop* + teclado accesible (`Alt+Up`/`Alt+Down`), BGP/OSPF v7, PPPoE Active, Simple Queues, System y Tools en vivo (Ping, Traceroute, Torch, Log).
  - **Capa 2 Universal:** Inspector dinámico de esquemas y CRUD autogenerado para el resto de submenús `/rest/*` de RouterOS v7 (MPLS, ZeroTier, Containers, CAPsMAN, SNMP, Certificates).
- **Interfaz Vue 3 de Alta Densidad Técnica y Alto Rendimiento (WCAG 2.1 AA):**
  - Sistema de diseño con 3 temas nativos (`dark` *Tactical NOC Cyan*, `light` de campo y `noc-high-contrast` para pantallas de monitoreo), tipografía numérica `tabular-nums`, stores con `shallowRef` y buscador global `Ctrl + K`.
  - **Densidad Dual Adaptativa y *Virtual Scrolling* en Tablas (`RgDataTable.vue`):** Filas compactas de `32px` estilo WinBox en PC (`>= 1024px`) con insignias `[D]`/`[X]`/`[I]`/`[R]`, modo táctil de `44px` en móvil/tablet (`< 1024px`) y virtualización del DOM para tablas mayores a 100 filas.
  - **Navegación Multi-Pestaña con Memoria (`<KeepAlive :max="5">`):** Conservación en RAM de filtros y estados al alternar entre vistas internas de un router, más barra de navegación inferior fija en móviles.
- **Gráficas Efímeras Estilo WinBox (`TelemetryRingBuffer` + `<canvas>` 2D):** Multiplexor WebSocket bajo demanda (`SCARD >= 1`), buffer circular en memoria RAM del navegador (hasta 5,400 puntos / 3 horas a 1 tick cada 2s) renderizado con `requestAnimationFrame` y cero almacenamiento histórico en base de datos.
- **Gobernanza Operativa (*Maker-Checker*), Backups Diff Git y Acciones Masivas:**
  - Interceptor de las 7 categorías críticas con segregación estricta de funciones (`maker != checker`).
  - Respaldos `.rsc` nocturnos/manuales con deduplicación `SHA-256`, retención de 30 días y comparador visual lado a lado estilo Git (`unified_diff`) contra respaldos previos o contra el estado `LIVE`.
  - Plantillas (*Golden Configs*), trabajos masivos multi-router y actualizador centralizado de RouterOS v7 con pre-backup obligatorio.
- **Alertas Multi-Canal *Zero-Storage* y Wallboard NOC:** Máquina de estados efímera en KeyDB (~200 bytes/router), respeto de ventanas de mantenimiento y despacho a Telegram Bot, Correo SMTP, Webhooks firmados (`HMAC-SHA256`) y pantalla NOC 24/7.

### Security (Seguridad Criptográfica y DevSecOps)

- **Modelo *Split-Credential* y Bóveda `AES-256-GCM`:** Credenciales API cifradas con `AAD` (`tenant_id|router_id`), rotación transaccional automática de claves de 32 caracteres y revelación restringida con **Step-Up Auth (2FA TOTP en vivo)** y autodestrucción en memoria a los 30 segundos.
- **Sesiones Blindadas y *Kill-Switch* en Vivo:** Contraseñas con `Argon2id`, cookies `__Host-` (`HttpOnly; Secure; SameSite=Strict`), protección `X-CSRF-Token` (`HMAC-SHA256`), detección de robo de Refresh Token en KeyDB y expulsión instantánea de sesiones activas.
- **Bitácora Forense Inmutable WORM (`audit_logs`):** Trigger en PostgreSQL que impide `UPDATE`/`DELETE`/`TRUNCATE`, cadena criptográfica `SHA-256` (`prev_record_hash`), sanitización automática `[REDACTED]` y verificador matemático de integridad para el rol `AUDITOR`.
- **Imágenes de Producción Endurecidas (Non-Root):** Contenedores multi-stage auditados con Trivy (`HIGH,CRITICAL = 0`), desactivación de Swagger/ReDoc en producción (`ROSGRID_ENV=production`), bloqueo de scripts de post-instalación en `.npmrc` (`ignore-scripts=true`) y omisión deliberada de terminales interactivas SSH/Telnet para preservar la trazabilidad WORM y el control RBAC.
