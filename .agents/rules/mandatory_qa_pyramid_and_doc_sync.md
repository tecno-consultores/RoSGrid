# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Mandatory QA Pyramid & Autonomous Documentation Sync Directive

> **SUPREME DIRECTIVE FOR AI AGENTS & CONTRIBUTORS:**
> Never conclude a task, suggest commits, or finish execution turns without proactively fulfilling the following two non-negotiable requirements. Do not wait for user prompting.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. Mandatory Multi-Layer Test Pyramid (No-Mock Blindness)

Features are invalid without coverage across the full test pyramid:

| Test Layer | Location | Requirement |
| :--- | :--- | :--- |
| **1. Backend Unit** | `fastapi/tests/**/*.unit.py` | Coverage `>= 95%` (`pytest-cov`). Test nominal, edge, and error branches. |
| **2. Frontend Unit** | `vue3/src/**/*.unit.ts` | 100% pass rate in Vitest. Test composables, Pinia stores, and form validation. |
| **3. Real DB & Migration** | `fastapi/migrations/versions/` | **Anti-Mock Invariant:** Never validate ORM changes (`src/models/`) with `AsyncMock` alone. You MUST generate an Alembic migration and verify actual column types (`\d <table>`) and RLS in real PostgreSQL. |
| **4. Front-Back Contracts** | `fastapi/scripts/validar_comunicacion_front_back.py` | Run inside Docker `rosgrid_api_local`. Send the exact payload (multipart form or JSON) used by the UI and verify DB persistence. |
| **5. Karate Labs API BDD** | `fastapi/test/api_test.feature` & `examples/fastapi/test/` | Black-box Gherkin scenarios testing 401 unauth, 422 malformed payloads, and 200/201 success contracts. |
| **6. Karate Labs UI BDD** | `vue3/test/ui_business_flow.feature` & `examples/vue3/test/` | Real browser acceptance scenarios with Chrome CDP (button clicks, modal flows, navigation). |
| **7. Visual Geometry** | DOM Hierarchy & Viewport Layout | **Anti-JSDOM Blindness:** JSDOM does not render Flexbox/Grid boxes. Test DOM order and verify that sticky footers (`.login-footer`) or modals never overlap content. |

---

## 2. Autonomous & Continuous Documentation Sync

Whenever code is added, updated, or refactored, simultaneously update:

1. **`specs/`:** Update all affected domain specifications (`specs/03`, `specs/11`, `specs/20`, etc.).
2. **`docs/`:** Update operational manuals, security guides, and `docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md`.
3. **Monorepo Root:**
   - **`CHANGELOG.md`:** Document changes under `## [Unreleased]` (`Added`, `Fixed`, `Changed`).
   - **`ROADMAP.md`:** Update milestone checkpoints and sub-task statuses.
   - **`TESTING.md`:** Update test metrics, coverage percentages, and scenario counts.
   - **`README.md`:** Update if user-facing features, installation, or architecture change.

---

## 3. Pre-Commit Verification Gate

Before concluding any task:
```bash
./verificar-secretos.sh
./.agents/scripts/certify_task_completion.sh
```
Verify zero secret leaks, zero type errors, clean git tree, and all Docker containers healthy.
