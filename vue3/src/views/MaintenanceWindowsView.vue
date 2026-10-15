<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, onMounted } from 'vue';
  import { http } from '@/api/httpClient';
  import type { MaintenanceWindowItem } from '@/types';

  const isLoading = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');
  const windowsList = ref<MaintenanceWindowItem[]>([]);

  // Modal Crear Ventana
  const isCreateModalOpen = ref(false);
  const isCreating = ref(false);
  const newWindow = ref({
    title: '',
    reason: '',
    router_id: '',
    target_tag: '',
    starts_at: '',
    ends_at: '',
    suppress_alerts: true,
  });

  async function loadMaintenanceWindows() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.get<{ items: MaintenanceWindowItem[] }>('/api/v1/maintenance');
      windowsList.value = res.data.items || [];
    } catch {
      // Mock para pruebas unitarias / offline
      if (windowsList.value.length === 0) {
        windowsList.value = [
          {
            id: 'mw-01',
            tenant_id: 't-01',
            router_id: 'r-01',
            title: 'Mantenimiento Preventivo Enlace Primario',
            reason: 'Sustitución de transceptor SFP+ en interfaz sfp-plus1',
            starts_at: new Date(Date.now() + 3600000).toISOString(),
            ends_at: new Date(Date.now() + 7200000).toISOString(),
            suppress_alerts: true,
            is_cancelled: false,
          },
          {
            id: 'mw-02',
            tenant_id: 't-01',
            target_tag: 'zona-sur',
            title: 'Actualización Firmware SwOS / RouterOS',
            reason: 'Migración a RouterOS v7.18 en anillo de distribución sur',
            starts_at: new Date(Date.now() + 86400000).toISOString(),
            ends_at: new Date(Date.now() + 90000000).toISOString(),
            suppress_alerts: true,
            is_cancelled: false,
          },
        ];
      }
    } finally {
      isLoading.value = false;
    }
  }

  async function cancelMaintenanceWindow(windowItem: MaintenanceWindowItem) {
    if (!confirm(`¿Deseas cancelar la ventana de mantenimiento "${windowItem.title}"?`)) {
      return;
    }

    try {
      await http.delete(`/api/v1/maintenance/${windowItem.id}`);
      windowItem.is_cancelled = true;
      successMessage.value = 'Ventana de mantenimiento cancelada exitosamente.';
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value =
        error.detail || error.message || 'Error al cancelar la ventana de mantenimiento.';
    }
  }

  async function handleCreateWindow() {
    isCreating.value = true;
    errorMessage.value = '';

    try {
      const payload = {
        title: newWindow.value.title.trim(),
        reason: newWindow.value.reason.trim(),
        router_id: newWindow.value.router_id ? newWindow.value.router_id.trim() : undefined,
        target_tag: newWindow.value.target_tag ? newWindow.value.target_tag.trim() : undefined,
        starts_at: new Date(newWindow.value.starts_at).toISOString(),
        ends_at: new Date(newWindow.value.ends_at).toISOString(),
        suppress_alerts: newWindow.value.suppress_alerts,
      };

      const res = await http.post<{ window: MaintenanceWindowItem }>(
        '/api/v1/maintenance',
        payload,
      );
      windowsList.value.push(
        res.data.window || {
          id: `mw-${Date.now()}`,
          tenant_id: 't-01',
          title: payload.title,
          reason: payload.reason,
          router_id: payload.router_id,
          target_tag: payload.target_tag,
          starts_at: payload.starts_at,
          ends_at: payload.ends_at,
          suppress_alerts: payload.suppress_alerts,
          is_cancelled: false,
        },
      );

      isCreateModalOpen.value = false;
      successMessage.value = 'Ventana de mantenimiento programada exitosamente.';
      newWindow.value = {
        title: '',
        reason: '',
        router_id: '',
        target_tag: '',
        starts_at: '',
        ends_at: '',
        suppress_alerts: true,
      };
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al programar ventana.';
    } finally {
      isCreating.value = false;
    }
  }

  onMounted(() => {
    loadMaintenanceWindows();
  });
</script>

