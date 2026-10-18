<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref } from 'vue';
  import { http } from '@/api/httpClient';
  import type { CsvDryRunResponse } from '@/types';

  defineProps<{
    isOpen: boolean;
  }>();

  const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'imported', count: number): void;
  }>();

  const step = ref<1 | 2>(1);
  const isProcessing = ref(false);
  const errorMessage = ref('');
  const selectedFile = ref<File | null>(null);
  const dryRunResult = ref<CsvDryRunResponse | null>(null);

  function resetState() {
    step.value = 1;
    selectedFile.value = null;
    dryRunResult.value = null;
    errorMessage.value = '';
    isProcessing.value = false;
  }

  function handleFileChange(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
      selectedFile.value = target.files[0];
      errorMessage.value = '';
    }
  }

  function downloadCsvTemplate() {
    const headers =
      'display_name,ip_address,api_port,ros_username,ros_password,network_role,serial_number,latitude,longitude,tags';
    const sample =
      'CCR2004-Edge-Norte,192.168.10.1,8728,api_admin,ClaveSegura123!,EDGE_BGP,HE4011ABC123,10.4806,-66.9036,core;zona-norte';
    const content = `\uFEFF${headers}\r\n${sample}\r\n`;
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url =
      typeof URL.createObjectURL === 'function' ? URL.createObjectURL(blob) : 'blob:sample';
    const link = document.createElement('a');
    link.style.display = 'none';
    link.href = url;
    link.download = 'rosgrid-inventario-plantilla.csv';
    link.setAttribute('download', 'rosgrid-inventario-plantilla.csv');
    if (typeof document !== 'undefined' && document.body) {
      document.body.appendChild(link);
    }
    link.click();
    setTimeout(() => {
      if (link.parentNode) {
        link.parentNode.removeChild(link);
      }
      if (typeof URL.revokeObjectURL === 'function') {
        URL.revokeObjectURL(url);
      }
    }, 15000);
  }

  async function handleDryRunSubmit() {
    if (!selectedFile.value) {
      errorMessage.value = 'Por favor, selecciona un archivo .csv para validar.';
      return;
    }

    isProcessing.value = true;
    errorMessage.value = '';

    const formData = new FormData();
    formData.append('file', selectedFile.value);

    try {
      const res = await http.post<CsvDryRunResponse>(
        '/api/v1/inventory/import-csv/dry-run',
        formData,
      );
      dryRunResult.value = res.data;
      step.value = 2;
    } catch (err: any) {
      errorMessage.value =
        err?.response?.data?.detail || err?.message || 'Error al validar el archivo CSV con el servidor';
    } finally {
      isProcessing.value = false;
    }
  }

  async function handleCommitImport() {
    if (!selectedFile.value) return;
    isProcessing.value = true;
    errorMessage.value = '';

    const formData = new FormData();
    formData.append('file', selectedFile.value);

    try {
      const res = await http.post<{ imported_count: number }>(
        '/api/v1/inventory/import-csv/commit',
        formData,
      );
      const count = res.data?.imported_count ?? dryRunResult.value?.valid_rows_count ?? 0;
      emit('imported', count);
      resetState();
      emit('close');
    } catch (err: any) {
      errorMessage.value =
        err?.response?.data?.detail || err?.message || 'Error al importar los equipos en el servidor';
    } finally {
      isProcessing.value = false;
    }
  }
</script>

