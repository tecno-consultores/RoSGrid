# 24 — ESTÁNDAR QA 11X BACKEND: ORQUESTADOR DOCKER EFÍMERO, MAKEFILE, TOX Y AUDITORÍA DE COMPLEJIDAD RADON (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica la infraestructura inmutable de validación Nivel 11X para el ecosistema Backend (fastapi/). Tienes estrictamente prohibido ejecutar pip install, uv sync o pytest directamente en el sistema operativo host, así como modificar fastapi/docker-compose.qa.yml para agregar Dockerfile o build:. Toda validación DEBE ejecutarse de manera efímera a través de fastapi/Makefile aprovechando el volumen persistente fastapi\_uv\_cache.




## **1. Especificación Exacta de fastapi/docker-compose.qa.yml**

El archivo fastapi/docker-compose.qa.yml utiliza exclusivamente las imágenes oficiales sinfallas/base-python-uv:3.15, sinfallas/karatelabs:latest, owasp/zap2docker-stable:latest, gaiaadm/pumba:latest, prom/prometheus:latest y sinfallas/remote-graphify:latest sobre una red bridge estrictamente IPv4:


services:


  api:


    image: sinfallas/base-python-uv:3.15


    container\_name: fastapi\_api


    hostname: fastapi\_api


    pull\_policy: always


    environment:


      TZ: 'America/Caracas'


      UV\_CACHE\_DIR: /root/.cache/uv


      ROSGRID\_ENV: 'qa\_test'


      ROSGRID\_MASTER\_VAULT\_KEY: 'MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY='


      ROSGRID\_JWT\_SECRET\_KEY: 'qa\_jwt\_secret\_key\_for\_ephemeral\_testing\_only'


      ROSGRID\_CSRF\_HMAC\_SECRET: 'qa\_csrf\_hmac\_secret\_for\_ephemeral\_testing\_only'


    volumes:


      - .:/app


      - uv-cache:/root/.cache/uv


    working\_dir: /app


    ports:


      - "8000:8000"


    cap\_add:


      - SYS\_PTRACE


    security\_opt:


      - seccomp:unconfined


    command: bash -c "uv pip install --system -e '.\[dev\]' && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload"


  qa-backend:


    image: sinfallas/base-python-uv:3.15


    container\_name: fastapi\_qa\_backend


    hostname: fastapi\_qa\_backend


    pull\_policy: always


    environment:


      TZ: 'America/Caracas'


      UV\_PYTHON\_DOWNLOADS: 'true'


      UV\_CACHE\_DIR: /root/.cache/uv


      ROSGRID\_ENV: 'qa\_unit'


      ROSGRID\_MASTER\_VAULT\_KEY: 'MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY='


      ROSGRID\_JWT\_SECRET\_KEY: 'qa\_jwt\_secret\_key\_for\_ephemeral\_testing\_only'


      ROSGRID\_CSRF\_HMAC\_SECRET: 'qa\_csrf\_hmac\_secret\_for\_ephemeral\_testing\_only'


    volumes:


      - .:/app


      - uv-cache:/root/.cache/uv


    working\_dir: /app


    cap\_add:


      - SYS\_PTRACE


    command: bash -c "echo 'Contenedor QA Backend (Python 3.13) listo para Lint, Pytest y Mutmut'; sleep infinity"


  karatelabs:


    image: sinfallas/karatelabs:latest


    container\_name: fastapi\_karate


    hostname: fastapi\_karate


    pull\_policy: always


    depends\_on:


      - api


    volumes:


      - ./test:/app/src/test/java/examples/test


    command: bash -c "echo 'Contenedor Karate listo. Usa docker compose run --rm karatelabs mvn clean test'; sleep infinity"


  zap:


    image: owasp/zap2docker-stable:latest


    container\_name: fastapi\_zap


    hostname: fastapi\_zap


    pull\_policy: always


    depends\_on:


      - api


    user: root


    volumes:


      - .:/zap/wrk/:rw


    command: bash -c "echo 'Contenedor ZAP listo.'; sleep infinity"


  pumba:


    image: gaiaadm/pumba:latest


    container\_name: fastapi\_pumba


    hostname: fastapi\_pumba


    profiles:


      - chaos


    volumes:


      - /var/run/docker.sock:/var/run/docker.sock:ro


    depends\_on:


      - api


    command: netem --tc-image gaiadocker/iproute2 --duration 1m delay --time 500 --jitter 50 re2:^fastapi\_api$


  prometheus:


    image: prom/prometheus:latest


    container\_name: fastapi\_prometheus


    hostname: fastapi\_prometheus


    profiles:


      - chaos


    entrypoint:


      - /bin/sh


      - -c


      - |


        echo "


        global:


          scrape\_interval: 2s


        scrape\_configs:


          - job\_name: 'fastapi\_qa'


            metrics\_path: '/metrics'


            static\_configs:


              - targets: \['api:8000'\]


        " \> /tmp/prometheus.yml


        /bin/prometheus --config.file=/tmp/prometheus.yml


    ports:


      - "9090:9090"


    depends\_on:


      - api


  stress\_test:


    image: sinfallas/base-python-uv:3.15


    container\_name: fastapi\_chaos\_locust


    hostname: fastapi\_chaos\_locust


    profiles:


      - chaos


    depends\_on:


      - api


    environment:


      UV\_CACHE\_DIR: /root/.cache/uv


    volumes:


      - .:/app


      - uv-cache:/root/.cache/uv


    working\_dir: /app


    command: bash -c "uv pip install --system -e '.\[dev\]' && echo 'Esperando asimilación del caos...' && sleep 5 && locust -f locustfile.py --headless -u 200 -r 20 -t 1m --host http://api:8000 --html chaos-report.html"


  graphify:


    image: sinfallas/remote-graphify:latest


    container\_name: fastapi\_graphify


    hostname: fastapi\_graphify


    profiles:


      - graphify


    restart: always


    command: uvx --from graphifyy python -m graphify.serve /app/graphify-out/graph.json --transport http --host 0.0.0.0 --port 8080


    ports:


      - "8080:8080"


    extra\_hosts:


      - "host.docker.internal:host-gateway"


    environment:


      - GRAPHIFY\_OLLAMA\_KEEP\_ALIVE=10


    volumes:


      - .:/app


    logging:


      driver: "json-file"


      options:


        max-size: "1m"


        max-file: "1"


