// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

/**
 * Módulo de Formateo Descriptivo Bilingüe (ES/EN) de Eventos y Auditoría WORM para RoSGrid.
 * Mapea códigos internos inmutables almacenados en la base de datos (ej. LOGIN_FAILED_USER_INACTIVE)
 * a descripciones claras, legibles y comprensibles para operadores del NOC y usuarios finales.
 */

const EVENT_ACTION_DESCRIPTIONS_ES: Record<string, string> = {
  // Autenticación, Sesiones y Seguridad de Cuenta
  LOGIN_FAILED_USER_INACTIVE: 'Acceso denegado: Usuario inactivo o deshabilitado',
  LOGIN_FAILED_INVALID_PASSWORD: 'Acceso denegado: Contraseña incorrecta',
  LOGIN_FAILED_USER_NOT_FOUND: 'Acceso denegado: Usuario no registrado',
  LOGIN_FAILED_ACCOUNT_LOCKED: 'Acceso bloqueado: Cuenta suspendida preventivamente',
  LOGIN_SUCCESSFUL: 'Inicio de sesión exitoso',
  LOGOUT_SUCCESSFUL: 'Cierre de sesión exitoso',
  SESSION_TOKEN_RENEWED: 'Sesión de operador renovada',
  '2FA_VERIFICATION_FAILED': 'Fallo en verificación de segundo factor (2FA)',
  SESSION_KILLED_DUPLICATE_LOGIN: 'Sesión finalizada por ingreso concurrente',
  PASSWORD_CHANGED: 'Contraseña de usuario actualizada',
  USER_REGISTERED: 'Nuevo usuario registrado pendiente de aprobación',
  USER_APPROVED: 'Cuenta de usuario aprobada y activada',
  USER_REJECTED: 'Solicitud de registro de usuario rechazada',

  // Caídas, Disponibilidad y Alertas Masivas (docs/specs/32)
  MASS_OUTAGE_TRIGGERED: 'Alerta de caída masiva activada',
  MASS_OUTAGE_DETECTED: 'Caída masiva detectada en la red',
  ROUTER_DOWN: 'Router fuera de línea (sin respuesta)',
  ROUTER_UP: 'Router restablecido y operativo',
  ROUTER_REBOOT_TRIGGERED: 'Reinicio remoto de equipo ejecutado',
  HIGH_CPU: 'Alerta de consumo elevado de CPU',
  SSL_MISMATCH: 'Discrepancia en huella criptográfica SSL (TOFU)',
  MAINTENANCE: 'Ventana de mantenimiento programada',
  MAINTENANCE_WINDOW_CREATED: 'Ventana de mantenimiento creada',
  MAINTENANCE_WINDOW_CANCELLED: 'Ventana de mantenimiento cancelada',
  MAINTENANCE_WINDOW_EXPIRED_AUTO_DELETED: 'Ventana de mantenimiento finalizada',

  // Bóveda de Credenciales y Criptografía
  CREDENTIAL_REVEALED: 'Credenciales de acceso reveladas en bóveda',
  CREDENTIAL_AUTO_ROTATED: 'Rotación automática de credenciales completada',
  VAULT_ROTATION_AUTOMATED: 'Rotación programada de bóveda completada',

  // Inventario y Gestión de Equipos
  ROUTER_CREATED: 'Nuevo router dado de alta en inventario',
  ROUTER_UPDATED: 'Parámetros de router actualizados en inventario',
  ROUTER_DELETED: 'Router eliminado del inventario',
  ROUTER_SSL_REPINNED: 'Certificado TLS re-fijado (TOFU)',
  ROUTER_IMPORT_CSV_COMMITTED: 'Importación masiva CSV procesada con éxito',
  CUSTOM_NETWORK_ROLE_CREATED: 'Nuevo rol de red táctico creado',
  CUSTOM_NETWORK_ROLE_DELETED: 'Rol de red táctico eliminado',
  ROUTER_BACKUP_CREATED: 'Respaldo de configuración generado',
  SYSTEM_IDENTITY_UPDATED: 'Identidad del router actualizada en RouterOS',

  // Seguridad, Mitigación y Cumplimiento
  AUTO_HARDEN_ROUTER: 'Fortalecimiento de seguridad aplicado',
  REVERT_TO_GOLDEN_BASELINE: 'Configuración revertida a línea base segura',
  ENABLE_DHCP_SNOOPING: 'DHCP Snooping habilitado en switch',
  ISOLATE_SWITCH_PORT: 'Aislamiento preventivo de puerto de switch',
  TRAFFIC_ANOMALY_MITIGATED: 'Anomalía de tráfico mitigada',
  DIAGNOSTIC_SUPPORT_BUNDLE_GENERATED: 'Paquete de soporte y diagnóstico generado',
  SIEM_CONFIG_UPDATED: 'Configuración de conector SIEM actualizada',

  // Aprobaciones y Gobernanza Maker-Checker
  MAKER_CHECKER_REJECTED: 'Solicitud rechazada por aprobador',
  MAKER_CHECKER_REQUESTED: 'Solicitud de cambio enviada para aprobación',
  MAKER_CHECKER_APPROVED: 'Solicitud de cambio aprobada y ejecutada',
  MAKER_CHECKER_RESOLVED: 'Solicitud Maker-Checker procesada',

  // Plantillas de Configuración y Capa 2
  CONFIG_TEMPLATE_CREATED: 'Plantilla de configuración creada',
  CONFIG_TEMPLATE_UPDATED: 'Plantilla de configuración actualizada',
  CONFIG_TEMPLATE_DELETED: 'Plantilla de configuración eliminada',
  L2_RESOURCE_CREATED: 'Recurso de Capa 2 aprovisionado',

  // Operaciones de Campo (Field Ops)
  FIELD_ORDER_CREATED: 'Orden de trabajo de campo generada',
  FIELD_INSTALLATION_CERTIFIED: 'Instalación en sitio certificada',

  // Servicios, Enrutamiento e IPAM
  IPAM_VRF_CREATED: 'Dominio de enrutamiento VRF creado',
  IPAM_PREFIX_CREATED: 'Prefijo IP asignado',
  CUSTOMER_SERVICE_CREATED: 'Servicio a cliente aprovisionado',
  CREATE_BANDWIDTH_PROFILE: 'Perfil de ancho de banda creado',
  UPDATE_BANDWIDTH_PROFILE: 'Perfil de ancho de banda actualizado',
  CREATE_SUBSCRIBER_DEVICE: 'Dispositivo de abonado registrado',
  UPDATE_SUBSCRIBER_DEVICE: 'Dispositivo de abonado actualizado',
  NETWORK_SERVICE_ISOLATED: 'Servicio de red aislado',
  NETWORK_SERVICE_RESTORED: 'Servicio de red restablecido',
  NETWORK_SERVICE_RATE_LIMIT_CHANGED: 'Límite de tasa de transferencia modificado',
  PROVISION_SPOKE_WIREGUARD: 'Túnel SD-WAN WireGuard aprovisionado',
  DEPLOY_RECURSIVE_NETWATCH: 'Monitoreo recursivo Netwatch desplegado',
  TENANT_FEATURE_FLAGS_UPDATED: 'Parámetros del tenant actualizados',
  TENANT_ONBOARDING_COMPLETED: 'Configuración inicial de la organización completada',
};

