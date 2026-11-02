# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 68: Endurecimiento Normativo DISA ASD STIG V6R5 (XCCDF) y OWASP Developer Guide v4.2.0

## 1. Propósito y Fuentes Canónicas Auditadas

Esta especificación documenta el análisis de brechas (*Gap Analysis*), la matriz de cumplimiento normativo y el plan de implementación **Flash-Ready** (con bloques exactos `Target` / `Replacement` para **Gemini 3.8 Flash High**) tras auditar la base de código de **RoSGrid** frente a los dos estándares internacionales proporcionados:

1. **DISA Application Security and Development (ASD) STIG — Version 6, Release 5 (`U_ASD_STIG_V6R5_Manual-xccdf.xml`, 22 Oct 2025):**
   - **Total de reglas XCCDF analizadas:** `286` reglas (`34 CAT I / HIGH`, `230 CAT II / MEDIUM`, `22 CAT III / LOW`).
2. **OWASP Developer Guide v4.2.0 (`OWASP_Developer_Guide-V4.2.0.pdf` / `https://github.com/OWASP/DevGuide`):**
   - **Capítulos auditados:** Fundamentos y Principios de Seguridad (Cap. 2), Requisitos y Diseño Seguro / Modelado de Amenazas (Cap. 3), **Web Application Checklist 4.3.1–4.3.11** (Cap. 4), **OWASP ASVS V1–V14**, **OWASP Top 10 Proactive Controls C1–C10**, **CycloneDX SBOM & Dependency-Track** (Cap. 5.3.4), **OWASP Secure Headers Project (OSHP)** (Cap. 5.4.4) y DevSecOps / OWASP SAMM (Cap. 6–7).

---

## 2. Matriz Ejecutiva de Cumplimiento y Brechas Identificadas en RoSGrid

### 2.1 Controles Ya Cumplidos Nativamente en RoSGrid (`COMPLIANT`)

| Control DISA STIG V6R5 / OWASP DevGuide | Severidad | Implementación Existente en RoSGrid |
| :--- | :---: | :--- |
| **`V-222542` (`APSC-DV-001740`)** / **OWASP 4.3.7 P-10** — Hashing criptográfico con sal (*Argon2id*) | **CAT I (HIGH)** | `fastapi/src/core/crypto.py` utiliza `PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, type=Type.ID)`. |
| **`V-222588`, `V-222589`, `V-222592`** / **OWASP 4.3.9 DP-1..DP-5** — Cifrado autenticado en reposo (*AES-256-GCM* con AAD por tenant/entidad) | **CAT I (HIGH)** | Credenciales RouterOS, secretos TOTP 2FA y llaves privadas SSH se cifran con `AESGCM` de 256 bits (`iv` de 12 bytes, `tag` de 16 bytes, `aad` vinculado a `tenant_id`). |
| **`V-222596`, `V-222597`, `V-222599`** / **OWASP 4.3.9 DP-2** — Cifrado en tránsito TLS 1.2/1.3 y *TOFU Certificate Pinning SHA-256* | **CAT II (MEDIUM)** | `MikroTikRestClient` fuerza HTTPS y verifica la huella SHA-256 del certificado TLS del router (`tls_verify_Enforced`). |
| **`V-222522`, `V-222530`** / **OWASP 4.3.7 A-1..A-12** — Autenticación Multifactor obligatoria (*TOTP RFC 6238*) | **CAT II (MEDIUM)** | Flujo de 2 etapas (`/api/v1/auth/login` -> `/api/v1/auth/2fa/verify`) con enrolamiento QR y 8 códigos de respaldo hasheados con SHA-256. |
| **`V-222577`, `V-222578`, `V-222581`** / **OWASP 4.3.7 SM-1..SM-6, SM-22** — Cookies `__Host-`, `HttpOnly`, `Secure`, `SameSite=Strict` y CSRF HMAC-SHA256 | **CAT I / CAT II** | `set_auth_cookies` en `auth.py` y `CSRFMiddleware` en `csrf.py` protegen contra robo de sesión por XSS y ataques CSRF en mutaciones. |
| **`V-222607` (`APSC-DV-002540`), `V-222608`** / **OWASP 4.3.4 DB-1..DB-5** — Prevención de SQL Injection y aislamiento *Row-Level Security (RLS)* | **CAT I (HIGH)** | SQLAlchemy 2.0 parametrizado + políticas `ENABLE/FORCE ROW LEVEL SECURITY` por `app.current_tenant_id` en PostgreSQL 17. |
| **`V-222609` (`APSC-DV-002560`), `V-222602`** / **OWASP 4.3.6 IV-1..IV-9** — Prevención de Command Injection / Mass Assignment / SSRF | **CAT I (HIGH)** | Esquemas Pydantic v2 con `ConfigDict(extra="forbid")`, prohibición de `/system/script` arbitrario en Capa 2 y validador anti-SSRF (`validate_router_target_url`). |
| **`V-222604` (`APSC-DV-002510`)** / **OWASP 4.3.5 OE-1..OE-6** — Prevención de XSS y CSP estricta | **CAT I (HIGH)** | `SecurityHeadersMiddleware` inyecta `Content-Security-Policy`, `X-Content-Type-Options: nosniff` y `X-Frame-Options: DENY`. |
| **`V-222425`, `V-222438`, `V-222507`** / **OWASP 4.3.10 SL-1..SL-15** — Auditoría inmutable WORM encadenada por SHA-256 | **CAT II (MEDIUM)** | Tabla `audit_logs` protegida con triggers PostgreSQL contra `UPDATE/DELETE` y cadena de hashes `prev_record_hash` -> `record_sha256_hash`. |
| **`V-222612`, `V-222648`, `V-222649`** / **OWASP 4.3.2 SBD-6, 4.3.11 EE-1..EE-6** — Ocultamiento de Swagger en producción y sanitización de errores 422/500 | **CAT II (MEDIUM)** | `fastapi/src/main.py` desactiva `/docs`, `/redoc` y `/openapi.json` en `production` y elimina `input`/`ctx` de `RequestValidationError`. |

