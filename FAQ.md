# ❓ Preguntas Frecuentes (FAQ) — RoSGrid

Respuestas directas a las dudas técnicas, operativas y de diseño más comunes sobre **RoSGrid**.

---

## 1. Compatibilidad con Equipos MikroTik

### ¿Por qué RoSGrid exige RouterOS v7.1+ y no soporta RouterOS v6?
RoSGrid se comunica exclusivamente a través de la **REST API nativa sobre HTTPS (`/rest/*`)**, la cual fue introducida por MikroTik a partir de **RouterOS v7.1**.
- El protocolo API binario propietario de RouterOS v6 (puertos `8728`/`8729`) carece de semántica HTTP estándar, complica la inspección de esquemas dinámicos y presenta limitaciones en el manejo de flujos modernos.
- Además, los esquemas de enrutamiento (`BGP`, `OSPF`, `Routing Filters`) y `WireGuard` en RoSGrid están diseñados específicamente sobre la arquitectura de kernel de RouterOS v7.

### ¿Necesito certificados SSL comprados a una CA pública en cada MikroTik?
**No.** En redes privadas de gestión de un ISP o corporación, los routers suelen identificarse por direcciones IP privadas donde Let's Encrypt no es viable. RoSGrid implementa **SSL Pinning con *Trust On First Use* (TOFU)**:
1. Generas un certificado autofirmado gratuito en el propio MikroTik y activas `www-ssl`.
2. En el primer registro, RoSGrid captura y fija la huella criptográfica `SHA-256` del certificado (`TRUSTED_PINNED`).
3. Todo el tráfico viaja cifrado con TLS (reutilizando conexiones `Keep-Alive` para baja latencia) y cualquier cambio posterior no autorizado de certificado es bloqueado como alerta de seguridad (`FINGERPRINT_MISMATCH`).

### ¿Qué hago si renuevo legítimamente el certificado SSL de un MikroTik y aparece bloqueado por `FINGERPRINT_MISMATCH`?
Un usuario con rol `SUPERADMIN_GLOBAL` o `TENANT_ADMIN` debe abrir el detalle del router en RoSGrid, seleccionar **"Autorizar Nuevo Certificado (Re-Pin SSL TOFU)"** e ingresar su código **2FA TOTP en vivo (*Step-Up Auth*)**. El cambio quedará asentado en la bitácora forense WORM.

### ¿Por qué mi usuario API creado en MikroTik devuelve HTTP 401 Unauthorized y en WinBox dice que nunca se ha conectado?
A partir de **MikroTik RouterOS v7.13+**, MikroTik dividió los permisos de la API binaria (`api`) y la API REST (`rest-api`).
- Si creaste un grupo personalizado en `/user group` con las políticas estándar (`read,write,api,test`) pero **omitiste `rest-api`**, el servidor HTTP de MikroTik rechazará cualquier petición REST con `401 Unauthorized` a nivel de autenticación básica antes de registrar una sesión interactiva en WinBox.
- **Solución en RouterOS CLI:**
  ```routeros
  /user group add name=rosgrid-api-group policy=read,write,api,rest-api,test
  /user set [find name=rosgrid_agent] group=rosgrid-api-group
  ```


---

## 2. Arquitectura, Rendimiento y Decisiones de Diseño

### ¿Por qué RoSGrid usa KeyDB Multi-Hilo por defecto en lugar de Redis tradicional, y cuándo debo usar DragonflyDB?
En RoSGrid, el motor en memoria gestiona el bus `Pub/Sub` de telemetría WebSocket (1 tick cada 2 segundos), las sesiones activas y los pipelines del monitor *Zero-Metrics*:
- **KeyDB (`eqalpha/keydb:alpine` con `--server-threads 2`)** es nuestro motor predeterminado porque ofrece procesamiento **multi-hilo real** bajo licencia `BSD-3-Clause` consumiendo apenas **~35 MB de RAM en reposo**.
- **Recomendación:** Mantén **KeyDB** a menos que operes una flota masiva (**más de 300 a 500 routers MikroTik con decenas de operadores simultáneos**) en un servidor dedicado con **16 GB+ de RAM**, caso en el cual puedes activar el perfil de **DragonflyDB** documentado en [INSTALL.md](./INSTALL.md).

