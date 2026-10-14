# Integración Autónoma con Agentes de IA

Este documento detalla cómo evolucionar de una interacción manual a un flujo de trabajo automatizado, donde los agentes de Inteligencia Artificial ingieren, aplican y ejecutan los *blueprints* de QA de forma autónoma.

## 1. Ingestión de Reglas mediante MCP (Model Context Protocol)
Para que un agente comprenda las restricciones corporativas en tiempo real, los *blueprints* deben exponerse como recursos dinámicos.

* **El Concepto:** Evita darle a la IA acceso irrestricto de lectura a todo tu disco duro. Usa un servidor MCP para exponer únicamente las reglas y el código que necesita de forma comprimida.
* **Ejemplo Práctico 1 (Implementación Nivel 11X para Código):** En lugar de dar acceso de lectura a todo el disco, nuestro ecosistema integra el perfil oculto `--profile graphify`. Antes de programar, la IA debe extraer el grafo semántico y levantar el servidor MCP efímero:

```bash
  docker compose -f docker-compose.qa.yml --profile graphify run --rm graphify bash -c "uvx graphifyy extract"
  docker compose -f docker-compose.qa.yml --profile graphify up -d graphify
```
* Luego, el agente se conecta por SSE a `http://localhost:8080/sse` para consultar la topología, ahorrando miles de tokens en OmniRoute.
* **Ejemplo Práctico 2 (Recursos Custom para Documentación):** Configura un servidor MCP que exponga los archivos `.md` como *Recursos* estáticos (URIs). Cuando el agente detecta que está en un proyecto Python, consulta `blueprints://python/fastapi`. El servidor lee el archivo local y le devuelve el prompt inyectando la regla inquebrantable del 95% de cobertura.
* **Ejemplo Práctico 3 (Lectura Proactiva de Configuraciones QA):** El servidor MCP (Graphify) no solo debe exponer la topología y las reglas del Blueprint. Debe exponer proactivamente los archivos de configuración de QA (como `pyproject.toml`, `.eslintrc.json`, `tsconfig.json`, `vitest.config.ts`) al Agente IA antes de que este genere código.
  * **Regla Inquebrantable a inyectar al Agente Developer:** "Si el Agente Developer va a escribir código, su primer paso autónomo debe ser leer las reglas de linters y tipado vía MCP, para generar código que cumpla con el estándar estricto (ej. `strict=true` en Mypy) desde el primer intento, ahorrando ciclos de auto-corrección (tokens)."

## 2. Orquestación Multi-Agente (Arquitecturas tipo Pantheon / Hermes)
Las pruebas de alta exigencia (mutación, SAST, BDD) abruman el contexto si un solo agente intenta programar la aplicación y auditarla al mismo tiempo. Se debe implementar una separación de roles.

* **El Concepto:** Un Agente Developer escribe el código; un Agente Auditor (QA) vigila que se cumplan las reglas del *blueprint*.
* **Sugerencia de Implementación (System Prompt para el Agente QA):**
  > *"Eres un auditor de QA implacable. Tu única fuente de la verdad es el archivo de reglas ingerido vía MCP. Si el Agente Developer propone comandos crudos locales como `pip install`, `npm run test` o intenta construir comandos largos de Docker, RECHAZA el código. Exígele estrictamente usar los comandos predefinidos en el `Makefile` (ej. `make qa-unit`, `make qa-all`) para aislar la infraestructura e invocar dependencias en los volúmenes de caché."*
* **Flujo:** Si el Developer crea un script de Bash destructivo sin usar `bats-mock`, el Agente QA intercepta el paso y obliga a refactorizar la prueba antes de dar el trabajo por terminado.

## 3. Optimización del Contexto con Proxies de Inferencia (OmniRoute)
El ciclo de auto-corrección consume masivamente tokens de entrada, especialmente al procesar volcados de error largos o reportes de cobertura en HTML.

* **El Concepto:** No gastes tokens de modelos de alto razonamiento (y alto costo) en arreglar un problema de espacios en blanco.
* **Ejemplo de Enrutamiento (Routing):**
  * **Tareas Mecánicas:** Configura OmniRoute para enrutar los errores de `shfmt`, `ShellCheck` o `Ruff` hacia un modelo local rápido y económico (ej. *Llama 3 8B* o *Hermes 3 8B*). Esta misma regla aplica para las herramientas de linting y formateo como `ESLint` y `Prettier`. Corregir indentación o punto y coma no requiere inteligencia avanzada.
  * **Tareas Lógicas:** Si una prueba de mutación en `Stryker` o `mutmut` falla, o hay un interbloqueo reportado por `Artillery`, enruta ese volcado al modelo de más alto razonamiento (ej. *Hermes 3 70B* o *Claude 3.5 Sonnet*), ya que requiere analizar el flujo de negocio para entender por qué la prueba es defectuosa. De igual manera, los reportes de análisis de deuda técnica y complejidad generados por `radon` o `eslint-plugin-sonarjs` deben ser procesados por los modelos mayores.

## 4. Sandboxing: Permisos de Ejecución (Tool Calling)
El ecosistema de `qa-testing-blueprints` está diseñado intencionalmente para ser el entorno de juegos de la IA. Como todas las pruebas ocurren en contenedores que se autodestruyen y se encapsulan tras comandos `make`, es seguro darle a la IA acceso de ejecución.

* **El Concepto:** Proporcionar al agente una herramienta (`tool_call`) para ejecutar comandos en la terminal, pero bloqueando el acceso al host real.
* **Ejemplo Práctico de Restricción (Python):** En la definición de tu herramienta para la IA, aplica una validación estricta antes de invocar el subproceso, forzando el uso exclusivo de los *Makefiles*:

```python
  def ejecutar_comando_qa(comando: str) -> str:
      if not comando.startswith("make qa-") and comando != "make clean-cache":
          return "ERROR: Operación denegada. Política corporativa: Solo puedes auditar usando las metas del Makefile estandarizado (ej. 'make qa-lint', 'make qa-unit')."
      
      resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)
      return resultado.stdout if resultado.returncode == 0 else resultado.stderr
```

* **El Bucle Autónomo de Observabilidad:** El agente ejecuta las pruebas y evalúa el `stderr`. Si `kcov` reporta solo un 85% de cobertura, o si la IA levanta el perfil `--profile chaos` y detecta mediante peticiones al endpoint `http://localhost:9090/api/v1/query` (Prometheus) que la latencia (P99) sobrepasa los umbrales corporativos, la IA comprende la falla, reescribe el código de negocio en su propio entorno interno y vuelve a invocar la herramienta de estrés hasta lograr el estándar.
