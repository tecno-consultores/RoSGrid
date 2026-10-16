Feature: Flujo principal de negocio de la interfaz Vue 3 de RoSGrid

  Background:
    * configure driver = { type: 'chrome', headless: true, addOptions: ['--no-sandbox'] }
    * def envBaseUrl = java.lang.System.getenv('UI_BASE_URL')
    * def baseUrl = karate.properties['UI_BASE_URL'] || envBaseUrl || 'http://ui-prod:80'

  Scenario: El operador accede al Dashboard/Inventario de RoSGrid y actualiza el estado de la flota
    Given driver baseUrl + '/'
    And waitFor("//h1[contains(., 'Dashboard')]")
    When click("//button[contains(@class, 'btn-primary') and contains(., 'Actualizar Datos')]")
    Then waitFor(".status-indicator.success")
    And match text(".status-text") == 'Actualizado'
