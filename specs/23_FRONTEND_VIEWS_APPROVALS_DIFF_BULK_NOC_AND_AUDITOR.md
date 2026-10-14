# 23 — VISTAS FRONTEND: BANDEJA MAKER-CHECKER, COMPARADOR DIFF GIT (.rsc), ACCIONES MASIVAS, WALLBOARD NOC Y CONSOLA AUDITOR (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica las vistas operativas de alto nivel en vue3/src/views/operations/, vue3/src/views/noc/ y vue3/src/views/audit/: la bandeja de aprobaciones **Maker-Checker**, el comparador visual lado a lado estilo Git (Diff) para configuraciones .rsc, el centro de **Acciones Masivas Multi-Router / Plantillas / Updates de RouterOS**, la pantalla dedicada **Wallboard NOC** para televisores de monitoreo y la consola exclusiva del rol **Auditor**.




## **1. Bandeja de Aprobación de Cambios Críticos — *Maker-Checker* (vue3/src/views/operations/ApprovalsInboxView.vue)**

- **Ruta:** /operations/approvals

- **Roles Aprobadores (Checker):** SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR, SUPPORT\_L3.

- **Roles Solicitantes (Maker):** SUPPORT\_L2, SUPPORT\_L1, FIELD\_TECH (ven el estado de sus propias solicitudes enviadas).

### **1.1 Componentes de la Vista de Aprobaciones**

1. **Pestañas de Estado:** Pendientes de Firma (con badge en vivo), Aprobadas y Ejecutadas, Rechazadas / Expiradas.

2. **Tarjeta de Inspección Técnica de la Solicitud (ApprovalDiffInspectorCard.vue):**

   - Muestra quién solicitó el cambio (requested\_by), su rol, la justificación escrita, el MikroTik destino y el tipo de acción crítica (ej. FIREWALL\_INPUT\_OR\_SERVICE\_PORT\_CHANGE o ROUTER\_REBOOT\_OR\_SHUTDOWN).

   - **Comparador JSON Previo vs Propuesto:** Muestra lado a lado el previous\_state\_snapshot leído del MikroTik frente al request\_payload que se aplicará si se aprueba.

   - **Bloqueo de Auto-Aprobación en UI:** Si approval.requested\_by === authStore.user.id, el botón **"Aprobar y Ejecutar"** aparece deshabilitado con el mensaje *"Segregación de funciones: otro Supervisor o N3 debe aprobar tu solicitud"*.

   - Al pulsar **"Aprobar y Ejecutar con Safe Mode"**, exige escribir un comentario de revisión e invoca POST /api/v1/operations/approvals/\{id\}/approve.




## **2. Historial de Backups (30 Días) y Comparador Visual Diff Estilo Git (vue3/src/views/operations/BackupsAndGitDiffView.vue)**

- **Ruta:** /routers/\{router\_id\}/webfig/backups y vista global /operations/backups.

- **Roles Permitidos:** SUPERADMIN\_GLOBAL, TENANT\_ADMIN, SUPERVISOR, SUPPORT\_L3, SUPPORT\_L2, INVENTORY\_MANAGER y AUDITOR (en modo lectura).

### **2.1 Línea de Tiempo de Backups Deduplicados**

- Lista los respaldos de los últimos **30 días** mostrando:

  - Fecha/hora de captura y versión de RouterOS (ros\_version\_at\_backup).

  - Hash SHA-256 truncado del script .rsc y marca de última verificación idéntica (last\_verified\_identical\_at).

  - Badges de cambio estilo GitHub/GitLab: **+12 líneas** (verde) / **-3 líneas** (rojo) respecto al backup anterior.

  - Botones para descargar el .rsc desencriptado, descargar el binario .backup o seleccionarlo como Base (Izquierda) / Objetivo (Derecha) en el comparador.

### **2.2 Componente Comparador Visual Lado a Lado (RscGitDiffViewer.vue)**

- Soporta dos modos de vista: **Split (Lado a Lado)** y **Unified (En Línea)**, con opción de comparar también contra el estado **EN VIVO (LIVE)** actual del MikroTik.

- Resalta la sintaxis de RouterOS (/ip firewall filter, /routing bgp connection, add, set) y colorea:

  - Líneas añadidas en verde accesible (background: rgba(34, 197, 94, 0.18)).

  - Líneas eliminadas en rojo accesible (background: rgba(239, 68, 68, 0.18)).

  - Navegador rápido de diferencias (Siguiente cambio \[n\] / Cambio anterior \[p\]).




