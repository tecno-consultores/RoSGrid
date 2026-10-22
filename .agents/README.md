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

## 📦 Publicación Obligatoria en Git (`git commit & push`)

Por gobernanza innegociable, tras **CADA** tarea que modifique código o configuraciones, el agente de IA debe:
1. Superar el protocolo de pruebas y certificación.
2. Registrar los cambios con `git add .`.
3. Crear el commit con mensaje semántico en español (`git commit -m "<tipo>(<ámbito>): <mensaje>"`).
4. Publicar inmediatamente en Git (`git push origin <rama>`).
Queda estrictamente prohibido concluir un turno dejando código modificado sin confirmar en el repositorio.

