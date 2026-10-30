# 19 — SISTEMA DE DISEÑO FRONTEND, ALTA DENSIDAD TÉCNICA, ACCESIBILIDAD WCAG 2.1 AA (@axe-core) Y RENDIMIENTO LIGHTHOUSE CI (RoSGrid)

**[DIRECTIVA PARA ANTIGRAVITY]:** Este documento define las reglas visuales, de experiencia de usuario (UI/UX), accesibilidad (`@axe-core/playwright` = 0 violaciones) y rendimiento (`Lighthouse CI` >= 90 en Performance/SEO/Best-Practices y >= 95 en Accessibility) para `vue3/`. Cada componente que construyas DEBE respetar estrictamente estas directrices para que `make qa-perf` y `make qa-e2e` aprueben en el primer intento.

---

## 1. Filosofía Visual: Consola de Alta Densidad Técnica (Estilo WinBox / WebFig Moderno)

Los ingenieros de red y operadores NOC necesitan visualizar decenas de interfaces, rutas BGP o reglas de Firewall simultáneamente con bordes de cuadrícula claros, tipografía numérica alineada y acentos que destaquen el estado operativo en milisegundos.

### 1.1 Los 3 Temas Oficiales (`vue3/src/assets/themes.css` — Variables CSS Nativas)

El archivo `vue3/src/assets/themes.css` define 3 paletas que cumplen matemáticamente con el ratio de contraste **WCAG 2.1 AA (`>= 4.5:1` para texto normal y `>= 3.0:1` para componentes UI)** para no fallar jamás la regla `color-contrast` de `@axe-core/playwright`:

1. **Tema Oscuro Táctico NOC (`data-theme="dark"` — Predeterminado con Resplandor Cian):**
   - `--rg-bg-canvas`: `#0B0F19` (Pizarra abisal de fondo general).
   - `--rg-bg-surface`: `#111827` (Superficie de paneles, tarjetas y tablas).
   - `--rg-bg-elevated`: `#1E293B` (Cabeceras de tabla, pestañas activas y filas en hover).
   - `--rg-border-grid`: `#1E293B` (Líneas divisorias de celdas estilo WinBox) y `#334155` (Bordes de paneles).
   - `--rg-accent-cyan`: `#22D3EE` para texto/iconos interactivos sobre fondo oscuro (ratio de contraste **10.8:1**, superando holgadamente WCAG AA) y `#06B6D4` para bordes activos e indicadores con resplandor sutil `--rg-cyan-glow: 0 0 12px rgba(6, 182, 212, 0.28)`.
   - `--rg-text-primary`: `#F8FAFC` | `--rg-text-secondary`: `#CBD5E1` | `--rg-text-muted`: `#94A3B8` (ratio >= 4.6:1 sobre `#0B0F19`, prohibido usar grises más oscuros).
   - **Estados Semánticos:**
     - `--rg-status-online`: `#10B981` (Texto en badges: `#6EE7B7` sobre `#064E3B`).
     - `--rg-status-warning`: `#F59E0B` (Safe Mode 60s / Maker-Checker / SFP Warning).
     - `--rg-status-critical`: `#EF4444` (Offline / Regla Inválida `[I]` / Alerta TOFU SSL).
     - `--rg-status-info`: `#38BDF8` (Rutas dinámicas `[D]` / Pinning TOFU).
2. **Tema Claro de Campo / Oficina (`data-theme="light"`):**
   - `--rg-bg-canvas`: `#F8FAFC` | `--rg-bg-surface`: `#FFFFFF` | `--rg-border-grid`: `#E2E8F0`.
   - `--rg-accent-cyan`: `#0E7490` (Cian oscuro con ratio >= 5.2:1 sobre blanco) | `--rg-text-primary`: `#0F172A` | `--rg-text-secondary`: `#334155`.
