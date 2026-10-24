# 📚 Recursos Técnicos, Estándares e Imágenes Oficiales (RoSGrid)

Este documento centraliza las referencias técnicas, imágenes oficiales de Docker, estándares criptográficos y guías internas utilizadas en el desarrollo y operación de **RoSGrid**.

---

## 1. Documentación Interna del Repositorio

### Manuales Operativos, de Despliegue y Referencia de API (`docs/`)

- `docs/01_GUIA_DESPLIEGUE_Y_ENTORNO.md` — Variables `.env`, generación de llaves criptográficas, motor **KeyDB Multi-Hilo** predeterminado vs. perfil **DragonflyDB** de alta escala, despliegue Docker Compose, auto-migración con `pg_advisory_lock` y compilación con `./scripts/build.sh`.
- `docs/02_PREPARACION_MIKROTIK_ROUTEROS_V7.md` — Configuración paso a paso de RouterOS v7.1+ (`www-ssl`, certificados autofirmados para TOFU, permisos API y funcionamiento del *Safe Mode*).
- `docs/03_MANUAL_ADMIN_MULTITENANT_Y_SEGURIDAD.md` — Gestión de empresas (Tenants), los 11 roles RBAC, matriz de permisos por router, Bóveda *Step-Up Auth* (30s) y *Kill-Switch*.
- `docs/04_MANUAL_OPERATIVO_WEBFIG_NOC_Y_BACKUPS.md` — Operación de Capa 1 y Capa 2, gráficas efímeras `RingBuffer` sobre `<canvas>` 2D, *Maker-Checker*, comparador Diff `.rsc` estilo Git, importador CSV y Wallboard NOC.
- `docs/05_AUDITORIA_FORENSE_Y_ARQUITECTURA.md` — Guía del rol `AUDITOR`, verificación criptográfica WORM, ADR sobre la exclusión deliberada de terminal CLI/SSH libre y diagramas de arquitectura AST generados con Graphify.
- `docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md` — Especificación completa de todos los endpoints `/api/v1/*` (incluyendo `/api/v1/mcp`) y canales `/ws/v1/*` (cabeceras `X-CSRF-Token`, `Idempotency-Key`, payloads JSON y uso de `SERVICE_ACCOUNT`), supliendo a Swagger/ReDoc en producción.
- `docs/07_GUIA_INTEGRACION_IA_MCP_HERMES_Y_CLAUDE.md` — Manual técnico del servidor MCP protegido (`POST /api/v1/mcp` JSON-RPC 2.0 Streamable HTTP) para conectar **Hermes Agent** y **Claude**, con catálogo de las 8 Tools semánticas, flujo NOC autónomo 24/7 y gobierno Maker-Checker.

### Enciclopedia de Especificaciones (`docs/specs/`)

- `docs/specs/00` a `docs/specs/08` — Gobernanza 11X, infraestructura Docker inmutable, esquema PostgreSQL 17 RLS/WORM/BRIN, KeyDB/RESP, criptografía, RBAC de 11 roles y cliente RouterOS v7 TOFU/Safe Mode con pool TLS Keep-Alive.
- `docs/specs/09` a `docs/specs/17` — Arquitectura Backend FastAPI (`ORJSONResponse` + `uvloop`), endpoints de Capa 1, motor universal de Capa 2, Maker-Checker, Backups Diff Git, WebSockets de telemetría efímera y Workers asíncronos.
- `docs/specs/18` a `docs/specs/23` — Arquitectura Frontend Vue 3 Zero-Trust (`shallowRef`), sistema de diseño táctico NOC (`WCAG 2.1 AA` + *Virtual Scrolling*), mapa OpenStreetMap (`Leaflet`), consola WebFig con `<KeepAlive :max="5">` y `TelemetryRingBuffer` sobre `<canvas>` 2D.
- `docs/specs/24` a `docs/specs/29` — Suites de certificación del Estándar Corporativo **QA 11X**.
- `docs/specs/30_BACKEND_MCP_PROTECTED_ENDPOINT.md` a `docs/specs/35_FLEET_AUTOMATION_TOPOLOGY_L2_SYSLOG_AND_PROMETHEUS.md` — Especificaciones arquitectónicas de servidor MCP, despliegue distribuido, módulo ISP, suite corporativa, feature flags y automatización de flota.

---

## 2. Catálogo de Imágenes Oficiales y Motores en Memoria

| Imagen en Docker Hub / Registro | Rol en el Ecosistema RoSGrid |
| :--- | :--- |
| `sinfallas/rosgrid-backend:latest` | Imagen oficial inmutable de producción para `rosgrid-api` y `rosgrid-worker` (usuario no-root `10001`, `uvloop` + `orjson`). |
| `sinfallas/rosgrid-frontend:latest` | Imagen oficial inmutable de producción para `rosgrid-ui` sobre Nginx endurecido no-root (`8080`). |
| `eqalpha/keydb:alpine` | Motor en memoria **Multi-Hilo predeterminado** (`--server-threads 2`, ~35 MB RAM, licencia BSD-3-Clause). |
| `docker.dragonflydb.io/dragonflydb/dragonfly:latest` | Perfil opcional de **Alto Rendimiento** (*Shared-Nothing* `io_uring`) para flotas masivas ISP (> 300–500 routers). |
| `sinfallas/base-python-uv:3.15` | Imagen base de Python 3.15 + `uv` para desarrollo, construcción multi-stage y suite QA Backend. |
| `sinfallas/base-node-ionic:26` | Imagen base de Node 26 + `pnpm` para etapa builder de Frontend y validación estática/unitaria. |
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

- **Model Context Protocol (MCP) Specification:** Protocolo estándar abierto JSON-RPC 2.0 para la comunicación segura entre agentes LLM (Hermes, Claude) y servidores de contexto/herramientas ([modelcontextprotocol.io](https://modelcontextprotocol.io)).
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
