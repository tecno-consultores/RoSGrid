# 06 — SEGURIDAD DE COMUNICACIÓN: SPLIT-CREDENTIAL, COOKIES HTTPONLY, CSRF HMAC, 2FA TOTP Y STEP-UP AUTH (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica la arquitectura criptográfica y de transporte entre el Frontend (**Vue 3**) y el Backend (**FastAPI**). Queda **TERMINANTEMENTE PROHIBIDO** almacenar tokens JWT o credenciales en localStorage, sessionStorage o variables globales accesibles por JavaScript si ocurre un ataque XSS. Toda función implementada bajo este documento DEBE mantener una Complejidad Ciclomática Grado A (Radon CC \<= 5) y pasar el escaneo dinámico de **OWASP ZAP Baseline** con cero alertas medias/altas.




## **1. Arquitectura de Autenticación *Split-Credential* + Cookies \_\_Host-**

Para lograr el mecanismo más seguro actualmente en producción entre **FastAPI** y **Vue 3 (SPA)**, RoSGrid implementa aislamiento total de credenciales en cookies HttpOnly combinadas con validación antifalsificación vinculada criptográficamente a la sesión (HMAC-SHA256).

### **1.1 Las 3 Cookies del Sistema**

| **Nombre de Cookie** | **Atributos Obligatorios** | **Contenido** | **Duración (Max-Age)** | **Acceso desde JS (document.cookie)** |
| - | - | - | - | - |
| \_\_Host-rg\_at *(en HTTPS)* o rg\_at *(solo en entorno QA HTTP interno)* | HttpOnly; Secure; SameSite=Strict; Path=/ | **Access Token (JWT firmado con HS256 o EdDSA)** con claims mínimos (sub, tid, sid, rol, iat, exp) | 600 segundos (10 minutos) | **PROHIBIDO (HttpOnly)** |
| \_\_Host-rg\_rt *(en HTTPS)* o rg\_rt *(en QA HTTP)* | HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth/refresh | **Refresh Token Opaco** (32 bytes aleatorios codificados en urlsafe\_b64) vinculado a una familia en Redis | 28800 segundos (8 horas) | **PROHIBIDO (HttpOnly + Path restringido)** |
| rg\_csrf | Secure; SameSite=Strict; Path=/ *(Sin HttpOnly)* | **Token CSRF firmado con HMAC-SHA256** (nonce.timestamp.signature atado al session\_id) | 28800 segundos (8 horas) | **Lectura permitida solo por el mismo origen** para inyectar cabecera X-CSRF-Token |

### **1.2 Estructura Exacta del Payload JWT (\_\_Host-rg\_at)**

\{


  "sub": "01928a10-4b22-7c00-8123-9876543210ab",


  "tid": "01928000-1111-7000-8000-000000000001",


  "tslug": "isp-norte",


  "sid": "01928b4c-9988-7d11-9000-112233445566",


  "rol": "SUPPORT\_L3",


  "all\_r": false,


  "iat": 1792000000,


  "exp": 1792000600


\}


- **sub**: user\_id (UUID).

- **tid**: tenant\_id (UUID) — usado para inyectar app.current\_tenant\_id en PostgreSQL RLS y prefijos de Redis.

- **sid**: session\_id (UUID) — verificado en cada petición contra EXISTS rg:\{tid\}:sess:\{sid\} en Redis para garantizar que el **Kill-Switch** tenga efecto instantáneo (0 segundos de retraso) sin esperar a que expire el JWT de 10 minutos.

- **rol**: Rol del usuario dentro del catálogo de los 11 roles.




## **2. Rotación Estricta de Refresh Tokens con Detección de Robo (*Reuse Detection*) y Período de Gracia (*Leeway*)**

Cada vez que el Access Token (rg_at) vence (cada 10 minutos), el interceptor de Vue 3 invoca silenciosamente POST /api/v1/auth/refresh:

1. El navegador envía automáticamente la cookie rg_rt (gracias a Path=/api/v1/auth/refresh).
2. FastAPI calcula el SHA-256 del token recibido y busca la familia en Redis (rg:{tid}:rt_family:{family_id}).
3. **Caso Normal (Hash coincide con current_rt_hash):**
   - Se genera un nuevo Refresh Token opaco, se actualiza current_rt_hash en Redis guardando el anterior en used_rt_hashes y registrando su marca de tiempo en used_rt_hashes_timed, y se emiten nuevas cookies rg_at, rg_rt y rg_csrf.