networks:


  default:


    driver: bridge


volumes:


  uv-cache:


    name: fastapi\_uv\_cache




## **2. Especificación de fastapi/Makefile (Task Runner Obligatorio)**

AntiGravity DEBE crear fastapi/Makefile incorporando las metas estandarizadas del blueprint 11X, incluyendo la validación de complejidad ciclomática (radon), seguridad estática (bandit + uv pip audit), tipado (mypy --strict), cobertura (\>= 95%) y mutación (mutmut):


.PHONY: qa-lint qa-unit qa-mutation qa-contracts qa-bdd qa-dast qa-chaos qa-all clean-cache


COMPOSE\_FILE = docker-compose.qa.yml


SERVICE\_NAME = qa-backend


qa-lint:


	@echo "🔍 Ejecutando Ruff, Mypy Strict, Radon (Complejidad \< C, MI \>= B), Bandit SAST y Auditoría CVE..."


	docker compose -f $(COMPOSE\_FILE) run --rm $(SERVICE\_NAME) bash -c "\\


		uv sync && \\


		uv run ruff check src/ tests/ && \\


		uv run ruff format --check src/ tests/ && \\


		uv run mypy --strict src/ && \\


		test -z \\"$$(uv run radon cc --min C src/)\\" && \\


		test -z \\"$$(uv run radon mi --min B src/)\\" && \\


		uv run bandit -c pyproject.toml -r src/ && \\


		uv pip audit"


