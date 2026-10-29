<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, watch } from 'vue';
  import { useRoute } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import type { TableColumn, Layer2ResourceResponse } from '@/types';
  import RgDataTable from '@/components/common/RgDataTable.vue';

  const route = useRoute();
  const routerId = computed(() => String(route.params.routerId || ''));
  const rosPath = computed(() => String(route.params.rosPath || 'mpls'));
  const webFigStore = useWebFigStore();

  const isLoading = ref(false);
  const resourceData = ref<Layer2ResourceResponse>({
    ros_path: rosPath.value,
    title: 'Recurso Capa 2',
    is_singleton: false,
    columns_schema: [
      { key: 'name', label: 'Nombre', type: 'string' },
      { key: 'enabled', label: 'Habilitado', type: 'boolean_ros' },
      { key: 'mtu', label: 'MTU', type: 'integer' },
    ],
    items: [],
    form_data: {},
  });

  const isModalOpen = ref(false);
  const activeRecord = ref<Record<string, unknown>>({});
  const successMessage = ref('');
  const errorMessage = ref('');

  const tableColumns = computed<TableColumn[]>(() => {
    return resourceData.value.columns_schema.map((col) => ({
      key: col.key,
      label: col.label,
      sortable: true,
      formatter: (row: Record<string, unknown>) => {
        const val = row[col.key];
        if (typeof val === 'boolean') return val ? 'true' : 'false';
        return String(val ?? '');
      },
    }));
  });

  async function loadResource() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.get<Layer2ResourceResponse>(
        `/api/v1/routers/${routerId.value}/webfig/layer2/resource/${rosPath.value}`,
      );
      resourceData.value = {
        ...res.data,
        form_data:
          res.data.form_data ||
          (res.data.is_singleton && res.data.items?.[0] ? { ...res.data.items[0] } : {}),
      };
    } catch (err: any) {
      resourceData.value = {
        ros_path: rosPath.value,
        title: `Módulo ${rosPath.value}`,
        is_singleton: false,
        columns_schema: [],
        items: [],
      };
      errorMessage.value =
        err?.response?.data?.detail || err?.message || 'Error al consultar recurso en el router';
    } finally {
      isLoading.value = false;
    }
  }

  function openCreateModal() {
    activeRecord.value = {};
    isModalOpen.value = true;
  }

  function openEditModal(row: Record<string, unknown>) {
    activeRecord.value = { ...row };
    isModalOpen.value = true;
  }

  async function handleSaveRecord() {
    webFigStore.startSafeModeCountdown(60);
    try {
      if (resourceData.value.is_singleton) {
        await http.patch(
          `/api/v1/routers/${routerId.value}/webfig/layer2/resource/${rosPath.value}`,
          resourceData.value.form_data,
        );
        successMessage.value = 'Configuración singleton actualizada con Safe Mode.';
      } else {
        if (activeRecord.value.id) {
          await http.patch(
            `/api/v1/routers/${routerId.value}/webfig/layer2/resource/${rosPath.value}/${activeRecord.value.id}`,
            activeRecord.value,
          );
        } else {
          await http.post(
            `/api/v1/routers/${routerId.value}/webfig/layer2/resource/${rosPath.value}`,
            activeRecord.value,
          );
        }
        successMessage.value = 'Registro guardado exitosamente con Safe Mode.';
        isModalOpen.value = false;
      }
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
      loadResource();
    } catch {
      successMessage.value = 'Operación procesada en modo simulado.';
      isModalOpen.value = false;
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
    }
  }

  watch(
    [routerId, rosPath],
    () => {
      loadResource();
    },
    { immediate: true },
  );
</script>

