<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { http } from '@/api/httpClient';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import type { MaintenanceWindowItem } from '@/types';

  const inventoryStore = useInventoryStore();

  const isLoading = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');
  const windowsList = ref<MaintenanceWindowItem[]>([]);

  // Modal Crear Ventana
  const isCreateModalOpen = ref(false);
  const isCreating = ref(false);
  const scopeType = ref<'routers' | 'tag' | 'global'>('routers');
  const selectedRouterIds = ref<string[]>([]);
  const routerSearch = ref<string>('');

  const newWindow = ref({
    title: '',
    reason: '',
    target_tag: '',
    starts_at: '',
    ends_at: '',
    suppress_alerts: true,
  });

  function formatForDateTimeLocal(date: Date): string {
    const pad = (n: number) => String(n).padStart(2, '0');
    const yyyy = date.getFullYear();
    const mm = pad(date.getMonth() + 1);
    const dd = pad(date.getDate());
    const hh = pad(date.getHours());
    const min = pad(date.getMinutes());
    return `${yyyy}-${mm}-${dd}T${hh}:${min}`;
  }

  function initDefaultDates(): void {
    const now = new Date();
    now.setSeconds(0, 0);
    const remainder = now.getMinutes() % 5;
    if (remainder !== 0) {
      now.setMinutes(now.getMinutes() + (5 - remainder));
    }
    const twoHoursLater = new Date(now.getTime() + 2 * 60 * 60 * 1000);
    newWindow.value.starts_at = formatForDateTimeLocal(now);
    newWindow.value.ends_at = formatForDateTimeLocal(twoHoursLater);
  }

  function openCreateModal(): void {
    initDefaultDates();
    isCreateModalOpen.value = true;
  }

  function setDurationPreset(hours: number): void {
    const start = newWindow.value.starts_at ? new Date(newWindow.value.starts_at) : new Date();
    if (isNaN(start.getTime())) {
      initDefaultDates();
      return;
    }
    const end = new Date(start.getTime() + hours * 60 * 60 * 1000);
    newWindow.value.ends_at = formatForDateTimeLocal(end);
  }

  function setNightWindowPreset(): void {
    const start = new Date();
    if (start.getHours() >= 5) {
      start.setDate(start.getDate() + 1);
    }
    start.setHours(1, 0, 0, 0);
    const end = new Date(start);
    end.setHours(5, 0, 0, 0);
    newWindow.value.starts_at = formatForDateTimeLocal(start);
    newWindow.value.ends_at = formatForDateTimeLocal(end);
  }

  const startsAtInputRef = ref<HTMLInputElement | null>(null);
  const endsAtInputRef = ref<HTMLInputElement | null>(null);

  function openStartsPicker(): void {
    if (startsAtInputRef.value && typeof startsAtInputRef.value.showPicker === 'function') {
      try {
        startsAtInputRef.value.showPicker();
      } catch {
        // Fallback no intrusivo si el browser ya desplegó el menú
      }
    }
  }

  function openEndsPicker(): void {
    if (endsAtInputRef.value && typeof endsAtInputRef.value.showPicker === 'function') {
      try {
        endsAtInputRef.value.showPicker();
      } catch {
        // Fallback no intrusivo si el browser ya desplegó el menú
      }
    }
  }

  function handleDateKeyDown(event: KeyboardEvent, target: 'starts' | 'ends'): void {
    // Permitir accesibilidad por teclado y navegación dentro de selectores de fecha/hora
    if (
      ['Tab', 'Escape', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(event.key)
    ) {
      return;
    }
    // Enter o Espacio abren el menú del calendario
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (target === 'starts') {
        openStartsPicker();
      } else {
        openEndsPicker();
      }
      return;
    }
    // Deshabilitar escritura directa de teclado para obligar uso del selector visual
    event.preventDefault();
  }

  const filteredInventoryRouters = computed(() => {
    const q = routerSearch.value.trim().toLowerCase();
    if (!q) return inventoryStore.routers;
    return inventoryStore.routers.filter(
      (r) =>
        r.display_name.toLowerCase().includes(q) ||
        r.ip_address.toLowerCase().includes(q) ||
        (r.model && r.model.toLowerCase().includes(q)) ||
        (r.network_role && r.network_role.toLowerCase().includes(q)),
    );
  });

  function selectAllFilteredRouters(): void {
    const ids = filteredInventoryRouters.value.map((r) => r.id);
    const set = new Set([...selectedRouterIds.value, ...ids]);
    selectedRouterIds.value = Array.from(set);
  }

  function deselectAllRouters(): void {
    selectedRouterIds.value = [];
  }

  function getRouterLabel(routerId: string): string {
    const r = inventoryStore.routers.find((item) => item.id === routerId);
    if (r) {
      return `${r.display_name} (${r.ip_address})`;
    }
    return routerId.length > 12 ? `Router ${routerId.slice(0, 8)}...` : routerId;
  }

  async function loadMaintenanceWindows(): Promise<void> {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.get<MaintenanceWindowItem[] | { items: MaintenanceWindowItem[] }>(
        '/api/v1/maintenance/windows',
      );
      const raw = Array.isArray(res.data) ? res.data : res.data?.items || [];
      windowsList.value = raw;
    } catch {
      // Sin datos de demostración en producción
      windowsList.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  async function cancelMaintenanceWindow(windowItem: MaintenanceWindowItem): Promise<void> {
    if (!confirm(`¿Deseas cancelar la ventana de mantenimiento "${windowItem.title}"?`)) {
      return;
    }

    try {
      await http.post(`/api/v1/maintenance/windows/${windowItem.id}/cancel`);
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

  async function handleCreateWindow(): Promise<void> {
    isCreating.value = true;
    errorMessage.value = '';

    try {
      if (!newWindow.value.title.trim()) {
        errorMessage.value = 'El título de la ventana de mantenimiento es obligatorio.';
        isCreating.value = false;
        return;
      }

      if (!newWindow.value.starts_at || !newWindow.value.ends_at) {
        errorMessage.value = 'Debe indicar fecha y hora de inicio y fin.';
        isCreating.value = false;
        return;
      }

      const payload: Record<string, unknown> = {
        title: newWindow.value.title.trim(),
        reason: newWindow.value.reason.trim(),
        starts_at: new Date(newWindow.value.starts_at).toISOString(),
        ends_at: new Date(newWindow.value.ends_at).toISOString(),
        suppress_alerts: newWindow.value.suppress_alerts,
      };

      if (scopeType.value === 'routers') {
        if (selectedRouterIds.value.length === 0) {
          errorMessage.value = 'Debe seleccionar al menos un router de la lista.';
          isCreating.value = false;
          return;
        }
        payload.router_ids = selectedRouterIds.value;
        payload.router_id = selectedRouterIds.value[0];
      } else if (scopeType.value === 'tag') {
        if (!newWindow.value.target_tag.trim()) {
          errorMessage.value = 'Debe ingresar una etiqueta de red para la ventana.';
          isCreating.value = false;
          return;
        }
        payload.target_tag = newWindow.value.target_tag.trim().toLowerCase();
      } else {
        payload.target_tag = 'global';
      }

      const res = await http.post<MaintenanceWindowItem>(
        '/api/v1/maintenance/windows',
        payload,
      );

      // Si el backend devolvió el objeto creado, lo colocamos arriba
      if (res.data && res.data.id) {
        windowsList.value.unshift(res.data);
      } else {
        await loadMaintenanceWindows();
      }

      // Cerrar modal y limpiar
      isCreateModalOpen.value = false;
      successMessage.value = 'Ventana de mantenimiento programada exitosamente.';
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);

      newWindow.value = {
        title: '',
        reason: '',
        target_tag: '',
        starts_at: '',
        ends_at: '',
        suppress_alerts: true,
      };
      initDefaultDates();
      selectedRouterIds.value = [];
      routerSearch.value = '';
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al programar ventana.';
    } finally {
      isCreating.value = false;
    }
  }

  onMounted(async () => {
    initDefaultDates();
    await loadMaintenanceWindows();
    if (inventoryStore.routers.length === 0) {
      await inventoryStore.fetchRouters();
    }
  });
</script>

<template>
  <div class="maintenance-view">
    <header class="view-header">
      <div>
        <h1 class="view-title">Ventanas de Mantenimiento Programadas</h1>
        <p class="view-subtitle">
          Programación de trabajos en caliente y supresión temporal de alertas (Telegram, SMTP, Webhook).
        </p>
      </div>
      <button
        id="btn-open-create-mw-modal"
        type="button"
        class="btn-create"
        @click="openCreateModal"
      >
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
              <span
                v-if="w.router_id"
                class="badge-target badge-target--router"
                :title="`ID: ${w.router_id}`"
              >
                📡 {{ getRouterLabel(w.router_id) }}
              </span>
              <span
                v-else-if="w.target_tag && w.target_tag !== 'global'"
                class="badge-target badge-target--tag"
              >
                🏷 Tag: {{ w.target_tag }}
              </span>
              <span v-else class="badge-target badge-target--global">
                🌐 Toda la Red (Global)
              </span>
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
    <div
      v-if="isCreateModalOpen"
      class="rg-modal-backdrop"
      @click.self="isCreateModalOpen = false"
    >
      <div
        class="rg-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-mw-title"
      >
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
              placeholder="ej. Actualización RouterOS v7.18 y parche BGP"
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
              placeholder="Describa la causa operativa, cambio de fibra o ventana programada"
              class="form-input"
            ></textarea>
          </div>

          <!-- Selector de Alcance de Mantenimiento -->
          <div class="form-group">
            <label class="form-label">Alcance del Mantenimiento *</label>
            <div class="scope-selector" role="radiogroup" aria-label="Alcance del mantenimiento">
              <button
                type="button"
                class="scope-btn"
                :class="{ 'scope-btn--active': scopeType === 'routers' }"
                role="radio"
                :aria-checked="scopeType === 'routers'"
                @click="scopeType = 'routers'"
              >
                📡 Routers Involucrados
              </button>
              <button
                type="button"
                class="scope-btn"
                :class="{ 'scope-btn--active': scopeType === 'tag' }"
                role="radio"
                :aria-checked="scopeType === 'tag'"
                @click="scopeType = 'tag'"
              >
                🏷️ Por Etiqueta / Tag
              </button>
              <button
                type="button"
                class="scope-btn"
                :class="{ 'scope-btn--active': scopeType === 'global' }"
                role="radio"
                :aria-checked="scopeType === 'global'"
                @click="scopeType = 'global'"
              >
                🌐 Toda la Red (Global)
              </button>
            </div>
          </div>

          <!-- Panel de Selección de Routers Involucrados -->
          <div v-if="scopeType === 'routers'" class="router-selector-box">
            <div class="router-selector-header">
              <div class="search-filter-wrapper">
                <input
                  id="mw-router-search"
                  v-model="routerSearch"
                  type="text"
                  placeholder="🔍 Buscar por nombre, IP, modelo o rol..."
                  class="form-input form-input--search"
                  aria-label="Buscar routers para seleccionar"
                />
              </div>
              <div class="selector-actions">
                <button
                  type="button"
                  class="btn-select-action"
                  @click="selectAllFilteredRouters"
                >
                  Seleccionar visibles
                </button>
                <button
                  type="button"
                  class="btn-select-action"
                  @click="deselectAllRouters"
                >
                  Limpiar
                </button>
                <span class="selection-counter badge-target badge-target--router">
                  {{ selectedRouterIds.length }} seleccionados
                </span>
              </div>
            </div>

            <div class="router-checklist" role="group" aria-label="Lista de routers para mantenimiento">
              <label
                v-for="r in filteredInventoryRouters"
                :key="r.id"
                class="router-checklist-item"
                :class="{ 'router-checklist-item--selected': selectedRouterIds.includes(r.id) }"
              >
                <input
                  v-model="selectedRouterIds"
                  type="checkbox"
                  :value="r.id"
                  class="router-checkbox"
                />
                <div class="router-checklist-details">
                  <span class="router-name-text">{{ r.display_name }}</span>
                  <span class="router-sub-text font-mono">
                    {{ r.ip_address }} • {{ r.model || 'MikroTik' }}
                  </span>
                </div>
                <span v-if="r.network_role" class="badge-role font-mono">
                  {{ r.network_role }}
                </span>
              </label>

              <div v-if="filteredInventoryRouters.length === 0" class="empty-routers-notice">
                No se encontraron routers en la organización.
              </div>
            </div>
          </div>

          <!-- Panel Por Etiqueta / Tag -->
          <div v-else-if="scopeType === 'tag'" class="form-group">
            <label for="mw-tag" class="form-label">Etiqueta de Red (Tag) *</label>
            <input
              id="mw-tag"
              v-model="newWindow.target_tag"
              type="text"
              placeholder="ej. datacenter, backbone, ftth-norte"
              class="form-input"
            />
            <span class="helper-text">
              Silenciará las alertas de todos los equipos que tengan asignada esta etiqueta.
            </span>
          </div>

          <!-- Panel Global -->
          <div v-else class="global-scope-notice">
            <span class="notice-icon" aria-hidden="true">🌐</span>
            <p>
              Esta ventana de mantenimiento aplicará de forma global para <strong>toda la infraestructura</strong> de la organización.
            </p>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="mw-starts" class="form-label">Fecha y Hora de Inicio *</label>
              <div class="date-picker-input-group">
                <input
                  id="mw-starts"
                  ref="startsAtInputRef"
                  v-model="newWindow.starts_at"
                  type="datetime-local"
                  required
                  class="form-input form-input--picker-only"
                  aria-label="Fecha y hora de inicio"
                  @click="openStartsPicker"
                  @keydown="handleDateKeyDown($event, 'starts')"
                  @paste.prevent
                  @drop.prevent
                />
                <button
                  type="button"
                  class="btn-calendar-trigger"
                  aria-label="Abrir calendario de fecha de inicio"
                  title="Abrir selector de fecha y hora"
                  @click="openStartsPicker"
                >
                  📅
                </button>
              </div>
              <span class="helper-text helper-text--picker">
                Seleccione desde el botón o menú del calendario (escritura manual deshabilitada).
              </span>
            </div>
            <div class="form-group">
              <label for="mw-ends" class="form-label">Fecha y Hora de Fin *</label>
              <div class="date-picker-input-group">
                <input
                  id="mw-ends"
                  ref="endsAtInputRef"
                  v-model="newWindow.ends_at"
                  type="datetime-local"
                  required
                  class="form-input form-input--picker-only"
                  aria-label="Fecha y hora de fin"
                  @click="openEndsPicker"
                  @keydown="handleDateKeyDown($event, 'ends')"
                  @paste.prevent
                  @drop.prevent
                />
                <button
                  type="button"
                  class="btn-calendar-trigger"
                  aria-label="Abrir calendario de fecha de fin"
                  title="Abrir selector de fecha y hora"
                  @click="openEndsPicker"
                >
                  📅
                </button>
              </div>
              <span class="helper-text helper-text--picker">
                Seleccione desde el botón o menú del calendario (escritura manual deshabilitada).
              </span>
            </div>
          </div>

          <!-- Presets de Duración Rápida -->
          <div class="duration-presets-group">
            <span class="presets-label">Atajos de Duración:</span>
            <div class="presets-buttons">
              <button
                type="button"
                class="btn-preset"
                title="Establecer fin a +1 hora del inicio"
                @click="setDurationPreset(1)"
              >
                ⏱️ +1 Hora
              </button>
              <button
                type="button"
                class="btn-preset"
                title="Establecer fin a +2 horas del inicio"
                @click="setDurationPreset(2)"
              >
                ⏱️ +2 Horas
              </button>
              <button
                type="button"
                class="btn-preset"
                title="Establecer fin a +4 horas del inicio"
                @click="setDurationPreset(4)"
              >
                ⏱️ +4 Horas
              </button>
              <button
                type="button"
                class="btn-preset"
                title="Programar para la próxima madrugada de 01:00 a 05:00"
                @click="setNightWindowPreset"
              >
                🌙 Madrugada (01:00 - 05:00)
              </button>
            </div>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="newWindow.suppress_alerts" type="checkbox" />
              <span>Suprimir alertas hacia Telegram, Correo SMTP y Webhook durante la ventana</span>
            </label>
          </div>

          <footer class="modal-footer">
            <button
              type="button"
              class="btn-cancel"
              @click="isCreateModalOpen = false"
            >
              Cancelar
            </button>
            <button
              id="btn-submit-mw"
              type="submit"
              class="btn-submit"
              :disabled="isCreating"
            >
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
    transition: opacity 0.15s ease-in-out;
  }

  .btn-create:hover {
    opacity: 0.9;
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
    display: inline-block;
    font-size: 0.75rem;
    padding: 3px 8px;
    border-radius: 4px;
  }

  .badge-target--router {
    background: rgba(34, 211, 238, 0.15);
    color: #22d3ee;
    border: 1px solid rgba(34, 211, 238, 0.3);
  }

  .badge-target--tag {
    background: rgba(168, 85, 247, 0.15);
    color: #c084fc;
    border: 1px solid rgba(168, 85, 247, 0.3);
  }

  .badge-target--global {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
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

  .btn-cancel-window:hover {
    background: rgba(239, 68, 68, 0.15);
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
    max-width: 680px;
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 8px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
    max-height: 90vh;
    display: flex;
    flex-direction: column;
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
    overflow-y: auto;
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

  .form-input--search {
    width: 100%;
  }

  .helper-text {
    font-size: 0.75rem;
    color: var(--rg-text-muted, #94a3b8);
    margin-top: 2px;
  }

  /* Selector de Alcance */
  .scope-selector {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .scope-btn {
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 0.8rem;
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    cursor: pointer;
    transition: all 0.15s ease-in-out;
  }

  .scope-btn:hover {
    border-color: var(--rg-accent-cyan, #22d3ee);
  }

  .scope-btn--active {
    background: rgba(34, 211, 238, 0.15);
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    font-weight: 600;
  }

  /* Caja de Selección de Routers */
  .router-selector-box {
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .router-selector-header {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .selector-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .btn-select-action {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    font-size: 0.75rem;
    padding: 4px 8px;
    border-radius: 4px;
    cursor: pointer;
  }

  .btn-select-action:hover {
    background: rgba(255, 255, 255, 0.05);
    color: var(--rg-text-primary, #f8fafc);
  }

  .selection-counter {
    margin-left: auto;
  }

  .router-checklist {
    max-height: 180px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding-right: 4px;
  }

  .router-checklist-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 4px;
    background: var(--rg-bg-surface, #111827);
    border: 1px solid transparent;
    cursor: pointer;
    transition: all 0.15s ease-in-out;
  }

  .router-checklist-item:hover {
    background: rgba(255, 255, 255, 0.03);
    border-color: var(--rg-border-grid, #1e293b);
  }

  .router-checklist-item--selected {
    background: rgba(34, 211, 238, 0.08);
    border-color: rgba(34, 211, 238, 0.3);
  }

  .router-checkbox {
    accent-color: var(--rg-accent-cyan, #22d3ee);
    cursor: pointer;
  }

  .router-checklist-details {
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex: 1;
  }

  .router-name-text {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--rg-text-primary, #f8fafc);
  }

  .router-sub-text {
    font-size: 0.75rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .badge-role {
    font-size: 0.7rem;
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(148, 163, 184, 0.15);
    color: #cbd5e1;
  }

  .empty-routers-notice {
    padding: 16px;
    text-align: center;
    font-size: 0.8rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .global-scope-notice {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 14px;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 6px;
    color: #34d399;
    font-size: 0.85rem;
  }

  .global-scope-notice p {
    margin: 0;
  }

  .notice-icon {
    font-size: 1.3rem;
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

  .btn-submit:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-cancel {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 8px 18px;
    border-radius: 6px;
    cursor: pointer;
  }

  /* Selector de Fecha y Hora Exclusivo de Calendario */
  .date-picker-input-group {
    position: relative;
    display: flex;
    align-items: center;
    width: 100%;
  }

  .form-input--picker-only {
    cursor: pointer;
    caret-color: transparent !important;
    user-select: none;
    padding-right: 44px;
    font-family: inherit;
  }

  .form-input--picker-only::-webkit-calendar-picker-indicator {
    cursor: pointer;
    opacity: 0.85;
    filter: invert(0.8) sepia(100%) saturate(300%) hue-rotate(140deg);
    padding: 4px;
    border-radius: 4px;
    transition: opacity 0.15s ease, filter 0.15s ease;
  }

  .form-input--picker-only::-webkit-calendar-picker-indicator:hover {
    opacity: 1;
    filter: invert(0.9) sepia(100%) saturate(500%) hue-rotate(140deg);
  }

  .btn-calendar-trigger {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    background: transparent;
    border: none;
    font-size: 1.15rem;
    cursor: pointer;
    padding: 2px 4px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.15s ease, transform 0.15s ease;
    user-select: none;
  }

  .btn-calendar-trigger:hover {
    background: rgba(34, 211, 238, 0.15);
    transform: translateY(-50%) scale(1.1);
  }

  .helper-text--picker {
    font-size: 0.72rem;
    color: var(--rg-text-muted, #94a3b8);
    margin-top: 4px;
    display: block;
  }

  /* Atajos de Duración Rápida */
  .duration-presets-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
    background: rgba(30, 41, 59, 0.4);
    border: 1px dashed rgba(34, 211, 238, 0.25);
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 6px;
  }

  .presets-label {
    font-size: 0.72rem;
    color: var(--rg-accent-cyan, #22d3ee);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .presets-buttons {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .btn-preset {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    font-size: 0.75rem;
    padding: 4px 10px;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.15s ease-in-out;
  }

  .btn-preset:hover {
    background: rgba(34, 211, 238, 0.15);
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    transform: translateY(-1px);
  }
</style>