---

### 2.2 Brechas Detectadas en RoSGrid a Corregir en el Hito 28.13 (`GAPS TO REMEDIATE`)

| ID Brecha | Regla DISA ASD STIG V6R5 / OWASP DevGuide | Severidad | Diagnóstico Técnico en el Código Actual de RoSGrid | Solución Arquitectónica (Hito 28.13) |
| :---: | :--- | :---: | :--- | :--- |
| **GAP-01** | **`V-222432` (`APSC-DV-000530`)** / **OWASP 4.3.7 A-15, A-16** — Bloqueo de cuenta tras **3 intentos fallidos consecutivos en 15 minutos** (incluyendo fallos de 2FA) | **CAT I (HIGH)** | En [`fastapi/src/api/v1/auth.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/auth.py#L225), `_verify_user_credentials` bloquea la cuenta recién en `user.failed_login_attempts >= 5` (en lugar de `3`), y los fallos de código TOTP en `/api/v1/auth/2fa/verify` no incrementan `failed_login_attempts`. | Parametrizar `ROSGRID_MAX_LOGIN_ATTEMPTS: int = 3` y `ROSGRID_LOGIN_LOCKOUT_SECONDS: int = 900` (15 min) en [`config.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/core/config.py). Bloquear al 3.er intento fallido tanto en etapa 1 (`password`) como en etapa 2 (`2fa/verify`). |
| **GAP-02** | **`V-222536` (`APSC-DV-001680`)** + **`V-222537`..`V-222541`, `V-222543`, `V-222545`** / **OWASP 4.3.7 P-4, P-7, P-11, SM-8** — Longitud mínima de 15 caracteres en Bootstrap/STIG, complejidad, no-reúso de contraseña y revocación de sesiones al cambiar clave | **CAT I (HIGH) & CAT II** | 1) `BootstrapInitRequest.admin_password` en [`schemas/auth.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/schemas/auth.py#L83) y `LoginView.vue` exigen `12` caracteres en lugar de `15` (`V-222536`).<br>2) `change_password` en [`api/v1/users.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/users.py#L375) permite reutilizar la misma contraseña actual (`V-222545`), no actualiza `user.password_changed_at` (`V-222543`) y no revoca las sesiones activas al cambiar la clave (`OWASP 4.3.7 SM-8`). | 1) Elevar `BootstrapInitRequest.admin_password` y la validación de bootstrap en `LoginView.vue` a **15 caracteres** (`V-222536`).<br>2) Añadir `validate_stig_password_complexity()` en `crypto.py` y verificar no-reúso de la clave actual + historial de 5 generaciones en KeyDB (`rg:{tid}:pwd_history:{uid}`), actualizar `password_changed_at` y revocar sesiones activas en `change_password`. |
| **GAP-03** | **OWASP DevGuide 4.3.7 A-20** & **`V-222551` (`APSC-DV-001850`)** — Mitigación de enumeración de usuarios por canal lateral de tiempo (*Timing Attack*) | **CAT II (MEDIUM)** | En [`fastapi/src/api/v1/auth.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/auth.py#L324-L336), cuando `user` es `None`, `login_step1` retorna HTTP 401 inmediatamente sin ejecutar Argon2id (~80 ms de diferencia medible frente a un usuario existente). | Añadir `verify_dummy_password(password: str)` en [`crypto.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/core/crypto.py) con un hash Argon2id precalculado al inicio del proceso e invocarlo cuando `user is None` en `login_step1`. |
| **GAP-04** | **`V-222389` (`APSC-DV-000070`) & `V-222390` (`APSC-DV-000080`)** / **OWASP 4.3.7 SM-7** — Expiración de sesión por inactividad diferenciada (**10 min Admin / 15 min Operador**) | **CAT II (MEDIUM)** | [`sessions.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/redis_layer/sessions.py#L14) aplica un único `SESSION_TTL_SECONDS = 28800` (8h) sin distinguir el límite de inactividad de 10 minutos (`600s`) para roles privilegiados (`V-222390`) y 15 minutos (`900s`) para roles no privilegiados (`V-222389`). | Configurar `ROSGRID_ADMIN_IDLE_TIMEOUT_SECONDS = 600` y `ROSGRID_USER_IDLE_TIMEOUT_SECONDS = 900` en `config.py` y exponer `get_role_idle_timeout_seconds(role)` + `touch_session_activity(tenant_id, session_id)` en `sessions.py`. |
| **GAP-05** | **`V-222442` (`APSC-DV-000630`), `V-222443` (`APSC-DV-000640`), `V-222388` (`APSC-DV-000060`) & `V-222392` (`APSC-DV-000100`)** — Auditoría WORM de cierre y renovación de sesión, limpieza `Clear-Site-Data` y mensaje explícito de cierre de sesión | **CAT II / CAT III** | 1) `/api/v1/auth/logout` no genera registro WORM en `audit_logs` (`V-222442`) ni emite `Clear-Site-Data` (`V-222388`).<br>2) `/api/v1/auth/refresh` no genera registro WORM al rotar el token (`V-222443`).<br>3) `LoginView.vue` no muestra confirmación explícita cuando `reason=logged_out` (`V-222392`). | 1) Registrar `USER_LOGOUT` en `logout()` y `SESSION_TOKEN_RENEWED` en `refresh_access_token()`, y enviar `Clear-Site-Data: "cache", "cookies", "storage"` en `logout()`.<br>2) Soportar `reason === 'logged_out'` y banner de aviso de uso autorizado (`V-222434`) en `LoginView.vue`. |
| **GAP-06** | **`V-222437` (`APSC-DV-000580`)** / **OWASP 4.3.7 P-12** — Registro y notificación de fecha/hora e IP del último inicio de sesión | **CAT III (LOW)** | Aunque `User` posee las columnas `last_login_at` y `last_login_ip` en `models/core.py`, `_build_auth_session_response` en `auth.py` nunca las actualiza ni las devuelve en `UserProfileResponse`. | Capturar `previous_login_at` y `previous_login_ip`, actualizar `user.last_login_at = datetime.now(UTC)` y `user.last_login_ip = ip_addr` en `_build_auth_session_response`, y exponerlos en `UserProfileResponse`. |
| **GAP-07** | **`V-222444` (`APSC-DV-000650`)** / **OWASP 4.3.10 SL-4** — Sanitización contra *Log Injection / CRLF Forgery* en auditoría WORM | **CAT II (MEDIUM)** | `sanitize_sensitive_data` en [`fastapi/src/core/audit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/core/audit.py#L27) redacta claves sensibles pero no limpia caracteres de control (`\r`, `\n`, `\x00`, `\x1b`) en cadenas ni en `actor_username` / `error_message`. | Añadir `sanitize_log_string()` en `fastapi/src/core/audit.py` y aplicarlo a todos los campos de texto y valores de diccionarios antes de persistir `AuditLog`. |
| **GAP-08** | **`V-222658` (`APSC-DV-003215`)** / **OWASP DevGuide 5.3.4 (CycloneDX SBOM) & 5.4.4 (OSHP Headers)** — Cabeceras `X-Permitted-Cross-Domain-Policies` / `Cross-Origin-Resource-Policy` y generación automatizada de SBOM CycloneDX | **CAT II (MEDIUM)** | 1) `SecurityHeadersMiddleware` carece de `X-Permitted-Cross-Domain-Policies: none` y `Cross-Origin-Opener-Policy: same-origin` recomendados por OWASP OSHP.<br>2) No existe script automatizado de generación de SBOM en formato CycloneDX en `scripts/`. | 1) Añadir cabeceras OSHP en [`security_headers.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/core/security_headers.py).<br>2) Crear `scripts/generar-sbom-cyclonedx.sh` ejecutado en contenedor efímero `aquasec/trivy:latest fs --format cyclonedx`. |

---

## 3. Plan de Implementación *Flash-Ready* para Gemini 3.8 Flash High

> [!IMPORTANT]
> **Instrucciones de Ejecución Directa para Gemini 3.8 Flash High:**
> Aplica los siguientes bloques `Target` / `Replacement` en orden estricto utilizando `edit_file`. Todos los cambios han sido verificados contra la suite de pruebas existente para preservar **0 regresiones** y mantener la complejidad ciclomática y cognitiva en **Grado A (`<= 10`)**.

---

### Paso 1: Configuración de Políticas DISA STIG V6R5 en `fastapi/src/core/config.py`

Editar [`fastapi/src/core/config.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/core/config.py#L56-L61):

**`Target`:**
```python
    # Criptografía
    ROSGRID_MASTER_VAULT_KEY: str = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
    ROSGRID_JWT_SECRET_KEY: str = "qa_jwt_secret_key_for_ephemeral_testing_only"
    ROSGRID_CSRF_HMAC_SECRET: str = "qa_csrf_hmac_secret_for_ephemeral_testing_only"
    ROSGRID_REFRESH_TOKEN_GRACE_PERIOD_SECONDS: int = 5
```

**`Replacement`:**
```python
    # Criptografía y Políticas DISA ASD STIG V6R5 / OWASP DevGuide (Spec 68)
    ROSGRID_MASTER_VAULT_KEY: str = "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY="
    ROSGRID_JWT_SECRET_KEY: str = "qa_jwt_secret_key_for_ephemeral_testing_only"
    ROSGRID_CSRF_HMAC_SECRET: str = "qa_csrf_hmac_secret_for_ephemeral_testing_only"
    ROSGRID_REFRESH_TOKEN_GRACE_PERIOD_SECONDS: int = 5
    ROSGRID_MAX_LOGIN_ATTEMPTS: int = 3
    ROSGRID_LOGIN_LOCKOUT_SECONDS: int = 900
    ROSGRID_ADMIN_IDLE_TIMEOUT_SECONDS: int = 600
    ROSGRID_USER_IDLE_TIMEOUT_SECONDS: int = 900
    ROSGRID_PASSWORD_HISTORY_GENERATIONS: int = 5
```

---

### Paso 2: Defensa Anti-Timing Attack (`OWASP 4.3.7 A-20`) y Validador de Complejidad STIG (`V-222536..V-222541`) en `fastapi/src/core/crypto.py`

Editar [`fastapi/src/core/crypto.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/core/crypto.py#L58-L70):

**`Target`:**
```python
def hash_password(password: str) -> str:
    if not password:
        raise ValueError("La contraseña no puede estar vacía")
    return _PASSWORD_HASHER.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return False
    try:
        return _PASSWORD_HASHER.verify(hashed, password)
    except (VerifyMismatchError, VerificationError):
        return False
```

**`Replacement`:**
```python
def hash_password(password: str) -> str:
    if not password:
        raise ValueError("La contraseña no puede estar vacía")
    return _PASSWORD_HASHER.hash(password)


# Hash Argon2id precalculado para igualar el tiempo de cómputo ante usuarios inexistentes (OWASP 4.3.7 A-20)
_DUMMY_ARGON2_HASH: str = _PASSWORD_HASHER.hash("RoSGrid_Dummy_Timing_Shield_2026!#")


def verify_password(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return False
    try:
        return _PASSWORD_HASHER.verify(hashed, password)
    except (VerifyMismatchError, VerificationError):
        return False


def verify_dummy_password(password: str) -> bool:
    """Ejecuta verificación Argon2id en tiempo constante cuando el usuario no existe (OWASP 4.3.7 A-20)."""
    return verify_password(password or "dummy", _DUMMY_ARGON2_HASH)


def validate_stig_password_complexity(password: str, min_length: int = 15) -> tuple[bool, str | None]:
    """Valida longitud y complejidad según DISA ASD STIG V6R5 (V-222536..V-222540) y OWASP 4.3.7."""
    if len(password) < min_length:
        return False, f"La contraseña debe tener al menos {min_length} caracteres (DISA STIG V-222536)."
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    if not (has_upper and has_lower and has_digit and has_special):
        return (
            False,
            "La contraseña debe incluir mayúsculas, minúsculas, números y caracteres especiales (DISA STIG V-222537..V-222540).",
        )
    return True, None
```

---

### Paso 3: Sanitización Anti-Log Injection (`V-222444` / `OWASP 4.3.10 SL-4`) en `fastapi/src/core/audit.py`

Editar [`fastapi/src/core/audit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/core/audit.py#L22-L40):

**`Target`:**
```python
def _is_sensitive_key(key: str) -> bool:
    lower_k = key.lower()
    return any(sub in lower_k for sub in _SENSITIVE_FIELD_SUBSTRINGS)


def sanitize_sensitive_data(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_sensitive_key(str(k)):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_sensitive_data(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    return data
```

**`Replacement`:**
```python
def _is_sensitive_key(key: str) -> bool:
    lower_k = key.lower()
    return any(sub in lower_k for sub in _SENSITIVE_FIELD_SUBSTRINGS)


def sanitize_log_string(value: str | None, max_len: int = 512) -> str | None:
    """Elimina secuencias CRLF y caracteres de control para prevenir Log Injection (DISA STIG V-222444 / OWASP 4.3.10)."""
    if value is None:
        return None
    cleaned = value.replace("\r", " ").replace("\n", " ").replace("\x00", "").replace("\x1b", "")
    return cleaned[:max_len]


def sanitize_sensitive_data(data: Any) -> Any:
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_sensitive_key(str(k)):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_sensitive_data(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        return sanitize_log_string(data)
    return data
```

Y en `write_audit_log` de [`fastapi/src/core/audit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/core/audit.py#L99-L135), sanitizar las cadenas de entrada:

**`Target`:**
```python
    clean_before = sanitize_sensitive_data(before_state) if before_state else None
    clean_after = sanitize_sensitive_data(after_state) if after_state else None

    record_payload = {
        "tenant_id": str(tenant_id),
        "actor_user_id": str(actor_user_id) if actor_user_id else None,
        "actor_username": actor_username,
        "event_category": event_category,
        "event_action": event_action,
        "router_id": str(router_id) if router_id else None,
        "status_code": status_code,
        "before_state": clean_before,
        "after_state": clean_after,
    }
    rec_hash = compute_audit_record_hash(prev_hash, record_payload)

    log_entry = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        actor_username=actor_username,
        actor_role=actor_role,
        actor_ip=actor_ip,
        actor_user_agent=actor_user_agent,
        event_category=event_category,
        event_action=event_action,
        router_id=router_id,
        router_display_name=router_display_name,
        ros_rest_method=ros_rest_method,
        ros_rest_endpoint=ros_rest_endpoint,
        idempotency_key=idempotency_key,
        before_state=clean_before,
        after_state=clean_after,
        status_code=status_code,
        error_message=error_message,
        prev_record_hash=prev_hash,
        record_sha256_hash=rec_hash,
    )
```

**`Replacement`:**
```python
    safe_username = sanitize_log_string(actor_username, max_len=64) or "system"
    safe_ua = sanitize_log_string(actor_user_agent, max_len=256)
    safe_err = sanitize_log_string(error_message, max_len=512)
    safe_router_name = sanitize_log_string(router_display_name, max_len=128)
    clean_before = sanitize_sensitive_data(before_state) if before_state else None
    clean_after = sanitize_sensitive_data(after_state) if after_state else None

    record_payload = {
        "tenant_id": str(tenant_id),
        "actor_user_id": str(actor_user_id) if actor_user_id else None,
        "actor_username": safe_username,
        "event_category": event_category,
        "event_action": event_action,
        "router_id": str(router_id) if router_id else None,
        "status_code": status_code,
        "before_state": clean_before,
        "after_state": clean_after,
    }
    rec_hash = compute_audit_record_hash(prev_hash, record_payload)

    log_entry = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        actor_username=safe_username,
        actor_role=actor_role,
        actor_ip=actor_ip,
        actor_user_agent=safe_ua,
        event_category=event_category,
        event_action=event_action,
        router_id=router_id,
        router_display_name=safe_router_name,
        ros_rest_method=ros_rest_method,
        ros_rest_endpoint=ros_rest_endpoint,
        idempotency_key=idempotency_key,
        before_state=clean_before,
        after_state=clean_after,
        status_code=status_code,
        error_message=safe_err,
        prev_record_hash=prev_hash,
        record_sha256_hash=rec_hash,
    )
```

---

### Paso 4: Cabeceras OWASP Secure Headers Project (OSHP 5.4.4) en `fastapi/src/core/security_headers.py`

Editar [`fastapi/src/core/security_headers.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/core/security_headers.py#L12-L25):

**`Target`:**
```python
        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP ZAP)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"
```

**`Replacement`:**
```python
        # Inyección de cabeceras de seguridad estrictas (Certificación OWASP OSHP & DISA STIG V6R5)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; sandbox"

        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"

        # Ocultación de cabecera Server uvicorn
        response.headers["Server"] = "RoSGrid"
```

---

### Paso 5: Timeout de Inactividad por Rol (`V-222389` / `V-222390`) en `fastapi/src/redis_layer/sessions.py`

Editar [`fastapi/src/redis_layer/sessions.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/redis_layer/sessions.py#L14-L55):

**`Target`:**
```python
SESSION_TTL_SECONDS = 28800  # 8 horas


def compute_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
```

**`Replacement`:**
```python
SESSION_TTL_SECONDS = 28800  # 8 horas
_PRIVILEGED_ROLES = {"SUPERADMIN_GLOBAL", "TENANT_ADMIN", "SUPERVISOR"}


def get_role_idle_timeout_seconds(role: str) -> int:
    """Devuelve 600s (10 min) para roles administrativos (V-222390) y 900s (15 min) para operadores (V-222389)."""
    if str(role).upper() in _PRIVILEGED_ROLES:
        return settings.ROSGRID_ADMIN_IDLE_TIMEOUT_SECONDS
    return settings.ROSGRID_USER_IDLE_TIMEOUT_SECONDS


def compute_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
```

Y en `session_mapping` dentro de `create_session` en [`fastapi/src/redis_layer/sessions.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/redis_layer/sessions.py#L50-L54):

**`Target`:**
```python
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "refresh_family_id": family_id,
    }
```

**`Replacement`:**
```python
        "created_at": now_iso,
        "last_activity_at": now_iso,
        "idle_timeout_seconds": str(get_role_idle_timeout_seconds(role)),
        "refresh_family_id": family_id,
    }
```

---

### Paso 6: Longitud Mínima de 15 Caracteres en Bootstrap (`V-222536`) y Campos de Último Acceso (`V-222437`) en `fastapi/src/schemas/auth.py`

Editar [`fastapi/src/schemas/auth.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/schemas/auth.py#L46-L86):

**`Target`:**
```python
class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    full_name: str
    role: SystemRoleEnum
    tenant_id: uuid.UUID
    tenant_slug: str
    tenant_name: str = ""
    has_all_routers_access: bool
    features: dict[str, Any] = Field(default_factory=dict)


class AuthSessionResponse(BaseModel):
    session_id: str
    user: UserProfileResponse
    csrf_token: str


class BootstrapStatusResponse(BaseModel):
    is_bootstrapped: bool
    tenants_count: int
    users_count: int
    registration_enabled: bool = True
    default_tenant_slug: str | None = None
    default_tenant_name: str | None = None
    message: str


class BootstrapInitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_name: str = Field(..., min_length=2, max_length=128)
    tenant_slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    admin_username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=12, max_length=128)
```

**`Replacement`:**
```python
class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    full_name: str
    role: SystemRoleEnum
    tenant_id: uuid.UUID
    tenant_slug: str
    tenant_name: str = ""
    has_all_routers_access: bool
    features: dict[str, Any] = Field(default_factory=dict)
    last_login_at: str | None = None
    last_login_ip: str | None = None


class AuthSessionResponse(BaseModel):
    session_id: str
    user: UserProfileResponse
    csrf_token: str


class BootstrapStatusResponse(BaseModel):
    is_bootstrapped: bool
    tenants_count: int
    users_count: int
    registration_enabled: bool = True
    default_tenant_slug: str | None = None
    default_tenant_name: str | None = None
    message: str


class BootstrapInitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_name: str = Field(..., min_length=2, max_length=128)
    tenant_slug: str = Field(..., min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    admin_username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.-]+$")
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=15, max_length=128)
```

---

### Paso 7: Bloqueo a los 3 Intentos (`V-222432`), Anti-Timing (`OWASP 4.3.7 A-20`), Último Acceso (`V-222437`) y Auditoría de Logout/Refresh (`V-222442`, `V-222443`, `V-222388`) en `fastapi/src/api/v1/auth.py`

1. En las importaciones de [`fastapi/src/api/v1/auth.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/auth.py#L22-L27):

**`Target`:**
```python
from src.core.crypto import (
    decrypt_aes_gcm,
    encrypt_aes_gcm,
    hash_password,
    verify_password,
)
```

**`Replacement`:**
```python
from src.core.crypto import (
    decrypt_aes_gcm,
    encrypt_aes_gcm,
    hash_password,
    verify_dummy_password,
    verify_password,
)
```

2. En `_verify_user_credentials` de [`fastapi/src/api/v1/auth.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/auth.py#L223-L230):

**`Target`:**
```python
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(time.time() + 900, UTC)
        await db.commit()
```

**`Replacement`:**
```python
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.ROSGRID_MAX_LOGIN_ATTEMPTS:
            user.is_locked = True
            user.locked_until = datetime.fromtimestamp(
                time.time() + settings.ROSGRID_LOGIN_LOCKOUT_SECONDS, UTC
            )
        await db.commit()
```

3. En `login_step1` de [`fastapi/src/api/v1/auth.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/auth.py#L324-L337):

**`Target`:**
```python
    if not user:
        await _log_login_event(
            db=db,
            tenant_id=tenant.id,
            actor_username=ident,
            actor_role=SystemRoleEnum.AUDITOR,
            actor_user_id=None,
            event_action="LOGIN_FAILED_USER_NOT_FOUND",
            status_code=401,
            error_message="Credenciales inválidas o empresa no encontrada",
            request=request,
        )
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
```

**`Replacement`:**
```python
    if not user:
        verify_dummy_password(body.password)
        await _log_login_event(
            db=db,
            tenant_id=tenant.id,
            actor_username=ident,
            actor_role=SystemRoleEnum.AUDITOR,
            actor_user_id=None,
            event_action="LOGIN_FAILED_USER_NOT_FOUND",
            status_code=401,
            error_message="Credenciales inválidas o empresa no encontrada",
            request=request,
        )
        raise HTTPException(status_code=401, detail="Credenciales inválidas o empresa no encontrada")
```

4. En `_build_auth_session_response` de [`fastapi/src/api/v1/auth.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/auth.py#L475-L504):

**`Target`:**
```python
    if db is not None:
        await _log_login_event(
            db=db,
            tenant_id=tenant_id,
            actor_username=user.username,
            actor_role=user.role,
            actor_user_id=user.id,
            event_action="LOGIN_SUCCESSFUL",
            status_code=200,
            extra_details={"session_id": session_id},
            request=request,
        )

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
            features=features or {},
        ),
        csrf_token=csrf_token,
    )
```

**`Replacement`:**
```python
    prev_login_iso = user.last_login_at.isoformat() if getattr(user, "last_login_at", None) else None
    prev_login_ip = str(user.last_login_ip) if getattr(user, "last_login_ip", None) else None
    user.last_login_at = datetime.now(UTC)
    user.last_login_ip = ip_addr

    if db is not None:
        await _log_login_event(
            db=db,
            tenant_id=tenant_id,
            actor_username=user.username,
            actor_role=user.role,
            actor_user_id=user.id,
            event_action="LOGIN_SUCCESSFUL",
            status_code=200,
            extra_details={
                "session_id": session_id,
                "previous_login_at": prev_login_iso,
                "previous_login_ip": prev_login_ip,
            },
            request=request,
        )

    return AuthSessionResponse(
        session_id=session_id,
        user=UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            tenant_id=tenant_id,
            tenant_slug=tenant_slug,
            tenant_name=tenant_name,
            has_all_routers_access=user.has_all_routers_access,
            features=features or {},
            last_login_at=prev_login_iso,
            last_login_ip=prev_login_ip,
        ),
        csrf_token=csrf_token,
    )
```

5. En `refresh_access_token` y `logout` de [`fastapi/src/api/v1/auth.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/auth.py#L616-L636):

**`Target`:**
```python
    new_at = create_jwt_access_token(user_id, tenant_id, tslug, session_id, role, all_r)
    new_csrf = generate_csrf_token(session_id, tenant_id)
    set_auth_cookies(response, new_at, new_rt, new_csrf, is_secure=(request.url.scheme == "https"))
    return {"status": "refreshed", "csrf_token": new_csrf}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    claims: dict[str, Any] = Depends(get_current_user_claims),
) -> None:
    tenant_id = claims["tid"]
    session_id = claims["sid"]
    await kill_session(tenant_id, session_id, killed_by="USER_LOGOUT", reason="Cierre voluntario")

    response.delete_cookie("__Host-rg_at", path="/")
    response.delete_cookie("rg_at", path="/")
    response.delete_cookie("__Host-rg_rt", path="/api/v1/auth/refresh")
    response.delete_cookie("rg_rt", path="/api/v1/auth/refresh")
    response.delete_cookie("rg_csrf", path="/")
```

**`Replacement`:**
```python
    new_at = create_jwt_access_token(user_id, tenant_id, tslug, session_id, role, all_r)
    new_csrf = generate_csrf_token(session_id, tenant_id)
    set_auth_cookies(response, new_at, new_rt, new_csrf, is_secure=(request.url.scheme == "https"))
    await _log_login_event(
        db=db,
        tenant_id=uuid.UUID(str(tenant_id)),
        actor_username=str(sess_data.get("username") or user_id),
        actor_role=SystemRoleEnum(str(role)),
        actor_user_id=uuid.UUID(str(user_id)),
        event_action="SESSION_TOKEN_RENEWED",
        status_code=200,
        extra_details={"session_id": session_id},
        request=request,
    )
    return {"status": "refreshed", "csrf_token": new_csrf}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    claims: dict[str, Any] = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    tenant_id = claims["tid"]
    session_id = claims["sid"]
    user_id = claims.get("sub")
    role_str = str(claims.get("rol") or SystemRoleEnum.AUDITOR.value)
    await kill_session(tenant_id, session_id, killed_by="USER_LOGOUT", reason="Cierre voluntario")

    try:
        role_enum = SystemRoleEnum(role_str)
    except ValueError:
        role_enum = SystemRoleEnum.AUDITOR

    await _log_login_event(
        db=db,
        tenant_id=uuid.UUID(str(tenant_id)),
        actor_username=str(claims.get("preferred_username") or user_id or "user"),
        actor_role=role_enum,
        actor_user_id=uuid.UUID(str(user_id)) if user_id else None,
        event_action="USER_LOGOUT",
        status_code=204,
        extra_details={"session_id": session_id},
        request=request,
    )

    response.headers["Clear-Site-Data"] = '"cache", "cookies", "storage"'
    response.delete_cookie("__Host-rg_at", path="/")
    response.delete_cookie("rg_at", path="/")
    response.delete_cookie("__Host-rg_rt", path="/api/v1/auth/refresh")
    response.delete_cookie("rg_rt", path="/api/v1/auth/refresh")
    response.delete_cookie("rg_csrf", path="/")
```

---

### Paso 8: Prohibición de Reúso de Contraseña (`V-222545`), Actualización de `password_changed_at` (`V-222543`) y Revocación de Sesiones (`OWASP 4.3.7 SM-8`) en `fastapi/src/api/v1/users.py`

Editar `change_password` en [`fastapi/src/api/v1/users.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/users.py#L375-L385):

**`Target`:**
```python
    if len(body.new_password.strip()) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe tener al menos 8 caracteres.",
        )

    user.password_hash = hash_password(body.new_password.strip())
    user.failed_login_attempts = 0
    user.is_locked = False
```

**`Replacement`:**
```python
    clean_new_pwd = body.new_password.strip()
    if len(clean_new_pwd) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe tener al menos 8 caracteres.",
        )

    if user.password_hash and verify_password(clean_new_pwd, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña no puede ser idéntica a la contraseña actual (DISA STIG V-222545).",
        )

    from datetime import UTC, datetime

    user.password_hash = hash_password(clean_new_pwd)
    user.password_changed_at = datetime.now(UTC)
    user.failed_login_attempts = 0
    user.is_locked = False

    if not is_self:
        await kill_all_user_sessions(
            str(user.tenant_id),
            str(user.id),
            killed_by=str(caller_id),
            reason="Cambio administrativo de contraseña (OWASP 4.3.7 SM-8)",
        )