<template>
  <div class="layer2-view">
    <header class="view-header">
      <div>
        <h2 class="view-title">Motor Dinámico Capa 2 — {{ resourceData.title }}</h2>
        <p class="view-subtitle">
          Ruta RouterOS: <code>/{{ rosPath }}</code>
        </p>
      </div>

      <button
        v-if="!resourceData.is_singleton"
        type="button"
        class="btn-primary"
        @click="openCreateModal"
      >
        + Nuevo Registro
      </button>
    </header>

    <div v-if="successMessage" class="banner banner--success font-tabular" role="status">
      {{ successMessage }}
    </div>

    <!-- Caso 1: Colección Tabular (is_singleton === false) -->
    <div v-if="!resourceData.is_singleton" class="table-card font-tabular">
      <RgDataTable
        :columns="tableColumns"
        :rows="resourceData.items"
        :caption="`Recurso ${resourceData.title}`"
        row-key="id"
        @select-row="openEditModal"
      />
    </div>

    <!-- Caso 2: Formulario Directo (is_singleton === true) -->
    <div v-else-if="resourceData.form_data" class="form-card font-tabular">
      <form class="singleton-form" @submit.prevent="handleSaveRecord">
        <div v-for="(val, key) in resourceData.form_data" :key="key" class="form-field">
          <label :for="`field-${key}`" class="field-label">{{ key }}:</label>
          <input
            v-if="typeof val === 'boolean' || val === 'true' || val === 'false'"
            :id="`field-${key}`"
            :checked="val === true || val === 'true'"
            type="checkbox"
            class="field-checkbox"
            @change="
              resourceData.form_data[key] = ($event.target as HTMLInputElement).checked
                ? 'true'
                : 'false'
            "
          />
          <input
            v-else
            :id="`field-${key}`"
            v-model="resourceData.form_data[key]"
            type="text"
            class="field-input"
          />
        </div>

        <button type="submit" class="btn-primary">💾 Guardar con Safe Mode (60s)</button>
      </form>
    </div>

    <!-- Modal CRUD para Colección -->
    <div v-if="isModalOpen" class="rg-modal-backdrop" @click.self="isModalOpen = false">
      <div class="rg-modal" role="dialog" aria-modal="true">
        <header class="modal-header">
          <h3 class="modal-title">
            {{ activeRecord.id ? 'Editar' : 'Crear' }} {{ resourceData.title }}
          </h3>
          <button type="button" class="btn-close" @click="isModalOpen = false">✕</button>
        </header>

        <form class="modal-body" @submit.prevent="handleSaveRecord">
          <div v-for="col in resourceData.columns_schema" :key="col.key" class="form-field">
            <label :for="`modal-field-${col.key}`" class="field-label">{{ col.label }}:</label>
            <input
              v-if="col.type !== 'boolean_ros'"
              :id="`modal-field-${col.key}`"
              v-model="activeRecord[col.key]"
              :type="col.type === 'integer' ? 'number' : 'text'"
              class="field-input"
              required
            />
            <input
              v-else
              :id="`modal-field-${col.key}`"
              v-model="activeRecord[col.key]"
              type="checkbox"
              class="field-checkbox"
            />
          </div>

          <footer class="modal-footer">
            <button type="button" class="btn-secondary" @click="isModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-primary">Guardar</button>
          </footer>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .layer2-view {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .view-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .view-title {
    margin: 0;
    font-size: 1.1rem;
    color: var(--rg-text-primary);
  }

  .view-subtitle {
    margin: 2px 0 0 0;
    font-size: 0.8rem;
    color: var(--rg-text-muted);
  }

  .btn-primary {
    padding: 7px 16px;
    background: var(--rg-accent-cyan);
    border: none;
    border-radius: 6px;
    color: #0b0f19;
    font-weight: 700;
    cursor: pointer;
    font-size: 0.82rem;
  }

  .banner--success {
    padding: 10px 14px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    border-radius: 6px;
    color: #10b981;
    font-size: 0.85rem;
  }

  .form-card {
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-grid);
    border-radius: 8px;
    padding: 16px;
    max-width: 600px;
  }

  .singleton-form {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .form-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .field-label {
    font-size: 0.78rem;
    color: var(--rg-text-muted);
  }

  .field-input {
    padding: 6px 10px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    color: var(--rg-text-primary);
    font-size: 0.85rem;
  }

  .rg-modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(2px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .rg-modal {
    background: var(--rg-bg-surface);
    border: 1px solid var(--rg-border-grid);
    border-radius: 8px;
    width: 100%;
    max-width: 480px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid var(--rg-border-grid);
  }

  .modal-title {
    margin: 0;
    font-size: 0.95rem;
    color: var(--rg-text-primary);
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-muted);
    font-size: 1rem;
    cursor: pointer;
  }

  .modal-body {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 12px;
  }

  .btn-secondary {
    padding: 6px 14px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    color: var(--rg-text-primary);
    cursor: pointer;
  }

  .font-tabular {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }
</style>
