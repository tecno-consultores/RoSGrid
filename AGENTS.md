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
   - **Supreme Directive:** Autonomous creation of ALL test pyramid layers (Backend unit `>=95%`, Frontend Vitest, real PostgreSQL Alembic verification, Front-Back contracts, Karate Labs API BDD & UI BDD) and **autonomous continuous documentation sync** across `specs/`, `docs/`, `CHANGELOG.md`, `ROADMAP.md`, and `TESTING.md` without waiting for user prompts.

2. [secure_development_and_testing_guidelines.md](file:///.agents/rules/secure_development_and_testing_guidelines.md):
   - **Anti-Mock Blindness:** ORM changes (`src/models/`) require immediate versioned Alembic migrations verified in PostgreSQL (`\d <table>`).
   - **Security-by-Design:** Forced PostgreSQL RLS per tenant, anti-SSRF URL validation (`validate_router_target_url`), AES-256-GCM Vault cryptography, HMAC-SHA256 CSRF protection, and mandatory `Idempotency-Key` headers.
   - **Visual Geometry (Anti-JSDOM):** JSDOM does not calculate layout or bounding boxes. Validate DOM tree order and inspect viewports in real browser sessions to prevent sticky footer/modal overlap.

3. [frontend_parity_and_closure.md](file:///.agents/rules/frontend_parity_and_closure.md):
   - **Terminal ↔ Frontend Parity:** Zero console-only actions or orphan API endpoints without a matching Vue 3 interface.
   - **Closure Protocol:** Full ephemeral Docker test suite execution, security scan, and doc sync before commit/push.

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
