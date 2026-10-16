---
name: 🚀 Plantilla de Pull Request Corporativa (RoSGrid)
about: Usa esta plantilla para someter cambios al ecosistema Multi-Tenant RoSGrid bajo el Estándar QA 11X.
---

## 📝 Descripción del Cambio
<!-- Describe claramente qué hace este Pull Request en RoSGrid, qué módulo afecta (Backend FastAPI, Frontend Vue 3, Conector RouterOS v7, MCP o Infraestructura) y por qué esta aproximación es segura. -->
<!-- Si este PR resuelve un Issue abierto, enlázalo aquí usando la sintaxis oficial (ej. "Closes #123" o "Fixes #123") -->


## 🔄 Tipo de PR
<!-- Marca con una 'x' entre los corchetes la opción que corresponda: [x] -->
- [ ] 🐛 Corrección de Bug (`fix`)
- [ ] 🚀 Nueva Funcionalidad WebFig / RBAC / MCP (`feat`)
- [ ] 📚 Actualización de Documentación en `docs/` (`docs`)
- [ ] 💅 Formateo / Estilo / Calidad (`style` / `chore`)
- [ ] ♻️ Refactorización / Optimización de Rendimiento (`refactor` / `perf`)

## ✅ Checklist de Calidad Corporativa (Estándar QA 11X — RoSGrid)
<!-- DEBES marcar todas las casillas aplicables comprobando que cumples nuestras políticas. Un PR que no cumpla esto será rechazado. -->
- [ ] **Ejecución 100% en Contenedores:** Todas las pruebas y linters se ejecutaron dentro de `docker-compose.qa.yml` (`sinfallas/base-python-uv:3.13` y `sinfallas/base-node-ionic:22`). Cero instalaciones en el host.
- [ ] **Cobertura Innegociable (>= 95%):** He verificado que las pruebas unitarias pasan con al menos un **95.0% de cobertura** tanto en `pytest` como en `Vitest v8` (`lines`, `functions`, `branches`, `statements`).
- [ ] **Aislamiento y Mocking:** Las pruebas unitarias (`*.unit.py` / `*.unit.ts`) están 100% aisladas y no tocan PostgreSQL, KeyDB ni equipos MikroTik reales.
- [ ] **Complejidad Ciclomática y Tipado Estricto:** Validé Grado A en `radon` (`CC <= 5`, `MI >= B`), `mypy --strict` con 0 errores en Backend, y `vue-tsc --noEmit` + `eslint-plugin-sonarjs` con 0 errores en Frontend.
- [ ] **Seguridad Operativa MikroTik:** Los cambios mutables respetan el aislamiento RLS por Tenant, el interceptor **Maker-Checker** (`202 Accepted`), el motor **Safe Mode (60s)** y la bitácora inmutable **WORM (`audit_logs`)**.
- [ ] **Higiene de Entorno:** Ejecuté `./fastapi/limpieza.sh` y/o `./vue3/limpieza.sh` para purgar reportes temporales de cobertura o mutación antes del commit.
- [ ] **Historial Semántico:** Mis commits siguen estrictamente las reglas de `commitlint` con los scopes permitidos (`fastapi`, `vue3`, `docs`, `ci`, `global`).

## 📸 Evidencia de Ejecución (Logs / Screenshots)
<!-- Pega aquí el volcado de la terminal demostrando que la suite QA en el contenedor efímero fue exitosa y reportó >= 95% de cobertura. -->
~~~text
(Pega tus resultados de make qa-lint y make qa-unit aquí)
~~~
