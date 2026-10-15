# 🤝 Guía de Contribución y Estándar QA 11X (RoSGrid)

¡Gracias por tu interés en contribuir a **RoSGrid**! Este proyecto es Software Libre licenciado bajo **GNU GPL-3.0-only** y se rige estrictamente por el **Estándar Corporativo [QA 11X](https://github.com/tecno-consultores/qa-testing-blueprints)**.

Cualquier *Pull Request (PR)* debe superar todas las barreras automatizadas de seguridad, complejidad, accesibilidad y cobertura antes de ser fusionado.

---

## 1. Regla Cero: Ejecución 100% en Contenedores Docker

Para garantizar reproducibilidad absoluta y proteger el sistema operativo anfitrión:
- **Está prohibido** exigir instalaciones globales en el host (`pip install`, `npm install -g`, etc.) para correr linters o pruebas.
- Todas las validaciones del Backend (`./fastapi/`) y del Frontend (`./vue3/`) se ejecutan dentro de los contenedores efímeros declarados en `fastapi/docker-compose.qa.yml` y `vue3/docker-compose.qa.yml` mediante sus respectivos `Makefile`.

~~~bash
# Activar los hooks locales de Lefthook (Pre-Commit, Commit-Msg y Pre-Push)
./instalar-hooks.sh

# Auditar Dockerfiles, docker-compose y vulnerabilidades con Trivy
./auditar-infra.sh
~~~

---

## 2. Límites Arquitectónicos Innegociables

Antes de proponer una nueva funcionalidad, verifica que cumpla estas 5 reglas de arquitectura de RoSGrid:

1. **Prohibición de Terminales Interactivas Libres (SSH / Telnet / CLI sin filtro):** No se aceptarán PRs que abran sesiones interactivas crudas hacia los equipos MikroTik que permitan evadir el modelo *Split-Credential*, el flujo *Maker-Checker*, el *Safe Mode* o la bitácora inmutable WORM. Toda operación nueva sobre RouterOS v7 debe pasar por Capa 1 o por el Motor Universal de Capa 2 (`/webfig/layer2/*`).
2. **Aislamiento Multi-Tenant (`RLS`):** Cualquier tabla nueva en PostgreSQL 17 que almacene datos de un Tenant debe incluir `tenant_id` e implementar `ENABLE` y `FORCE ROW LEVEL SECURITY` en su migración de Alembic.
3. **Encabezado SPDX Obligatorio:** Todo archivo de código fuente (`.py`, `.ts`, `.vue`, `.sh`, `Dockerfile`) debe iniciar con el identificador de licencia:
   ~~~text
   SPDX-License-Identifier: GPL-3.0-only
   ~~~
4. **Esquemas Estrictos y Tipado Total:**
   - **Backend (`fastapi/`):** Todos los modelos de entrada en Pydantic v2 deben declarar `model_config = ConfigDict(extra="forbid")` y pasar `mypy --strict`.
   - **Frontend (`vue3/`):** Tipado estricto en TypeScript (`vue-tsc --noEmit`). Queda prohibido el uso de `any`.
5. **Accesibilidad (`WCAG 2.1 AA`) y Diseño de Alta Densidad:**
   - Toda vista o componente en `vue3/` debe usar las variables CSS de `src/assets/themes.css` (soportando los temas `dark`, `light` y `noc-high-contrast` con ratio de contraste `>= 4.5:1`), respetar la **Densidad Dual Adaptativa (`32px` en PC / `44px` en móvil)** y aplicar `font-variant-numeric: tabular-nums` en columnas numéricas, IPs y contadores.

---

## 3. Métricas de Calidad Exigidas (QA 11X)

| Ecosistema | Métrica / Herramienta | Umbral Mínimo Obligatorio | Comando en Docker |
| :--- | :--- | :--- | :--- |
| **Backend (FastAPI)** | Complejidad Ciclomática (`Radon`) | **Grado A (`CC <= 5` por función)** | `cd fastapi && make qa-lint` |
| **Backend (FastAPI)** | Seguridad Estática (`Bandit` + `Ruff`) | **0 errores / 0 vulnerabilidades** | `cd fastapi && make qa-lint` |
| **Backend (FastAPI)** | Cobertura Unitaria (`Pytest`) | **`>= 95%` real sobre `src/`** | `cd fastapi && make qa-unit` |
| **Backend (FastAPI)** | Pruebas de Mutación (`Mutmut`) | Ejecución sin mutantes críticos vivos | `cd fastapi && make qa-mutation` |
| **Frontend (Vue 3)** | Linter y Complejidad (`ESLint` + `SonarJS`) | **0 errores / Baja complejidad cognitiva** | `cd vue3 && make qa-lint` |
| **Frontend (Vue 3)** | Cobertura Unitaria (`Vitest`) | **`>= 95%` en lines, functions, branches, statements** | `cd vue3 && make qa-unit` |
| **Frontend (Vue 3)** | Accesibilidad E2E (`@axe-core/playwright`) | **0 violaciones WCAG 2.1 A / AA** | `cd vue3 && make qa-e2e` |
| **Frontend (Vue 3)** | Rendimiento (`Lighthouse CI`) | **Perf/SEO/BP `>= 90` y A11y `>= 95`** | `cd vue3 && make qa-perf` |

---

## 4. Convención de Mensajes de Commit (`Conventional Commits`)

Todos los commits son validados automáticamente por `commitlint.config.js`. Utiliza el formato:

~~~text
<tipo>(<alcance>): <descripción en minúsculas sin punto final>
~~~

**Tipos permitidos:**
- `feat`: Nueva característica en Backend o Frontend.
- `fix`: Corrección de un error.
- `security`: Mejora o parche de seguridad criptográfica, RBAC o RLS.
- `perf`: Optimización de rendimiento (WebSockets, RingBuffer, consultas SQL).
- `test`: Adición o ajuste de pruebas unitarias, mutación, BDD o E2E.
- `docs`: Cambios en `README.md`, `ROADMAP.md`, `TESTING.md` o manuales en `docs/`.
- `refactor`: Refactorización de código para reducir complejidad ciclomática sin alterar funcionalidad.
- `chore` / `ci`: Ajustes en `Makefile`, Docker o configuración de QA.

**Ejemplo válido:**
~~~text
feat(webfig-l1): agregar diagnostico optico sfp ddm con umbrales dbm
~~~

---

## 5. Limpieza antes de Hacer Push

Nunca subas al repositorio directorios autogenerados como `mutants/`, `htmlcov/`, `.coverage`, `dist/`, `node_modules/` ni `graphify-out/`. Antes de enviar tu PR, ejecuta los scripts de limpieza:

~~~bash
./fastapi/limpieza.sh
./vue3/limpieza.sh
~~~