4. **Manejo de Concurrencia Multi-Pestaña (*Grace Period Leeway*):**
   - Para prevenir falsos positivos de robo cuando múltiples pestañas del navegador o peticiones simultáneas intentan refrescar la sesión al mismo tiempo, el sistema aplica una ventana de tolerancia configurable (`ROSGRID_REFRESH_TOKEN_GRACE_PERIOD_SECONDS`, por defecto 5 segundos).
   - Si el hash recibido figura en `used_rt_hashes_timed` y el tiempo transcurrido desde la rotación es menor o igual al período de gracia, FastAPI devuelve el token vigente recién emitido (`last_issued_rt`) con status 200 sin invalidar la sesión.
5. **Caso de Robo Confirmado (*Reuse Attack* fuera del período de gracia):**
   - Si el token recibido ya figura en used_rt_hashes y ha expirado la ventana de gracia, indica que el token fue clonado por un tercero no sincronizado.
   - **Acción Inmediata de Contención:** FastAPI ejecuta el protocolo **Kill-Switch** sobre toda la sesión (DEL rg:{tid}:sess:{sid} y DEL rg:{tid}:rt_family:{family_id}), registra una alerta crítica en audit_logs (REFRESH_TOKEN_REUSE_DETECTED) y responde HTTP 401 Unauthorized borrando las cookies.


## **3. Protección Criptográfica Anti-CSRF (X-CSRF-Token)**

Para proteger todas las rutas mutables (POST, PUT, PATCH, DELETE) contra ataques Cross-Site Request Forgery:

1. **Generación del Token:**
   - csrf_payload = f"{session_id}:{tenant_id}:{random_nonce_16b}:{issued_epoch}"
   - signature = hmac.new(CSRF_HMAC_SECRET, csrf_payload.encode(), hashlib.sha256).hexdigest()
   - csrf_token = f"{random_nonce_16b}.{issued_epoch}.{signature}"

2. **Validación Autónoma en Middleware FastAPI (fastapi/src/core/csrf.py):**
   - El middleware `CSRFProtectionMiddleware` opera antes del enrutador de FastAPI y desacopla la extracción del JWT del ciclo de inyección de dependencias `request.state`.
   - **Ámbito Exclusivo de Navegador:** Se inspecciona la presencia de cookies de sesión (`__Host-rg_at` o `rg_at`). Si la petición no utiliza cookies del navegador y en su lugar se autentica puramente mediante cabecera `Authorization: Bearer <JWT>` (como agentes de IA, scripts de automatización o el endpoint MCP `/api/v1/mcp`), la validación CSRF se omite de forma segura (conforme a OWASP CSRF Prevention Cheat Sheet, las peticiones sin credenciales ambientales en cookies son inmunes a CSRF).
   - Para toda petición mutable originada desde navegador (con cookie de sesión), el middleware extrae:
     - El valor de la cabecera `X-CSRF-Token` enviada por el interceptor Axios/Fetch de Vue 3.
     - El `session_id` y `tenant_id` decodificados del JWT presente en la cookie de sesión.
   - Recalcula el HMAC-SHA256 en tiempo constante (`hmac.compare_digest`).
   - Si falta la cabecera o la firma no coincide con la sesión activa del usuario, rechaza la petición con HTTP 403 Forbidden (`{"detail": "Fallo de validación criptográfica CSRF"}`) y escribe en audit_logs.





## **4. Flujo de Login Multi-Tenant en 2 Pasos + 2FA TOTP Obligatorio**

### **Paso 1: Credenciales Primarias (POST /api/v1/auth/login)**

- **Entrada:** tenant\_slug (ej. "isp-norte"), email (o username) y password.

