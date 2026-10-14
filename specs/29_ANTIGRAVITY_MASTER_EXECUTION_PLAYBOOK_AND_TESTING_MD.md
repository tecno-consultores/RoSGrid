# 29 — PLAYBOOK MAESTRO DE EJECUCIÓN SECUENCIAL PARA ANTIGRAVITY Y PLANTILLA VIVA TESTING.md (RoSGrid)

**\[DIRECTIVA DE SISTEMA FINAL PARA ANTIGRAVITY\]:** Este documento es tu hoja de ruta operativa paso a paso para construir, integrar y certificar **RoSGrid** desde cero hasta producción cumpliendo al 100% con el **Estándar QA 11X**. No avances al siguiente hito si el hito actual no ha superado su compuerta de validación efímera (Gate 11X).




## **1. Secuencia Maestra de Ejecución por Hitos (Step-by-Step Playbook)**

### **Hito 0: Preparación del Monorepo, Licencia GPLv3, Hooks y Fusión Quirúrgica 11X**

1. **Lectura de Gobernanza:** Lee 00\_MASTER\_INDEX\_AND\_11X\_GOVERNANCE.md y 01\_DOCKER\_INFRASTRUCTURE\_AND\_IMMUTABLE\_IMAGES.md.

2. **Estructura Base y Licencia:**

   - Crea el árbol de carpetas (fastapi/, vue3/, docs/qa/, docs/specs/).

   - Crea LICENSE (GPL-3.0-only), .env.example, docker-compose.yml, lefthook.yml, commitlint.config.js, instalar-hooks.sh y auditar-infra.sh.

3. **Fusión Quirúrgica No Destructiva:**

   - En fastapi/: Fusiona pyproject.toml, tox.ini, Makefile, docker-compose.qa.yml y .gitignore según los documentos 09 y 24.

   - En vue3/: Fusiona package.json, .npmrc, vitest.config.ts, stryker.conf.json, playwright.config.ts, lighthouserc.js, Makefile, docker-compose.qa.yml y .gitignore según los documentos 18, 27 y 28.

4. **Activación del Paso 0 (Graphify MCP):**

   - Levanta el contenedor graphify (--profile graphify) e ingiere las configuraciones estrictas locales antes de escribir código de negocio.

5. **Gate 0 (Infraestructura IaC):**

   - Ejecuta ./auditar-infra.sh (Trivy IaC + FS) y verifica Exit Code 0.




### **Hito 1: Construcción del Núcleo Backend, Base de Datos RLS, Redis y Seguridad (Fases 1 y 2 Backend)**

1. **Lectura Obligatoria:** Lee los documentos 02, 03, 04, 05, 06, 07, 09 y 10.

2. **Implementación en fastapi/src/:**

   - Crea main.py exponiendo /metrics (prometheus-fastapi-instrumentator) y /health.

   - Crea scripts/entrypoint.sh con auto-migración Alembic protegida por pg\_advisory\_lock.

   - Crea los modelos SQLAlchemy 2.0 y las 3 migraciones de Alembic (Tenants, Users, 11 Roles, RLS, Inventario, Bóveda AES-256-GCM, Ventanas de Mantenimiento, Maker-Checker, Backups, Plantillas, Bulk Jobs y audit\_logs con trigger WORM inmutable).

   - Crea los motores en core/ (config.py, crypto.py, csrf.py, security\_headers.py, audit.py) y redis\_layer/ (idempotency.py, sessions.py, zero\_metrics\_monitor.py).

   - Crea el motor RBAC de 11 roles y el clasificador Maker-Checker (rbac/).

   - Crea los endpoints de Auth Multi-Tenant + 2FA TOTP, Tenants, Usuarios, Permisos por Equipo y el **Kill-Switch** de sesiones en vivo.

