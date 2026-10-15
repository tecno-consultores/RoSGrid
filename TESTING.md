# 🛡️ Bitácora Viva de Calidad y Certificación 11X — RoSGrid

**Licencia:** GPL-3.0-only  
**Estándar Aplicado:** QA Testing Blueprints (Nivel 11X)  
**Estado Actual:** Hito 0 Completado y Certificado con Gate 0 (Trivy IaC + FS Exit 0) — Listo para Ejecución del Hito 1 por AntiGravity.




## **1. Resumen de Flujos de Negocio Cubiertos por la Suite 11X**

Esta bitácora documenta los flujos críticos de negocio de **RoSGrid** y los comandos exactos de validación efímera que todo desarrollador o agente de IA (**AntiGravity**) debe ejecutar y mantener al cierre de cada hito:


1. **Aislamiento Multi-Tenant y Seguridad *Split-Credential*:**

   - Inicio de sesión en 2 pasos (tenant\_slug + credenciales con hash Argon2id + validación o enrolamiento 2FA TOTP).

   - Emisión de cookies \_\_Host-rg\_at y \_\_Host-rg\_rt (HttpOnly; Secure; SameSite=Strict) + validación criptográfica de X-CSRF-Token (HMAC-SHA256) e Idempotency-Key (UUIDv7) en Redis.

   - Aislamiento estricto por tenant\_id mediante políticas PostgreSQL *Row-Level Security (RLS)*.

2. **Matriz RBAC (11 Roles), Segmentación por Equipo y *Kill-Switch* en Tiempo Real:**

   - Evaluación declarativa de los 11 perfiles cruzada contra los permisos por equipo (user\_router\_permissions).

   - Revocación instantánea de sesiones activas en Redis y cierre forzoso de WebSockets (SESSION\_KILLED).

3. **Inventario MikroTik RouterOS v7+, Bóveda AES-256-GCM (*Step-Up Auth* 30s) y Pinning SSL TOFU:**

   - Alta individual e importación masiva por CSV en 2 pasos (*Dry-Run* + ejecución transaccional).

   - Captura y verificación de huella SHA-256 de certificados SSL autofirmados (TOFU) y rotación automática de contraseñas API.

   - Revelación de contraseñas restringida exclusivamente a los 2 roles más altos (SUPERADMIN\_GLOBAL y TENANT\_ADMIN) tras validar código 2FA TOTP en vivo, con autodestrucción en memoria a los 30 segundos.

4. **Consola Centralizada WebFig (Capa 1 + Capa 2), *Safe Mode* Anti-Bloqueo y *Maker-Checker*:**

   - Módulos nativos Capa 1 (Interfaces, diagnóstico óptico SFP DDM, VLAN, Bridge, WireGuard, WiFi, IP/IPv6 con protección anti-suicidio www-ssl, Firewall con Drag & Drop accesible, Routing BGP/OSPF/BFD, PPPoE, Queues, System, Tools) y motor dinámico universal Capa 2 (/rest/\*).

   - Protocolo *Dead Man's Switch* vía /system/scheduler (reversión autónoma en 60 segundos si un cambio interrumpe la comunicación con el MikroTik).

   - Intercepción automática de las 7 categorías de acciones críticas hacia la bandeja de aprobación *Maker-Checker* con segregación de funciones (requested\_by != reviewed\_by).

5. **Gráficas Efímeras Estilo WinBox (Cero Métricas en DB), Alertas *Zero-Storage* y Backups Diff Git:**

   - Multiplexor WebSocket en vivo + TelemetryRingBuffer en memoria RAM del navegador (capacidad de 3 horas a 1 tick cada 2s; se reinicia al salir de la vista sin almacenar series de tiempo en PostgreSQL).

   - Máquina de estados en Redis (~200 bytes por router) con despacho de alertas por transición de estado hacia Telegram Bot, Correo SMTP, Webhooks firmados y Wallboard NOC.

   - Backups automáticos y manuales (.rsc y .backup) con deduplicación SHA-256, retención de 30 días, comparador visual lado a lado estilo Git (Diff) y bitácora de Auditoría Inmutable WORM (audit\_logs).




## **2. Umbrales Innegociables de Aprobación ("Fail & Forbid")**

- **Cobertura de Pruebas Unitarias Aisladas:** \>= 95% tanto en Backend (pytest-cov) como en Frontend (Vitest v8 en lines, functions, branches y statements).

- **Complejidad Ciclomática y Deuda Técnica:**

  - Backend (fastapi/): radon cc --min C src/ vacío (ninguna función grado C o peor) y radon mi --min B src/ vacío (índice de mantenibilidad grado A).

  - Frontend (vue3/): eslint-plugin-sonarjs y eslint-plugin-security con 0 errores.

- **Pruebas de Mutación:** 0 mutantes críticos sobrevivientes en mutmut (Backend) y Stryker (Frontend).

- **Accesibilidad y Rendimiento UI:** 0 violaciones WCAG 2.1 A/AA en @axe-core/playwright, regresión visual pixel-perfect (maxDiffPixelRatio \<= 0.01) y Lighthouse CI con Performance \>= 0.90, Accessibility \>= 0.95, Best-Practices \>= 0.90 y SEO \>= 0.90.




## **3. Comandos Oficiales de Ejecución Efímera (Cero Instalación Local)**