- **Proceso:**

  1. Busca el Tenant activo por slug.

  2. Busca el usuario dentro de ese tenant\_id (activando RLS).

  3. Verifica bloqueo temporal (locked\_until \> NOW()). Si falla la contraseña Argon2id, incrementa failed\_login\_attempts; al 5.º intento fallido bloquea la cuenta por 15 minutos y registra en audit\_logs.

  4. Si la contraseña Argon2id es válida:

     - Crea un desafío efímero en Redis: rg:\{tenant\_id\}:preauth:\{challenge\_id\} con TTL de **180 segundos**.

     - Si el usuario aún no tiene totp\_enabled = True y la política lo exige (require\_2fa\_all\_users = True o roles críticos), el desafío se marca con status = "ENROLL\_2FA\_REQUIRED" e incluye el aprovisionamiento QR (otpauth://totp/RoSGrid:\{tenant\_slug\}:\{email\}?secret=...&issuer=RoSGrid).

     - Si ya tiene totp\_enabled = True, devuelve \{ "challenge\_id": "...", "next\_step": "VERIFY\_2FA\_TOTP" \}.

### **Paso 2: Verificación 2FA TOTP (POST /api/v1/auth/2fa/verify)**

- **Entrada:** challenge\_id y totp\_code (6 dígitos numéricos o código de recuperación de emergencia de 10 caracteres).

- **Proceso:**

  1. Recupera rg:\{tenant\_id\}:preauth:\{challenge\_id\} de Redis (y consume un intento; máximo 3 intentos por challenge\_id).

  2. Desencripta totp\_secret\_ciphertext de la tabla users usando AES-256-GCM con AAD = f"\{tenant\_id\}:\{user\_id\}".

  3. Valida el código TOTP con ventana de tolerancia de ±1 paso de 30 segundos (pyotp.TOTP(secret).verify(code, valid\_window=1)) y previene replay del mismo código guardando rg:\{tenant\_id\}:used\_totp:\{user\_id\}:\{code\} en Redis por 90 segundos.

  4. Al ser válido: elimina el preauth, registra la sesión activa en Redis (rg:\{tenant\_id\}:sess:\{session\_id\}), escribe el evento USER\_LOGIN\_SUCCESS en audit\_logs y establece las cookies rg\_at, rg\_rt y rg\_csrf.




## **5. Protocolo *Step-Up Authentication* para la Bóveda de Claves (30 Segundos)**

Por requerimiento estricto del proyecto, **solo los 2 perfiles más altos (SUPERADMIN\_GLOBAL y TENANT\_ADMIN) pueden consultar las contraseñas actuales o rotadas de la REST API de los MikroTiks**.


2. El administrador entra a la ficha del router y pulsa **"Revelar Clave de Bóveda"**.

3. Vue 3 abre un modal solicitando ingresar el código **2FA TOTP actual** y el motivo de consulta.

4. Vue 3 envía POST /api/v1/inventory/routers/\{router\_id\}/vault/reveal con \{ "totp\_code": "123456", "reason": "Diagnóstico de emergencia por consola directa" \}.

5. FastAPI:

   - Verifica que el rol sea exclusivamente SUPERADMIN\_GLOBAL o TENANT\_ADMIN (cualquier otro rol recibe 403 Forbidden).

   - Valida el código TOTP en vivo contra el secreto del administrador.

   - Registra obligatoriamente en audit\_logs el evento CREDENTIAL\_REVEALED con nivel crítico ANTES de entregar el dato.

   - Desencripta en memoria RAM current\_password y previous\_password usando AES-256-GCM (AAD = f"\{tenant\_id\}:\{router\_id\}").

   - Devuelve el JSON con las cabeceras HTTP Cache-Control: no-store, no-cache, must-revalidate, max-age=0 y Pragma: no-cache.

2. En Vue 3, la clave se mantiene visible en un componente reactivo aislado durante exactamente **30 segundos** (con barra de cuenta regresiva visual) y al llegar a 0 (o al desmontar el componente onUnmounted) se sobrescribe la variable en memoria con null.




## **6. Cabeceras de Seguridad HTTP en FastAPI (Cumplimiento DAST OWASP ZAP)**

Para que el contenedor zap (zap-baseline.py -t http://api:8000) apruebe la API sin alertas de seguridad, FastAPI DEBE incluir un middleware global de cabeceras seguras (fastapi/src/core/security\_headers.py) que inyecte en todas las respuestas:


- X-Content-Type-Options: nosniff

- X-Frame-Options: DENY

- Referrer-Policy: strict-origin-when-cross-origin

- Permissions-Policy: geolocation=(), camera=(), microphone=()

- Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; sandbox *(para respuestas JSON de la API)*

- Cache-Control: no-store *(por defecto en todas las rutas /api/v1/\*)*

- Ocultación de la cabecera Server: uvicorn (reemplazada o suprimida).
