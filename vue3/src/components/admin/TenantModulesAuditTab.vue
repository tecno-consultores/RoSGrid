<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, onMounted } from 'vue';
  import { http } from '@/api/httpClient';
  import { useI18n } from '@/composables/useI18n';
  import type { TenantFeatureFlags } from '@/types';

  const props = defineProps<{
    tenantId: string;
  }>();

  const emit = defineEmits<{
    (e: 'rollback', previousFeatures: Partial<TenantFeatureFlags>): void;
  }>();

  const { t, locale } = useI18n();

  interface AuditRecord {
    id: string;
    created_at: string;
    actor_username: string;
    actor_role: string;
    actor_ip: string;
    event_category: string;
    event_action: string;
    status_code: number;
    before_state?: Record<string, unknown>;
    after_state?: Record<string, unknown>;
    record_sha256_hash: string;
  }

  const records = ref<AuditRecord[]>([]);
  const isLoading = ref(true);
  const errorMessage = ref('');

  async function fetchAuditHistory(): Promise<void> {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.get<AuditRecord[]>(
        `/api/v1/tenants/${props.tenantId}/features/audit?limit=30`,
      );
      records.value = res.data || [];
    } catch {
      errorMessage.value = t('tenants_mgmt.audit_error', 'Error al consultar el historial de auditoría de módulos.');
    } finally {
      isLoading.value = false;
    }
  }

  function formatTimestamp(isoStr: string): string {
    try {
      const d = new Date(isoStr);
      return d.toLocaleString(locale.value === 'en' ? 'en-US' : 'es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return isoStr;
    }
  }

  function formatDiffItem(key: string, beforeVal: unknown, afterVal: unknown): string | null {
    if (beforeVal === afterVal) return null;
    const shortKey = key.replace(/_enabled$/, '').replace(/_/g, ' ');
    const bText = beforeVal ? 'ON' : 'OFF';
    const aText = afterVal ? 'ON' : 'OFF';
    return `${shortKey}: ${bText} ➔ ${aText}`;
  }

  function summarizeDiff(before?: Record<string, unknown>, after?: Record<string, unknown>): string[] {
    if (!after && !before) return ['Modificación general'];
    const b = before ?? {};
    const a = after ?? {};
    const keys = Array.from(new Set([...Object.keys(b), ...Object.keys(a)]));
    const changes: string[] = [];

    for (const k of keys) {
      if (k === 'onboarding_completed') continue;
      const formatted = formatDiffItem(k, b[k], a[k]);
      if (formatted) {
        changes.push(formatted);
      }
    }

    return changes.length > 0 ? changes : ['Sin cambios de flags'];
  }

  function handleRollbackClick(record: AuditRecord): void {
    if (record.before_state && Object.keys(record.before_state).length > 0) {
      emit('rollback', record.before_state as Partial<TenantFeatureFlags>);
    }
  }

  onMounted(() => {
    fetchAuditHistory();
  });
</script>

<template>
  <div class="tenant-audit-tab" role="region" :aria-label="t('tenants_mgmt.tab_audit_aria', 'Historial de Modificaciones de Módulos')">
    <div class="tab-actions-bar">
      <div class="info-block">
        <h3 class="tab-title">{{ t('tenants_mgmt.audit_title', 'Historial Forense WORM de Módulos') }}</h3>
        <p class="tab-subtitle">
          {{ t('tenants_mgmt.audit_subtitle', 'Trazabilidad criptográfica inmutable de cambios de licenciamiento y arquetipos') }}
        </p>
      </div>
      <button
        type="button"
        class="btn-refresh-audit"
        :disabled="isLoading"
        :aria-label="t('common.refresh', 'Refrescar')"
        @click="fetchAuditHistory"
      >
        <span aria-hidden="true">↻</span>
        <span>{{ t('common.refresh', 'Refrescar') }}</span>
      </button>
    </div>

    <!-- Estado de Carga -->
    <div v-if="isLoading" class="audit-state-box">
      <span class="spinner" aria-hidden="true">⏳</span>
      <p>{{ t('common.loading', 'Cargando registros de auditoría...') }}</p>
    </div>

    <!-- Estado de Error -->
    <div v-else-if="errorMessage" class="audit-state-box audit-state-box--error" role="alert">
      <span>⚠️</span>
      <p>{{ errorMessage }}</p>
      <button type="button" class="btn-retry" @click="fetchAuditHistory">
        {{ t('common.refresh', 'Reintentar') }}
      </button>
    </div>

    <!-- Lista Vacía -->
    <div v-else-if="records.length === 0" class="audit-state-box">
      <span class="empty-icon" aria-hidden="true">📜</span>
      <p class="empty-title">{{ t('tenants_mgmt.audit_empty_title', 'Sin modificaciones registradas') }}</p>
      <p class="empty-desc">
        {{ t('tenants_mgmt.audit_empty_desc', 'Aún no se han ejecutado cambios de capacidades o arquetipos sobre esta empresa.') }}
      </p>
    </div>

    <!-- Tabla Forense de Auditoría -->
    <div v-else class="table-wrapper">
      <table class="audit-table" aria-label="Tabla de eventos de modificación de módulos">
        <thead>
          <tr>
            <th scope="col">{{ t('tenants_mgmt.th_datetime', 'Fecha / Hora') }}</th>
            <th scope="col">{{ t('tenants_mgmt.th_operator', 'Operador') }}</th>
            <th scope="col">{{ t('tenants_mgmt.th_role', 'Rol & Origen IP') }}</th>
            <th scope="col">{{ t('tenants_mgmt.th_changes', 'Módulos Modificados') }}</th>
            <th scope="col" class="th-actions">{{ t('tenants_mgmt.th_actions', 'Acción') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in records" :key="r.id" class="audit-row">
            <td class="cell-time font-mono">
              {{ formatTimestamp(r.created_at) }}
            </td>
            <td class="cell-actor">
              <strong>@{{ r.actor_username }}</strong>
            </td>
            <td class="cell-meta">
              <span class="role-badge">{{ r.actor_role }}</span>
              <span class="ip-tag font-mono">{{ r.actor_ip }}</span>
            </td>
            <td class="cell-diff">
              <div class="diff-chips-list">
                <span
                  v-for="(c, idx) in summarizeDiff(r.before_state, r.after_state)"
                  :key="idx"
                  class="diff-chip"
                >
                  {{ c }}
                </span>
              </div>
            </td>
            <td class="cell-actions">
              <button
                v-if="r.before_state && Object.keys(r.before_state).length > 0"
                type="button"
                class="btn-rollback"
                :title="t('tenants_mgmt.rollback_title', 'Cargar estos valores en el formulario para revisión')"
                @click="handleRollbackClick(r)"
              >
                <span aria-hidden="true">⤺</span>
                <span>{{ t('tenants_mgmt.btn_rollback', 'Cargar esta versión') }}</span>
              </button>
              <span v-else class="text-subtle text-xs">-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
  .tenant-audit-tab {
    display: flex;
    flex-direction: column;
    gap: 16px;
    background: var(--rg-bg-surface, #0f172a);
    border: 1px solid var(--rg-border-panel, #1e293b);
    border-radius: 8px;
    padding: 16px 20px;
  }

  .tab-actions-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    padding-bottom: 12px;
  }

  .tab-title {
    font-size: 15px;
    font-weight: 700;
    color: var(--rg-text-primary, #f1f5f9);
    margin: 0 0 4px 0;
  }

  .tab-subtitle {
    font-size: 12px;
    color: var(--rg-text-muted, #94a3b8);
    margin: 0;
  }

  .btn-refresh-audit {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(148, 163, 184, 0.25);
    border-radius: 6px;
    color: var(--rg-text-primary, #f1f5f9);
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-refresh-audit:hover:not(:disabled) {
    border-color: var(--rg-accent-cyan, #06b6d4);
    color: var(--rg-accent-cyan, #06b6d4);
  }

  .audit-state-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    gap: 8px;
    color: var(--rg-text-muted, #94a3b8);
    text-align: center;
  }

  .audit-state-box--error {
    color: #ef4444;
  }

  .btn-retry {
    margin-top: 8px;
    padding: 6px 14px;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    border-radius: 4px;
    color: #fca5a5;
    cursor: pointer;
  }

  .empty-icon {
    font-size: 32px;
  }

  .empty-title {
    font-size: 14px;
    font-weight: 700;
    color: var(--rg-text-primary, #f1f5f9);
    margin: 0;
  }

  .empty-desc {
    font-size: 12px;
    margin: 0;
  }

  .table-wrapper {
    overflow-x: auto;
  }

  .audit-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    text-align: left;
  }

  .audit-table th {
    background: rgba(15, 23, 42, 0.9);
    color: var(--rg-text-muted, #94a3b8);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 10px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .audit-table td {
    padding: 10px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    color: var(--rg-text-primary, #f1f5f9);
    vertical-align: middle;
  }

  .audit-row:hover td {
    background: rgba(6, 182, 212, 0.04);
  }

  .cell-time {
    color: var(--rg-text-muted, #94a3b8);
    font-size: 11px;
    white-space: nowrap;
  }

  .cell-actor {
    color: var(--rg-accent-cyan, #06b6d4);
  }

  .cell-meta {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .role-badge {
    font-size: 10px;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(148, 163, 184, 0.2);
    padding: 2px 6px;
    border-radius: 4px;
    display: inline-block;
    width: fit-content;
  }

  .ip-tag {
    font-size: 10px;
    color: var(--rg-text-muted, #94a3b8);
  }

  .diff-chips-list {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .diff-chip {
    font-size: 11px;
    font-family: var(--rg-font-mono, monospace);
    background: rgba(6, 182, 212, 0.1);
    border: 1px solid rgba(6, 182, 212, 0.25);
    color: var(--rg-accent-cyan, #06b6d4);
    padding: 2px 6px;
    border-radius: 4px;
  }

  .cell-actions {
    text-align: right;
    white-space: nowrap;
  }

  .btn-rollback {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 10px;
    background: rgba(6, 182, 212, 0.15);
    border: 1px solid rgba(6, 182, 212, 0.4);
    border-radius: 4px;
    color: var(--rg-accent-cyan, #06b6d4);
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-rollback:hover {
    background: var(--rg-accent-cyan, #06b6d4);
    color: #0b0f19;
    box-shadow: 0 0 10px rgba(6, 182, 212, 0.4);
  }
</style>
