// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

/**
 * Módulo de Formateo Descriptivo de Eventos y Auditoría WORM para RoSGrid.
 * Mapea códigos internos inmutables almacenados en la base de datos (ej. LOGIN_FAILED_USER_INACTIVE)
 * a descripciones claras, legibles y comprensibles para operadores del NOC y usuarios finales.
 */

const EVENT_ACTION_DESCRIPTIONS: Record<string, string> = {
  // Autenticación, Sesiones y Seguridad de Cuenta
  LOGIN_FAILED_USER_INACTIVE: 'Acceso denegado: Usuario inactivo o deshabilitado',
  LOGIN_FAILED_INVALID_PASSWORD: 'Acceso denegado: Contraseña incorrecta',
  LOGIN_FAILED_USER_NOT_FOUND: 'Acceso denegado: Usuario no registrado',
  LOGIN_FAILED_ACCOUNT_LOCKED: 'Acceso bloqueado: Cuenta suspendida preventivamente',
  LOGIN_SUCCESSFUL: 'Inicio de sesión exitoso',
  '2FA_VERIFICATION_FAILED': 'Fallo en verificación de segundo factor (2FA)',
  SESSION_KILLED_DUPLICATE_LOGIN: 'Sesión finalizada por ingreso concurrente',

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

  // Bóveda de Credenciales y Criptografía
  CREDENTIAL_REVEALED: 'Credenciales de acceso reveladas en bóveda',
  CREDENTIAL_AUTO_ROTATED: 'Rotación automática de credenciales completada',
  VAULT_ROTATION_AUTOMATED: 'Rotación programada de bóveda completada',

  // Inventario y Gestión de Equipos
  ROUTER_CREATED: 'Nuevo router dado de alta en inventario',
  ROUTER_SSL_REPINNED: 'Certificado TLS re-fijado (TOFU)',
  ROUTER_IMPORT_CSV_COMMITTED: 'Importación masiva CSV procesada con éxito',
  CUSTOM_NETWORK_ROLE_CREATED: 'Nuevo rol de red táctico creado',
  CUSTOM_NETWORK_ROLE_DELETED: 'Rol de red táctico eliminado',
  ROUTER_BACKUP_CREATED: 'Respaldo de configuración generado',

  // Seguridad, Mitigación y Cumplimiento
  AUTO_HARDEN_ROUTER: 'Fortalecimiento de seguridad aplicado',
  REVERT_TO_GOLDEN_BASELINE: 'Configuración revertida a línea base segura',
  ENABLE_DHCP_SNOOPING: 'DHCP Snooping habilitado en switch',
  ISOLATE_SWITCH_PORT: 'Aislamiento preventivo de puerto de switch',
  TRAFFIC_ANOMALY_MITIGATED: 'Anomalía de tráfico mitigada',

  // Aprobaciones y Gobernanza Maker-Checker
  MAKER_CHECKER_REJECTED: 'Solicitud rechazada por aprobador',
  MAKER_CHECKER_REQUESTED: 'Solicitud de cambio enviada para aprobación',
  MAKER_CHECKER_APPROVED: 'Solicitud de cambio aprobada y ejecutada',

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
};

/**
 * Transforma un código de acción interno de la base de datos a un texto descriptivo en español.
 * Si el código no está en el catálogo, realiza una conversión amigable sustituyendo guiones bajos.
 */
export function formatEventAction(action: string | null | undefined): string {
  if (!action || typeof action !== 'string') {
    return 'Operación del sistema';
  }

  const trimmed = action.trim();
  if (EVENT_ACTION_DESCRIPTIONS[trimmed]) {
    return EVENT_ACTION_DESCRIPTIONS[trimmed];
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

/**
 * Genera el mensaje descriptivo completo combinando la acción formateada y el actor.
 */
export function formatEventMessage(
  action: string | null | undefined,
  actor?: string | null,
): string {
  const actionText = formatEventAction(action);
  const normalizedActor = (actor || '').trim();

  if (!normalizedActor || normalizedActor.toLowerCase() === 'sistema' || normalizedActor.toLowerCase() === 'system') {
    return actionText;
  }

  return `${actionText} (por ${normalizedActor})`;
}
