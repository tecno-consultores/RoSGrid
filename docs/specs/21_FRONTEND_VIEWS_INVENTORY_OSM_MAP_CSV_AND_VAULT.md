# 21 — VISTAS FRONTEND: INVENTARIO MIKROTIK, MAPA INTERACTIVO OPENSTREETMAP (LEAFLET), IMPORTADOR CSV, BÓVEDA STEP-UP (30s) Y MANTENIMIENTO (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica los componentes y vistas en vue3/src/views/inventory/ para la gestión del inventario de routers MikroTik RouterOS v7+, el mapa geográfico interactivo 100% gratuito con **Leaflet + OpenStreetMap**, el asistente de importación masiva por CSV en 2 pasos, el modal de **Bóveda Criptográfica con *Step-Up Auth* de 30 segundos** (exclusivo para los 2 roles más altos) y el programador de ventanas de mantenimiento.




## **1. Vista Principal de Inventario y Topología (vue3/src/views/inventory/RouterInventoryView.vue)**

- **Ruta:** /inventory/routers (y resumen integrado en /dashboard).

- **Modos de Visualización Conmutables:**

  1. **Modo Tabla de Alta Densidad (Table View)**: Para filtrado rápido, selección múltiple y acceso técnico.

  2. **Modo Mapa Geográfico (OpenStreetMap View)**: Para supervisión espacial de nodos, torres y sucursales.

  3. **Modo Dividido (Split View en pantallas \>= 1440px)**: Tabla a la izquierda y mapa interactivo sincronizado a la derecha.

### **1.1 Columnas y Filtros de la Tabla de Inventario**

- **Filtros Superiores Accesibles:**

  - Selector por **Rol en la Red (network\_role)**: CORE, EDGE\_BGP, WAN\_BALANCER, BRAS\_PPPOE, DISTRIBUTION\_SWITCH, TOWER\_AP, CORPORATE\_CPE.

  - Selector por **Estado Administrativo (admin\_state)**: PRODUCTION, MAINTENANCE, STAGING\_LAB, RETIRED.

  - Selector por **Estado Operativo en Vivo (desde Redis)**: ONLINE, DEGRADED\_HIGH\_LOAD, OFFLINE, SSL\_MISMATCH.

  - Filtro por **Etiquetas (tags)** y buscador instantáneo por nombre, serial, identity, modelo o ubicación física.

