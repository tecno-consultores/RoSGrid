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

## 3. Mandatory Task Closure Protocol

Before marking tasks complete or pushing to GitHub:

1. **Full Ephemeral Docker Test Execution:**
   - Backend: `uv run pytest tests/ --cov=src` (coverage `>= 95%`).
   - Frontend: `npx vitest run` & `npx vue-tsc --noEmit` (100% pass, 0 type errors).
2. **Autonomous Documentation Sync:**
   - Update `specs/`, `docs/`, `CHANGELOG.md`, `ROADMAP.md`, and `TESTING.md`.
3. **Secret & Parity Certification:**
   - Run `./verificar-secretos.sh`.
   - Run `./.agents/scripts/certify_task_completion.sh`.
4. **Git Commit & Push:**
   - Follow Conventional Commits (`feat:`, `fix:`, `docs:`) and push to `origin/main`.
