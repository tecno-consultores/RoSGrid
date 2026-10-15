# 🛡️ Política de Seguridad y Arquitectura de Defensa (RoSGrid)

**Proyecto:** RoSGrid — Consola Centralizada Multi-Tenant para Flotas MikroTik RouterOS v7+  
**Licencia:** GPL-3.0-only  
**Estándar de Certificación:** QA 11X DevSecOps

---

## 1. Versiones Soportadas

Actualmente reciben parches de seguridad activos las siguientes ramas e imágenes oficiales en Docker Hub (`sinfallas/rosgrid-backend` y `sinfallas/rosgrid-frontend`):

| Versión | Estado de Soporte | Requisitos de Infraestructura |
| :--- | :--- | :--- |
| **1.0.x (`latest`)** | ✅ Soporte Activo | RouterOS v7.1+, PostgreSQL 17, Redis 7 |
| **< 1.0.0** | ❌ No Soportado | N/A |

---

## 2. Reporte Responsable de Vulnerabilidades

Si descubres una vulnerabilidad de seguridad en el motor criptográfico, el aislamiento Multi-Tenant (RLS), el interceptor RBAC/Maker-Checker o el conector de RouterOS v7:

1. **NO abras un Issue público en GitHub/GitLab** con el exploit o vector de ataque.
2. Envía un reporte detallado por correo electrónico a: **Sinfallas (`sinfallas@yahoo.com`)** con el asunto `[SECURITY-ROSGRID] Descripción breve del hallazgo`.
3. Incluye los pasos de reproducción, el componente afectado (`fastapi/` o `vue3/`) y el impacto potencial.
4. Recibirás acuse de recibo en un máximo de **48 horas** y coordinaremos la publicación del parche antes de la divulgación pública.

---

## 3. Pilares de Seguridad por Diseño en RoSGrid

RoSGrid administra infraestructura crítica de telecomunicaciones e ISP (routers de borde BGP, BRAS PPPoE y firewalls). Por ello, implementa **7 capas de defensa en profundidad**:

### 3.1 Aislamiento Multi-Tenant a Nivel de Motor (`FORCE ROW LEVEL SECURITY`)
- Todas las tablas operativas en PostgreSQL 17 aplican políticas `ENABLE` y `FORCE ROW LEVEL SECURITY (RLS)`.
- Cada transacción inyecta `SET LOCAL app.current_tenant_id = '<uuid>'`, impidiendo matemáticamente fugas de datos cruzadas entre empresas (Tenants) incluso ante errores en consultas de la capa de aplicación.

### 3.2 Autenticación *Split-Credential*, 2FA TOTP y Cookies `__Host-`
- **Contraseñas de Usuario:** Hash con `Argon2id` de alta dureza de memoria.
- **Segundo Factor Obligatorio (2FA):** TOTP conforme al RFC 6238 para todos los operadores humanos.
- **Cero Tokens en `localStorage`:** Los tokens de sesión viajan exclusivamente en cookies `__Host-rg_at` y `__Host-rg_rt` con banderas `HttpOnly; Secure; SameSite=Strict`, acompañadas de validación `X-CSRF-Token` firmada con `HMAC-SHA256`.
- **Detección de Robo de Sesión (*Reuse Detection*) y *Kill-Switch*:** Redis 7 invalida automáticamente toda la familia de Refresh Tokens si detecta el reúso de un token rotado y permite la expulsión instantánea en vivo (`SESSION_KILLED` con cierre de WebSockets código `4401`).

### 3.3 Bóveda Criptográfica `AES-256-GCM` y *Step-Up Auth* (30s)
- Las credenciales de la REST API de cada router MikroTik se cifran con `AES-256-GCM` vinculando criptográficamente el `tenant_id|router_id` como *Additional Authenticated Data (AAD)*.
- **Rotación Automática Transaccional:** El worker de bóveda rota las contraseñas API por llaves aleatorias de 32 caracteres manteniendo `previous_password` para recuperación ante cortes de red.
- **Revelación Efímera (30 Segundos):** Solo los roles `SUPERADMIN_GLOBAL` y `TENANT_ADMIN` pueden consultar una clave tras superar un desafío **Step-Up 2FA TOTP en vivo**. El Frontend purga la clave de la memoria RAM automáticamente tras 30 segundos.

### 3.4 Pinning TLS *Trust On First Use* (TOFU) sobre `/rest/*`
- RoSGrid se comunica exclusivamente mediante HTTPS (`/ip/service/www-ssl`) contra la REST API de RouterOS v7.1+.
- En el primer contacto verificado se fija la huella `SHA-256` del certificado X.509 del MikroTik (`TRUSTED_PINNED`). Si la huella cambia sin autorización previa (`FINGERPRINT_MISMATCH`), RoSGrid aborta la conexión y dispara una alerta crítica de posible ataque *Man-in-the-Middle (MitM)*.

### 3.5 *Safe Mode (Dead Man's Switch)* y Protección Anti-Suicidio
- Toda mutación delicada inyecta previamente una tarea temporal `rosgrid_safemode_*` en `/rest/system/scheduler` a 60 segundos antes de aplicar el cambio. Si el cambio corta la conectividad de gestión, el propio MikroTik revierte la operación automáticamente.
- El sistema bloquea cualquier intento de deshabilitar o alterar el servicio `www-ssl` desde Capa 1 o Capa 2 (`FORBIDDEN_L2_PATHS`).

### 3.6 Segregación de Funciones (*Maker-Checker*) y Cadena Forense WORM
- Los cambios en las 7 categorías críticas realizados por roles intermedios se retienen con estado `202 Accepted` (`AWAITING_APPROVAL`). Ningún usuario puede aprobar su propia solicitud (`maker_user_id != checker_user_id`).
- La tabla `audit_logs` cuenta con un trigger en PostgreSQL (`trg_immutable_audit_logs`) que prohíbe `UPDATE`, `DELETE` y `TRUNCATE`, encadenando cada registro con `SHA-256` (`prev_record_hash -> record_sha256_hash`) y sanitizando secretos (`[REDACTED]`).

### 3.7 Exclusión Deliberada de Terminal CLI / SSH Libre
- Por diseño de seguridad, RoSGrid **no incluye ni aceptará** terminales interactivas SSH/Telnet ni consolas CLI libres que permitan a un operador evadir el modelo *Split-Credential*, el interceptor *Maker-Checker*, el *Safe Mode* o la auditoría estructurada `before_state` / `after_state`.

---

## 4. Barreras Automatizadas DevSecOps

Antes de cada commit, push o publicación de imagen en Docker Hub (`./build.sh`), el código supera:
- **Detección de Secretos:** `gitleaks` vía `lefthook.yml`.
- **SAST Backend & Frontend:** `Bandit` (Python) y `eslint-plugin-security` (Vue 3 / TypeScript), más `.npmrc` con `ignore-scripts=true`.
- **Auditoría IaC y Contenedores:** `Trivy` (`./auditar-infra.sh`) exigiendo `0` vulnerabilidades `HIGH` o `CRITICAL` y ejecución con usuarios sin privilegios (`non-root`).
- **DAST en Vivo:** Escaneo dinámico con **OWASP ZAP Baseline** contra el contenedor compilado.