const EVENT_ACTION_DESCRIPTIONS_EN: Record<string, string> = {
  // Authentication, Sessions & Account Security
  LOGIN_FAILED_USER_INACTIVE: 'Access denied: Inactive or disabled user',
  LOGIN_FAILED_INVALID_PASSWORD: 'Access denied: Invalid password',
  LOGIN_FAILED_USER_NOT_FOUND: 'Access denied: Unregistered user',
  LOGIN_FAILED_ACCOUNT_LOCKED: 'Access blocked: Account temporarily locked',
  LOGIN_SUCCESSFUL: 'Successful login',
  LOGOUT_SUCCESSFUL: 'Successful logout',
  SESSION_TOKEN_RENEWED: 'Operator session renewed',
  '2FA_VERIFICATION_FAILED': 'Two-factor authentication (2FA) verification failed',
  SESSION_KILLED_DUPLICATE_LOGIN: 'Session terminated due to concurrent login',
  PASSWORD_CHANGED: 'User password updated',
  USER_REGISTERED: 'New user registered pending approval',
  USER_APPROVED: 'User account approved and activated',
  USER_REJECTED: 'User registration request rejected',

  // Outages, Availability & Mass Alerts
  MASS_OUTAGE_TRIGGERED: 'Mass outage alert triggered',
  MASS_OUTAGE_DETECTED: 'Mass network outage detected',
  ROUTER_DOWN: 'Router offline (unreachable)',
  ROUTER_UP: 'Router restored and online',
  ROUTER_REBOOT_TRIGGERED: 'Remote router reboot executed',
  HIGH_CPU: 'High CPU load alert',
  SSL_MISMATCH: 'SSL cryptographic fingerprint mismatch (TOFU)',
  MAINTENANCE: 'Scheduled maintenance window',
  MAINTENANCE_WINDOW_CREATED: 'Maintenance window created',
  MAINTENANCE_WINDOW_CANCELLED: 'Maintenance window cancelled',
  MAINTENANCE_WINDOW_EXPIRED_AUTO_DELETED: 'Maintenance window completed',

  // Credential Vault & Cryptography
  CREDENTIAL_REVEALED: 'Router credentials revealed from vault',
  CREDENTIAL_AUTO_ROTATED: 'Automated credential rotation completed',
  VAULT_ROTATION_AUTOMATED: 'Scheduled vault rotation completed',

  // Inventory & Device Management
  ROUTER_CREATED: 'New router registered in inventory',
  ROUTER_UPDATED: 'Router parameters updated in inventory',
  ROUTER_DELETED: 'Router removed from inventory',
  ROUTER_SSL_REPINNED: 'TLS certificate re-pinned (TOFU)',
  ROUTER_IMPORT_CSV_COMMITTED: 'Bulk CSV import committed successfully',
  CUSTOM_NETWORK_ROLE_CREATED: 'New tactical network role created',
  CUSTOM_NETWORK_ROLE_DELETED: 'Tactical network role deleted',
  ROUTER_BACKUP_CREATED: 'Configuration backup generated',
  SYSTEM_IDENTITY_UPDATED: 'Router identity updated in RouterOS',

  // Security, Mitigation & Compliance
  AUTO_HARDEN_ROUTER: 'Security hardening applied',
  REVERT_TO_GOLDEN_BASELINE: 'Configuration reverted to golden baseline',
  ENABLE_DHCP_SNOOPING: 'DHCP Snooping enabled on switch',
  ISOLATE_SWITCH_PORT: 'Preventive switch port isolation applied',
  TRAFFIC_ANOMALY_MITIGATED: 'Traffic anomaly mitigated',
  DIAGNOSTIC_SUPPORT_BUNDLE_GENERATED: 'Diagnostic support bundle generated',
  SIEM_CONFIG_UPDATED: 'SIEM forwarder configuration updated',

  // Maker-Checker Approvals & Governance
  MAKER_CHECKER_REJECTED: 'Change request rejected by approver',
  MAKER_CHECKER_REQUESTED: 'Change request submitted for approval',
  MAKER_CHECKER_APPROVED: 'Change request approved and executed',
  MAKER_CHECKER_RESOLVED: 'Maker-Checker request resolved',

  // Configuration Templates & Layer 2
  CONFIG_TEMPLATE_CREATED: 'Configuration template created',
  CONFIG_TEMPLATE_UPDATED: 'Configuration template updated',
  CONFIG_TEMPLATE_DELETED: 'Configuration template deleted',
  L2_RESOURCE_CREATED: 'Layer 2 resource provisioned',

  // Field Operations
  FIELD_ORDER_CREATED: 'Field work order created',
  FIELD_INSTALLATION_CERTIFIED: 'On-site installation certified',

  // Services, Routing & IPAM
  IPAM_VRF_CREATED: 'VRF routing domain created',
  IPAM_PREFIX_CREATED: 'IP prefix allocated',
  CUSTOMER_SERVICE_CREATED: 'Subscriber service provisioned',
  CREATE_BANDWIDTH_PROFILE: 'Bandwidth profile created',
  UPDATE_BANDWIDTH_PROFILE: 'Bandwidth profile updated',
  CREATE_SUBSCRIBER_DEVICE: 'Subscriber device registered',
  UPDATE_SUBSCRIBER_DEVICE: 'Subscriber device updated',
  NETWORK_SERVICE_ISOLATED: 'Network service isolated',
  NETWORK_SERVICE_RESTORED: 'Network service restored',
  NETWORK_SERVICE_RATE_LIMIT_CHANGED: 'Bandwidth rate limit modified',
  PROVISION_SPOKE_WIREGUARD: 'SD-WAN WireGuard spoke provisioned',
  DEPLOY_RECURSIVE_NETWATCH: 'Recursive Netwatch monitoring deployed',
  TENANT_FEATURE_FLAGS_UPDATED: 'Tenant parameters updated',
  TENANT_ONBOARDING_COMPLETED: 'Organization initial onboarding completed',
};