**ADVERTENCIA:** Está estrictamente prohibido ejecutar pip install, npm install, pnpm install o docker build en la máquina host. Utiliza exclusivamente las metas de los Makefile y scripts detallados a continuación.

### **A. Barrera Global de Infraestructura y Hooks Locales (Raíz del Repositorio)**

\# 1. Inicializar hooks de Git locales (Lefthook)


./instalar-hooks.sh


\# 2. Ejecutar auditoría estática de infraestructura Docker e inventario de CVEs (Trivy)


./auditar-infra.sh

### **B. Ecosistema Backend (cd fastapi)**

\# Paso 0 (Obligatorio para Agentes IA antes de programar): Ingestión de Contexto MCP Graphify


docker compose -f docker-compose.qa.yml --profile graphify run --rm graphify bash -c "uvx graphifyy extract"


docker compose -f docker-compose.qa.yml --profile graphify up -d graphify


\# 1. Análisis Estático, Tipado Estricto (Mypy), Complejidad (Radon) y SAST (Bandit + Audit)


make qa-lint


\# 2. Pruebas Unitarias Aisladas con Mocking Estricto (Cobertura \>= 95%)


make qa-unit


\# 3. Pruebas de Mutación Backend (Mutmut)


make qa-mutation


\# 4. Pipeline Estándar Completo (Lint + Unit + Mutation)


make qa-all


\# 5. Validación de Contratos OpenAPI (Schemathesis), BDD (Karate Labs) y DAST (OWASP ZAP)


docker compose -f docker-compose.qa.yml up -d api


docker compose -f docker-compose.qa.yml run --rm qa-backend bash -c "uv sync && uv run schemathesis run http://api:8000/openapi.json"


docker compose -f docker-compose.qa.yml run --rm karatelabs mvn clean test


docker compose -f docker-compose.qa.yml run --rm zap zap-baseline.py -t http://api:8000 -r zap-report.html


\# 6. Profiling de CPU (Flamegraph py-spy) e Ingeniería del Caos (Pumba + Locust + Prometheus)


docker compose -f docker-compose.qa.yml exec -T api bash -c "py-spy record -o /app/profile.svg --pid 1 --duration 30"


docker compose -f docker-compose.qa.yml --profile chaos up --abort-on-container-exit stress\_test


\# 7. Limpieza de volúmenes y contenedores efímeros


make clean-cache

### **C. Ecosistema Frontend (cd vue3)**

\# Paso 0 (Obligatorio para Agentes IA antes de programar): Ingestión de Contexto MCP Graphify


docker compose -f docker-compose.qa.yml --profile graphify run --rm graphify bash -c "uvx graphifyy extract"


docker compose -f docker-compose.qa.yml --profile graphify up -d graphify


\# 1. Auditoría de CVEs, Type-Check (vue-tsc), Formateo (Prettier) y Linting (ESLint + SonarJS + Security)


make qa-lint


\# 2. Pruebas Unitarias Aisladas en JSDOM (Vitest \>= 95% en las 4 métricas)


make qa-unit


\# 3. Pruebas de Mutación Frontend (Stryker)


make qa-mutation


\# 4. Compilación de Producción y Auditoría Core Web Vitals / PWA (Lighthouse CI)


make qa-perf


\# 5. Regresión Visual Pixel-Perfect, E2E y Accesibilidad WCAG 2.1 AA (Playwright + @axe-core)


make qa-e2e


\# 6. Pruebas de Aceptación BDD de Caja Negra (Karate UI)


make qa-bdd


\# 7. Stack de Observabilidad Frontend en Vivo (Nginx Prometheus Exporter + Prometheus)


make qa-obs


\# 8. Pipeline Completo Frontend y Limpieza


make qa-all


make clean-cache




## **4. Registro de Progreso por Hitos (Actualizado por AntiGravity)**

| **Hito** | **Descripción** | **Cobertura Unitaria** | **Mutación** | **SAST / DAST / A11y** | **Estado** |
| - | - | :-: | :-: | :-: | :-: |
| **Hito 0** | Estructura Monorepo, Licencia GPLv3, Hooks y Fusión 11X | N/A | N/A | Trivy IaC + FS Aprobado (Exit 0) | ✅ Completado |
| **Hito 1** | Núcleo Backend, PostgreSQL RLS, Redis, Auth 2FA, RBAC y Kill-Switch | 97.89% (103/103 tests aislados) | Mutmut (1141 eliminados, 0 no testeados) | Bandit (0 issues) + Radon CC/MI (Grade A) + Pip-Audit (0 CVEs) | ✅ Completado (Gate 1 Superado) |
| **Hito 2** | Conector RouterOS v7 (TOFU + Safe Mode), Inventario, Bóveda y WebFig L1/L2 | >= 95% | Mutmut | Bandit + Radon A | ⏳ Pendiente (Requiere autorización) |
| **Hito 3** | Maker-Checker, Backups Diff Git, WebSockets, Alertas y Caos Backend | >= 95% | Mutmut | ZAP + Pumba/Locust | ⏳ Pendiente |
| **Hito 4** | Frontend Vue 3 Completo, Mapa OSM, RingBuffer WinBox, NOC y Auditor | >= 95% | Stryker | Axe 0 Viol. + LH >= 90 | ⏳ Pendiente |


