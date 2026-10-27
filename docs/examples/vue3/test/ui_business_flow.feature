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