const CATALOG_ES = new Map<string, string>(Object.entries(EVENT_ACTION_DESCRIPTIONS_ES));
const CATALOG_EN = new Map<string, string>(Object.entries(EVENT_ACTION_DESCRIPTIONS_EN));
const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function resolveActiveLocale(locale?: 'es' | 'en' | string | null): 'es' | 'en' {
  if (locale === 'en' || locale === 'es') return locale;
  try {
    if (typeof localStorage !== 'undefined') {
      const stored = localStorage.getItem('rg_locale') || localStorage.getItem('rosgrid_locale');
      if (stored === 'en') {
        return 'en';
      }
    }
  } catch {
    // Ignorar errores de acceso a localStorage
  }
  return 'es';
}

export function parseRawAuditString(
  input: string | null | undefined,
): { actionCode: string; extractedActor?: string } | null {
  if (!input || typeof input !== 'string') return null;
  const trimmed = input.trim();
  const openParen = trimmed.indexOf('(');
  const closeParen = trimmed.indexOf(')', openParen + 1);
  if (openParen <= 0 || closeParen <= openParen + 1) return null;

  const actionCode = trimmed.slice(0, openParen).trim();
  const category = trimmed.slice(openParen + 1, closeParen).trim();
  if (!/^[A-Z0-9_]+$/.test(actionCode) || !/^[A-Z0-9_]+$/.test(category)) {
    return null;
  }

  const remainder = trimmed.slice(closeParen + 1).trim();
  if (!remainder) {
    return { actionCode };
  }
  if (remainder.startsWith(':')) {
    const actor = remainder.slice(1).trim();
    return { actionCode, extractedActor: actor || undefined };
  }
  return null;
}