<template>
  <div v-if="isOpen" class="rg-modal-backdrop" @click.self="emit('close')">
    <div class="rg-modal" role="dialog" aria-modal="true" aria-labelledby="csv-wizard-title">
      <header class="modal-header">
        <h2 id="csv-wizard-title" class="modal-title">
          Asistente de Importación Masiva CSV (Paso {{ step }} de 2)
        </h2>
        <button
          type="button"
          class="btn-close"
          aria-label="Cerrar modal de importación"
          @click="emit('close')"
        >
          ✕
        </button>
      </header>

      <div class="modal-body">
        <div v-if="errorMessage" class="banner banner--error" role="alert">
          {{ errorMessage }}
        </div>

        <!-- PASO 1: Selección de Archivo y Dry-Run -->
        <div v-if="step === 1" class="step-content">
          <p class="step-help">
            Carga una lista de routers MikroTik para validar la estructura antes de importarlos a la
            base de datos.
          </p>

          <div class="template-box">
            <span>¿No tienes la plantilla oficial?</span>
            <button type="button" class="btn-download-template" @click="downloadCsvTemplate">
              📄 Descargar Plantilla .CSV
            </button>
          </div>

          <div class="file-drop-area">
            <label for="csv-file-input" class="file-label">
              <span class="file-icon" aria-hidden="true">📂</span>
              <span class="file-instruction">
                {{
                  selectedFile
                    ? selectedFile.name
                    : 'Haz clic para seleccionar o arrastra tu archivo .csv'
                }}
              </span>
              <input
                id="csv-file-input"
                type="file"
                accept=".csv"
                class="file-input-hidden"
                @change="handleFileChange"
              />
            </label>
          </div>
        </div>

        <!-- PASO 2: Resultados del Dry-Run y Confirmación -->
        <div v-else class="step-content">
          <div v-if="dryRunResult" class="dryrun-summary">
            <span class="badge-valid"> ✓ {{ dryRunResult.valid_rows_count }} filas válidas </span>
            <span v-if="dryRunResult.invalid_rows_count > 0" class="badge-invalid">
              ⛔ {{ dryRunResult.invalid_rows_count }} filas con error
            </span>
          </div>

          <p class="step-help">
            Revisa la previsualización de datos. Solo se importarán los equipos válidos:
          </p>

          <div class="table-scroll">
            <table class="rg-preview-table" aria-label="Previsualización de importación">
              <thead>
                <tr>
                  <th scope="col">Línea</th>
                  <th scope="col">Estado</th>
                  <th scope="col">Nombre</th>
                  <th scope="col">IP</th>
                  <th scope="col">Serial</th>
                  <th scope="col">Observación</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in dryRunResult?.rows"
                  :key="row.line"
                  :class="{ 'row--invalid': !row.is_valid }"
                >
                  <td>{{ row.line }}</td>
                  <td>
                    <span :class="row.is_valid ? 'text-ok' : 'text-err'">
                      {{ row.is_valid ? 'Válido' : 'Inválido' }}
                    </span>
                  </td>
                  <td>
                    <strong>{{ row.display_name }}</strong>
                  </td>
                  <td>
                    <code>{{ row.ip_address }}</code>
                  </td>
                  <td>
                    <code>{{ row.serial_number }}</code>
                  </td>
                  <td>{{ row.error || 'Listo para importar' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <footer class="modal-footer">
        <button
          v-if="step === 2"
          type="button"
          class="btn-secondary"
          :disabled="isProcessing"
          @click="step = 1"
        >
          ← Volver a cargar archivo
        </button>

        <button type="button" class="btn-secondary" :disabled="isProcessing" @click="emit('close')">
          Cancelar
        </button>

        <button
          v-if="step === 1"
          type="button"
          class="btn-primary"
          :disabled="isProcessing"
          @click="handleDryRunSubmit"
        >
          {{ isProcessing ? 'Validando...' : 'Validar Archivo (Dry-Run) →' }}
        </button>

        <button
          v-else
          type="button"
          class="btn-primary"
          :disabled="isProcessing || !dryRunResult || dryRunResult.valid_rows_count === 0"
          @click="handleCommitImport"
        >
          {{
            isProcessing
              ? 'Importando...'
              : `Confirmar e Importar ${dryRunResult?.valid_rows_count} Equipos`
          }}
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
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
    max-width: 720px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    background-color: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 8px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
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
    font-weight: 700;
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

  .modal-body {
    padding: 20px;
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .banner--error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #f87171;
    padding: 10px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .step-help {
    font-size: 0.85rem;
    color: var(--rg-text-secondary, #cbd5e1);
    margin: 0;
  }

  .template-box {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .btn-download-template {
    background: transparent;
    border: 1px solid var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
  }

  .file-drop-area {
    border: 2px dashed var(--rg-border-grid, #1e293b);
    border-radius: 8px;
    padding: 36px 20px;
    text-align: center;
    background: var(--rg-bg-canvas, #0b0f19);
    cursor: pointer;
  }

  .file-drop-area:hover {
    border-color: var(--rg-accent-cyan, #22d3ee);
  }

  .file-label {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    cursor: pointer;
  }

  .file-icon {
    font-size: 2.2rem;
  }

  .file-instruction {
    font-size: 0.9rem;
    color: var(--rg-text-primary, #f8fafc);
  }

  .file-input-hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
  }

  .dryrun-summary {
    display: flex;
    gap: 12px;
  }

  .badge-valid {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid #10b981;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
  }

  .badge-invalid {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid #ef4444;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
  }

  .table-scroll {
    overflow-x: auto;
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
  }

  .rg-preview-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
    text-align: left;
  }

  .rg-preview-table th {
    background: var(--rg-bg-elevated, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 8px 12px;
    border-bottom: 1px solid var(--rg-border-grid, #334155);
  }

  .rg-preview-table td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-primary, #f8fafc);
  }

  .row--invalid {
    background: rgba(239, 68, 68, 0.08);
  }

  .text-ok {
    color: #34d399;
  }

  .text-err {
    color: #f87171;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 20px;
    border-top: 1px solid var(--rg-border-grid, #1e293b);
  }

  .btn-primary {
    background: var(--rg-accent-cyan, #22d3ee);
    color: #0b0f19;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 700;
    cursor: pointer;
  }

  .btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-secondary {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 8px 18px;
    border-radius: 6px;
    cursor: pointer;
  }
</style>
