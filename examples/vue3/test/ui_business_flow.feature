Feature: Flujo principal de negocio de la interfaz Vue

  Background:
    # Karate interceptará y levantará Chrome internamente
    * configure driver = { type: 'chrome', headless: true, addOptions: ['--no-sandbox'] }
    # Lee la URL desde las variables inyectadas en docker-compose
    * def baseUrl = karate.env == 'local' ? 'http://localhost:8080' : karate.properties['UI_BASE_URL']

  Scenario: El usuario navega al dashboard y verifica la carga de componentes
    Given driver baseUrl + '/'
    And waitFor("h1:contains('Dashboard')")
    When click("button.btn-primary:contains('Actualizar Datos')")
    Then waitFor(".status-indicator.success")
    And match text(".status-text") == 'Actualizado'