3. **Tema Wallboard NOC Alto Contraste (`data-theme="noc-high-contrast"`):**
   - Fondo negro puro `#000000` para pantallas OLED/LED de centros de monitoreo 24/7, tipografía escalada `1.15rem`, bordes de `2px` de alto contraste y resplandor semántico para lectura a 5 metros de distancia.

### 1.2 Tipografía del Sistema (Cero Fuentes Externas Bloqueantes)

Para lograr un **Score >= 95 en Lighthouse Performance** y evitar *Cumulative Layout Shift (CLS)* o bloqueos de red en contenedores aislados:

- Queda **TERMINANTEMENTE PROHIBIDO** cargar fuentes desde servidores externos (Google Fonts) o CDNs en internet.
- Se utiliza pila de fuentes nativas del sistema:
  - **UI General:** `system-ui, -apple-system, 'Segoe UI', Roboto, Ubuntu, sans-serif`.
  - **Datos Técnicos (IPs, MACs, contadores de paquetes/bytes, potencias SFP en `dBm`, reglas Firewall, `.rsc` Diff):** `'JetBrains Mono', 'Ubuntu Mono', ui-monospace, SFMono-Regular, monospace` con `font-variant-numeric: tabular-nums` obligatorio para que los números en las tablas y gráficas en vivo no bailen horizontalmente al actualizarse cada 2 segundos.

---

## 2. Componentes Base Reutilizables y Accesibles (`vue3/src/components/common/`)

Para evitar duplicación de código y mantener complejidad cognitiva baja en SonarJS, Antigravity DEBE construir estos 5 componentes base:

### 2.1 `RgDataTable.vue` (Tabla Técnica Estilo WinBox con Densidad Dual, Virtual Scrolling y Drag & Drop)

- **Densidad Dual Adaptativa (`compact` vs `comfortable`):**
  - Conectada a `useThemeAndLayoutStore.effectiveTableDensity` e incluye en su barra de herramientas superior un botón conmutador accesible (`[≡ Compacta | ☰ Cómoda]`, `aria-label="Cambiar densidad de tabla"`).
  - **Modo `compact` (Predeterminado en PC `>= 1024px`):** Altura de fila determinista de `32px`, relleno compacto `4px 8px`, bordes de cuadrícula `1px solid var(--rg-border-grid)` visibles al estilo WinBox y resaltado de fila activa con borde izquierdo cian (`2px solid #06B6D4`).
  - **Modo `comfortable` (Automático en Móvil/Tablet `< 1024px`):** Altura mínima de fila y botones de `44px`, primera columna fija (`position: sticky; left: 0; z-index: 2`) y botón `+ Ver detalles` para desplegar las columnas secundarias en formato de tarjeta vertical sin exigir scroll horizontal excesivo.
- **Virtual Scrolling Nativo de Alto Rendimiento (Sin Librerías Externas):**
  - Aprovechando la altura determinista de fila (`32px` en modo `compact` y `44px` en modo `comfortable`), cuando el arreglo `rows` supere los `100` elementos, `RgDataTable.vue` activa automáticamente su ventana de virtualización (`startIndex`, `endIndex`, `overscan = 10`), renderizando en el DOM únicamente las ~30 filas visibles en el viewport más un espaciador superior/inferior para mantener 60 FPS constantes en PC y móviles incluso con 5,000 sesiones PPPoE o rutas BGP.
- **Insignias de Estado Nativas de RouterOS (Flags Column):**
  - Soporta el renderizado estandarizado de banderas MikroTik al inicio de cada fila:
    - `[D]` (*Dynamic*) en cian informativo.
    - `[X]` (*Disabled*) aplicando estilo cursiva y opacidad accesible a toda la fila (igual que en WinBox).
    - `[I]` (*Invalid*) en rojo coral con etiqueta `title` del motivo.
    - `[R]` (*Running*) en verde esmeralda para interfaces y sesiones activas.
