# 19 — SISTEMA DE DISEÑO FRONTEND, ALTA DENSIDAD TÉCNICA, ACCESIBILIDAD WCAG 2.1 AA (@axe-core) Y RENDIMIENTO LIGHTHOUSE CI (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento define las reglas visuales, de experiencia de usuario (UI/UX), accesibilidad (@axe-core/playwright = 0 violaciones) y rendimiento (Lighthouse CI \>= 90 en Performance/SEO/Best-Practices y \>= 95 en Accessibility) para vue3/. Cada componente que construyas DEBE respetar estrictamente estas directrices para que make qa-perf y make qa-e2e aprueben en el primer intento.




## **1. Filosofía Visual: Consola de Alta Densidad Técnica (Estilo WinBox / WebFig Moderno)**

Los ingenieros de red y operadores NOC necesitan visualizar decenas de interfaces, rutas BGP o reglas de Firewall simultáneamente sin desperdiciar espacio en márgenes excesivos.

### **1.1 Los 3 Temas Oficiales (Variables CSS Nativas sin Runtime Cost)**

El archivo vue3/src/assets/themes.css define 3 paletas que cumplen matemáticamente con el ratio de contraste **WCAG 2.1 AA (\>= 4.5:1 para texto normal y \>= 3.0:1 para componentes UI)** para no fallar jamás la regla color-contrast de @axe-core/playwright:


1. **Tema Oscuro Técnico (data-theme="dark" — Predeterminado):**

   - Fondo base: \#0B132B | Superficie tarjetas/tablas: \#1C2541 | Bordes: \#3A506B.

   - Acento primario (Cian Técnico): \#5BC0BE (sobre fondo oscuro ratio 8.4:1).

   - Texto principal: \#F8FAFC | Texto secundario: \#CBD5E1 (prohibido usar grises apagados con ratio \< 4.5:1).

   - Estados semánticos: Online \#22C55E, Alerta/Mantenimiento \#F59E0B, Offline/Crítico \#EF4444, Pinning/Info \#38BDF8.

2. **Tema Claro de Oficina (data-theme="light"):**

   - Fondo base: \#F8FAFC | Superficie: \#FFFFFF | Bordes: \#CBD5E1.

   - Acento primario: \#0F4C81 | Texto principal: \#0F172A | Texto secundario: \#334155.

3. **Tema Wallboard NOC Alto Contraste (data-theme="noc-high-contrast"):**

   - Fondo negro puro \#000000 para pantallas OLED/LED de centros de monitoreo 24/7, tipografía escalada 1.15rem y bordes de alto contraste para lectura a 5 metros de distancia.

### **1.2 Tipografía del Sistema (Cero Fuentes Externas Bloqueantes)**

Para lograr un **Score \>= 95 en Lighthouse Performance** y evitar *Cumulative Layout Shift (CLS)* o bloqueos de red en contenedores aislados:


- Queda **TERMINANTEMENTE PROHIBIDO** cargar fuentes desde servidores de fuentes externos o CDNs en internet.

- Se utiliza pila de fuentes nativas del sistema:

  - UI General: system-ui, -apple-system, 'Segoe UI', Roboto, Ubuntu, sans-serif.

  - Datos Técnicos (IPs, MACs, contadores, reglas Firewall, .rsc Diff): 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, SFMono-Regular, monospace con font-variant-numeric: tabular-nums (para que los números en las tablas y gráficas en vivo no bailen horizontalmente al actualizarse cada 2 segundos).




## **2. Componentes Base Reutilizables y Accesibles (vue3/src/components/common/)**

Para evitar duplicación de código y mantener complejidad cognitiva baja en SonarJS, AntiGravity DEBE construir estos 5 componentes base:

### **2.1 RgDataTable.vue (Tabla Técnica de Alta Densidad con Drag & Drop Accesible)**

- Soporta filtrado instantáneo por texto y por columna, ordenamiento, selección múltiple con casillas (checkbox) para acciones masivas y paginación virtual.

- **Soporte Drag & Drop Dual (Ratón + Teclado + Táctil):**

  - Utilizado en Firewall (Filter, NAT, Mangle, RAW) y Simple Queues.

  - Además de arrastrar con el ratón o el dedo en tabletas, cada fila ordenable incluye botones accesibles por teclado (Alt + Flecha Arriba / Alt + Flecha Abajo con aria-label="Mover regla \*1C hacia arriba") para cumplir al 100% con **WCAG 2.1.1 (Keyboard Accessible)**.