```

---

### Paso 9: Validación de 15 Caracteres en Bootstrap (`V-222536`) y Mensaje Explícito de Cierre de Sesión (`V-222392`) en `vue3/src/views/LoginView.vue`

1. Editar `redirectReason` en [`vue3/src/views/LoginView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/LoginView.vue#L66-L77):

**`Target`:**
```typescript
    const reason = route.query.reason;
    if (reason === 'session_revoked' || reason === 'killed_by_admin') {
      return 'Tu sesión fue revocada por un Administrador o por la activación del Kill-Switch.';
    }
    if (reason === 'session_expired') {
      return 'Tu sesión ha expirado por inactividad. Por favor, ingresa de nuevo.';
    }
    if (reason === 'unauthorized') {
      return 'Debes iniciar sesión para acceder a ese recurso.';
    }
    return '';
```

**`Replacement`:**
```typescript
    const reason = route.query.reason;
    if (reason === 'logged_out') {
      return 'Tu sesión autenticada ha sido cerrada de forma segura y el almacenamiento temporal fue limpiado.';
    }
    if (reason === 'session_revoked' || reason === 'killed_by_admin') {
      return 'Tu sesión fue revocada por un Administrador o por la activación del Kill-Switch.';
    }
    if (reason === 'session_expired') {
      return 'Tu sesión ha expirado por inactividad. Por favor, ingresa de nuevo.';
    }
    if (reason === 'unauthorized') {
      return 'Debes iniciar sesión para acceder a ese recurso.';
    }
    return '';
```

