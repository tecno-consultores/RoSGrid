# 22 — CONSOLA WEBFIG EN VUE 3: GRÁFICAS EFÍMERAS EN RAM (RINGBUFFER ESTILO WINBOX), PESTAÑAS CON MEMORIA (KEEPALIVE), CAPA 1 Y MOTOR DINÁMICO CAPA 2 (RoSGrid)

**[DIRECTIVA PARA ANTIGRAVITY]:** Este documento especifica la vista más importante para la operación técnica diaria: la **Consola Centralizada WebFig de un Equipo MikroTik** (`vue3/src/views/webfig/RouterWebFigLayout.vue`). Incluye la navegación multi-pestaña con memoria en RAM (`<KeepAlive :max="5">`) estilo sub-ventanas de WinBox, el diseño del buffer circular (`TelemetryRingBuffer` con `shallowRef` y dibujo en `<canvas>` 2D) para que las gráficas de CPU, RAM y tráfico de interfaces funcionen exactamente igual que en WinBox (acumulando datos mientras la consola del router permanezca abierta y reseteándose al salir, con cero almacenamiento en base de datos), las vistas especializadas de Capa 1 y el renderizador dinámico universal de Capa 2.

---

## 1. Estructura del Layout Interno del Router (`RouterWebFigLayout.vue`)

Al entrar a `/routers/{router_id}/webfig/*`, la interfaz replica la ergonomía y velocidad de **WinBox / WebFig v7** adaptada a escritorio, tableta y teléfono móvil mediante 4 bloques coordinados:

1. **Cabecera Técnica del Equipo (`RouterContextHeader.vue`):**
   - Muestra en una sola barra compacta con números tabulares (`tabular-nums`): `display_name`, `ros_identity`, `model_name`, `serial_number`, `ros_version`, `uptime` en vivo, medidores mini de `CPU%` / `RAM%` / `Temperatura (°C)` / `Voltaje (V)`, badge de `Safe Mode: Activo (60s Rollback)` y selector rápido para saltar a otro MikroTik sin salir de la consola.
2. **Barra de Pestañas de Trabajo con Memoria en RAM (`RouterWorkspaceTabsBar.vue` + `<KeepAlive :max="5">`):**
   - **Problema que resuelve:** En la operación real de un ISP/NOC, el ingeniero salta constantemente entre `Interfaces SFP`, `Firewall`, `BGP` y `Ping/Torch`.
   - **En Escritorio y Tablet Horizontal (`>= 768px`):** Muestra una barra superior de pestañas estilo IDE / sub-ventanas ordenadas de WinBox (`[📊 Vivo] [🔌 Interfaces ×] [🛡️ Firewall ×] [🌐 BGP ×]`) con borde inferior cian (`#06B6D4`) en la pestaña activa y botón accesible para cerrar cada pestaña (`aria-label="Cerrar pestaña Firewall"`).
   - **En Móvil (`< 768px`):** Se transforma en una tira horizontal deslizable con el pulgar (*swipeable pills*) en la parte superior, complementada por la **Barra Inferior Fija (*Bottom Bar*)** de 5 accesos rápidos (`[📊 Vivo]`, `[🔌 SFP/Red]`, `[⚡ PPP/Colas]`, `[🛠️ Ping/Tools]`, `[☰ Menú Completo]`).
   - **Persistencia Efímera con `<RouterView v-slot="{ Component }">` + `<KeepAlive :max="5">`:** Conserva vivas en memoria RAM las últimas 5 vistas abiertas dentro del mismo router para no perder filtros escritos (ej. `chain=forward`), ordenamientos ni ejecuciones de `Ping` al alternar de pestaña.