3. **Pruebas Unitarias del Hito 1 (fastapi/tests/):**

   - Escribe test\_crypto\_aes\_gcm\_argon2.unit.py, test\_csrf\_and\_cookies.unit.py, test\_security\_headers.unit.py, test\_immutable\_audit\_hashchain.unit.py, test\_idempotency\_middleware.unit.py, test\_sessions\_and\_killswitch.unit.py, test\_rbac\_11\_roles\_matrix.unit.py y test\_auth\_and\_2fa\_endpoints.unit.py.

4. **Gate 1 (Backend Core 11X):**

   - Ejecuta en fastapi/: make qa-lint && make qa-unit && make qa-mutation.

   - Verifica cobertura \>= 95%, complejidad Radon CC \< C (MI == A) y 0 mutantes sobrevivientes.




### **Hito 2: Conector RouterOS v7 (TOFU SSL + Safe Mode), Inventario, Bóveda Step-Up y WebFig Capa 1/Capa 2 (Fases 3, 4 y 5 Backend)**

1. **Lectura Obligatoria:** Lee los documentos 08, 11, 12, 13, 14 y 15.

2. **Implementación en fastapi/src/:**

   - Construye mikrotik/ssl\_tofu.py, mikrotik/client.py, mikrotik/safemode.py (Dead Man's Switch con /system/scheduler) y mikrotik/normalizers.py.

   - Construye los endpoints de Inventario, Importador CSV en 2 pasos (dry-run y commit), Bóveda con *Step-Up Auth* de 30s (exclusiva para SUPERADMIN\_GLOBAL y TENANT\_ADMIN), Rotación automática de contraseñas API y Ventanas de Mantenimiento.

   - Construye todos los endpoints de **WebFig Capa 1** (Interfaces, SFP DDM, VLAN, Bridge, WireGuard, WiFi, IP/IPv6 con protección anti-suicidio www-ssl, Firewall con reordenamiento Drag & Drop, Routing BGP/OSPF/BFD, PPPoE/Queues, System y Tools de diagnóstico en vivo).

   - Construye el **Motor Dinámico Universal WebFig Capa 2** (/webfig/layer2/\*).

3. **Pruebas Unitarias del Hito 2 (fastapi/tests/):**

   - Escribe test\_ssl\_tofu\_pinning.unit.py, test\_rest\_client\_v7.unit.py, test\_safemode\_deadman\_switch.unit.py, test\_inventory\_csv\_and\_vault.unit.py, test\_webfig\_layer1\_endpoints.unit.py y test\_webfig\_layer2\_universal.unit.py usando routeros\_v7\_payloads.py.

4. **Gate 2 (Backend WebFig 11X):**

   - Ejecuta en fastapi/: make qa-lint && make qa-unit && make qa-mutation.




### **Hito 3: Operaciones Avanzadas, Backups/Diff Git, WebSockets Efímeros, Workers de Alerta y Certificación Total Backend (Fase 6 Backend)**

1. **Lectura Obligatoria:** Lee los documentos 16, 17 y 26.

2. **Implementación en fastapi/src/:**

   - Construye los endpoints de Bandeja Maker-Checker, Backups .rsc/.backup con deduplicación SHA-256 (30 días) y comparador **Diff estilo Git**, Plantillas (*Golden Configs*), Acciones Masivas Multi-Router, Actualizador centralizado de RouterOS v7 y Consola de Auditoría Inmutable.

   - Construye los 2 canales WebSocket (/ws/v1/routers/\{router\_id\}/live-telemetry y /ws/v1/tenant/events) y los 4 workers en segundo plano (Monitor *Zero-Storage*, Despachador de Alertas a Telegram/SMTP/Webhook/NOC, Backup Nocturno y Rotación de Bóveda).

3. **Pruebas Unitarias, Contratos, BDD, DAST y Caos (fastapi/):**

   - Escribe test\_backups\_diff\_and\_bulk\_ops.unit.py, test\_zero\_metrics\_state\_machine.unit.py y test\_websockets\_multiplexer.unit.py.

   - Configura fastapi/test/api\_test.feature y fastapi/locustfile.py.

4. **Gate 3 (Certificación 11X Completa del Backend):**

   - Ejecuta make qa-all.

   - Levanta api y ejecuta Schemathesis, Karate Labs, OWASP ZAP Baseline y el perfil --profile chaos (Pumba + Locust + Prometheus).

   - Actualiza fastapi/TESTING.md.




### **Hito 4: Construcción del Frontend Vue 3, Sistema de Diseño, Inventario OSM y Consola WebFig (Fases 1 a 5 Frontend)**

1. **Lectura Obligatoria:** Lee los documentos 18, 19, 20, 21, 22, 23, 27 y 28.

2. **Implementación en vue3/src/:**

   - Construye httpClient.ts (interceptores CSRF, Idempotency-Key UUIDv7, Refresh Token y 202 Accepted Maker-Checker).

   - Construye los 6 stores de Pinia y la clase TelemetryRingBuffer\<T\> (5400 puntos en RAM para 3 horas de gráficas en vivo que se reinician al salir).

   - Construye el sistema de diseño (themes.css con ratios WCAG 2.1 AA, RgDataTable.vue con Drag & Drop accesible, RgCommandPalette.vue Ctrl + K, RgSafeModeBanner.vue, RgStepUp2FAModal.vue y RgResponsiveShell.vue para Móvil/Tablet/Escritorio).

   - Construye todas las vistas: Login Multi-Tenant + 2FA QR, Gestión de Tenants/Usuarios/Matriz de Routers, Panel de Sesiones Activas (*Kill-Switch*), Inventario con Mapa **Leaflet + OpenStreetMap (OsmRouterMap.vue)**, Asistente CSV, Modal de Bóveda *Step-Up* (30s), Consola WebFig (Dashboard en vivo + Capa 1 + Capa 2), Bandeja Maker-Checker, Comparador Diff Git (.rsc), Acciones Masivas/Updates, **Wallboard NOC** y Consola del **Auditor**.

3. **Gate 4 (Certificación 11X Completa del Frontend):**

   - Ejecuta en vue3/:

     - make qa-lint (0 errores en npm audit, vue-tsc, prettier y eslint con sonarjs + security).

     - make qa-unit (Vitest \>= 95% en lines, functions, branches y statements).

     - make qa-mutation (Stryker sin mutantes críticos sobrevivientes).

     - make qa-perf (Lighthouse CI: Performance \>= 0.90, Accessibility \>= 0.95, Best-Practices \>= 0.90, SEO \>= 0.90).

     - make qa-e2e (Playwright + @axe-core/playwright con **0 violaciones WCAG 2.1 AA** y snapshots visuales deterministas).

     - make qa-bdd (Karate UI).

   - Actualiza vue3/TESTING.md y el TESTING.md de la raíz del proyecto.




## **2. Plantilla Obligatoria de Bitácora Viva (TESTING.md)**

Por ley innegociable del Estándar 11X (AI\_MASTER\_PROMPT.md Regla 5), AntiGravity DEBE mantener actualizado el archivo TESTING.md en la raíz del repositorio con la siguiente estructura exacta:


\# 🛡️ Bitácora Viva de Calidad y Certificación 11X — RoSGrid


\*\*Licencia:\*\* GPL-3.0-only  


\*\*Estándar Aplicado:\*\* QA Testing Blueprints (Nivel 11X)


\#\# 1. Resumen de Flujos de Negocio Certificados


1. \*\*Aislamiento Multi-Tenant y Seguridad Split-Credential:\*\*


   - Login en 2 pasos (\`tenant\_slug\` + credenciales Argon2id + 2FA TOTP obligatorio).


   - Emisión de cookies \`\_\_Host-rg\_at\` y \`\_\_Host-rg\_rt\` (\`HttpOnly; Secure; SameSite=Strict\`) + protección \`X-CSRF-Token\` (HMAC-SHA256).


   - Políticas PostgreSQL \*Row-Level Security (RLS)\* activas en todas las tablas del dominio.


2. \*\*Matriz RBAC (11 Roles), Segmentación por Equipo y Kill-Switch en Tiempo Real:\*\*


   - Evaluación declarativa de los 11 perfiles cruzada con \`user\_router\_permissions\`.


   - Revocación instantánea de sesiones activas en Redis y cierre forzoso de WebSockets (\`SESSION\_KILLED\`).


3. \*\*Inventario MikroTik RouterOS v7+, Bóveda AES-256-GCM (\*Step-Up Auth\* 30s) y Pinning SSL TOFU:\*\*


   - Alta individual e importación masiva por CSV en 2 pasos (\*Dry-Run\* + ejecución).


   - Verificación de huella SHA-256 de certificados autofirmados (TOFU) y rotación automática de claves API.


   - Revelación de claves restringida a los 2 roles superiores con validación TOTP en vivo y autodestrucción en memoria a los 30s.


4. \*\*Consola Centralizada WebFig (Capa 1 + Capa 2), Safe Mode Anti-Bloqueo y Maker-Checker:\*\*


   - Módulos nativos Capa 1 (Interfaces, SFP DDM, VLAN, Bridge, WireGuard, WiFi, IP/IPv6, Firewall con Drag & Drop, Routing BGP/OSPF/BFD, PPPoE, Queues, System, Tools) y motor dinámico universal Capa 2.


   - Protocolo \*Dead Man's Switch\* vía \`/system/scheduler\` (reversión automática en 60s si un cambio corta la red).


   - Intercepción de las 7 categorías de acciones críticas hacia bandeja de aprobación \*Maker-Checker\*.


5. \*\*Gráficas Efímeras Estilo WinBox (Cero Métricas en DB), Alertas Zero-Storage y Backups Diff Git:\*\*


   - Multiplexor WebSocket en vivo + \`TelemetryRingBuffer\` en RAM del navegador (se reinicia al salir).


   - Máquina de estados en Redis (~200 bytes/router) con alertas a Telegram, SMTP, Webhook y Wallboard NOC.


   - Backups \`.rsc\`/\`.backup\` con deduplicación SHA-256, retención de 30 días, comparador visual Diff estilo Git y Auditoría Inmutable WORM (\`audit\_logs\`).


---


\#\# 2. Comandos Oficiales de Ejecución Efímera (Cero Instalación Local)


\#\#\# A. Auditoría Global de Infraestructura y Secretos (Trivy IaC + FS)


\`\`\`bash


./auditar-infra.sh

### **B. Ecosistema Backend (cd fastapi)**

\# Paso 0: Ingestión de Contexto IA (Graphify MCP)


docker compose -f docker-compose.qa.yml --profile graphify run --rm graphify bash -c "uvx graphifyy extract"


docker compose -f docker-compose.qa.yml --profile graphify up -d graphify


\# Suite Estándar (Lint + Mypy + Radon + Bandit + Pytest \>= 95% + Mutmut)


make qa-lint


make qa-unit


make qa-mutation


make qa-all


\# Pruebas Dinámicas, Contratos, BDD, DAST y Caos


docker compose -f docker-compose.qa.yml up -d api


docker compose -f docker-compose.qa.yml run --rm qa-backend bash -c "uv sync && uv run schemathesis run http://api:8000/openapi.json"


docker compose -f docker-compose.qa.yml run --rm karatelabs mvn clean test


docker compose -f docker-compose.qa.yml run --rm zap zap-baseline.py -t http://api:8000 -r zap-report.html


docker compose -f docker-compose.qa.yml --profile chaos up --abort-on-container-exit stress\_test


make clean-cache

### **C. Ecosistema Frontend (cd vue3)**

\# Paso 0: Ingestión de Contexto IA (Graphify MCP)


docker compose -f docker-compose.qa.yml --profile graphify run --rm graphify bash -c "uvx graphifyy extract"


docker compose -f docker-compose.qa.yml --profile graphify up -d graphify


\# Suite Completa (Lint + SonarJS + Vitest \>= 95% + Stryker + Lighthouse CI + Playwright/Axe + Karate UI)


make qa-lint


make qa-unit


make qa-mutation


make qa-perf


make qa-e2e


make qa-bdd


make qa-obs


make qa-all


make clean-cache

