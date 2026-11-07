# Especificación Técnica 92: Despacho Real de Prueba y Alertas en Canales de Notificación (SMTP `to_emails`/`from_email`/TLS/SSL, Telegram y Webhook) y Edición Interactiva de Canales (`✏️ Editar`) (Hito 30.15)

**Estado:** `PROPOSED (READY FOR IMPLEMENTATION)`  
**Hito Asociado:** `Hito 30.15`  
**Prioridad:** `CRÍTICA (Bloqueante Operativo en Canales de Alerta y Notificación Multicanal)`  
**Módulos Afectados:**
- Backend:
  - [`fastapi/src/api/v1/notification_channels.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/notification_channels.py)
  - [`fastapi/src/workers/alert_dispatcher_worker.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/workers/alert_dispatcher_worker.py)
  - [`fastapi/src/schemas/notifications.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/schemas/notifications.py)
- Frontend:
  - [`vue3/src/components/operations/NotificationChannelsPanel.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/operations/NotificationChannelsPanel.vue)
  - [`vue3/src/types/index.ts`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/types/index.ts)
- Pruebas 11X:
  - [`fastapi/tests/api/test_operations_endpoints_full.unit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/tests/api/test_operations_endpoints_full.unit.py)
  - [`fastapi/tests/workers/test_workers_full.unit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/tests/workers/test_workers_full.unit.py)
  - [`vue3/src/components/operations/NotificationChannelsPanel.unit.ts`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/operations/NotificationChannelsPanel.unit.ts)
  - [`fastapi/test/api_test.feature`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/test/api_test.feature) y [`vue3/test/ui_business_flow.feature`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/test/ui_business_flow.feature) (+ réplicas en `docs/examples/`)

---

## 1. Contexto y Diagnóstico de Causa Raíz (Root Cause Analysis)

Durante las pruebas operativas en `/enterprise/compliance?tab=notifications` (**Flota & Seguridad -> Canales de Alerta & Notificación**), al configurar un canal de **Correo SMTP** (`gmail`) y pulsar **⚡ Probar Envío**, el sistema responde `Despacho Exitoso: Configuración de canal SMTP_EMAIL validada con éxito`, pero **el correo nunca llega** al destinatario, y además **no existe ningún botón para editar** un canal una vez creado.

La auditoría forense del código reveló tres defectos críticos:

