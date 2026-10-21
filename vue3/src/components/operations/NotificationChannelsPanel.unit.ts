// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import NotificationChannelsPanel from './NotificationChannelsPanel.vue';
import { http, type ApiResponse } from '@/api/httpClient';
import type { NotificationChannelItem, NotificationTestResponse } from '@/types';

const CH_TELEGRAM_ID = 'ch-telegram-1111-2222';
const TENANT_DEMO_ID = 'tenant-demo-1234';

const mockChannels: NotificationChannelItem[] = [
  {
    id: CH_TELEGRAM_ID,
    tenant_id: TENANT_DEMO_ID,
    name: 'Canal Alertas Telegram NOC',
    channel_type: 'TELEGRAM_BOT',
    is_enabled: true,
    subscribed_events: ['ROUTER_OFFLINE', 'ROUTER_ONLINE', 'DEGRADED_HIGH_LOAD'],
    created_at: '2026-02-15T10:00:00Z',
    updated_at: '2026-02-15T10:00:00Z',
  },
  {
    id: 'ch-smtp-3333-4444',
    tenant_id: TENANT_DEMO_ID,
    name: 'Servidor Correo SMTP Corporativo',
    channel_type: 'SMTP_EMAIL',
    is_enabled: false,
    subscribed_events: ['SSL_MISMATCH', 'CONFIG_DRIFT_DETECTED'],
    created_at: '2026-03-01T12:00:00Z',
    updated_at: '2026-03-01T12:00:00Z',
  },
];

describe('NotificationChannelsPanel.vue — Gestión de Canales de Alerta', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renderiza estado vacío cuando no existen canales configurados', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      data: [],
      status: 200,
      headers: new Headers(),
    } as unknown as ApiResponse);

    const wrapper = mount(NotificationChannelsPanel);
    await flushPromises();

    expect(wrapper.text()).toContain('No hay canales de notificación configurados');
    expect(wrapper.find('.empty-state').exists()).toBe(true);
  });

  it('lista los canales configurados mostrando tipo, estado y eventos suscritos', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      data: mockChannels,
      status: 200,
      headers: new Headers(),
    } as unknown as ApiResponse);

    const wrapper = mount(NotificationChannelsPanel);
    await flushPromises();

    expect(wrapper.find('.channels-grid').exists()).toBe(true);
    expect(wrapper.text()).toContain('Canal Alertas Telegram NOC');
    expect(wrapper.text()).toContain('Servidor Correo SMTP Corporativo');
    expect(wrapper.text()).toContain('Telegram Bot');
    expect(wrapper.text()).toContain('Correo SMTP');
    expect(wrapper.text()).toContain('ROUTER_OFFLINE');
    expect(wrapper.text()).toContain('SSL_MISMATCH');
  });

  it('permite alternar el estado activo/inactivo de un canal (PATCH)', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      data: [mockChannels[0]],
      status: 200,
      headers: new Headers(),
    } as unknown as ApiResponse);
    const patchSpy = vi.spyOn(http, 'patch').mockResolvedValueOnce({
      data: { ...mockChannels[0], is_enabled: false },
      status: 200,
      headers: new Headers(),
    } as unknown as ApiResponse);

    const wrapper = mount(NotificationChannelsPanel);
    await flushPromises();

    const toggleBtn = wrapper.find('.btn-toggle');
    expect(toggleBtn.text()).toContain('Desactivar');
    await toggleBtn.trigger('click');
    await flushPromises();

    expect(patchSpy).toHaveBeenCalledWith(
      `/api/v1/operations/notification-channels/${CH_TELEGRAM_ID}`,
      { is_enabled: false },
    );
  });

  it('abre el modal de prueba y despacha mensaje de test con éxito', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      data: [mockChannels[0]],
      status: 200,
      headers: new Headers(),
    } as unknown as ApiResponse);
    const testResponse: NotificationTestResponse = {
      status: 'SUCCESS',
      detail: 'Configuración de canal TELEGRAM_BOT validada con éxito',
    };
    const postSpy = vi.spyOn(http, 'post').mockResolvedValueOnce({
      data: testResponse,
      status: 200,
      headers: new Headers(),
    } as unknown as ApiResponse);

    const wrapper = mount(NotificationChannelsPanel);
    await flushPromises();

    // Clic en Probar
    const testBtn = wrapper.find('.btn-test');
    await testBtn.trigger('click');

    expect(wrapper.find('#test-channel-title').exists()).toBe(true);
    expect(wrapper.text()).toContain('Probar Canal: Canal Alertas Telegram NOC');

    // Despachar prueba
    const dispatchBtn = wrapper
      .findAll('.btn-tactical')
      .find((b) => b.text().includes('Despachar Prueba'));
    await dispatchBtn?.trigger('click');
    await flushPromises();

    expect(postSpy).toHaveBeenCalledWith(
      `/api/v1/operations/notification-channels/${CH_TELEGRAM_ID}/test`,
      expect.objectContaining({ message: expect.any(String) }),
    );
    expect(wrapper.text()).toContain('Despacho Exitoso');
    expect(wrapper.text()).toContain('Configuración de canal TELEGRAM_BOT validada con éxito');
  });

  it('permite registrar un nuevo canal en modal de creación (POST)', async () => {
    const webhookName = 'Webhook Discord NOC';
    vi.spyOn(http, 'get').mockResolvedValue({
      data: [],
      status: 200,
      headers: new Headers(),
    } as unknown as ApiResponse);
    const postSpy = vi.spyOn(http, 'post').mockResolvedValueOnce({
      data: {
        id: 'new-id-999',
        tenant_id: TENANT_DEMO_ID,
        name: webhookName,
        channel_type: 'GENERIC_WEBHOOK',
        is_enabled: true,
        subscribed_events: ['ROUTER_OFFLINE'],
        created_at: '2026-03-01T00:00:00Z',
        updated_at: '2026-03-01T00:00:00Z',
      },
      status: 201,
      headers: new Headers(),
    } as unknown as ApiResponse);

    const wrapper = mount(NotificationChannelsPanel);
    await flushPromises();

    // Abrir modal de creación
    const createBtn = wrapper
      .findAll('.btn-tactical')
      .find((b) => b.text().includes('Nuevo Canal'));
    await createBtn?.trigger('click');

    expect(wrapper.find('#create-channel-title').exists()).toBe(true);

    // Llenar campos
    await wrapper.find('#ch-name').setValue(webhookName);
    await wrapper.find('#ch-type').setValue('GENERIC_WEBHOOK');
    await wrapper.find('#webhook-url').setValue('https://discord.com/api/webhooks/123/xyz');

    // Enviar
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    expect(postSpy).toHaveBeenCalledWith(
      '/api/v1/operations/notification-channels',
      expect.objectContaining({
        name: webhookName,
        channel_type: 'GENERIC_WEBHOOK',
        config: expect.objectContaining({
          webhook_url: 'https://discord.com/api/webhooks/123/xyz',
        }),
      }),
    );
  });
});
