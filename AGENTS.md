# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# 🤖 AI Agent Directives & Technical Governance — RoSGrid

Welcome to the **RoSGrid** repository. All AI coding assistants (Google Antigravity, Claude, Hermes Agent, Cursor, etc.) and human developers must strictly adhere to the Level-11X corporate quality and security directives defined here and in `.agents/rules/`.

> **OUTPUT LANGUAGE CONSTRAINT:**
> Always interact with the user, provide status updates, explain reasoning, and write commit messages / user-facing documentation in Spanish.
>
> **TOKEN EFFICIENCY & LANGUAGE DESIGN:**
> All directives in `.agents/rules/` and skills in `.agents/skills/` are maintained in concise, high-density technical English to optimize token utilization (~35% reduction in context window) and ensure maximum logical adherence across LLMs (Google Antigravity, Claude, Hermes Agent, Cursor). All human-facing documentation (`specs/`, `docs/`, `CHANGELOG.md`, `ROADMAP.md`, `TESTING.md`) remains strictly in Spanish. See [.agents/README.md](file:///.agents/README.md) for full architectural rationale.

---

## 1. Active Rules in `.agents/rules/`

1. [mandatory_qa_pyramid_and_doc_sync.md](file:///.agents/rules/mandatory_qa_pyramid_and_doc_sync.md):
   - **Supreme Directive — Creación Obligatoria de Pruebas 11X:** Todo cambio o adición de código DEBE ir acompañado innegociablemente de sus pruebas correspondientes en todas las capas de la pirámide de calidad 11X, tomando como **blueprints canónicos obligatorios** los ejemplos provistos en `examples/` (`examples/fastapi/` y `examples/vue3/`). Incluye pruebas unitarias backend (`fastapi/tests/**/*.unit.py` con cobertura `>= 95%`), pruebas unitarias frontend (`vue3/src/**/*.unit.ts` Vitest 100% pass), verificación real de esquema PostgreSQL y Alembic, contratos de integración front-back, y escenarios BDD Karate Labs.
   - **Ejecución Obligatoria de Pruebas:** Es OBLIGATORIO ejecutar y aprobar la suite de pruebas completa en contenedores efímeros (`Rule Zero`) tras CADA tarea que cambie código antes de darla por finalizada.
   - **Sincronización Documental Continua Obligatoria:** Es OBLIGATORIO actualizar de forma autónoma y continua tras cualquier modificación de código:
     - Todos los manuales y guías técnicas afectadas en `docs/`.
     - Todas las especificaciones arquitectónicas afectadas en `specs/`.
     - El historial de cambios en `CHANGELOG.md` (bajo `## [Unreleased]`).
     - El control de hitos y sub-tareas en `ROADMAP.md`.
     - Las métricas y conteo de pruebas en `TESTING.md`.
     - La documentación en la raíz del repositorio (`README.md`, `INSTALL.md`, etc., cuando aplique).

2. [secure_development_and_testing_guidelines.md](file:///.agents/rules/secure_development_and_testing_guidelines.md):
   - **Anti-Mock Blindness:** ORM changes (`src/models/`) require immediate versioned Alembic migrations verified in PostgreSQL (`\d <table>`).
   - **Security-by-Design:** Forced PostgreSQL RLS per tenant, anti-SSRF URL validation (`validate_router_target_url`), AES-256-GCM Vault cryptography, HMAC-SHA256 CSRF protection, and mandatory `Idempotency-Key` headers.
   - **Visual Geometry (Anti-JSDOM):** JSDOM does not calculate layout or bounding boxes. Validate DOM tree order and inspect viewports in real browser sessions to prevent sticky footer/modal overlap.

3. [frontend_parity_and_closure.md](file:///.agents/rules/frontend_parity_and_closure.md):
   - **Terminal ↔ Frontend Parity:** Zero console-only actions or orphan API endpoints without a matching Vue 3 interface.
   - **Closure Protocol & Mandatory Git Push:** Creación y ejecución de pruebas en Docker efímero, sincronización obligatoria de `docs/`, `specs/`, `CHANGELOG.md`, `ROADMAP.md`, `TESTING.md` y `README.md`, escaneo de secretos y publicación forzada a Git (`git add`, `git commit` y `git push`).

4. [continuous_agent_evolution.md](file:///.agents/rules/continuous_agent_evolution.md):
   - **Autonomous Evolution of `.agents/`:** Proactively update rules, skills, and automation scripts whenever discovering an improvement opportunity, unhandled edge case, procedure automation, or token optimization without waiting for user prompting.

---

## 2. Rule Zero: Ephemeral Docker Execution

**NEVER** execute tests, migrations, linters, or operational scripts directly on the host machine (`Ubuntu`). All executions must occur inside the project's ephemeral Docker containers (`docker-compose.qa.yml`, `docker-compose.prod.local.yml`, and `Makefile`).

---

## 3. Skills Catalog in `.agents/skills/`

1. `rosgrid-noc-operator`: NOC Operator & Autonomous Diagnostics for MikroTik RouterOS v7 via MCP (`/api/v1/mcp`) with 7 SOP Playbooks and 20 tools.
2. `qa-11x-docker-certifier`: QA 11X Corporate Standard certifier in ephemeral Docker (coverage `>= 95%`, SonarJS, Karate Labs, mutation testing).
3. `mikrotik-webfig-safemode`: RouterOS v7 REST API domain rules, native flags, 60s Safe Mode, and 30s Step-Up Auth Vault.
4. `vue3-wcag-tactical-ui`: WinBox-style high-density Vue 3 + TypeScript architecture (Tactical NOC Cyan), virtual scrolling, and WCAG 2.1 AA compliance.
5. `docker-trivy-keydb-hardening`: Docker container hardening (Trivy HIGH/CRITICAL = 0), Multi-Threaded KeyDB in-memory engine, and backend performance.
6. `graphify-docs-api-writer`: Technical authoring for operations manuals, Mermaid architecture, REST/WebSockets API specs, and AI MCP integration guides.

---

## 4. Automation Scripts in `.agents/scripts/`

- `verify_alembic_orm_parity.py`: Automated parity validator between SQLAlchemy ORM models and Alembic migrations (detects schema drift).
- `certify_task_completion.sh`: End-to-end certification gate enforcing secret scanning, ORM parity, front-back contracts, and documentation sync.

---

## 5. Mandatory Git Publication Directive & Task Closure Gate

> **INNEGOCIABLE:** Tras **CADA** tarea o solicitud del usuario que modifique, añada o corrija código fuente (`fastapi/`, `vue3/`, scripts o configuraciones), el agente de IA **DEBE** ejecutar de forma autónoma el siguiente protocolo de 7 pasos antes de concluir su turno:
>
> 1. **Creación Obligatoria de Pruebas 11X:** Crear o ampliar las pruebas unitarias e integración en `fastapi/tests/` y `vue3/src/`, empleando obligatoriamente los blueprints y patrones de `examples/` (`examples/fastapi/` y `examples/vue3/`).
> 2. **Ejecución Obligatoria de Pruebas:** Ejecutar la suite de pruebas completa en contenedores Docker efímeros (`Rule Zero`), certificando cobertura `>= 95%`, 100% de aserciones aprobadas y 0 errores de tipado/linting (`ruff`, `mypy`, `eslint`, `vue-tsc`).
> 3. **Sincronización Documental Obligatoria:** Actualizar incondicionalmente todos los archivos afectados en:
>    - `docs/` (manuales operativos, guías y especificación de API REST/WebSockets).
>    - `specs/` (especificaciones arquitectónicas de dominio).
>    - `CHANGELOG.md` (sección `## [Unreleased]`).
>    - `ROADMAP.md` (estado de hitos y sub-tareas).
>    - `TESTING.md` (métricas de aseguramiento y conteo de pruebas).
>    - Raíz del repositorio (`README.md`, `INSTALL.md`, etc., cuando aplique).
> 4. **Escaneo de Secretos y Paridad:** Ejecutar `./verificar-secretos.sh` y certificar paridad ORM con PostgreSQL.
> 5. **Indexación de Cambios:** Registrar todas las modificaciones con `git add .`.
> 6. **Confirmación Semántica:** Crear el commit siguiendo Conventional Commits estrictamente en español: `git commit -m "<tipo>(<ámbito>): <descripción_en_español>"`.
> 7. **Publicación Remota Inmediata:** Publicar en el repositorio remoto con `git push origin <rama_actual>`.
>
> **Bajo ninguna circunstancia** el agente debe finalizar una respuesta con modificaciones de código pendientes de confirmar (*uncommitted changes*) ni con documentación desfasada en el árbol de trabajo.

