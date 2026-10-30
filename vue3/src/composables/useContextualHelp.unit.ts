// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref } from 'vue';
import { useContextualHelp } from './useContextualHelp';
import {
  HELP_CATALOG,
  formatHelpEntryAsMarkdown,
  getHelpEntryByKey,
  resolveHelpKeyFromRoute,
} from '@/data/helpCatalog';

const mockRoutePath = ref('/inventory');
const mockRouteName = ref<string | undefined>('RouterInventory');

vi.mock('vue-router', () => ({
  useRoute: () => ({
    get path() {
      return mockRoutePath.value;
    },
    get name() {
      return mockRouteName.value;
    },
  }),
}));

describe('useContextualHelp & helpCatalog — Ayuda Contextual en Pantalla (Hito 27.14)', () => {
  beforeEach(() => {
    mockRoutePath.value = '/inventory';
    mockRouteName.value = 'RouterInventory';
    const help = useContextualHelp();
    help.closeHelp();
  });

  it('resuelve la clave de ayuda contextual para rutas globales, WebFig Capa 1 y Capa 2 Universal', () => {
    expect(resolveHelpKeyFromRoute('/', 'DashboardRoot')).toBe('dashboard');
    expect(resolveHelpKeyFromRoute('/inventory', 'RouterInventory')).toBe('inventory');
    expect(resolveHelpKeyFromRoute('/noc-wallboard')).toBe('wallboard');
    expect(resolveHelpKeyFromRoute('/approvals')).toBe('approvals');
    expect(resolveHelpKeyFromRoute('/ipam')).toBe('ipam');
    expect(resolveHelpKeyFromRoute('/subscribers/map')).toBe('subscribers-map');
    expect(resolveHelpKeyFromRoute('/field-ops')).toBe('field-tech');
    expect(resolveHelpKeyFromRoute('/topology/l2')).toBe('topology-l2');
    expect(resolveHelpKeyFromRoute('/backups')).toBe('backups-diff');
    expect(resolveHelpKeyFromRoute('/bulk-ops')).toBe('bulk-ops');
    expect(resolveHelpKeyFromRoute('/users')).toBe('users-rbac');
    expect(resolveHelpKeyFromRoute('/sessions')).toBe('sessions');
    expect(resolveHelpKeyFromRoute('/admin/tenants')).toBe('tenants');
    expect(resolveHelpKeyFromRoute('/admin/tenants/t1/modules')).toBe('tenant-modules');
    expect(resolveHelpKeyFromRoute('/enterprise/compliance')).toBe('enterprise');
    expect(resolveHelpKeyFromRoute('/inventory/cves')).toBe('fleet-cves');
    expect(resolveHelpKeyFromRoute('/inventory/maintenance-windows')).toBe('maintenance');
    expect(resolveHelpKeyFromRoute('/audit-logs')).toBe('audit-logs');
    expect(resolveHelpKeyFromRoute('/routers/r1/webfig/live')).toBe('webfig-dashboard');
    expect(resolveHelpKeyFromRoute('/routers/r1/webfig/interfaces')).toBe('webfig-interfaces');
    expect(resolveHelpKeyFromRoute('/routers/r1/webfig/bridge')).toBe('webfig-bridge');
    expect(resolveHelpKeyFromRoute('/routers/r1/webfig/wireguard')).toBe('webfig-wireguard');
    expect(resolveHelpKeyFromRoute('/routers/r1/webfig/ip')).toBe('webfig-ip');
    expect(resolveHelpKeyFromRoute('/routers/r1/webfig/ipv6')).toBe('webfig-ipv6');
    expect(resolveHelpKeyFromRoute('/routers/r1/webfig/firewall')).toBe('webfig-firewall');
    expect(resolveHelpKeyFromRoute('/routers/r1/webfig/routing')).toBe('webfig-routing');
    expect(resolveHelpKeyFromRoute('/routers/r1/webfig/ppp')).toBe('webfig-ppp');
    expect(resolveHelpKeyFromRoute('/routers/r1/webfig/tools')).toBe('webfig-tools');
    expect(resolveHelpKeyFromRoute('/routers/r1/webfig/syslog')).toBe('webfig-syslog');
    expect(resolveHelpKeyFromRoute('/routers/r1/webfig/layer2/system/certificate')).toBe(
      'webfig-layer2',
    );
    expect(resolveHelpKeyFromRoute('/unknown-path')).toBe('dashboard');
  });

  it('retorna entradas válidas del catálogo y formatea la guía como Markdown LLM-Ready', () => {
    const entry = getHelpEntryByKey('FirewallRules');
    expect(entry.routeKey).toBe('webfig-firewall');
    expect(entry.title).toContain('Firewall');
    expect(entry.keyActions.length).toBeGreaterThan(0);

    const fallback = getHelpEntryByKey('NonExistentKey');
    expect(fallback.routeKey).toBe(HELP_CATALOG.dashboard.routeKey);

    const md = formatHelpEntryAsMarkdown(entry);
    expect(md).toContain(`# ${entry.title}`);
    expect(md).toContain('## Acciones Clave Paso a Paso');
    expect(md).toContain('## Gobernanza, Safe Mode (60s) y Seguridad Zero-Trust');
    expect(md).toContain('## Notas Técnicas MikroTik RouterOS v7 (/rest/*)');
  });

  it('controla apertura, cierre, conmutación, selección manual de tópico y atajos F1 / Alt+H / Escape', async () => {
    const help = useContextualHelp();
    expect(help.isHelpOpen.value).toBe(false);
    expect(help.activeHelpKey.value).toBe('inventory');

    help.openHelp();
    expect(help.isHelpOpen.value).toBe(true);
    expect(help.currentHelpEntry.value.routeKey).toBe('inventory');

    help.selectHelpTopic('webfig-firewall');
    expect(help.activeHelpKey.value).toBe('webfig-firewall');
    expect(help.currentHelpEntry.value.routeKey).toBe('webfig-firewall');

    help.resetToRouteTopic();
    expect(help.activeHelpKey.value).toBe('inventory');

    // Toggle con clave específica
    help.toggleHelp('webfig-routing');
    expect(help.isHelpOpen.value).toBe(true);
    expect(help.activeHelpKey.value).toBe('webfig-routing');

    // Toggle con la misma clave cierra el cajón
    help.toggleHelp('webfig-routing');
    expect(help.isHelpOpen.value).toBe(false);

    // Atajos de teclado F1, Alt+H y Escape
    const f1Event = new KeyboardEvent('keydown', { key: 'F1', cancelable: true });
    help.handleHelpKeydown(f1Event);
    expect(help.isHelpOpen.value).toBe(true);

    const escEvent = new KeyboardEvent('keydown', { key: 'Escape', cancelable: true });
    help.handleHelpKeydown(escEvent);
    expect(help.isHelpOpen.value).toBe(false);

    const altHEvent = new KeyboardEvent('keydown', { key: 'h', altKey: true, cancelable: true });
    help.handleHelpKeydown(altHEvent);
    expect(help.isHelpOpen.value).toBe(true);
  });

  it('copia la guía activa como Markdown al portapapeles', async () => {
    const writeTextSpy = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: { writeText: writeTextSpy },
    });

    const help = useContextualHelp();
    help.openHelp('webfig-layer2');
    const md = await help.copyCurrentHelpAsMarkdown();

    expect(md).toContain('Motor Universal Capa 2');
    expect(writeTextSpy).toHaveBeenCalledWith(md);
    expect(help.isMarkdownCopied.value).toBe(true);
  });
});
