# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Terminal ↔ Frontend Parity & Task Closure Protocol

> **CORE GOVERNANCE DIRECTIVE:**
> Applies to all AI agents and developers working on RoSGrid.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. Terminal ↔ Frontend Parity Invariants

1. **Zero Console-Exclusive Actions:** Any administrative, operational, or diagnostics action executable from the terminal (except initial unattended system bootstrap) MUST have an equivalent Vue 3 screen.
2. **Zero Orphan API Endpoints:** Every route defined under `fastapi/src/api/v1/` MUST be paired with a frontend interface enabling visual inspection, parameter configuration, and interactive verification.
3. **Bidirectional Audit Sync:** Maintenance CLI scripts issuing tokens or altering sessions MUST sync metadata into KeyDB/Redis (`issued_by_username: "CLI (Terminal)"`) so they are visible and revocable via `ActiveSessionsKillSwitchView.vue`.

---

## 2. Proactive Vulnerability Audit

Before exposing new endpoints or frontend views:

1. **User State Checks:** Ensure inactive (`is_active = False`) or locked (`is_locked = True`) accounts cannot generate tokens or trigger protected actions.
2. **Multi-Tenant Context:** Ensure every DB query executes within an active tenant context (`set_tenant_context`).
3. **Automated SAST:** Run Bandit (`bandit -r src/ -ll`) and dependency auditing in ephemeral Docker with 0 High/Medium alerts.
4. **Anti-XSS & Anti-CSRF:** In Vue 3, never bind unescaped dynamic HTML (`v-html`); in FastAPI, mandate CSRF tokens on mutation endpoints and strict SameSite cookies.

---

## 3. Mandatory Task Closure Protocol & Autonomous Git Publication

After **EVERY** task or turn that adds, edits, or removes code or configuration files, the AI agent **MUST** autonomously execute this protocol and publish to Git without waiting for user prompting:

1. **Mandatory 11X Test Creation (Blueprints in `examples/`):**
   - For backend mutations: add/update unit tests in `fastapi/tests/**/*.unit.py` and behavioral scenarios following `examples/fastapi/`.
   - For frontend mutations: add/update unit tests in `vue3/src/**/*.unit.ts` and scenarios following `examples/vue3/`.
2. **Full Ephemeral Docker Test Execution (`Rule Zero`):**
   - Backend: `docker compose -f docker-compose.qa.yml run --rm qa-backend uv run pytest tests/ --cov=src --cov-fail-under=95`
   - Frontend: `docker compose -f docker-compose.qa.yml run --rm qa-vue3 pnpm run test:unit` & `type-check` (100% pass, 0 type errors).
   - Linters: `ruff check`, `mypy --strict`, `eslint`, `prettier`.
3. **Autonomous & Mandatory Multi-Layer Documentation Sync:**
   - Update affected operational and technical manuals in `docs/` (including `docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md`).
   - Update affected specifications in `specs/`.
   - Update `CHANGELOG.md` under `## [Unreleased]`.
   - Update `ROADMAP.md` task checkpoints and deliverables.
   - Update `TESTING.md` metrics and counts.
   - Update `README.md` and root documentation when user-facing interfaces or architectures change.
4. **Secret & Parity Certification:**
   - Run `./verificar-secretos.sh` (0 secret leaks).
   - Run `./.agents/scripts/certify_task_completion.sh`.
5. **Mandatory Git Commit & Push:**
   - Run `git add .`
   - Create a commit following Conventional Commits in Spanish: `git commit -m "<tipo>(<ámbito>): <descripción_en_español>"`
   - Push immediately to remote: `git push origin <current_branch>`
   - **Never leave uncommitted or unpushed code changes** in the workspace at the end of a response.


