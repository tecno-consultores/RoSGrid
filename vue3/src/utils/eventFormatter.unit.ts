// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect } from 'vitest';
import { formatEventAction, formatEventMessage, isRawUuid, parseRawAuditString } from './eventFormatter';

const ROUTER_DOWN_ES = 'Router fuera de línea (sin respuesta)';

describe('eventFormatter.ts — Transformación de códigos internos a texto descriptivo', () => {
  it('formatea LOGIN_FAILED_USER_INACTIVE a descripción en español amigable', () => {
    expect(formatEventAction('LOGIN_FAILED_USER_INACTIVE')).toBe(
      'Acceso denegado: Usuario inactivo o deshabilitado',
    );
  });

  it('formatea eventos críticos de autenticación y 2FA', () => {
    expect(formatEventAction('LOGIN_FAILED_INVALID_PASSWORD')).toBe(
      'Acceso denegado: Contraseña incorrecta',
    );
    expect(formatEventAction('LOGIN_FAILED_USER_NOT_FOUND')).toBe(
      'Acceso denegado: Usuario no registrado',
    );
    expect(formatEventAction('LOGIN_FAILED_ACCOUNT_LOCKED')).toBe(
      'Acceso bloqueado: Cuenta suspendida preventivamente',
    );
    expect(formatEventAction('LOGIN_SUCCESSFUL')).toBe('Inicio de sesión exitoso');
    expect(formatEventAction('2FA_VERIFICATION_FAILED')).toBe(
      'Fallo en verificación de segundo factor (2FA)',
    );
    expect(formatEventAction('SESSION_KILLED_DUPLICATE_LOGIN')).toBe(
      'Sesión finalizada por ingreso concurrente',
    );
  });

  it('formatea eventos de caída masiva, red y bóveda', () => {
    expect(formatEventAction('MASS_OUTAGE_TRIGGERED')).toBe(
      'Alerta de caída masiva activada',
    );
    expect(formatEventAction('ROUTER_DOWN')).toBe(ROUTER_DOWN_ES);
    expect(formatEventAction('CREDENTIAL_REVEALED')).toBe(
      'Credenciales de acceso reveladas en bóveda',
    );
    expect(formatEventAction('ROUTER_CREATED')).toBe(
      'Nuevo router dado de alta en inventario',
    );
  });

  it('aplica fallback legible cuando el evento no está en el catálogo', () => {
    expect(formatEventAction('UNKNOWN_CUSTOM_EVENT')).toBe('Unknown custom event');
    expect(formatEventAction(null)).toBe('Operación del sistema');
    expect(formatEventAction('')).toBe('Operación del sistema');
  });

  it('formatea mensajes completos con actor', () => {
    expect(
      formatEventMessage('LOGIN_FAILED_USER_INACTIVE', 'juan_operador'),
    ).toBe(
      'Acceso denegado: Usuario inactivo o deshabilitado (por juan_operador)',
    );

    expect(formatEventMessage('ROUTER_DOWN', 'sistema')).toBe(ROUTER_DOWN_ES);

    expect(formatEventMessage('ROUTER_DOWN', null)).toBe(ROUTER_DOWN_ES);
  });

  it('detecta UUIDs crudos y los omite del mensaje formateado para evitar fuga visual', () => {
    const rawUuid = '5046a660-b1ba-423d-bf0b-a6f0fd80c40b';
    expect(isRawUuid(rawUuid)).toBe(true);
    expect(isRawUuid('operador_noc')).toBe(false);
    expect(isRawUuid('')).toBe(false);
    expect(isRawUuid(null)).toBe(false);

    expect(formatEventMessage('SESSION_TOKEN_RENEWED', rawUuid)).toBe(
      'Sesión de operador renovada',
    );
    expect(formatEventMessage('MAINTENANCE_WINDOW_EXPIRED_AUTO_DELETED', rawUuid)).toBe(
      'Ventana de mantenimiento finalizada',
    );
    expect(formatEventMessage('MAINTENANCE_WINDOW_EXPIRED_AUTO_DELETED', 'admin')).toBe(
      'Ventana de mantenimiento finalizada (por admin)',
    );
  });

  it('soporta traducción bilingüe (es/en) y desempaqueta cadenas crudas de auditoría ACTION (CATEGORY): actor', () => {
    const rawAudit = 'TENANT_FEATURE_FLAGS_UPDATED (GOVERNANCE): sinfallas';
    const parsed = parseRawAuditString(rawAudit);
    expect(parsed).toEqual({
      actionCode: 'TENANT_FEATURE_FLAGS_UPDATED',
      extractedActor: 'sinfallas',
    });

    expect(formatEventMessage(rawAudit, undefined, 'es')).toBe(
      'Parámetros del tenant actualizados (por sinfallas)',
    );
    expect(formatEventMessage(rawAudit, undefined, 'en')).toBe(
      'Tenant parameters updated (by sinfallas)',
    );
    expect(formatEventAction('ROUTER_DOWN', 'en')).toBe('Router offline (unreachable)');
  });
});
