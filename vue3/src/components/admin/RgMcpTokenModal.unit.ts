// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import RgMcpTokenModal from './RgMcpTokenModal.vue';
import { http, type ApiResponse } from '@/api/httpClient';
import type { UserManagementItem, McpTokenResponse } from '@/types';

const MOCK_USER_ID = 'usr-1111-2222-3333-4444';
const MOCK_USERNAME = 'ai-agent-noc';

const mockUser: UserManagementItem = {
  id: MOCK_USER_ID,
  username: MOCK_USERNAME,
  email: 'hermes@rosgrid.local',
  full_name: 'Hermes AI Assistant',
  role: 'SERVICE_ACCOUNT',
  is_active: true,
  allowed_cidr_list: ['10.0.0.0/24'],
  totp_enabled: false,
  has_all_routers_access: true,
  created_at: '2026-01-01T00:00:00Z',
};

const mockMcpResponse: McpTokenResponse = {
  token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mocktoken',
  token_type: 'Bearer',
  session_id: 'sid-mcp-9999-8888',
  expires_at: '2027-10-20T00:00:00Z',
  expiry_days: 365,
  user_id: MOCK_USER_ID,
  username: MOCK_USERNAME,
  tenant_slug: 'corp-noc',
  role: 'SERVICE_ACCOUNT',
  allowed_cidr_list: ['10.0.0.0/24'],
  issued_by: 'admin-alice',
};

