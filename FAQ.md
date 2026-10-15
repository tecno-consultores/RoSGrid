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
