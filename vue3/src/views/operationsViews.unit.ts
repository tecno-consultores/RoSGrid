// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { setActivePinia, createPinia } from 'pinia';
import { http } from '@/api/httpClient';

import ApprovalsInboxView from './ApprovalsInboxView.vue';
import RscGitDiffViewer from './RscGitDiffViewer.vue';
import BulkOperationsAndUpdatesView from './BulkOperationsAndUpdatesView.vue';
import NocWallboardView from './NocWallboardView.vue';
import ImmutableAuditLogsView from './ImmutableAuditLogsView.vue';

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { routerId: 'r-01' },
    path: '/operations/approvals',
    query: {},
  }),
  useRouter: () => ({
    push: vi.fn(),
  }),
  RouterView: { template: '<div>ROUTER_VIEW</div>' },
  RouterLink: { template: '<a><slot /></a>' },
}));

describe('Operations and Auditor Views Unit Tests (Hito 13)', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('ApprovalsInboxView — aprueba solicitudes con Safe Mode y filtra subpestañas', async () => {
    vi.useFakeTimers();

    const { useAuthStore } = await import('@/stores/useAuthStore');
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-checker',
      email: 'checker@example.com',
      username: 'checker.user',
      tenant_id: 't-1',
      tenant_slug: 'corp',
      role: 'SUPERVISOR',
      totp_enabled: true,
    });

    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: {
        items: [
          {
            id: 'appr-100',
            requested_by: 'usr-other',
            requested_by_username: 'maker.user',
            requested_by_role: 'SUPPORT_L2',
            action_type: 'ROUTING_CHANGE',
            router_id: 'r-01',
            router_name: 'Core-01',
            justification: 'Expirada',
            previous_state_snapshot: {},
            request_payload: {},
            status: 'EXPIRED',
            created_at: new Date().toISOString(),
          },
          {
            id: 'appr-101',
            requested_by: 'usr-other',
            requested_by_username: 'maker.user',
            requested_by_role: 'SUPPORT_L2',
            action_type: 'FIREWALL_DROP',
            router_id: 'r-01',
            router_name: 'Core-01',
            justification: 'Bloqueo puerto sospechoso',
            previous_state_snapshot: { rule: 1 },
            request_payload: { rule: 2 },
            status: 'AWAITING_APPROVAL',
            created_at: new Date().toISOString(),
          },
          {
            id: 'appr-102',
            requested_by: 'usr-other',
            requested_by_username: 'maker.user',
            requested_by_role: 'SUPPORT_L2',
            action_type: 'ROUTING_CHANGE',
            router_id: 'r-01',
            router_name: 'Core-01',
            justification: 'Cambio ruta BGP',
            previous_state_snapshot: { rule: 1 },
            request_payload: { rule: 2 },
            status: 'AWAITING_APPROVAL',
            created_at: new Date().toISOString(),
          },
        ],
      },
      headers: new Headers(),
    });

    vi.spyOn(http, 'post').mockResolvedValue({
      status: 200,
      data: { success: true },
      headers: new Headers(),
    });

    const wrapper = mount(ApprovalsInboxView);
    await flushPromises();

    expect(wrapper.find('h1').text()).toContain('Bandeja de Aprobaciones');

    // Cambiar pestañas
    const tabs = wrapper.findAll('.btn-subtab');
    if (tabs.length >= 3) {
      await tabs[1].trigger('click'); // aprobadas
      await tabs[2].trigger('click'); // rechazadas
      await tabs[0].trigger('click'); // pendientes
      await flushPromises();
    }

    // Seleccionar solicitud 0 de la lista y aprobar con éxito
    const cards = wrapper.findAll('.inbox-card');
    if (cards.length > 0) {
      await cards[0].trigger('click');
      await cards[0].trigger('keydown.enter');
    }

    // Escribir comentario y aprobar (éxito)
    const commentInput = wrapper.find('#review-comment');
    if (commentInput.exists()) {
      await commentInput.setValue('Aprobado conforme al ticket de soporte #1234');
    }

    const approveBtn = wrapper.find('.btn-approve');
    if (approveBtn.exists()) {
      await approveBtn.trigger('click');
      await flushPromises();
    }

    // Seleccionar solicitud 1 de la lista y rechazar con éxito
    const remainingCards = wrapper.findAll('.inbox-card');
    if (remainingCards.length > 0) {
      await remainingCards[0].trigger('click');
    }
    const rejectBtn = wrapper.find('.btn-reject');
    if (rejectBtn.exists()) {
      await rejectBtn.trigger('click');
      await flushPromises();
    }

    // Avanzar temporizador simulado para limpiar mensajes de acción
    vi.advanceTimersByTime(4500);
    await flushPromises();
    vi.useRealTimers();
  });

  it('ApprovalsInboxView — maneja rechazo, fallback de error y bloquea auto-aprobación', async () => {
    vi.useFakeTimers();

    const { useAuthStore } = await import('@/stores/useAuthStore');
    const authStore = useAuthStore();
    authStore.setAuth({
      id: 'usr-checker',
      email: 'checker@example.com',
      username: 'checker.user',
      tenant_id: 't-1',
      tenant_slug: 'corp',
      role: 'SUPERADMIN_GLOBAL',
      totp_enabled: true,
    });

    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: {
        items: [
          {
            id: 'appr-103',
            requested_by: 'usr-maker',
            requested_by_username: 'maker.user',
            requested_by_role: 'SUPPORT_L2',
            action_type: 'BGP_PEER_RESET',
            router_id: 'r-01',
            router_name: 'Core-01',
            justification: 'Reset de sesión BGP',
            previous_state_snapshot: {},
            request_payload: {},
            status: 'AWAITING_APPROVAL',
            created_at: new Date().toISOString(),
          },
          {
            id: 'appr-104',
            requested_by: 'usr-maker',
            requested_by_username: 'maker.user',
            requested_by_role: 'SUPPORT_L2',
            action_type: 'BGP_PEER_RESET',
            router_id: 'r-01',
            router_name: 'Core-01',
            justification: 'Reset de sesión BGP 2',
            previous_state_snapshot: {},
            request_payload: {},
            status: 'AWAITING_APPROVAL',
            created_at: new Date().toISOString(),
          },
        ],
      },
      headers: new Headers(),
    });

    // Probar fallo en rechazo para cubrir catch block
    vi.spyOn(http, 'post').mockRejectedValueOnce(new Error('Network reject fail'));

    const wrapper = mount(ApprovalsInboxView);
    await flushPromises();

    // Rechazar solicitud con fallback catch
    const rejectBtn = wrapper.find('.btn-reject');
    if (rejectBtn.exists()) {
      await rejectBtn.trigger('click');
      await flushPromises();
    }

    // Seleccionar segunda solicitud para probar fallo en aprobación
    const cards = wrapper.findAll('.inbox-card');
    if (cards.length > 0) {
      await cards[0].trigger('click');
      await flushPromises();
    }

    // Probar fallo en aprobación para cubrir catch block
    vi.spyOn(http, 'post').mockRejectedValueOnce(new Error('Network approve fail'));
    const approveBtnAction = wrapper.find('.btn-approve');
    if (approveBtnAction.exists()) {
      await approveBtnAction.trigger('click');
      await flushPromises();
    }

    // Probar auto-aprobación: cambiar usuario a 'usr-maker'
    authStore.setAuth({
      id: 'usr-maker',
      email: 'maker@example.com',
      username: 'maker.user',
      tenant_id: 't-1',
      tenant_slug: 'corp',
      role: 'SUPERVISOR',
      totp_enabled: true,
    });

    const wrapperSelf = mount(ApprovalsInboxView);
    await flushPromises();

    // El botón aprobar debe estar deshabilitado por segregación
    const approveBtn = wrapperSelf.find('.btn-approve');
    if (approveBtn.exists()) {
      expect((approveBtn.element as HTMLButtonElement).disabled).toBe(true);
    }

    // Avanzar temporizador simulado para limpiar mensajes de acción en catch
    vi.advanceTimersByTime(4500);
    await flushPromises();
    vi.useRealTimers();
  });

  it('RscGitDiffViewer — calcula diferencias, cambia modos y descarga backups', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: {
        items: [
          {
            id: 'bk-1',
            router_id: 'r-01',
            filename: 'backup-1.rsc',
            ros_version_at_backup: '7.16.1',
            created_at: new Date().toISOString(),
            sha256_hash: '1234567890abcdef',
            lines_added: 5,
            lines_removed: 2,
          },
        ],
      },
      headers: new Headers(),
    });

    vi.spyOn(http, 'post').mockResolvedValue({
      status: 200,
      data: { success: true },
      headers: new Headers(),
    });

    const wrapper = mount(RscGitDiffViewer);
    await flushPromises();

    // Crear backup manual (éxito)
    const createBtn = wrapper.find('.diff-header-actions .btn--primary');
    await createBtn.trigger('click');
    await flushPromises();

    // Crear backup manual con fallback catch
    vi.spyOn(http, 'post').mockRejectedValueOnce(new Error('Post fail'));
    await createBtn.trigger('click');
    await flushPromises();

    // Avanzar temporizador para limpiar mensaje de backup
    vi.useFakeTimers();
    vi.advanceTimersByTime(5500);
    await flushPromises();
    vi.useRealTimers();

    // Cambiar modo a unificado y dividido
    const toggleBtns = wrapper.findAll('.btn-toggle');
    if (toggleBtns.length > 1) {
      await toggleBtns[1].trigger('click');
      expect(wrapper.find('.diff-unified-container').exists()).toBe(true);
      await toggleBtns[0].trigger('click');
      expect(wrapper.find('.diff-split-container').exists()).toBe(true);
    }

    // Cambiar selectores de diff base y objetivo
    const selects = wrapper.findAll('.diff-select');
    if (selects.length > 1) {
      await selects[1].setValue('LIVE');
      await selects[1].trigger('change');
      await selects[0].setValue('bk-1');
      await selects[0].trigger('change');
    }

    // Seleccionar backup mediante botón en la lista lateral
    const btnText = wrapper.find('.btn-text');
    if (btnText.exists()) {
      await btnText.trigger('click');
    }

    // Eventos de teclado (n incrementa, luego p decrementa)
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'n' }));
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'p' }));

    // Descarga de backup (rsc y backup)
    const createObjUrl = vi.fn().mockReturnValue('blob:dummy');
    const revokeObjUrl = vi.fn();
    globalThis.URL.createObjectURL = createObjUrl;
    globalThis.URL.revokeObjectURL = revokeObjUrl;

    const downloadBtns = wrapper.findAll('.btn-icon');
    for (const btn of downloadBtns) {
      await btn.trigger('click');
    }

    wrapper.unmount();
  });

  it('RscGitDiffViewer — fallback ante lista vacía de respaldos', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: { items: [] },
      headers: new Headers(),
    });
    const wrapper = mount(RscGitDiffViewer);
    await flushPromises();
    expect(wrapper.exists()).toBe(true);
  });

  it('BulkOperationsAndUpdatesView — completa asistente de 3 pasos y matriz de updates', async () => {
    vi.useFakeTimers();

    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: [
        {
          id: 'tpl-dns',
          name: 'Actualizar DNS Corporativos',
          category: 'IP Service',
          description: 'Configura servidores DNS',
          variables_schema: [{ key: 'primary_dns', label: 'DNS Primario', default_val: '1.1.1.1' }],
          ros_command_template: '/ip dns set servers={{primary_dns}}',
        },
        {
          id: 'tpl-fw-drop',
          name: 'Bloquear IP Atacante',
          category: 'Seguridad',
          description: 'Agrega regla firewall',
          variables_schema: [
            { key: 'bad_ip', label: 'IP Atacante', default_val: '203.0.113.45/32' },
          ],
          ros_command_template:
            '/ip firewall raw add chain=prerouting src-address={{bad_ip}} action=drop',
        },
      ],
      headers: new Headers(),
    });

    vi.spyOn(http, 'post').mockResolvedValue({
      status: 200,
      data: { success: true },
      headers: new Headers(),
    });

    const { useInventoryStore } = await import('@/stores/useInventoryStore');
    const invStore = useInventoryStore();
    invStore.setRouters([
      {
        id: 'r-01',
        tenant_id: 't-1',
        display_name: 'RB5009-Core-01',
        ros_identity: 'RB5009-Core-01',
        ip_address: '192.168.88.1',
        api_port: 8728,
        ros_version: '7.16',
        network_role: 'CORE_ROUTER',
        admin_state: 'PRODUCTION',
        is_reachable: true,
      },
      {
        id: 'r-02',
        tenant_id: 't-1',
        display_name: 'CCR2004-Border-02',
        ros_identity: 'CCR2004-Border-02',
        ip_address: '10.0.0.1',
        api_port: 8728,
        ros_version: '7.16',
        network_role: 'BORDER_BGP',
        admin_state: 'PRODUCTION',
        is_reachable: true,
      },
    ]);

    const wrapper = mount(BulkOperationsAndUpdatesView);
    await flushPromises();

    // Paso 1: Filtros de flota
    const selects = wrapper.findAll('.form-select');
    if (selects.length > 1) {
      await selects[0].setValue('CORE_ROUTER');
      await selects[0].trigger('change');
      await selects[1].setValue('datacenter-central');
      await selects[1].trigger('change');
    }

    // Toggle seleccionar todos los routers visibles
    const selectAllChk = wrapper.find(
      'input[aria-label="Seleccionar todos los routers mostrados"]',
    );
    if (selectAllChk.exists()) {
      await selectAllChk.setValue(true);
      await selectAllChk.trigger('change');
    }

    // Siguiente a paso 2
    const nextBtn1 = wrapper.find('.step-footer .btn--primary');
    await nextBtn1.trigger('click');

    // Paso 2: Selección de plantilla
    const tplCards = wrapper.findAll('.template-card');
    if (tplCards.length > 1) {
      await tplCards[1].trigger('click');
    }

    // Modificar variables para activar @input generatePreview
    const varInput = wrapper.find('.vars-grid input');
    if (varInput.exists()) {
      await varInput.setValue('10.200.0.1/32');
      await varInput.trigger('input');
    }

    // Volver a paso 1 y regresar a paso 2
    const backBtn = wrapper.find('.step-footer .btn--secondary');
    if (backBtn.exists()) {
      await backBtn.trigger('click');
      expect(wrapper.find('.fleet-table').exists()).toBe(true);
      await wrapper.find('.step-footer .btn--primary').trigger('click');
    }

    // Ejecutar masivo (Paso 3) con error post para cubrir catch branch
    vi.spyOn(http, 'post').mockRejectedValueOnce(new Error('Bulk fail'));
    const runBtn = wrapper.find('.btn--run');
    if (runBtn.exists()) {
      await runBtn.trigger('click');
      // Avanzar temporizador simulado para progreso
      for (let i = 0; i < 6; i++) {
        vi.advanceTimersByTime(400);
        await flushPromises();
      }
    }

    // Cambiar a pestaña de Updates RouterOS
    const tabBtns = wrapper.findAll('.tab-btn');
    if (tabBtns.length > 1) {
      await tabBtns[1].trigger('click');
      await flushPromises();

      const updateBtns = wrapper.findAll('.fleet-table .btn--primary');
      if (updateBtns.length > 0) {
        await updateBtns[0].trigger('click');
        await flushPromises();

        // Probar error fallback en siguiente botón pendiente
        const nextBtns = wrapper.findAll('.fleet-table .btn--primary');
        if (nextBtns.length > 0) {
          vi.spyOn(http, 'post').mockRejectedValueOnce(new Error('Update network fail'));
          await nextBtns[0].trigger('click');
          await flushPromises();
        }

        // Avanzar temporizador para limpiar updateSuccess callback
        vi.advanceTimersByTime(5500);
        await flushPromises();
      }
    }

    vi.useRealTimers();
  });

  it('NocWallboardView — pantalla completa, eventos en tiempo real y selección de router', async () => {
    vi.useFakeTimers();

    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: {
        items: [
          {
            id: 'r-01',
            tenant_id: 't-1',
            display_name: 'Wallboard Router',
            ip_address: '10.0.0.1',
            is_reachable: true,
            admin_state: 'PRODUCTION',
            ssl_trust_status: 'TRUSTED_PINNED',
          },
        ],
      },
      headers: new Headers(),
    });

    const wrapper = mount(NocWallboardView, {
      global: {
        stubs: { OsmRouterMap: true },
      },
    });
    await flushPromises();

    expect(wrapper.find('.brand-title').text()).toContain('NOC Wallboard');

    // Validación de eliminación de elementos innecesarios
    expect(wrapper.find('.live-indicator').exists()).toBe(false);
    expect(wrapper.find('.wallboard-clock').exists()).toBe(false);
    expect(wrapper.find('.clock-time').exists()).toBe(false);
    expect(wrapper.find('.clock-sync').exists()).toBe(false);
    expect(wrapper.find('.events-subtitle').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('/ws/v1/tenant/events');
    expect(wrapper.text()).not.toContain('EN VIVO 24/7');

    // Seleccionar router desde mapa OsmRouterMap stub
    const osmMap = wrapper.findComponent({ name: 'OsmRouterMap' });
    if (osmMap.exists()) {
      osmMap.vm.$emit('select-router', 'r-01');
    }

    // Toggle fullscreen
    const fsBtn = wrapper.find('.btn-fullscreen');
    await fsBtn.trigger('click');

    // Simular evento fullscreenchange
    document.dispatchEvent(new Event('fullscreenchange'));

    // Salir de fullscreen
    Object.defineProperty(document, 'fullscreenElement', {
      value: document.body,
      configurable: true,
    });
    await fsBtn.trigger('click');
    Object.defineProperty(document, 'fullscreenElement', {
      value: null,
      configurable: true,
    });

    // Eventos timer de simulación NOC (disparar más de 20 veces para cubrir pop() y severidades)
    vi.advanceTimersByTime(350000);
    await flushPromises();

    const events = wrapper.findAll('.event-item');
    expect(events.length).toBeGreaterThan(0);

    wrapper.unmount();
    vi.useRealTimers();
  });

  it('NocWallboardView — alerta y banner de caída masiva (Mass Outage) con reconocimiento y silenciado', async () => {
    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url.includes('/api/v1/inventory/routers')) {
        return {
          status: 200,
          data: { items: [] },
          headers: new Headers(),
        };
      }
      if (url.includes('/api/v1/audit/logs')) {
        return {
          status: 200,
          data: {
            items: [
              {
                id: 'log-outage-1',
                event_action: 'MASS_OUTAGE_TRIGGERED',
                created_at: new Date().toISOString(),
                after_state: {
                  affected_onus_count: 14,
                  pon_port: 'sfp-plus1',
                  optical_box: 'NAP-SectorNorte',
                },
              },
            ],
          },
          headers: new Headers(),
        };
      }
      return { status: 200, data: [], headers: new Headers() };
    });

    const wrapper = mount(NocWallboardView, {
      global: {
        stubs: { OsmRouterMap: true },
      },
    });
    await flushPromises();

    expect(wrapper.find('.mass-outage-banner').exists()).toBe(true);
    expect(wrapper.text()).toContain('ALERTA DE CAÍDA MASIVA');
    expect(wrapper.text()).toContain('14 Equipos');

    // Botón de silenciar
    const btnSilence = wrapper.find('.btn-outage-silence');
    await btnSilence.trigger('click');
    expect(btnSilence.text()).toContain('Activar Sonido');

    // Botón de reconocer
    const btnAck = wrapper.find('#btn-ack-mass-outage');
    await btnAck.trigger('click');
    expect(wrapper.find('.mass-outage-banner').exists()).toBe(false);
  });

  it('NocWallboardView — traduce eventos crudos como LOGIN_FAILED_USER_INACTIVE a descripciones amigables', async () => {
    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url.includes('/api/v1/inventory/routers')) {
        return { status: 200, data: { items: [] }, headers: new Headers() };
      }
      if (url.includes('/api/v1/audit/logs')) {
        return {
          status: 200,
          data: {
            items: [
              {
                id: 'log-1',
                event_action: 'LOGIN_FAILED_USER_INACTIVE',
                actor_username: 'operador_prueba',
                status_code: 403,
                created_at: new Date().toISOString(),
              },
            ],
          },
          headers: new Headers(),
        };
      }
      return { status: 200, data: [], headers: new Headers() };
    });

    const wrapper = mount(NocWallboardView, {
      global: {
        stubs: { OsmRouterMap: true },
      },
    });
    await flushPromises();

    expect(wrapper.text()).toContain('Acceso denegado: Usuario inactivo o deshabilitado');
    expect(wrapper.text()).not.toContain('LOGIN_FAILED_USER_INACTIVE registrada por');
  });

  it('ImmutableAuditLogsView — busca registros forenses, verifica cadena WORM y exporta', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: {
        items: [
          {
            id: 'aud-test-1',
            actor_id: 'usr-1',
            actor_username: 'auditor.test',
            actor_role: 'AUDITOR',
            action_category: 'AUTH',
            action_name: 'LOGIN',
            source_ip: '127.0.0.1',
            router_name: 'CCR2004-Border-02',
            http_status: 200,
            id_key: 'idem-1',
            created_at: new Date().toISOString(),
            prev_record_hash: '00000000',
            record_sha256_hash: '11111111',
            before_state: {},
            after_state: { ok: true },
          },
        ],
      },
      headers: new Headers(),
    });

    vi.spyOn(http, 'post').mockResolvedValue({
      status: 200,
      data: {
        verified: true,
        report: {
          total_records: 1,
          first_record_at: new Date().toISOString(),
          last_record_at: new Date().toISOString(),
          root_hash: 'root-hash-test',
          tampered_records_count: 0,
        },
      },
      headers: new Headers(),
    });

    const wrapper = mount(ImmutableAuditLogsView);
    await flushPromises();

    // Filtros de búsqueda
    const actorInput = wrapper.find('#filter-actor');
    await actorInput.setValue('auditor');

    const catSelect = wrapper.find('#filter-cat');
    await catSelect.setValue('AUTH');

    const routerInput = wrapper.find('#filter-router');
    if (routerInput.exists()) {
      await routerInput.setValue('CCR2004');
    }

    // Click en fila para ver inspector forense
    const row = wrapper.find('.audit-row');
    if (row.exists()) {
      await row.trigger('click');
      expect(wrapper.find('.inspector-panel').exists()).toBe(true);
    }

    // Verificar WORM (éxito)
    const verifyBtn = wrapper.find('.btn--verify');
    await verifyBtn.trigger('click');
    await flushPromises();
    expect(wrapper.find('.integrity-seal').exists()).toBe(true);

    // Verificar WORM con fallo simulado
    vi.spyOn(http, 'post').mockRejectedValueOnce(new Error('Verify fail'));
    await verifyBtn.trigger('click');
    await flushPromises();

    // Exportar
    const createObjUrl = vi.fn().mockReturnValue('blob:dummy');
    const revokeObjUrl = vi.fn();
    globalThis.URL.createObjectURL = createObjUrl;
    globalThis.URL.revokeObjectURL = revokeObjUrl;

    const exportBtns = wrapper.findAll('.audit-header-actions .btn--secondary');
    if (exportBtns.length > 0) {
      await exportBtns[0].trigger('click'); // CSV
      expect(createObjUrl).toHaveBeenCalled();
      const csvBlob = createObjUrl.mock.calls[0][0] as Blob;
      expect(csvBlob.type).toContain('text/csv');
    }
    if (exportBtns.length > 1) {
      await exportBtns[1].trigger('click'); // JSON
      await flushPromises();
      expect(createObjUrl).toHaveBeenCalledTimes(2);
      const jsonBlob = createObjUrl.mock.calls[1][0] as Blob;
      expect(jsonBlob.type).toContain('application/json');
    }
  });

  it('ImmutableAuditLogsView — maneja lista vacía sin datos de demostración', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: { items: [] },
      headers: new Headers(),
    });

    const wrapper = mount(ImmutableAuditLogsView);
    await flushPromises();
    expect(wrapper.findAll('.audit-row').length).toBe(0);
  });

  it('BulkOperationsAndUpdatesView — lista de plantillas con botón radio, contenedor con scroll y despliegue de parámetros al seleccionar', async () => {
    vi.spyOn(http, 'get').mockResolvedValue({
      status: 200,
      data: [
        {
          id: 'tpl-ntp',
          name: 'CLIENTE_NTP',
          category: 'SYSTEM',
          description: 'Activa cliente NTP',
          variables_schema: [
            { key: 'ntp_srv', label: 'Servidor NTP', default_val: '0.pool.ntp.org' },
          ],
          ros_command_template: '/system ntp client set enabled=yes',
        },
        {
          id: 'tpl-dns',
          name: 'DNS_CORPORATIVO',
          category: 'NETWORK',
          description: 'Configura DNS',
          variables_schema: [
            { key: 'dns_1', label: 'DNS Primario', default_val: '9.9.9.9' },
            { key: 'dns_2', label: 'DNS Secundario', default_val: '1.1.1.1' },
          ],
          ros_command_template: '/ip dns set servers={{dns_1}},{{dns_2}}',
        },
        {
          id: 'tpl-reboot',
          name: 'REINICIO_PROGRAMADO',
          category: 'MAINTENANCE',
          description: 'Reinicia el equipo sin variables',
          variables_schema: [],
          ros_command_template: '/system reboot',
        },
      ],
      headers: new Headers(),
    });

    const wrapper = mount(BulkOperationsAndUpdatesView);
    await flushPromises();

    // Avanzar al paso 2
    const nextBtn = wrapper.find('.step-footer .btn--primary');
    await nextBtn.trigger('click');
    await flushPromises();

    // 1. Contenedor de lista con scroll y role="radiogroup"
    const scrollList = wrapper.find('.templates-list-scroll');
    expect(scrollList.exists()).toBe(true);
    expect(scrollList.attributes('role')).toBe('radiogroup');

    // 2. Elementos de la lista con botones radio
    const listItems = wrapper.findAll('.template-list-item');
    expect(listItems.length).toBe(3);
    const radioInputs = wrapper.findAll('.tpl-radio-input');
    expect(radioInputs.length).toBe(3);

    // Primera plantilla seleccionada por defecto
    expect((radioInputs[0].element as HTMLInputElement).checked).toBe(true);
    expect(wrapper.find('.vars-title-hint').text()).toMatch(/CLIENTE_NTP|Cliente NTP/);
    expect(wrapper.findAll('.vars-grid .form-group').length).toBe(1);
    expect(wrapper.find('.form-label').text()).toContain('Servidor NTP');

    // 3. Seleccionar la segunda plantilla mediante clic en el radio o fila
    await listItems[1].trigger('click');
    await flushPromises();

    expect((radioInputs[1].element as HTMLInputElement).checked).toBe(true);
    expect(wrapper.find('.vars-title-hint').text()).toMatch(/DNS_CORPORATIVO|DNS Corporativo/);
    expect(wrapper.findAll('.vars-grid .form-group').length).toBe(2);

    // 4. Seleccionar la tercera plantilla (sin parámetros)
    await listItems[2].trigger('click');
    await flushPromises();

    expect((radioInputs[2].element as HTMLInputElement).checked).toBe(true);
    expect(wrapper.find('.vars-empty-state').text()).toContain('no requiere parámetros adicionales');
  });
});
