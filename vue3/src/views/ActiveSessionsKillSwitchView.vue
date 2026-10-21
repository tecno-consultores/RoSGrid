<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
  import { http } from '@/api/httpClient';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useNocEventsStore } from '@/stores/useNocEventsStore';
  import type { ActiveSessionItem, SystemRole } from '@/types';

  const authStore = useAuthStore();
  const nocEventsStore = useNocEventsStore();

  const isOperator = computed(() => {
    const r = authStore.currentRole;
    return r === 'SUPERADMIN_GLOBAL' || r === 'TENANT_ADMIN' || r === 'SUPERVISOR';
  });

  const isLoading = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');
  const sessions = ref<ActiveSessionItem[]>([]);
  const isRevoking = ref(false);

  // Filtros de Sesiones (Humanos vs Agentes IA MCP)
  type SessionFilterType = 'ALL' | 'HUMAN' | 'MCP';
  const currentFilter = ref<SessionFilterType>('ALL');

  const mcpSessionsCount = computed(
    () => sessions.value.filter((s) => s.is_service_account || s.role === 'SERVICE_ACCOUNT').length,
  );
  const humanSessionsCount = computed(
    () =>
      sessions.value.filter((s) => !s.is_service_account && s.role !== 'SERVICE_ACCOUNT').length,
  );
  const filteredSessions = computed(() => {
    if (currentFilter.value === 'MCP') {
      return sessions.value.filter((s) => s.is_service_account || s.role === 'SERVICE_ACCOUNT');
    }
    if (currentFilter.value === 'HUMAN') {
      return sessions.value.filter((s) => !s.is_service_account && s.role !== 'SERVICE_ACCOUNT');
    }
    return sessions.value;
  });

  // Modal para revocar con motivo
  const isRevokeModalOpen = ref(false);
  const sessionToRevoke = ref<ActiveSessionItem | null>(null);
  const revokeReason = ref('');
  const revokeAllForUser = ref(false);

  let pollInterval: ReturnType<typeof setInterval> | null = null;

  function asString(val: unknown, fallback = ''): string {
    return typeof val === 'string' && val.length > 0 ? val : fallback;
  }

  function calculateSecondsSince(item: Record<string, unknown>): number {
    if (typeof item.seconds_since_active === 'number') {
      return item.seconds_since_active;
    }
    if (item.last_activity_at) {
      const elapsed = (Date.now() - new Date(String(item.last_activity_at)).getTime()) / 1000;
      return Math.max(0, Math.floor(elapsed));
    }
    return 0;
  }

  function parseSessionItem(item: Record<string, unknown>): ActiveSessionItem {
    const nowIso = new Date().toISOString();
    return {
      session_id: asString(item.session_id),
      user_id: asString(item.user_id),
      username: asString(item.username, 'unknown'),
      full_name: typeof item.full_name === 'string' ? item.full_name : undefined,
      role: (item.role || 'GUEST') as SystemRole,
      ip_address: asString(item.ip_address, '127.0.0.1'),
      user_agent: asString(item.user_agent),
      current_router_id:
        typeof item.current_router_id === 'string' ? item.current_router_id : undefined,
      current_router_name:
        typeof item.current_router_name === 'string' ? item.current_router_name : undefined,
      current_view_path:
        typeof item.current_view_path === 'string' ? item.current_view_path : undefined,
      created_at: asString(item.created_at, asString(item.login_at, nowIso)),
      last_active_at: asString(item.last_active_at, asString(item.last_activity_at, nowIso)),
      seconds_since_active: calculateSecondsSince(item),
      is_service_account: Boolean(item.is_service_account || item.role === 'SERVICE_ACCOUNT'),
      issued_by_username:
        typeof item.issued_by_username === 'string' ? item.issued_by_username : undefined,
      allowed_cidr_list: Array.isArray(item.allowed_cidr_list)
        ? (item.allowed_cidr_list as string[])
        : undefined,
    };
  }

  async function loadActiveSessions() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.get<{ items?: ActiveSessionItem[] } | ActiveSessionItem[]>(
        '/api/v1/sessions/active',
      );
      const raw = ((Array.isArray(res.data) ? res.data : res.data?.items || []) as unknown) as Array<
        Record<string, unknown>
      >;
      sessions.value = raw.map(parseSessionItem);
    } catch {
      // Sin datos de demostración en producción
      sessions.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  function parseUserAgent(ua: string, isMcp?: boolean): string {
    if (isMcp || ua.includes('MCP') || ua.includes('Daemon')) {
      return '🤖 Agente IA (MCP)';
    }
    if (ua.includes('iPhone') || ua.includes('Android') || ua.includes('Mobile')) {
      return '📱 Móvil / Tablet';
    }
    if (ua.includes('Linux')) {
      return '🐧 Linux PC';
    }
    if (ua.includes('Windows')) {
      return '🪟 Windows PC';
    }
    if (ua.includes('Macintosh')) {
      return '🍎 macOS';
    }
    return '💻 Navegador Web';
  }

  function openRevokeModal(session: ActiveSessionItem, allDevices = false) {
    sessionToRevoke.value = session;
    revokeAllForUser.value = allDevices;
    if (session.is_service_account || session.role === 'SERVICE_ACCOUNT') {
      revokeReason.value = 'Revocación de credenciales del Agente MCP (Kill-Switch)';
    } else {
      revokeReason.value = allDevices
        ? 'Comportamiento sospechoso o bloqueo de cuenta'
        : 'Cierre forzado de sesión';
    }
    isRevokeModalOpen.value = true;
  }

  async function handleConfirmRevoke() {
    if (!sessionToRevoke.value) return;
    isRevoking.value = true;
    errorMessage.value = '';

    try {
      if (revokeAllForUser.value) {
        await http.delete(`/api/v1/sessions/user/${sessionToRevoke.value.user_id}/all`);
        sessions.value = sessions.value.filter((s) => s.user_id !== sessionToRevoke.value?.user_id);
        successMessage.value = `Todas las sesiones de @${sessionToRevoke.value.username} han sido revocadas.`;
      } else {
        await http.delete(`/api/v1/sessions/${sessionToRevoke.value.session_id}`);
        sessions.value = sessions.value.filter(
          (s) => s.session_id !== sessionToRevoke.value?.session_id,
        );
        successMessage.value = `Sesión ${sessionToRevoke.value.session_id} revocada exitosamente.`;
      }

      isRevokeModalOpen.value = false;
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value =
        error.detail || error.message || 'Error al ejecutar la orden Kill-Switch.';
    } finally {
      isRevoking.value = false;
    }
  }

  onMounted(() => {
    loadActiveSessions();
    nocEventsStore.connectEventsWebSocket();
    // Sondeo de respaldo cada 30 segundos
    pollInterval = setInterval(() => {
      loadActiveSessions();
    }, 30000);
  });

  onBeforeUnmount(() => {
    if (pollInterval) {
      clearInterval(pollInterval);
    }
  });
</script>

<template>
  <div class="sessions-view">
    <header class="view-header">
      <div>
        <h1 class="view-title">Sesiones Activas y Kill-Switch en Tiempo Real</h1>
        <p class="view-subtitle">
          Supervisión de sesiones abiertas en KeyDB y contención instantánea de acceso operativo.
        </p>
      </div>

      <div class="header-actions">
        <button
          type="button"
          class="btn-refresh"
          aria-label="Actualizar listado de sesiones"
          :disabled="isLoading"
          @click="loadActiveSessions"
        >
          🔄 Refrescar
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="banner banner--error" role="alert">
      {{ errorMessage }}
    </div>
    <div v-if="successMessage" class="banner banner--success" role="status">
      {{ successMessage }}
    </div>

    <!-- Selector de Filtros: Humanos vs Agentes IA MCP -->
    <div class="session-filters">
      <button
        type="button"
        class="filter-tab"
        :class="{ 'filter-tab--active': currentFilter === 'ALL' }"
        @click="currentFilter = 'ALL'"
      >
        🌐 Todas las Sesiones ({{ sessions.length }})
      </button>
      <button
        type="button"
        class="filter-tab"
        :class="{ 'filter-tab--active': currentFilter === 'HUMAN' }"
        @click="currentFilter = 'HUMAN'"
      >
        👤 Operadores Humanos ({{ humanSessionsCount }})
      </button>
      <button
        type="button"
        class="filter-tab filter-tab--mcp"
        :class="{ 'filter-tab--active': currentFilter === 'MCP' }"
        @click="currentFilter = 'MCP'"
      >
        🤖 Agentes IA MCP ({{ mcpSessionsCount }})
      </button>
    </div>

    <div class="table-container">
      <table class="rg-table" aria-label="Tabla de sesiones activas en KeyDB">
        <thead>
          <tr>
            <th scope="col">Operador / Agente IA</th>
            <th scope="col">Origen IP y Dispositivo</th>
            <th scope="col">Actividad en Vivo (MikroTik / MCP)</th>
            <th scope="col">Última Acción</th>
            <th scope="col">Inicio de Sesión</th>
            <th scope="col" class="col-actions">Acciones Kill-Switch</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in filteredSessions" :key="s.session_id">
            <td class="cell-user">
              <div class="user-name-line">
                <strong>{{ s.full_name || s.username }}</strong>
                <span
                  v-if="s.is_service_account"
                  class="badge-mcp-tag"
                  title="Agente IA conectado vía MCP"
                >
                  🤖 MCP
                </span>
              </div>
              <div class="user-meta">
                <code>@{{ s.username }}</code>
                <span class="badge-role">{{ s.role }}</span>
                <span
                  v-if="s.issued_by_username"
                  class="badge-lineage"
                  title="Administrador que emitió el token"
                >
                  Por: @{{ s.issued_by_username }}
                </span>
              </div>
            </td>
            <td class="cell-origin">
              <span class="ip-address">{{ s.ip_address || '127.0.0.1' }}</span>
              <span class="user-agent">{{
                parseUserAgent(s.user_agent, s.is_service_account)
              }}</span>
              <span v-if="s.allowed_cidr_list && s.allowed_cidr_list.length > 0" class="cidr-list">
                CIDR: {{ s.allowed_cidr_list.join(', ') }}
              </span>
            </td>
            <td class="cell-activity">
              <span v-if="s.is_service_account" class="mcp-live-indicator">
                ⚡ Invocaciones JSON-RPC 2.0 (/api/v1/mcp)
              </span>
              <template v-else-if="s.current_router_name">
                <router-link
                  :to="s.current_view_path || `/routers/${s.current_router_id}/webfig`"
                  class="router-link"
                >
                  📡 {{ s.current_router_name }}
                </router-link>
                <span class="view-path">{{ s.current_view_path }}</span>
              </template>
              <span v-else class="text-idle">En espera / Navegando inventario</span>
            </td>
            <td class="cell-time">
              hace <strong>{{ s.seconds_since_active }}s</strong>
            </td>
            <td class="cell-time">
              {{ new Date(s.created_at).toLocaleTimeString() }}
            </td>
            <td class="col-actions">
              <div v-if="isOperator" class="action-buttons">
                <button
                  type="button"
                  class="btn-kill-session"
                  :class="{ 'btn-kill-session--mcp': s.is_service_account }"
                  :aria-label="
                    s.is_service_account
                      ? 'Revocar Token MCP de este agente'
                      : 'Revocar esta sesión individual'
                  "
                  @click="openRevokeModal(s, false)"
                >
                  {{ s.is_service_account ? '🛑 Revocar Token' : 'Revocar' }}
                </button>
                <button
                  v-if="!s.is_service_account"
                  type="button"
                  class="btn-kill-user"
                  aria-label="Expulsar de todos los dispositivos y bloquear"
                  @click="openRevokeModal(s, true)"
                >
                  Expulsar Todo
                </button>
              </div>
              <span v-else class="text-readonly">Solo Lectura</span>
            </td>
          </tr>
          <tr v-if="filteredSessions.length === 0 && !isLoading">
            <td colspan="6" class="cell-empty">
              {{
                currentFilter === 'MCP'
                  ? 'No hay agentes MCP activos registrados en KeyDB.'
                  : currentFilter === 'HUMAN'
                    ? 'No hay operadores humanos conectados en este momento.'
                    : 'No hay sesiones activas registradas en KeyDB.'
              }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal de Confirmación Kill-Switch -->
    <div v-if="isRevokeModalOpen" class="rg-modal-backdrop" @click.self="isRevokeModalOpen = false">
      <div class="rg-modal" role="dialog" aria-modal="true" aria-labelledby="modal-kill-title">
        <header class="modal-header">
          <h2 id="modal-kill-title" class="modal-title">
            {{ revokeAllForUser ? '⚠️ Kill-Switch Total de Usuario' : 'Revocar Sesión Individual' }}
          </h2>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar modal"
            @click="isRevokeModalOpen = false"
          >
            ✕
          </button>
        </header>

        <div class="modal-body">
          <p class="warning-text">
            Esta acción invalidará de inmediato las llaves de sesión en KeyDB y cerrará la interfaz
            en vivo del técnico.
          </p>

          <div v-if="sessionToRevoke" class="target-info">
            <div>
              Operador: <strong>@{{ sessionToRevoke.username }}</strong>
            </div>
            <div>
              IP de Origen: <code>{{ sessionToRevoke.ip_address }}</code>
            </div>
            <div v-if="sessionToRevoke.current_router_name">
              Router Actual: <strong>{{ sessionToRevoke.current_router_name }}</strong>
            </div>
          </div>

          <div class="form-group">
            <label for="revoke-reason" class="form-label">
              Motivo de Revocación (Quedará registrado en Auditoría WORM):
            </label>
            <input
              id="revoke-reason"
              v-model="revokeReason"
              type="text"
              class="form-input"
              placeholder="ej. Sesión sospechosa fuera de horario"
            />
          </div>
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn-cancel" @click="isRevokeModalOpen = false">
            Cancelar
          </button>
          <button
            type="button"
            class="btn-confirm-kill"
            :disabled="isRevoking"
            @click="handleConfirmRevoke"
          >
            {{
              isRevoking
                ? 'Revocando...'
                : revokeAllForUser
                  ? 'Confirmar Expulsión Total'
                  : 'Confirmar Revocación'
            }}
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .sessions-view {
    padding: 24px;
    background-color: var(--rg-bg-canvas, #0b0f19);
    min-height: 100%;
  }

  .view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 16px;
  }

  .view-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--rg-accent-cyan, #22d3ee);
    margin: 0;
  }

  .view-subtitle {
    font-size: 0.85rem;
    color: var(--rg-text-muted, #94a3b8);
    margin: 4px 0 0 0;
  }

  .btn-refresh {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-primary, #f8fafc);
    padding: 8px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.85rem;
  }

  .banner {
    padding: 12px 16px;
    border-radius: 6px;
    margin-bottom: 16px;
    font-size: 0.85rem;
  }

  .banner--error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #f87171;
  }

  .banner--success {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #34d399;
  }

  .table-container {
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 8px;
    overflow-x: auto;
  }

  .rg-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    text-align: left;
  }

  .rg-table th {
    background-color: var(--rg-bg-elevated, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 10px 14px;
    border-bottom: 1px solid var(--rg-border-grid, #334155);
    white-space: nowrap;
  }

  .rg-table td {
    padding: 12px 14px;
    border-bottom: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-primary, #f8fafc);
  }

  .cell-user {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .user-meta {
    display: flex;
    gap: 6px;
    align-items: center;
  }

  .badge-role {
    font-size: 0.7rem;
    background: rgba(34, 211, 238, 0.12);
    color: #22d3ee;
    padding: 2px 6px;
    border-radius: 4px;
  }

  .cell-origin {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .ip-address {
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
  }

  .user-agent {
    font-size: 0.75rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .cell-activity {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .router-link {
    color: var(--rg-accent-cyan, #22d3ee);
    text-decoration: none;
    font-weight: 600;
  }

  .router-link:hover {
    text-decoration: underline;
  }

  .view-path {
    font-size: 0.75rem;
    color: var(--rg-text-muted, #94a3b8);
    font-family: 'JetBrains Mono', monospace;
  }

  .text-idle {
    font-size: 0.8rem;
    color: var(--rg-text-muted, #94a3b8);
    font-style: italic;
  }

  .cell-time {
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
  }

  .action-buttons {
    display: flex;
    gap: 6px;
  }

  .btn-kill-session {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #f87171;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    cursor: pointer;
  }

  .btn-kill-session:hover {
    background: #ef4444;
    color: #ffffff;
  }

  .btn-kill-user {
    background: #7f1d1d;
    border: 1px solid #dc2626;
    color: #fca5a5;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    cursor: pointer;
  }

  .btn-kill-user:hover {
    background: #dc2626;
    color: #ffffff;
  }

  .text-readonly {
    font-size: 0.75rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .cell-empty {
    text-align: center;
    padding: 32px;
    color: var(--rg-text-muted, #94a3b8);
  }

  .rg-modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(11, 15, 25, 0.85);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1050;
    padding: 16px;
  }

  .rg-modal {
    width: 100%;
    max-width: 520px;
    background: var(--rg-bg-surface, #111827);
    border: 1px solid #ef4444;
    border-radius: 8px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.7);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid var(--rg-border-grid, #1e293b);
  }

  .modal-title {
    font-size: 1.15rem;
    color: #f87171;
    margin: 0;
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-muted, #94a3b8);
    font-size: 1.2rem;
    cursor: pointer;
  }

  .modal-body {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .warning-text {
    font-size: 0.85rem;
    color: #fca5a5;
    margin: 0;
  }

  .target-info {
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .form-label {
    font-size: 0.8rem;
    color: var(--rg-text-secondary, #cbd5e1);
  }

  .form-input {
    padding: 8px 12px;
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    color: var(--rg-text-primary, #f8fafc);
    font-size: 0.85rem;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 20px;
    border-top: 1px solid var(--rg-border-grid, #1e293b);
  }

  .btn-cancel {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 8px 18px;
    border-radius: 6px;
    cursor: pointer;
  }

  .btn-confirm-kill {
    background: #ef4444;
    color: #ffffff;
    border: none;
    padding: 8px 18px;
    border-radius: 6px;
    font-weight: 700;
    cursor: pointer;
  }

  .btn-confirm-kill:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  /* Filtros de Sesiones */
  .session-filters {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    flex-wrap: wrap;
  }

  .filter-tab {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-muted, #94a3b8);
    padding: 7px 14px;
    border-radius: 6px;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .filter-tab:hover {
    color: var(--rg-text-primary, #f8fafc);
    border-color: #334155;
  }

  .filter-tab--active {
    background: rgba(34, 211, 238, 0.12);
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
  }

  .filter-tab--mcp.filter-tab--active {
    background: rgba(168, 85, 247, 0.15);
    border-color: #a855f7;
    color: #c084fc;
  }

  /* Elementos Visuales MCP */
  .user-name-line {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .badge-mcp-tag {
    background: rgba(168, 85, 247, 0.15);
    color: #c084fc;
    border: 1px solid #9333ea;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.5px;
  }

  .badge-lineage {
    background: rgba(34, 211, 238, 0.1);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.3);
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 500;
  }

  .cidr-list {
    display: block;
    font-size: 0.72rem;
    color: #10b981;
    font-family: monospace;
    margin-top: 2px;
  }

  .mcp-live-indicator {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 0.78rem;
    font-weight: 600;
    color: #a855f7;
    font-family: monospace;
    background: rgba(168, 85, 247, 0.08);
    padding: 3px 8px;
    border-radius: 4px;
    border: 1px solid rgba(168, 85, 247, 0.25);
  }

  .btn-kill-session--mcp {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fca5a5;
    font-weight: 700;
  }

  .btn-kill-session--mcp:hover {
    background: #ef4444;
    color: #ffffff;
  }
</style>
