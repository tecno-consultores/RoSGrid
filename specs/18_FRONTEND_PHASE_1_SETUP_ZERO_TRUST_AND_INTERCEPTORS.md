# 18 — FASE 1 FRONTEND: ARQUITECTURA VUE 3, FUSIÓN ZERO-TRUST (.npmrc), INTERCEPTORES DE SEGURIDAD Y PWA MÓVIL/TABLET (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento guía paso a paso la construcción de la **Fase 1 del Frontend (vue3/)**. Antes de generar cualquier archivo .ts o .vue, debes ejecutar el **Paso 0 (Graphify MCP)** y realizar la **Fusión Quirúrgica No Destructiva** de package.json.example, npmrc.example, vitest.config.ts.example, stryker.conf.json.example, playwright.config.ts.example, lighthouserc.js.example, Makefile.example y gitignore.example. Todo el código generado DEBE mantener Complejidad Cognitiva baja en eslint-plugin-sonarjs y alcanzar una cobertura unitaria \>= 95% en lines, functions, branches y statements.




## **1. Fusión Quirúrgica de vue3/package.json y Política Zero-Trust (vue3/.npmrc)**

### **1.1 Configuración de vue3/.npmrc**

Para mitigar ataques de cadena de suministro (*Supply Chain Attacks*), el archivo vue3/.npmrc mantiene ignore-scripts=true y engine-strict=true:


engine-strict=true


ignore-scripts=true


fetch-retries=3


strict-peer-dependencies=false

### **1.2 Especificación de vue3/package.json Fusionado**

Se fusionan las librerías operativas de **RoSGrid** (pinia, vue-router, leaflet para OpenStreetMap, qrcode para enrolamiento 2FA TOTP) con todas las herramientas de auditoría del Estándar 11X y la lista blanca pnpm.onlyBuiltDependencies para permitir los binarios legítimos de compilación y pruebas:


\{


  "name": "rosgrid-frontend",


  "version": "1.0.0",


  "license": "GPL-3.0-only",


  "description": "Consola Web Centralizada Multi-Tenant para Flotas MikroTik RouterOS v7+ (Vue 3 + TS + Pinia)",


  "scripts": \{


    "dev": "vite",


    "build": "vue-tsc --noEmit && vite build",


    "type-check": "vue-tsc --noEmit",


    "format": "prettier --write \\"src/\*\*/\*.\{js,ts,vue\}\\" \\"tests/\*\*/\*.\{js,ts\}\\" \\"e2e/\*\*/\*.\{js,ts\}\\"",


    "format:check": "prettier --check \\"src/\*\*/\*.\{js,ts,vue\}\\" \\"tests/\*\*/\*.\{js,ts\}\\" \\"e2e/\*\*/\*.\{js,ts\}\\"",


    "lint": "eslint . --ext .vue,.js,.ts",


    "test:unit": "vitest run",


    "test:coverage": "vitest run --coverage",


    "mutate": "stryker run",


    "audit:deps": "npm audit --audit-level=high",


    "test:e2e": "playwright test",


    "test:perf": "lhci autorun"


  \},


  "dependencies": \{


    "leaflet": "^1.9.4",


    "pinia": "^2.2.2",


    "qrcode": "^1.5.4",


    "vue": "^3.4.38",


    "vue-router": "^4.4.3"


  \},


  "devDependencies": \{


    "@axe-core/playwright": "^4.9.1",


    "@lhci/cli": "^0.13.0",


    "@playwright/test": "^1.43.0",


    "@stryker-mutator/core": "^8.2.6",


    "@stryker-mutator/vitest-runner": "^8.2.6",


    "@types/leaflet": "^1.9.12",


    "@types/qrcode": "^1.5.5",


    "@typescript-eslint/eslint-plugin": "^7.1.1",


    "@typescript-eslint/parser": "^7.1.1",


    "@vitejs/plugin-vue": "^5.1.2",


    "@vitest/coverage-v8": "^1.3.1",


    "@vue/test-utils": "^2.4.6",


    "eslint": "^8.56.0",


    "eslint-config-prettier": "^9.1.0",


    "eslint-plugin-security": "^3.0.0",


    "eslint-plugin-sonarjs": "^0.24.0",


    "eslint-plugin-vue": "^9.21.1",


    "jsdom": "^24.0.0",


    "prettier": "^3.2.5",


    "typescript": "^5.3.0",


    "vite": "^5.1.0",


    "vitest": "^1.3.0",


    "vue-eslint-parser": "^9.4.2",


    "vue-tsc": "^1.8.27"


  \},


  "pnpm": \{


    "onlyBuiltDependencies": \[


      "esbuild",


      "playwright",


      "@playwright/test"


    \]


  \}


\}




## **2. Arquitectura del Cliente HTTP Seguro e Interceptores (vue3/src/api/httpClient.ts)**

Queda **prohibido** guardar tokens JWT en localStorage o sessionStorage. El cliente HTTP de RoSGrid utiliza fetch nativo encapsulado con credentials: "include" para que el navegador gestione las cookies HttpOnly (\_\_Host-rg\_at y \_\_Host-rg\_rt), aplicando 4 interceptores deterministas (CC \<= 4 por función):

### **2.1 Interceptor 1: Lectura y Adjunto de X-CSRF-Token**

- Antes de toda petición con método POST, PUT, PATCH o DELETE, el helper readCsrfCookie() extrae el valor de la cookie rg\_csrf (o el último csrf\_token recibido en memoria del useAuthStore) y lo inyecta en la cabecera X-CSRF-Token.

### **2.2 Interceptor 2: Generador Criptográfico de Idempotency-Key (UUIDv7)**

