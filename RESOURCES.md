# 📚 Recursos Técnicos, Estándares e Imágenes Oficiales (RoSGrid)

Este documento centraliza las referencias técnicas, imágenes oficiales de Docker, estándares criptográficos y guías internas utilizadas en el desarrollo y operación de **RoSGrid**.

---

## 1. Documentación Interna del Repositorio

### Manuales Operativos y de Arquitectura (`docs/`)
- `docs/01_GUIA_DESPLIEGUE_Y_ENTORNO.md` — Variables `.env`, generación de llaves criptográficas, despliegue Docker Compose, auto-migración con `pg_advisory_lock` y compilación con `./build.sh`.
- `docs/02_PREPARACION_MIKROTIK_ROUTEROS_V7.md` — Configuración paso a paso de RouterOS v7.1+ (`www-ssl`, certificados autofirmados para TOFU, permisos API y funcionamiento del *Safe Mode*).
- `docs/03_MANUAL_ADMIN_MULTITENANT_Y_SEGURIDAD.md` — Gestión de empresas (Tenants), los 11 roles RBAC, matriz de permisos por router, Bóveda *Step-Up Auth* (30s) y *Kill-Switch*.
- `docs/04_MANUAL_OPERATIVO_WEBFIG_NOC_Y_BACKUPS.md` — Operación de Capa 1 y Capa 2, gráficas efímeras `RingBuffer`, *Maker-Checker*, comparador Diff `.rsc` estilo Git, importador CSV y Wallboard NOC.
- `docs/05_AUDITORIA_FORENSE_Y_ARQUITECTURA.md` — Guía del rol `AUDITOR`, verificación criptográfica WORM y diagramas de arquitectura AST generados con Graphify.

### Enciclopedia de Especificaciones (`specs/`)
- `specs/00` a `specs/08` — Gobernanza 11X, infraestructura Docker inmutable, esquema PostgreSQL 17 RLS/WORM, Redis 7, criptografía, RBAC de 11 roles y cliente RouterOS v7 TOFU/Safe Mode.
- `specs/09` a `specs/17` — Arquitectura Backend FastAPI, endpoints de Capa 1, motor universal de Capa 2, Maker-Checker, Backups Diff Git, WebSockets de telemetría efímera y Workers asíncronos.
- `specs/18` a `specs/23` — Arquitectura Frontend Vue 3 Zero-Trust, sistema de diseño táctico NOC (`WCAG 2.1 AA`), mapa OpenStreetMap (`Leaflet`), consola WebFig con `<KeepAlive :max="5">` y `TelemetryRingBuffer`.
- `specs/24` a `specs/29` — Suites de certificación del Estándar Corporativo **QA 11X**.

---

## 2. Catálogo de Imágenes Oficiales en Docker Hub (`sinfallas/*`)

| Imagen en Docker Hub | Rol en el Ecosistema RoSGrid |
| :--- | :--- |
| `sinfallas/rosgrid-backend:latest` | Imagen oficial inmutable de producción para `rosgrid-api` y `rosgrid-worker` (usuario no-root `10001`). |
| `sinfallas/rosgrid-frontend:latest` | Imagen oficial inmutable de producción para `rosgrid-ui` sobre Nginx endurecido no-root (`8080`). |
| `sinfallas/base-python-uv:3.13` | Imagen base de Python 3.13 + `uv` para desarrollo, construcción multi-stage y suite QA Backend. |
| `sinfallas/base-node-ionic:22` | Imagen base de Node 22 + `pnpm` para etapa builder de Frontend y validación estática/unitaria. |
| `sinfallas/karatelabs:latest` | Ejecutor de pruebas funcionales BDD Gherkin de caja negra para API y UI. |
| `sinfallas/remote-graphify:latest` | Extracción de grafos semánticos AST (`GRAPH_REPORT.md`) bajo el perfil `--profile graphify`. |

---

## 3. Documentación Oficial de MikroTik RouterOS v7+

- **RouterOS v7 REST API Oficial:** [https://help.mikrotik.com/docs/display/ROS/REST+API](https://help.mikrotik.com/docs/display/ROS/REST+API)
- **RouterOS v7 Routing (BGP / OSPF / Routing Filters):** [https://help.mikrotik.com/docs/display/ROS/Routing](https://help.mikrotik.com/docs/display/ROS/Routing)
- **Certificados TLS y Servicio `www-ssl`:** [https://help.mikrotik.com/docs/display/ROS/Certificates](https://help.mikrotik.com/docs/display/ROS/Certificates)
- **Diagnóstico Óptico SFP / SFP+ (DDM):** [https://help.mikrotik.com/docs/display/ROS/SFP](https://help.mikrotik.com/docs/display/ROS/SFP)

---

## 4. Estándares Técnicos, RFCs y Normativas Aplicadas

- **Estándar Corporativo QA 11X:** [https://github.com/tecno-consultores/qa-testing-blueprints](https://github.com/tecno-consultores/qa-testing-blueprints)
- **NIST SP 800-38D:** Especificación de cifrado autenticado `AES-256-GCM` con `AAD` utilizado en la bóveda `router_credentials_vault`.
- **RFC 9106:** Algoritmo `Argon2id` para almacenamiento seguro de contraseñas resistentes a ataques por GPU/ASIC.
- **RFC 6238:** *Time-Based One-Time Password (TOTP)* para autenticación multifactor y desafíos *Step-Up Auth*.
- **RFC 9562 (UUIDv7):** Identificadores únicos ordenables temporalmente para llaves primarias y cabeceras `Idempotency-Key`.
- **W3C WCAG 2.1 Nivel AA:** Directrices de accesibilidad web validadas automáticamente mediante `@axe-core/playwright`.
- **OpenStreetMap & Leaflet:** Cartografía libre utilizada para la georreferenciación de nodos sin dependencia de servicios propietarios de pago.

---

## 5. Laboratorio Recomendado para Pruebas (EVE-NG + MikroTik CHR)

Para validar RoSGrid en entornos de pre-producción se recomienda una topología en **EVE-NG** con al menos 3 nodos **MikroTik Cloud Hosted Router (CHR) v7.1+**:
1. **`R1-CORE-EVENG`:** Enrutador de borde con sesiones BGP e interfaces de subida ECMP.
2. **`R2-BORDE-EVENG`:** Enrutador de distribución con adyacencias OSPF, VLANs 802.1Q y reglas de Firewall/Mangle.
3. **`R3-BRAS-EVENG`:** Concentrador de última milla con servidor PPPoE activo, `Simple Queues` y perfiles de clientes.