qa-unit:


	@echo "🧪 Ejecutando Pruebas Unitarias Aisladas y Cobertura Innegociable \>= 95% (Pytest)..."


	docker compose -f $(COMPOSE\_FILE) run --rm $(SERVICE\_NAME) bash -c "\\


		uv sync && \\


		uv run pytest -m 'not integration' --cov=src --cov-fail-under=95 --cov-report=term-missing --cov-report=html"


qa-mutation:


	@echo "👽 Ejecutando Pruebas de Mutación (Mutmut)..."


	docker compose -f $(COMPOSE\_FILE) run --rm $(SERVICE\_NAME) bash -c "\\


		uv sync && \\


		uv run mutmut run && \\


		uv run mutmut results"


qa-all: qa-lint qa-unit qa-mutation


	@echo "✅ Pipeline QA Backend (FastAPI RoSGrid) completado exitosamente."


clean-cache:


	@echo "🧹 Limpiando volúmenes de caché de uv y contenedores efímeros..."


	docker compose -f $(COMPOSE\_FILE) down -v


	docker compose -f $(COMPOSE\_FILE) --profile chaos down -v


	docker compose -f $(COMPOSE\_FILE) --profile graphify down -v




## **3. Especificación de fastapi/tox.ini**

\[tox\]


env\_list = py313


isolated\_build = True


\[testenv\]


description = Instala dependencias con uv y ejecuta QA 11X, complejidad Radon, SAST Bandit y pruebas de RoSGrid


deps =


    .\[dev\]


commands =


    ruff check src/ tests/


    ruff format --check src/ tests/


    mypy --strict src/


    radon cc --min C src/


    radon mi --min B src/


    uv pip audit


    bandit -c pyproject.toml -r src/


    pytest -m "not integration" --cov=src/ --cov-fail-under=95 --cov-report=term-missing




## **4. Reglas de Diseño para Aprobar Radon (CC \< C y MI \>= B) y Bandit en el Primer Intento**

1. **Límite de Complejidad Ciclomática (CC \<= 5 por función):**

   - En Python, radon cc --min C src/ reporta cualquier función o método cuya complejidad ciclomática sea **11 o superior** (Grado C).

   - Para garantizar que ninguna función se acerque a ese límite, AntiGravity tiene prohibido escribir funciones con más de **5 bifurcaciones (if, for, while, except, and, or)**.

   - En lugar de grandes bloques condicionales, utiliza **diccionarios de despacho (Dispatch Tables)** (ej. POLICY\_MATRIX\[role\]\[action\] en RBAC o CRITICAL\_MATCHERS en Maker-Checker).

2. **Cumplimiento de Bandit (SAST):**

   - Prohibido usar assert dentro de src/ para validaciones de negocio o seguridad (Bandit lanza B101: assert\_used); lanza siempre excepciones explícitas (HTTPException o excepciones de dominio).

   - Prohibido usar random estándar para tokens, nonces o contraseñas de rotación (B311); usa exclusivamente el módulo secrets o os.urandom().

   - Prohibido usar subprocess con shell=True (B602).

## **5. Protocolo de Aislamiento de Producción (--no-dev) y Smoke Test Inmutable**

1. **Test Estático AST de Limpieza (`test_production_no_dev_cleanliness.unit.py`):**
   - Ejecuta un análisis del árbol de sintaxis abstracta (AST) sobre el 100% de los archivos `.py` en `src/`.
   - Garantiza que ninguna clase, servicio o endpoint importe módulos del grupo `[project.optional-dependencies] dev` (`pytest`, `radon`, `hypothesis`, `freezegun`, `unittest.mock`, etc.).

2. **Smoke Test de Arranque Inmutable (`fastapi/scripts/test_production_boot_smoke.py`):**
   - Ejecutado directamente dentro de la imagen final compilada con `uv sync --frozen --no-dev --compile-bytecode`.
   - Verifica la ausencia de paquetes dev en memoria (`sys.modules`), importa recursivamente los 80 submódulos de `src/`, confirma la desactivación estricta de Swagger en producción (`docs_url=None`, `redoc_url=None`, `openapi_url=None`) y valida el ciclo `/health` in-process.
