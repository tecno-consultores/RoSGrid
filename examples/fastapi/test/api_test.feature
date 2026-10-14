Feature: Validación BDD de la API FastAPI y Manejo de Errores

  Background:
    # URL apuntando al servicio FastAPI dentro de la red interna de Docker[cite: 21]
    * url 'http://api:8000'
    * configure headers = { 'Content-Type': 'application/json' }

  Scenario: Verificar que la API responda correctamente al healthcheck con estructura validada
    Given path '/health'
    When method get
    Then status 200
    And match response == { status: '#string' }
    And match response.status == 'healthy'

  Scenario: Intento de acceso a ruta protegida devuelve 401 y estructura estandarizada de error
    Given path '/users/me'
    When method get
    Then status 401
    And match response == { detail: 'Not authenticated' }

  Scenario: Enviar un payload malformado (Pydantic validation failure) devuelve HTTP 422
    Given path '/login'
    And request { user: "solouser_sinpassword" }
    When method post
    Then status 422
    # Valida que Pydantic esté filtrando la data y devolviendo el array de detalles del error
    And match response.detail[0].type == '#string'
    And match response.detail[0].loc contains 'password'Feature: Validación BDD de la API FastAPI

  Background:
    # URL apuntando al servicio FastAPI (o al host si corre localmente)
    * url 'http://api:8000'

  Scenario: Verificar que la API responda al healthcheck
    Given path '/health'
    When method get
    Then status 200
    And match response == { status: 'healthy' }

  Scenario: Intento de acceso a ruta protegida devuelve 401
    Given path '/users/me'
    When method get
    Then status 401
    And match response.detail == 'Not authenticated'
