# Especificación 114: Remediación Integral de Seguridad Zero-Trust, RLS Multi-Transacción, Cadena WORM Determinista, WCAG 2.1 AA e Infraestructura 11X (Hito 30.38)

## 1. Contexto y Objetivo Arquitectónico

Esta especificación documenta la remediación integral de los **65 hallazgos técnicos y de seguridad** identificados en la auditoría arquitectónica de los 5 dominios del monorepo **RoSGrid** (`Infra/CI/CD`, `Frontend Vue 3`, `Documentación & Gobernanza`, `Backend FastAPI Core/Workers/DB` y `Seguridad & Autenticación Zero-Trust`).

---

## 2. Arquitectura de Seguridad y Autenticación (`fastapi/src/`)

1. **Validación Fail-Fast de Secretos en Producción (`src/core/config.py`):**
   - El validador `_validate_production_secrets()` aborta el arranque si `ROSGRID_ENV == "production"` y cualquiera de las llaves `ROSGRID_MASTER_VAULT_KEY`, `ROSGRID_JWT_SECRET_KEY` o `ROSGRID_CSRF_HMAC_SECRET` conserva el valor QA por defecto o mide menos de 32 caracteres.
2. **Persistencia de Contexto PostgreSQL RLS tras `commit()` Intermedios (`src/db/session.py` y `migrations/versions/0016_rls_worm_seq_and_fk_idx.py`):**
   - Se registra un listener `@event.listens_for(AsyncSession.sync_session_class, "after_begin")` que reaplica automáticamente `app.current_tenant_id` y `app.is_superadmin_global` al iniciar cualquier transacción subsecuente en la misma sesión tras un `await db.commit()`.
   - La migración `0016` crea el rol `rosgrid_app` (`NOSUPERUSER NOBYPASSRLS`), la función `SECURITY DEFINER` `public.fn_resolve_tenant_by_slug(p_slug TEXT)` para resolución segura pre-autenticación y políticas uniformes `tenant_isolation_*` con soporte para `app.is_superadmin_global`.
3. **Aislamiento de Alcance `SERVICE_ACCOUNT` (`mcp_only`) y Prevención de Escalada RBAC (`src/api/deps.py`, `src/api/v1/users.py`):**
   - Los tokens emitidos para `SERVICE_ACCOUNT` incluyen `"scope": "mcp_only"` y `get_current_user_claims` bloquea (`HTTP 403`) su uso fuera de `/api/v1/mcp`.
   - `TENANT_ADMIN` tiene prohibido modificar, desactivar o cambiar contraseñas de cuentas `SUPERADMIN_GLOBAL` (`HTTP 403`).
   - `approve_user` (cuando cambia el rol) y `reject_user` ejecutan `kill_all_user_sessions` en KeyDB.
4. **Higiene Redis Anti-Glob Injection y Re-Validación en Refresh (`src/api/v1/auth.py`):**
   - Se valida `challenge_id` y `sid` mediante `_SAFE_REDIS_ID_RE = re.compile(r"^[a-zA-Z0-9_\-:.]{1,128}$")` y se indexa `rg:preauth_idx:{challenge_id}` para evitar escaneos `KEYS` con metacaracteres.
   - `refresh_access_token` verifica en PostgreSQL que el usuario continúe activo (`is_active == True`, `is_locked == False`) y sincroniza su rol actual antes de emitir nuevos tokens; además soporta la cookie `__Secure-rg_rt`.
   - El login sobre cuentas bloqueadas ejecuta `verify_dummy_password(password)` para mitigar ataques de enumeración por tiempos de respuesta (*Timing Attack*).
5. **Ejecución Diferida Maker-Checker, Step-Up 2FA y Bloqueo Pesimista (`src/api/v1/approvals.py`):**
   - `resolve_approval_request` adquiere bloqueo de fila `SELECT ... FOR UPDATE`, exige verificación TOTP Step-Up (`stepup_totp_code`) cuando el aprobador tiene 2FA activo, soporta `PPP_ACTIVE_REMOVE_RECONNECT` y garantiza `await client.close()` en bloques `finally`.
6. **Defensa Anti-SSRF Unificada y Verificación de Huella TLS en Vivo (`src/schemas/inventory.py`, `src/mikrotik/client.py`, `src/services/network_events.py`, `src/workers/alert_dispatcher_worker.py`):**
   - Normalización de `_`/`-` en nombres de host, bloqueo de dominios comodín (`.localhost`, `.localtest.me`, `.nip.io`, `.sslip.io`, `.xip.io`) y bloqueo de direcciones `is_unspecified` / `is_multicast`.
   - `MikroTikRestClient._raw_send` verifica en tiempo real la huella SHA-256 del certificado TLS del peer contra `pinned_cert_sha256` y cierra siempre el `AsyncClient` en bloques `try ... finally`.
7. **Cadena Forense WORM Determinista (`src/models/operations.py`, `src/core/audit.py`):**
   - Se incorpora `seq_num: Mapped[int]` (`BigInteger Identity`) a `AuditLog` y bloqueo transaccional `pg_advisory_xact_lock(hashtext(:tid))` junto con encadenamiento en memoria dentro de la misma transacción para impedir bifurcaciones de `prev_record_hash`.

---

## 3. Endurecimiento de Frontend (`vue3/`), Accesibilidad e i18n

1. **Seguridad en Cliente y Proxy Nginx (`LoginView.vue`, `httpClient.ts`, `OsmRouterMap.vue`, `OsmOnuMap.vue`, `vue3/nginx/default.conf`):**
   - Eliminación del fallback estático `'csrf-session'`, validación de origen en `resolveUrl` y en `route.query.redirect` (*Anti-Open Redirect*), y escapado `escapeHtml(...)` en iconos y popups de Leaflet.
   - Cabeceras de seguridad persistidas en bloques estáticos de Nginx, `Permissions-Policy: geolocation=(self)` para captura GPS de campo y restricción de `/stub_status` a redes RFC1918/loopback.
2. **Semántica HTML, Temas Dinámicos, Paridad i18n y Tipado Estricto:**
   - Eliminación de `data-theme="noc-dark"` hardcodeado y reemplazo de `<main>` anidados en vistas hijas por `<div role="region">`, preservando un único `<main id="main-content">` en `RgResponsiveShell.vue`.
   - Paridad completa entre `es.json` y `en.json`, atributos `aria-label` en botones de cierre (`✕`), `role="button" tabindex="0"` en `.kpi-card` y `scope="col"` en `<th>`.

---

## 4. Infraestructura, CI/CD y Gobernanza Documental

1. **Pipelines CI/CD y Docker Compose:**
   - Fijación de SHA en `.github/workflows/00-iac-audit.yml` e incorporación de `.github/workflows/01-backend-qa.yml` y `.github/workflows/02-frontend-qa.yml`.
   - `ROSGRID_TELEMETRY_BEACON_ENABLED=false` (*Opt-In* por defecto) en los tres `docker-compose*.yml`, inyección de secretos en `rosgrid-worker`, `security_opt: [no-new-privileges:true]` y exposición local `127.0.0.1:8000:8000`.
2. **Gobernanza y Archivo Histórico (`docs/archive/`):**
   - Ejecución 100% en contenedores efímeros dentro de `.agents/scripts/certify_task_completion.sh` (**Regla Cero**), archivo histórico de hitos cerrados (`0–29`) en `docs/archive/ROADMAP_HITOS_00-29.md` y `docs/archive/TESTING_HISTORICO.md`, y sincronización completa del índice maestro `00_MASTER_INDEX_AND_11X_GOVERNANCE.md` (Specs `01` a `114`).
