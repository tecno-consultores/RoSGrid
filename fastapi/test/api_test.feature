Feature: Validación BDD Caja Negra de la API FastAPI de RoSGrid y Seguridad Multi-Tenant

  Background:
    * url 'http://api:8000'
    * configure headers = { 'Content-Type': 'application/json' }

  Scenario: 1. Verificar que la API responda correctamente al healthcheck con estructura validada
    Given path '/health'
    When method get
    Then status 200
    And match response == { status: '#string', service: '#string' }
    And match response.status == 'healthy'
    And match response.service == 'rosgrid-api'

  Scenario: 2. Verificar que el endpoint de observabilidad Prometheus (/metrics) esté expuesto
    Given path '/metrics'
    When method get
    Then status 200
    And match response contains 'http_requests_total'

  Scenario: 3. Intento de acceso a ruta protegida sin cookie HttpOnly devuelve 401
    Given path '/users/me'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 4. Enviar un payload malformado al login (Pydantic validation failure) devuelve HTTP 422
    Given path '/api/v1/auth/login'
    And request { username: "solouser_sinpassword" }
    When method post
    Then status 422
    And match response.detail[0].type == '#string'

  Scenario: 5. Petición mutable sin cabecera X-CSRF-Token ni sesión es rechazada
    Given path '/api/v1/inventory/routers'
    And request { display_name: 'RB4011-Test' }
    When method post
    Then status 401
