# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors
# Suite Integral de Aceptación BDD con Karate UI para RoSGrid Frontend

Feature: Cobertura Funcional y Flujos BDD de la Interfaz Web Vue 3 de RoSGrid

  Background:
    * configure driver = { type: 'chrome', headless: true, addOptions: ['--no-sandbox', '--disable-dev-shm-usage'] }
    * def envBaseUrl = java.lang.System.getenv('UI_BASE_URL')
    * def baseUrl = karate.properties['UI_BASE_URL'] || envBaseUrl || 'http://ui-prod:80'

  Scenario: 1. Autenticación, pantalla de Login y verificación de campos de acceso
    Given driver baseUrl + '/login'
    And waitFor("#login-heading")
    Then match text("#login-heading") contains 'RoSGrid'
    And waitFor("#tenant-slug")
    And waitFor("#login-email")
    And waitFor("#login-password")
    When input("#tenant-slug", 'isp-demo')
    And input("#login-email", 'operador@ispdemo.net')
    And input("#login-password", 'PasswordInvalido123!')
    And click("#btn-login-submit")
    Then waitFor(".banner--error")

  Scenario: 2. Centro de Mando / Dashboard y actualización de telemetría de flota
    Given driver baseUrl + '/'
    And waitFor("//h1[contains(., 'Centro de Mando') or contains(., 'Dashboard')]")
    And waitFor(".kpi-strip")
    When click("//button[contains(@class, 'btn-primary') and contains(., 'Actualizar Datos')]")
    Then waitFor(".status-indicator.success")
    And match text(".status-text") == 'Actualizado'

  Scenario: 3. Inventario de Routers MikroTik y Filtros de Estado
    Given driver baseUrl + '/inventory'
    And waitFor("//h1[contains(., 'Inventario de Equipos')]")
    And waitFor("#inv-search")
    And waitFor("button.btn-import-csv")
    When input("#inv-search", 'CCR2004')
    Then waitFor(".view-mode-toggle")
    When click("//button[contains(@class, 'btn-toggle') and contains(., 'Tabla')]")
    Then match attribute("//button[contains(@class, 'btn-toggle') and contains(., 'Tabla')]", 'class') contains 'btn-toggle--active'

  Scenario: 4. Consola WebFig v7 y Pestañas en Memoria (KeepAlive)
    Given driver baseUrl + '/routers/01928900-aaaa-7bbb-8ccc-111122223333/webfig/live'
    And waitFor(".webfig-shell")
    And waitFor(".tab-strip")
    Then match text(".tab-strip") contains 'Dashboard en Vivo'
    When click("//a[contains(@class, 'tab-link') and contains(., 'Interfaces')]")
    Then waitFor("//h2[contains(., 'Interfaces') or contains(., 'SFP')]")

  Scenario: 5. Bandeja de Aprobaciones Maker-Checker con Freno de Seguridad
    Given driver baseUrl + '/operations/approvals'
    And waitFor("//h1[contains(., 'Bandeja de Aprobaciones')]")
    And waitFor(".subtabs-bar")
    When click("//button[contains(@class, 'btn-subtab') and contains(., 'Pendientes')]")
    Then match attribute("//button[contains(@class, 'btn-subtab') and contains(., 'Pendientes')]", 'class') contains 'btn-subtab--active'

  Scenario: 6. Historial de Respaldos y Comparador Git Diff (.rsc)
    Given driver baseUrl + '/backups'
    And waitFor("//h1[contains(., 'Historial de Respaldos')]")
    And waitFor(".diff-header")
    Then match text(".diff-subtitle") contains 'Deduplicación SHA-256'

  Scenario: 7. Operaciones Masivas y Actualizador de RouterOS
    Given driver baseUrl + '/bulk-ops'
    And waitFor("//h1[contains(., 'Operaciones Masivas')]")
    And waitFor(".tabs-nav")
    When click("//button[contains(@class, 'tab-btn') and contains(., 'Actualizador de RouterOS')]")
    Then match attribute("//button[contains(@class, 'tab-btn') and contains(., 'Actualizador de RouterOS')]", 'class') contains 'tab-btn--active'

  Scenario: 8. Muro Táctico Wallboard NOC 24/7 y KPIs en Tiempo Real
    Given driver baseUrl + '/noc-wallboard'
    And waitFor("//h1[contains(., 'RoSGrid NOC Wallboard')]")
    And waitFor(".live-indicator")
    Then match text(".live-indicator") contains 'EN VIVO 24/7'
    And waitFor(".kpi-strip")

  Scenario: 9. Consola Forense de Auditoría Inmutable (WORM)
    Given driver baseUrl + '/audit-logs'
    And waitFor("//h1[contains(., 'Consola Forense de Auditoría Inmutable')]")
    And waitFor("button.btn--verify")
    Then match text("button.btn--verify") contains 'Certificar Cadena WORM'
    And waitFor("//button[contains(., 'Exportar CSV')]")

  Scenario: 10. Administración de Empresas Multi-Tenant
    Given driver baseUrl + '/admin/tenants'
    And waitFor("//h1[contains(., 'Administración de Empresas')]")
    And waitFor("#btn-open-create-tenant")
    When click("#btn-open-create-tenant")
    Then waitFor(".rg-modal")

  Scenario: 11. Gestión de Usuarios y Matriz de Roles RBAC
    Given driver baseUrl + '/users'
    And waitFor("//h1[contains(., 'Gestión de Usuarios y Roles RBAC')]")
    And waitFor(".btn-toggle-reg")
    And waitFor("button.btn-create")

  Scenario: 12. Sesiones Activas y Kill-Switch en Tiempo Real
    Given driver baseUrl + '/sessions'
    And waitFor("//h1[contains(., 'Sesiones Activas y Kill-Switch')]")
    And waitFor("button.btn-refresh")
    When click("button.btn-refresh")
    Then waitFor(".sessions-table-container")

  Scenario: 13. IPAM Dual-Stack Universal & Gestión de Red
    Given driver baseUrl + '/ipam'
    And waitFor("//h1[contains(., 'IPAM') or contains(., 'Direccionamiento')]")
    And waitFor(".ipam-view")

  Scenario: 14. Toolkit de Operaciones de Campo para Técnicos
    Given driver baseUrl + '/field-ops'
    And waitFor(".field-ops-view")
    And waitFor(".toolkit-card")

  Scenario: 15. Mapa Exclusivo de Abonados y ONUs de Fibra Óptica
    Given driver baseUrl + '/subscribers/map'
    And waitFor("//h1[contains(., 'Mapa Exclusivo de Clientes') or contains(., 'ONUs')]")
    And waitFor(".subscribers-map-view")

  Scenario: 16. Gestión de Flota & Cumplimiento Normativo (CIS, Config Drift, SD-WAN)
    Given driver baseUrl + '/enterprise/compliance'
    And waitFor(".enterprise-compliance-view")
    And waitFor(".safemode-badge")
    Then match text(".safemode-badge") contains 'Safe Mode (60s) Activo'
    And waitFor("#compliance-router-select")

  Scenario: 17. Mapa de Topología Física Layer 2 y Enlaces PoE
    Given driver baseUrl + '/topology/l2'
    And waitFor("//h1[contains(., 'Topología Física Layer 2')]")
    And waitFor("canvas.topology-canvas")
    And waitFor(".btn-refresh-topo")
    Then match text(".legend-wrap") contains 'Inyector PSE'

  Scenario: 18. Matriz de Vulnerabilidades CVE de Flota y Remediación Táctica
    Given driver baseUrl + '/inventory/cves'
    And waitFor("//h1[contains(., 'Matriz de Vulnerabilidades CVE')]")
    And waitFor(".kpi-grid")
    And waitFor("button.btn-sync-cve")
    And waitFor("button.btn-remediate-fleet")
    Then match text("button.btn-remediate-fleet") contains 'Actualizar Flota Afectada'

  Scenario: 19. Consola WebFig v7 — Terminal Syslog en Vivo (RingBuffer Efímero)
    Given driver baseUrl + '/routers/01928900-aaaa-7bbb-8ccc-111122223333/webfig/syslog'
    And waitFor(".syslog-view")
    And waitFor("//h2[contains(., 'Consola Syslog en Vivo')]")
    And waitFor(".terminal-container")
    And waitFor("button.btn-template")
    Then match text("button.btn-template") contains 'Script RouterOS'

  Scenario: 20. Operaciones Masivas — Actualización con Conmutador PoE-Aware y Safety Stop
    Given driver baseUrl + '/bulk-ops'
    And waitFor("//h1[contains(., 'Operaciones Masivas')]")
    When click("//button[contains(@class, 'tab-btn') and contains(., 'Actualizador de RouterOS')]")
    Then waitFor(".poe-safety-card")
    And waitFor("button.btn-poe-upgrade")
    And match text("button.btn-poe-upgrade") contains 'Actualizar Flota Seleccionada con PoE-Aware'
    And waitFor(".checkbox-poe")

  Scenario: 21. Modal Asistente de Importación Masiva CSV en Inventario
    Given driver baseUrl + '/inventory'
    And waitFor("//h1[contains(., 'Inventario de Equipos')]")
    And waitFor("button.btn-import-csv")
    When click("button.btn-import-csv")
    Then waitFor(".rg-modal-dialog")
    And match text("//h2[contains(., 'Asistente de Importación Masiva CSV')]") contains 'Paso 1 de 2'
    And waitFor("button.btn-download-template")
    And waitFor("#csv-file-input")
    When click("button.btn-close")
    Then waitUntil("!document.querySelector('.rg-modal-dialog')")

  Scenario: 22. Estructura y Posicionamiento del Pie de Página en Pantalla de Login
    Given driver baseUrl + '/login'
    And waitFor(".login-wrapper")
    And waitFor(".login-card")
    And waitFor(".login-footer")
    Then match text(".login-footer") contains 'Elaborado por Tecno Consultores'
    And waitFor("#tenant-slug")
    And waitFor("#login-email")
    And waitFor("#login-password")

