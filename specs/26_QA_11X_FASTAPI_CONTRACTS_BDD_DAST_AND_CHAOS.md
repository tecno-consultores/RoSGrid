# 26 — ESTÁNDAR QA 11X BACKEND: CONTRATOS SCHEMATHESIS, BDD KARATE LABS, DAST OWASP ZAP, PROFILING PY-SPY E INGENIERÍA DEL CAOS (PUMBA + LOCUST) (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica las capas dinámicas, de contratos, caja negra, seguridad DAST y resiliencia bajo caos del Backend (fastapi/) según el Estándar 11X.




## **1. Validación de Contratos y Fuzzing OpenAPI (Schemathesis)**

- **Propósito:** Bombardear el esquema http://api:8000/openapi.json con miles de combinaciones de tipos límite, cadenas vacías, caracteres Unicode y estructuras malformadas para certificar que ningún endpoint de RoSGrid arroje jamás un HTTP 500 Internal Server Error no controlado.

- **Regla de Implementación en Schemas Pydantic v2 (fastapi/src/schemas/):**

  - Todos los modelos Pydantic de entrada DEBEN declarar model\_config = ConfigDict(extra="forbid", str\_strip\_whitespace=True) y límites explícitos Field(min\_length=..., max\_length=..., pattern=...) para que cualquier payload malformado sea rechazado limpiamente con HTTP 422 Unprocessable Entity o HTTP 400/401/403.

- **Comando Efímero de Ejecución:**


docker compose -f docker-compose.qa.yml up -d api


docker compose -f docker-compose.qa.yml run --rm qa-backend bash -c "uv sync && uv run schemathesis run http://api:8000/openapi.json"




## **2. Escenarios BDD de Caja Negra en Karate Labs (fastapi/test/api\_test.feature)**

AntiGravity DEBE fusionar los escenarios base del blueprint 11X con los escenarios críticos de seguridad Multi-Tenant de RoSGrid dentro de fastapi/test/api\_test.feature:


Feature: Validación BDD Caja Negra de la API FastAPI de RoSGrid y Seguridad Multi-Tenant


  Background:


    \* url 'http://api:8000'


    \* configure headers = \{ 'Content-Type': 'application/json' \}


  Scenario: 1. Verificar que la API responda correctamente al healthcheck con estructura validada


    Given path '/health'


    When method get


    Then status 200


    And match response == \{ status: '\#string' \}


    And match response.status == 'healthy'


  Scenario: 2. Verificar que el endpoint de observabilidad Prometheus (/metrics) esté expuesto


    Given path '/metrics'


    When method get


    Then status 200


    And match response contains 'http\_requests\_total'


  Scenario: 3. Intento de acceso a ruta protegida sin cookie HttpOnly devuelve 401


    Given path '/users/me'


    When method get


    Then status 401


    And match response == \{ detail: 'Not authenticated' \}


  Scenario: 4. Enviar un payload malformado al login (Pydantic validation failure) devuelve HTTP 422


    Given path '/api/v1/auth/login'


    And request \{ email: "solouser\_sinpassword" \}


    When method post


    Then status 422


    And match response.detail\[0\].type == '\#string'


  Scenario: 5. Petición mutable sin cabecera X-CSRF-Token ni sesión es rechazada


    Given path '/api/v1/inventory/routers'


    And request \{ display\_name: 'RB4011-Test' \}


    When method post


    Then status 401


- **Comando Efímero de Ejecución:**


docker compose -f docker-compose.qa.yml run --rm karatelabs mvn clean test




## **3. Seguridad Dinámica DAST con OWASP ZAP Baseline**

- **Comando Efímero de Ejecución:**


docker compose -f docker-compose.qa.yml run --rm zap zap-baseline.py -t http://api:8000 -r zap-report.html


- **Requisitos en SecurityHeadersMiddleware para Aprobar con 0 Alertas Medias/Altas:**

  1. Cabecera X-Content-Type-Options: nosniff presente en todas las respuestas (incluyendo /health, /metrics, 401, 403, 404 y 422).

  2. Cabecera X-Frame-Options: DENY presente en todas las respuestas.

  3. Cabecera Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; sandbox en respuestas de la API.

  4. Cabecera Cache-Control: no-store en todas las rutas de autenticación y negocio.

  5. Supresión del banner de versión de servidor (Server).




## **4. Profiling de CPU y Detección de Bloqueos del Event Loop (py-spy)**

Para certificar que operaciones intensivas (como el cálculo de unified\_diff entre dos archivos .rsc grandes, la validación de un CSV de 500 routers o el cifrado AES-256-GCM) no bloquean el Event Loop asíncrono de Uvicorn:


- **Comando Efímero de Ejecución:**


docker compose -f docker-compose.qa.yml exec -T api bash -c "py-spy record -o /app/profile.svg --pid 1 --duration 30"


- Si una operación de hashing Argon2id o compresión/diff de .rsc supera los 5ms de CPU síncrona, AntiGravity DEBE delegarla a asyncio.to\_thread(...) para no bloquear las demás peticiones ni los WebSockets en vivo.




## **5. Ingeniería del Caos y Estrés Concurrente (Pumba + Locust + Prometheus)**

El archivo fastapi/locustfile.py DEBE fusionar la plantilla .example del blueprint 11X con los flujos reales de RoSGrid:


\# SPDX-License-Identifier: GPL-3.0-only


\# Copyright (C) 2026 RoSGrid Contributors


import uuid


from locust import HttpUser, between, task



class RoSGridStressUser(HttpUser):


    wait\_time = between(1, 3)


    def on\_start(self) -\> None:


        self.headers = \{


            "Content-Type": "application/json",


            "X-CSRF-Token": "qa-load-test-csrf",


        \}


    @task(4)


    def check\_health(self) -\> None:


        """Verifica disponibilidad continua bajo inyección de jitter de Pumba."""


        self.client.get("/health", headers=self.headers)


    @task(2)


    def check\_prometheus\_metrics(self) -\> None:


        """Verifica que el colector de métricas RED responda sin bloqueos."""


        self.client.get("/metrics")


    @task(2)


    def simulate\_inventory\_read\_unauthorized\_or\_cached(self) -\> None:


        """Evalúa velocidad de respuesta del guard de sesión/RBAC bajo carga."""


        with self.client.get(


            "/api/v1/inventory/routers",


            headers=self.headers,


            catch\_response=True,


        ) as response:


            if response.status\_code in (200, 401):


                response.success()


    @task(1)


    def invalid\_login\_attempt\_validation(self) -\> None:


        """Estresa el parser Pydantic v2 y el control de intentos fallidos."""


        payload = \{


            "tenant\_slug": "isp-chaos-test",


            "email": f"bot-\{uuid.uuid4().hex\[:6\]\}@isp.net",


            "password": "invalid\_password\_123",


        \}


        with self.client.post(


            "/api/v1/auth/login",


            json=payload,


            headers=self.headers,


            catch\_response=True,


        ) as response:


            if response.status\_code in (401, 422, 423, 429):


                response.success()


- **Comando de Certificación de Caos Nivel 11X:**


docker compose -f docker-compose.qa.yml --profile chaos up --abort-on-container-exit stress\_test


Durante 1 minuto, **Pumba** inyecta 500ms de delay con 50ms de jitter en la interfaz de red del contenedor fastapi\_api, mientras **Locust** simula 200 usuarios concurrentes (-u 200 -r 20) y **Prometheus** recolecta métricas cada 2 segundos en :9090. El criterio de éxito exige **0 caídas del proceso Uvicorn (0 Exit Code 137 / 0 Deadlocks)** y generación limpia de chaos-report.html.