3. **Menú Lateral de Módulos RouterOS (`RouterSidebarMenu.vue` — Fijo en PC, Drawer en Móvil):**
   - **Sección 1 (Principal):** Dashboard & Recursos en Vivo.
   - **Sección 2 (Módulos Nativos Capa 1):**
     - `Interfaces` (Todo, Ethernet & SFP Óptico, VLAN, Bridge & Ports, WireGuard, WiFi Registration).
     - `IP & Red` (Addresses, Routes & ECMP, ARP, Pools, DHCP Server Leases, DNS, Neighbors, Services).
     - `Firewall` (Filter Rules, NAT, Mangle, RAW, Address Lists, Connections).
     - `Routing v7` (BGP Sessions & Peers, OSPF, Routing Tables, Routing Rules, BFD, Filters).
     - `PPP & Queues` (PPPoE Active, PPP Secrets, Profiles, PPPoE Servers, Simple Queues, Queue Tree).
     - `System` (Resources, Identity, Users, Scripts, Scheduler, Packages & Updates, Reboot).
     - `Tools & Diagnóstico` (Ping, Traceroute, Torch en Vivo, Router Log).
     - `Backups & Diff Git` (Historial 30 Días, Comparador Diff `.rsc`).
   - **Sección 3 (Explorador Universal Capa 2):**
     - Desplegable alimentado por `GET .../webfig/layer2/catalog` (MPLS, ZeroTier, Containers, CAPsMAN, SNMP, Certificates, etc.).

---

## 2. Gráficas Efímeras en Memoria RAM Estilo WinBox (`RingBuffer` + `<canvas>` 2D Acelerado)

### 2.1 Implementación de la Clase Pura `TelemetryRingBuffer<T>` (`vue3/src/composables/useTelemetryRingBuffer.ts`)

Para cumplir el requerimiento de que **"si dejas el navegador en ese router por 3 horas podrás ver las gráficas de cómo ha ido subiendo o bajando el consumo, pero si sales del router y entras de nuevo las gráficas se resetean igual que en WinBox"**:

- **Capacidad para 3 Horas a 1 Tick cada 2 Segundos:**
  - $3 \text{ horas} = 10,800 \text{ segundos} \div 2\text{ s/tick} = 5,400 \text{ puntos máximos}$.
  - El `TelemetryRingBuffer` pre-aloja un arreglo circular con capacidad máxima `MAX_POINTS = 5400` en la memoria RAM de la pestaña del navegador (~600 KB de RAM total) expuesto mediante `shallowRef` para cero sobrecarga de Proxies reactivos.
  - Cada vez que llega un mensaje `TELEMETRY_TICK` por el WebSocket `/ws/v1/routers/{router_id}/live-telemetry`, inserta el punto en $O(1)$ (`head = (head + 1) % MAX_POINTS`).
- **Selectores de Ventana Temporal en Vivo:**
  - El operador puede conmutar el zoom horizontal de la gráfica entre: `Últimos 2 min (60 pts)`, `Últimos 15 min (450 pts)`, `Última 1 hora (1800 pts)` y `Últimas 3 horas (5400 pts)`.
- **Diferenciación entre Cambiar de Pestaña Interna vs. Salir del Router:**
  - El WebSocket `/ws/v1/routers/{router_id}/live-telemetry` se gestiona a nivel del contenedor padre `RouterWebFigLayout.vue`. Así, mientras el técnico salta entre las pestañas internas del mismo router (`Firewall`, `BGP`, `Interfaces`), la gráfica sigue recibiendo ticks en segundo plano sin perder ni un segundo de historial.
  - Cuando el técnico **sale de la consola del router** (`onBeforeUnmount` en `RouterWebFigLayout.vue`) o **cambia a otro `router_id`**, se cierra inmediatamente el WebSocket (haciendo que el Backend detenga el poller si `SCARD == 0` en KeyDB), se invoca `liveTelemetryStore.resetChartsBuffer()` y `webFigStore.clearRouterWorkspace()`, vaciando por completo el arreglo en RAM. No se escribe absolutamente nada en `localStorage`, `IndexedDB` ni base de datos.

### 2.2 Gráficas Incluidas en `RouterLiveDashboardView.vue` y Motor `<canvas>` 2D

- **Motor de Dibujo en `<canvas>` 2D con `requestAnimationFrame`:**
  - Queda prohibido renderizar miles de nodos DOM/SVG para las curvas de tiempo real. Las gráficas del `TelemetryRingBuffer` (hasta 5,400 puntos) se dibujan sobre un elemento `<canvas>` HTML5 nativo utilizando `requestAnimationFrame` (y un modo estático determinista cuando `navigator.webdriver === true` para superar los snapshots visuales de Playwright con `maxDiffPixelRatio <= 0.01`).