- En toda petición mutable (POST, PUT, PATCH, DELETE), si el llamador no proporcionó una llave explícita de reintento, el cliente genera automáticamente un UUIDv7 ordenable por tiempo (generateUuidV7() usando crypto.getRandomValues) y lo inyecta en la cabecera Idempotency-Key.

- Si ocurre un error de red transitorio (TypeError: Failed to fetch o HTTP 502/503/504) y el usuario pulsa "Reintentar", el cliente **reutiliza exactamente la misma Idempotency-Key** para garantizar que FastAPI/Redis jamás aplique dos veces el cambio en el MikroTik.

### **2.3 Interceptor 3: Rotación Transparente de Refresh Token (401 -\> /api/v1/auth/refresh)**

- Si una petición recibe HTTP 401 Unauthorized y la ruta no es /api/v1/auth/login, /api/v1/auth/2fa/verify ni /api/v1/auth/refresh:

  1. Utiliza una única promesa compartida (refreshPromiseSingleton) para evitar condiciones de carrera si hay 5 peticiones en paralelo.

  2. Invoca POST /api/v1/auth/refresh con credentials: "include".

  3. Si devuelve 200 OK, actualiza el csrf\_token en useAuthStore y reintenta transparentemente la petición original.

  4. Si devuelve 401 Unauthorized, significa que la sesión expiró o fue revocada por el **Kill-Switch**; limpia la memoria de todos los stores de Pinia y redirige a /login?reason=session\_expired.

### **2.4 Interceptor 4: Manejo de Respuesta HTTP 202 Accepted (*Maker-Checker*)**

- Cuando cualquier operación sobre un MikroTik devuelve HTTP 202 Accepted con status === "INTERCEPTED\_FOR\_APPROVAL", el interceptor dispara automáticamente un toast informativo global en la interfaz:

  - *"Operación crítica enviada a aprobación (Maker-Checker). ID de solicitud: \#..."* y actualiza el estado del formulario sin arrojar una excepción no controlada.




## **3. Arquitectura de Stores en Pinia (vue3/src/stores/)**

Cada store DEBE tener su archivo de pruebas unitarias correspondiente (\*.unit.ts) cubriendo \>= 95% de sus ramas:


2. useAuthStore.ts — Estado del usuario autenticado, tenant\_slug, rol actual (de los 11 roles), csrf\_token, helpers reactivos hasCapability(actionCode) y método forceKillSwitchLogout(reason).

3. useThemeAndLayoutStore.ts — Control de temas (dark, light, noc-high-contrast), estado del cajón lateral en móviles/tabletas (isMobileDrawerOpen), densidad de tablas (compact, comfortable) y estado del buscador global Ctrl + K.

4. useInventoryStore.ts — Lista de MikroTiks del Tenant, filtros por rol de red/estado/etiqueta, coordenadas para el mapa OpenStreetMap y estado de ventanas de mantenimiento.

5. useWebFigStore.ts — Estado activo del MikroTik seleccionado, caché efímero de pestañas abiertas de Capa 1 / Capa 2 y estado del indicador **Safe Mode (Dead Man's Switch)**.

6. useLiveTelemetryStore.ts — **Almacenamiento 100% en RAM (RingBuffer)** de los puntos recibidos por WebSocket para las gráficas estilo WinBox. Incluye el hook de limpieza automática resetChartsBuffer() al salir del router.

7. useNocEventsStore.ts — Conexión al WebSocket global /ws/v1/tenant/events, cola de alertas sonoras/visuales del NOC, contador en vivo de solicitudes *Maker-Checker* pendientes y escucha activa del evento SESSION\_KILLED.




## **4. Vue Router y Guards de Autorización RBAC (vue3/src/router/index.ts)**

1. Toda ruta declara en su meta:


meta: \{


  requiresAuth: true,


  allowedRoles: \['SUPERADMIN\_GLOBAL', 'TENANT\_ADMIN', ...\],


  title: 'Inventario de Equipos MikroTik — RoSGrid'


\}


2. El guard router.beforeEach:

   - Actualiza document.title en cada navegación (obligatorio para accesibilidad WCAG 2.1 AA y SEO en Lighthouse).

   - Si requiresAuth && !authStore.isAuthenticated, redirige a /login.

   - Si el usuario tiene rol NOC\_MONITOR, lo encauza automáticamente a la vista /noc-wallboard bloqueando rutas de edición.

   - Si el usuario tiene rol AUDITOR, habilita las vistas de auditoría inmutable (/audit-logs), inventario de lectura y comparador Diff (.rsc), bloqueando formularios mutables.




## **5. Soporte Adaptativo para Navegadores Móviles, Tabletas y Escritorio (PWA Ready)**

Para cumplir tu sugerencia de uso fluido tanto en PC como en tabletas y teléfonos móviles:


- **Breakpoints Responsivos:**

  - \< 768px (Móvil — ideal para *Técnico de Campo* o guardia): Navegación inferior rápida + menú lateral tipo Drawer táctil; las tablas densas activan scroll horizontal suave con primera columna fija (sticky) y botón para expandir fila en tarjeta vertical.

  - 768px - 1199px (Tableta): Menú lateral colapsado a iconos con expansión al toque y cuadrícula de 2 columnas en dashboards.

  - \>= 1200px (Escritorio / NOC): Consola completa de alta densidad tipo WinBox/WebFig con panel lateral fijo y múltiples paneles visibles.

- **Web App Manifest (public/manifest.webmanifest):** Configurado con iconos, display: "standalone", theme\_color: "\#0b132b" y background\_color: "\#0b132b" para superar las auditorías de Best Practices y PWA de **Lighthouse CI**.