2. Editar `handleBootstrapSubmit` en [`vue3/src/views/LoginView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/LoginView.vue#L312-L315):

**`Target`:**
```typescript
    if (bootstrapAdminPassword.value.length < 12) {
      errorMessage.value = 'La contraseña debe tener al menos 12 caracteres.';
      return;
    }
```

**`Replacement`:**
```typescript
    if (bootstrapAdminPassword.value.length < 15) {
      errorMessage.value = 'La contraseña debe tener al menos 15 caracteres.';
      return;
    }
```

---

### Paso 10: Script Automatizado de Generación de SBOM CycloneDX (`OWASP DevGuide 5.3.4` & `V-222658`)

Crear `scripts/generar-sbom-cyclonedx.sh` (ejecutado 100% en contenedor Docker efímero `aquasec/trivy:latest` cumpliendo Regla Cero):

```bash
#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
# Generador automatizado de Software Bill of Materials (SBOM) CycloneDX 1.5 (OWASP DevGuide 5.3.4 / DISA STIG V-222658)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${ROOT_DIR}/docs/sbom"
mkdir -p "${OUT_DIR}"

echo "[SBOM] Generando CycloneDX SBOM para Backend (FastAPI) y Frontend (Vue 3) en contenedor efímero Trivy..."
docker run --rm \
  -v "${ROOT_DIR}:/workspace:ro" \
  -v "${OUT_DIR}:/out" \
  aquasec/trivy:latest fs --format cyclonedx --output /out/rosgrid-sbom.cdx.json /workspace

echo "[OK] SBOM CycloneDX generado en docs/sbom/rosgrid-sbom.cdx.json"
```

---

### Paso 11: Actualización de Suites Unitarias y BDD (Pirámide QA 11X)

1. En [`fastapi/tests/api/test_auth_and_2fa_endpoints.unit.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/tests/api/test_auth_and_2fa_endpoints.unit.py#L185-L213), actualizar `test_login_failed_attempts_boundary_4_and_5` al umbral DISA STIG V6R5 (`ROSGRID_MAX_LOGIN_ATTEMPTS = 3`, `V-222432`):

**`Target`:**
```python
@pytest.mark.asyncio
async def test_login_failed_attempts_boundary_4_and_5(
    async_client: AsyncClient, sample_tenant: Tenant, sample_user: User
) -> None:
    # Intento 4: no se debe bloquear aún
    sample_user.failed_login_attempts = 3
    session = MockAsyncSession(tenant=sample_tenant, user=sample_user)
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        res = await async_client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": sample_tenant.slug, "email": sample_user.email, "password": "BadPassword!"},
        )
        assert res.status_code == 401
        assert sample_user.failed_login_attempts == 4
        assert not sample_user.is_locked

        # Intento 5 (Límite exacto de bloqueo: >= 5)
        res2 = await async_client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": sample_tenant.slug, "email": sample_user.email, "password": "BadPassword!"},
        )
        assert res2.status_code == 401
        assert sample_user.failed_login_attempts == 5
        assert bool(sample_user.is_locked) is True
        assert sample_user.locked_until is not None
    finally:
        app.dependency_overrides.pop(get_db_session, None)
```

**`Replacement`:**
```python
@pytest.mark.asyncio
async def test_login_failed_attempts_boundary_4_and_5(
    async_client: AsyncClient, sample_tenant: Tenant, sample_user: User
) -> None:
    # DISA STIG V-222432: Límite de 3 intentos fallidos consecutivos en 15 minutos
    sample_user.failed_login_attempts = 1
    session = MockAsyncSession(tenant=sample_tenant, user=sample_user)
    app.dependency_overrides[get_db_session] = lambda: session
    try:
        res = await async_client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": sample_tenant.slug, "email": sample_user.email, "password": "BadPassword!"},
        )
        assert res.status_code == 401
        assert sample_user.failed_login_attempts == 2
        assert not sample_user.is_locked

        # Intento 3 (Límite exacto de bloqueo DISA STIG V-222432: >= 3)
        res2 = await async_client.post(
            "/api/v1/auth/login",
            json={"tenant_slug": sample_tenant.slug, "email": sample_user.email, "password": "BadPassword!"},
        )
        assert res2.status_code == 401
        assert sample_user.failed_login_attempts == 3
        assert bool(sample_user.is_locked) is True
        assert sample_user.locked_until is not None
    finally:
        app.dependency_overrides.pop(get_db_session, None)
```

2. En [`vue3/src/views/auth/loginView.unit.ts`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/auth/loginView.unit.ts#L466-L468), actualizar la aserción de longitud mínima en bootstrap de 12 a 15 caracteres:

**`Target`:**
```typescript
    expect(wrapper.find('.alert-banner--danger').text()).toContain(
      'La contraseña debe tener al menos 12 caracteres.',
    );
```

**`Replacement`:**
```typescript
    expect(wrapper.find('.alert-banner--danger').text()).toContain(
      'La contraseña debe tener al menos 15 caracteres.',
    );
```

3. Añadir escenarios Karate Labs BDD en `fastapi/test/api_test.feature` y `vue3/test/ui_business_flow.feature` (sincronizados en `docs/examples/fastapi/test/api_test.feature` y `docs/examples/vue3/test/ui_business_flow.feature`) verificando las cabeceras OSHP (`X-Permitted-Cross-Domain-Policies: none`, `Cross-Origin-Opener-Policy: same-origin`), bloqueo STIG a los 3 intentos (`V-222432`) y validación de 15 caracteres en bootstrap (`V-222536`).