- **Soporte Drag & Drop Dual (Ratón + Teclado + Táctil):**
  - Utilizado en Firewall (`Filter`, `NAT`, `Mangle`, `RAW`) y `Simple Queues`.
  - Además de arrastrar con el ratón, cada fila ordenable incluye botones accesibles por teclado (`Alt + Flecha Arriba` / `Alt + Flecha Abajo` con `aria-label="Mover regla *1C hacia arriba"`) para cumplir al 100% con **WCAG 2.1.1 (Keyboard Accessible)**.

### 2.2 `RgCommandPalette.vue` (Buscador Global Rápido `Ctrl + K` / `Cmd + K`)

- Modal accesible (`role="dialog"`, `aria-modal="true"`, `aria-labelledby="cmd-palette-title"`) invocable desde cualquier pantalla con `Ctrl + K` o desde el botón de búsqueda de la cabecera.
- Permite buscar en milisegundos:
  - Cualquier MikroTik por `display_name`, `serial_number`, `ros_identity`, ubicación física o IP.
  - Saltar directamente a un submenú de Capa 1 o Capa 2 de un router (ej. escribir `"RB4011 bgp"` o `"CCR2004 firewall"` y abrir directamente esa pestaña de trabajo).

### 2.3 `RgSafeModeBanner.vue` (Indicador Visual del *Dead Man's Switch*)

- Barra superior fija con `role="status"` y `aria-live="polite"` que se activa con borde ámbar/cian cuando una operación con **Safe Mode** está verificando la supervivencia del MikroTik, mostrando la cuenta regresiva de 60 segundos y la confirmación verde cuando el scheduler temporal `rosgrid_safemode_*` fue limpiado con éxito.

### 2.4 `RgStepUp2FAModal.vue` (Modal de Confirmación TOTP para Acciones Sensibles)

- Reutilizado para revelar claves en la Bóveda (con barra de progreso visual que se vacía en **30 segundos** antes de purgar la clave de la memoria RAM), autorizar Re-Pin SSL TOFU o reiniciar el 2FA de un técnico.

### 2.5 `RgResponsiveShell.vue` (Layout Maestro de Doble Contexto: Escritorio / Tablet / Móvil)

- Implementa una arquitectura de navegación de **Doble Contexto**:
  1. **Riel Global Izquierdo (Flota & Tenant):** Acceso rápido a Inventario + Mapa OSM, Bandeja Maker-Checker, Backups/Diff, Trabajos Masivos, Matriz de Usuarios (11 Roles), Kill-Switch en vivo, Wallboard NOC y Consola Forense WORM.
  2. **Área Contextual Principal (`<main id="main-content">`):** Donde se montan las vistas globales o la consola `RouterWebFigLayout.vue` del equipo seleccionado.
  3. **Barra Inferior Fija para Móvil (`< 768px`):** Barra táctil inferior con áreas de toque de `44x44px` para operación con el pulgar en campo (`Vivo`, `SFP/Red`, `PPP/Colas`, `Ping/Tools`, `Menú`).
  4. **Pie de Página Global Autenticado (`<footer id="app-global-footer">`):** Ubicado en la base del shell de navegación, presenta de forma discreta y elegante el crédito institucional: *"Elaborado por [Tecno Consultores 2023 C.A.](https://www.tecnoconsultores.net/) • Licencia GNU GPLv3"*, enlace al repositorio de GitHub (`https://github.com/tecno-consultores/RoSGrid/`) y número de versión activa, manteniendo ratio de contraste accesible `>= 4.5:1` (`--rg-text-muted`) sin interferir en la cuadrícula de trabajo.
- Incluye todos los hitos semánticos HTML5 obligatorios para `@axe-core`: `<header>`, `<nav aria-label="Navegación principal">`, `<main id="main-content">` (con enlace *Saltar al contenido principal* al pulsar `Tab`), `<aside aria-label="Estado de sesión y alertas">` y `<footer id="app-global-footer">`.

### 2.6 `RgApiHealthBadge.vue` (Indicador Táctico de Disponibilidad de API, Heartbeat y Popover Diagnóstico)