### ¿Por qué no encuentro `/docs` (Swagger) ni `/redoc` activos en la imagen de producción?
Por seguridad (*Hardening*). Cuando `ROSGRID_ENV=production`, FastAPI desactiva completamente Swagger, ReDoc y `/openapi.json` para evitar exponer la estructura de la API. Toda la especificación de endpoints REST (`/api/v1/*`) y canales WebSocket (`/ws/v1/*`) se encuentra documentada en `docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md`.

### ¿Por qué RoSGrid NO tiene un botón de Terminal CLI / SSH interactiva como WebFig o WinBox?
Es una **decisión de seguridad deliberada (ADR)**. Incluir una consola interactiva libre (SSH o Telnet) destruiría las garantías empresariales de RoSGrid:
1. Rompería el aislamiento **Split-Credential** (donde el técnico opera sin acceso directo a la sesión libre del router).
2. Permitiría a roles intermedios (`SUPPORT_L2`, `SUPPORT_L1`, `FIELD_TECH`) ejecutar comandos que se salten la bandeja de aprobación **Maker-Checker**.
3. Permitiría deshabilitar `/ip/service/www-ssl` o borrar el scheduler del **Safe Mode**, dejando el equipo incomunicado.
4. Impediría registrar estados estructurados `before_state` y `after_state` en la bitácora inmutable **WORM (`audit_logs`)**.
5. **Alternativa en RoSGrid:** El 100% de los menús de RouterOS v7 que no están en la Capa 1 están disponibles mediante tablas y formularios autogenerados en el **Motor Dinámico Universal de Capa 2 (`/webfig/layer2/*`)**, conservando RBAC, Safe Mode y auditoría completa.

### ¿Por qué las gráficas de CPU, RAM y tráfico se reinician al salir del router (*Zero-Metrics Storage*)?
Porque **RoSGrid no es un recolector histórico pesado como Zabbix o Prometheus**. Guardar métricas cada 2 segundos de cientos de routers e interfaces llenaría gigabytes de disco en PostgreSQL diariamente:
- Cuando un operador entra a la consola de un router en RoSGrid, el Multiplexor WebSocket activa el sondeo en vivo de ese equipo y acumula los datos en un **`TelemetryRingBuffer` en la memoria RAM del navegador** (hasta **5,400 puntos = 3 horas continuas** a 1 tick cada 2 segundos, dibujados sobre `<canvas>` 2D).
- Mientras saltes entre las pestañas internas del mismo router (`Interfaces`, `Firewall`, `BGP`, `Ping`), la gráfica sigue acumulando datos gracias al contenedor padre y `<KeepAlive :max="5">`.
- En el instante en que el último operador cierra o sale de ese router (`SCARD == 0` en KeyDB), el Backend detiene el sondeo inmediatamente (cero carga innecesaria al MikroTik) y el navegador libera la memoria RAM, exactamente igual que ocurre al cerrar WinBox.

---

## 3. Operación Segura y Recuperación ante Fallos

### ¿Cómo evita el *Safe Mode* que me quede fuera de un router remoto al editar el Firewall o las Rutas?
Antes de enviar una modificación riesgosa a `/rest/*`, RoSGrid inyecta en el MikroTik una tarea programada temporal (`/rest/system/scheduler`) llamada `rosgrid_safemode_<id>` configurada para ejecutarse en **60 segundos** con el comando exacto que revierte el cambio al estado anterior (`before_state`):
- Si después de aplicar el cambio RoSGrid sigue teniendo comunicación con el router, elimina el scheduler temporal de inmediato y confirma la operación.
- Si el cambio dejó sin conexión al router, RoSGrid no podrá borrar el scheduler; al cumplirse los 60 segundos, el propio MikroTik ejecutará la reversión automáticamente y devolverá la conectividad.

### ¿Qué pasa si se cae la red justo cuando RoSGrid está rotando automáticamente la contraseña API de un router?
La bóveda `router_credentials_vault` opera de forma transaccional en dos fases: antes de enviar la nueva contraseña aleatoria de 32 caracteres al MikroTik, conserva la contraseña anterior cifrada en `previous_password_encrypted`. Si la confirmación falla por un corte eléctrico o de red, el cliente HTTP de RoSGrid prueba automáticamente ambas llaves en la reconexión y resincroniza el estado sin dejar huérfano al equipo.