describe('RgMcpTokenModal.vue — Emisión de Tokens MCP para Agentes IA', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('no se renderiza en el DOM cuando isOpen es false', () => {
    const wrapper = mount(RgMcpTokenModal, {
      props: {
        isOpen: false,
        user: mockUser,
      },
    });

    expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(false);
  });

  it('se renderiza correctamente cuando isOpen es true mostrando datos del usuario', () => {
    const wrapper = mount(RgMcpTokenModal, {
      props: {
        isOpen: true,
        user: mockUser,
      },
    });

    expect(wrapper.find('.rg-modal-backdrop').exists()).toBe(true);
    expect(wrapper.text()).toContain('Generador de Token MCP (Agentes IA)');
    expect(wrapper.text()).toContain(MOCK_USERNAME);
    expect(wrapper.text()).toContain('SERVICE_ACCOUNT');
  });

  it('permite cambiar la vigencia usando el selector', async () => {
    const wrapper = mount(RgMcpTokenModal, {
      props: {
        isOpen: true,
        user: mockUser,
      },
    });

    const select = wrapper.find<HTMLSelectElement>('#expiry-selector');
    expect(select.exists()).toBe(true);
    await select.setValue(90);

    expect(select.element.value).toBe('90');
  });

  it('emite el token llamando a POST /api/v1/users/{userId}/mcp-token', async () => {
    const postSpy = vi.spyOn(http, 'post').mockResolvedValueOnce({
      data: mockMcpResponse,
      status: 200,
      headers: new Headers(),
    } as unknown as ApiResponse);

    const wrapper = mount(RgMcpTokenModal, {
      props: {
        isOpen: true,
        user: mockUser,
      },
    });

    // Hacer submit del formulario
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    expect(postSpy).toHaveBeenCalledWith(
      `/api/v1/users/${MOCK_USER_ID}/mcp-token`,
      { expiry_days: 365 },
      expect.anything(),
    );

    // Debe mostrar la sección con el token generado y los snippets de Claude/Hermes
    expect(wrapper.text()).toContain(
      '¡Token Bearer MCP emitido y registrado en KeyDB exitosamente!',
    );
    expect(wrapper.find<HTMLInputElement>('#generated-token-input').element.value).toBe(
      mockMcpResponse.token,
    );
    expect(wrapper.text()).toContain('Configuración de Ejemplo para Claude Desktop y Hermes Agent');
    expect(wrapper.text()).toContain('claude_desktop_config.json');
    expect(wrapper.emitted('token-generated')).toBeTruthy();
    expect(wrapper.emitted('token-generated')?.[0]).toEqual([mockMcpResponse]);
  });

  it('muestra mensaje de error cuando la API rechaza la solicitud', async () => {
    vi.spyOn(http, 'post').mockRejectedValueOnce({
      detail: 'El usuario no pertenece a su Tenant o no tiene rol autorizado.',
    });

    const wrapper = mount(RgMcpTokenModal, {
      props: {
        isOpen: true,
        user: mockUser,
      },
    });

    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    expect(wrapper.text()).toContain('El usuario no pertenece a su Tenant');
  });

  it('emite evento close al hacer clic en el botón de cerrar', async () => {
    const wrapper = mount(RgMcpTokenModal, {
      props: {
        isOpen: true,
        user: mockUser,
      },
    });

    await wrapper.find('.btn-close').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('permite copiar la Skill oficial llamando a GET /api/v1/mcp/skill', async () => {
    const getSpy = vi.spyOn(http, 'get').mockResolvedValueOnce({
      data: '# Skill rosgrid-noc-operator markdown content',
      status: 200,
      headers: new Headers(),
    } as unknown as ApiResponse);

    const writeTextSpy = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextSpy,
      },
    });

    const wrapper = mount(RgMcpTokenModal, {
      props: {
        isOpen: true,
        user: mockUser,
      },
    });

    const copyBtn = wrapper.find('.btn-skill-mini');
    expect(copyBtn.exists()).toBe(true);
    await copyBtn.trigger('click');
    await flushPromises();

    expect(getSpy).toHaveBeenCalledWith('/api/v1/mcp/skill');
    expect(writeTextSpy).toHaveBeenCalledWith('# Skill rosgrid-noc-operator markdown content');
    expect(wrapper.text()).toContain('¡Copiada!');
  });

  it('permite descargar el archivo SKILL.md al hacer clic en Descargar', async () => {
    const createElementSpy = vi.spyOn(document, 'createElement');

    const wrapper = mount(RgMcpTokenModal, {
      props: {
        isOpen: true,
        user: mockUser,
      },
    });

    const downloadBtn = wrapper.findAll('.btn-skill-mini')[1];
    expect(downloadBtn.exists()).toBe(true);
    await downloadBtn.trigger('click');

    expect(createElementSpy).toHaveBeenCalledWith('a');
  });

  it('copia el contexto llms.txt con # Agent Instructions (ask y goal) y soporta los 6 clientes MCP (Hito 27.15)', async () => {
    vi.spyOn(http, 'post').mockResolvedValueOnce({
      data: mockMcpResponse,
      status: 200,
      headers: new Headers(),
    } as unknown as ApiResponse);

    const writeTextSpy = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextSpy,
      },
    });

    const wrapper = mount(RgMcpTokenModal, {
      props: {
        isOpen: true,
        user: mockUser,
      },
    });

    const llmsBtn = wrapper.find('#btn-copy-llms-context');
    expect(llmsBtn.exists()).toBe(true);
    await llmsBtn.trigger('click');
    expect(writeTextSpy).toHaveBeenCalled();
    const copiedLlms = writeTextSpy.mock.calls[0][0] as string;
    expect(copiedLlms).toContain('# Agent Instructions');
    expect(copiedLlms).toContain('- **ask**:');
    expect(copiedLlms).toContain('- **goal**:');
    expect(copiedLlms).toContain('rosgrid_list_routers');

    // Generar token y probar los 6 conectores de clientes MCP
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    const clientTabs = wrapper.findAll('.mcp-client-tab');
    expect(clientTabs.length).toBe(6);

    await wrapper.find('[data-client-id="claude-code"]').trigger('click');
    expect(wrapper.find('.snippet-pre').text()).toContain('claude mcp add --transport http rosgrid');

    await wrapper.find('[data-client-id="codex"]').trigger('click');
    expect(wrapper.find('.snippet-pre').text()).toContain('[mcp_servers.rosgrid]');

    await wrapper.find('[data-client-id="cursor"]').trigger('click');
    expect(wrapper.find('.snippet-pre').text()).toContain('"mcpServers"');

    await wrapper.find('[data-client-id="vscode"]').trigger('click');
    expect(wrapper.find('.snippet-pre').text()).toContain('"servers"');

    await wrapper.find('[data-client-id="hermes"]').trigger('click');
    expect(wrapper.find('.snippet-pre').text()).toContain('transport: streamable_http');
  });
});