1. **Gráfica de Carga de CPU (%) e Historial Multi-Core** (trazo en Cian `#22D3EE` con relleno translúcido).
2. **Gráfica de Uso de Memoria RAM (%) y Espacio en Disco.**
3. **Gráfica de Tráfico en Vivo por Interfaz (`RX bps` en Cian `#06B6D4` / `TX bps` en Esmeralda `#10B981` y `RX pps` / `TX pps`)** con selector para superponer múltiples interfaces (ej. comparar en vivo `ether1-WAN1` vs `ether2-WAN2` en un balanceador ECMP).
4. **Indicadores Térmicos y Eléctricos:** Tarjetas compactas con `Temperatura (°C)` y `Voltaje (V)` cuando el hardware RouterBOARD los reporta.

---

## 3. Vistas Especializadas de la Capa 1 (`vue3/src/views/webfig/layer1/`)

Todas las tablas de Capa 1 utilizan `RgDataTable.vue` con **Densidad Dual Adaptativa** (`32px` WinBox en PC / `44px` táctil en móvil), **Virtual Scrolling** automático (`> 100` filas) e insignias de estado `[D]`, `[X]`, `[I]`, `[R]`:

1. **`InterfacesAndSfpView.vue`:**
   - Sub-pestañas para `Todas`, `Ethernet`, `VLAN`, `Bridge`, `WireGuard` y `WiFi`.
   - En puertos SFP/SFP+, botón **"Diagnóstico Óptico DDM"** que abre un panel en vivo con medidores visuales de potencia láser `TX dBm` y `RX dBm` coloreados según salud óptica (`OPTIMAL`, `WARNING`, `CRITICAL_LOW_LIGHT`).
2. **`FirewallRulesView.vue`:**
   - Sub-pestañas para `Filter Rules`, `NAT`, `Mangle`, `RAW`, `Address Lists` y `Connections`.
   - Filtro rápido por cadena (`all`, `input`, `forward`, `output`, `prerouting`, `postrouting`, `srcnat`, `dstnat`).
   - **Reordenamiento Drag & Drop + Teclado (`Alt+Up`/`Alt+Down`):** Al mover una fila, invoca `POST .../firewall/{proto}/{table_type}/move` mostrando el `RgSafeModeBanner.vue` mientras el MikroTik confirma que no perdió conectividad.
   - Barras proporcionales cian en la columna `Bytes / Packets` con `tabular-nums` para identificar visualmente qué reglas están recibiendo más tráfico.
3. **`RoutingBgpOspfView.vue`:**
   - Panel de sesiones BGP con indicadores de estado (`ESTABLISHED` en verde esmeralda con contador de prefijos recibidos y uptime, o `CONNECT`/`ACTIVE`/`IDLE` en ámbar/rojo).
   - Visor de prefijos anunciados (*Advertisements*), adyacencias OSPF en vivo y sesiones BFD.
4. **`PppAndQueuesView.vue`:**
   - En `PPPoE Active`, buscador instantáneo por usuario/IP/MAC y botón de un clic **"Reconectar Sesión"** (ideal para Soporte Nivel 1 desde móvil o PC).
   - En `Simple Queues`, editor visual de velocidades (`Target Upload / Download`, `Max-Limit`, `Burst`) con conversión legible (`Mbps` / `Gbps`) y reordenamiento con Safe Mode.
5. **`LiveToolsDiagnosticsView.vue`:**
   - Consola unificada con sub-pestañas para **Ping**, **Traceroute**, **Torch por Interfaz** y **Log del Router** con resaltado semántico de líneas `error` / `critical` / `warning`.

---

## 4. Renderizador Universal de la Capa 2 (`vue3/src/views/webfig/layer2/DynamicLayer2ResourceView.vue`)

Cuando un ingeniero de Soporte N3 o Administrador navega a cualquier ruta `/routers/{router_id}/webfig/layer2/{ros_path}`:

1. Consulta `GET /api/v1/routers/{router_id}/webfig/layer2/resource/{ros_path}` y abre o enfoca su pestaña en `RouterWorkspaceTabsBar.vue`.
2. Si `is_singleton === false`, construye automáticamente la tabla `RgDataTable.vue` a partir de `columns_schema` (respetando la densidad adaptativa `32px`/`44px` y el *Virtual Scrolling*) y genera dinámicamente el modal de **Crear / Editar Registro** mapeando cada tipo de atributo (`string`, `integer`, `boolean_ros`).
3. Si `is_singleton === true`, renderiza directamente el formulario de configuración del módulo con el switch **"Proteger cambio con Safe Mode (60s Rollback)"** activado por defecto.