### **2.2 RgCommandPalette.vue (Buscador Global Rápido Ctrl + K / Cmd + K)**

- Modal accesible (role="dialog", aria-modal="true", aria-labelledby="cmd-palette-title") invocable desde cualquier pantalla con Ctrl + K o botón en la barra superior.

- Permite buscar en milisegundos:

  - Cualquier MikroTik por display\_name, serial\_number, ros\_identity, ubicación física o IP.

  - Saltar directamente a un submenú de Capa 1 o Capa 2 de un router (ej. escribir "RB4011 bgp" o "CCR2004 firewall" y navegar directamente a esa vista).

### **2.3 RgSafeModeBanner.vue (Indicador Visual del *Dead Man's Switch*)**

- Barra superior fija con role="status" y aria-live="polite" que se activa cuando una operación con **Safe Mode** está verificando la supervivencia del MikroTik, mostrando la cuenta regresiva de confirmación y confirmación verde cuando el scheduler temporal fue limpiado con éxito.

### **2.4 RgStepUp2FAModal.vue (Modal de Confirmación TOTP para Acciones Sensibles)**

- Reutilizado para revelar claves en la Bóveda (con temporizador de autodestrucción de 30 segundos), autorizar Re-Pin SSL TOFU o reiniciar el 2FA de un técnico.

### **2.5 RgResponsiveShell.vue (Layout Maestro Escritorio / Tablet / Móvil)**

- Incluye hitos semánticos HTML5 obligatorios para @axe-core: \<header\>, \<nav aria-label="Navegación principal"\>, \<main id="main-content"\> (con enlace *Skip to main content* al pulsar Tab) y \<aside aria-label="Estado de sesión y alertas"\>.




## **3. Reglas Estrictas de Accesibilidad para Aprobar @axe-core/playwright (0 Violaciones)**

El test vue3/e2e/accessibility.e2e.ts escanea las rutas con los tags \['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'\]. Todo componente Vue 3 DEBE cumplir:


1. **Etiquetado de Formularios (label / aria-label):**

   - Ningún \<input\>, \<select\> o \<textarea\> puede existir sin un \<label :for="id"\> explícito o atributo aria-label descriptivo (incluyendo los buscadores de tablas y selectores de paginación).

2. **Botones con Solo Icono:**

   - Todo botón que represente una acción mediante un icono SVG (ej. desconectar sesión PPPoE, copiar clave de bóveda, expulsar usuario en *Kill-Switch*, refrescar tabla) DEBE tener aria-label="..." y el \<svg\> interno DEBE llevar aria-hidden="true".

3. **Jerarquía de Encabezados (h1 -\> h2 -\> h3):**

   - Toda vista en vue3/src/views/ DEBE tener exactamente **un único \<h1\>** visible que identifique la pantalla actual, seguido de \<h2\> y \<h3\> sin saltar niveles.

4. **Estabilidad Visual para Snapshot Testing (toHaveScreenshot):**

   - En playwright.config.ts, maxDiffPixelRatio es 0.01. Todos los contenedores de gráficas (\<canvas\> / \<svg\>) y el contenedor del mapa OpenStreetMap DEBEN tener dimensiones explícitas (min-height) y soportar modo determinista cuando se detecta entorno de prueba E2E.




## **4. Reglas de Rendimiento para Aprobar Lighthouse CI (lighthouserc.js)**

Los umbrales de lighthouserc.js exigen performance \>= 0.90, accessibility \>= 0.95, best-practices \>= 0.90 y seo \>= 0.90:


1. **Code-Splitting y Lazy Loading en Vue Router:**

   - Solo el layout base, LoginView.vue y DashboardView.vue se cargan en el bundle principal.

   - Todas las demás vistas (y especialmente la librería leaflet del mapa y el comparador Diff) se importan dinámicamente con () =\> import('../views/...').

2. **Configuración de Chunks en vite.config.ts:**

   - Separar vendor-vue (vue, vue-router, pinia) y vendor-map (leaflet) en build.rollupOptions.output.manualChunks para que el *First Contentful Paint (FCP)* y el *Largest Contentful Paint (LCP)* ocurran en menos de 800ms.

3. **Metadatos SEO / Best Practices en vue3/index.html:**

   - Atributo \<html lang="es"\>, \<meta name="viewport" content="width=device-width, initial-scale=1.0"\>, \<meta name="description" content="RoSGrid - Consola Centralizada Multi-Tenant para Gestión de Flotas MikroTik RouterOS v7+"\> y enlace al manifest.webmanifest.