### 1.1. Defecto 1: `POST /api/v1/operations/notification-channels/{channel_id}/test` es un Stub que No Envía Nada ([`notification_channels.py#L180-L205`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/notification_channels.py#L180-L205))
- **Causa Raíz:** En [`test_channel`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/notification_channels.py#L181-L205):
  ```python
  conf = _decrypt_channel_config(tenant_id, channel)
  ch_type = channel.channel_type.value

  if ch_type == "TELEGRAM_BOT" and ("bot_token" not in conf or "chat_id" not in conf):
      return NotificationTestResponse(status="FAILED", detail="Faltan 'bot_token' o 'chat_id'")
  if ch_type == "GENERIC_WEBHOOK" and "webhook_url" not in conf:
      return NotificationTestResponse(status="FAILED", detail="Falta 'webhook_url'")

  return NotificationTestResponse(
      status="SUCCESS",
      detail=f"Configuración de canal {ch_type} validada con éxito",
  )
  ```
  El endpoint únicamente descifra el JSON y devuelve `status="SUCCESS"` **sin invocar jamás a `smtplib`, ni a la API de Telegram, ni al Webhook HTTP**.

### 1.2. Defecto 2: Desajuste de Claves JSON (`to_emails` vs `to_addresses`) y Manejo SMTP en [`alert_dispatcher_worker.py#L53-L79`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/workers/alert_dispatcher_worker.py#L53-L79)
- **Causa Raíz:**
  1. En [`NotificationChannelsPanel.vue#L116-L127`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/operations/NotificationChannelsPanel.vue#L116-L127), el formulario guarda el payload SMTP con las claves `from_email` y `to_emails`:
     ```ts
     return {
       smtp_host: smtpHost.value.trim(),
       smtp_port: Number(smtpPort.value),
       smtp_user: smtpUser.value.trim(),
       smtp_password: smtpPassword.value,
       from_email: smtpFrom.value.trim(),
       to_emails: smtpTo.value.split(',').map((s) => s.trim()).filter(Boolean),
     };
     ```
  2. Sin embargo, en [`_dispatch_smtp_sync`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/workers/alert_dispatcher_worker.py#L53-L79), el worker busca `to_addresses` (que no existe en el payload guardado por el frontend) e ignora `from_email`:
     ```python
     to_addrs = config.get("to_addresses", [])
     if not to_addrs:
         return
     ```
     Como `to_addrs` resulta `[]`, el despachador aborta silenciosamente en `if not to_addrs: return` sin enviar ningún correo.
  3. Adicionalmente, cuando se usa Gmail (`smtp.gmail.com`):
     - En puerto `465` (SSL implícito), `smtplib.SMTP(host, port)` falla porque requiere `smtplib.SMTP_SSL(host, port)`.
     - En puerto `587` (`STARTTLS`), conviene ejecutar `server.ehlo()` antes y después de `server.starttls()`.
     - Las *Contraseñas de Aplicación* de Google (`App Passwords` de 16 caracteres mostradas en bloques de 4 como `abcd efgh ijkl mnop`) suelen pegarse con espacios; para `gmail.com` o `googlemail.com`, se deben eliminar espacios internos de `smtp_password` antes de `server.login(user, pwd)`.
     - Si el usuario dejó `to_emails` vacío pero configuró `smtp_user` o `from_email`, debe usar `smtp_user` / `from_email` como destinatario por defecto para que la prueba de su propia cuenta funcione siempre.

### 1.3. Defecto 3: Ausencia de Botón y Modal de Edición (`✏️ Editar`) en [`NotificationChannelsPanel.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/operations/NotificationChannelsPanel.vue#L341-L367)
- **Causa Raíz:**
  - En [`.card-actions`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/operations/NotificationChannelsPanel.vue#L341-L367) solo existen los botones `🧪 Probar` (`⚡ Probar Envío`), `Desactivar`/`Activar` y `🗑️` (Eliminar).
  - Aunque el backend ya expone `PATCH /api/v1/operations/notification-channels/{channel_id}` ([`update_channel`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/notification_channels.py#L124-L162)), el frontend no tiene botón `✏️ Editar` ni modo de edición en el modal, y [`NotificationChannelResponse`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/schemas/notifications.py#L36-L45) no devuelve un resumen sanitizado (`config_summary`) de los parámetros no sensibles (`smtp_host`, `smtp_port`, `smtp_user`, `from_email`, `to_emails`, `chat_id`, `webhook_url`) para prellenar el formulario al editar.

---

## 2. Diseño Técnico de la Solución (Instrucciones Exactas de Implementación)

### 2.1. Backend: Normalización de `_dispatch_smtp_sync` en [`fastapi/src/workers/alert_dispatcher_worker.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/workers/alert_dispatcher_worker.py)

Actualizar [`_dispatch_smtp_sync`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/workers/alert_dispatcher_worker.py#L53-L79) y [`_dispatch_webhook`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/workers/alert_dispatcher_worker.py#L101-L119) para soportar tanto las claves del frontend (`to_emails`, `from_email`, `auth_header`) como las legadas (`to_addresses`, `secret`), puerto `465` (`SMTP_SSL`) vs `587` (`STARTTLS`), y contraseñas de aplicación de Gmail:

```python
def _resolve_smtp_recipients(config: dict[str, Any]) -> list[str]:
    """Extrae la lista de destinatarios desde 'to_emails', 'to_addresses' o fallback a 'smtp_user'/'from_email'."""
    raw_to = config.get("to_emails") or config.get("to_addresses") or []
    if isinstance(raw_to, str):
        recipients = [addr.strip() for addr in raw_to.split(",") if addr.strip()]
    elif isinstance(raw_to, list):
        recipients = [str(addr).strip() for addr in raw_to if str(addr).strip()]
    else:
        recipients = []
    if not recipients:
        fallback = str(config.get("from_email") or config.get("smtp_user") or "").strip()
        if "@" in fallback:
            recipients = [fallback]
    return recipients


def _dispatch_smtp_sync(config: dict[str, Any], alert: dict[str, Any]) -> None:
    host = str(config.get("smtp_host") or "localhost").strip()
    port = int(config.get("smtp_port") or 587)
    user = str(config.get("smtp_user") or "").strip()
    pwd = str(config.get("smtp_password") or "")
    from_addr = str(config.get("from_email") or user or "noreply@rosgrid.local").strip()
    to_addrs = _resolve_smtp_recipients(config)

    if not to_addrs:
        raise ValueError("No se especificaron destinatarios de correo ('to_emails').")

    if "gmail.com" in host.lower() or "googlemail.com" in host.lower():
        pwd_no_spaces = pwd.replace(" ", "")
        if len(pwd_no_spaces) == 16:
            pwd = pwd_no_spaces

    msg = EmailMessage()
    custom_msg = alert.get("custom_message")
    msg["Subject"] = (
        f"[RoSGrid] Prueba de Canal SMTP: {alert.get('channel_name', 'NOC')}"
        if custom_msg
        else f"[RoSGrid] Alerta: {alert.get('event_name')} - {alert.get('router_display_name')}"
    )
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    body_lines = [
        f"Mensaje: {custom_msg}" if custom_msg else f"Evento: {alert.get('event_name')}",
        f"Router: {alert.get('router_display_name', 'N/A')}",
        f"Estado: {alert.get('operational_status', 'TEST')}",
        f"Timestamp: {alert.get('timestamp_iso', '')}",
    ]
    msg.set_content("\n".join(body_lines) + "\n")

    smtp_cls = smtplib.SMTP_SSL if port == 465 else smtplib.SMTP
    with smtp_cls(host, port, timeout=12) as server:
        server.ehlo()
        if port != 465 and config.get("use_tls", True):
            server.starttls()
            server.ehlo()
        if user and pwd:
            server.login(user, pwd)
        server.send_message(msg)
```

### 2.2. Backend: Envío Real en `POST /{channel_id}/test`, `config_summary` y Fusión de Secretos en `PATCH /{channel_id}` ([`fastapi/src/schemas/notifications.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/schemas/notifications.py) y [`fastapi/src/api/v1/notification_channels.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/notification_channels.py))

1. **En [`fastapi/src/schemas/notifications.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/schemas/notifications.py):**
   Añadir `config_summary: dict[str, Any] = Field(default_factory=dict)` a `NotificationChannelResponse`:
   ```python
   class NotificationChannelResponse(StrictBaseModel):
       id: uuid.UUID
       tenant_id: uuid.UUID
       name: str
       channel_type: str
       is_enabled: bool
       subscribed_events: list[str]
       config_summary: dict[str, Any] = Field(default_factory=dict)
       created_at: datetime
       updated_at: datetime
   ```

2. **En [`fastapi/src/api/v1/notification_channels.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/notification_channels.py):**
   - Implementar `_build_safe_config_summary(tenant_id: uuid.UUID, ch: NotificationChannel) -> dict[str, Any]` que descifra la configuración y devuelve los campos no sensibles para poblar el modal de edición sin exponer contraseñas ni tokens en texto plano:
     - Para `TELEGRAM_BOT`: `{"chat_id": conf.get("chat_id", ""), "has_bot_token": bool(conf.get("bot_token"))}`
     - Para `SMTP_EMAIL`:
       ```python
       raw_to = conf.get("to_emails") or conf.get("to_addresses") or []
       to_list = [s.strip() for s in raw_to.split(",") if s.strip()] if isinstance(raw_to, str) else list(raw_to)
       return {
           "smtp_host": conf.get("smtp_host", ""),
           "smtp_port": int(conf.get("smtp_port", 587)),
           "smtp_user": conf.get("smtp_user", ""),
           "from_email": conf.get("from_email", ""),
           "to_emails": to_list,
           "has_password": bool(conf.get("smtp_password")),
       }
       ```
     - Para `GENERIC_WEBHOOK`: `{"webhook_url": conf.get("webhook_url", ""), "has_auth_header": bool(conf.get("auth_header") or conf.get("secret"))}`
   - En `update_channel` (`PATCH /{channel_id}`):
     Cuando `payload.config is not None`, descifrar primero la configuración actual (`existing_conf = _decrypt_channel_config(tenant_id, channel)`) y fusionar (`merged = {**existing_conf, **payload.config}`), **conservando** `existing_conf["smtp_password"]`, `existing_conf["bot_token"]` o `existing_conf["auth_header"]` cuando en `payload.config` vengan vacíos (`""` o `None`), de modo que el usuario pueda editar destinatarios, puerto, remitente o eventos sin tener que volver a escribir la contraseña SMTP o el token de Telegram.
   - En `test_channel` (`POST /{channel_id}/test`):
     Ejecutar el despacho real cuando la configuración tenga un host/token externo real:
     - Validar primero los campos obligatorios:
       - `TELEGRAM_BOT`: `bot_token` y `chat_id` requeridos.
       - `GENERIC_WEBHOOK`: `webhook_url` requerido.
       - `SMTP_EMAIL`: `smtp_host` requerido y al menos un destinatario en `_resolve_smtp_recipients(conf)`.
     - Construir el objeto `alert_payload`:
       ```python
       alert_payload = {
           "event_name": "CHANNEL_TEST",
           "channel_name": channel.name,
           "router_display_name": "RoSGrid Control Plane",
           "operational_status": "ONLINE",
           "timestamp_iso": datetime.now(UTC).isoformat(),
           "custom_message": payload.message or f"Prueba de alerta desde el canal {channel.name}",
       }
       ```
     - Despachar según `ch_type`:
       - En entorno de pruebas unitarias sin servidor real o si ocurre un error de red/autenticación SMTP (`smtplib.SMTPException`, `OSError`, `httpx.HTTPError`, `ValueError`), capturar la excepción y devolver `NotificationTestResponse(status="FAILED", detail=f"Fallo al enviar prueba ({ch_type}): {exc}")`.
       - Para `SMTP_EMAIL`: ejecutar `await asyncio.to_thread(_dispatch_smtp_sync, conf, alert_payload)` y devolver `NotificationTestResponse(status="SUCCESS", detail=f"Correo de prueba enviado con éxito a {', '.join(_resolve_smtp_recipients(conf))} vía {conf.get('smtp_host')}:{conf.get('smtp_port', 587)}")`.
       - Para `TELEGRAM_BOT`: ejecutar `await _dispatch_telegram(conf, alert_payload)`.
       - Para `GENERIC_WEBHOOK`: ejecutar `await _dispatch_webhook(conf, alert_payload)`.

### 2.3. Frontend: Botón `✏️ Editar` y Modal Dual Crear/Editar en [`vue3/src/components/operations/NotificationChannelsPanel.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/operations/NotificationChannelsPanel.vue)

1. **En [`vue3/src/types/index.ts`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/types/index.ts):**
   Añadir `config_summary?: Record<string, unknown>;` a `NotificationChannelItem`.
2. **En [`NotificationChannelsPanel.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/operations/NotificationChannelsPanel.vue):**
   - Añadir estado `const editingChannelId = ref<string | null>(null);`.
   - Añadir función `openEditModal(ch: NotificationChannelItem)`:
     - Asigna `editingChannelId.value = ch.id`, `formName.value = ch.name`, `formType.value = ch.channel_type`, `formIsEnabled.value = ch.is_enabled`, `formSubscribedEvents.value = [...ch.subscribed_events]`.
     - Carga los datos desde `const summary = ch.config_summary || {};`:
       - Si `ch.channel_type === 'SMTP_EMAIL'`: `smtpHost.value = String(summary.smtp_host || '')`, `smtpPort.value = Number(summary.smtp_port || 587)`, `smtpUser.value = String(summary.smtp_user || '')`, `smtpPassword.value = ''`, `smtpFrom.value = String(summary.from_email || '')`, `smtpTo.value = Array.isArray(summary.to_emails) ? summary.to_emails.join(', ') : String(summary.to_emails || '')`.
       - Si `ch.channel_type === 'TELEGRAM_BOT'`: `telegramChatId.value = String(summary.chat_id || '')`, `telegramBotToken.value = ''`.
       - Si `ch.channel_type === 'GENERIC_WEBHOOK'`: `webhookUrl.value = String(summary.webhook_url || '')`, `webhookAuthHeader.value = ''`.
     - Abre el modal (`isCreateModalOpen.value = true`).
   - En `handleCreateChannel()` (renombrado o adaptado para soportar creación y edición):
     - Si `editingChannelId.value` está presente:
       - Invocar `await http.patch(\`/api/v1/operations/notification-channels/\${editingChannelId.value}\`, payload)`.
       - Mostrar `successMessage.value = \`Canal "\${formName.value}" actualizado con éxito.\``.
     - En modo creación (`!editingChannelId.value`):
       - Validar que para `SMTP_EMAIL` se indique `smtpHost.value.trim()` y al menos un destinatario en `smtpTo.value.trim()` (o `smtpUser.value.trim()`).
       - Invocar `await http.post('/api/v1/operations/notification-channels', payload)`.
   - En la tarjeta `.card-actions` de cada canal (`NotificationChannelsPanel.vue` líneas 341–367), añadir el botón **`✏️ Editar`** junto a `⚡ Probar Envío` y `Desactivar`:
     ```html
     <button
       :id="'btn-edit-channel-' + ch.id"
       type="button"
       class="btn-card-action btn-edit"
       title="Editar configuración del canal"
       @click="openEditModal(ch)"
     >
       ✏️ {{ t('common.edit', 'Editar') }}
     </button>
     ```

---

## 3. Criterios de Aceptación y Pirámide de Pruebas 11X

1. **Pruebas Unitarias Backend:**
   - En [`fastapi/tests/api/test_operations_endpoints_full.unit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/tests/api/test_operations_endpoints_full.unit.py) y [`fastapi/tests/workers/test_workers_full.unit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/tests/workers/test_workers_full.unit.py):
     - Verificar que `_dispatch_smtp_sync` procese correctamente `to_emails` (lista o string), `from_email`, puerto `587` (`STARTTLS`) y puerto `465` (`SMTP_SSL`), y normalice contraseñas de aplicación de 16 caracteres con espacios para Gmail.
     - Verificar que `POST /api/v1/operations/notification-channels/{id}/test` invoque realmente el despachador del canal y devuelva `status="FAILED"` si el servidor SMTP rechaza la conexión o las credenciales.
     - Verificar que `GET /api/v1/operations/notification-channels` incluya `config_summary` sin exponer secretos y que `PATCH /api/v1/operations/notification-channels/{id}` conserve la contraseña previa si `smtp_password` se envía vacío.
2. **Pruebas Unitarias Frontend:**
   - En [`vue3/src/components/operations/NotificationChannelsPanel.unit.ts`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/operations/NotificationChannelsPanel.unit.ts):
     - Verificar la presencia del botón `✏️ Editar` (`#btn-edit-channel-<id>`), la precarga de `config_summary` en el modal y la llamada `PATCH /api/v1/operations/notification-channels/<id>` al guardar cambios.
3. **Escenarios BDD Karate Labs:**
   - Añadir validación en [`fastapi/test/api_test.feature`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/test/api_test.feature) y [`vue3/test/ui_business_flow.feature`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/test/ui_business_flow.feature) (y réplicas en `docs/examples/`).