- **Ubicación Estratégica:** Visible permanentemente en la barra superior de `RgResponsiveShell.vue` (junto al reloj del sistema `🕒`) y en la cabecera de acceso en `LoginView.vue`.
- **Estados Semánticos y Micro-animaciones:**
  - `ONLINE`: Punto verde esmeralda con respiración táctica suave (`box-shadow: 0 0 8px #10b981`) y latencia en milisegundos (`API XXms`).
  - `OFFLINE`: Punto rojo carmesí con destello alternante de alerta NOC (`API OFFLINE`) ante fallos de red o caídas completas del backend.
  - `DEGRADED`: Punto ámbar (`API DEGRADADO`) ante indisponibilidad de dependencias (PostgreSQL o KeyDB caídos con HTTP 503).
  - `CHECKING`: Indicador cian interactivo mientras se evalúa la conexión (`PING...`).
- **Arquitectura de Alto Rendimiento y Cero Sobrecarga (`useApiHeartbeatStore.ts`):**
  - **Monitoreo Pasivo (Piggybacking):** Intercepta llamadas exitosas de `httpClient.ts` mediante eventos personalizados `rosgrid:api-health-event`, actualizando latencia sin generar peticiones HTTP adicionales mientras el operador trabaja activamente.
  - **Sincronización Pestaña a Pestaña (`BroadcastChannel`):** Utiliza el canal `rosgrid_api_heartbeat` para que una sola pestaña consulte la API y propague el estado instantáneamente a todas las demás pestañas abiertas en el navegador.
  - **Pausa Automática en Segundo Plano (`Page Visibility API`):** Pausa el sondeo por completo cuando la pestaña está oculta o minimizada (`document.hidden`), reanudando y evaluando frescura al volver al primer plano.
  - **Popover Diagnóstico Táctico:** Despliegue interactivo con desglose de latencia, estado de FastAPI, PostgreSQL y KeyDB, y acción para reintentar ping manualmente de forma inmediata.

### 2.7 `RgContextualHelpDrawer.vue` (Cajón de Ayuda Contextual por Pantalla y Submódulo WebFig)

- **Ubicación y Activación (`docs/specs/52`):** Invocable desde el botón táctico `[ ❓ Ayuda ]` en la barra superior de `RgResponsiveShell.vue`, desde el botón `[ ❓ Guía del Módulo ]` en `RouterWebFigLayout.vue` o mediante el atajo de teclado `F1` / `Alt + H`.
- **Resolución Contextual Automática (`helpCatalog.ts`):** Detecta la ruta activa (`route.name` / `route.path`) y la pestaña seleccionada en WebFig para mostrar el propósito de la pantalla, guía paso a paso de acciones CRUD, reglas de Safe Mode (60s) / Maker-Checker (HTTP 202) y notas de RouterOS v7.
- **Frontera Arquitectónica Estricta:** El componente en `RoSGrid` **no** incluye botón de conversión a PDF (la descarga y conversión de los manuales `docs/MANUAL_ADMINISTRADOR_E_INSTALADOR.md` y `docs/MANUAL_USUARIO_Y_OPERADOR_NOC.md` desde GitHub a PDF reside exclusivamente en el portal de presentación `rosgrid-web`).

---

## 3. Reglas Estrictas de Accesibilidad para Aprobar `@axe-core/playwright` (0 Violaciones)

El test `vue3/e2e/accessibility.spec.ts` escanea las rutas con los tags `['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']`. Todo componente Vue 3 DEBE cumplir:

1. **Etiquetado de Formularios (`label` / `aria-label`):**
   - Ningún `<input>`, `<select>` o `<textarea>` puede existir sin un `<label :for="id">` explícito o atributo `aria-label` descriptivo (incluyendo los buscadores de tablas y selectores de paginación).
2. **Botones con Solo Icono:**
   - Todo botón que represente una acción mediante un icono SVG (ej. desconectar sesión PPPoE, copiar clave de bóveda, cerrar pestaña de trabajo, expulsar usuario en *Kill-Switch*, refrescar tabla) DEBE tener `aria-label="..."` y el `<svg>` interno DEBE llevar `aria-hidden="true"`.
