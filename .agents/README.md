# 🤖 Carpeta `.agents/` — Gobernanza de Inteligencia Artificial y Reglas de Dominio (RoSGrid)

Bienvenido a la carpeta de configuración y gobernanza para **Agentes de Inteligencia Artificial** y **Desarrolladores Humanos** de RoSGrid.

Este directorio implementa el estándar abierto de gobernanza para agentes autónomos (Google Antigravity, Claude Code / Claude Desktop, Hermes Agent, Cursor, Windsurf), proporcionando el contexto técnico, las restricciones de seguridad y los playbooks operativos necesarios para mantener la plataforma en el estándar de calidad corporativa **Nivel 11X**.

---

## 📂 Estructura Real del Directorio

```text
.agents/
├── README.md                                         # Este documento explicativo
├── ACTIVE_TASK.md                                    # Diario de resiliencia y progreso en tiempo real (Invariante 11X)
├── proposals/                                        # Propuestas de evolución hacia qa-testing-blueprints
├── rules/                                            # Reglas y directivas de comportamiento forzadas (4 archivos activos)
│   ├── mandatory_qa_pyramid_and_doc_sync.md          # Pirámide de pruebas 11X, Karate Labs y sync documental conciso
│   ├── secure_development_and_testing_guidelines.md  # Anti-Mocks ciegos, RLS, SSRF, Vault, MCP Zero-Trust y anti-regresión
│   ├── frontend_parity_and_closure.md                # Paridad terminal-UI, temas dinámicos, mapas y compuerta de cierre
│   └── ground_truth_fixtures_and_negative_invariants.md # Fixtures trimodales RouterOS v7 e invariantes negativos
├── skills/                                           # Habilidades y Playbooks de dominio de RoSGrid (4 skills locales)
│   ├── rosgrid-noc-operator/                         # Operador NOC vía MCP (RouterOS v7.13+, 22 tools, 6 Maker-Checker)
│   ├── mikrotik-webfig-safemode/                     # Reglas de dominio MikroTik v7.13+, Safe Mode 60s y RingBuffer
│   ├── vue3-wcag-tactical-ui/                        # Arquitectura Vue 3 WinBox, WCAG 2.1 AA y Refactoring UI
│   └── graphify-docs-api-writer/                     # Redacción y mantenimiento de manuales y API specs con Graphify AST
└── scripts/                                          # Scripts de automatización y compuertas de calidad
    ├── verify_alembic_orm_parity.py                  # Auditoría estricta: modelos ORM vs migraciones Alembic
    ├── verify_json_no_duplicate_keys.py              # Auditoría estricta anti-colisión de claves duplicadas en JSON i18n
    ├── verify_topological_health.py                  # Auditoría estricta de salud topológica y límites de capas AST
    ├── inspect_blast_radius.py                       # Análisis de radio de impacto pre-refactorización (aristas entrantes)
    ├── verify_zero_orphan_vue_components.py          # Auditoría estricta: 100% de componentes Vue 3 con pruebas unitarias
    ├── verify_no_orphan_api_endpoints.py             # Auditoría bidireccional de paridad FastAPI <-> Vue 3 (0 rutas huérfanas)
    ├── verify_anti_silo_test_quality.py              # Auditoría estática anti-mocks ciegos de write_audit_log (Spec 83)
    ├── verify_roadmap_consistency.py                 # Verificador de consistencia entre ROADMAP.md y ACTIVE_TASK.md
    └── certify_task_completion.sh                    # Compuerta de certificación pre-commit automatizada (9 etapas)
```

---

## 🌐 Estrategia Lingüística y Optimización de Tokens (Inglés Técnico vs. Español Humano)

> **PREMISA DE DISEÑO:**  
> Las instrucciones destinadas al consumo interno de los modelos de IA (`rules/` y `skills/`) están redactadas en **inglés técnico compacto de alta densidad** (~35% de ahorro en ventana de contexto), mientras que toda la interacción con desarrolladores humanos, respuestas en el chat, commits y documentación del negocio (`docs/specs/`, `docs/`, `CHANGELOG.md`, `ROADMAP.md`, `TESTING.md`) se mantiene estrictamente en **español**.

---

## 📚 Fuente Canónica Oficial MikroTik RouterOS v7.13+

- **Portal Oficial de Documentación RouterOS v7:** [https://manual.mikrotik.com/docs/introduction/](https://manual.mikrotik.com/docs/introduction/)
- **Índice Abierto para LLMs (Fast Semantic Retrieval):** [https://manual.mikrotik.com/llms.txt](https://manual.mikrotik.com/llms.txt)
- **Referencia Canónica de Comandos CLI y REST API:** [https://manual.mikrotik.com/docs/cli-reference/](https://manual.mikrotik.com/docs/cli-reference/)

---

## 🚀 Cómo Ejecutar las Compuertas de Calidad

```bash
# Ejecutar compuerta integral de certificación 11X (9 etapas)
./.agents/scripts/certify_task_completion.sh

# Auditar paridad 100% de componentes Vue sin huérfanos
python3 ./.agents/scripts/verify_zero_orphan_vue_components.py

# Auditar paridad bidireccional de endpoints FastAPI <-> Vue 3
python3 ./.agents/scripts/verify_no_orphan_api_endpoints.py

# Auditar que no existen modelos ORM huérfanos sin migración Alembic
docker exec -t rosgrid_api_local python scripts/verify_alembic_orm_parity.py
```

Para el flujo completo de ejecución y cierre de tareas (`DOCS_ONLY`, `MICRO_CHANGE` y `FULL_11X`), consulta [`AGENTS.md`](../AGENTS.md).