## **3. Plantillas (*Golden Configs*), Acciones Masivas y Actualizador de RouterOS (vue3/src/views/operations/BulkOperationsAndUpdatesView.vue)**

- **Ruta:** /operations/bulk-jobs y /operations/ros-updates.

### **3.1 Asistente de Ejecución Masiva en 3 Pasos**

1. **Paso 1 — Selección de Flota Destino:**

   - Selección de 2, 50 o todos los MikroTiks filtrando por Rol en la Red (ej. todos los TOWER\_AP), por Etiqueta (ej. zona-norte) o selección manual.

2. **Paso 2 — Selección de Plantilla Parametrizable o Acción:**

   - Elige una plantilla de config\_templates (ej. *"Actualizar DNS Corporativos"* o *"Bloquear IP Atacante en Firewall RAW"*) y rellena las variables definidas en variables\_schema.

   - Botón **"Previsualizar Comandos REST (render-preview)"** para verificar exactamente qué payload JSON recibirá cada router.

3. **Paso 3 — Ejecución con Progreso en Tiempo Real:**

   - Muestra una barra de progreso alimentada por el WebSocket (BULK\_JOB\_PROGRESS) y una tabla con el estado individual de cada MikroTik (PENDING, RUNNING, SUCCESS, ROLLED\_BACK por Safe Mode, o FAILED).

### **3.2 Centro de Actualización de RouterOS v7 y RouterBOOT**

- Muestra la matriz de versiones de toda la flota resaltando los equipos con actualización pendiente.

- Permite lanzar la actualización inmediata o agendarla dentro de una **Ventana de Mantenimiento**, indicando claramente que RoSGrid tomará un backup .rsc + .backup obligatorio antes de actualizar cada equipo.




## **4. Modo Pantalla Completa Wallboard NOC (vue3/src/views/noc/NocWallboardView.vue)**

- **Ruta:** /noc-wallboard (Vista predeterminada para el rol **NOC\_MONITOR** y accesible desde cualquier rol mediante el botón *"Modo TV / NOC"*).

- **Diseño Especial para Monitores y Televisores de Guardia 24/7:**

  1. Activa automáticamente el tema noc-high-contrast y oculta barras de herramientas de edición.

  2. **Cabecera KPI Gigante:** Contadores en tipografía grande con: Total Routers, Online (Verde), Carga Alta / Alerta (Ámbar), Offline / Caídos (Rojo Parpadeante), En Mantenimiento (Azul) y Alertas SSL TOFU.

  3. **Mitad Izquierda:** Mapa interactivo **OpenStreetMap (OsmRouterMap.vue)** con auto-zoom dinámico hacia cualquier nodo que cambie a estado OFFLINE.

  4. **Mitad Derecha:** Cinta en vivo de eventos críticos (ROUTER\_DOWN, ROUTER\_UP, HIGH\_CPU, SSL\_MISMATCH) recibidos por /ws/v1/tenant/events sin almacenar métricas históricas.




## **5. Consola de Auditoría Inmutable (vue3/src/views/audit/ImmutableAuditLogsView.vue)**

- **Ruta:** /audit-logs

- **Roles Permitidos:** Exclusivamente **AUDITOR**, **SUPERVISOR**, **TENANT\_ADMIN** y **SUPERADMIN\_GLOBAL**.

- **Capacidades:**

  1. **Buscador Forense:** Filtrado combinado por rango de fechas, usuario (actor\_username), rol, dirección IP origen, router afectado, categoría (AUTH, VAULT, WEBFIG\_L1, WEBFIG\_L2, MAKER\_CHECKER, SAFEMODE, SESSION\_KILL) y código HTTP.

  2. **Inspector de Registro e Integridad Hash-Chain:**

     - Al hacer clic en un evento, muestra el JSON completo de before\_state vs after\_state (con secretos sanitizados \[REDACTED\]), la Idempotency-Key utilizada, el prev\_record\_hash y el record\_sha256\_hash.

  3. **Botón de Certificación Criptográfica (Verificar Cadena de Custodia WORM):**

     - Invoca POST /api/v1/audit/logs/verify-integrity y muestra el sello verde certificando que ningún registro histórico del Tenant ha sido alterado ni eliminado.

  4. **Exportación Oficial:** Descarga el reporte filtrado en CSV o JSON firmado.
