# 📋 Historial de Cambios (Changelog) — RoSGrid

Todos los cambios notables en las versiones oficiales de **RoSGrid** (y en sus imágenes inmutables de Docker Hub `sinfallas/rosgrid-backend` y `sinfallas/rosgrid-frontend`) se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/), y este proyecto se adhiere a [Semantic Versioning (SemVer)](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Pendiente para cierre de Release 1.0.0
- Construcción de la interfaz Frontend Vue 3 (Hitos 11, 12 y 13) y manuales en `docs/` (Hito 14).
- Certificación completa de suites QA 11X en contenedores efímeros (Hito 15 — `15.1` y `15.2` ya superados con 95.03% de cobertura en Backend).
- Publicación inicial multi-etapa con `docker buildx` hacia Docker Hub (`sinfallas/rosgrid-backend:1.0.0` y `sinfallas/rosgrid-frontend:1.0.0`) (Hito 16).

---

## [1.0.0] - 2026-10-15

### Added (Nuevas Características)
- **Arquitectura Multi-Tenant con Aislamiento RLS e Índice BRIN:** Esquema en PostgreSQL 17 con `FORCE ROW LEVEL SECURITY` inyectando `app.current_tenant_id` por sesión transaccional, índice `BRIN` de alta velocidad sobre `audit_logs(created_at)` y migraciones automáticas protegidas por `pg_advisory_lock`.
- **Motor en Memoria KeyDB Multi-Hilo y Perfil DragonflyDB:** Configuración predeterminada con `eqalpha/keydb:alpine` (`--server-threads 2`), serialización rápida en Rust con `ORJSONResponse`, event loop `uvloop` + `httptools`, pipelines en lote y soporte documentado para **DragonflyDB** en despliegues ISP de gran escala.
- **Matriz RBAC de 11 Roles y Asignación Granular:** Soporte nativo para `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`, `SUPERVISOR`, `SUPPORT_L3`, `SUPPORT_L2`, `SUPPORT_L1`, `FIELD_TECH`, `INVENTORY_MANAGER`, `AUDITOR`, `NOC_MONITOR` y `SERVICE_ACCOUNT`.
- **Conector Asíncrono RouterOS v7 (`/rest/*`) con Pool TLS Keep-Alive:** Cliente `httpx` sobre TLS con reutilización de conexiones persistentes, fijación de certificados autofirmados *Trust On First Use* (`SHA-256` TOFU) y protección anti-bloqueo **Safe Mode (*Dead Man's Switch*)** mediante `/system/scheduler` a 60 segundos.
- **Inventario Georreferenciado e Importador Masivo CSV:** Autodescubrimiento de hardware RouterBOARD, mapa interactivo gratuito con **Leaflet + OpenStreetMap** y asistente de importación CSV en 2 etapas (`dry-run` y `commit`).
- **Consola WebFig de Doble Capa (RouterOS v7.1+):**
  - **Capa 1 Especializada:** Interfaces, diagnóstico óptico **SFP/SFP+ DDM** (`dBm`), VLANs, Bridges, WireGuard, IP/Routes ECMP, DHCP Leases, Firewall con reordenamiento *Drag & Drop* + teclado accesible (`Alt+Up`/`Alt+Down`), BGP/OSPF v7, PPPoE Active, Simple Queues, System y Tools en vivo (Ping, Traceroute, Torch, Log).
  - **Capa 2 Universal:** Inspector dinámico de esquemas y CRUD autogenerado para el resto de submenús `/rest/*` de RouterOS v7 (MPLS, ZeroTier, Containers, CAPsMAN, SNMP, Certificates).
- **Interfaz Vue 3 de Alta Densidad Técnica y Alto Rendimiento (WCAG 2.1 AA):**
  - Sistema de diseño con 3 temas nativos (`dark` *Tactical NOC Cyan*, `light` de campo y `noc-high-contrast` para pantallas de monitoreo), tipografía numérica `tabular-nums`, stores con `shallowRef` y buscador global `Ctrl + K`.
  - **Densidad Dual Adaptativa y *Virtual Scrolling* en Tablas (`RgDataTable.vue`):** Filas compactas de `32px` estilo WinBox en PC (`>= 1024px`) con insignias `[D]`/`[X]`/`[I]`/`[R]`, modo táctil de `44px` en móvil/tablet (`< 1024px`) y virtualización del DOM para tablas mayores a 100 filas.
  - **Navegación Multi-Pestaña con Memoria (`<KeepAlive :max="5">`):** Conservación en RAM de filtros y estados al alternar entre vistas internas de un router, más barra de navegación inferior fija en móviles.
- **Gráficas Efímeras Estilo WinBox (`TelemetryRingBuffer` + `<canvas>` 2D):** Multiplexor WebSocket bajo demanda (`SCARD >= 1`), buffer circular en memoria RAM del navegador (hasta 5,400 puntos / 3 horas a 1 tick cada 2s) renderizado con `requestAnimationFrame` y cero almacenamiento histórico en base de datos.
- **Gobernanza Operativa (*Maker-Checker*), Backups Diff Git y Acciones Masivas:**
  - Interceptor de las 7 categorías críticas con segregación estricta de funciones (`maker != checker`).
  - Respaldos `.rsc` nocturnos/manuales con deduplicación `SHA-256`, retención de 30 días y comparador visual lado a lado estilo Git (`unified_diff`) contra respaldos previos o contra el estado `LIVE`.
  - Plantillas (*Golden Configs*), trabajos masivos multi-router y actualizador centralizado de RouterOS v7 con pre-backup obligatorio.
- **Alertas Multi-Canal *Zero-Storage* y Wallboard NOC:** Máquina de estados efímera en KeyDB (~200 bytes/router), respeto de ventanas de mantenimiento y despacho a Telegram Bot, Correo SMTP, Webhooks firmados (`HMAC-SHA256`) y pantalla NOC 24/7.

### Security (Seguridad Criptográfica y DevSecOps)
- **Modelo *Split-Credential* y Bóveda `AES-256-GCM`:** Credenciales API cifradas con `AAD` (`tenant_id|router_id`), rotación transaccional automática de claves de 32 caracteres y revelación restringida con **Step-Up Auth (2FA TOTP en vivo)** y autodestrucción en memoria a los 30 segundos.
- **Sesiones Blindadas y *Kill-Switch* en Vivo:** Contraseñas con `Argon2id`, cookies `__Host-` (`HttpOnly; Secure; SameSite=Strict`), protección `X-CSRF-Token` (`HMAC-SHA256`), detección de robo de Refresh Token en KeyDB y expulsión instantánea de sesiones activas.
- **Bitácora Forense Inmutable WORM (`audit_logs`):** Trigger en PostgreSQL que impide `UPDATE`/`DELETE`/`TRUNCATE`, cadena criptográfica `SHA-256` (`prev_record_hash`), sanitización automática `[REDACTED]` y verificador matemático de integridad para el rol `AUDITOR`.
- **Imágenes de Producción Endurecidas (Non-Root):** Contenedores multi-stage auditados con Trivy (`HIGH,CRITICAL = 0`), desactivación de Swagger/ReDoc en producción (`ROSGRID_ENV=production`), bloqueo de scripts de post-instalación en `.npmrc` (`ignore-scripts=true`) y omisión deliberada de terminales interactivas SSH/Telnet para preservar la trazabilidad WORM y el control RBAC.