3. **Jerarquía de Encabezados (`h1 -> h2 -> h3`):**
   - Toda vista en `vue3/src/views/` DEBE tener exactamente **un único `<h1>`** visible que identifique la pantalla actual, seguido de `<h2>` y `<h3>` sin saltar niveles.
4. **Estabilidad Visual para Snapshot Testing (`toHaveScreenshot`):**
   - En `playwright.config.ts`, `maxDiffPixelRatio` es `0.01`. Todos los contenedores de gráficas (`<canvas>` / `<svg>`) y el contenedor del mapa OpenStreetMap DEBEN tener dimensiones explícitas (`min-height`) y soportar modo determinista cuando se detecta entorno de prueba E2E.

---

## 4. Reglas de Rendimiento para Aprobar Lighthouse CI (`lighthouserc.js`)

Los umbrales de `lighthouserc.js` exigen `performance >= 0.90`, `accessibility >= 0.95`, `best-practices >= 0.90` y `seo >= 0.90`:

1. **Code-Splitting y Lazy Loading en Vue Router:**
   - Solo el layout base, `LoginView.vue` y el dashboard inicial se cargan en el bundle principal.
   - Todas las demás vistas (y especialmente la librería `leaflet` del mapa y el comparador Diff) se importan dinámicamente con `() => import('../views/...')`.
2. **Configuración de Chunks en `vite.config.ts`:**
   - Separar `vendor-vue` (`vue`, `vue-router`, `pinia`) y `vendor-map` (`leaflet`) en `build.rollupOptions.output.manualChunks` para que el *First Contentful Paint (FCP)* y el *Largest Contentful Paint (LCP)* ocurran en menos de 800ms.
3. **Metadatos SEO / Best Practices en `vue3/index.html`:**
   - Atributo `<html lang="es" data-theme="dark">`, `<meta name="viewport" content="width=device-width, initial-scale=1.0">`, `<meta name="theme-color" content="#0B0F19">`, `<meta name="description" content="RoSGrid - Consola Centralizada Multi-Tenant para Gestión de Flotas MikroTik RouterOS v7+">` y enlace al `manifest.webmanifest`.

---

## 5. Estándar Refactoring UI (Sistemas de Tokens, Jerarquía Visual y Pulido Táctico)

Para garantizar coherencia estética de grado corporativo sin sacrificar la densidad tipo WinBox:

1. **Cero Tokens CSS Huérfanos y Escalas con Nombre (`themes.css`):**
   - Toda propiedad `var(--rg-*)` empleada en vistas o modales está declarada en los tres temas (`dark`, `light`, `noc-high-contrast`), incluyendo `--rg-bg-card`, `--rg-bg-input`, `--rg-border`, `--rg-space-1` a `--rg-space-12`, `--rg-radius-xs` a `--rg-radius-xl`, y la escala tipográfica de 7 peldaños (`--rg-text-2xs` a `--rg-text-xl`).
2. **Jerarquía de Botonera y Acciones de Fila (*Severity is not rank*):**
   - Cada pantalla exhibe una única acción primaria destacada (`.rg-btn--primary` / `.btn-primary`). Las acciones secundarias de cabecera (`Importar CSV`, `Matriz CVE`, `Ventanas de Mantenimiento`, `Personalizar Roles`, `Wizards NAT`) mantienen superficie y borde neutros en reposo, revelando su color semántico en `:hover` / `:focus-visible`.
   - En las filas de `RgDataTable.vue`, se mantienen todas las acciones visibles en línea (ergonomía NOC de 1 clic): solo `WebFig` conserva acento cian en reposo y las demás acciones (`Syslog`, `Vault`, `Mantenimiento`, `TOFU`, `Eliminar`) permanecen neutras hasta `:hover` / `:focus-visible`.
