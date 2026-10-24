# 📋 Historial de Cambios (Changelog) — RoSGrid

Todos los cambios notables en las versiones oficiales de **RoSGrid** (y en sus imágenes inmutables de Docker Hub `sinfallas/rosgrid-backend` y `sinfallas/rosgrid-frontend`) se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/), y este proyecto se adhiere a [Semantic Versioning (SemVer)](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed

- **Centralización de Scripts Operativos en `scripts/` y Consolidación de Guías en `docs/`:**
  - **Reubicación de Scripts Raíz:** Migración de los 7 scripts ejecutables de la raíz hacia el directorio dedicado `scripts/` (`scripts/auditar-infra.sh`, `scripts/build.sh`, `scripts/instalar-hooks.sh`, `scripts/instalar-rosgrid.sh`, `scripts/limpieza.sh`, `scripts/probar-prod-local.sh` y `scripts/verificar-secretos.sh`), con resolución dinámica de rutas (`REPO_ROOT` y `SCRIPT_DIR`) para garantizar ejecución transparente e idéntica tanto desde la raíz del proyecto como desde `scripts/`.
  - **Consolidación de Documentos de Soporte e Instalación:** Reubicación de los manuales de la raíz `INSTALL.md`, `FAQ.md` y `RESOURCES.md` hacia `docs/` (`docs/INSTALL.md`, `docs/FAQ.md`, `docs/RESOURCES.md`), actualizando rutas relativas a manuales complementarios y simplificando el árbol de la raíz.
  - **Alineación de CI/CD, Directivas de IA y Documentación Técnica:** Sincronización de hooks Git (`lefthook.yml`), directivas de agentes en `.agents/` (`AGENTS.md`, `.agents/README.md`, `.agents/rules/`, `.agents/scripts/certify_task_completion.sh`, `.agents/skills/`), guías de despliegue (`README.md`, `SECURITY.md`, `CONTRIBUTING.md`, `docs/01_GUIA_DESPLIEGUE_Y_ENTORNO.md`, `docs/07_...`, `docs/08_...`, `docs/09_...`), especificaciones (`docs/specs/00`, `01`, `29`, `31`, `35`, `qa-11x/`), bitácora `TESTING.md` y control de hitos en `ROADMAP.md`.

- **Reorganización Estructural del Repositorio y Consolidación Documental (`docs/specs/` y `docs/examples/`):**
  - **Limpieza de la Raíz del Monorepo:** Consolidación de las carpetas de especificaciones arquitectónicas (`specs/` $\to$ `docs/specs/`, 36 especificaciones y subdirectorio `qa-11x/`) y de plantillas canónicas (`examples/` $\to$ `docs/examples/`, blueprints para FastAPI y Vue 3) dentro del directorio unificado de documentación `docs/`.
  - **Sincronización Total de Gobernanza y Agentes de IA:** Actualización completa de rutas y directivas en `AGENTS.md`, `.agents/README.md`, `.agents/rules/` (`mandatory_qa_pyramid_and_doc_sync.md`, `secure_development_and_testing_guidelines.md`, `frontend_parity_and_closure.md`), `.agents/scripts/certify_task_completion.sh` y `.agents/skills/graphify-docs-api-writer/SKILL.md`.
  - **Trazabilidad en Código Fuente y Documentos Raíz:** Actualizados todos los comentarios y docstrings de referencia en el backend (`enterprise.py`, `tenants.py`, `policy_matrix.py`, `sdwan.py`, `sla.py`, `switching.py`, `wifi.py`, pruebas unitarias) y frontend (`OsmOnuMap.vue`, `NocWallboardView.vue`, `SubscribersMapView.vue`, `eventFormatter.ts`), así como los índices maestros en `README.md`, `ROADMAP.md`, `TESTING.md`, `CONTRIBUTING.md` y `RESOURCES.md`.

### Added

- **Indicador Táctico de Disponibilidad de API (Heartbeat/Ping) y Caché en Memoria Anti-Thundering Herd (`main.py`, `httpClient.ts`, `useApiHeartbeatStore.ts`, `RgApiHealthBadge.vue`, `RgResponsiveShell.vue`, `LoginView.vue`):**
  - **Sonda Ligera y Caché en Memoria (FastAPI):** Optimizado el endpoint `GET /health` con una caché en memoria de 5.0 segundos controlada por `asyncio.Lock` en producción, evitando sobrecarga y consultas repetidas a PostgreSQL y KeyDB ante ráfagas concurrentes de sondeo, con soporte del parámetro de forzado `?force=true`.
  - **Monitoreo Pasivo y Cero Sobrecarga (Vue 3 Interceptor):** Incorporado en `httpClient.ts` el cálculo de latencia de cada petición y emisión del evento `rosgrid:api-health-event`, permitiendo a `useApiHeartbeatStore` mantener actualizado el estado `ONLINE` sin necesidad de realizar peticiones de sondeo adicionales mientras el usuario esté activo.
  - **Pausa por Inactividad y Sincronización entre Pestañas:** Integración con `Page Visibility API` (pausando el sondeo a 45s cuando la pestaña está minimizada u oculta) y canal nativo `BroadcastChannel('rosgrid_api_heartbeat')` para sincronizar el estado entre múltiples pestañas del operador sin duplicar tráfico de red.
  - **Componente Táctico con Popover Diagnóstico (`RgApiHealthBadge.vue`):** Indicador visual en la barra superior y pantalla de acceso (`ONLINE` en verde esmeralda con latencia en ms, `OFFLINE` en rojo de alerta NOC, `DEGRADED` en ámbar y `CHECKING` en cian), con popover interactivo accesible para inspeccionar el estado de la API, BD y KeyDB, y botón para forzar ping manual inmediato.
  - **Certificación QA 11X Integral:** Creadas pruebas unitarias dedicadas en backend (`test_health_cache.unit.py` con 100% de aserciones aprobadas) y frontend (`useApiHeartbeatStore.unit.ts`, `RgApiHealthBadge.unit.ts`, y `RgResponsiveShell.unit.ts` con 31 pruebas en Vitest), más escenarios BDD en Karate Labs: Escenario 69 en API (`fastapi/test/api_test.feature`) y Escenario 25 en UI (`vue3/test/ui_business_flow.feature`), sincronizados en `docs/examples/`.

- **Gobernanza de Calidad 11X — Invariante Obligatoria de Pruebas Karate Labs (`AGENTS.md`, `.agents/rules/`, `.agents/README.md`, `.agents/scripts/`):**
  - **Exigencia Estricta de Karate Labs en Cada Cambio:** Establecida la invariante incondicional en `AGENTS.md` (Directiva Suprema y Protocolo de 7 pasos), `mandatory_qa_pyramid_and_doc_sync.md` y `frontend_parity_and_closure.md`, obligando a todo agente de IA y desarrollador a crear o actualizar escenarios BDD de Karate Labs en `fastapi/test/api_test.feature` (API) y `vue3/test/ui_business_flow.feature` (UI) ante **CADA** cambio de código o endpoint.
  - **Sincronización Canónica con Blueprints:** Obligatoriedad de reflejar idénticamente cada nuevo escenario en los blueprints canónicos de `docs/examples/fastapi/test/` y `docs/examples/vue3/test/`.
  - **Auditoría Pre-Commit en Script de Certificación:** Ampliado `certify_task_completion.sh` con inspección automatizada de archivos `.feature` de Karate Labs en Git diff, emitiendo advertencia de bloqueo si se modifica código sin adjuntar escenarios BDD correspondientes.
  - **Expansión y Certificación Integral de Suites Karate Labs:** Cobertura ampliada a 68 escenarios BDD en API (`fastapi/test/api_test.feature`: descarga de plantilla CSV oficial, contratos de aprobación y rechazo Maker-Checker con `review_comment`, e interfaces Bridge L1) y 24 escenarios BDD en UI (`vue3/test/ui_business_flow.feature`: gestión de bridges WebFig con Safe Mode, menú de usuario y reloj en barra superior, enlaces a fuentes oficiales CVEs y descarga nativa CSV), 100% sincronizados con `docs/examples/`.

- **Sustitución de Feed Remoto CVE Obsoleto por Fuentes Oficiales MikroTik Security y Búsqueda NIST NVD (`config.py`, `cve_matcher.py`, `cve_catalog_ros.json`, `FleetCveMatrix.vue`):**
  - **Desacoplamiento del Endpoint Obsoleto NVD:** Eliminado el intento de consulta directa a la API REST bloqueada por Cloudflare/rate-limit de NIST (`https://services.nvd.nist.gov/rest/json/cves/2.0`).
  - **Integración del Feed Oficial MikroTik Security (`https://mikrotik.com/supportsec`):** Implementado parser XML de alta resiliencia para el feed RSS oficial de MikroTik (`https://cdn.mikrotik.com/web-assets/supportsec/rss.xml`), enriqueciendo dinámicamente el catálogo de vulnerabilidades con boletines vigentes y reglas de versiones RouterOS v7.
  - **Enlace a Búsqueda Oficial NIST NVD:** Incorporado enlace directo y trazabilidad a `https://nvd.nist.gov/vuln/search?keyword=mikrotik&resultType=records` como fuente secundaria de verificación.
  - **Enriquecimiento del Catálogo Base Local:** Actualizado el catálogo embebido (`cve_catalog_ros.json`) de 6 a 23 boletines oficiales verificados de RouterOS v7 (incluyendo CVEs críticos y altos de 2025 y 2026 como CVE-2026-88464, CVE-2026-84411, CVE-2026-67279, CVE-2025-10948, CVE-2024-38355, etc.).
  - **Transparencia en Frontend y Pruebas Unitarias:** Visibilidad clara de ambas fuentes en el encabezado de `FleetCveMatrix.vue` mediante enlaces accesibles con `target="_blank"` y `rel="noopener noreferrer"`. Cobertura y aserciones de sincronización certificadas al 100% en backend (`test_hito23_cve_and_syslog.unit.py`), frontend (`fleetCveMatrix.unit.ts`) y Karate Labs BDD (Escenarios 55-56 en API y Escenario 18 en UI).

- **Soporte de Parámetros STP y Validación de Puertos en Consola WebFig L1 Bridge (`webfig_interfaces.py`, `webfig_l1_net.py`, `BridgeView.vue`):**
  - **Ampliación de Esquemas Pydantic v2 (`BridgeCreateRequest`, `BridgeUpdateRequest`, `BridgePortCreateRequest`):** Incorporado el atributo `protocol_mode: str | None = Field(default=None, max_length=16)` para configuración de Spanning Tree Protocol (RSTP, STP, MSTP, none) y `ingress_filtering: bool = False` para puertos bridge, resolviendo la incompatibilidad con esquemas estrictos (`extra='forbid'`) que generaban un error de validación HTTP 422 (*"Extra inputs are not permitted: protocol_mode"*).
  - **Mapeo Nativo a RouterOS v7 REST API:** Adaptación del payload en `create_bridge` y `update_bridge` para transformar `protocol_mode` a `protocol-mode` y convertir flags booleanos (`vlan_filtering`, `disabled`, `ingress_filtering`) al formato nativo `"yes"`/`"no"` requerido por RouterOS v7.
  - **Cierre Instantáneo de Modal y Creación Fluida:** Solventado el bloqueo en el frontend (`BridgeView.vue`) donde el error 422 impedía que la promesa cerrara el modal `Crear Nuevo Bridge MikroTik`. El modal ahora se oculta de inmediato al pulsar *"Crear con Safe Mode"*, activando la cuenta regresiva del Dead Man's Switch (60s) e incorporando el nuevo Bridge en la tabla de Capa 2 en tiempo real.
  - **Certificación QA y Sincronización Arquitectónica:** Ampliada la suite `webfigViews.unit.ts` (19/19 pruebas al 100%) verificando el envío de `protocol_mode`, `ingress_filtering` y el cierre interactivo de modales. Sincronizadas las especificaciones técnicas en `docs/specs/12` y `docs/specs/22`, así como los manuales operativos y de API en `docs/04` y `docs/06`.

- **Motor de Ejecución en Flota para Aprobaciones Masivas Maker-Checker (`approvals.py`, `bulk_and_updates.py`, `ApprovalsInboxView.vue`):**
  - **Despacho Automático en Routers MikroTik:** Implementado el despachador `execute_bulk_job_on_fleet` que conecta dinámicamente con cada router de la flota objetivo vía `MikrotikRestClient` empleando las credenciales de la bóveda AES-256-GCM.
  - **Resolución y Renderizado de Plantillas Golden Config:** Sustitución automática de variables y ejecución secuencial de pasos REST con tolerancia nativa a menús singulares de RouterOS v7 (fallback automático a `POST <endpoint>/set` cuando RouterOS rechaza `PATCH` en recursos sin identificador, ej. `/system/ntp/client`).
  - **Ejecución Diferida al Aprobar (`approve_request`):** Al confirmar la aprobación de una solicitud de tipo `BULK_MULTI_ROUTER_EXECUTION`, el backend ejecuta inmediatamente la plantilla en todos los equipos objetivo, actualizando el estado de cada `BulkJobItem` a `SUCCESS`/`FAILED`, completando el `BulkJob` y devolviendo el resumen de ejecución en `ApprovalRequest.execution_result`.
  - **Transparencia Visual de Resultados en Frontend (`ApprovalsInboxView.vue`):** Incorporado el panel visual `execution-result-panel` que muestra en tiempo real el desglose de routers procesados exitosamente, estado final del trabajo masivo y auditoría en la pestaña de solicitudes "Aprobadas y Ejecutadas".
  - **Normalización de Estados de Solicitud en Frontend:** Corregida la discrepancia entre el estado en base de datos (`PENDING`) y el filtro de pestaña del frontend (`AWAITING_APPROVAL`), mapeando bidireccionalmente los estados de forma que las solicitudes pendientes de firma se listen de inmediato al ingresar.
  - **Paridad de Contrato en Aprobación y Rechazo:** Actualizados los métodos `handleApprove` y `handleReject` en `ApprovalsInboxView.vue` para enviar el campo tipado estricto `review_comment` (en lugar de `comment`), cumpliendo con el esquema Pydantic v2 `ApproveRequestPayload` (`extra='forbid'`).

- **Optimización y Depuración Visual de Wallboard NOC y Reloj Global del Sistema (`NocWallboardView.vue`, `RgResponsiveShell.vue`, `DashboardHomeView.vue`, `eventFormatter.ts`):**
  - **Reloj Operativo Global en Barra Superior (`RgResponsiveShell.vue`):** Reubicado el reloj digital táctico (HH:MM sin segundos) a la barra de navegación superior derecha (antes del buscador y perfil de usuario), garantizando su visibilidad persistente en toda la aplicación con reactividad inmediata al formato configurado (24 Horas vs 12h AM/PM).
  - **Limpieza del Centro de Mando (`DashboardHomeView.vue`):** Eliminada la tarjeta local del reloj (`.clock-card`) en el cuerpo del dashboard para evitar redundancia visual con la barra superior.
  - **Depuración del Encabezado del Wallboard NOC (`NocWallboardView.vue`):**
    - Eliminado el óvalo e indicador *"EN VIVO 24/7"* del encabezado del Wallboard para maximizar la superficie útil.
    - Eliminado el reloj local de la pantalla del Wallboard (`.clock-time`).
    - Eliminado el texto redundante de sincronización/inicio *"since / Sinc: "* (`.clock-sync`).
    - Eliminada la exposición de la URL interna del WebSocket (`/ws/v1/tenant/events`) en el panel de eventos críticos.
  - **Mapeo y Formateo Descriptivo de Eventos (`eventFormatter.ts`):** Transformación automática de códigos internos inmutables de auditoría (ej. `LOGIN_FAILED_USER_INACTIVE`, `MASS_OUTAGE_TRIGGERED`, `ROUTER_DOWN`) a descripciones claras y amigables para el operador en español (*"Acceso denegado: Usuario inactivo o deshabilitado"*, *"Alerta de caída masiva activada"*, *"Router fuera de línea"*), preservando la inmutabilidad de la base de datos y mejorando drásticamente la legibilidad en el ticker del Wallboard.

- **Perfeccionamiento Visual y Funcional de Inventario y Consola WebFig (`RouterInventoryView.vue`, `ManageNetworkRolesModal.vue`, `CsvOnboardingWizardModal.vue`, `RouterSidebarMenu.vue` y `RouterContextHeader.vue`):**
  - **Eliminación de Texto Redundante en Título:** Eliminado el sufijo superfluo *" — Flota MikroTik"* del título principal en `RouterInventoryView.vue` y del diccionario i18n (`es.json`: *"Inventario de Equipos"* / `en.json`: *"Equipment Inventory"*), así como en el metadato del router (`router/index.ts`).
  - **Alineación Milimétrica en Modal de Roles de Red (`ManageNetworkRolesModal.vue`):** Corregido el desfase vertical de los campos en el formulario de creación de roles mediante un layout estandarizado con inputs y botón a 38px de altura, etiquetas uniformes (16px), espaciador invisible en la columna de acción y reubicación del texto explicativo (`.help-text`) debajo de la fila horizontal.
  - **Descarga Robusta de Plantilla CSV Oficial (`GET /api/v1/inventory/template-csv`):** Incorporado endpoint dedicado en backend que entrega la plantilla CSV con codificación estándar RFC 4180, BOM UTF-8 y cabecera `Content-Disposition: attachment; filename="rosgrid-inventario-plantilla.csv"`. En el frontend (`CsvOnboardingWizardModal.vue`), se transformó el botón de descarga en un enlace nativo directo `<a>` con atributos `href` y `download`, erradicando por completo el uso de `Blob` URLs temporales en memoria (`URL.createObjectURL`) que causaban que Google Chrome y navegadores Chromium bloquearan la descarga como archivo sospechoso o le asignasen el UUID interno del blob sin extensión `.csv`.
  - **Internacionalización Completa en Inglés para WebFig v7:** Integrado composable reactivo `useI18n` en `RouterSidebarMenu.vue`, `RouterContextHeader.vue`, `RouterWorkspaceTabsBar.vue` y `RouterLiveDashboardView.vue`, permitiendo que toda la navegación de módulos, grupos, pestañas dinámicas, cabecera técnica y paneles de telemetría conmuten al instante entre español e inglés al cambiar el idioma global.

- **Refactorización Táctica del Centro de Mando y Menú Desplegable de Usuario (`RgResponsiveShell.vue` y `DashboardHomeView.vue`):**
  - **Reloj Operativo sin Segundos (HH:MM):** Actualizada la lógica de formateo en `DashboardHomeView.vue` para restringir la hora a `{ hour: '2-digit', minute: '2-digit' }` sin mostrar segundos, sincronizada de forma reactiva con el conmutador de formato (24 Horas vs 12h AM/PM) e idioma.
  - **Internacionalización Completa del Menú Desplegable de Usuario:** Integradas claves i18n (`user_menu.*`) en `RgResponsiveShell.vue` y diccionarios `es.json` y `en.json`, permitiendo que todos los títulos de secciones ("Time Format", "Visual Theme", "Language"), opciones de temas, acciones de seguridad ("Change My Password", "Reset My 2FA", "MCP Access Token") y el botón de salida ("Sign Out") se traduzcan en caliente.
  - **Internacionalización de Enlaces en Riel de Navegación Lateral:** Incorporadas las traducciones oficiales para `nav.l2_topology` (*"Topología L2"* / *"L2 Topology"*) y `nav.cve_matrix` (*"Matriz de CVEs"* / *"CVE Matrix"*), corrigiendo el texto estático en el riel de navegación principal.
  - **Depuración Visual del Centro de Mando:** Eliminación del texto redundantemente anglosajón *"Mission Control"* (quedando exclusivamente *"Centro de Mando"* / *"Command Center"*), erradicación de la etiqueta estática *"Tactical NOC v1.0"*, eliminación del indicador superfluo *"NOC EN VIVO"* y remoción de la hora secundaria pequeña UTC en el reloj táctico para dejar una única lectura horaria nítida.
  - **Menú Desplegable de Usuario Superior Derecho:** Sustitución de la etiqueta de rol técnico por el nombre de usuario (`username`) interactivo con avatar y chevron indicador. Al hacer clic, despliega un menú contextual con:
    - Selector de formato horario en caliente: **24 Horas** vs **12h AM/PM** (sincronizado reactivamente con el reloj del Centro de Mando y persistido en `useThemeAndLayoutStore`).
    - Conmutador de tema visual: **Oscuro Táctico**, **Modo Claro** y **Alto Contraste NOC** movidos al menú.
    - Conmutador de idioma: **Español** e **English** movido a la cabecera del menú.
    - Acción de seguridad personal: **Cambiar Mi Clave** con modal accesible (`ChangePasswordModal.vue`).
    - Acción de seguridad personal: **Resetear Mi 2FA** (`RgStepUp2FAModal.vue`).
    - Acción de integración autónoma: **Token de Acceso MCP** (`RgMcpTokenModal.vue`) para clientes Hermes Agent y Claude.
    - Botón de **Cerrar Sesión** ubicado limpiamente al pie del menú.
  - **Paridad y No Regresión en Administración de Usuarios y RBAC (`/users`):** Se integró el botón `🔑 Clave` en la tabla de operadores preservando intactos los accesos a `↺ Reset 2FA` y `⚡ Token MCP`.
  - **Navegación al Centro de Mando desde el Logo:** El logotipo y marca corporativa *"RoSGrid"* en la barra de navegación superior ahora enlazan reactivamente al Centro de Mando (`/`).
  - **Limpieza de Identidad de Organización:** Remoción del prefijo redundante *"Organización: "* en el subtítulo del dashboard y del prefijo *"Tenant: "* en la barra superior, mostrando únicamente el slug de la empresa.
  - **Endpoint de Cambio de Contraseña en Backend (`POST /api/v1/users/change-password`):** Soporte dual de auto-cambio validando contraseña actual con `argon2` y reseteo administrativo directo, con registro inmutable en auditoría WORM (`USER_SECURITY` / `CHANGE_PASSWORD`).

- **Plantilla Oficial de Acciones Masivas para Enrolamiento Syslog (`SYSLOG_CENTRALIZADO_ROSGRID`):**
  - **Catálogo de Plantillas Predefinidas (Backend & Frontend):** Incorporada la plantilla predefinida `SYSLOG_CENTRALIZADO_ROSGRID` en `fastapi/src/api/v1/bulk_and_updates.py` (`_DEFAULT_STARTER_TEMPLATES`) y en `vue3/src/components/operations/templatePresets.ts` (`PREDEFINED_TEMPLATES`), facilitando el despliegue masivo y seguro de configuración Syslog bajo Safe Mode de 60 segundos.
  - **Parametrización Flexible de Servidor RoSGrid:** Definición del esquema tipado de variables con `rosgrid_server_ip` (Dirección IP del servidor RoSGrid) y `rosgrid_syslog_port` (Puerto UDP centralizado, por defecto `5514`), permitiendo al operador ingresar la IP exacta del colector en el asistente de ejecución masiva.
  - **Pasos REST y Comandos CLI RouterOS v7:** Configuración integral de la acción `/system/logging/action` remota (BSD syslog, daemon, sys-ident) y 6 reglas de tópicos críticos (`interface`, `route/bgp`, `route/ospf`, `system/error`, `dhcp`, `firewall`) tanto en pasos de la API REST (`PUT /rest/system/logging/*`) como en scripts CLI de RouterOS.
  - **Resolución Insensible a Mayúsculas/Minúsculas:** Renderizado de plantillas optimizado en backend (`_render_template_steps`) y frontend (`substituteVariables`), permitiendo sustitución automática tanto de `{{ rosgrid_server_ip }}` como de `{{ ROSGRID_SERVER_IP }}`.
  - **Integración en Modal Editor y Mapeo Fallback:** Selector de presets en `ConfigTemplateEditorModal.vue` ampliado con `📜 Syslog Centralizado RoSGrid [SECURITY]`, y tabla de mapeo de comandos CLI fallback en `BulkOperationsAndUpdatesView.vue` optimizada con `Map` (cero vulnerabilidades de inyección de objetos y complejidad cognitiva Grado A).


- **Clarificación Táctica y Guía Visual en Pad de Firma Digital (`FieldTechMobileView.vue`):**
  - **Firma Manuscrita Táctil (HTML5 Canvas):** Se incorporó una marca de agua translúcida orientativa (`✍️ Dibujar firma manuscrita aquí` y línea base `✕ ────────────────────────`) que se oculta automáticamente al iniciar el trazo.
  - **Instrucción de Interacción:** Se añadió la etiqueta explicativa clara *"El cliente debe dibujar su firma con el dedo, stylus o ratón"* para disipar dudas operativas sobre la naturaleza del recuadro (táctil manuscrita, no carga de fotografía estática).
  - **Preservación Forense Inmutable:** El trazo en color cian táctico (`#00f3ff`) se codifica como PNG Base64 nativo y se sella junto a las coordenadas GPS del técnico de campo en el acta de instalación WORM.

- **Centrado Táctico en Caracas y Renderizado Nítido en Mapa de ONUs (`OsmOnuMap.vue` y `SubscribersMapView.vue`):**
  - **Eliminación del Cuadro Gris sin Abonados:** Cuando no existen ONUs registradas o georreferenciadas (`props.onus.length === 0`), el mapa inicializa y encuadra explícitamente sobre **Caracas, Venezuela** (`[10.4806, -66.9036]`, zoom 12) evitando que el viewport quede en blanco o gris.
  - **Migración a Tiles de OpenStreetMap:** Homogeneizado el proveedor de teselas cartográficas a `https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`, garantizando alta disponibilidad, visibilidad de calles y topografía urbana (Ávila, litoral y valles del Tuy).
  - **Invocación de `invalidateSize()` en Ciclo de Vida:** Añadida re-computación diferida del contenedor Leaflet tras el montaje (`150ms` y `500ms`) y observación con `ResizeObserver` para erradicar el renderizado nulo del layout en navegación por pestañas.
  - **Badge Táctico Informativo:** Indicador visual flotante `📍 Centrado en Caracas, D.C. — Sin ONUs georreferenciadas` cuando no hay abonados en la base de datos.

- **Precarga y Sincronización Continua del Feed de Actividad NOC (`DashboardHomeView.vue` y `useNocEventsStore.ts`):**
  - **Precarga Inmediata de Registros de Auditoría WORM:** Implementado `fetchRecentAuditLogs()` en `useNocEventsStore.ts`, resolviendo el estado vacío en frío (*cold start*) en el recuadro inferior derecho del Centro de Mando (`DashboardHomeView.vue`). Ahora los últimos 5 eventos de auditoría e inventario se visualizan al instante al cargar la página sin esperar eventos push.
  - **Sincronización Bidireccional en Vivo:** Los eventos nuevos recibidos por WebSocket se agregan reactivamente a la cabecera de la lista en tiempo real, mientras que el botón de refresco táctico (`Actualizar Datos`) sincroniza en paralelo el inventario y la bitácora forense.

- **Soporte de Auto-Refresco Continuo 24/7 y Reloj Táctico en Wallboard NOC (`NocWallboardView.vue`):**
  - **Auto-refresco Autónomo sin Intervención Humana:** Implementado bucle de sondeo silencioso en segundo plano cada 15 segundos (`performAutoRefresh`) que actualiza la flota de routers y registros de auditoría sin congelar la interfaz ni parpadear la pantalla.
  - **Reloj Digital Táctico en Vivo:** Visualización en cabecera de la hora local en tiempo real con segundos (`🕒 HH:MM:SS`) y etiqueta reactiva de última sincronización exitosa (`Sinc: HH:MM:SS`), permitiendo al personal de guardia en salas de control verificar visualmente que el monitor o Smart TV está activo.
  - **Suscripción de Eventos Críticos en Tiempo Real por WebSocket:** Integración reactiva con `useNocEventsStore` (`/ws/v1/tenant/events`) para inyectar al instante alertas críticas de caída (`ROUTER_DOWN`) y disparar la alarma acústica / visual de Caída Masiva (*Mass Outage*) sin esperar el ciclo de 15 segundos.
  - **Gestión Limpia del Ciclo de Vida:** Limpieza garantizada de todos los temporizadores de fondo (`autoRefreshTimer`, `clockTimer`, `eventSimulationTimer`) en el hook `onUnmounted` para prevenir fugas de memoria en navegadores de pantalla continua.

- **Gobernanza de Acceso a Feature Flags y Control de Capacidades para Tenant Admin:**
  - **Permisos en API (`fastapi/src/api/v1/tenants.py`):** Los endpoints `GET /api/v1/tenants` y `PATCH /api/v1/tenants/{tenant_id}/features` ahora admiten tanto a `SUPERADMIN_GLOBAL` como a `TENANT_ADMIN`. Los administradores de empresa (`TENANT_ADMIN`) pueden consultar y gestionar de forma autónoma los módulos y capacidades técnicas exclusivas de su propia organización con aislamiento estricto de tenant.
  - **Control en Enrutador Frontend (`vue3/src/router/index.ts`):** Ruta `/admin/tenants` ampliada para `allowedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN']`.
  - **Navegación Táctica (`RgResponsiveShell.vue`):** Enlace a la gestión de empresa visible para `TENANT_ADMIN` y `SUPERADMIN_GLOBAL`, adaptando las acciones disponibles (creación de empresa y suspensión restringidas exclusivamente a superadministradores globales).
  - **Sincronización Reactiva de Capacidades (`useAuthStore.ts` y `App.vue`):** Implementado el método `fetchTenantFeatures()` para actualizar los flags del tenant en KeyDB y LocalStorage al autenticar o refrescar la pantalla, sincronizando los estados de módulos en caliente sin requerir re-inicio de sesión.

- **Activación de Receptor Continuo Syslog UDP 5514 en Worker y Telemetría en Inventario:**
  - **Colector Continuo Syslog UDP 5514 (`syslog_collector.py` & `runner.py`):** Integración de `SyslogCollectorWorker` en el orquestador principal del worker, escuchando datagramas UDP en `0.0.0.0:5514` y manteniendo sincronizado el mapa de direcciones IP (`ip_router_map`) para todos los routers registrados.
  - **Mapeo de Presencia y Eventos en KeyDB:** Cada datagrama UDP recibido actualiza una clave efímera de presencia con TTL de 300 segundos (`rg:{tenant}:router:{router_id}:syslog:active`) e inserta el evento en el RingBuffer en memoria RAM de KeyDB (límite 500 eventos por router, cero almacenamiento en disco).
  - **Exposición de Puertos en Docker Compose:** Mapeo de `5514:5514/udp` en `rosgrid-worker` en `docker-compose.prod.local.yml` y `docker-compose.prod.yml`.
  - **Enriquecimiento de Telemetría en Inventario (`inventory_helpers.py`):** Pipeline optimizado de KeyDB que consulta de forma atómica el estado de monitorización, la bandera de presencia `syslog_active` y la longitud del RingBuffer `syslog_event_count`.
  - **Indicador Táctico y Acceso Rápido en Vue 3 (`RouterInventoryView.vue`):** Columna de estado Syslog (`🟢 Activo (N)` o `⚪ Sin Syslog`) y botón directo `[ 📜 Syslog ]` en cada fila del inventario para acceso inmediato a la consola de logs efímeros.
  - **Optimización de Timeout en Sincronización CVE (`cve_matcher.py`):** Configurado un timeout de 4.0s (connect=2.0s) en consultas remotas a NIST NVD para mitigar errores HTTP 504 Gateway Time-out de NGINX, garantizando fallback instantáneo al catálogo offline local embebido (`cve_catalog_ros.json`).

- **Internacionalización y Reactividad Multilingüe (Español / Inglés) en Vistas Operativas:**
  - **Soporte Global Reactivo con `useI18n`:** Homogeneización de cadenas de texto y etiquetas tácticas en `RouterInventoryView.vue`, `DashboardHomeView.vue` y `NocWallboardView.vue` utilizando el composable nativo `useI18n`.
  - **Conmutación Dinámica en Caliente:** Al alternar el selector de idioma en la barra superior (ES / EN), las columnas de inventario (`Syslog`, estados, acciones), los módulos del Centro de Mando, los relojes forenses y las métricas del Wallboard se traducen instantáneamente sin requerir recargar la página.
  - **Ampliación de Diccionarios (`es.json` y `en.json`):** Incorporadas claves completas para estados Syslog (`syslog_active`, `syslog_inactive`, `action_syslog_active`), tarjetas de herramientas operativas, descripciones de permisos RBAC y banners de alerta crítica.

### Fixed

- **Corrección de Reactividad en Feature Flags y Ocultamiento de Módulos Inactivos (`EnterpriseComplianceView.vue` & API):**
  - **Filtrado Dinámico de Pestañas en Cumplimiento:** Las pestañas de `Config Drift & Baselines`, `SD-WAN Hub & Spoke`, `Telemetría SLA`, `Wi-Fi CAPsMAN` y `Canales de Notificación` ahora evalúan `authStore.isFeatureEnabled(...)`. Si una casilla está apagada en el panel de gobernanza, su pestaña correspondiente desaparece de inmediato de la interfaz.
  - **Resolución Automática de Pestaña Activa:** La vista calcula `availableTabs` en tiempo de ejecución; si el módulo por defecto (`drift`) está desactivado para el tenant, la selección inicial y el cambio dinámico de estado apuntan automáticamente a la primera pestaña habilitada (`CIS Benchmark Hardening` o `Seguridad L2`).
  - **Protección a Nivel de API (`require_feature`):** Se blindaron los endpoints de backend en `compliance.py` (`/compliance/config-drift/*` con `config_drift_monitoring_enabled` y `/compliance/cis-audit/*` con `cis_audit_enabled`), `sdwan.py` (`sdwan_orchestrator_enabled`), `sla.py` (`sla_tracker_enabled`) y `wifi.py` (`capsman_wifi_enabled`), retornando HTTP 403 `FEATURE_MODULE_DISABLED` si se invocan estando desactivados.
  - **Soporte GET en Auditoría CIS (`compliance.py`):** Se habilitó el método `GET` en `/api/v1/compliance/cis-audit/{router_id}` para resolver el fallo `405 Method Not Allowed` al consultar el puntaje de seguridad desde la interfaz.
  - **Filtrado de Respaldos Git Diff en Menú Lateral:** La entrada `RscGitDiff` (`/backups`) en `RgResponsiveShell.vue` ahora se condiciona dinámicamente al flag `nightly_backups_enabled`.

- **Corrección de Conflicto en Auditoría Inmutable WORM y Eliminación de Routers (Alembic 0009):**
  - **Desacoplamiento de Claves Foráneas en `audit_logs`:** Creada y aplicada la migración `0009_audit_logs_worm_decouple_fk.py` que elimina las restricciones `audit_logs_router_id_fkey` y `audit_logs_actor_user_id_fkey`.
  - **Resolución de Conflicto WORM:** Se resolvió la excepción 42501 provocada porque la cláusula `ON DELETE SET NULL` de PostgreSQL ejecutaba una sentencia `UPDATE` sobre `audit_logs`, la cual era abortada por el trigger `trg_immutable_audit_logs` a nivel de sentencia (`FOR EACH STATEMENT`).
  - **Preservación Forense Criptográfica:** Garantiza que los registros históricos de auditoría conserven intactos los UUIDs de routers o usuarios eliminados sin alterar el hash SHA-256 (`record_sha256_hash`), permitiendo a su vez la eliminación limpia de equipos en el inventario.

- **Corrección de Error HTTP 500 en Importación Masiva CSV con Roles Personalizados (Alembic 0008):**
  - **Migración Faltante `tenant_custom_roles`:** Creada y aplicada la migración de Alembic `0008_tenant_custom_roles.py` que genera la tabla `tenant_custom_roles` con Row Level Security (RLS) forzado y política de aislamiento multi-tenant.
  - **Evolución del Tipo de Columna `routers.network_role`:** Modificado el tipo de columna en PostgreSQL de `router_network_role_enum` a `VARCHAR(64)` mediante `ALTER TABLE routers ALTER COLUMN network_role TYPE VARCHAR(64) USING network_role::text;`, permitiendo el registro y persistencia de roles tácticos definidos dinámicamente por los operadores (ej. `L1`).
- **Corrección de Geometría y Disposición CSS en Pantalla de Login (`LoginView.vue`):**
  - Se corrigió la superposición del pie de página institucional sobre la tarjeta de credenciales añadiendo `flex-direction: column` a `.login-wrapper`, `margin: auto 0` a `.login-card` y `width: 100%` a `.login-footer`, garantizando un flujo vertical limpio y sticky al fondo.

- **Gobernanza de Agentes IA y Optimización de Tokens (`.agents/` y `AGENTS.md`):**
  - Implementación del marco de gobernanza técnica y directivas operativas para asistentes IA (Google Antigravity, Claude Code, Hermes Agent, Cursor) bajo el estándar corporativo Nivel 11X.
  - Redacción de reglas en `.agents/rules/` (`mandatory_qa_pyramid_and_doc_sync.md`, `secure_development_and_testing_guidelines.md`, `frontend_parity_and_closure.md`, `continuous_agent_evolution.md`) y `AGENTS.md` en inglés técnico compacto de alta densidad (reduciendo ~35% el consumo de tokens en el context window del LLM) con directiva forzada de interacción y respuestas al usuario en español.
  - Incorporación de la regla obligatoria `continuous_agent_evolution.md` que instruye a los agentes de IA a mejorar, optimizar y automatizar de forma continua y autónoma el contenido de `.agents/` ante cualquier hallazgo o resolución de defectos sin requerir solicitudes explícitas del usuario.
  - Despliegue y optimización lingüística de las 6 habilidades de dominio en `.agents/skills/` (`rosgrid-noc-operator`, `qa-11x-docker-certifier`, `mikrotik-webfig-safemode`, `vue3-wcag-tactical-ui`, `docker-trivy-keydb-hardening` y `graphify-docs-api-writer`) y sus documentos de referencia técnica (`mcp_tools.md`, `routeros_flags.md`) en inglés técnico de alta densidad.
  - Inclusión de sección explicativa de arquitectura en `.agents/README.md` detallando la justificación de la optimización de tokens (ahorro $\approx 35\%$ en context window, menor latencia y mayor adherencia semántica) manteniendo la directiva forzada `OUTPUT LANGUAGE CONSTRAINT` para respuestas y documentación en español.
  - Creación de compuertas automatizadas en `.agents/scripts/`: `verify_alembic_orm_parity.py` (verificación de 25/25 modelos ORM vs migraciones Alembic) y `certify_task_completion.sh` (compuerta pre-commit integral sin ejecución en host).

- **Ampliación de Pruebas Automatizadas y Detección de Regresiones (Karate Labs, Contratos y Unitarias):**
  - **Pruebas BDD API (Karate Labs):** Incorporados los escenarios 62 (Dry-Run CSV), 63 (Commit Transaccional CSV) y 64 (Consulta de Catálogo de Roles Personalizados) en `fastapi/test/api_test.feature` y `docs/examples/fastapi/test/api_test.feature`.
  - **Pruebas BDD UI (Karate Labs):** Incorporados los escenarios 21 (Apertura, inspección y cierre del modal asistente de importación CSV) y 22 (Verificación estructural del pie de página en login sin solapamiento) en `vue3/test/ui_business_flow.feature` y `docs/examples/vue3/test/ui_business_flow.feature`.
  - **Contrato Front-Back (`validar_comunicacion_front_back.py`):** Ampliado con carga multipart/form-data idéntica a la UI Vue 3 para dry-run y commit transaccional de CSV con rol `L1`, consulta del catálogo `GET /api/v1/inventory/network-roles`, resolución dinámica de tokens para entornos wizard y prueba de eliminación `DELETE /api/v1/inventory/routers/{router_id}` (HTTP 204) con `Idempotency-Key` y cliente desacoplado, alcanzando 26/26 pruebas aprobadas (100%) y garantizando la higiene absoluta del inventario.
  - **Pruebas Unitarias de Backend (`test_inventory_csv_and_vault.unit.py`):** Añadidas validaciones de roles dinámicos en CSV y verificación del modelo `TenantCustomRole` en metadatos de SQLAlchemy.
  - **Pruebas Unitarias de Frontend (`loginView.unit.ts`):** Añadida prueba de orden jerárquico DOM entre `.login-card` y `.login-footer`.

- **Certificación Integral Pre-Lanzamiento y Cobertura QA 11X (Hito 23.6):**
  - **Elevación de Cobertura Backend a 95.11% (`pytest-cov`):** 463 pruebas unitarias aprobadas al 100% en Docker (`sinfallas/base-python-uv:3.15`), incorporando suites dedicadas para `test_hito23_cve_and_syslog.unit.py`, `test_hito23_topology_and_fleet.unit.py` y `test_hito23_mcp_tools.unit.py` cubriendo la totalidad de endpoints de Syslog, matrices CVE, Topología L2, DAG PoE inverso, herramientas semánticas MCP y exportador Prometheus.
  - **Endurecimiento SAST (Bandit):** Mitigación de alertas B110 (`try_except_pass`) en `topology_l2.py` y `csrf.py` mediante logging estructurado y marcado `# nosec B106` para el argumento de tipo de token en `users.py`, logrando 0 incidencias en 19.941 líneas analizadas.
  - **Auditoría de Dependencias (`pip-audit`):** Sincronización de `uv.lock` con actualización a versiones seguras de `certifi` (`2026.10.19`) y `uv` (`0.13.4`), certificando 0 vulnerabilidades conocidas en paquetes de producción y desarrollo.
  - **Pipeline de Validación Local de Producción (`./scripts/probar-prod-local.sh`):** Ejecución automatizada y validación al 100% de las 6 fases del pipeline pre-release: compilación multi-etapa de imágenes de backend y frontend, healthchecks en aislamiento, pruebas sintéticas HTTP, hardening de docs 404, prueba fail-closed 401, token MCP, JSON-RPC 2.0 y 24 contratos Front-Back (`validar_comunicacion_front_back.py`).
  - **Auditoría de Shell Scripts:** Cero errores y cero advertencias en `ShellCheck` sobre todos los scripts `.sh` del monorepo.

- **Implementación Frontend (Vue 3 + Pinia) — Topología L2, Matriz CVE, Syslog Live y PoE-Aware (Hito 23.5):**
  - **Vista interactiva de Topología Física Layer 2 (`L2TopologyView.vue`):** Canvas 2D interactivo a 60 FPS con Pan/Zoom suave, badges dinámicos de consumo PoE en tiempo real (`⚡ W`), indicadores de estado Online/Offline, selector de modo Sólo-PoE, drawer lateral táctico y fallback accesible para screen readers.
  - **Matriz de Vulnerabilidades CVE de Flota (`FleetCveMatrix.vue`):** Panel táctico con 4 tarjetas KPI evaluadas (Evaluados, Vulnerables, Críticos, Versión Recomendada), filtros reactivos por severidad (CRITICAL, HIGH, MEDIUM, LOW), sincronización remota contra NIST NVD y enlace directo al orquestador de actualización masiva.
  - **Acceso Directo CVE en Inventario (`RouterInventoryView.vue`):** Botón táctico `[ 🛡️ Matriz de CVEs ]` para auditoría inmediata de vulnerabilidades de toda la flota.
  - **Terminal Syslog en Vivo en WebFig (`RouterSyslogTerminalView.vue`):** Consola embebida en la vista de router que consume en tiempo real el RingBuffer efímero de KeyDB (500 eventos) sin persistencia en base de datos, con alertas visuales de severidad crítica, auto-scroll inteligente y modal con plantilla CLI de enrolamiento MikroTik.
  - **Orquestador de Actualización Masiva PoE-Aware con Safety Stop (`BulkOperationsAndUpdatesView.vue`):** Conmutador táctico PoE-Aware para actualización de clientes PD antes que switches PSE y selector de umbral Safety Stop (1%, 2%, 5%).
  - **Navegación Táctica:** Enlace a Topología L2 y Matriz CVE en el shell responsive principal (`RgResponsiveShell.vue`) y acceso a Syslog Live en el menú lateral de WebFig (`RouterSidebarMenu.vue`).
  - **Certificación QA 11X:** 297 tests unitarios Vitest (100% pasando en 43 suites), 20 escenarios BDD Karate Labs UI, cero errores en `vue-tsc --noEmit` y cero violaciones ESLint / SonarJS.

- **Planificación y Diseño Arquitectónico: Automatización de Flota, Topología L2, Syslog Efímero, Exportador Prometheus y Seguridad CVE (Hito 23):**
  - **Especificación Técnica y Arquitectura de Datos (`docs/specs/35` y `docs/12`):** Diseño formal de estructuras en memoria para preservar estrictamente el modelo *Zero-Metrics Storage* (cero almacenamiento de series de tiempo en PostgreSQL 17).
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
  - **Sincronización Documental:** Actualización integral de `docs/specs/30_BACKEND_MCP_PROTECTED_ENDPOINT.md` y `docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md`.

- **Generador de Tokens MCP, Supervisión de Sesiones IA con Kill-Switch y Panel de Notificaciones (Hito 22.14):**
  - **Generador Visual de Tokens MCP (`RgMcpTokenModal.vue`):** Modal interactivo integrado en la pantalla de Usuarios y Permisos (`UsersAndPermissionsView.vue`) para la emisión de Bearer Tokens de larga duración (30 a 730 días) para cuentas de servicio (`SERVICE_ACCOUNT`, `TENANT_ADMIN`, `SUPERADMIN_GLOBAL`). Muestra metadatos de sesión, advertencias de gobernanza y snippets de configuración de 1-clic para Claude Desktop (`claude_desktop_config.json`) y Hermes Agent (`config.yaml`).
  - **Supervisión y Kill-Switch de Agentes IA (`ActiveSessionsKillSwitchView.vue`):** Pestañas de filtrado táctico (*Todas*, *Operadores Humanos*, *Agentes IA MCP*), badges distintivos de cuenta de servicio, linaje del operador que autorizó el token (`Por: @usuario`), lista blanca CIDR y botón de revocación en caliente en tiempo real en KeyDB/Redis.
  - **Endpoint Backend `POST /api/v1/users/{user_id}/mcp-token`:** Emisión criptográfica firmada con JWT HS256, validación de pertenencia al tenant, registro de sesión en KeyDB (`rg:{tenant}:sess:{sid}`) sincronizado con `active_sessions` y auditoría inmutable WORM (`MCP_TOKEN_ISSUED`).
  - **Sincronización del Script CLI (`generar_token_mcp.py`):** Vinculación de tokens generados desde terminal al registro de sesiones activas con metadatos de autoría (`CLI (Terminal)`), permitiendo su revocación inmediata desde la interfaz web.
  - **Panel de Canales de Alerta y Notificación Multicanal (`NotificationChannelsPanel.vue`):** Interfaz completa para el módulo de API de notificaciones (`fastapi/src/api/v1/notification_channels.py`), integrado como 7ª pestaña en la pantalla de Cumplimiento Normativo (`EnterpriseComplianceView.vue`). Permite creación, edición, alternado activo/inactivo, prueba de despacho interactiva (`POST /{id}/test`) y eliminación de canales Telegram Bot, Servidores SMTP y Webhooks genéricos cifrados con AES-256-GCM.
  - **Certificación QA 11X:** 406 pruebas de backend aprobadas con 95% de cobertura global, 278 pruebas unitarias frontend en 40 archivos aprobadas al 100%, 0 errores en ESLint y Vue-TSC.

- **Consolidación de Calidad, Resolución Integral de Diagnósticos y Robustecimiento DevOps (Hito 22.13):**
  - **Sintaxis y Linter de Documentación (`markdownlint-cli`):** Corrección y certificación de 0 errores y 0 advertencias en la totalidad de especificaciones (`docs/specs/30`, `docs/specs/31`, `docs/specs/32`, `docs/specs/33`, `docs/specs/34`), manuales operativos (`docs/01`, `docs/03`, `docs/04`, `docs/05`, `docs/06`, `docs/07`, `docs/10`, `docs/11`) y guías de contribución (`CONTRIBUTING.md`), estandarizando viñetas (`MD004`), espaciado en encabezados (`MD022`), listas (`MD032`), bloques de código (`MD031`), tablas compactas (`MD060`) y eliminación de puntuación en títulos (`MD026`).
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
  - **Orquestadores y Manifiestos:** Sincronización de `docker-compose.yml`, `fastapi/docker-compose.qa.yml`, `vue3/docker-compose.qa.yml`, `docs/examples/` y Dockerfiles de producción.
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
  - Sincronización idéntica de la suite en `docs/examples/vue3/test/ui_business_flow.feature`.
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
  - Sincronización idéntica de la suite en `docs/examples/fastapi/test/api_test.feature`.
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
- Publicación multi-arquitectura con `./scripts/build.sh` hacia Docker Hub (`sinfallas/rosgrid-backend:1.0.0` y `sinfallas/rosgrid-frontend:1.0.0`).

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
