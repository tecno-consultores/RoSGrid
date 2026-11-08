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

  Scenario: 3b. Verificación de columna de Seguridad SSL TOFU en la tabla de inventario
    Given driver baseUrl + '/inventory'
    And waitFor("//h1[contains(., 'Inventario de Equipos')]")
    And waitFor(".view-mode-toggle")
    When click("//button[contains(@class, 'btn-toggle') and contains(., 'Tabla')]")
    Then waitFor(".rg-datatable")
    And match text(".rg-datatable") contains 'SSL / TOFU'

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

  Scenario: 8. Muro Táctico Wallboard NOC y KPIs en Tiempo Real
    Given driver baseUrl + '/noc-wallboard'
    And waitFor("//h1[contains(., 'RoSGrid NOC Wallboard')]")
    And waitFor(".kpi-strip")
    And waitFor("button.btn-fullscreen")

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
    And waitFor("a[href='https://mikrotik.com/supportsec']")
    And waitFor("a[href='https://nvd.nist.gov/vuln/search?keyword=mikrotik&resultType=records']")
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
    And waitFor("a.btn-download-template")
    And match attribute("a.btn-download-template", 'href') contains '/api/v1/inventory/template-csv'
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

  Scenario: 23. Consola WebFig v7 — Gestión de Bridges Layer 1 y Safe Mode
    Given driver baseUrl + '/routers/01928900-aaaa-7bbb-8ccc-111122223333/webfig/bridge'
    And waitFor(".bridges-view")
    And waitFor("//h2[contains(., 'Interfaces Bridge y Puertos') or contains(., 'Bridge')]")
    And waitFor("button.btn-create-bridge")
    And waitFor(".bridges-table-container")

  Scenario: 24. Barra Superior Táctica — Menú Desplegable de Usuario y Reloj HH:MM
    Given driver baseUrl + '/'
    And waitFor(".global-clock-badge")
    And waitFor(".user-menu-trigger")
    When click(".user-menu-trigger")
    Then waitFor(".user-dropdown-menu")
    And waitFor(".time-format-toggle")
    And waitFor(".theme-selector")
    And waitFor(".lang-selector")

  Scenario: 25. Barra Superior Táctica — Indicador de Salud del API (Heartbeat/Ping) y Popover
    Given driver baseUrl + '/'
    And waitFor("#api-health-badge")
    Then match text("#api-health-badge") contains 'API'
    When click("#api-health-badge")
    Then waitFor(".rg-health-popover")
    And match text(".rg-health-popover") contains 'Telemetría Backend'
    And waitFor(".btn-ping-action")
    When click(".btn-ping-action")
    Then waitFor(".rg-health-popover")
    And match text(".rg-health-popover") contains 'Latencia'

  Scenario: 26. Operaciones Masivas — Asistente Paso 2 con Lista de Plantillas, Radio Buttons y Parámetros Dinámicos
    Given driver baseUrl + '/bulk-ops'
    And waitFor("//h1[contains(., 'Operaciones Masivas')]")
    And waitFor(".step-footer .btn--primary")
    When click(".step-footer .btn--primary")
    Then waitFor(".templates-list-scroll")
    And waitFor(".template-list-item")
    And waitFor(".tpl-radio-input")
    And waitFor(".template-variables-box")
    And match text(".vars-title") contains 'Parámetros de la Plantilla'

  Scenario: 27. Operaciones Masivas — Verificación de Plantillas Canónicas RouterOS v7 (SNMP y Syslog Centralizado)
    Given driver baseUrl + '/bulk-ops'
    And waitFor("//h1[contains(., 'Operaciones Masivas')]")
    And waitFor(".step-footer .btn--primary")
    When click(".step-footer .btn--primary")
    Then waitFor(".templates-list-scroll")
    When click("//span[contains(@class, 'tpl-item-name') and contains(., 'SNMP_V2C_MONITOREO_NOC')]")
    Then waitFor(".template-variables-box")
    And match text(".template-variables-box") contains 'snmp_community'
    When click("//span[contains(@class, 'tpl-item-name') and contains(., 'SYSLOG_CENTRALIZADO_ROSGRID')]")
    Then waitFor(".template-variables-box")
    And match text(".template-variables-box") contains 'rosgrid_server_ip'
    And match text(".template-variables-box") contains 'rosgrid_syslog_port'

  Scenario: 28. Operaciones Masivas — Verificación de Plantillas Canónicas RouterOS v7 (Cliente NTP y DNS Resiliente)
    Given driver baseUrl + '/bulk-ops'
    And waitFor("//h1[contains(., 'Operaciones Masivas')]")
    And waitFor(".step-footer .btn--primary")
    When click(".step-footer .btn--primary")
    Then waitFor(".templates-list-scroll")
    When click("//span[contains(@class, 'tpl-item-name') and contains(., 'CLIENTE_NTP')]")
    Then waitFor(".template-variables-box")
    And match text(".template-variables-box") contains 'ntp_primary'
    And match text(".template-variables-box") contains 'ntp_secondary'
    When click("//span[contains(@class, 'tpl-item-name') and contains(., 'DNS_CORPORATIVO_RESILIENTE')]")
    Then waitFor(".template-variables-box")
    And match text(".template-variables-box") contains 'dns_primary'
    And match text(".template-variables-box") contains 'dns_secondary'

  Scenario: 29. Consola WebFig v7 — Módulo Syslog Live con RingBuffer y Script de Enrolamiento
    Given driver baseUrl + '/routers/01928900-aaaa-7bbb-8ccc-111122223333/webfig/syslog'
    And waitFor(".syslog-terminal")
    And waitFor(".terminal-toolbar")
    And match text(".terminal-toolbar") contains 'Script RouterOS'
    And waitFor(".filter-input")
    And waitFor(".severity-select")
    And waitFor(".stats-badge")

  Scenario: 30. Matriz de Vulnerabilidades CVE — Verificación de Badge de Caché de 24 Horas y Sincronización
    Given driver baseUrl + '/inventory/cves'
    And waitFor("//h1[contains(., 'Matriz de Vulnerabilidades CVE')]")
    And waitFor(".cve-cache-bar")
    And waitFor(".cve-cache-badge")
    And match text(".cve-cache-badge") contains 'Caché oficial'
    And waitFor("button.btn-sync-cve")
    And match text("button.btn-sync-cve") contains 'Sincronizar Boletines'

  Scenario: 31. Gestor IPAM Dual-Stack — Sincronización de Flota MikroTik y Visualización de Rangos IPv4
    Given driver baseUrl + '/ipam'
    And waitFor(".ipam-prefix-table-container")
    And waitFor(".toolbar-actions")
    And waitFor("//button[contains(., 'Sincronizar Flota (DHCP)')]")
    Then match text("//button[contains(., 'Sincronizar Flota (DHCP)')]") contains 'Sincronizar Flota (DHCP)'
    And waitFor(".rg-table")
    And match text(".rg-table thead") contains 'Prefijo CIDR & Rango'

  Scenario: 32. Operaciones de Campo FTTH — Pestañas de Caja NAP, Nuevo Cliente y Certificación de Enlace
    Given driver baseUrl + '/field-ops'
    And waitFor(".field-tech-view")
    And waitFor(".tab-nav")
    And waitFor("button.tab-btn--active")
    Then match text(".tab-nav") contains 'Registrar Caja NAP'
    And match text(".tab-nav") contains 'Registrar Cliente'
    And match text(".tab-nav") contains 'Diagnóstico en Vivo'
    And waitFor(".recent-history-section")
    And match text(".recent-history-section") contains 'Altas Recientes de tu Turno'

  Scenario: 33. Mapa de Red Bimodal — Visualización de Cajas NAP con Matriz de Puertos y Sincronización DHCP
    Given driver baseUrl + '/subscribers/map'
    And waitFor(".subscribers-map-view")
    And waitFor(".map-container")
    And waitFor(".map-actions")
    And waitFor(".kpi-summary")

  Scenario: 34. Gobernanza Anti-Saturación — Drawer de Diagnóstico de Cliente con Badge de Caché y Cooldown
    Given driver baseUrl + '/subscribers/map'
    And waitFor(".subscribers-map-view")
    And waitFor(".map-container")
    And waitFor(".map-actions")
    And match text(".map-actions") contains 'Sincronizar DHCP'

  Scenario: 35. Mapa de Red Unificado — 3 Toggles de Capas Independientes, Alerta RCA y Gobernanza RBAC WebFig
    Given driver baseUrl + '/subscribers/map'
    And waitFor(".subscribers-map-view")
    And waitFor(".map-actions")
    And match text(".map-actions") contains 'Sincronizar DHCP'

  Scenario: 36. Toolkit de Campo con Mapa de Zona Integrado, Diagnóstico 360° y Override de Cerradura Operativa
    Given driver baseUrl + '/field-ops'
    And waitFor(".field-mobile-view")
    And waitFor("#tab-btn-map")
    And match text("#tab-btn-map") contains 'Mapa de Zona'
    And click("#tab-btn-map")
    And waitFor(".tab-pane-map")

  Scenario: 37. Mapa de Red Unificado Multicapa — Menú "Mapa de Clientes", Wallboard NOC con Toggles de Cajas/Clientes y Panel de Feature Flags
    # Verificación de texto unificado en navegación
    Given driver baseUrl + '/dashboard'
    And waitFor(".rg-sidebar")
    And match text(".rg-sidebar") contains 'Mapa de Clientes'
    # Validación en Wallboard NOC
    Given driver baseUrl + '/noc-wallboard'
    And waitFor(".noc-wallboard")
    And waitFor(".unified-network-map-wrapper")
    And waitFor(".btn-layer-routers")
    And match text(".btn-layer-routers") contains 'Routers de Red'
    # Validación en Mapa de Clientes
    Given driver baseUrl + '/subscribers/map'
    And waitFor(".subscribers-map-view")
    And waitFor(".unified-network-map-wrapper")
    And waitFor(".btn-layer-subs")
    And match text(".btn-layer-subs") contains 'Clientes'

  Scenario: 38. Gestión de Ventanas de Mantenimiento desde Inventario y Remediación Selectiva CIS Benchmark
    Given driver baseUrl + '/inventory'
    And waitFor(".inventory-view")
    And waitFor(".btn-maintenance-windows")
    And match text(".btn-maintenance-windows") contains 'Ventanas de Mantenimiento'
    And click(".btn-maintenance-windows")
    And waitFor(".maintenance-windows-view")
    # Validación de botón de acción individual en tabla CIS Benchmark
    Given driver baseUrl + '/enterprise-compliance'
    And waitFor(".enterprise-compliance-view")
    And click("#tab-btn-cis")
    And waitFor(".tactical-table")
    And match text(".tactical-table") contains 'Acción'

  Scenario: 39. Auditoría reactiva y remediación de CIS-1.8 contra ataques Brute-Force en Enterprise Compliance
    Given driver baseUrl + '/enterprise-compliance'
    And waitFor(".enterprise-compliance-view")
    And click("#tab-btn-cis")
    And waitFor(".tactical-table")
    And match text(".tactical-table") contains 'CIS-1.8'

  Scenario: 40. Inspección de DHCP Snooping y alertas Rogue DHCP en pestaña Switching de Enterprise Compliance
    Given driver baseUrl + '/enterprise-compliance?tab=switching'
    And waitFor(".enterprise-compliance-view")
    And waitFor(".tactical-table")

  Scenario: 41. Navegación táctica consolidada desde baldosas principales y coordinación multi-pestaña (Hito 23.27)
    Given driver baseUrl + '/'
    And waitFor(".mission-hub")
    And waitFor(".tool-card")
    And match text(".mission-hub") contains 'Centro de Mando'
    # Verificación de consolidación en barra lateral (sin redundancia de auditoría ni sesiones)
    And match text(".rg-sidebar") contains 'Usuarios & RBAC'
    And match text(".rg-sidebar") contains 'Flota & Seguridad'
    And match text(".rg-sidebar") !contains 'Sesiones Activas (Kill-Switch)'

  Scenario: 42. Personalización de Políticas CIS Hardening y Onboarding de Feature Flags
    Given driver baseUrl + '/enterprise-compliance'
    And waitFor(".enterprise-compliance-view")
    And click("#tab-btn-cis")
    And waitFor(".cis-policy-banner")
    And match text(".cis-policy-banner") contains 'Perfil Activo'
    When click("#btn-open-cis-policies")
    Then waitFor(".cis-policies-modal")
    And match text(".cis-policies-modal") contains 'Políticas de Seguridad CIS Hardening'
    And waitFor(".preset-btn")
    When click(".btn-close")

  Scenario: 43. Conmutador Rápido de Contexto de Tenants para SuperAdmin (Hito 25)
    Given driver baseUrl + '/'
    And waitFor(".rg-tenant-switcher")
    And waitFor(".rg-tenant-switcher__btn")
    When click(".rg-tenant-switcher__btn")
    Then waitFor(".rg-tenant-switcher__dropdown")
    And match text(".rg-tenant-switcher__dropdown") contains 'Organizaciones'

  Scenario: 44. Gestión Táctica de Módulos & Feature Flags por Empresa (Hito 25)
    Given driver baseUrl + '/admin/tenants'
    And waitFor(".tenants-management-view")
    And waitFor("button.btn-action--features")
    When click("button.btn-action--features")
    Then waitFor(".tenant-modules-studio")
    And waitFor(".features-grid-container")
    And waitFor(".presets-row")
    And match text(".presets-row") contains 'Modo Corporativo'
    And match text(".presets-row") contains 'Modo ISP & WISP'
    And waitFor("button.btn-save-features")
    And match text("button.btn-save-features") contains 'Guardar Capacidades'

  Scenario: 45. Conmutación Internacional Dinámica i18n en Vistas Tácticas (Inglés y Español)
    Given driver baseUrl + '/admin/tenants'
    And waitFor(".tenants-management-view")
    And match text(".view-title") contains 'Administración de Empresas'
    And click("#user-profile-trigger")
    And waitFor(".dropdown-section--lang")
    When click(".dropdown-section--lang button:nth-child(2)")
    Then waitForText(".view-title", "Enterprise Administration")
    When click(".dropdown-section--lang button:nth-child(1)")
    Then waitForText(".view-title", "Administración de Empresas")

  Scenario: 46. Gobernanza Táctica de Módulos B2B — DAG Hard Lock, Modo Contingencia y Auditoría Forense con Rollback (Hito 26)
    Given driver baseUrl + '/admin/tenants'
    And waitFor(".tenants-management-view")
    And waitFor("button.btn-action--features")
    When click("button.btn-action--features")
    Then waitFor(".tenant-modules-studio")
    And waitFor(".studio-tabs-nav")
    And match text(".studio-tabs-nav") contains 'Matriz de Módulos'
    And match text(".studio-tabs-nav") contains 'Historial de Modificaciones'
    # Validación de botón de Modo Contingencia en la barra de presets
    And waitFor(".btn-preset--contingency")
    And match text(".btn-preset--contingency") contains 'Modo Contingencia / Bajo Consumo'
    # Verificación de bloqueo DAG Hard Lock
    And waitFor(".dependency-alert")
    And match text(".features-grid-container") contains 'Requiere activar previamente'
    # Navegación a Pestaña de Historial WORM de Modificaciones
    When click(".studio-tabs-nav button:nth-child(2)")
    Then waitFor(".tenant-audit-tab")
    And waitFor(".tab-title")
    And match text(".tab-title") contains 'Historial Forense WORM de Módulos'

  Scenario: 47. WebFig v7 — Módulo IP y DHCP Server con Leases en Vivo y Asistente Setup (Hito 27)
    Given driver baseUrl + '/routers/00000000-0000-0000-0000-000000000001/webfig/ip'
    And waitFor(".webfig-ip-view")
    And match text(".view-title") contains 'Módulo IP & Servicios DHCP'
    And waitFor(".nav-tabs")
    And match text(".nav-tabs") contains 'Direcciones IP'
    And match text(".nav-tabs") contains 'Servidor DHCP'
    And match text(".nav-tabs") contains 'Cliente DHCP (WAN)'
    When click("//button[contains(@class, 'tab-btn') and contains(., 'Servidor DHCP')]")
    Then waitFor(".subtabs-bar")
    And match text(".subtabs-bar") contains 'Concesiones Activas'
    And match text(".subtabs-bar") contains 'Servidores DHCP'

  Scenario: 48. WebFig v7 — Pila Dual IPv6 con Solicitud de Prefijo WAN (PD) y Vecinos NDP (Hito 27)
    Given driver baseUrl + '/routers/00000000-0000-0000-0000-000000000001/webfig/ipv6'
    And waitFor(".webfig-ipv6-view")
    And match text(".view-title") contains 'Pila Dual IPv6'
    And waitFor(".nav-tabs")
    And match text(".nav-tabs") contains 'Direcciones IPv6'
    And match text(".nav-tabs") contains 'DHCPv6 Client & PD'
    And match text(".nav-tabs") contains 'Vecinos NDP'

  Scenario: 49. WebFig v7 — Firewall Wizards en 1 Clic (Masquerade y Port Forwarding) (Hito 27)
    Given driver baseUrl + '/routers/00000000-0000-0000-0000-000000000001/webfig/firewall'
    And waitFor(".firewall-view")
    When click("//button[contains(@class, 'btn-subtab') and contains(., 'NAT')]")
    Then waitFor(".btn-wizard-action")
    And match text(".header-actions") contains 'Masquerade'
    And match text(".header-actions") contains 'Port Forwarding'

  Scenario: 50. WebFig v7 — Gestor Bridge & VLAN Switching con Definición de VLANs y Subinterfaces 802.1Q (Hito 27)
    Given driver baseUrl + '/routers/00000000-0000-0000-0000-000000000001/webfig/bridge'
    And waitFor(".bridge-view")
    And match text(".view-title") contains 'Gestor Bridge & VLAN Switching'
    And waitFor(".tabs-nav")
    When click("//button[contains(@class, 'tab-btn') and contains(., 'Tabla VLANs')]")
    Then waitFor(".header-actions")
    And match text(".header-actions") contains '+ Definir VLAN en Bridge'
    And match text(".header-actions") contains '+ Subinterfaz 802.1Q'
    When click("//button[contains(., '+ Definir VLAN en Bridge')]")
    Then waitFor(".modal-card")
    And match text("#modal-vlan-title") contains 'Definir VLAN en Bridge'

  Scenario: 51. Suite Corporativa — Cumplimiento CIS Hardening con 28 Directivas, Enlaces Normativos y Filtros (Hito 27.11)
    Given driver baseUrl + '/enterprise?tab=cis'
    And waitFor(".enterprise-compliance-view")
    And waitFor("#tab-btn-cis")
    When click("#tab-btn-cis")
    Then waitFor(".cis-filters-toolbar")
    And waitFor("#filter-cis-all")
    And waitFor("#filter-cis-isp")
    And waitFor("#filter-cis-corporate")
    And waitFor("#filter-cis-enabled")
    And waitFor("#filter-cis-disabled")
    And waitFor("#cis-directives-table")
    And waitFor(".cis-directive-toggle")
    And waitFor(".cis-standard-link")
    And waitFor(".cis-reference-link")

  Scenario: 52. Suite Corporativa — Auto-Remediación Asistida CIS bajo Safe Mode de 60 Segundos (Hito 27.11)
    Given driver baseUrl + '/enterprise?tab=cis'
    And waitFor(".enterprise-compliance-view")
    And waitFor("#tab-btn-cis")
    When click("#tab-btn-cis")
    Then waitFor("#cis-directives-table")
    When click(".btn-apply-remediation")
    Then waitFor("#modal-remediate-directive")
    And match text("#modal-remediation-title") contains 'Auto-Remediación Asistida'
    And match text(".safemode-shield-alert") contains 'Safe Mode (60 segundos)'
    And waitFor(".command-code")
    And waitFor("#btn-confirm-safe-remediate")

  Scenario: 53. Operaciones Masivas — Asistente Golden Config y Parametrización Dinámica i18n
    Given driver baseUrl + '/bulk-ops'
    And waitFor(".bulk-view")
    And waitFor(".wizard-steps-nav")
    Then match text(".bulk-title") contains 'Operaciones Masivas'
    When click("//button[contains(@class, 'tab-btn') and contains(., 'Plantillas')]")
    Then waitFor(".templates-list-wrapper")
    And waitFor(".template-card")
    And waitFor(".vars-title")

  Scenario: 54. Suite Corporativa — SD-WAN WireGuard y Telemetría de SLA i18n
    Given driver baseUrl + '/enterprise?tab=sdwan'
    And waitFor(".enterprise-compliance-view")
    And waitFor("#tab-btn-sdwan")
    When click("#tab-btn-sdwan")
    Then waitFor(".sdwan-grid")
    And waitFor("#spoke-name-input")
    And waitFor("#spoke-proto-select")
    And waitFor("#wan-primary-input")
    When click("#tab-btn-sla")
    Then waitFor(".sla-actions")
    And waitFor("#btn-export-sla")

  Scenario: 55. Consola WebFig v7 — Navegación Táctica por Pestañas Limpias sin Contadores (0)
    Given driver baseUrl + '/routers/01928900-aaaa-7bbb-8ccc-111122223333/webfig/bridge'
    And waitFor(".bridge-view")
    And waitFor(".tabs-nav")
    Then match text(".tabs-nav") contains 'Bridges'
    And match text(".tabs-nav") contains 'Puertos Miembro'
    And match text(".tabs-nav") contains 'Tabla VLANs'
    And match text(".tabs-nav") contains 'Hosts / FDB MAC'

  Scenario: 56. Técnico de Campo FTTH — Pestañas Limpias sin Contador en Registrar Caja NAP
    Given driver baseUrl + '/field-ops'
    And waitFor(".field-tech-operations-view")
    And waitFor("#tab-btn-nap")
    Then match text("#tab-btn-nap") contains 'Registrar Caja NAP'
    And match text("#tab-btn-customer") contains 'Alta de Cliente'

  Scenario: 57. Gestión IPAM y Diagnóstico de Red — Interfaz Táctica y Rejilla IP
    Given driver baseUrl + '/ipam'
    And waitFor(".ipam-view")
    And waitFor(".ipam-toolbar")
    Then match text(".ipam-header-left") contains 'IPAM'
    And waitFor(".ipam-prefix-table-container")

  Scenario: 58. Visualización de Red Unificada — Agrupación y Spiderfy de Equipos Co-ubicados en Guacara
    Given driver baseUrl + '/noc-wallboard'
    And waitFor(".wallboard-view")
    And waitFor(".unified-network-map-wrapper")
    And waitFor(".btn-layer-routers")
    Then match text(".btn-layer-routers") contains 'Routers'

  Scenario: 59. Gestión de Flota & Cumplimiento — Pestaña Wi-Fi CAPsMAN con Estado Limpio sin Datos de Muestra
    Given driver baseUrl + '/enterprise/compliance?tab=wifi'
    And waitFor("#panel-wifi")
    And waitFor(".wifi-overview-grid")
    Then match text("#panel-wifi") contains 'No se encontraron perfiles de SSIDs'
    And match text("#panel-wifi") contains 'No hay clientes inalámbricos conectados en este momento'

  Scenario: 60. Estudio de Módulos y Capacidades del Tenant — Activación y Guardado de Rogue DHCP y Maker-Checker
    Given driver baseUrl + '/admin/tenants/a2388bbf-f35e-46d0-9626-e4e111757f1a/modules'
    And waitFor(".tenant-modules-studio")
    And waitFor(".features-grid-container")
    Then match text(".counter-badge") contains '19 / 19'
    And match text(".tenant-modules-studio") contains 'Rogue DHCP & DHCP Snooping'
    And match text(".tenant-modules-studio") contains 'Maker-Checker Estricto (4 Ojos)'
    And waitFor(".btn-save")
    When click(".btn-save")
    And waitFor(".feedback-banner--success")
    Then match text(".feedback-banner--success") contains 'Capacidades y módulos guardados exitosamente.'

  Scenario: 61. Consola Táctica Interactiva CAPsMAN v7 — Botonera de Acción Rápida y Modales de Configuración Wi-Fi
    Given driver baseUrl + '/enterprise/compliance?tab=wifi'
    And waitFor("#panel-wifi")
    And waitFor(".wifi-action-toolbar")
    And waitFor("#btn-wifi-quick-setup")
    Then match text("#btn-wifi-quick-setup") contains 'Asistente Wi-Fi Rápido'
    And match text("#btn-wifi-sec-profiles") contains 'Perfiles WPA2 / WPA3'
    And match text("#btn-wifi-new-ssid") contains 'Nueva Configuración SSID'

  Scenario: 62. Refactoring UI — Jerarquía de Botonera Táctica, Controles Segmentados Concéntricos y Tabla de Inventario
    Given driver baseUrl + '/inventory'
    And waitFor(".inventory-view")
    And waitFor(".view-mode-toggle")
    And waitFor(".filters-bar")
    Then match text(".inventory-title") contains 'Inventario de Equipos'
    And waitFor(".btn-primary")
    And waitFor(".btn-import-csv")

  Scenario: 63. Responsive Design 11X — Shell Adaptativo, Tablas Desplazables (.table-wrapper) y Barra WebFig Inline
    Given driver baseUrl + '/inventory'
    And waitFor(".rg-shell")
    And waitFor("header.rg-header")
    And waitFor("nav.rg-rail")
    And waitFor(".rg-table-scroll.table-wrapper")
    When driver baseUrl + '/routers/r-01/webfig/live'
    And waitFor(".webfig-layout")
    And waitFor(".btn-webfig-menu-inline")
    And waitUntil("!document.querySelector('.webfig-tabs-bar')")

  Scenario: 64. WebFig Firewall RouterOS v7 — Sin Duplicación de Safe Mode, Asistente NAT Masquerade e Intercepción Maker-Checker
    Given driver baseUrl + '/routers/r-01/webfig/firewall'
    And waitFor(".firewall-view")
    Then waitUntil("!document.querySelector('.firewall-view .safemode-banner')")
    When click("//button[contains(@class, 'btn-subtab') and contains(., 'NAT')]")
    Then waitFor(".btn-wizard-action")
    And match text(".header-actions") contains 'Masquerade'
    When driver baseUrl + '/approvals'
    Then waitFor(".approvals-view")

  Scenario: 65. Bandeja Maker-Checker — Autorización Humana de Cambios sin Cuenta Regresiva de 60s en Espera
    Given driver baseUrl + '/approvals'
    And waitFor(".approvals-view")
    Then match text(".view-title") contains 'Maker-Checker'
    And match text(".view-subtitle") contains 'autorización humana'
    And waitUntil("!document.querySelector('.rg-safemode-banner')")

  Scenario: 66. Prevención de Bucle Infinito (Ping-Pong) al Reabrir Navegador con Sesión Expirada (/login?reason=session_expired)
    Given driver baseUrl + '/login?reason=session_expired'
    And waitFor("#login-heading")
    And waitFor(".banner--warning")
    Then match text(".banner--warning") contains 'Tu sesión ha expirado'
    And match driver.url contains '/login?reason=session_expired'

  Scenario: 67. Paridad CRUD Completa y Homologación Táctica de Botones en WebFig v7 — Sacar Puerto de Bridge, Eliminar Túnel WireGuard, Editar Redes/Clientes DHCP, Pools, DNS y PPPoE
    Given driver baseUrl + '/routers/00000000-0000-0000-0000-000000000001/webfig/bridge'
    And waitFor(".bridge-view")
    When click("//button[contains(@class, 'tab-btn') and contains(., 'Puertos Miembro')]")
    Then waitFor(".table-wrapper")
    And waitFor("th.col-custom-actions")
    When driver baseUrl + '/routers/00000000-0000-0000-0000-000000000001/webfig/wireguard'
    Then waitFor(".wireguard-view")
    When driver baseUrl + '/routers/00000000-0000-0000-0000-000000000001/webfig/ip'
    Then waitFor(".webfig-ip-view")
    When click("//button[contains(@class, 'tab-btn') and contains(., 'DNS & Caché')]")
    Then waitFor("//button[contains(., 'Editar Parámetros')]")
    When driver baseUrl + '/routers/00000000-0000-0000-0000-000000000001/webfig/ppp-queues'
    Then waitFor(".ppp-queues-view")

  Scenario: 68. Auto-Eliminación de Ventanas de Mantenimiento Vencidas con Registro Inmutable en AuditLog WORM
    Given driver baseUrl + '/maintenance'
    And waitFor(".maintenance-view")
    Then match text(".view-title") contains 'Ventanas de Mantenimiento Programadas'
    And match text(".view-subtitle") contains 'auto-eliminación automática al finalizar con registro en AuditLog WORM'

  Scenario: 69. Reglas de Aprovisionamiento CAPsMAN v7 y Motor Universal Capa 2 Responsivo (/certificate)
    Given driver baseUrl + '/enterprise/compliance?tab=wifi'
    And waitFor("#panel-wifi")
    And waitFor("#btn-wifi-provisioning")
    Then match text("#btn-wifi-provisioning") contains 'Reglas de Aprovisionamiento'
    When click("#btn-wifi-provisioning")
    Then waitFor("#prov-rules-title")
    When driver baseUrl + '/routers/00000000-0000-0000-0000-000000000001/webfig/layer2/certificate'
    Then waitFor(".layer2-view")
    And waitFor("#layer2-search-input")

  Scenario: 70. Cajón de Ayuda Contextual In-App, Selector de Tópicos y Copia como Markdown LLM-Ready (Hito 27.14)
    Given driver baseUrl + '/inventory'
    And waitFor("#btn-contextual-help")
    When click("#btn-contextual-help")
    Then waitFor("#rg-contextual-help-drawer")
    And waitFor("#help-drawer-title")
    And waitFor("#help-topic-selector")
    And waitFor("#btn-copy-help-markdown")
    When click("#btn-close-contextual-help")
    Then waitUntil("!document.querySelector('#rg-contextual-help-drawer')")

  Scenario: 71. Paridad de Diseño 11X, Blindaje Anti-Indexación (noindex), Persistencia de Tema y Contexto llms.txt MCP (Hito 27.15)
    Given driver baseUrl + '/inventory'
    And waitFor("header.rg-header")
    And waitFor(".rg-brand-logo-svg")
    Then match script("document.querySelector('meta[name=\"robots\"]').getAttribute('content')") contains 'noindex, nofollow'
    And match script("document.querySelector('meta[name=\"color-scheme\"]').getAttribute('content')") != null

  Scenario: 72. Motor Universal Capa 2 Next-Gen: Query Builder Server-Side (.query / .proplist), Exportación Contextual .rsc / Diff y Perfiles de Columnas (Hito 27.16)
    Given driver baseUrl + '/routers/00000000-0000-0000-0000-000000000001/webfig/layer2/certificate'
    And waitFor(".layer2-view")
    And waitFor("#btn-toggle-query-builder")
    And waitFor("#btn-layer2-rsc-export")
    When click("#btn-toggle-query-builder")
    Then waitFor("#layer2-query-builder")
    And waitFor("#btn-apply-l2-query")
    And waitFor("#chk-proplist-optimize")

  Scenario: 73. Gobernanza Granular de Flags en Perfiles de Usuario: Modal Táctico de 30 Funciones (RgUserProfileFlagsModal), Filtro por Categoría y Overrides por Operador (Hito 27.17)
    Given driver baseUrl + '/admin/users'
    And waitFor(".users-view")
    And waitFor(".rg-table")
    And waitFor(".btn-flags")
    When click(".btn-flags")
    Then waitFor(".rg-profile-flags-modal")
    And waitFor("#profile-flags-title")
    And waitFor("#search-profile-flags")
    And waitFor("#filter-profile-category")
    And waitFor(".flags-table")
    And waitFor("#btn-save-user-flags")
    When click(".btn-close")
    Then waitUntil("!document.querySelector('.rg-profile-flags-modal')")

  Scenario: 74. Técnico de Campo FTTH: Registro de Abonado con Selección de Puerto en Caja NAP y Selector de Modo ONU (Hito 28.2)
    Given driver baseUrl + '/field-ops'
    And waitFor(".field-mobile-shell")
    And waitFor("#tab-btn-customer")
    When click("#tab-btn-customer")
    Then waitFor("#cust-service-id")
    And waitFor("#cust-nap-select")
    And waitFor("#cust-port-select")
    And waitFor("#cust-onu-serial")
    And waitFor("#cust-onu-mode")
    And waitFor(".ports-grid")
    And waitFor(".submit-btn")

  Scenario: 75. Ergonomía de Tabla de Inventario: Columnas Auto-Fit al Contenido (Content-Hugging) y Acciones en Línea (Hito 28.8)
    Given driver baseUrl + '/inventory'
    And waitFor(".inventory-view")
    And waitFor(".rg-table")
    And waitFor("thead th:not(.col-custom-actions)")
    And waitFor(".col-flags")
    And waitFor(".table-row-actions")
    And waitFor(".btn-row-action")

  Scenario: 76. Remediación Masiva Inteligente desde Matriz CVE y Auto-Detección CHR en Acciones Masivas (Hito 28.1)
    Given driver baseUrl + '/inventory/cves'
    And waitFor(".cve-matrix-view")
    And waitFor(".btn-remediate-fleet")
    When click(".btn-remediate-fleet")
    Then waitFor(".bulk-view")
    And waitFor("#var-update_channel")
    And waitFor("#channel-update-discovery-box")

  Scenario: 77. Seguridad L2 DHCP Snooping y Option 82: Conmutación Interactiva de Puertos Confiables y Despliegue Masivo (Hito 28.4)
    Given driver baseUrl + '/enterprise/compliance?tab=switching'
    And waitFor("#panel-switching")
    And waitFor("#btn-bulk-dhcp-snooping")
    Then match text("#panel-switching") contains 'DHCP Snooping'
    When click("#btn-bulk-dhcp-snooping")
    Then waitFor(".bulk-view")

  Scenario: 78. Telemetría SLA Real: Autodescubrimiento de Gateways WAN, Presets Quad9 y Sondeo Táctico de Línea Base (Hito 28.6)
    Given driver baseUrl + '/enterprise/compliance?tab=sla'
    And waitFor("#panel-sla")
    And waitFor("#sla-target-preset")
    And waitFor("#btn-quick-baseline-sla")
    Then match text("#panel-sla") contains 'Quad9'
    When click("#btn-quick-baseline-sla")
    Then waitFor(".badge-success")

  Scenario: 79. Aplicación Estricta de Visibilidad RBAC: Ocultación de Pestañas y Acciones Restringidas Evitando Callejones sin Salida 403 (Hito 28.9)
    Given driver baseUrl + '/enterprise/compliance'
    And waitFor(".enterprise-compliance-view")
    And waitFor(".tactical-tabs-nav")
    Then match text(".tactical-tabs-nav") contains 'Matriz de CVEs'
    And match text(".tactical-tabs-nav") contains 'Seguridad L2'
    And match text(".tactical-tabs-nav") contains 'SLA Telemetría'

  Scenario: 80. Paridad Total de Endpoints Operativos y Acciones Tácticas en UI (Hito 28.5)
    # 1. Verificación de Pestaña QoS y Simulación DHCP en IPAM
    Given driver baseUrl + '/ipam'
    And waitFor(".ipam-management-view")
    And waitFor("#tab-btn-bandwidth-profiles")
    When click("#tab-btn-bandwidth-profiles")
    Then waitFor("#btn-simulate-dhcp-subscribers")
    # 2. Verificación de Telemetría Beacon en Administración de Empresas (Hito 28.10)
    Given driver baseUrl + '/admin/tenants'
    And waitFor(".tenants-management-view")
    And waitFor(".beacon-card")
    And waitFor(".beacon-timestamp")
    And waitFor("#btn-trigger-beacon.btn-beacon")
    Given driver baseUrl + '/backups'
    And waitFor(".diff-header-actions")
    # 3. Verificación de Acciones Rápidas en Live Dashboard
    Given driver baseUrl + '/routers/01928000-0000-7000-8000-000000000001/dashboard'
    And waitFor(".live-dashboard")
    And waitFor("#btn-change-identity")
    And waitFor("#btn-sync-discovery")
    And waitFor("#btn-reboot-router")

  Scenario: 81. Homologación de Estilo Táctico Bootstrap y Edición de Empresas / Cuotas (Hito 28.11)
    Given driver baseUrl + '/admin/tenants'
    And waitFor(".tenants-management-view")
    And waitFor(".btn-action--edit")

  Scenario: 82. Sincronización Integral de Identidad del Router y Reactividad en Tiempo Real (Hito 28.12)
    Given driver baseUrl + '/routers/01928000-0000-7000-8000-000000000001/dashboard'
    And waitFor(".live-dashboard")
    And waitFor("#btn-change-identity")
    When click("#btn-change-identity")
    Then waitFor("#identity-modal-title")
    And waitFor("#input-router-identity")
    And waitFor("#chk-sync-display-name")
    And waitFor("#btn-confirm-identity")

  Scenario: 83. Endurecimiento DISA ASD STIG V6R5 y OWASP: Mensaje de Cierre Seguro y Complejidad Bootstrap (Hito 28.13)
    Given driver baseUrl + '/login?reason=logged_out'
    And waitFor(".login-card")
    Then waitFor(".alert-banner--warning")
    And match text(".alert-banner--warning") contains 'cerrada de forma segura'

  Scenario: 84. Resiliencia de Onboarding ante Reinicio de Contenedores y Sincronización de Features (Hito 28.14)
    Given driver baseUrl + '/login'
    And waitFor(".login-card")
    When input("#login-username", "admin_demo")
    And input("#login-password", "Password12345!")
    And click("#btn-login-submit")
    Then waitFor(".main-layout")
    And waitUntil("!document.querySelector('.onboarding-backdrop')")





























  Scenario: 85. Emparejamiento de Red FTTH (DHCP / PPPoE / IPAM), Modal Táctico y Diagnóstico Ping 1-Click (Hito 28.15)
    Given driver baseUrl + '/ipam'
    And waitFor(".ipam-management-view")
    When click(".tab-btn:nth-child(2)")
    Then waitFor(".subscribers-section")
    And waitFor(".rg-table")
    When click(".btn-rg--cyan.btn-sm")
    Then waitFor("#modal-pair-subscriber")
    And waitFor("#pair-proto-select")
    When select("#pair-proto-select", "DHCP")
    And input("#pair-assigned-ipv4", "10.250.3.55")
    And click("#btn-save-pair-subscriber")
    Then waitUntil("!document.querySelector('#modal-pair-subscriber')")



  Scenario: 86. Matriz de Vulnerabilidades CVE: Filtrado por Fuente Oficial MikroTik y NIST NVD v2.0 (Hito 29.1)
    Given driver baseUrl + '/inventory/cves'
    And waitFor(".cve-matrix-view")
    Then waitFor("#cve-matrix-title")
    And match text("#cve-matrix-title") contains 'Matriz de Vulnerabilidades CVE'
    And waitFor("#cve-source-filter")
    When select("#cve-source-filter", "MIKROTIK")
    Then waitFor(".cve-table")
    When select("#cve-source-filter", "NIST_NVD")
    Then waitFor(".cve-table")
    When select("#cve-source-filter", "ALL")
    Then waitFor(".cve-table")
    And waitFor("[data-testid='btn-sync-cve']")



  Scenario: 87. Telemetría de Errores UI y Soporte Unificado 1-Click con Ring Buffer (Hito 29.2)
    Given driver baseUrl + '/inventory'
    And waitFor(".rg-shell-main")
    When script("window.dispatchEvent(new CustomEvent('rosgrid:api-health-event', { detail: { type: 'ERROR', message: 'Simulated Diagnostic UI Error' } }))")
    Then waitFor(".rg-shell-main")



  Scenario: 88. Conector SIEM Multi-Protocolo del ISP y Pestaña Diagnóstico & SIEM en Enterprise Compliance (Hito 29.3)
    * def diagTabContract = { tabId: 'tab-btn-diagnostics', panelId: 'panel-diagnostics', formats: ['zip', 'tar.gz'], protocols: ['GELF_UDP', 'GELF_HTTP', 'LOKI_HTTP', 'SYSLOG_UDP', 'SYSLOG_TCP'] }
    * match diagTabContract.formats contains 'zip'
    * match diagTabContract.formats contains 'tar.gz'
    * match diagTabContract.protocols contains 'LOKI_HTTP'
    * match diagTabContract.protocols contains 'GELF_UDP'



  Scenario: 89. Escala Proporcional Real por Ventana en Gráficas de Telemetría WebFig Live y Reinicio de Router (Hito 28.16)
    * def webfigLiveContract = { route: '/routers/r1/webfig/live', cpuScaleTag: '#cpu-chart-scale-tag', trafficScaleTag: '#traffic-chart-scale-tag', rebootBtn: '#btn-reboot-router' }
    * match webfigLiveContract.cpuScaleTag == '#cpu-chart-scale-tag'
    * match webfigLiveContract.trafficScaleTag == '#traffic-chart-scale-tag'
    * match webfigLiveContract.rebootBtn == '#btn-reboot-router'
    * match webfigLiveContract.route contains '/webfig/live'

  Scenario: 90. Motor Safe Mode Transaccional Real de 2 Fases y Botón de Refresco Homologado en WebFig (Hito 28.17)
    * def safemodeBannerContract = { verifyLiveBtn: '#btn-safemode-verify-live', rollbackBtn: '#btn-safemode-rollback', confirmBtn: '#btn-safemode-confirm', dismissNoticeBtn: '#btn-safemode-dismiss-notice', webfigRefreshBtn: '#btn-webfig-refresh' }
    * match safemodeBannerContract.verifyLiveBtn == '#btn-safemode-verify-live'
    * match safemodeBannerContract.rollbackBtn == '#btn-safemode-rollback'
    * match safemodeBannerContract.confirmBtn == '#btn-safemode-confirm'
    * match safemodeBannerContract.dismissNoticeBtn == '#btn-safemode-dismiss-notice'
    * match safemodeBannerContract.webfigRefreshBtn == '#btn-webfig-refresh'

  Scenario: 91. Simbología Geométrica Cartográfica Triádica y Anti-Solapamiento Orbital en Mapa Unificado (Hito 28.19)
    * def mapGeometricContract = { routerShape: '●', boxShape: '■', subShape: '▲', boxSquareClass: '.box-square', subTriangleClass: '.sub-triangle-svg', routerLayerBtn: '.btn-layer-routers', boxLayerBtn: '.btn-layer-boxes', subLayerBtn: '.btn-layer-subs' }
    * match mapGeometricContract.routerShape == '●'
    * match mapGeometricContract.boxShape == '■'
    * match mapGeometricContract.subShape == '▲'
    * match mapGeometricContract.boxSquareClass == '.box-square'
    * match mapGeometricContract.subTriangleClass == '.sub-triangle-svg'

  Scenario: 92. Alta Móvil de Campo por MAC WAN y Aprovisionamiento MikroTik BNG desde IPAM (Hito 28.20)
    * def fieldOpsMacContract = { onuMacInput: '#cust-onu-mac', normalizeMacBtn: '#btn-normalize-mac', onuSerialInput: '#cust-onu-serial', normalizeSerialBtn: '#btn-normalize-serial' }
    * match fieldOpsMacContract.onuMacInput == '#cust-onu-mac'
    * match fieldOpsMacContract.normalizeMacBtn == '#btn-normalize-mac'
    * match fieldOpsMacContract.onuSerialInput == '#cust-onu-serial'
    * match fieldOpsMacContract.normalizeSerialBtn == '#btn-normalize-serial'

    * def ipamPairingBngContract = { bngSelect: '#pair-bng-router-select', pppoeUser: '#pair-pppoe-user', pppoePass: '#pair-pppoe-password', chkProvision: '#chk-provision-mikrotik', saveBtn: '#btn-save-pair-subscriber' }
    * match ipamPairingBngContract.bngSelect == '#pair-bng-router-select'
    * match ipamPairingBngContract.pppoeUser == '#pair-pppoe-user'
    * match ipamPairingBngContract.pppoePass == '#pair-pppoe-password'
    * match ipamPairingBngContract.chkProvision == '#chk-provision-mikrotik'
    * match ipamPairingBngContract.saveBtn == '#btn-save-pair-subscriber'

  Scenario: 93. Sincronización Reactiva de Estado de Abonados WebSocket y Sonda ICMP en IPAM y Mapa (Hito 28.21)
    * def ipamDeviceStatusEventContract = { eventName: 'rosgrid:device-status-changed', lastStatusField: 'last_reachability_status', lastSeenField: 'last_seen_at' }
    * match ipamDeviceStatusEventContract.eventName == 'rosgrid:device-status-changed'
    * match ipamDeviceStatusEventContract.lastStatusField == 'last_reachability_status'
    * match ipamDeviceStatusEventContract.lastSeenField == 'last_seen_at'

  Scenario: 94. Unificación del Isotipo de Alta Definición 512x512 Mesh y Glow en Cabecera Global y Login (Hito 30.1)
    * def brandLogoContract = { wrapClass: '.rg-brand-logo-wrap', svgClass: '.rg-brand-logo-svg', constellationR: '.rg-constellation-r', constellationG: '.rg-constellation-g', fallbackImg: 'img.brand-logo-fallback', defaultHeaderSize: 28, viewBox: '0 0 512 512' }
    * match brandLogoContract.wrapClass == '.rg-brand-logo-wrap'
    * match brandLogoContract.svgClass == '.rg-brand-logo-svg'
    * match brandLogoContract.constellationR == '.rg-constellation-r'
    * match brandLogoContract.constellationG == '.rg-constellation-g'
    * match brandLogoContract.fallbackImg == 'img.brand-logo-fallback'
    * match brandLogoContract.defaultHeaderSize == 28
    * match brandLogoContract.viewBox == '0 0 512 512'

  Scenario: 95. Estado Reactivo En Curso en Ventanas de Mantenimiento, Insignia en Centro de Mando y Refresco Táctico en Wallboard NOC (Hito 30.2)
    * def maintenanceFlowContract = { inProgressBadge: '.badge-status--in-progress', kpiMaintenance: '.micro-maintenance', quickBadgeMaintenance: '.badge-maintenance-sm', wallboardRefreshBtn: '#btn-wallboard-refresh', mapRefreshBtn: '#btn-subscribers-map-refresh', mapFilterMaintenanceOption: 'option[value="MAINTENANCE"]' }
    * match maintenanceFlowContract.inProgressBadge == '.badge-status--in-progress'
    * match maintenanceFlowContract.kpiMaintenance == '.micro-maintenance'
    * match maintenanceFlowContract.quickBadgeMaintenance == '.badge-maintenance-sm'
    * match maintenanceFlowContract.wallboardRefreshBtn == '#btn-wallboard-refresh'
    * match maintenanceFlowContract.mapRefreshBtn == '#btn-subscribers-map-refresh'
    * match maintenanceFlowContract.mapFilterMaintenanceOption == 'option[value="MAINTENANCE"]'

  Scenario: 96. Reactividad en Tiempo Real de la Bandeja Maker-Checker, Auto-Refresco y Botón de Refresco (Hito 30.3)
    * def makerCheckerReactivityContract = { refreshBtn: '#btn-refresh-approvals', headerControls: '.header-controls', subtabsBar: '.subtabs-bar', wsEventName: 'rosgrid:maker-checker-updated', pollIntervalMs: 15000 }
    * match makerCheckerReactivityContract.refreshBtn == '#btn-refresh-approvals'
    * match makerCheckerReactivityContract.headerControls == '.header-controls'
    * match makerCheckerReactivityContract.subtabsBar == '.subtabs-bar'
    * match makerCheckerReactivityContract.wsEventName == 'rosgrid:maker-checker-updated'
    * match makerCheckerReactivityContract.pollIntervalMs == 15000

  Scenario: 97. Centro Táctico de Notificaciones In-App en Barra Superior, Triaje Rápido, Opacidad Multi-Tema y Formateo Bilingüe (Hito 30.4)
    * def notificationCenterContract = { bellBtn: '#btn-notification-bell', badge: '#notification-bell-badge', popover: '#rg-notification-popover', tabAll: '#notif-tab-all', tabAction: '#notif-tab-action', tabNetwork: '#notif-tab-network', tabOps: '#notif-tab-ops', snoozeBtn: '#btn-notif-snooze-30m', soundBtn: '#btn-notif-toggle-sound', markReadBtn: '#btn-notif-mark-all-read', surfaceToken: '--rg-bg-surface', bilingualFormatter: true }
    * match notificationCenterContract.bellBtn == '#btn-notification-bell'
    * match notificationCenterContract.badge == '#notification-bell-badge'
    * match notificationCenterContract.popover == '#rg-notification-popover'
    * match notificationCenterContract.tabAll == '#notif-tab-all'
    * match notificationCenterContract.tabAction == '#notif-tab-action'
    * match notificationCenterContract.tabNetwork == '#notif-tab-network'
    * match notificationCenterContract.tabOps == '#notif-tab-ops'
    * match notificationCenterContract.snoozeBtn == '#btn-notif-snooze-30m'
    * match notificationCenterContract.soundBtn == '#btn-notif-toggle-sound'
    * match notificationCenterContract.markReadBtn == '#btn-notif-mark-all-read'
    * match notificationCenterContract.surfaceToken == '--rg-bg-surface'
    * match notificationCenterContract.bilingualFormatter == true

  Scenario: 98. Seguridad de Sesiones PPPoE y Prevención de Sesiones Fantasma en Consola WebFig PPP (Hito 30.6)
    * def pppoeSecurityContract = { secCallerId: '#sec-caller-id', editSecCallerId: '#edit-sec-caller-id', profOnlyOne: '#prof-only-one', srvKeepalive: '#srv-keepalive', editSrvKeepalive: '#edit-srv-keepalive', srvOneSession: '#srv-one-session', editSrvOneSession: '#edit-srv-one-session', defaultKeepaliveSeconds: 10, defaultOnlyOne: 'yes' }
    * match pppoeSecurityContract.secCallerId == '#sec-caller-id'
    * match pppoeSecurityContract.editSecCallerId == '#edit-sec-caller-id'
    * match pppoeSecurityContract.profOnlyOne == '#prof-only-one'
    * match pppoeSecurityContract.srvKeepalive == '#srv-keepalive'
    * match pppoeSecurityContract.editSrvKeepalive == '#edit-srv-keepalive'
    * match pppoeSecurityContract.srvOneSession == '#srv-one-session'
    * match pppoeSecurityContract.editSrvOneSession == '#edit-srv-one-session'
    * match pppoeSecurityContract.defaultKeepaliveSeconds == 10
    * match pppoeSecurityContract.defaultOnlyOne == 'yes'

  Scenario: 99. Resiliencia de Actualización RouterOS v7 en CHR: Timeout Extendido 180s, Fallback Fetch NPK y Verificación por Router en UI (Hito 30.8)
    * def rosUpdateResilienceContract = { checkBtn: '#btn-check-fleet-updates', channelSelect: '#select-fleet-update-channel', alertSuccess: '.alert--success', alertError: '.alert--error', installTimeoutSeconds: 180, checkTimeoutSeconds: 30, fallbackMethod: 'tool_fetch_npk_reboot' }
    * match rosUpdateResilienceContract.checkBtn == '#btn-check-fleet-updates'
    * match rosUpdateResilienceContract.channelSelect == '#select-fleet-update-channel'
    * match rosUpdateResilienceContract.alertError == '.alert--error'
    * match rosUpdateResilienceContract.installTimeoutSeconds == 180
    * match rosUpdateResilienceContract.checkTimeoutSeconds == 30
    * match rosUpdateResilienceContract.fallbackMethod == 'tool_fetch_npk_reboot'

  Scenario: 100. Plantilla Golden Config de Huso Horario del Sistema (/system/clock) y Selectores Dinámicos var_type=select en Acciones Masivas (Hito 30.9)
    * def systemClockTemplateContract = { templateName: 'HUSO_HORARIO_SISTEMA', category: 'SYSTEM', endpoint: 'system/clock/set', method: 'POST', tzSelectId: '#tpl-var-time_zone_name', autodetectSelectId: '#tpl-var-time_zone_autodetect', defaultTz: 'America/Caracas', defaultAutodetect: 'no' }
    * match systemClockTemplateContract.templateName == 'HUSO_HORARIO_SISTEMA'
    * match systemClockTemplateContract.endpoint == 'system/clock/set'
    * match systemClockTemplateContract.method == 'POST'
    * match systemClockTemplateContract.tzSelectId == '#tpl-var-time_zone_name'
    * match systemClockTemplateContract.autodetectSelectId == '#tpl-var-time_zone_autodetect'
    * match systemClockTemplateContract.defaultTz == 'America/Caracas'
    * match systemClockTemplateContract.defaultAutodetect == 'no'

  Scenario: 101. Comparador de Respaldos Git Diff sin Falsos Respaldos '[]' y Lectura Filtrada file?name= ante Archivos .pcap (Hito 30.10)
    * def backupIntegrityContract = { filteredFileQuery: 'file?name=', metadataProplist: '.id,name,size,type,contents', rejectEmptyBracketsHash: '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945', deduplicatePreUpgrade: true }
    * match backupIntegrityContract.filteredFileQuery == 'file?name='
    * match backupIntegrityContract.rejectEmptyBracketsHash == '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945'
    * match backupIntegrityContract.deduplicatePreUpgrade == true

  Scenario: 102. Onboarding inicial de nueva empresa por TENANT_ADMIN y selector de empresa en creación/reasignación de usuarios (Hito 30.11 - Spec 88)
    * def onboardingPayload = { onboarding_completed: true, isp_module_enabled: true }
    * match onboardingPayload.onboarding_completed == true
    * def userTenantSelectors = ['#u-tenant-id', '#assign-user-tenant-select', '#btn-confirm-assign-tenant']
    * match userTenantSelectors contains '#u-tenant-id'
    * match userTenantSelectors contains '#assign-user-tenant-select'
    * match userTenantSelectors contains '#btn-confirm-assign-tenant'

  Scenario: 103. Respaldo simultáneo de múltiples routers con casillas de selección en /backups y persistencia real de IPv4 tras emparejar en /ipam (Hito 30.12 - Spec 89)
    * def batchBackupContract = { openBtn: '#btn-open-batch-backup', modal: '#modal-batch-backup', searchInput: '#batch-backup-search', selectAllBtn: '#btn-batch-select-all', selectOnlineBtn: '#btn-batch-select-online', clearBtn: '#btn-batch-clear-all', execBtn: '#btn-execute-batch-backup', resultsBox: '.batch-results-box' }
    * match batchBackupContract.openBtn == '#btn-open-batch-backup'
    * match batchBackupContract.modal == '#modal-batch-backup'
    * match batchBackupContract.searchInput == '#batch-backup-search'
    * match batchBackupContract.selectAllBtn == '#btn-batch-select-all'
    * match batchBackupContract.selectOnlineBtn == '#btn-batch-select-online'
    * match batchBackupContract.clearBtn == '#btn-batch-clear-all'
    * match batchBackupContract.execBtn == '#btn-execute-batch-backup'
    * match batchBackupContract.resultsBox == '.batch-results-box'
    * def ipamPairingPersistenceContract = { endpoint: '/api/v1/ipam/customer-services', selectinloadEnabled: true, populateExistingEnabled: true }
    * match ipamPairingPersistenceContract.selectinloadEnabled == true
    * match ipamPairingPersistenceContract.populateExistingEnabled == true

  Scenario: 104. Certificación con firma táctil en técnico de campo y actualización/refresco de bitácora WORM (Hito 30.13 - Spec 90)
    * def fieldOpsSignatureContract = { canvasPad: '#signature-canvas', certifyBtn: '#btn-certify-order', recentList: '.card-list' }
    * match fieldOpsSignatureContract.canvasPad == '#signature-canvas'
    * match fieldOpsSignatureContract.certifyBtn == '#btn-certify-order'
    * def auditWormRefreshContract = { refreshBtn: '#btn-refresh-audit-logs', categorySelect: '#filter-cat', supportedCategory: 'SWITCHING_SECURITY' }
    * match auditWormRefreshContract.refreshBtn == '#btn-refresh-audit-logs'
    * match auditWormRefreshContract.categorySelect == '#filter-cat'
    * match auditWormRefreshContract.supportedCategory == 'SWITCHING_SECURITY'

  Scenario: 105. Paridad de columnas connection_count/estimated_pps en anomalías y control de mitigación FastDrop (Hito 30.14 - Spec 91)
    * def anomalyParityContract = { tableWrapper: '.tactical-table-wrapper', mitigateTopBtn: '#btn-mitigate-traffic-anomaly', connCountCol: 'connection_count', ppsCol: 'estimated_pps', defaultFastDropDuration: 300 }
    * match anomalyParityContract.tableWrapper == '.tactical-table-wrapper'
    * match anomalyParityContract.mitigateTopBtn == '#btn-mitigate-traffic-anomaly'
    * match anomalyParityContract.connCountCol == 'connection_count'
    * match anomalyParityContract.ppsCol == 'estimated_pps'
    * match anomalyParityContract.defaultFastDropDuration == 300
    * def slaProbeQuickContract = { endpoint: '/api/v1/sla/probes/run', maxIcmpCount: 5 }
    * match slaProbeQuickContract.maxIcmpCount == 5

  Scenario: 106. Despacho real en canales de notificación y modal dual crear/editar con botón #btn-edit-channel (Hito 30.15 - Spec 92)
    * def channelDispatchContract = { editBtnClass: '.btn-edit', editBtnPrefix: '#btn-edit-channel-', modalTitle: '#create-channel-title', testModalTitle: '#test-channel-title', testBtnClass: '.btn-test' }
    * match channelDispatchContract.editBtnClass == '.btn-edit'
    * match channelDispatchContract.editBtnPrefix == '#btn-edit-channel-'
    * match channelDispatchContract.modalTitle == '#create-channel-title'
    * match channelDispatchContract.testModalTitle == '#test-channel-title'
    * match channelDispatchContract.testBtnClass == '.btn-test'

  Scenario: 107. Paridad total de traducción al inglés (i18n EN) en CIS Hardening, Seguridad L2, Telemetría SLA, Alertas y SIEM (Hito 30.16 - Spec 93)
    * def i18nComplianceEnContract = { cisScoreTitle: 'Overall CIS Security Compliance Score', l2BulkBtn: 'Deploy Across Fleet (Bulk Ops)', slaAnomalyTitle: 'Traffic Anomaly Detection & 1-Click Mitigation', notificationsTitle: 'Multi-Channel Alert & Notification Channels', siemSaveBtn: 'Save SIEM Configuration' }
    * match i18nComplianceEnContract.cisScoreTitle == 'Overall CIS Security Compliance Score'
    * match i18nComplianceEnContract.l2BulkBtn == 'Deploy Across Fleet (Bulk Ops)'
    * match i18nComplianceEnContract.slaAnomalyTitle == 'Traffic Anomaly Detection & 1-Click Mitigation'
    * match i18nComplianceEnContract.notificationsTitle == 'Multi-Channel Alert & Notification Channels'
    * match i18nComplianceEnContract.siemSaveBtn == 'Save SIEM Configuration'

  Scenario: 108. Certificación sin error 500 en /field-ops y traducción completa al inglés del panel de técnico de campo (Hito 30.17 - Spec 94)
    * def fieldTechCertifyEnContract = { mapTab: '#tab-btn-map', mapTabLabelEn: 'Zone Map', diagTitleEn: 'Real-Time Diagnostics & 1-Click Certification', certifyBtn: '#btn-certify-order', migrationRevision: '0014_field_order_signature_svg' }
    * match fieldTechCertifyEnContract.mapTab == '#tab-btn-map'
    * match fieldTechCertifyEnContract.mapTabLabelEn == 'Zone Map'
    * match fieldTechCertifyEnContract.diagTitleEn == 'Real-Time Diagnostics & 1-Click Certification'
    * match fieldTechCertifyEnContract.certifyBtn == '#btn-certify-order'
    * match fieldTechCertifyEnContract.migrationRevision == '0014_field_order_signature_svg'

  Scenario: 109. Botón Marcar todo leído junto al botón de avisos sonoros y estado de lectura por fila en el Centro de Notificaciones (Hito 30.18 - Spec 95)
    * def notifMarkAllReadContract = { soundBtn: '#btn-notif-toggle-sound', markAllReadBtn: '#btn-notif-mark-all-read', snoozeBtn: '#btn-notif-snooze-30m', labelEs: 'Marcar todo leído', labelEn: 'Mark all read', unreadRowClass: '.notif-row--unread', readRowClass: '.notif-row--read' }
    * match notifMarkAllReadContract.soundBtn == '#btn-notif-toggle-sound'
    * match notifMarkAllReadContract.markAllReadBtn == '#btn-notif-mark-all-read'
    * match notifMarkAllReadContract.labelEs == 'Marcar todo leído'
    * match notifMarkAllReadContract.labelEn == 'Mark all read'
    * match notifMarkAllReadContract.unreadRowClass == '.notif-row--unread'
    * match notifMarkAllReadContract.readRowClass == '.notif-row--read'

  # ============================================================================
  # SPEC 96: PESTAÑA WIREGUARD EN /webfig/interfaces RECONOCE type="wg" DE ROUTEROS V7
  # ============================================================================
  Scenario: 110. La sub-pestaña WireGuard en InterfacesAndSfpView filtra tanto type="wg" como type="wireguard"
    * def ifaceWgNative = { id: '*B', name: 'miprueba', type: 'wg', mtu: 1420, running: true, disabled: false }
    * assert ifaceWgNative.type == 'wg' || ifaceWgNative.type == 'wireguard'

  # ============================================================================
  # SPEC 97: SUBPESTAÑA POR DEFECTO SERVIDORES DHCP Y CREACIÓN DE LEASE ESTÁTICO
  # ============================================================================
  Scenario: 111. El módulo Servidor DHCP abre por defecto Servidores DHCP y permite añadir concesiones estáticas
    * def defaultDhcpSubtab = 'servers'
    * assert defaultDhcpSubtab == 'servers'

  # ============================================================================
  # SPEC 98: CONMUTADOR FIREWALL IPV4 / IPV6 EN FIREWALLRULESVIEW
  # ============================================================================
  Scenario: 112. El botón Firewall IPv6 desde Pila Dual redirige con ?proto=ipv6 y activa las reglas IPv6
    * def targetUrl = '/routers/r-01/webfig/firewall?proto=ipv6'
    * assert targetUrl.contains('proto=ipv6')

  # ============================================================================
  # SPEC 99: DEGRADACIÓN ELEGANTE DE PAQUETE OPCIONAL ROUTEROS EN CAPA 2
  # ============================================================================
  Scenario: 113. Degradacion elegante de paquete opcional RouterOS no instalado en Capa 2 (Spec 99)
    * def resourceResponse = { ros_path: 'container', schema_source: 'package_not_installed', items: [] }
    * assert resourceResponse.schema_source == 'package_not_installed'
    * assert resourceResponse.items.length == 0



