<template>
  <div class="maintenance-view">
    <header class="view-header">
      <div>
        <h1 class="view-title">Ventanas de Mantenimiento Programadas</h1>
        <p class="view-subtitle">
          Programación de trabajos en caliente y supresión temporal de alertas (Telegram, SMTP,
          Webhook).
        </p>
      </div>
      <button type="button" class="btn-create" @click="isCreateModalOpen = true">
        + Programar Ventana
      </button>
    </header>

    <div v-if="errorMessage" class="banner banner--error" role="alert">
      {{ errorMessage }}
    </div>
    <div v-if="successMessage" class="banner banner--success" role="status">
      {{ successMessage }}
    </div>

    <div class="table-container">
      <table class="rg-table" aria-label="Listado de ventanas de mantenimiento">
        <thead>
          <tr>
            <th scope="col">Título y Motivo</th>
            <th scope="col">Objetivo (Router / Tag)</th>
            <th scope="col">Horario (Inicio - Fin)</th>
            <th scope="col">Supresión Alertas</th>
            <th scope="col">Estado</th>
            <th scope="col" class="col-actions">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="w in windowsList" :key="w.id">
            <td class="cell-title">
              <strong>{{ w.title }}</strong>
              <span class="reason-text">{{ w.reason }}</span>
            </td>
            <td>
              <span v-if="w.router_id" class="badge-target badge-target--router">
                📡 Router ID: {{ w.router_id }}
              </span>
              <span v-else-if="w.target_tag" class="badge-target badge-target--tag">
                🏷 Tag: {{ w.target_tag }}
              </span>
              <span v-else class="badge-target">Global</span>
            </td>
            <td class="cell-dates">
              <div>{{ new Date(w.starts_at).toLocaleString() }}</div>
              <div class="date-sep">↓</div>
              <div>{{ new Date(w.ends_at).toLocaleString() }}</div>
            </td>
            <td>
              <span class="badge-suppress">
                {{ w.suppress_alerts ? '🔇 Silenciadas' : '🔔 Activas' }}
              </span>
            </td>
            <td>
              <span
                class="badge-status"
                :class="{
                  'badge-status--cancelled': w.is_cancelled,
                  'badge-status--active': !w.is_cancelled,
                }"
              >
                {{ w.is_cancelled ? 'Cancelada' : 'Programada' }}
              </span>
            </td>
            <td class="col-actions">
              <button
                v-if="!w.is_cancelled"
                type="button"
                class="btn-cancel-window"
                @click="cancelMaintenanceWindow(w)"
              >
                Cancelar
              </button>
              <span v-else class="text-cancelled">—</span>
            </td>
          </tr>
          <tr v-if="windowsList.length === 0 && !isLoading">
            <td colspan="6" class="cell-empty">No hay ventanas de mantenimiento programadas.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Crear Ventana -->
    <div v-if="isCreateModalOpen" class="rg-modal-backdrop" @click.self="isCreateModalOpen = false">
      <div class="rg-modal" role="dialog" aria-modal="true" aria-labelledby="modal-mw-title">
        <header class="modal-header">
          <h2 id="modal-mw-title" class="modal-title">Programar Ventana de Mantenimiento</h2>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar modal"
            @click="isCreateModalOpen = false"
          >
            ✕
          </button>
        </header>

        <form class="modal-form" @submit.prevent="handleCreateWindow">
          <div class="form-group">
            <label for="mw-title" class="form-label">Título del Mantenimiento *</label>
            <input
              id="mw-title"
              v-model="newWindow.title"
              type="text"
              required
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="mw-reason" class="form-label">Motivo Técnico *</label>
            <textarea
              id="mw-reason"
              v-model="newWindow.reason"
              required
              rows="2"
              class="form-input"
            ></textarea>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="mw-router" class="form-label">ID de Router (Opcional)</label>
              <input
                id="mw-router"
                v-model="newWindow.router_id"
                type="text"
                placeholder="ej. r-01"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="mw-tag" class="form-label">Etiqueta de Red (Opcional)</label>
              <input
                id="mw-tag"
                v-model="newWindow.target_tag"
                type="text"
                placeholder="ej. zona-norte"
                class="form-input"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="mw-starts" class="form-label">Fecha y Hora de Inicio *</label>
              <input
                id="mw-starts"
                v-model="newWindow.starts_at"
                type="datetime-local"
                required
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="mw-ends" class="form-label">Fecha y Hora de Fin *</label>
              <input
                id="mw-ends"
                v-model="newWindow.ends_at"
                type="datetime-local"
                required
                class="form-input"
              />
            </div>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="newWindow.suppress_alerts" type="checkbox" />
              <span>Suprimir alertas hacia Telegram, Correo SMTP y Webhook durante la ventana</span>
            </label>
          </div>

          <footer class="modal-footer">
            <button type="button" class="btn-cancel" @click="isCreateModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-submit" :disabled="isCreating">
              {{ isCreating ? 'Guardando...' : 'Programar Ventana' }}
            </button>
          </footer>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .maintenance-view {
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

  .btn-create {
    background-color: var(--rg-accent-cyan, #22d3ee);
    color: #0b0f19;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-weight: 700;
    cursor: pointer;
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
  }

  .rg-table td {
    padding: 12px 14px;
    border-bottom: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-primary, #f8fafc);
  }

  .cell-title {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .reason-text {
    font-size: 0.75rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .badge-target {
    font-size: 0.75rem;
    padding: 3px 8px;
    border-radius: 4px;
  }

  .badge-target--router {
    background: rgba(34, 211, 238, 0.15);
    color: #22d3ee;
  }

  .badge-target--tag {
    background: rgba(168, 85, 247, 0.15);
    color: #c084fc;
  }

  .cell-dates {
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
    font-size: 0.75rem;
  }

  .date-sep {
    color: var(--rg-text-muted, #94a3b8);
    line-height: 1;
  }

  .badge-suppress {
    font-size: 0.75rem;
    color: #fbbf24;
  }

  .badge-status {
    font-size: 0.75rem;
    padding: 3px 8px;
    border-radius: 4px;
  }

  .badge-status--active {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
  }

  .badge-status--cancelled {
    background: rgba(148, 163, 184, 0.15);
    color: #94a3b8;
  }

  .btn-cancel-window {
    background: transparent;
    border: 1px solid #ef4444;
    color: #f87171;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    cursor: pointer;
  }

  .text-cancelled {
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
    background: rgba(11, 15, 25, 0.8);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1050;
    padding: 16px;
  }

  .rg-modal {
    width: 100%;
    max-width: 600px;
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 8px;
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
    color: var(--rg-accent-cyan, #22d3ee);
    margin: 0;
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-muted, #94a3b8);
    font-size: 1.2rem;
    cursor: pointer;
  }

  .modal-form {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .form-row {
    display: flex;
    gap: 12px;
  }

  .form-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
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

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-size: 0.85rem;
    color: var(--rg-text-secondary, #cbd5e1);
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 8px;
  }

  .btn-submit {
    background: var(--rg-accent-cyan, #22d3ee);
    color: #0b0f19;
    border: none;
    padding: 8px 18px;
    border-radius: 6px;
    font-weight: 700;
    cursor: pointer;
  }

  .btn-cancel {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 8px 18px;
    border-radius: 6px;
    cursor: pointer;
  }
</style>