### ¿Por qué cuando edito una regla con rol `SUPPORT_L2` recibo un aviso `202 Accepted` y el cambio no se aplica de inmediato?
Porque tu rol está sujeto a la política **Maker-Checker** en las 7 categorías críticas (Firewall, BGP/OSPF, direccionamiento de interfaces troncales, etc.). La plataforma captura tu solicitud con su vista previa y la coloca en la **Bandeja de Aprobaciones** para que un `SUPERVISOR`, `SUPPORT_L3` o `TENANT_ADMIN` la revise y ejecute con un clic.

### ¿Cómo funciona el Auto-Registro Web de Operadores y la Aprobación Maker-Checker?
Para evitar la necesidad obligatoria de crear usuarios mediante terminal CLI en producción:
1. En la pantalla de login, los técnicos pueden usar el enlace *"Solicitar acceso de operador"*.
2. El registro crea la cuenta en estado `PENDING_APPROVAL` con acceso bloqueado (`HTTP 403 Forbidden`).
3. El Superadmin recibe la solicitud en la pestaña *Solicitudes Pendientes* de la vista de usuarios, donde puede evaluar la solicitud, asignarle su rol definitivo (`SUPPORT_L1`, `SUPPORT_L2`, etc.) y aprobarla o rechazarla con un clic.
4. El Superadmin puede deshabilitar el registro público en cualquier momento mediante el switch táctil en la barra superior (gobernado por la llave `rosgrid:registration_enabled` en KeyDB).

---

## 4. Integración con Inteligencia Artificial y Agentes Autónomos (MCP)

### ¿Cómo conecto RoSGrid con Hermes Agent, Claude Desktop o Claude Code mediante el protocolo MCP?
RoSGrid implementa de forma nativa la especificación **Model Context Protocol (JSON-RPC 2.0 Streamable HTTP)** sobre el endpoint `POST /api/v1/mcp`:
1. Habilita la funcionalidad en tu `.env` con `ROSGRID_MCP_ENABLED=true`.
2. Crea un usuario con rol `SERVICE_ACCOUNT`, asígnale los routers permitidos en la matriz de permisos y declara la subred autorizada en `allowed_cidr`.
3. Configura el bloque de conexión HTTP en `mcp_config.json` (Hermes Agent) o en tu cliente MCP apuntando a `https://tu-dominio.com/api/v1/mcp` con la cabecera `Authorization: Bearer <token>`.
4. El agente dispondrá inmediatamente de **16 herramientas semánticas** especializadas de diagnóstico 360°, salud, óptica SFP DDM, enrutamiento BGP, aislamiento técnico, remediación de Config Drift, auditoría CIS y detección de cortes masivos. Consulta la guía detallada en [docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md](./docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md).

### ¿Puede un agente de IA causar una interrupción masiva de red a través del endpoint MCP?
**No.** RoSGrid aplica el principio de contención estricta:
- Las herramientas de lectura e inspección técnica solo consultan el estado sin alterar la configuración del router.
- Las acciones de aprovisionamiento como el aislamiento de un equipo (`rosgrid_isolate_subscriber`) o el cambio de ancho de banda son estrictamente **idempotentes**, evitando mutaciones dobles ante reintentos.
- La herramienta de modificación de red no estructurada (`rosgrid_propose_network_change`) **no aplica ningún cambio directamente**: intercepta la propuesta hacia la bandeja **Maker-Checker** con código HTTP `202 Accepted` (`AWAITING_APPROVAL`). Un supervisor humano debe validar el cambio antes de que se ejecute bajo protección de **Safe Mode (60s)**.
- Cada interacción del LLM queda registrada de forma inalterable en la bitácora WORM con el evento `MCP_AI_TOOL_CALL`.

---

## 5. Gobernanza Modular, Feature Flags, Operaciones ISP y Redes Corporativas

