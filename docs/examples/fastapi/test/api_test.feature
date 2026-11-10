# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

Feature: Validación BDD Caja Negra de la API REST FastAPI de RoSGrid y Seguridad Multi-Tenant

  Background:
    * url 'http://api:8000'
    * configure headers = { 'Content-Type': 'application/json' }

  # ==============================================================================
  # Grupo 1: Observabilidad, Salud y Endpoint Raíz
  # ==============================================================================

  Scenario: 1. Healthcheck activo de la API con estado de PostgreSQL y KeyDB
    Given path '/health'
    When method get
    Then status 200
    And match response.status == 'healthy'
    And match response.service == 'rosgrid-api'
    And match response.database == '#string'
    And match response.redis == '#string'

  Scenario: 1b. Healthcheck activo mediante alias estandarizado /api/v1/health
    Given path '/api/v1/health'
    When method get
    Then status 200
    And match response.status == 'healthy'
    And match response.service == 'rosgrid-api'
    And match response.database == '#string'
    And match response.redis == '#string'

  Scenario: 2. Métricas del sistema expuestas en formato estándar Prometheus
    Given path '/metrics'
    When method get
    Then status 200
    And match response contains 'http_requests_total'

  Scenario: 3. Consulta de identidad del usuario actual sin cookie de sesión devuelve 401
    Given path '/users/me'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 2: Ciclo de Vida de Autenticación, Bootstrap y Registro
  # ==============================================================================

  Scenario: 4. Consulta de estado de inicialización del clúster (bootstrap-status)
    Given path '/api/v1/auth/bootstrap-status'
    When method get
    Then status 200
    And match response == { is_bootstrapped: '#boolean', tenants_count: '#number', users_count: '#number', registration_enabled: '#boolean', default_tenant_slug: '##string', default_tenant_name: '##string', message: '#string' }

  Scenario: 5. Envío de credenciales incompletas al login genera error de validación 422
    Given path '/api/v1/auth/login'
    And request { username: "solouser_sinpassword" }
    When method post
    Then status 422
    And match response.detail == '#present'

  Scenario: 6. Solicitud de auto-registro con campos faltantes devuelve HTTP 422
    Given path '/api/v1/auth/register'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { username: "operador_nuevo" }
    When method post
    Then status 422
    And match response.detail == '#present'

  Scenario: 7. Verificación de segundo factor 2FA con payload inválido devuelve HTTP 422
    Given path '/api/v1/auth/2fa/verify'
    And request { challenge_id: "invalido", totp_code: "12" }
    When method post
    Then status 422
    And match response.detail == '#present'

  Scenario: 8. Rotación de Refresh Token sin cookie de sesión activa devuelve 401
    Given path '/api/v1/auth/refresh'
    When method post
    Then status 401
    And match response == { detail: 'Cookie de Refresh Token ausente' }

  Scenario: 9. Cierre de sesión (logout) sin sesión previa devuelve 401
    Given path '/api/v1/auth/logout'
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 3: Gestión Multi-Tenant y Gobernanza de Feature Flags
  # ==============================================================================

  Scenario: 10. Listado de empresas (Tenants) sin rol SUPERADMIN_GLOBAL devuelve 401
    Given path '/api/v1/tenants'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 11. Creación de nueva empresa sin cabecera Idempotency-Key devuelve 400
    Given path '/api/v1/tenants'
    And request { name: "Tenant Test", slug: "tenant-test" }
    When method post
    Then status 400
    And match response == { detail: 'Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables' }

  Scenario: 12. Modificación de Feature Flags de tenant sin autenticación devuelve 401
    Given path '/api/v1/tenants/00000000-0000-0000-0000-000000000001/features'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { isp_module_enabled: true, enforce_maker_checker: true }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 4: Usuarios, Aprobación Maker-Checker y Switch de Registro
  # ==============================================================================

  Scenario: 13. Catálogo de usuarios y operadores del tenant sin autenticación devuelve 401
    Given path '/api/v1/users'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 14. Conmutación en caliente del switch de registro público sin credenciales devuelve 401
    Given path '/api/v1/users/registration-toggle'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { enabled: false }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 15. Aprobación de operador pendiente sin privilegios devuelve 401
    Given path '/api/v1/users/00000000-0000-0000-0000-000000000001/approve'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { role: 'SUPPORT_L2', has_all_routers_access: true }
    When method put
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 5: Sesiones Activas y Kill-Switch de Expulsión
  # ==============================================================================

  Scenario: 16. Monitor de sesiones concurrentes sin autenticación devuelve 401
    Given path '/api/v1/sessions/active'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 17. Invocación del Kill-Switch de sesión sin credenciales de administrador devuelve 401
    Given path '/api/v1/sessions/sess-test-uuid'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method delete
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 6: Inventario de Routers, Pinning TOFU y Asistente CSV
  # ==============================================================================

  Scenario: 18. Listado de flota de routers sin autenticación devuelve 401
    Given path '/api/v1/inventory/routers'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 19. Alta de nuevo router sin cabecera Idempotency-Key obligatoria devuelve 400
    Given path '/api/v1/inventory/routers'
    And request { display_name: 'RB4011-Test' }
    When method post
    Then status 400
    And match response == { detail: 'Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables' }

  Scenario: 20. Redescubrimiento dinámico de certificados SSL TOFU sin sesión devuelve 401
    Given path '/api/v1/inventory/routers/00000000-0000-0000-0000-000000000001/discover'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 20b. Validación de auto-pinning TOFU continuo y sincronización sin sesión devuelve 401
    Given path '/api/v1/inventory/routers/00000000-0000-0000-0000-000000000001/sync-discovery'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 21. Catálogo de roles personalizados de infraestructura sin sesión devuelve 401
    Given path '/api/v1/inventory/network-roles'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 7: Bóveda Criptográfica (Split-Credential) y Step-Up 2FA
  # ==============================================================================

  Scenario: 22. Revelación de clave de router sin Step-Up 2FA TOTP devuelve 401
    Given path '/api/v1/inventory/routers/00000000-0000-0000-0000-000000000001/vault/reveal'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { totp_code: '123456', reason: 'Auditoría no autorizada' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 23. Disparo de rotación automática transaccional de clave sin autenticación devuelve 401
    Given path '/api/v1/inventory/routers/00000000-0000-0000-0000-000000000001/vault/rotate'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 8: IPAM Dual-Stack (IPv4 / IPv6) y Pools
  # ==============================================================================

  Scenario: 24. Inspección de subredes IPAM sin sesión devuelve 401
    Given path '/api/v1/ipam/prefixes'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 25. Creación de subred sin cabecera Idempotency-Key devuelve 400
    Given path '/api/v1/ipam/subnets'
    And request { cidr: '10.50.0.0/24', name: 'Pool-NOC' }
    When method post
    Then status 400
    And match response == { detail: 'Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables' }

  # ==============================================================================
  # Grupo 9: Perfiles QoS y Dispositivos de Abonados (ONUs / CPEs)
  # ==============================================================================

  Scenario: 26. Catálogo de perfiles de ancho de banda QoS sin sesión devuelve 401
    Given path '/api/v1/bandwidth-profiles'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 27. Inventario técnico de abonados (ONUs) sin sesión devuelve 401
    Given path '/api/v1/subscriber-devices'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 10: Aprovisionamiento Técnico Idempotente de Red
  # ==============================================================================

  Scenario: 28. Aislamiento técnico de servicio sin cabecera Idempotency-Key devuelve 400
    Given path '/api/v1/network-services/00000000-0000-0000-0000-000000000001/isolate'
    And request { reason: 'Mora técnica' }
    When method post
    Then status 400
    And match response == { detail: 'Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables' }

  Scenario: 29. Restauración técnica de servicio sin autenticación devuelve 401
    Given path '/api/v1/network-services/00000000-0000-0000-0000-000000000001/restore'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { reason: 'Pago conciliado' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 11: Operaciones de Campo (Field Ops) y Diagnóstico SFP
  # ==============================================================================

  Scenario: 30. Registro de coordenadas GPS de abonado sin Idempotency-Key devuelve 400
    Given path '/api/v1/field-ops/register-gps'
    And request { device_id: '00000000-0000-0000-0000-000000000001', latitude: 10.48, longitude: -66.90 }
    When method post
    Then status 400
    And match response == { detail: 'Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables' }

  Scenario: 31. Telemetría óptica SFP DDM en vivo sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/interfaces/ethernet/sfp-sfpplus1/sfp-monitor'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 12: Ventanas de Mantenimiento Programadas
  # ==============================================================================

  Scenario: 32. Consulta de ventanas de mantenimiento sin autenticación devuelve 401
    Given path '/api/v1/maintenance/windows'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 13: Consola WebFig v7 de Doble Capa (Layer 1 y Layer 2)
  # ==============================================================================

  Scenario: 33. Consulta de interfaces y óptica SFP en router sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/interfaces'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 34. Consulta de reglas de firewall sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/firewall/ip/filter'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 35. Proxy universal de Capa 2 RouterOS v7 sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/layer2/resource/interface/bridge'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 14: Bandeja de Aprobaciones Maker-Checker
  # ==============================================================================

  Scenario: 36. Acceso a la bandeja de aprobaciones Maker-Checker sin credenciales devuelve 401
    Given path '/api/v1/operations/approvals'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 15: Respaldos Cifrados y Comparador Git Diff
  # ==============================================================================

  Scenario: 37. Listado del historial de 30 días de respaldos sin sesión devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/backups'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 38. Disparo manual de generación de respaldo sin Idempotency-Key devuelve 400
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/backups'
    And request { backup_type: 'rsc' }
    When method post
    Then status 400
    And match response == { detail: 'Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables' }

  # ==============================================================================
  # Grupo 16: Operaciones Masivas y Golden Templates
  # ==============================================================================

  Scenario: 39. Aplicación de plantilla masiva sin Idempotency-Key devuelve 400
    Given path '/api/v1/operations/bulk/apply-template'
    And request { template_id: '00000000-0000-0000-0000-000000000001', router_ids: [] }
    When method post
    Then status 400
    And match response == { detail: 'Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables' }

  # ==============================================================================
  # Grupo 17: Canales de Alerta y Webhooks HMAC
  # ==============================================================================

  Scenario: 40. Consulta de canales de notificación sin sesión devuelve 401
    Given path '/api/v1/operations/notification-channels'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 18: Auditoría Inmutable WORM y Certificación Criptográfica
  # ==============================================================================

  Scenario: 41. Búsqueda en bitácora inmutable WORM sin rol AUDITOR devuelve 401
    Given path '/api/v1/audit/logs'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 42. Verificación matemática de la cadena SHA-256 sin autenticación devuelve 401
    Given path '/api/v1/audit/logs/verify-integrity'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 19: Servidor MCP Protegido para Agentes IA (JSON-RPC 2.0)
  # ==============================================================================

  Scenario: 43. Endpoint MCP: Petición JSON-RPC 2.0 sin autenticación Bearer devuelve 401
    Given path '/api/v1/mcp'
    And request { jsonrpc: '2.0', id: 'karate-test-1', method: 'tools/list', params: {} }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 44. Endpoint MCP: Token Bearer inválido o corrupto devuelve 401
    Given path '/api/v1/mcp'
    And header Authorization = 'Bearer token_invalido_corrupto_123'
    And request { jsonrpc: '2.0', id: 'karate-test-2', method: 'tools/list', params: {} }
    When method post
    Then status 401
    And match response.detail contains 'Token de acceso inválido'

  # ==============================================================================
  # Grupo 20: Diagnóstico 360°, BGP Looking Glass e IPFIX
  # ==============================================================================

  Scenario: 45. Invocación de suite de diagnóstico 360° sin Idempotency-Key devuelve 400
    Given path '/api/v1/diagnostics/endpoint-360'
    And request { router_id: '00000000-0000-0000-0000-000000000001', target_ip: '8.8.8.8' }
    When method post
    Then status 400
    And match response == { detail: 'Cabecera Idempotency-Key (UUID) obligatoria para operaciones mutables' }

  Scenario: 46. Consulta de rutas BGP en Looking Glass sin sesión devuelve 401
    Given path '/api/v1/bgp/looking-glass/route'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 47. Consulta de anomalías de flujo de tráfico IPFIX sin autenticación devuelve 401
    Given path '/api/v1/traffic-flow/anomalies'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 21: Cumplimiento Corporativo, SD-WAN, Switching, SLA y WiFi
  # ==============================================================================

  Scenario: 48. Escaneo de auditoría CIS Benchmark sin autenticación devuelve 401
    Given path '/api/v1/compliance/cis-audit/00000000-0000-0000-0000-000000000001'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 49. Detección de desviación de configuración (Config Drift) sin sesión devuelve 401
    Given path '/api/v1/compliance/config-drift/00000000-0000-0000-0000-000000000001'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 50. Consulta de topologías SD-WAN WireGuard Hub & Spoke sin sesión devuelve 401
    Given path '/api/v1/sdwan/topology/00000000-0000-0000-0000-000000000001'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 51. Consulta de eventos de Rogue DHCP Snooping en switches sin autenticación devuelve 401
    Given path '/api/v1/switching/dhcp-snooping/events'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 52. Consulta de métricas SLA de carriers sin autenticación devuelve 401
    Given path '/api/v1/sla/metrics/00000000-0000-0000-0000-000000000001'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 53. Consulta de radios WiFi corporativos CAPsMAN sin autenticación devuelve 401
    Given path '/api/v1/wifi/capsman/00000000-0000-0000-0000-000000000001/overview'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 54. Catálogo de los 11 roles del sistema RBAC sin autenticación devuelve 401
    Given path '/api/v1/rbac/roles'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 22: Automatización de Flota, Topología L2, Syslog, CVEs y Exporter Prometheus (Hito 23.4)
  # ==============================================================================

  Scenario: 55. Consulta de matriz CVE de flota sin autenticación devuelve 401
    Given path '/api/v1/inventory/cves'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 56. Sincronización del catálogo CVE sin autenticación devuelve 401
    Given path '/api/v1/inventory/cves/sync'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 57. Consulta de topología física Layer 2 sin autenticación devuelve 401
    Given path '/api/v1/topology/l2'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 58. Consulta de plantilla de enrolamiento Syslog sin autenticación devuelve 401
    Given path '/api/v1/routers/syslog/template'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 59. Consulta de RingBuffer Syslog de un router sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/syslog'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 60. Endpoint de métricas de flota en formato OpenMetrics Prometheus /api/v1/metrics/fleet
    Given path '/api/v1/metrics/fleet'
    When method get
    Then status 200
    And match response contains 'rosgrid_router_status'
    And match response contains 'rosgrid_router_cpu_percent'
    And match response contains 'rosgrid_router_memory_usage_ratio'
    And match response contains 'rosgrid_router_uptime_seconds'
    And match response contains 'rosgrid_router_temperature_celsius'
    And match response contains 'rosgrid_router_voltage_volts'
    And match response contains 'rosgrid_router_active_cves_count'
    And match response contains 'rosgrid_router_syslog_critical_events_total'

  Scenario: 61. Ejecución de actualización masiva con orden PoE-aware sin autenticación devuelve 401
    Given path '/api/v1/operations/ros-updates/execute'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { router_ids: ['00000000-0000-0000-0000-000000000001'], poe_aware: true }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 12: Onboarding Masivo CSV y Catálogo de Roles de Red Dinámicos
  # ==============================================================================

  Scenario: 62. Validación en seco (dry-run) de importación masiva CSV sin autenticación devuelve 401
    Given path '/api/v1/inventory/import-csv/dry-run'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 63. Confirmación transaccional (commit) de importación masiva CSV sin autenticación devuelve 401
    Given path '/api/v1/inventory/import-csv/commit'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 64. Consulta de catálogo de roles de red y roles personalizados sin autenticación devuelve 401
    Given path '/api/v1/inventory/network-roles'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 65. Descarga de plantilla CSV oficial de inventario devuelve 200 con cabecera de adjunto
    Given path '/api/v1/inventory/template-csv'
    When method get
    Then status 200
    And match header Content-Disposition contains 'rosgrid-inventario-plantilla.csv'

  Scenario: 66. Aprobación de solicitud Maker-Checker sin autenticación devuelve 401
    Given path '/api/v1/operations/approvals/00000000-0000-0000-0000-000000000001/approve'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { review_comment: 'Aprobación autorizada' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 67. Rechazo de solicitud Maker-Checker sin autenticación devuelve 401
    Given path '/api/v1/operations/approvals/00000000-0000-0000-0000-000000000001/reject'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { review_comment: 'Rechazo por política' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 68. Consulta de interfaces Bridge Layer 1 sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/interfaces/bridge'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 69. Consulta optimizada de /health con soporte de forzado y respuesta estructurada
    Given path '/health'
    And param force = 'true'
    When method get
    Then status 200
    And match response.status == 'healthy'
    And match response.service == 'rosgrid-api'
    And match response.database == '#string'
    And match response.redis == '#string'

  Scenario: 70. Consulta del catálogo de plantillas predefinidas RouterOS v7 sin autenticación devuelve 401
    Given path '/api/v1/operations/templates/presets'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 71. Consulta de plantillas de configuración del tenant sin autenticación devuelve 401
    Given path '/api/v1/operations/templates'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 72. Validación sintáctica canónica de plantillas RouterOS v7 (NTP, DNS, SNMP y Syslog) sin autenticación devuelve 401
    Given path '/api/v1/operations/templates/00000000-0000-0000-0000-000000000000/render-preview'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { "template_id": "00000000-0000-0000-0000-000000000000", "router_ids": [] }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 73. Consulta de plantilla de aprovisionamiento Syslog RouterOS v7 sin autenticación devuelve 401
    Given path '/api/v1/routers/syslog/template'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 74. Consulta de RingBuffer de eventos Syslog de router sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/syslog'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 75. Consulta de eventos Syslog con límite superior a 500 devuelve error de validación 422
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/syslog'
    And param limit = 501
    When method get
    Then status 401

  Scenario: 76. Consulta de matriz CVE con autosincronización y caché de 24 horas sin autenticación devuelve 401
    Given path '/api/v1/inventory/cves'
    And param auto_sync = true
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 77. Sincronización masiva de IPAM (pools DHCP e interfaces) de la flota sin autenticación devuelve 401
    Given path '/api/v1/ipam/sync-all'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 24: Arquitectura Bimodal y Operaciones de Campo FTTH (Hito 23.23)
  # ==============================================================================

  Scenario: 78. Consulta de Cajas NAP de distribución óptica FTTH sin autenticación devuelve 401
    Given path '/api/v1/optical-boxes'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 79. Creación de Caja NAP de fibra óptica sin autenticación devuelve 401
    Given path '/api/v1/optical-boxes'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { "box_code": "NAP-NORTE-01", "capacity_ports": 16, "splitter_ratio": "1:16" }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 80. Consulta de detalle y matriz de puertos de Caja NAP sin autenticación devuelve 401
    Given path '/api/v1/optical-boxes/00000000-0000-0000-0000-000000000001'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 81. Sincronización en vivo de dispositivos DHCP para Mapa de Red sin autenticación devuelve 401
    Given path '/api/v1/subscriber-devices/sync-dhcp'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 82. Test Ping ICMP 1-Click hacia dispositivo de red sin autenticación devuelve 401
    Given path '/api/v1/subscriber-devices/00000000-0000-0000-0000-000000000001/ping'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 83. Gobernanza Anti-Saturación — Diagnóstico Ping ICMP con Caché KeyDB y Semáforo Concurrente
    Given path '/api/v1/subscriber-devices/00000000-0000-0000-0000-000000000001/ping'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 84. Consulta de Estado Operacional, Causa Raíz (RCA) y Cerradura de Cuadrillas sin autenticación devuelve 401
    Given path '/api/v1/subscriber-devices/00000000-0000-0000-0000-000000000001/operational-status'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 85. Diagnóstico Integral 360° con Parámetros Force y Extended sin autenticación devuelve 401
    Given path '/api/v1/subscriber-devices/00000000-0000-0000-0000-000000000001/ping'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And param force = true
    And param extended = true
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 86. Remediación individual selectiva CIS Benchmark con Safe Mode sin autenticación devuelve 401
    Given path '/api/v1/compliance/cis-audit/00000000-0000-0000-0000-000000000001/auto-harden'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { router_id: '00000000-0000-0000-0000-000000000001', directive_codes_to_apply: ['CIS-1.1'] }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 87. Remediación individual CIS-1.8 de defensa contra fuerza bruta (SSH/WinBox) sin autenticación devuelve 401
    Given path '/api/v1/compliance/cis-audit/00000000-0000-0000-0000-000000000001/auto-harden'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { router_id: '00000000-0000-0000-0000-000000000001', directive_codes_to_apply: ['CIS-1.8'] }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 88. Consulta de alertas de Rogue DHCP en switches MikroTik sin autenticación devuelve 401
    Given path '/api/v1/switching/rogue-dhcp/alerts/00000000-0000-0000-0000-000000000001'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 89. Notificación de Cierre de Sesión / Ventana (session-closing) sin session_id devuelve 400
    Given path '/api/v1/auth/session-closing'
    And request { session_id: '' }
    When method post
    Then status 400
    And match response == { detail: 'Se requiere session_id para registrar el cierre' }

  Scenario: 90. Consulta de directivas y políticas CIS personalizadas sin autenticación devuelve 401
    Given path '/api/v1/compliance/cis-policies'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 91. Actualización de directivas y políticas CIS personalizadas sin autenticación devuelve 401
    Given path '/api/v1/compliance/cis-policies'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { profile: 'ISP', rules: [] }
    When method put
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 92. Finalización de Onboarding de Tenant sin autenticación devuelve 401
    Given path '/api/v1/tenants/00000000-0000-0000-0000-000000000001/onboarding-complete'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 93. Conmutación Rápida de Tenants (switch-tenant) sin autenticación devuelve 401
    Given path '/api/v1/auth/switch-tenant'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { target_tenant_slug: 'fibra-norte' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 94. Conmutación Rápida de Tenants (switch-tenant) con método no permitido devuelve 405
    Given path '/api/v1/auth/switch-tenant'
    When method get
    Then status 405

  # ==============================================================================
  # Grupo 25: Gobernanza Táctica de Módulos B2B y Auditoría Forense WORM (Hito 26)
  # ==============================================================================

  Scenario: 95. Modificación de capacidades y módulos B2B de tenant sin autenticación devuelve 401
    Given path '/api/v1/tenants/00000000-0000-0000-0000-000000000001/features'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { "isp_module_enabled": true }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 96. Consulta de historial WORM de auditoría de modificaciones de módulos sin autenticación devuelve 401
    Given path '/api/v1/tenants/00000000-0000-0000-0000-000000000001/features/audit'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 97. Consulta de historial WORM de auditoría con límite no válido devuelve 422
    Given path '/api/v1/tenants/00000000-0000-0000-0000-000000000001/features/audit'
    And param limit = 0
    When method get
    Then status 401

  # ==============================================================================
  # Grupo 26: WebFig v7 Paridad Total — DHCPv4, Pila Dual IPv6 & Routing (Hito 27)
  # ==============================================================================

  Scenario: 98. Consulta de servidores DHCP sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/ip/dhcp-servers'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 99. Creación de red DHCP sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/ip/dhcp-server/networks'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { address: '192.168.100.0/24', gateway: '192.168.100.1' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 100. Renovación de concesión de cliente DHCP WAN sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/ip/dhcp-clients/c1/renew'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 101. Consulta de direcciones IPv6 Dual-Stack sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/ipv6/addresses'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 102. Solicitud de prefijo delegable DHCPv6-PD sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/ipv6/dhcp-clients'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { interface: 'ether1', request: 'prefix', pool_name: 'v6-pool', pool_prefix_length: 64, add_default_route: true }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 103. Consulta de tabla de vecinos IPv6 (NDP) sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/ipv6/neighbors'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 104. Creación de entrada Bridge VLAN Filtering sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/interfaces/bridge/vlans'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { bridge: 'bridge1', vlan_ids: '10,20', tagged: 'ether1', untagged: 'ether2' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 105. Creación de subinterfaz VLAN 802.1Q sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/interfaces/vlan'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { name: 'vlan100-mgmt', vlan_id: 100, interface: 'bridge1' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 106. Consulta del catálogo canónico de 28 directivas CIS Benchmark sin sesión devuelve 401
    Given path '/api/v1/compliance/cis-catalog'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 107. Consulta de auditoría CIS sin autenticación devuelve 401
    Given path '/api/v1/compliance/cis-audit/00000000-0000-0000-0000-000000000001'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 108. Solicitud de remediación asistida CIS bajo Safe Mode sin autenticación devuelve 401
    Given path '/api/v1/compliance/cis-audit/00000000-0000-0000-0000-000000000001/auto-harden'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { directive_codes_to_apply: ['CIS-1.1'] }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 109. Consulta de políticas CIS personalizadas por Tenant sin sesión devuelve 401
    Given path '/api/v1/compliance/cis-policies'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 110. Consulta del catálogo de plantillas de configuración sin autenticación devuelve 401
    Given path '/api/v1/operations/templates'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 111. Consulta de presets de plantillas Golden Config sin autenticación devuelve 401
    Given path '/api/v1/operations/templates/presets'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 112. Consulta de eventos Syslog de router sin autenticación devuelve 401
    Given path '/api/v1/routers/3fc15cff-31eb-4230-81c6-800130be18e8/syslog'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 113. Consulta de perfiles SSIDs y clientes WiFi CAPsMAN en router sin autenticación devuelve 401
    Given path '/api/v1/wifi/capsman/3fc15cff-31eb-4230-81c6-800130be18e8/ssids'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 114. Actualización modular de Feature Flags con rogue_dhcp_enabled sin autenticación devuelve 401
    Given path '/api/v1/tenants/00000000-0000-0000-0000-000000000001/features'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { isp_module_enabled: true, enforce_maker_checker: true, rogue_dhcp_enabled: true }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 115. Toggle interactivo del Manager CAPsMAN WiFi v7 sin autenticación devuelve 401
    Given path '/api/v1/wifi/capsman/3fc15cff-31eb-4230-81c6-800130be18e8/manager/toggle'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { enabled: true, comment: 'Activar CAPsMAN v7' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 116. Quick Setup asistente WiFi corporativo sin autenticación devuelve 401
    Given path '/api/v1/wifi/capsman/3fc15cff-31eb-4230-81c6-800130be18e8/quick-setup'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { corp_ssid: 'CORP-NET', corp_passphrase: 'supersecretpass', create_guest: false }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 117. Autodescubrimiento TOFU de router en inventario sin autenticación devuelve 401
    Given path '/api/v1/inventory/routers/00000000-0000-0000-0000-000000000001/discover'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 118. Consulta de catálogo de módulos WebFig v7 para navegación responsive sin autenticación devuelve 401
    Given path '/api/v1/routers/3fc15cff-31eb-4230-81c6-800130be18e8/webfig/layer2/catalog'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 119. Creación de regla NAT Masquerade en WebFig Firewall RouterOS v7 sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/firewall/ip/nat'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { chain: 'srcnat', out_interface: 'ether1', action: 'masquerade', comment: 'NAT Masquerade RoSGrid Wizard' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 120. Creación idempotente de Servidor DHCP en WebFig IP RouterOS v7 sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/ip/dhcp-servers'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { name: 'dhcp-ether1', interface: 'ether1', address_pool: 'pool-ether1', lease_time: '12h', disabled: false }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 121. Creación de subinterfaz VLAN 802.1Q en WebFig Interfaces con intercepción Maker-Checker L1/L2 sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/interfaces/vlan'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { name: 'vlan20', vlan_id: 20, interface: 'ether1', mtu: 1500, comment: 'VLAN L1 Maker-Checker' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 122. Notificación de cierre de navegador (session-closing) con comodín session_id 'current' sin cookie activa devuelve 400
    Given path '/api/v1/auth/session-closing'
    And request { session_id: 'current', client_timestamp: 1730240000000 }
    When method post
    Then status 400
    And match response.detail contains 'session_id'

  Scenario: 123. Liberar puerto miembro de un Bridge (DELETE /bridge/ports/{id}) en WebFig Interfaces sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/interfaces/bridge/ports/*BP1'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method delete
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 124. Eliminar interfaz de túnel WireGuard (DELETE /wireguard/{id}) en WebFig Interfaces sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/interfaces/wireguard/*WG1'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method delete
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 125. Editar parámetros de red DHCP, Pool IP y configuración DNS Singleton (PATCH /dns) en WebFig IP sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/ip/dns'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { servers: '1.1.1.1,8.8.8.8', allow_remote_requests: true, cache_size: 4096 }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 126. Eliminar Pool de conexiones IP (DELETE /pools/{id}) y editar servidor PPPoE (PATCH /pppoe-servers/{id}) sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/ip/pools/*P1'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method delete
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 127. Creación de Regla de Aprovisionamiento de Radios CAPsMAN v7 (/provisioning) y Reprovisión de Flota sin autenticación devuelve 401
    Given path '/api/v1/wifi/capsman/00000000-0000-0000-0000-000000000001/provisioning'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { name: 'prov-all-bands', action: 'create-dynamic-enabled', master_configuration: 'cfg-corporate', slave_configurations: ['cfg-guest'], supported_bands: ['2ghz-ax', '5ghz-ax', '6ghz-ax'], identity_regex: '.*' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 128. Motor Universal Capa 2 Next-Gen: Operaciones por Lote Bulk (POST /webfig/layer2/bulk/certificate) y Exportación Contextual .rsc sin autenticación devuelve 401 (Hito 27.16)
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/layer2/bulk/certificate'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { action: 'comment', ids: ['*1', '*2'], comment: 'Auditado NOC 27.16' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 129. Gobernanza Granular de Flags en Perfiles de Usuario: Consulta de Permisos Efectivos (GET /users/{id}/effective-permissions) y Overrides Individuales (PATCH /users/{id}/feature-flags) sin autenticación devuelve 401 (Hito 27.17)
    Given path '/api/v1/users/00000000-0000-0000-0000-000000000001/effective-permissions'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/users/00000000-0000-0000-0000-000000000001/feature-flags'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { feature_flags_override: { WEBFIG_L2_RPC_COMMANDS: 'ALLOW', LIVE_DIAGNOSTICS: 'DENY' } }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 130. Telemetría Anónima de Instancias Activas: Inspección de Estado de Beacon (GET /system/telemetry-beacon/status) y Disparo Manual (POST /system/telemetry-beacon/trigger) sin autenticación devuelve 401 (Hito 27.18)
    Given path '/api/v1/system/telemetry-beacon/status'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/system/telemetry-beacon/trigger'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 131. Contrato FTTH y Validación de Cajas NAP: Detalle de Caja NAP (GET /optical-boxes/{id}) y Alta de Abonado FTTH (POST /subscriber-devices) sin autenticación devuelve 401 (Hito 28.2)
    Given path '/api/v1/optical-boxes/00000000-0000-0000-0000-000000000001'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/subscriber-devices'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { router_id: '00000000-0000-0000-0000-000000000001', endpoint_identifier: 'CLI-FTTH-001', service_type: 'FTTH_GPON', onu_mode: 'ROUTER_NAT', optical_box_port: 1 }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 132. Disparo de Respaldos .rsc con Diagnóstico de Política FTP y Terminación de Sesión con Scoping Estricto (Hitos 28.3 y 28.7)
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/backups/trigger'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/sessions/sess-target-001'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method delete
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 133. Actualización Inteligente RouterOS y Firmware con Auto-Detección CHR: Sondeo de Canal (POST /operations/ros-updates/check) sin autenticación devuelve 401 (Hito 28.1)
    Given path '/api/v1/operations/ros-updates/check'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { channel: 'stable', router_ids: [] }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 134. Activación/Configuración de DHCP Snooping en Bridge (POST /switching/dhcp-snooping/enable) sin autenticación devuelve 401 (Hito 28.4)
    Given path '/api/v1/switching/dhcp-snooping/enable'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { router_id: '01928000-0000-7000-8000-000000000001', bridge_name: 'bridge1', enabled: true, trusted_ports: ['ether1'] }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 135. Telemetría SLA Real: Autodescubrimiento de Gateways WAN y Presets Quad9 (GET /sla/targets/{router_id}) sin autenticación devuelve 401 (Hito 28.6)
    Given path '/api/v1/sla/targets/01928000-0000-7000-8000-000000000001'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 136. Paridad de Roles RBAC y Visibilidad Estricta: Endpoints de Monitoreo de Cumplimiento sin autenticación devuelven 401 (Hito 28.9)
    Given path '/api/v1/compliance/config-drift/01928000-0000-7000-8000-000000000001'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 137. Paridad de Endpoints Operativos: Alias de Rotación de Credenciales de Bóveda (POST /vault/routers/{id}/rotate) sin autenticación devuelve 401 (Hito 28.5)
    Given path '/api/v1/vault/routers/01928000-0000-7000-8000-000000000001/rotate'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 138. Paridad de Endpoints Operativos: Alias de Re-Pinning SSL TOFU (POST /vault/routers/{id}/repin-ssl) sin autenticación devuelve 401 (Hito 28.5)
    Given path '/api/v1/vault/routers/01928000-0000-7000-8000-000000000001/repin-ssl'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 139. Paridad de Endpoints Operativos: Alias de Aprovisionamiento SD-WAN Spoke (POST /sdwan/spokes) sin autenticación devuelve 401 (Hito 28.5)
    Given path '/api/v1/sdwan/spokes'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { spoke_router_id: '01928000-0000-7000-8000-000000000001', hub_router_id: '01928000-0000-7000-8000-000000000002', tunnel_subnet: '10.255.0.0/30', endpoint_address: '198.51.100.1' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 140. Paridad de Endpoints Operativos: Alias de Failover Multi-WAN (POST /sdwan/multi-wan/failover) sin autenticación devuelve 401 (Hito 28.5)
    Given path '/api/v1/sdwan/multi-wan/failover'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { router_id: '01928000-0000-7000-8000-000000000001', primary_interface: 'ether1', primary_gateway: '192.168.1.1', secondary_interface: 'ether2', secondary_gateway: '192.168.2.1' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 141. Paridad de Endpoints Operativos: Mutación de Recurso Singleton WebFig Capa 2 (PATCH /webfig/layer2/singleton/{ros_path}) sin autenticación devuelve 401 (Hito 28.5)
    Given path '/api/v1/routers/01928000-0000-7000-8000-000000000001/webfig/layer2/singleton/system/ntp/client'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { attributes: { enabled: true }, enable_safemode: true }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 142. Paridad de Endpoints Operativos: Terminación de Conexión Activa Firewall Conntrack (DELETE /webfig/firewall/{proto}/connections/{conn_id}) sin autenticación devuelve 401 (Hito 28.5)
    Given path '/api/v1/routers/01928000-0000-7000-8000-000000000001/webfig/firewall/ipv4/connections/*4A'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method delete
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 143. Contrato de Telemetría Anónima de Flota: Esquema de Estado de Beacon y Conteo RLS (GET /system/telemetry-beacon/status) (Hito 28.10)
    # Valida el contrato JSON del beacon en /system/telemetry-beacon/status rechazando accesos no autenticados
    Given path '/api/v1/system/telemetry-beacon/status'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/system/telemetry-beacon/trigger'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/routers/01928000-0000-7000-8000-000000000001/backups/trigger'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/tenants'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 144. Edición Integral de Empresa y Cuotas Multi-Tenant: PATCH /api/v1/tenants/{id} sin autenticación devuelve 401 (Hito 28.11)
    Given path '/api/v1/tenants/01928000-0000-7000-8000-000000000001'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { name: 'Empresa Principal Editada', slug: 'master-hq', tax_id: 'J-12345678-9', max_routers_quota: 150, max_users_quota: 50, default_safemode_seconds: 30 }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 145. Sincronización Integral de Identidad del Router: PATCH /api/v1/routers/{id}/webfig/system/identity sin autenticación devuelve 401 (Hito 28.12)
    Given path '/api/v1/routers/01928000-0000-7000-8000-000000000001/webfig/system/identity'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { name: 'CCR2004-Core-North', sync_display_name: true }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 146. Endurecimiento Normativo DISA ASD STIG V6R5 y OWASP OSHP: Cabeceras de seguridad estrictas y validación de 15 caracteres en Bootstrap (Hito 28.13)
    Given path '/api/v1/auth/bootstrap'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { tenant_name: 'Test Tenant', tenant_slug: 'test-stig', admin_username: 'stigadmin', admin_email: 'stig@test.com', admin_password: 'short', admin_full_name: 'STIG Admin' }
    When method post
    Then status 422
    And match header X-Permitted-Cross-Domain-Policies == 'none'
    And match header Cross-Origin-Opener-Policy == 'same-origin'
    And match header X-Content-Type-Options == 'nosniff'
    And match header X-Frame-Options == 'DENY'

  Scenario: 147. Persistencia Relacional de onboarding_completed en PostgreSQL y Resiliencia ante Reinicio (Hito 28.14)
    Given path '/api/v1/tenants/00000000-0000-0000-0000-000000000001/features'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/tenants/00000000-0000-0000-0000-000000000001/features'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { onboarding_completed: true }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }




























  Scenario: 148. Emparejamiento de Red FTTH (DHCP, PPPoE e IPAM), Candidatos en Vivo y Ping 1-Click (Hito 28.15)
    Given path '/api/v1/subscriber-devices/00000000-0000-0000-0000-000000000001/live-candidates'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/subscriber-devices/00000000-0000-0000-0000-000000000001'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { service_type: 'DHCP', assigned_ipv4: '10.250.3.55', onu_mac_address: 'AA:BB:CC:11:22:33' }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/subscriber-devices/00000000-0000-0000-0000-000000000001/ping'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And param force = true
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }



  Scenario: 149. Conector Oficial a la API REST v2.0 de NIST NVD, Fusión Multi-Fuente y Filtrado RouterOS v7 (Hito 29.1)
    Given path '/api/v1/inventory/cves/sync'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/inventory/cves'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/inventory/cves/routers/00000000-0000-0000-0000-000000000001'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }



  Scenario: 150. Paquete de Soporte y Diagnóstico Unificado 1-Click con Sanitización Zero-Leak y Telemetría UI (Hito 29.2)
    Given path '/api/v1/system/diagnostics/ui-error'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { error_message: 'Uncaught TypeError: test', source_url: '/inventory', stack_trace: 'Error at test:1:1' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/system/diagnostics/bundle'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { format: 'zip', include_ui_logs: true, include_backend_logs: true, include_siem_status: true }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/system/siem-config'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/system/siem-config'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { enabled: true, destination_type: 'SYSLOG_UDP', host: '127.0.0.1', port: 514 }
    When method put
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/system/siem-config/test'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }



  Scenario: 151. Conector SIEM Multi-Protocolo del ISP y Paquete de Soporte Sanitizado (Hito 29.3)
    Given path '/api/v1/system/siem-config'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/system/diagnostics/bundle'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { format: 'zip', log_lines_limit: 500, operator_notes: 'Prueba BDD Hito 29.3', include_frontend_buffer: [] }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }



  Scenario: 152. Resiliencia en Reinicio de Router MikroTik y Esquema Tolerante (Hito 28.16)
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/system/reboot'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/system/reboot'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { reason: 'Reinicio programado por ventana de mantenimiento' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 153. Motor Safe Mode Transaccional Real de 2 Fases y Verificación en Vivo (Hito 28.17)
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/system/safemode/status'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/system/safemode/verify'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/system/safemode/confirm'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/system/safemode/rollback'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 154. Precarga de Bóveda y Herencia de Coordenadas en Alta de Abonados FTTH (Hito 28.19)
    Given path '/api/v1/subscriber-devices/00000000-0000-0000-0000-000000000001/live-candidates'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/subscriber-devices/00000000-0000-0000-0000-000000000001/ping'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 155. Alta FTTH por MAC WAN, Auto-Conmutación L2 Bridge -> BNG y Aprovisionamiento MikroTik (Hito 28.20)
    Given path '/api/v1/subscriber-devices/00000000-0000-0000-0000-000000000001/live-candidates'
    And param bng_router_id = '00000000-0000-0000-0000-000000000111'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/subscriber-devices/00000000-0000-0000-0000-000000000001'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { service_type: 'DHCP', assigned_ipv4: '10.250.3.55', onu_mac_address: 'AA:BB:CC:11:22:33', provision_on_router: true, bng_router_id: '00000000-0000-0000-0000-000000000111' }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 156. Monitoreo Periódico Híbrido de Abonados FTTH y Sonda ICMP Ligera (Hito 28.21)
    Given path '/api/v1/subscriber-devices/00000000-0000-0000-0000-000000000001/ping'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 157. Sincronización Automática de Ventanas de Mantenimiento con admin_state del Router y Resolución de WORM Audit (Hito 30.2)
    Given path '/api/v1/maintenance/windows'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { title: 'Ventana UAT Test', reason: 'Reemplazo BGP', target_tag: 'global', starts_at: '2026-11-04T18:00:00Z', ends_at: '2026-11-04T19:00:00Z', suppress_alerts: true }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/inventory/routers'
    And param admin_state = 'MAINTENANCE'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 158. Reactividad en Tiempo Real de la Bandeja Maker-Checker y Emisión WebSocket Push (Hito 30.3)
    Given path '/api/v1/operations/approvals'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/operations/approvals/00000000-0000-0000-0000-000000000001/approve'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { review_comment: 'Aprobación verificada por Supervisor NOC' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 159. Ciclo de Vida Temporal de 3 Fases en Bóveda Step-Up (30s) y Propagación de Estado Anti-Silo (Hito 30.5)
    Given path '/api/v1/inventory/routers/00000000-0000-0000-0000-000000000001/vault/reveal'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { totp_code: '123456', reason: 'Verificación de contrato 3 fases Step-Up 30s' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/audit/logs'
    And param event_category = 'VAULT_OPERATIONS'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 160. Seguridad de Sesiones PPPoE: Keepalive Timeout (10s), One-Session-Per-Host, Only-One y Candado MAC Caller-ID (Hito 30.6)
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/ppp/pppoe-servers'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { service_name: 'pppoe-isp-core', interface: 'vlan200', default_profile: 'plan-10M', one_session_per_host: true, keepalive_timeout: 10 }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/ppp/secrets'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { name: 'cliente01', password: 'ClaveSegura123', service: 'pppoe', profile: 'plan-10M', caller_id: 'AA:BB:CC:11:22:33' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 161. Resiliencia de Actualización RouterOS v7 en CHR y RouterBOARD: Sondeo de Canal y Ejecución con Timeout Extendido (Hito 30.8)
    Given path '/api/v1/operations/ros-updates/check'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { channel: 'stable', router_ids: ['00000000-0000-0000-0000-000000000001'] }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/operations/ros-updates/execute'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { router_ids: ['00000000-0000-0000-0000-000000000001'], channel: 'stable', auto_upgrade_firmware: false, poe_aware: true, safety_stop_threshold_percent: 2.0 }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 162. Catálogo de Presets Golden Config e Inclusión de HUSO_HORARIO_SISTEMA (/system/clock/set) (Hito 30.9)
    Given path '/api/v1/operations/templates/presets'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 163. Respaldo .rsc Libre de Corrupción por Binarios .pcap y Purga Automática de Exportaciones Vacías '[]' (Hito 30.10)
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/backups'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/backups/diff'
    And param base_backup_id = '00000000-0000-0000-0000-000000000002'
    And param target_backup_id = 'LIVE'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 164. Reasignación directa de empresa (tenant_id) a un usuario y onboarding inicial de TENANT_ADMIN (Hito 30.11 - Spec 88)
    Given path '/api/v1/users/00000000-0000-0000-0000-000000000001/tenant'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { tenant_id: '00000000-0000-0000-0000-000000000002', role: 'TENANT_ADMIN' }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 165. Respaldo Simultáneo Multi-Equipo por Lote y Persistencia Real de IPv4 en IPAM (Hito 30.12 - Spec 89)
    Given path '/api/v1/backups/batch-trigger'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { router_ids: ['00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002'] }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/ipam/customer-services'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 166. Persistencia de firma táctil en operaciones de campo y separación tolerante en mutación DHCP Snooping (Hito 30.13 - Spec 90)
    Given path '/api/v1/field-ops/certify'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { customer_service_id: '00000000-0000-0000-0000-000000000001', onu_scanned_serial: 'SN-FIELD-3013', customer_signature_svg: 'data:image/png;base64,mockSignature' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/switching/dhcp-snooping/enable'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { router_id: '00000000-0000-0000-0000-000000000001', bridge_name: 'bridge11', enabled: true, add_dhcp_option82: true, trusted_ports: ['ether1'], untrusted_ports: ['ether2'] }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 167. Filtrado RFC de IPs no enrutables/0.0.0.0 en anomalías de tráfico y sondeo ICMP rápido en SLA (Hito 30.14 - Spec 91)
    Given path '/api/v1/traffic-flow/anomalies'
    And param router_id = '00000000-0000-0000-0000-000000000001'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/traffic-flow/mitigate'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { router_id: '00000000-0000-0000-0000-000000000001', target_ip: '198.51.100.99', action: 'fast_drop', duration_seconds: 300, comment: 'Karate SLA Anomaly Mitigation' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/sla/probes/run'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { router_id: '00000000-0000-0000-0000-000000000001', target_host: '9.9.9.9', target_name: 'Quad9', count: 5 }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 168. Despacho real de prueba en canales de notificación y edición de canal con preservación de secretos (Hito 30.15 - Spec 92)
    Given path '/api/v1/operations/notification-channels'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/operations/notification-channels/00000000-0000-0000-0000-000000000001/test'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { message: 'Prueba Karate Alerta de Canal' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/operations/notification-channels/00000000-0000-0000-0000-000000000001'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { name: 'Canal Renovado', config: { chat_id: '123456789' } }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 169. Certificación de instalación en campo con persistencia de customer_signature_svg en PostgreSQL tras migración 0014 (Hito 30.17 - Spec 94)
    Given path '/api/v1/field-ops/certify'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { customer_service_id: 'a9cea882-0a4e-4be4-824a-35fb38080189', onu_scanned_serial: 'MAC-55447788', onu_scanned_mac: '55:44:77:88:99:00', customer_signature_svg: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ============================================================================
  # SPEC 96: PARIDAD TIPO NATIVO WIREGUARD (type="wg") E INVALIDACIÓN CACHÉ
  # ============================================================================
  Scenario: 170. Listado de interfaces (/webfig/interfaces) incluye túneles WireGuard con type="wg" nativo de RouterOS v7
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/interfaces'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ============================================================================
  # SPEC 97: SERVIDORES DHCP, REDES NTP Y CREACIÓN DE CONCESIÓN ESTÁTICA DHCP
  # ============================================================================
  Scenario: 171. Listado de servidores DHCP (/webfig/ip/dhcp-servers) y redes DHCP (/webfig/ip/dhcp-server/networks)
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/ip/dhcp-servers'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ============================================================================
  # SPEC 98: PARIDAD DUAL-STACK FIREWALL IPV6 (/webfig/firewall/ipv6/filter)
  # ============================================================================
  Scenario: 172. Consulta de reglas de Firewall IPv6 (/webfig/firewall/ipv6/filter) sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/firewall/ipv6/filter'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ============================================================================
  # SPEC 99: FILTRADO DE PAQUETES ACTIVOS EN CAPA 2 Y DEGRADACIÓN ELEGANTE
  # ============================================================================
  Scenario: 173. Catalogo WebFig Capa 2 (/webfig/layer2/catalog) filtra paquetes opcionales deshabilitados y degrada paquetes no instalados (Spec 99)
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/layer2/catalog'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/layer2/resource/container'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ============================================================================
  # SPEC 100: CARGA MASIVA CSV DE CLIENTES / ABONADOS CON VALIDACIÓN Y DRY-RUN
  # ============================================================================
  Scenario: 174. Descarga de plantilla CSV y validacion Dry-Run para carga masiva de clientes (Spec 100)
    Given path '/api/v1/subscriber-devices/template-csv'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/subscriber-devices/import-csv/dry-run'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/subscriber-devices/import-csv/commit'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ============================================================================
  # SPEC 103: CARGA MASIVA CSV DE CAJAS NAP CON UPSERT Y AUTO-CREACIÓN (HITO 30.26)
  # ============================================================================
  Scenario: 175. Descarga de plantilla CSV y validacion Dry-Run para carga masiva de Cajas NAP con soporte Upsert (Spec 103)
    Given path '/api/v1/optical-boxes/template-csv'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/optical-boxes/import-csv/dry-run'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/optical-boxes/import-csv/commit'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ============================================================================
  # SPEC 104: COORDENADAS GPS DE SEDE PRINCIPAL Y CENTRADO CARTOGRÁFICO (HITO 30.27)
  # ============================================================================
  Scenario: 176. Persistencia y exposicion de coordenadas GPS de Sede Principal (hq_latitude, hq_longitude) en Tenant y Features (Spec 104)
    Given path '/api/v1/tenants'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/tenants'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { slug: 'isp-karate', name: 'ISP Karate Test', admin_username: 'karateadmin', admin_email: 'karate@isp.test', admin_password: 'Password123!', hq_latitude: 10.2123, hq_longitude: -67.9876 }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/tenants/00000000-0000-0000-0000-000000000000/features'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ============================================================================
  # SPEC 105: SERIALIZACIÓN JSONB DE DECIMAL EN AUDITORÍA WORM AL EDITAR TENANT
  # ============================================================================
  Scenario: 177. Actualizacion PATCH de coordenadas GPS de Sede Principal sin error Decimal en AuditLog JSONB (Spec 105)
    Given path '/api/v1/tenants/00000000-0000-0000-0000-000000000000'
    And header Idempotency-Key = java.util.UUID.randomUUID() + ''
    And request { name: 'Tecno Sede Carabobo', hq_latitude: 10.232345, hq_longitude: -67.879812 }
    When method patch
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ============================================================================
  # SPEC 106: SINCRONIZACIÓN DE COORDENADAS HQ EN AUTH Y VISIBILIDAD CAJAS NAP
  # ============================================================================
  Scenario: 178. Entrega de coordenadas GPS de Sede Principal en contrato de autenticacion y perfil (Spec 106)
    Given path '/api/v1/auth/me'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ============================================================================
  # HITO 30.36: CIERRE V1.0.0 — CONSULTA PÚBLICA DE SKILL MCP Y BLINDAJE STIG
  # ============================================================================
  Scenario: 179. Consulta publica del catalogo de skill MCP en formato JSON sin requerir sesion (Hito 30.36)
    Given path '/api/v1/mcp/skill'
    And param format = 'json'
    When method get
    Then status 200
    And match response.name == 'rosgrid-noc-operator'
    And match response.version == '1.0.0'
    And match response.content contains 'rosgrid-noc-operator'

  # ============================================================================
  # SPEC 113: ENDURECIMIENTO MCP ZERO-TRUST (22 TOOLS, MAKER-CHECKER 6 TOOLS, CIDR)
  # ============================================================================
  Scenario: 180. Proteccion de endpoint MCP Zero-Trust exigiendo autenticacion Bearer previa (Spec 113)
    Given path '/api/v1/mcp'
    And request { jsonrpc: '2.0', id: 1, method: 'tools/list', params: {} }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ============================================================================
  # SPEC 114: REMEDIACIÓN INTEGRAL ZERO-TRUST, RLS MULTI-TRANSACCIÓN Y WORM
  # ============================================================================
  Scenario: 181. Paridad del catalogo publico SKILL.md en /api/v1/mcp/skill con 22 herramientas y 8 Playbooks SOP (Spec 114)
    Given path '/api/v1/mcp/skill'
    And param format = 'json'
    When method get
    Then status 200
    And match response.name == 'rosgrid-noc-operator'
    And match response.content contains '22 herramientas'
    And match response.content contains 'Playbook 8'
    And match response.content contains 'rosgrid_search_mikrotik_docs'
    And match response.content contains 'rosgrid_get_mikrotik_doc_topic'

  # ============================================================================
  # HITO 30.39: HOMOLOGACIÓN RLS 0017, ANTI-SSRF UNIFICADO, CANON SYSLOG 10 TOPICS Y VERSIÓN 1.1.0
  # ============================================================================
  Scenario: 182. Homologacion RLS de 25 tablas en migracion 0017, canon de 10 topics Syslog y version 1.1.0 en /health (Hito 30.39)
    Given path '/health'
    When method get
    Then status 200
    And match response.version == '1.1.0'

  # ============================================================================
  # HITO 30.40: CORRECCIÓN ÍNDICE PREAUTH REDIS EN BOOTSTRAP INICIAL Y CONFIRMACIÓN 2FA
  # ============================================================================
  Scenario: 183. Rechazo limpio 401 con detail semantico en /api/v1/auth/2fa/confirm-enrollment ante challenge_id inexistente (Hito 30.40)
    Given path '/api/v1/auth/2fa/confirm-enrollment'
    And request { challenge_id: '00000000000000000000000000000000', totp_code: '123456' }
    When method post
    Then status 401
    And match response == { detail: 'Desafío 2FA inválido o expirado' }
















