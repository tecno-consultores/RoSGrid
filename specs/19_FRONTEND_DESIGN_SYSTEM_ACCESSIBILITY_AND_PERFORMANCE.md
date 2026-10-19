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
