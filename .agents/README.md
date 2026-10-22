# 🤖 Carpeta `.agents/` — Gobernanza de Inteligencia Artificial y Reglas de Dominio (RoSGrid)

Bienvenido a la carpeta de configuración y gobernanza para **Agentes de Inteligencia Artificial** y **Desarrolladores Humanos** de RoSGrid.

Este directorio implementa el estándar abierto y emergente de la industria para agentes autónomos (Google Antigravity, Claude Code / Claude Desktop, Hermes Agent, Cursor, Windsurf, etc.), proporcionando el contexto técnico, las restricciones de seguridad y los playbooks operativos necesarios para mantener la plataforma en el estándar de calidad corporativa **Nivel 11X**.

---

## 📂 Estructura del Directorio

```text
.agents/
├── README.md                                         # Este documento explicativo
├── rules/                                            # Reglas y directivas de comportamiento forzadas
│   ├── mandatory_qa_pyramid_and_doc_sync.md          # Pirámide de pruebas multi-capa y sync documental
│   ├── secure_development_and_testing_guidelines.md  # Anti-Mocks ciegos, RLS forzado, SSRF y bóveda
│   ├── frontend_parity_and_closure.md                # Paridad terminal-UI y protocolo de cierre
│   └── continuous_agent_evolution.md                 # Evolución y actualización autónoma y continua de .agents/
├── skills/                                           # Habilidades y Playbooks de dominio
│   ├── rosgrid-noc-operator/                         # Operador NOC y diagnóstico autónomo vía MCP (RouterOS v7)
│   ├── qa-11x-docker-certifier/                      # Certificación 11X en Docker efímero (95% cobertura)
│   ├── mikrotik-webfig-safemode/                     # Reglas de dominio MikroTik v7, Safe Mode y RingBuffer
│   ├── vue3-wcag-tactical-ui/                        # Arquitectura Vue 3 WinBox, WCAG 2.1 AA y Lighthouse
│   ├── docker-trivy-keydb-hardening/                 # Endurecimiento Docker, Trivy = 0 y KeyDB multi-hilo
│   └── graphify-docs-api-writer/                     # Redacción de arquitectura, grafos AST y manuales
└── scripts/                                          # Scripts de automatización y compuertas de calidad
    ├── verify_alembic_orm_parity.py                  # Auditoría estricta: modelos ORM vs migraciones Alembic
    └── certify_task_completion.sh                    # Compuerta de certificación pre-commit automatizada
```

---

## 🌐 Estrategia Lingüística y Optimización de Tokens (Inglés Técnico vs. Español Humano)

> **PREMISA DE DISEÑO:**  
> Las instrucciones destinadas al consumo interno de los modelos de IA (`rules/` y `skills/`) están redactadas en **inglés técnico compacto de alta densidad**, mientras que toda la interacción con desarrolladores humanos, respuestas en el chat y documentación del negocio (`specs/`, `docs/`, `CHANGELOG.md`, `ROADMAP.md`, `TESTING.md`) se mantiene estrictamente en **español**.

### ¿Por qué las directivas de IA están en inglés?

1. **Economía de Tokens en la Ventana de Contexto ($\approx 35\%$ de Ahorro):**
   - Los tokenizadores de frontera basados en BPE (*Byte-Pair Encoding*, ej. Tiktoken, Gemini Tokenizer, Claude Tokenizer) dividen las palabras en español en una mayor cantidad de fragmentos o subtokens debido a sufijos, conjugaciones y menor frecuencia estadística en los corpus de entrenamiento masivo.
   - Redactar las reglas y habilidades en inglés técnico de alta densidad reduce drásticamente el consumo de tokens en el prompt de sistema en cada interacción, dejando mayor espacio disponible en el contexto para el código fuente del proyecto, esquemas de bases de datos y trazas de depuración.

2. **Menor Latencia y Mayor Velocidad de Respuesta:**
   - Menos tokens de entrada se traducen directamente en menor tiempo de procesamiento (Time-To-First-Token y tiempo de procesamiento por turno) en herramientas como Google Antigravity, Claude Code o Hermes Agent.

3. **Adherencia Semántica y Rigor Lógico Superior:**
   - La literatura técnica de redes (RFCs de IETF, BGP, OSPF, MikroTik REST API, IEEE 802.3, WCAG 2.1 AA) y los estándares de seguridad (OWASP, CIS Benchmark, RLS, AES-256-GCM) tienen su máxima densidad conceptual y precisión de alineación en inglés. Los modelos exhiben un cumplimiento de instrucciones (*instruction following*) más estricto y predecible al procesar directivas en este idioma.

4. **Garantía Inviolable de Salida en Español (`OUTPUT LANGUAGE CONSTRAINT`):**
   - Para garantizar que el desarrollador reciba siempre explicaciones claras y fluidas en su lengua materna, cada archivo en `.agents/rules/` y `.agents/skills/` incluye la directiva forzada:
     ```markdown
     > **OUTPUT LANGUAGE CONSTRAINT:**
     > Always communicate with the user, provide status updates, explain reasoning,
     > and write commit messages / user-facing documentation in Spanish.
     ```

---

