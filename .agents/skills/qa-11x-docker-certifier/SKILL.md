---
name: qa-11x-docker-certifier
description: >-
  QA 11X Corporate Standard certifier in ephemeral Docker containers. Enforces Rule Zero
  (zero host executions on Ubuntu), Cyclomatic/Cognitive Complexity Grade A, unit test coverage >= 95%,
  mutation testing, WCAG 2.1 AA accessibility, Lighthouse CI, and silent mode RAM conservation.
  Applies to milestone validations and RoSGrid Milestone 15.
---

# QA 11X Corporate Standard Certifier (Ephemeral Docker Execution)

This skill governs all tests, linters, audits, and cleanups in `fastapi/` and `vue3/`.
> **OUTPUT LANGUAGE CONSTRAINT:** Always communicate with the user and write final explanations in Spanish.

---

## 1. Rule Zero: Total Isolation in Docker Containers

- **STRICTLY FORBIDDEN:** Executing `pip`, `uv`, `pytest`, `ruff`, `mypy`, `npm`, `pnpm`, `vitest`, `stryker`, or `playwright` directly on the host machine (`Ubuntu`).
- Every validation command MUST execute inside the ephemeral containers defined in `fastapi/docker-compose.qa.yml` and `vue3/docker-compose.qa.yml` via monorepo `Makefile` targets (`make qa-lint`, `make qa-unit`, `make qa-mutation`, `make qa-e2e`, `make qa-perf`, `make qa-bdd`).
- Every new source file (`.py`, `.ts`, `.vue`, `.sh`, `Dockerfile`) MUST include the header:
  `SPDX-License-Identifier: GPL-3.0-only`

---

## 2. Strict QA 11X Approval Thresholds

| Ecosystem | Tool / Suite | Mandatory Gate | Container Command |
| :--- | :--- | :--- | :--- |
| **Backend (`fastapi/`)** | `Ruff` + `Mypy --strict` + `Bandit` | **0 errors / 0 vulnerabilities** | `cd fastapi && make qa-lint` |
| **Backend (`fastapi/`)** | `Radon` (Cyclomatic Complexity) | **Grade A (`CC <= 5`, `MI >= B`)** | `cd fastapi && make qa-lint` |
| **Backend (`fastapi/`)** | `Pytest` (Unit Coverage) | **`>= 95.0%` real coverage on `src/`** | `cd fastapi && make qa-unit` |
| **Backend (`fastapi/`)** | `Mutmut` / `Schemathesis` / `Karate` / `ZAP` | Zero contract failures or surviving critical mutants | `make qa-mutation` / `make qa-bdd` |
| **Frontend (`vue3/`)** | `vue-tsc --noEmit` + `ESLint` + `SonarJS` | **0 type errors / Low cognitive complexity** | `cd vue3 && make qa-lint` |
| **Frontend (`vue3/`)** | `Vitest` (`@vitest/coverage-v8`) | **`>= 95.0%` lines, functions, branches, statements** | `cd vue3 && make qa-unit` |
| **Frontend (`vue3/`)** | `Stryker Mutator` | Clean execution across critical business logic | `cd vue3 && make qa-mutation` |
| **Frontend (`vue3/`)** | `Playwright` + `@axe-core/playwright` | **0 WCAG 2.1 A/AA violations + Snapshots `<= 0.01`** | `cd vue3 && make qa-e2e` |
| **Frontend (`vue3/`)** | `Lighthouse CI` (`lhci autorun`) | **Perf/SEO/BP `>= 0.90` and Accessibility `>= 0.95`** | `cd vue3 && make qa-perf` |

---

## 3. Repository Hygiene & Silent Mode (IDE RAM Conservation)

1. **Mandatory Post-QA Cleanup:**
   - After running coverage or mutation tests, execute `./scripts/limpieza.sh` (or `make clean-cache`), purging `mutants/`, `htmlcov/`, `.coverage`, `.stryker-tmp/`, `playwright-report/`.
   - **Exception:** Retain `fastapi/graphify-out/GRAPH_REPORT.md` and `vue3/graphify-out/GRAPH_REPORT.md` when needed for Milestone 14 and Milestone 15.
2. **Silent Chat Mode:**
   - Do not dump verbose source code or raw terminal logs in the chat.
   - Write artifacts to disk, check `- [x]` boxes in `ROADMAP.md`, update metrics in `TESTING.md`, and report back with a concise markdown summary.
