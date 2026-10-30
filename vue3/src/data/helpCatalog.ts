// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors
/* eslint-disable sonarjs/no-duplicate-string, security/detect-object-injection */

export interface ContextualHelpStep {
  title: string;
  description: string;
}

export interface ContextualHelpEntry {
  routeKey: string;
  title: string;
  moduleBadge: string;
  summary: string;
  keyActions: ContextualHelpStep[];
  safetyAndGovernance: string[];
  mikrotikV7Notes: string[];
  relatedRoles: string[];
}

export const CONTEXTUAL_HELP_CATALOG: Record<string, ContextualHelpEntry> = {
  dashboard: {
    routeKey: 'dashboard',
    title: 'Centro de Mando Global (Dashboard NOC)',
    moduleBadge: 'NÚCLEO GLOBAL • OBSERVABILIDAD',
    summary:
      'Vista panorámica en tiempo real del estado de la flota MikroTik RouterOS v7+, colector Syslog UDP 5514, alertas activas y solicitudes Maker-Checker pendientes.',
    keyActions: [
      {
        title: 'Inspeccionar KPIs de Flota',
        description:
          'Verifica cuántos equipos están Online, Offline, en Ventana de Mantenimiento o con Syslog activo.',
      },
      {
        title: 'Acceso Rápido a Consola WebFig',
        description:
          'Haz clic sobre cualquier router crítico o usa Ctrl+K para saltar directamente a su consola WebFig v7.',
      },
      {
        title: 'Monitoreo de Eventos NOC',
        description:
          'Revisa el feed en tiempo real alimentado por el colector Syslog efímero y el sondeo pasivo Zero-Storage.',
      },
    ],
    safetyAndGovernance: [
      'Aislamiento estricto por empresa (PostgreSQL 17 Row-Level Security).',
      'Arquitectura Zero-Metrics Storage: la telemetría de alta frecuencia vive en KeyDB RAM sin saturar el disco.',
    ],
    mikrotikV7Notes: [
      'Los indicadores de salud se calculan mediante /rest/system/resource y /rest/system/health en RouterOS v7.1+.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2', 'SUPPORT_L1'],
  },
  inventory: {
    routeKey: 'inventory',
    title: 'Inventario de Equipos, SSL TOFU y Bóveda Zero-Trust',
    moduleBadge: 'INVENTARIO & CRIPTOGRAFÍA • CAPA 1',
    summary:
      'Gestión del catálogo de routers MikroTik RouterOS v7+, importación masiva CSV en 2 fases, fijado criptográfico de huella TLS SHA-256 (TOFU) y revelación Step-Up Auth (30s).',
    keyActions: [
      {
        title: 'Alta Individual o Importación CSV (Dry-Run + Commit)',
        description:
          'Registra routers indicando IP/FQDN, puerto HTTPS REST (443) y credenciales cifradas con AES-256-GCM.',
      },
      {
        title: 'Descubrimiento y Pinning SSL TOFU',
        description:
          'Pulsa Descubrir (TOFU) para extraer y fijar la huella SHA-256 del certificado X.509 e interrogar modelo, serie y versión.',
      },
      {
        title: 'Sincronización Automática de 9 Reglas Syslog',
        description:
          'Configura en 1 clic el envío de eventos críticos, system,info, account y firewall,info hacia el colector UDP 5514.',
      },
      {
        title: 'Bóveda Step-Up 2FA (30 Segundos)',
        description:
          'Desbloquea temporalmente una credencial ingresando un código TOTP válido; se purga de RAM automáticamente a los 30s.',
      },
    ],
    safetyAndGovernance: [
      'Validación Anti-SSRF estricta sobre direcciones IP/FQDN antes de abrir sockets TLS.',
      'Toda revelación de contraseña en la bóveda genera un registro inmutable WORM (VAULT_CREDENTIAL_REVEALED).',
    ],
    mikrotikV7Notes: [
      'Requiere el servicio www-ssl activo en /ip/service y usuario con políticas rest-api,read,write,policy,test,sensitive.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'INVENTORY_MANAGER', 'SUPERVISOR', 'SUPPORT_L3'],
  },
  wallboard: {
    routeKey: 'wallboard',
    title: 'Wallboard NOC 24/7 para Pantallas de Videowall',
    moduleBadge: 'MONITOREO 24/7 • VIDEOWALL',
    summary:
      'Interfaz de alto contraste diseñada para operación continua en pantallas de NOC con detección temprana de caídas masivas, corte de fibra GPON y mapa de incidentes.',
    keyActions: [
      {
        title: 'Conmutar Pantalla Completa y Tema NOC High-Contrast',
        description:
          'Optimiza el contraste sobre fondo negro puro (#000000) para máxima legibilidad a distancia en salas de control.',
      },
      {
        title: 'Correlación de Caídas Masivas',
        description:
          'Identifica nodos troncales caídos y el número de suscriptores PPPoE/DHCP impactados aguas abajo.',
      },
    ],
    safetyAndGovernance: [
      'El rol NOC_MONITOR está confinado exclusivamente a esta vista de solo lectura sin acceso a mutaciones.',
    ],
    mikrotikV7Notes: [
      'Integra alertas ópticas SFP+ DDM (/rest/interface/ethernet/monitor) y caídas de sesiones BGP/OSPF.',
    ],
    relatedRoles: ['NOC_MONITOR', 'SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2', 'SUPPORT_L1'],
  },
  approvals: {
    routeKey: 'approvals',
    title: 'Bandeja de Gobernanza Maker-Checker (HTTP 202)',
    moduleBadge: 'GOBERNANZA HUMANA • MAKER-CHECKER',
    summary:
      'Flujo de doble control criptográfico para revisar, aprobar o rechazar mutaciones sensibles propuestas por operadores N1/N2 o agentes IA vía MCP.',
    keyActions: [
      {
        title: 'Inspeccionar Payload y Estado Previo',
        description:
          'Revisa el método REST, la ruta /rest/*, los atributos propuestos y la justificación del solicitante.',
      },
      {
        title: 'Aprobar y Ejecutar con Safe Mode (60s)',
        description:
          'Autoriza el cambio para que RoSGrid lo aplique en el router bajo protección de reversión automática.',
      },
      {
        title: 'Rechazar con Motivo Auditado',
        description:
          'Descarta la solicitud dejando constancia inmutable en la bitácora forense WORM.',
      },
    ],
    safetyAndGovernance: [
      'Invariante estricto maker != checker: un operador jamás puede aprobar su propia solicitud.',
      'Las solicitudes no atendidas expiran automáticamente a las 24 horas.',
    ],
    mikrotikV7Notes: [
      'Al aprobarse una solicitud, la ejecución en el router arma automáticamente el scheduler rosgrid-safemode-* a 60s.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3'],
  },
  ipam: {
    routeKey: 'ipam',
    title: 'IPAM Dual-Stack Universal (IPv4 / IPv6) y Pools',
    moduleBadge: 'GESTIÓN IPAM • DUAL-STACK',
    summary:
      'Administración centralizada de prefijos IPv4/IPv6, rejilla visual /24 de 256 direcciones, delegación DHCPv6-PD y detección de agotamiento de pools.',
    keyActions: [
      {
        title: 'Inspeccionar Rejilla /24 de 256 IPs',
        description:
          'Haz clic en un prefijo IPv4 para visualizar qué direcciones están libres, asignadas por DHCP/PPPoE o reservadas.',
      },
      {
        title: 'Gestionar Prefijos IPv6 Corporativos y PD',
        description:
          'Administra bloques /48, /56 y /64 sincronizados con los pools de tus routers MikroTik.',
      },
    ],
    safetyAndGovernance: [
      'Evita colisiones de direccionamiento IP y alerta proactivamente cuando un pool supera el 85% de ocupación.',
    ],
    mikrotikV7Notes: [
      'Sincroniza contra /rest/ip/pool, /rest/ip/dhcp-server/lease y /rest/ipv6/pool en RouterOS v7.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2'],
  },
  'subscribers-map': {
    routeKey: 'subscribers-map',
    title: 'Mapa Geográfico de Red, NAPs FTTH y Clientes',
    moduleBadge: 'CARTOGRAFÍA NOC • RCA',
    summary:
      'Cartografía interactiva bimodal (ISP FTTH/WISP y Campus Corporativo) con análisis de causa raíz (RCA) y alertas de corte de fibra.',
    keyActions: [
      {
        title: 'Filtrar por Estado de Suscriptor o Caja NAP',
        description:
          'Localiza clientes activos, aislados o sin potencia óptica sobre teselas OpenStreetMap.',
      },
      {
        title: 'Ejecutar Diagnóstico Rápido desde el Pin',
        description:
          'Selecciona un nodo en el mapa para inspeccionar su sesión PPPoE/DHCP y niveles de señal.',
      },
    ],
    safetyAndGovernance: [
      'Bloqueo anti-colisión en KeyDB para evitar que dos operadores intervengan simultáneamente la misma caja NAP.',
    ],
    mikrotikV7Notes: [
      'Correlaciona sesiones /rest/ppp/active y /rest/ip/dhcp-server/lease con coordenadas registradas.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2', 'SUPPORT_L1', 'FIELD_TECH'],
  },
  'field-tech': {
    routeKey: 'field-tech',
    title: 'Consola de Operaciones de Campo (Field Tech Toolkit)',
    moduleBadge: 'CAMPO & ÚLTIMA MILLA • MÓVIL',
    summary:
      'Herramienta optimizada para teléfonos y tablets de cuadrillas técnicas con diagnóstico 360° en 1 clic, validación óptica SFP DDM y reconexión N1.',
    keyActions: [
      {
        title: 'Ejecutar Diagnóstico 360° de Abonado',
        description:
          'Verifica estado de sesión PPPoE, cola QoS, ARP, ping Multi-MTU y niveles ópticos sin abrir consola completa.',
      },
      {
        title: 'Actualizar Coordenadas GPS de Instalación',
        description:
          'Registra la ubicación exacta del CPE o caja de distribución desde el navegador móvil.',
      },
    ],
    safetyAndGovernance: [
      'El rol FIELD_TECH solo puede ejecutar pruebas acotadas y acciones autorizadas sin modificar el core de red.',
    ],
    mikrotikV7Notes: [
      'Utiliza /rest/tool/ping con paquetes de 64B, 512B y 1472B (do-not-fragment) para detectar problemas de MTU.',
    ],
    relatedRoles: ['FIELD_TECH', 'SUPPORT_L1', 'SUPPORT_L2', 'SUPPORT_L3', 'SUPERVISOR', 'TENANT_ADMIN', 'SUPERADMIN_GLOBAL'],
  },
  'topology-l2': {
    routeKey: 'topology-l2',
    title: 'Topología Física Capa 2 (MNDP / LLDP / CDP & PoE)',
    moduleBadge: 'TOPOLOGÍA L2 • DESCUBRIMIENTO',
    summary:
      'Grafo interactivo de adyacencias físicas descubiertas automáticamente entre routers, switches CRS y puntos de acceso MikroTik.',
    keyActions: [
      {
        title: 'Explorar Vecinos Descubiertos',
        description:
          'Inspecciona por qué interfaz física o VLAN se conectan dos equipos, su versión de RouterOS y dirección MAC.',
      },
      {
        title: 'Verificar Telemetría PoE-Out',
        description:
          'Comprueba el consumo en vatios (W) y estado de alimentación en puertos PoE antes de reiniciar equipos.',
      },
    ],
    safetyAndGovernance: [
      'Invariante negativo: cuando la tabla de vecinos está vacía, no se inventan enlaces ni se falla ante MACs de terceros.',
    ],
    mikrotikV7Notes: [
      'Consulta /rest/ip/neighbor y /rest/interface/ethernet/poe/monitor en RouterOS v7.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2'],
  },
  'backups-diff': {
    routeKey: 'backups-diff',
    title: 'Respaldos .rsc Deduplicados y Comparador Git Diff',
    moduleBadge: 'CONTROL DE CAMBIOS • GIT DIFF',
    summary:
      'Historial inmutable de exportaciones .rsc con deduplicación SHA-256 y comparador visual línea por línea contra el estado en vivo del router.',
    keyActions: [
      {
        title: 'Capturar Respaldo Manual o Inspeccionar Nocturnos',
        description:
          'Genera una instantánea .rsc bajo demanda o selecciona dos versiones históricas para compararlas.',
      },
      {
        title: 'Comparar contra Configuración LIVE',
        description:
          'Detecta en segundos qué líneas fueron añadidas (+) o eliminadas (-) respecto a la línea base aprobada.',
      },
    ],
    safetyAndGovernance: [
      'Los secretos sensibles son sanitizados o cifrados en reposo con retención automática configurable.',
    ],
    mikrotikV7Notes: [
      'Ejecuta /rest/export con formato compact para obtener una salida determinista libre de ruido.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2', 'AUDITOR'],
  },
  'bulk-ops': {
    routeKey: 'bulk-ops',
    title: 'Operaciones Masivas (24 Golden Configs) y Firmware PoE-Aware',
    moduleBadge: 'AUTOMATIZACIÓN DE FLOTA • BULK-OPS',
    summary:
      'Despliegue masivo parametrizado de 24 plantillas Golden Config (BGP RPKI, CGNAT, CoPP, BCP38, CAKE, WireGuard) y actualización de RouterOS con orden DAG PoE-Aware.',
    keyActions: [
      {
        title: 'Aplicar Plantilla Golden Config con Safe Mode (60s)',
        description:
          'Selecciona una plantilla del catálogo, completa sus variables tipadas y previsualiza los comandos antes de despachar.',
      },
      {
        title: 'Actualización de Firmware PoE-Aware con Safety Stop (1%)',
        description:
          'Actualiza primero los CPEs/APs alimentados por PoE y al final el switch/router PoE-Out, abortando si falla > 1% del lote.',
      },
    ],
    safetyAndGovernance: [
      'Cada ejecución masiva inyecta schedulers Safe Mode individuales en cada router objetivo.',
      'Los operadores SUPPORT_L2 requieren aprobación Maker-Checker para despachar lotes masivos.',
    ],
    mikrotikV7Notes: [
      'Utiliza /rest/system/package/update/check-for-updates y /rest/system/routerboard/upgrade en RouterOS v7.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2'],
  },
  maintenance: {
    routeKey: 'maintenance',
    title: 'Ventanas de Mantenimiento Programadas y Auto-Expiración WORM',
    moduleBadge: 'OPERACIONES NOC • MANTENIMIENTO',
    summary:
      'Programación de ventanas de trabajo para suprimir alertas falsas positivas durante cortes programados, con auto-eliminación auditada al vencer.',
    keyActions: [
      {
        title: 'Programar Nueva Ventana de Mantenimiento',
        description:
          'Define título, rango horario UTC, motivo técnico y los routers incluidos en la intervención.',
      },
      {
        title: 'Auto-Eliminación al Vencer (Hito 27.12.7)',
        description:
          'Al cumplirse ends_at <= now(UTC), RoSGrid purga automáticamente la ventana vencida y graba un registro WORM.',
      },
    ],
    safetyAndGovernance: [
      'Toda creación, cancelación o expiración automática genera un evento firmado en AuditLog (MAINTENANCE_WINDOW_EXPIRED_AUTO_DELETED).',
    ],
    mikrotikV7Notes: [
      'Durante una ventana activa, el monitor de salud mantiene la visibilidad del equipo sin disparar tormentas de alertas.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3'],
  },
  'users-rbac': {
    routeKey: 'users-rbac',
    title: 'Usuarios, Matriz de 11 Roles RBAC y Tokens MCP para IA',
    moduleBadge: 'IDENTIDAD ZERO-TRUST • RBAC & MCP',
    summary:
      'Administración de operadores humanos y cuentas de servicio IA (SERVICE_ACCOUNT), aprobación de auto-registro, permisos granulares por router y emisión de tokens MCP.',
    keyActions: [
      {
        title: 'Crear Usuario o Aprobar Solicitud Pendiente',
        description:
          'Asigna uno de los 11 roles RBAC, lista blanca CIDR opcional y política de acceso global o por router específico.',
      },
      {
        title: 'Emitir Token Bearer MCP y Copiar Contexto llms.txt',
        description:
          'Genera credenciales JWT de larga duración para conectar Claude Code, Codex, Cursor, Copilot, Claude Desktop o Hermes Agent.',
      },
    ],
    safetyAndGovernance: [
      'Autenticación Argon2id + 2FA TOTP obligatorio en el inicio de sesión humano.',
      'Los tokens MCP respetan la lista blanca CIDR del usuario y pueden revocarse en 1 clic desde Sesiones Activas.',
    ],
    mikrotikV7Notes: [
      'Los operadores nunca conocen la clave del router MikroTik; operan a través del proxy autenticado de RoSGrid.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN'],
  },
  sessions: {
    routeKey: 'sessions',
    title: 'Sesiones Activas en KeyDB y Kill-Switch en Tiempo Real',
    moduleBadge: 'SEGURIDAD ACTIVA • KILL-SWITCH',
    summary:
      'Auditoría en vivo de todas las sesiones humanas y de agentes IA conectadas en KeyDB, con revocación instantánea por WebSocket.',
    keyActions: [
      {
        title: 'Inspeccionar Sesiones Humanas y Tokens MCP',
        description:
          'Visualiza usuario, rol, dirección IP de origen, User-Agent y fecha de creación/expiración.',
      },
      {
        title: 'Ejecutar Kill-Switch Inmediato',
        description:
          'Revoca cualquier sesión sospechosa en milisegundos; el navegador o agente afectado es desconectado al instante.',
      },
    ],
    safetyAndGovernance: [
      'Detección automática de robo de Refresh Token (Reuse Detection) con ventana de gracia de 35s sincronizada por BroadcastChannel.',
    ],
    mikrotikV7Notes: [
      'Al revocar una sesión, cualquier petición en vuelo hacia /api/v1/routers/*/webfig/* es bloqueada inmediatamente con HTTP 401.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR'],
  },
  tenants: {
    routeKey: 'tenants',
    title: 'Administración Multi-Tenant de Empresas y Organizaciones',
    moduleBadge: 'GOBERNANZA B2B • MULTI-TENANT',
    summary:
      'Gestión de inquilinos (Tenants), cuotas de equipos, aislamiento criptográfico RLS y acceso al Estudio de Módulos y Capacidades.',
    keyActions: [
      {
        title: 'Crear o Editar Organización (Tenant)',
        description:
          'Define nombre comercial, slug único, estado activo y límite contractual de routers.',
      },
      {
        title: 'Conmutar Contexto de Empresa en Caliente',
        description:
          'El SUPERADMIN_GLOBAL puede cambiar de empresa desde la barra superior sin cerrar sesión.',
      },
    ],
    safetyAndGovernance: [
      'Políticas Row-Level Security (RLS) forzadas en PostgreSQL 17 mediante app.current_tenant_id en cada transacción.',
    ],
    mikrotikV7Notes: [
      'Las cachés de KeyDB y las colas de telemetría están particionadas por el prefijo rg:{tenant_id}:*.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN'],
  },
  'tenant-modules': {
    routeKey: 'tenant-modules',
    title: 'Estudio de 19 Feature Flags B2B, DAG en Cascada y Rollback WORM',
    moduleBadge: 'LICENCIAMIENTO B2B • DAG 19 FLAGS',
    summary:
      'Configuración granular de los 19 módulos funcionales por empresa con arquetipos en 1 clic (ISP, Corporativo, Mínimo, Contingencia), grafo DAG y reversión histórica.',
    keyActions: [
      {
        title: 'Aplicar Arquetipo B2B o Modo Contingencia',
        description:
          'Activa perfiles preconfigurados para ISP/WISP, Redes Corporativas o apaga colectores intensivos en Modo Contingencia.',
      },
      {
        title: 'Restaurar Versión desde el Historial WORM',
        description:
          'En la pestaña Historial de Modificaciones, pulsa Cargar esta versión para revertir la matriz a un estado anterior.',
      },
    ],
    safetyAndGovernance: [
      'Escudo de Radio de Impacto antes de desactivar flags críticas (syslog_collector_enabled, enforce_maker_checker, auto_safemode_enforced).',
      'Solo SUPERADMIN_GLOBAL puede mutar el licenciamiento de módulos (HTTP 403 para roles inferiores).',
    ],
    mikrotikV7Notes: [
      'El grafo DAG bloquea automáticamente submódulos dependientes si su módulo padre es deshabilitado.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL'],
  },
  enterprise: {
    routeKey: 'enterprise',
    title: 'Cumplimiento CIS Benchmark (28 Directivas), Config Drift y CAPsMAN Wi-Fi v7',
    moduleBadge: 'CIBERSEGURIDAD & WI-FI V7 • FLOTA',
    summary:
      'Auditoría interactiva de 28 directivas CIS (ISP + Corporativo) con auto-remediación Safe Mode 60s, detección de Config Drift, Rogue DHCP, SLA y consola CAPsMAN Wi-Fi v7.',
    keyActions: [
      {
        title: 'Auditar y Auto-Remediar 28 Directivas CIS Benchmark',
        description:
          'Filtra por perfil (ISP, Empresa, Todos), activa/desactiva reglas y ejecuta Auto-Remediar bajo Safe Mode de 60s.',
      },
      {
        title: 'Operar Consola Interactiva CAPsMAN Wi-Fi v7 (Hito 27.13)',
        description:
          'Crea SSIDs con Datapath VLAN automático, perfiles WPA2/WPA3, reglas de aprovisionamiento por banda, Quick Setup y Kick Client.',
      },
      {
        title: 'Verificar Config Drift y Rogue DHCP',
        description:
          'Compara la configuración actual contra el Golden Baseline y detecta servidores DHCP no autorizados en la LAN.',
      },
    ],
    safetyAndGovernance: [
      'Eliminación protegida de SSIDs: retorna HTTP 409 Conflict si la configuración está en uso por una regla activa de provisioning.',
      'Todas las operaciones CAPsMAN y remediaciones CIS quedan firmadas en la bitácora WORM.',
    ],
    mikrotikV7Notes: [
      'Soporte bimodal para /rest/interface/wifi/capsman (RouterOS v7.13+ wifi-qcom) y /rest/caps-man/manager.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'AUDITOR'],
  },
  'fleet-cves': {
    routeKey: 'fleet-cves',
    title: 'Matriz de Vulnerabilidades CVE y Estado de Firmware RouterOS',
    moduleBadge: 'GESTIÓN DE VULNERABILIDADES • CVE',
    summary:
      'Cruce automatizado entre la versión de RouterOS v7 instalada en cada equipo y el catálogo de avisos de seguridad CVE sin depender de nubes externas.',
    keyActions: [
      {
        title: 'Identificar Equipos Expuestos por Severidad',
        description:
          'Filtra routers afectados por vulnerabilidades Críticas o Altas y verifica la versión mínima corregida.',
      },
      {
        title: 'Programar Actualización desde Operaciones Masivas',
        description:
          'Pasa los equipos vulnerables al orquestador de actualizaciones PoE-Aware.',
      },
    ],
    safetyAndGovernance: [
      'Evaluación 100% local y determinista (Zero-External-Cloud) para preservar la privacidad de la topología.',
    ],
    mikrotikV7Notes: [
      'Compara el campo version de /rest/system/resource y current-firmware de /rest/system/routerboard.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'AUDITOR'],
  },
  'audit-logs': {
    routeKey: 'audit-logs',
    title: 'Consola Forense Inmutable WORM (Cadena HMAC-SHA256)',
    moduleBadge: 'AUDITORÍA FORENSE • WORM',
    summary:
      'Registro inmutable de solo adición (Write-Once-Read-Many) en PostgreSQL 17 protegido por triggers a nivel de motor e índices BRIN.',
    keyActions: [
      {
        title: 'Auditar Acciones por Usuario, Router o Tipo de Evento',
        description:
          'Filtra mutaciones WebFig, revelaciones de bóveda, cambios de Feature Flags y expiraciones de mantenimiento.',
      },
      {
        title: 'Verificar Integridad Criptográfica de la Cadena',
        description:
          'Comprueba que cada eslabón preserve la firma HMAC-SHA256 enlazada al registro anterior (previous_hash -> entry_hash).',
      },
    ],
    safetyAndGovernance: [
      'Los triggers de PostgreSQL bloquean cualquier instrucción UPDATE, DELETE o TRUNCATE sobre audit_logs incluso para el superusuario.',
    ],
    mikrotikV7Notes: [
      'Correlaciona el comando exacto enviado a /rest/* con la identidad del operador o agente MCP.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'AUDITOR'],
  },
  'webfig-dashboard': {
    routeKey: 'webfig-dashboard',
    title: 'WebFig v7: Dashboard en Vivo y Telemetría RingBuffer',
    moduleBadge: 'WEBFIG CAPA 1 • TELEMETRÍA EN VIVO',
    summary:
      'Panel en tiempo real del router activo con gráficas a 60 FPS respaldadas por Float32Array circular en RAM (useTelemetryRingBuffer).',
    keyActions: [
      {
        title: 'Monitorear CPU, Memoria Libre, Temperatura y Tráfico TX/RX',
        description:
          'Observa el comportamiento instantáneo del equipo a través del canal WebSocket dedicado.',
      },
      {
        title: 'Conmutar entre Routers o Activar Safe Mode',
        description:
          'Usa el selector superior para cambiar de equipo o armar manualmente el Safe Mode de 60 segundos.',
      },
    ],
    safetyAndGovernance: [
      'Las pestañas WebFig utilizan <KeepAlive :max="5"> para conservar el estado en RAM al cambiar de módulo.',
    ],
    mikrotikV7Notes: [
      'Consume /rest/system/resource, /rest/system/health y /rest/interface en intervalos ligeros no bloqueantes.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2', 'SUPPORT_L1'],
  },
  'webfig-interfaces': {
    routeKey: 'webfig-interfaces',
    title: 'WebFig v7: Interfaces, Subinterfaces VLAN 802.1Q y Óptica SFP+ DDM',
    moduleBadge: 'WEBFIG CAPA 1 • INTERFACES & SFP+',
    summary:
      'Gestión CRUD completa de interfaces físicas/lógicas, creación y edición de VLANs 802.1Q y diagnóstico óptico Digital Diagnostic Monitoring (DDM).',
    keyActions: [
      {
        title: 'Editar MTU, Comentario o Estado de Interfaz',
        description:
          'Habilita, deshabilita o ajusta parámetros de cualquier interfaz con protección anti-bloqueo en el puerto de gestión.',
      },
      {
        title: 'Crear, Editar o Eliminar VLANs 802.1Q',
        description:
          'Administra subinterfaces en /interface/vlan especificando vlan-id (1–4094) e interfaz troncal.',
      },
      {
        title: 'Diagnosticar Potencia Óptica SFP/SFP+ (TX/RX dBm)',
        description:
          'Verifica niveles de luz en transceptores de fibra, temperatura del láser y alertas de atenuación.',
      },
    ],
    safetyAndGovernance: [
      'Toda modificación sobre interfaces se ejecuta bajo el paraguas del Dead Man’s Switch (Safe Mode 60s).',
    ],
    mikrotikV7Notes: [
      'Opera sobre /rest/interface, /rest/interface/vlan y /rest/interface/ethernet/monitor.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2'],
  },
  'webfig-bridge': {
    routeKey: 'webfig-bridge',
    title: 'WebFig v7: Gestor Bridge, Liberación de Puertos y VLAN Filtering',
    moduleBadge: 'WEBFIG CAPA 1 • SWITCHING CAPA 2',
    summary:
      'Administración integral de puentes L2 (/interface/bridge), asignación y liberación de puertos miembro en 1 clic, tabla de VLANs y tabla MAC (FDB).',
    keyActions: [
      {
        title: 'Crear, Editar y Eliminar Bridges',
        description:
          'Configura bridges con protocolo RSTP/MSTP, vlan-filtering y dhcp-snooping.',
      },
      {
        title: 'Asignar, Editar PVID o Sacar Puertos del Bridge',
        description:
          'Usa el botón [ ⏏ Sacar del Bridge ] para liberar cualquier interfaz miembro sin recrear el bridge.',
      },
      {
        title: 'Gestionar Bridge VLANs e Inspeccionar Hosts MAC',
        description:
          'Configura puertos tagged/untagged en /interface/bridge/vlan y consulta la tabla FDB en vivo.',
      },
    ],
    safetyAndGovernance: [
      'Liberar el puerto de administración o activar vlan-filtering arma obligatoriamente el Safe Mode de 60 segundos.',
    ],
    mikrotikV7Notes: [
      'Opera sobre /rest/interface/bridge, /rest/interface/bridge/port, /rest/interface/bridge/vlan y /rest/interface/bridge/host.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2'],
  },
  'webfig-wireguard': {
    routeKey: 'webfig-wireguard',
    title: 'WebFig v7: Túneles Criptográficos WireGuard y Peers',
    moduleBadge: 'WEBFIG CAPA 1 • VPN WIREGUARD',
    summary:
      'Ciclo de vida CRUD completo para interfaces WireGuard (/interface/wireguard) y Peers remotos (/interface/wireguard/peers) con generación de llaves en RouterOS v7.',
    keyActions: [
      {
        title: 'Crear, Editar o Eliminar Interfaces WireGuard',
        description:
          'Define listen-port y MTU; RouterOS v7 genera automáticamente el par de llaves Curve25519.',
      },
      {
        title: 'Gestionar Peers Criptográficos',
        description:
          'Configura public-key, allowed-address, endpoint-address, persistent-keepalive y preshared-key.',
      },
    ],
    safetyAndGovernance: [
      'Las llaves privadas nunca se exponen en texto plano salvo solicitud explícita autorizada.',
    ],
    mikrotikV7Notes: [
      'Opera directamente sobre /rest/interface/wireguard y /rest/interface/wireguard/peers (nativo desde RouterOS v7.1+).',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2'],
  },
  'webfig-ip': {
    routeKey: 'webfig-ip',
    title: 'WebFig v7: Direccionamiento IPv4, DHCP Server/Client, Pools, DNS y ARP',
    moduleBadge: 'WEBFIG CAPA 1 • PILA IP & DHCPV4',
    summary:
      'Siete pestañas tácticas con paridad CRUD total: Direcciones IP, Servidor DHCP (con Wizard en 3 pasos), Redes DHCP, Cliente DHCP WAN, Pools IP, DNS Singleton/Estático y ARP.',
    keyActions: [
      {
        title: 'Asistente DHCP Setup en 3 Pasos y Gestión de Leases',
        description:
          'Aprovisiona Pool, Red y Servidor DHCP automáticamente; convierte concesiones en estáticas (Make Static) o bloquea intrusos.',
      },
      {
        title: 'Editar Redes DHCP, Clientes WAN y Pools IP',
        description:
          'Modifica gateway/dns-server en /ip/dhcp-server/network, opciones de cliente WAN y rangos en /ip/pool.',
      },
      {
        title: 'Configurar DNS Global (/ip/dns/set) y Registros Estáticos',
        description:
          'Edita servidores upstream, controla allow-remote-requests, vacía la caché DNS y gestiona registros A/AAAA/CNAME.',
      },
    ],
    safetyAndGovernance: [
      'Protección anti-suicidio: impide eliminar por accidente la dirección IP utilizada por RoSGrid para administrar el router.',
    ],
    mikrotikV7Notes: [
      'El menú singleton /ip/dns se actualiza mediante POST /rest/ip/dns/set conforme a la especificación oficial de RouterOS v7.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2'],
  },
  'webfig-ipv6': {
    routeKey: 'webfig-ipv6',
    title: 'WebFig v7: Pila Dual IPv6 (SLAAC, EUI-64, DHCPv6-PD, Pools y NDP)',
    moduleBadge: 'WEBFIG CAPA 1 • DUAL-STACK IPV6',
    summary:
      'Despliegue y edición completa de IPv6 nativo: direcciones /ipv6/address, cliente DHCPv6 con Prefix Delegation, servidor DHCPv6, pools IPv6 y tabla de vecinos NDP.',
    keyActions: [
      {
        title: 'Asignar Direcciones IPv6 con SLAAC y EUI-64',
        description:
          'Crea o edita direcciones IPv6 directamente o tomando prefijos dinámicos desde un pool delegado.',
      },
      {
        title: 'Configurar DHCPv6 Client (PD) y DHCPv6 Server',
        description:
          'Solicita prefijos al carrier en la WAN, inyéctalos en un pool local y entrégalos a clientes o CPEs.',
      },
    ],
    safetyAndGovernance: [
      'Preserva las reglas esenciales ICMPv6 requeridas por RFC 4890 para Neighbor Discovery y Path MTU Discovery.',
    ],
    mikrotikV7Notes: [
      'Opera sobre /rest/ipv6/address, /rest/ipv6/dhcp-client, /rest/ipv6/dhcp-server, /rest/ipv6/pool y /rest/ipv6/neighbor.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2'],
  },
  'webfig-firewall': {
    routeKey: 'webfig-firewall',
    title: 'WebFig v7: Firewall (Filter, NAT, Mangle, RAW, Address-Lists) y Wizards NAT',
    moduleBadge: 'WEBFIG CAPA 1 • FIREWALL & NAT',
    summary:
      'Control de reglas IPv4/IPv6 con posicionamiento determinista (place-before), edición de Address-Lists y asistentes en 1 clic para Masquerade y Port Forwarding.',
    keyActions: [
      {
        title: 'Crear, Editar, Duplicar y Reordenar Reglas',
        description:
          'Administra las tablas Filter, NAT, Mangle y RAW manteniendo el orden exacto de evaluación de paquetes.',
      },
      {
        title: 'Asistentes Visuales NAT (Masquerade & Port Forwarding)',
        description:
          'Configura salida a Internet o publica servicios internos (dst-nat + regla forward opcional) en segundos.',
      },
      {
        title: 'Gestionar Listas de Direcciones (Address-Lists)',
        description:
          'Crea, edita o elimina entradas en /ip/firewall/address-list con soporte para listas dinámicas y timeouts.',
      },
    ],
    safetyAndGovernance: [
      'Las reglas drop/reject en la cadena input fuerzan Safe Mode de 60s y pasan por Maker-Checker (HTTP 202) para operadores N2.',
    ],
    mikrotikV7Notes: [
      'Utiliza /rest/ip/firewall/filter, /rest/ip/firewall/nat, /rest/ip/firewall/mangle, /rest/ip/firewall/raw y /rest/ip/firewall/address-list.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2'],
  },
  'webfig-routing': {
    routeKey: 'webfig-routing',
    title: 'WebFig v7: Rutas Estáticas ECMP, BGP v7, OSPF y Policy-Based Routing (PBR)',
    moduleBadge: 'WEBFIG CAPA 1 • ROUTING DINÁMICO V7',
    summary:
      'Administración de rutas IPv4/IPv6 con failover check-gateway, sesiones y conexiones BGP v7, vecinos OSPF y tablas/reglas PBR.',
    keyActions: [
      {
        title: 'Crear y Editar Rutas Estáticas y Balanceo ECMP',
        description:
          'Define dst-address, gateway, distance, routing-table y monitoreo por ping o arp.',
      },
      {
        title: 'Operar Conexiones BGP v7 y Soft Reset',
        description:
          'Administra /routing/bgp/connection, templates y ejecuta refresco suave de prefijos sin tumbar la sesión.',
      },
      {
        title: 'Configurar Tablas FIB y Reglas PBR',
        description:
          'Crea tablas en /routing/table y reglas de política en /routing/rule para dirigir tráfico por múltiples WANs.',
      },
    ],
    safetyAndGovernance: [
      'Mutaciones en BGP o rutas por defecto (0.0.0.0/0) están protegidas por Safe Mode de 60s y Maker-Checker para roles N2.',
    ],
    mikrotikV7Notes: [
      'Alineado 100% con el motor de ruteo reescrito en RouterOS v7 (/rest/routing/bgp/connection, /rest/routing/ospf/neighbor, /rest/routing/table).',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2'],
  },
  'webfig-ppp': {
    routeKey: 'webfig-ppp',
    title: 'WebFig v7: Abonados PPPoE (Active, Secrets, Profiles, Servers) y Colas QoS',
    moduleBadge: 'WEBFIG CAPA 1 • PPPOE & QOS',
    summary:
      'Soporte N1/N2/N3 para desconexión rápida de sesiones PPPoE (Kick Session), CRUD completo de secretos, perfiles y concentradores PPPoE, y Simple Queues con presets.',
    keyActions: [
      {
        title: 'Reconectar Abonado en 1 Clic (Kick Session)',
        description:
          'En la pestaña Sesiones Activas, pulsa [ ⏏ Desconectar ] para forzar la renegociación inmediata del CPE.',
      },
      {
        title: 'Crear, Editar y Eliminar Secretos, Perfiles y Servidores PPPoE',
        description:
          'Administra credenciales de suscriptores (/ppp/secret), planes (/ppp/profile) y concentradores (/interface/pppoe-server/server).',
      },
      {
        title: 'Configurar Simple Queues con Presets (10M a 1 Gbps)',
        description:
          'Aplica límites de ancho de banda simétricos o asimétricos y jerarquías Parent Queue con semáforo de saturación.',
      },
    ],
    safetyAndGovernance: [
      'Los operadores SUPPORT_L1 pueden reconectar sesiones PPPoE sin tener acceso para borrar secretos ni alterar el firewall.',
    ],
    mikrotikV7Notes: [
      'Opera sobre /rest/ppp/active, /rest/ppp/secret, /rest/ppp/profile, /rest/interface/pppoe-server/server y /rest/queue/simple.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2', 'SUPPORT_L1'],
  },
  'webfig-tools': {
    routeKey: 'webfig-tools',
    title: 'WebFig v7: Herramientas de Diagnóstico en Vivo (Ping, Traceroute, Torch)',
    moduleBadge: 'WEBFIG CAPA 1 • DIAGNÓSTICO EN VIVO',
    summary:
      'Ejecución acotada de herramientas de red directamente desde el router seleccionado sin necesidad de abrir sesiones SSH ni WinBox.',
    keyActions: [
      {
        title: 'Ejecutar Ping Acotado y Prueba de MTU',
        description:
          'Lanza ráfagas ICMP hacia cualquier IP o dominio especificando interfaz de origen, tamaño de paquete y conteo.',
      },
      {
        title: 'Trazar Ruta (Traceroute) e Inspeccionar Tráfico',
        description:
          'Identifica saltos con latencia elevada o pérdida de paquetes en el camino hacia el destino.',
      },
    ],
    safetyAndGovernance: [
      'Todas las herramientas tienen un límite máximo de paquetes/duración para evitar que un comando infinito consuma CPU en el router.',
    ],
    mikrotikV7Notes: [
      'Invoca POST /rest/tool/ping y POST /rest/tool/traceroute con parámetros validados contra inyección.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2', 'SUPPORT_L1', 'FIELD_TECH'],
  },
  'webfig-syslog': {
    routeKey: 'webfig-syslog',
    title: 'WebFig v7: Terminal Syslog en Vivo del Router',
    moduleBadge: 'WEBFIG CAPA 1 • SYSLOG LIVE',
    summary:
      'Consola de eventos en tiempo real del router activo con filtrado por severidad, tópico (system, firewall, account, bgp, wireless) y búsqueda instantánea.',
    keyActions: [
      {
        title: 'Filtrar Eventos por Tópico o Palabra Clave',
        description:
          'Aísla rápidamente intentos de login, cambios de configuración o bloqueos de firewall.',
      },
      {
        title: 'Pausar / Reanudar el Flujo en Vivo',
        description:
          'Congela la ventana para copiar líneas de diagnóstico sin perder eventos entrantes en el buffer.',
      },
    ],
    safetyAndGovernance: [
      'Combina el buffer local /rest/log del equipo con el stream UDP 5514 recibido por el colector de RoSGrid.',
    ],
    mikrotikV7Notes: [
      'Reconoce automáticamente los 9 tópicos configurados por la plantilla oficial rosgridsyslog en /system/logging.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2', 'SUPPORT_L1', 'AUDITOR'],
  },
  'webfig-layer2': {
    routeKey: 'webfig-layer2',
    title: 'WebFig v7: Motor Universal Capa 2 (/rest/*) con Vista Compacta Responsiva',
    moduleBadge: 'WEBFIG CAPA 2 • MOTOR UNIVERSAL /REST/*',
    summary:
      'Inspector y editor dinámico capaz de renderizar formularios Singleton o tablas de colección para cualquier submenú de RouterOS v7 (ej. /certificate, /ip/service, /snmp).',
    keyActions: [
      {
        title: 'Alternar Vista Compacta (8 cols) y Selector de Columnas',
        description:
          'En menús anchos de 30+ atributos (como /certificate), usa [ 📐 Vista Compacta ] o [ ⚙️ Columnas ] para evitar desbordamiento.',
      },
      {
        title: 'Buscar, Crear, Editar o Eliminar Registros Dinámicos',
        description:
          'Filtra en tiempo real con el buscador superior y edita cualquier atributo en el modal responsivo de 2 columnas.',
      },
      {
        title: 'Actualizar Menús Singleton (POST /set)',
        description:
          'En submenús de instancia única (/ip/cloud, /system/ntp/client), guarda cambios directamente con Safe Mode de 60s.',
      },
    ],
    safetyAndGovernance: [
      'Lista negra de rutas peligrosas bloqueada en backend y protección Safe Mode de 60s activa por defecto en toda escritura.',
    ],
    mikrotikV7Notes: [
      'Infiere dinámicamente tipos boolean_ros, integer, ip_cidr y read-only a partir de la respuesta nativa de /rest/<path>.',
    ],
    relatedRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SUPERVISOR', 'SUPPORT_L3', 'SUPPORT_L2'],
  },
};

export const CONTEXTUAL_HELP_LIST: ContextualHelpEntry[] = Object.values(CONTEXTUAL_HELP_CATALOG);

const ROUTE_NAME_TO_HELP_KEY: Record<string, string> = {
  DashboardRoot: 'dashboard',
  RouterInventory: 'inventory',
  NocWallboard: 'wallboard',
  ApprovalsInbox: 'approvals',
  IpamManagement: 'ipam',
  SubscribersMap: 'subscribers-map',
  FieldTechOperations: 'field-tech',
  L2Topology: 'topology-l2',
  RscGitDiff: 'backups-diff',
  RouterBackupsGitDiff: 'backups-diff',
  BulkOperations: 'bulk-ops',
  MaintenanceWindows: 'maintenance',
  UsersAndPermissions: 'users-rbac',
  ActiveSessionsKillSwitch: 'sessions',
  TenantsManagement: 'tenants',
  TenantModulesStudio: 'tenant-modules',
  EnterpriseCompliance: 'enterprise',
  FleetCveMatrix: 'fleet-cves',
  ImmutableAuditLogs: 'audit-logs',
  RouterLiveDashboard: 'webfig-dashboard',
  InterfacesAndSfp: 'webfig-interfaces',
  BridgeSwitching: 'webfig-bridge',
  WireGuardVpn: 'webfig-wireguard',
  IpAddressesAndDhcp: 'webfig-ip',
  Ipv6DualStack: 'webfig-ipv6',
  FirewallRules: 'webfig-firewall',
  RoutingBgpOspf: 'webfig-routing',
  PppAndQueues: 'webfig-ppp',
  LiveToolsDiagnostics: 'webfig-tools',
  RouterSyslogLive: 'webfig-syslog',
  DynamicLayer2Resource: 'webfig-layer2',
};

const PATH_SUBSTRING_RULES: ReadonlyArray<readonly [string, string]> = [
  ['/webfig/interfaces', 'webfig-interfaces'],
  ['/webfig/bridge', 'webfig-bridge'],
  ['/webfig/wireguard', 'webfig-wireguard'],
  ['/webfig/ipv6', 'webfig-ipv6'],
  ['/webfig/ip', 'webfig-ip'],
  ['/webfig/firewall', 'webfig-firewall'],
  ['/webfig/routing', 'webfig-routing'],
  ['/webfig/ppp', 'webfig-ppp'],
  ['/webfig/tools', 'webfig-tools'],
  ['/webfig/syslog', 'webfig-syslog'],
  ['/webfig/layer2', 'webfig-layer2'],
  ['/webfig/backups', 'backups-diff'],
  ['/webfig', 'webfig-dashboard'],
  ['/inventory/cves', 'fleet-cves'],
  ['/fleet/cve', 'fleet-cves'],
  ['/maintenance-windows', 'maintenance'],
  ['/inventory', 'inventory'],
  ['/noc-wallboard', 'wallboard'],
  ['/approvals', 'approvals'],
  ['/ipam', 'ipam'],
  ['/subscribers/map', 'subscribers-map'],
  ['/field-ops', 'field-tech'],
  ['/topology', 'topology-l2'],
  ['/backups', 'backups-diff'],
  ['/bulk-ops', 'bulk-ops'],
  ['/users', 'users-rbac'],
  ['/sessions', 'sessions'],
  ['/active-sessions', 'sessions'],
  ['/modules', 'tenant-modules'],
  ['/admin/tenants', 'tenants'],
  ['/compliance', 'enterprise'],
  ['/audit', 'audit-logs'],
];

export const HELP_CATALOG = CONTEXTUAL_HELP_CATALOG;
export const HELP_CATALOG_LIST: ContextualHelpEntry[] = Object.values(CONTEXTUAL_HELP_CATALOG);

export function resolveHelpKeyFromRoute(
  routePath?: string,
  routeName?: string | symbol | null,
): string {
  if (routeName && typeof routeName === 'string' && ROUTE_NAME_TO_HELP_KEY[routeName]) {
    return ROUTE_NAME_TO_HELP_KEY[routeName];
  }

  const normalizedPath = (routePath || '/').toLowerCase();
  for (const [pattern, helpKey] of PATH_SUBSTRING_RULES) {
    if (normalizedPath.includes(pattern)) {
      return helpKey;
    }
  }

  return 'dashboard';
}

export function getHelpEntryByKey(key: string): ContextualHelpEntry {
  if (CONTEXTUAL_HELP_CATALOG[key]) {
    return CONTEXTUAL_HELP_CATALOG[key];
  }
  const mappedKey = ROUTE_NAME_TO_HELP_KEY[key];
  if (mappedKey && CONTEXTUAL_HELP_CATALOG[mappedKey]) {
    return CONTEXTUAL_HELP_CATALOG[mappedKey];
  }
  return CONTEXTUAL_HELP_CATALOG.dashboard;
}

export function formatHelpEntryAsMarkdown(entry: ContextualHelpEntry): string {
  const actionsMd = entry.keyActions
    .map((step, idx) => `${idx + 1}. **${step.title}:** ${step.description}`)
    .join('\n');
  const safetyMd = entry.safetyAndGovernance.map((item) => `- ${item}`).join('\n');
  const rosMd = entry.mikrotikV7Notes.map((item) => `- ${item}`).join('\n');

  return [
    `# ${entry.title}`,
    `> **Módulo:** \`${entry.moduleBadge}\` | **Clave de Ruta:** \`${entry.routeKey}\``,
    '',
    '## Resumen Operativo',
    entry.summary,
    '',
    '## Acciones Clave Paso a Paso',
    actionsMd,
    '',
    '## Gobernanza, Safe Mode (60s) y Seguridad Zero-Trust',
    safetyMd,
    '',
    '## Notas Técnicas MikroTik RouterOS v7 (/rest/*)',
    rosMd,
    '',
    '## Roles RBAC Autorizados',
    entry.relatedRoles.map((r) => `\`${r}\``).join(', '),
    '',
  ].join('\n');
}
