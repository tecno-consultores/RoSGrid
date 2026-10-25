// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach } from 'vitest';
import { useI18n } from './useI18n';

const storageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = String(value);
    },
    clear: () => {
      store = {};
    },
    removeItem: (key: string) => {
      delete store[key];
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: storageMock,
  writable: true,
  configurable: true,
});

describe('useI18n — Composable de Internacionalización Reactivo', () => {
  beforeEach(() => {
    window.localStorage.clear();
    const { setLocale } = useI18n();
    setLocale('es');
  });

  it('inicia por defecto en idioma español ("es")', () => {
    const { locale } = useI18n();
    expect(locale.value).toBe('es');
  });

  it('traduce claves existentes en el diccionario español', () => {
    const { t } = useI18n();
    expect(t('common.save')).toBe('Guardar');
    expect(t('nav.inventory')).toBe('Inventario');
    expect(t('nav.subscribers_map')).toBe('Mapa de Clientes');
    expect(t('field_tech.capture_gps')).toBe('📍 Capturar Coordenadas GPS');
  });

  it('retorna la clave o el fallback provisto si la clave no existe', () => {
    const { t } = useI18n();
    expect(t('non.existent.key')).toBe('non.existent.key');
    expect(t('another.missing.key', 'Texto por defecto')).toBe('Texto por defecto');
  });

  it('permite cambiar el idioma a inglés ("en") y actualiza traducciones', () => {
    const { locale, setLocale, t } = useI18n();
    setLocale('en');
    expect(locale.value).toBe('en');
    expect(t('common.save')).toBe('Save');
    expect(t('nav.inventory')).toBe('Inventory');
    expect(t('nav.subscribers_map')).toBe('Subscribers Map');
    expect(t('field_tech.capture_gps')).toBe('📍 Capture GPS Coordinates');
    expect(window.localStorage.getItem('rg_locale')).toBe('en');
    expect(document.documentElement.lang).toBe('en');
  });

  it('alterna el idioma entre "es" y "en" con toggleLocale()', () => {
    const { locale, toggleLocale, setLocale } = useI18n();
    setLocale('es');
    expect(locale.value).toBe('es');

    toggleLocale();
    expect(locale.value).toBe('en');

    toggleLocale();
    expect(locale.value).toBe('es');
  });

  it('ignora códigos de idioma no soportados', () => {
    const { locale, setLocale } = useI18n();
    setLocale('es');
    (setLocale as (l: string) => void)('fr');
    expect(locale.value).toBe('es');
  });

  it('expone la lista de idiomas disponibles', () => {
    const { availableLocales } = useI18n();
    expect(availableLocales).toContain('es');
    expect(availableLocales).toContain('en');
  });

  it('proporciona traducciones simétricas válidas para los 16 módulos clave en español e inglés', () => {
    const { setLocale, t } = useI18n();

    const keysToVerify = [
      // 1. Maker-Checker
      { key: 'approvals.title', es: 'Bandeja de Aprobaciones — Maker-Checker', en: 'Approval Inbox — Maker-Checker' },
      { key: 'approvals.tab_pending', es: 'Pendientes de Firma', en: 'Pending Signature' },
      { key: 'approvals.btn_approve', es: '✓ Aprobar y Ejecutar con Safe Mode (60s)', en: '✓ Approve & Execute with Safe Mode (60s)' },
      // 2. IPAM
      { key: 'ipam.total_subscribers', es: 'Total Abonados / Servicios', en: 'Total Subscribers / Services' },
      { key: 'ipam.tab_sync', es: '🔄 Sincronización MikroTik', en: '🔄 MikroTik Sync' },
      // 3. Mapa de Clientes / Red
      { key: 'network_map.layer_routers', es: 'Routers de Red', en: 'Network Routers' },
      { key: 'network_map.filter_online', es: '🟢 Solo Online', en: '🟢 Online Only' },
      // 4. Técnico de Campo Móvil
      { key: 'field_tech.ports_24', es: '24 Puertos', en: '24 Ports' },
      { key: 'field_tech.splitter_symmetric_8', es: 'Splitter Simétrico 1:8', en: 'Symmetric Splitter 1:8' },
      // 5. Topología L2
      { key: 'l2_topology.title', es: 'Topología Física Layer 2 — Mapa de Interconexión', en: 'Layer 2 Physical Topology — Interconnection Map' },
      { key: 'l2_topology.filter_only_poe', es: 'Solo enlaces PoE (⚡)', en: 'PoE links only (⚡)' },
      // 6. Respaldos Diff
      { key: 'backups_diff.title', es: 'Historial de Respaldos & Comparador de Diferencias', en: 'Backup History & Difference Comparator' },
      { key: 'backups_diff.btn_create_now', es: '➕ Crear Backup Ahora', en: '➕ Create Backup Now' },
      // 7. Operaciones Masivas
      { key: 'bulk_ops.title', es: 'Operaciones Masivas & Actualizaciones de Flota', en: 'Bulk Operations & Fleet Updates' },
      { key: 'bulk_ops.tab_templates', es: 'Plantillas Golden Config', en: 'Golden Config Templates' },
      // 8. Usuarios & RBAC
      { key: 'users_mgmt.title', es: 'Gestión de Usuarios y Roles RBAC (11 Roles)', en: 'User Management & RBAC Roles (11 Roles)' },
      { key: 'users_mgmt.btn_create_user', es: '+ Registrar Operador', en: '+ Register Operator' },
      { key: 'users_mgmt.btn_router_matrix', es: '🎯 Matriz de Routers', en: '🎯 Router Matrix' },
      // 9. Tenants & Módulos Studio
      { key: 'tenants_mgmt.title', es: 'Administración de Empresas (Multi-Tenant)', en: 'Enterprise Administration (Multi-Tenant)' },
      { key: 'tenants_mgmt.btn_register_tenant', es: '+ Registrar Empresa', en: '+ Register Enterprise' },
      { key: 'tenants_mgmt.studio_back', es: '⬅ Volver a Empresas', en: '⬅ Back to Enterprises' },
      // 10. CIS Hardening
      { key: 'enterprise.tab_cis', es: 'CIS Hardening', en: 'CIS Hardening' },
      { key: 'enterprise.cis_score_desc', es: 'Puntaje Global de Cumplimiento Normativo CIS', en: 'Overall CIS Security Compliance Score' },
      { key: 'enterprise.auto_harden', es: 'Endurecer Router (Auto-Hardening)', en: 'Auto-Harden Router (CIS)' },
      // 11. CVE Matrix
      { key: 'cve_matrix.title', es: 'Matriz de Vulnerabilidades CVE — Flota MikroTik', en: 'CVE Vulnerability Matrix — MikroTik Fleet' },
      { key: 'cve_matrix.btn_sync', es: 'Sincronizar Boletines', en: 'Sync Advisories' },
      // 12. WORM Audit Logs
      { key: 'audit_logs.title', es: 'Registro de Auditoría Inmutable (WORM)', en: 'Immutable Audit Logs (WORM)' },
      { key: 'audit_logs.btn_verify_integrity', es: 'Verificar Integridad WORM', en: 'Verify WORM Integrity' },
      // 13. SD-WAN
      { key: 'enterprise.tab_sdwan', es: 'SD-WAN Hub & Spoke', en: 'SD-WAN Hub & Spoke' },
      { key: 'enterprise.deploy_failover', es: 'Desplegar Failover Multi-WAN', en: 'Deploy Multi-WAN Failover' },
      // 14. L2 Security & Rogue DHCP
      { key: 'enterprise.tab_switching', es: 'Seguridad L2 & Rogue DHCP', en: 'L2 Security & Rogue DHCP' },
      { key: 'enterprise.switching_trusted', es: 'Puertos Confiables (Trusted / Uplink):', en: 'Trusted Ports (Uplink):' },
      // 15. SLA Telemetry
      { key: 'enterprise.tab_sla', es: 'Telemetría de SLA', en: 'SLA Telemetry' },
      { key: 'enterprise.export_sla', es: 'Exportar Reporte Formal de SLA', en: 'Export Formal SLA Report' },
      // 16. Canales de Alerta
      { key: 'notification_channels.title', es: 'Canales de Notificación y Alerta', en: 'Notification & Alert Channels' },
      { key: 'notification_channels.btn_new_channel', es: '+ Nuevo Canal', en: '+ New Channel' },
    ];

    // Verificar en Español
    setLocale('es');
    for (const item of keysToVerify) {
      const translated = t(item.key);
      expect(translated).toBe(item.es);
      expect(translated).not.toBe(item.key);
    }

    // Verificar en Inglés
    setLocale('en');
    for (const item of keysToVerify) {
      const translated = t(item.key);
      expect(translated).toBe(item.en);
      expect(translated).not.toBe(item.key);
      // Asegurar que no es idéntico al español cuando difieren
      if (item.es !== item.en) {
        expect(translated).not.toBe(item.es);
      }
    }
  });
});
