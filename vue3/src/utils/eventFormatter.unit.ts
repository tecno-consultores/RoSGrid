// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect } from 'vitest';
import { formatEventAction, formatEventMessage } from './eventFormatter';

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
    expect(formatEventAction('ROUTER_DOWN')).toBe(
      'Router fuera de línea (sin respuesta)',
    );
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

    expect(formatEventMessage('ROUTER_DOWN', 'sistema')).toBe(
      'Router fuera de línea (sin respuesta)',
    );

    expect(formatEventMessage('ROUTER_DOWN', null)).toBe(
      'Router fuera de línea (sin respuesta)',
    );
  });
});