/**
 * Transforma un código de acción interno de la base de datos a un texto descriptivo en el idioma activo (ES/EN).
 * Si el código no está en el catálogo, realiza una conversión amigable sustituyendo guiones bajos.
 */
export function formatEventAction(
  action: string | null | undefined,
  locale?: 'es' | 'en' | string | null,
): string {
  const lang = resolveActiveLocale(locale);
  if (!action || typeof action !== 'string' || !action.trim()) {
    return lang === 'en' ? 'System operation' : 'Operación del sistema';
  }

  const parsed = parseRawAuditString(action);
  const trimmed = parsed ? parsed.actionCode : action.trim();
  const catalog = lang === 'en' ? CATALOG_EN : CATALOG_ES;
  const matched = catalog.get(trimmed);

  if (matched) {
    return matched;
  }

  // Si ya es una frase humana (contiene espacios y minúsculas), devolverla tal cual
  if (trimmed.includes(' ') && /[a-záéíóúñ]/.test(trimmed)) {
    return trimmed;
  }

  // Fallback amigable: transformar SCREAMING_SNAKE_CASE a Texto legible
  const words = trimmed
    .toLowerCase()
    .split('_')
    .filter(Boolean);

  if (words.length === 0) return trimmed;
  const sentence = words.join(' ');
  return sentence.charAt(0).toUpperCase() + sentence.slice(1);
}

export function isRawUuid(val: string | null | undefined): boolean {
  if (!val || typeof val !== 'string') return false;
  return UUID_V4_REGEX.test(val.trim());
}

/**
 * Genera el mensaje descriptivo completo combinando la acción formateada y el actor en el idioma activo (ES/EN).
 */
export function formatEventMessage(
  action: string | null | undefined,
  actor?: string | null,
  locale?: 'es' | 'en' | string | null,
): string {
  const lang = resolveActiveLocale(locale);
  const parsed = parseRawAuditString(action);
  const effectiveAction = parsed ? parsed.actionCode : action;
  const effectiveActor = (actor || parsed?.extractedActor || '').trim();

  const actionText = formatEventAction(effectiveAction, lang);

  if (
    !effectiveActor ||
    effectiveActor.toLowerCase() === 'sistema' ||
    effectiveActor.toLowerCase() === 'system' ||
    effectiveActor.toLowerCase() === 'usuario' ||
    effectiveActor.toLowerCase() === 'user' ||
    isRawUuid(effectiveActor)
  ) {
    return actionText;
  }

  const prep = lang === 'en' ? 'by' : 'por';
  return `${actionText} (${prep} ${effectiveActor})`;
}