## 🤝 Compatibilidad Multi-Agente

Esta carpeta **NO es exclusiva de una sola herramienta**. Ha sido diseñada bajo especificaciones estándar y portables:

1. **Google Antigravity:** Carga automáticamente las directivas en `rules/` y expone las habilidades en `skills/` en cada sesión de trabajo.
2. **Anthropic Claude Code / Claude Desktop:** Puede consumir los playbooks de `skills/rosgrid-noc-operator/` y leer `rules/` como System Prompt contextual. Incluye preconfiguración en `skills/rosgrid-noc-operator/configs/claude_desktop.json`.
3. **Hermes Agent (Nous Research):** Compatible nativo para agentes de terminal autónomos conectados al Model Context Protocol (MCP) de RoSGrid vía `skills/rosgrid-noc-operator/configs/hermes_agent.yaml`.
4. **Cursor / Windsurf / Copilot:** Las directivas de `rules/` y `AGENTS.md` en la raíz son leídas automáticamente como reglas de contexto para generación de código.
5. **Ingenieros y Desarrolladores Humanos:** Funciona como un catálogo centralizado de directivas ("guía de estilo viva") que explica exactamente cómo probar el sistema, qué trampas evitar (ej. mocks ciegos de base de datos) y cómo operar la flota de routers.

---

## 🔒 Seguridad y Versionado en Git

**¿Es seguro y recomendable versionar `.agents/` en GitHub?**
**Sí, es 100% recomendable y una práctica recomendada en ingeniería de software moderna:**
- **Cero Secretos:** Este directorio solo contiene directivas en Markdown, configuraciones de muestra (`.json`, `.yaml`) y scripts en Python/Bash. No contiene tokens de producción, contraseñas ni variables de entorno.
- **Reproducibilidad:** Permite que cualquier desarrollador que clone el repositorio obtenga inmediatamente un agente de IA calibrado y alineado con las reglas de RoSGrid, sin riesgo de que introduzca código roto, modelos sin migración o fallos de seguridad.
- **Auditoría Continua:** Cualquier script añadido a `.agents/scripts/` es auditado por `ShellCheck` y `verificar-secretos.sh` en el pipeline de CI/CD.

---

## 🚀 Cómo Usar las Automatizaciones

Para certificar localmente que una tarea cumple con todos los requisitos antes de hacer commit:

```bash
# Ejecutar compuerta integral de certificación 11X
./.agents/scripts/certify_task_completion.sh

# Auditar que no existen modelos ORM huérfanos sin migración
docker exec -t rosgrid_api_local python scripts/verify_alembic_orm_parity.py
```

---

## 📦 Protocolo de Cierre Obligatorio y Publicación en Git (`git commit & push`)

Por gobernanza innegociable de Nivel 11X, tras **CADA** tarea o solicitud que modifique, añada o corrija código fuente (`fastapi/`, `vue3/`, scripts o configuraciones), el agente de IA **DEBE** ejecutar de forma autónoma el siguiente protocolo:

1. **Creación Obligatoria de Pruebas 11X (Blueprints en `examples/`):**
   - Utilizar de forma obligatoria los ejemplos y patrones de `examples/fastapi/` (pytest, pytest-cov, pytest-mock, Karate Labs API BDD, mutmut, schemathesis) y `examples/vue3/` (Vitest, SonarJS, Stryker, Playwright e2e, @axe-core A11y, Karate Labs UI BDD).
   - Toda mutación de backend requiere pruebas en `fastapi/tests/**/*.unit.py` con cobertura `>= 95%`.
   - Toda mutación de frontend requiere pruebas en `vue3/src/**/*.unit.ts` con 100% pass en Vitest.
2. **Ejecución Obligatoria de Pruebas en Docker Efímero (`Rule Zero`):**
   - Ejecutar la suite en contenedores efímeros (`docker-compose.qa.yml` o `Makefile`) validando que no existan fallos ni degradación de cobertura.
3. **Sincronización Documental Obligatoria:**
   - Actualizar los manuales técnicos afectados en `docs/` (incluyendo `docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md`).
   - Actualizar las especificaciones de arquitectura en `specs/`.
   - Actualizar el historial de cambios en `CHANGELOG.md` (bajo `## [Unreleased]`).
   - Actualizar el estado de hitos y sub-tareas en `ROADMAP.md`.
   - Actualizar las métricas y conteo de pruebas en `TESTING.md`.
   - Actualizar `README.md` y documentación en la raíz cuando aplique.
4. **Auditoría de Secretos y Paridad ORM:**
   - Ejecutar `./verificar-secretos.sh` (0 secretos expuestos).
   - Ejecutar `./.agents/scripts/certify_task_completion.sh`.
5. **Registro y Publicación Remota Inmediata:**
   - Registrar los cambios con `git add .`.
   - Crear el commit con mensaje semántico en español (`git commit -m "<tipo>(<ámbito>): <descripción_en_español>"`).
   - Publicar inmediatamente en Git (`git push origin <rama_actual>`).

**Queda estrictamente prohibido concluir un turno dejando código modificado sin confirmar (*uncommitted changes*) ni con documentación desfasada en el repositorio.**


