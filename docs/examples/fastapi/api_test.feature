# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

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
    And match response.detail[0].type == '#string'

  Scenario: 6. Solicitud de auto-registro con campos faltantes devuelve HTTP 422
    Given path '/api/v1/auth/register'
    And request { username: "operador_nuevo" }
    When method post
    Then status 422
    And match response.detail[0].type == '#string'

  Scenario: 7. Verificación de segundo factor 2FA con payload inválido devuelve HTTP 422
    Given path '/api/v1/auth/2fa/verify'
    And request { challenge_id: "invalido", totp_code: "12" }
    When method post
    Then status 422
    And match response.detail[0].type == '#string'

  Scenario: 8. Rotación de Refresh Token sin cookie de sesión activa devuelve 401
    Given path '/api/v1/auth/refresh'
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

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
    And header Idempotency-Key = '01928900-0000-7000-8000-000000000010'
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
    And header Idempotency-Key = '01928900-0000-7000-8000-000000000011'
    And request { enabled: false }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 15. Aprobación de operador pendiente sin privilegios devuelve 401
    Given path '/api/v1/users/00000000-0000-0000-0000-000000000001/approve'
    And header Idempotency-Key = '01928900-0000-7000-8000-000000000012'
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
    And header Idempotency-Key = '01928900-0000-7000-8000-000000000013'
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
    And header Idempotency-Key = '01928900-0000-7000-8000-000000000014'
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 20b. Validación de auto-pinning TOFU continuo y sincronización sin sesión devuelve 401
    Given path '/api/v1/inventory/routers/00000000-0000-0000-0000-000000000001/sync-discovery'
    And header Idempotency-Key = '01928900-0000-7000-8000-000000000015'
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 21. Catálogo de roles personalizados de infraestructura sin sesión devuelve 401
    Given path '/api/v1/inventory/roles'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 7: Bóveda Criptográfica (Split-Credential) y Step-Up 2FA
  # ==============================================================================

  Scenario: 22. Revelación de clave de router sin Step-Up 2FA TOTP devuelve 401
    Given path '/api/v1/inventory/routers/00000000-0000-0000-0000-000000000001/vault/reveal'
    And header Idempotency-Key = '01928900-0000-7000-8000-000000000015'
    And request { totp_code: '123456', reason: 'Auditoría no autorizada' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 23. Disparo de rotación automática transaccional de clave sin autenticación devuelve 401
    Given path '/api/v1/inventory/routers/00000000-0000-0000-0000-000000000001/vault/rotate'
    And header Idempotency-Key = '01928900-0000-7000-8000-000000000016'
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 8: IPAM Dual-Stack (IPv4 / IPv6) y Pools
  # ==============================================================================

  Scenario: 24. Inspección de subredes IPAM sin sesión devuelve 401
    Given path '/api/v1/ipam/subnets'
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
    And header Idempotency-Key = '01928900-0000-7000-8000-000000000017'
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
    Given path '/api/v1/field-ops/diagnostics/00000000-0000-0000-0000-000000000001/sfp-sfpplus1'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 12: Ventanas de Mantenimiento Programadas
  # ==============================================================================

  Scenario: 32. Consulta de ventanas de mantenimiento sin autenticación devuelve 401
    Given path '/api/v1/maintenance-windows'
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
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/firewall/filter'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 35. Proxy universal de Capa 2 RouterOS v7 sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/layer2/interface/bridge'
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
    Given path '/api/v1/notifications/channels'
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
    Given path '/api/v1/audit/verify-chain'
    When method get
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
    Given path '/api/v1/compliance/cis-benchmark'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 49. Detección de desviación de configuración (Config Drift) sin sesión devuelve 401
    Given path '/api/v1/compliance/drift'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 50. Consulta de topologías SD-WAN WireGuard Hub & Spoke sin sesión devuelve 401
    Given path '/api/v1/sdwan/topologies'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 51. Consulta de eventos de Rogue DHCP Snooping en switches sin autenticación devuelve 401
    Given path '/api/v1/switching/dhcp-snooping/events'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 52. Consulta de métricas SLA de carriers sin autenticación devuelve 401
    Given path '/api/v1/sla/metrics'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 53. Consulta de radios WiFi corporativos CAPsMAN sin autenticación devuelve 401
    Given path '/api/v1/wifi/capsman/radios'
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

  Scenario: 61. Ejecución de actualización masiva con orden PoE-aware sin autenticación devuelve 401
    Given path '/api/v1/operations/ros-updates/execute'
    And request { router_ids: ['00000000-0000-0000-0000-000000000001'], poe_aware: true }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  # ==============================================================================
  # Grupo 12: Onboarding Masivo CSV y Catálogo de Roles de Red Dinámicos
  # ==============================================================================

  Scenario: 62. Validación en seco (dry-run) de importación masiva CSV sin autenticación devuelve 401
    Given path '/api/v1/inventory/import-csv/dry-run'
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 63. Confirmación transaccional (commit) de importación masiva CSV sin autenticación devuelve 401
    Given path '/api/v1/inventory/import-csv/commit'
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
    And match responseHeaders['Content-Disposition'][0] contains 'rosgrid-inventario-plantilla.csv'

  Scenario: 66. Aprobación de solicitud Maker-Checker sin autenticación devuelve 401
    Given path '/api/v1/operations/approvals/00000000-0000-0000-0000-000000000001/approve'
    And request { review_comment: 'Aprobación autorizada' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 67. Rechazo de solicitud Maker-Checker sin autenticación devuelve 401
    Given path '/api/v1/operations/approvals/00000000-0000-0000-0000-000000000001/reject'
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
    Given path '/api/v1/operations/templates/apply-preview'
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
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 82. Test Ping ICMP 1-Click hacia dispositivo de red sin autenticación devuelve 401
    Given path '/api/v1/subscriber-devices/00000000-0000-0000-0000-000000000001/ping'
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 83. Gobernanza Anti-Saturación — Diagnóstico Ping ICMP con Caché KeyDB y Semáforo Concurrente
    Given path '/api/v1/subscriber-devices/00000000-0000-0000-0000-000000000001/ping'
    And header Idempotency-Key = 'test-ping-governor-key'
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
    And param force = true
    And param extended = true
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 86. Remediación individual selectiva CIS Benchmark con Safe Mode sin autenticación devuelve 401
    Given path '/api/v1/compliance/cis-audit/00000000-0000-0000-0000-000000000001/auto-harden'
    And request { router_id: '00000000-0000-0000-0000-000000000001', directive_codes_to_apply: ['CIS-1.1'] }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 87. Remediación individual CIS-1.8 de defensa contra fuerza bruta (SSH/WinBox) sin autenticación devuelve 401
    Given path '/api/v1/compliance/cis-audit/00000000-0000-0000-0000-000000000001/auto-harden'
    And request { router_id: '00000000-0000-0000-0000-000000000001', directive_codes_to_apply: ['CIS-1.8'] }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 88. Consulta de alertas de Rogue DHCP en switches MikroTik sin autenticación devuelve 401
    Given path '/api/v1/switching/routers/00000000-0000-0000-0000-000000000001/rogue-dhcp/alerts'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 89. Notificación de Cierre de Sesión / Ventana (session-closing) sin session_id devuelve 400
    Given path '/api/v1/auth/session-closing'
    And request {}
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
    And request { profile: 'ISP', rules: [] }
    When method put
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 92. Finalización de Onboarding de Tenant sin autenticación devuelve 401
    Given path '/api/v1/tenants/00000000-0000-0000-0000-000000000001/onboarding-complete'
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 93. Conmutación Rápida de Tenants (switch-tenant) sin autenticación devuelve 401
    Given path '/api/v1/auth/switch-tenant'
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
    And request { address: '192.168.100.0/24', gateway: '192.168.100.1' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 100. Renovación de concesión de cliente DHCP WAN sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/ip/dhcp-clients/c1/renew'
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
    And request { bridge: 'bridge1', vlan_ids: '10,20', tagged: 'ether1', untagged: 'ether2' }
    When method post
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

  Scenario: 105. Creación de subinterfaz VLAN 802.1Q sin autenticación devuelve 401
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/webfig/interfaces/vlan'
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