- **Columnas Mostradas:**

  1. **Indicador de Salud + Nombre (display\_name + ros\_identity):** Punto luminoso (\#22C55E Online, \#F59E0B Carga Alta, \#EF4444 Offline, \#38BDF8 en Mantenimiento).

  2. **Rol en la Red y Etiquetas:** Badges compactos.

  3. **Ubicación Física y Coordenadas:** Texto de ubicación + icono para centrar el equipo en el mapa OpenStreetMap.

  4. **Hardware Autodescubierto:** model\_name / board\_name, architecture\_name y **serial\_number** (monoespaciado).

  5. **Versión RouterOS / Firmware:** Muestra ros\_version y un indicador si existe update\_available\_version.

  6. **Estado SSL TOFU:** Badge Pinned SHA-256 (verde), Pending TOFU (gris) o SSL Mismatch! (rojo parpadeante con acceso directo a Re-Pin para Administradores).

  7. **Puesta en Línea (online\_since\_date) y Último Contacto (last\_seen\_at).**

  8. **Acciones Rápidas:**

     - Botón **"Abrir Consola WebFig"** (navega a /routers/\{router\_id\}/webfig/dashboard).

     - Botón **"Bóveda de Claves"** (visible y habilitado **únicamente** si authStore.role es SUPERADMIN\_GLOBAL o TENANT\_ADMIN).

     - Botón **"Rotar Clave API Ahora"** (para roles autorizados).




## **2. Mapa Interactivo 100% Gratuito con Leaflet y OpenStreetMap (vue3/src/components/inventory/OsmRouterMap.vue)**

No utiliza Google Maps ni requiere API Keys de pago. Utiliza **Leaflet (L.map)** consumiendo capas públicas de **OpenStreetMap**:

### **2.1 Especificación Técnica del Componente OsmRouterMap.vue**

2. **Plantilla de Tiles Configurable:**

   - Por defecto utiliza el servidor público de tiles de OpenStreetMap (/\{s\}.tile.openstreetmap.org/\{z\}/\{x\}/\{y\}.png bajo protocolo seguro TLS con atribución reglamentaria © OpenStreetMap contributors).

   - En el Tema Oscuro (dark) y Wallboard NOC (noc-high-contrast), aplica un filtro CSS ligero sobre la capa .leaflet-tile-pane (filter: brightness(0.82) contrast(1.15) saturate(0.8)) para no encandilar a los operadores nocturnos.

2. **Pines SVG Vectoriales por Estado y Rol (L.divIcon):**

   - Cada MikroTik con coordenadas (latitude, longitude) se renderiza con un marcador SVG accesible (role="button", tabindex="0", aria-label="Router RB4011-Norte, estado ONLINE") cuyo color refleja en tiempo real los eventos recibidos por el WebSocket /ws/v1/tenant/events:

     - **Verde (\#22C55E)**: ONLINE

     - **Amarillo (\#F59E0B)**: DEGRADED\_HIGH\_LOAD (CPU \>= 90%)

     - **Rojo con pulso (\#EF4444)**: OFFLINE o SSL\_MISMATCH

     - **Azul (\#38BDF8)**: En ventana de mantenimiento (MAINTENANCE)

3. **Popup Técnico y Sanitización Obligatoria Anti-XSS (escapeHtml):**
   - Muestra: Nombre, Identity, Rol en la Red, Ubicación Física, Serial, Versión de RouterOS, CPU/RAM instantáneos del último chequeo en Redis y botones de acción ("Entrar a WebFig" y "Ejecutar Ping Rápido").
   - **Prevención de XSS en Popups Leaflet:** Debido a que Leaflet renderiza HTML crudo en `popupContent.innerHTML`, todos los valores dinámicos provenientes del inventario o telemetría (`display_name`, `ros_identity`, `serial_number`, `physical_location`, etc.) son sanitizados estrictamente mediante `escapeHtml()` (`vue3/src/utils/security.ts`) antes de su inserción en el DOM, neutralizando cualquier inyección maliciosa `<script>`, `onload` o tags HTML en nombres de routers u ONUs.

4. **Selector Interactivo de Coordenadas en el Formulario de Alta/Edición:**

   - Al crear o editar un MikroTik, el administrador puede escribir latitude y longitude manualmente o hacer clic directamente sobre el mini-mapa para fijar la ubicación exacta del nodo o torre.

5. **Modo Determinista para Pruebas E2E Playwright (accessibility.e2e.ts):**

   - Cuando Playwright intercepta las rutas en las pruebas de regresión visual, los tiles se reemplazan por un bloque SVG gris uniforme con cuadrícula estática para garantizar 0.00 de diferencia de píxeles en toHaveScreenshot.




## **3. Asistente de Importación Masiva por CSV en 2 Pasos (vue3/src/components/inventory/CsvOnboardingWizardModal.vue)**

1. **Paso 1 (Descarga de Plantilla y Validación *Dry-Run*):**

   - Botón **"Descargar Plantilla CSV de Ejemplo"** (genera un Blob local con los encabezados oficiales).

   - Zona de arrastrar archivo .csv (\<input type="file" accept=".csv"\>).

   - Envía el archivo a POST /api/v1/inventory/import-csv/dry-run y muestra una tabla previa donde las filas válidas aparecen en verde y las filas con errores (ej. serial repetido o URL inválida) aparecen en rojo con la explicación exacta del campo a corregir.

2. **Paso 2 (Confirmación e Importación):**

   - Botón **"Importar N Equipos Válidos y Ejecutar Autodescubrimiento TOFU"** que invoca POST /api/v1/inventory/import-csv/commit con Idempotency-Key.




## **4. Modal de Bóveda Criptográfica con *Step-Up Auth* de 30 Segundos (vue3/src/components/inventory/VaultRevealModal.vue)**

Cumple la condición estricta de que **solo los 2 perfiles más altos (SUPERADMIN\_GLOBAL y TENANT\_ADMIN) puedan consultar las claves API actuales y rotadas**:


1. **Verificación de Rol en UI y Backend:**

   - El componente verifica \['SUPERADMIN\_GLOBAL', 'TENANT\_ADMIN'\].includes(authStore.user.role).

2. **Estado Inicial (Bloqueado):**

   - Muestra el api\_username, la fecha de última rotación (last\_rotated\_at), la fecha de próxima rotación automática (next\_rotation\_due\_at), y las contraseñas enmascaradas (••••••••••••••••••••••••••••••••).

   - Muestra el formulario *Step-Up*: campo obligatorio **"Motivo de consulta (quedará registrado en la Auditoría Inmutable)"** + campo de 6 dígitos **"Código 2FA TOTP actual"**.

3. **Estado Desbloqueado Temporal (30 Segundos Exactos):**

   - Tras responder 200 OK el endpoint POST /api/v1/inventory/routers/\{router\_id\}/vault/reveal, el modal muestra:

     - **Contraseña API Actual (current\_password)** con botón **"Copiar al Portapapeles"** (navigator.clipboard.writeText).

     - **Contraseña API Anterior (previous\_password)** (útil para diagnóstico si una rotación reciente falló a mitad de camino).

     - **Barra de Progreso de Autodestrucción (30s -\> 0s):** Un setInterval descuenta cada segundo. Al llegar a 0 segundos (o en el hook onBeforeUnmount si el usuario cierra el modal antes), las variables reactivas revealedCurrentPassword y revealedPreviousPassword se sobrescriben inmediatamente con "" y el modal vuelve al estado bloqueado.




## **5. Vista de Ventanas de Mantenimiento Programadas (vue3/src/views/inventory/MaintenanceWindowsView.vue)**

- **Ruta:** /inventory/maintenance-windows

- Permite listar, crear y cancelar ventanas de mantenimiento indicando:

  - Título y motivo técnico.

  - Selección de un MikroTik específico (router\_id) o una etiqueta completa (target\_tag, ej. nodo-valencia).

  - Rango de inicio y fin (starts\_at, ends\_at en zona horaria local America/Caracas, convertidos a UTC al enviar al backend).

  - Checkbox suppress\_alerts = true para silenciar notificaciones hacia Telegram, SMTP y Webhook mientras dure el trabajo programado.