### ¿Por qué RoSGrid NO incluye módulos de facturación ni almacena datos personales de clientes?
RoSGrid es una **plataforma pura de ingeniería de red e infraestructura**. No es un CRM comercial, ERP ni sistema de facturación tributaria (BSS):
- **Cumplimiento y Privacidad:** En RoSGrid no existen campos para nombres de personas, identificaciones fiscales, direcciones residenciales ni datos bancarios.
- **Identificación Técnica Exclusiva:** Los equipos y circuitos de abonados se referencian únicamente por su `device_serial` (serial de la ONU/CPE) y su `endpoint_identifier` técnico (ej. usuario PPPoE o código de circuito).
- **Desacoplamiento Total:** La relación entre la persona y su número de contrato reside en el sistema de cobro externo del cliente, no en RoSGrid.

### ¿Cómo se integra un sistema de facturación o CRM externo con RoSGrid?
A través de la **API de Aprovisionamiento Técnico Idempotente** documentada en [docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md](./docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md):
- El sistema externo invoca `POST /api/v1/network-services/{id}/isolate` para suspender el tráfico en MikroTik, o `/restore` para reactivarlo, utilizando la cabecera `Idempotency-Key` (UUIDv7) para garantizar cero efectos secundarios ante cortes de red.
- RoSGrid responde en milisegundos y despacha **Webhooks Salientes** firmados criptográficamente con `HMAC-SHA256` para notificar al CRM eventos como `DEVICE_ACTIVATED_GPS`, `DEVICE_ISOLATED` o `MASS_OUTAGE_TRIGGERED`.

### ¿Cómo se adapta RoSGrid para un Banco, Hospital, Campus o Cadena de Retail (Entorno Corporativo)?
El Superadmin simplemente desactiva el switch **"Módulo ISP & Operaciones de Campo"** en el panel de Feature Flags (`TenantsManagementView.vue`):
- La interfaz oculta automáticamente el mapa de ONUs y el formulario de técnicos de calle.
- Se activan las herramientas empresariales: **Detección de Desviación de Configuración (*Config Drift*)** contra la Plantilla Maestra homologada, **Orquestador SD-WAN WireGuard Hub & Spoke**, **Auditoría CIS Benchmark**, **Detección de Rogue DHCP en switches**, **Monitor de Cumplimiento de SLA de enlaces WAN** y **Gestión Centralizada WiFi (CAPsMAN)**.

---

## 6. Dónde Aprender Más (`docs/`)

Para consultar todos los manuales oficiales de producción de RoSGrid:
- [docs/01_GUIA_DESPLIEGUE_Y_ENTORNO.md](./docs/01_GUIA_DESPLIEGUE_Y_ENTORNO.md) — Despliegue, `.env` y perfiles KeyDB / DragonflyDB.
- [docs/02_PREPARACION_MIKROTIK_ROUTEROS_V7.md](./docs/02_PREPARACION_MIKROTIK_ROUTEROS_V7.md) — Configuración RouterOS v7, TOFU y Safe Mode.
- [docs/03_MANUAL_ADMIN_MULTITENANT_Y_SEGURIDAD.md](./docs/03_MANUAL_ADMIN_MULTITENANT_Y_SEGURIDAD.md) — RLS, 11 roles RBAC, Bóveda 2FA, Kill-Switch y Auto-Registro.
- [docs/04_MANUAL_OPERATIVO_WEBFIG_NOC_Y_BACKUPS.md](./docs/04_MANUAL_OPERATIVO_WEBFIG_NOC_Y_BACKUPS.md) — WebFig, RingBuffer, Maker-Checker y Wallboard.
- [docs/05_AUDITORIA_FORENSE_Y_ARQUITECTURA.md](./docs/05_AUDITORIA_FORENSE_Y_ARQUITECTURA.md) — Bitácora WORM, ADR y grafos de arquitectura.
- [docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md](./docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md) — Catálogo de endpoints REST, WebSockets, Aprovisionamiento QoS y Webhooks.
- [docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md](./docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md) — Integración de IA con Model Context Protocol (16 Tools).
- [docs/08_PIPELINE_VALIDACION_LOCAL_PRODUCCION.md](./docs/08_PIPELINE_VALIDACION_LOCAL_PRODUCCION.md) — Pipeline local y suite de 24 pruebas UI-API.
- [docs/09_PLAN_MAESTRO_PRUEBAS_MANUALES_UAT.md](./docs/09_PLAN_MAESTRO_PRUEBAS_MANUALES_UAT.md) — Plan maestro UAT 11X (75 casos de prueba E2E).