3. **Radios Concéntricos, Profundidad en Modo Oscuro y Estados Vacíos:**
   - Los controles segmentados usan `border-radius: 8px` externo con `padding: 3px` y botones internos de `border-radius: 5px` (`--rg-radius-concentric`).
   - La elevación en modo oscuro se apoya en iluminación cenital (`--rg-inset-highlight`) y escalones de superficie (`canvas` ➔ `surface` ➔ `elevated`), eliminando bordes dobles concéntricos.
   - `RgDataTable.vue` presenta automáticamente un estado vacío táctico accesible (`.rg-table-empty`, `role="status"`) cuando `rows.length === 0`.
4. **Seguridad para Daltonismo (*Color supports, never carries*) y `<canvas>` Dinámico:**
   - Los indicadores de conectividad combinan color y geometría: círculo sólido verde (`#10B981`) para *Online* frente a anillo hueco de `2px` (`#EF4444`) para *Offline*.
   - Las gráficas 2D `<canvas>` en `RouterLiveDashboardView.vue` leen `--rg-border-grid` y `--rg-text-muted` dinámicamente mediante `getComputedStyle`.

---

## 6. Arquitectura Responsive Integral Multi-Viewport (Móvil `375px`, Tablet `768px`, Escritorio `1440px`)

1. **Unidades de Viewport Dinámicas (`100dvh`) y Aislamiento de Scroll (`overscroll-behavior: contain`):**
   - `App.vue`, `RgResponsiveShell.vue` y `RouterWebFigLayout.vue` emplean `height: 100vh; height: 100dvh` con mejora progresiva y `overscroll-behavior: contain` en `.rg-rail`, `.rg-main` y `.router-sidebar` para adaptarse a barras dinámicas de navegadores móviles y evitar encadenamiento de scroll.
2. **Independencia entre Colapso de Escritorio y Drawer Móvil/Tablet:**
   - En viewports `<= 1023px`, el botón `#btn-toggle-sidebar` de escritorio se oculta y la regla `.rg-rail.rg-rail--collapsed.rg-rail--open` garantiza que el cajón lateral abra siempre a `260px` aunque exista preferencia previa en `localStorage`.
3. **Contención Horizontal de Tablas (`.table-wrapper` y `role="region"`):**
   - `RgDataTable.vue` (`.rg-table-scroll.table-wrapper`) y todas las tablas nativas (`.table-scroll-wrapper` en IPAM, Operaciones Masivas, Interfaces, Firewall, RBAC, CVE, Auditoría WORM y Canales de Notificación) envuelven los elementos `<table>` con `overflow-x: auto; max-width: 100%; -webkit-overflow-scrolling: touch; overscroll-behavior-x: contain`, garantizando `document.documentElement.scrollWidth <= window.innerWidth` en cualquier resolución.
4. **Acceso Táctico a Módulos WebFig en Tablet y Móvil (`<= 1024px`):**
   - `RouterWorkspaceTabsBar.vue` incorpora el botón en línea `.btn-webfig-menu-inline` (`☰ Módulos`) para abrir el cajón de navegación de módulos RouterOS v7 tanto en tablets (`768px–1024px`) como en teléfonos móviles (`< 768px`), sin depender exclusivamente de la barra inferior.
5. **Rejillas intrínsecas (`minmax(min(100%, ...), 1fr)`) y Drawers Cartográficos Adaptativos:**
   - Las rejillas de gráficas (`RouterLiveDashboardView.vue`), Feature Flags (`RgFeatureFlagsGrid.vue`) y formularios de 2 columnas colapsan limpiamente a 1 columna en `<= 640px`, mientras que la matriz IPAM de 256 IPs (`IpamIpGridModal.vue`) adapta sus columnas de `16` (escritorio) a `8` (`<= 768px`) y `4` (`<= 480px`).
   - Los paneles laterales de mapas (`UnifiedNetworkMap.vue`, `SubscribersMapView.vue`, `L2TopologyView.vue`) se anclan al borde inferior del lienzo (`left: 8px; right: 8px; width: auto; max-height: 55%`) en pantallas estrechas.


