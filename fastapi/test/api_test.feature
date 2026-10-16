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

  Scenario: 5. Petición mutable sin cabecera Idempotency-Key es rechazada con HTTP 400
    Given path '/api/v1/inventory/routers'
    And request { display_name: 'RB4011-Test' }
    When method post
    Then status 400
    And match response == { detail: 'Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables' }

  Scenario: 6. Aislamiento Multi-Tenant RLS: Acceso a inventario de routers sin autenticación devuelve 401
    Given path '/api/v1/inventory/routers'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 7. Bóveda Criptográfica: Intento de revelación de clave sin Step-Up 2FA devuelve 401
    Given path '/api/v1/inventory/routers/00000000-0000-0000-0000-000000000001/vault/reveal'
    And header Idempotency-Key = '01928900-0000-7000-8000-000000000001'
    And request { totp_code: '123456', reason: 'Auditoría no autorizada' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 8. Maker-Checker: Acceso a la bandeja de aprobaciones sin credenciales devuelve 401
    Given path '/api/v1/operations/approvals'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 9. Endpoint MCP Protegido: Petición JSON-RPC 2.0 sin autenticación Bearer devuelve 401
    Given path '/api/v1/mcp'
    And header Idempotency-Key = '01928900-0000-7000-8000-000000000002'
    And request { jsonrpc: '2.0', id: 'karate-test-1', method: 'initialize', params: {} }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 10. Endpoint MCP Protegido: Token Bearer inválido o corrupto devuelve 401
    Given path '/api/v1/mcp'
    And header Authorization = 'Bearer token_invalido_123'
    And header Idempotency-Key = '01928900-0000-7000-8000-000000000003'
    And request { jsonrpc: '2.0', id: 'karate-test-2', method: 'initialize', params: {} }
    When method post
    Then status 401
    And match response.detail contains 'Token de acceso inválido'

  Scenario: 11. Login 2FA: Enviar código 2FA con payload malformado devuelve HTTP 422
    Given path '/api/v1/auth/2fa/verify'
    And header Idempotency-Key = '01928900-0000-7000-8000-000000000004'
    And request { codigo_invalido: 123456 }
    When method post
    Then status 422
    And match response.detail[0].type == '#string'

