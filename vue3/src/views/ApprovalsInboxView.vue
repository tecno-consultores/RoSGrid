<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { http } from '@/api/httpClient';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useI18n } from '@/composables/useI18n';
  import type { ApprovalRequestItem } from '@/types';

  const authStore = useAuthStore();
  const { t } = useI18n();

  const activeTab = ref<'pending' | 'approved' | 'rejected'>('pending');
  const isLoading = ref(false);
  const requests = ref<ApprovalRequestItem[]>([]);
  const selectedRequest = ref<ApprovalRequestItem | null>(null);
  const reviewComment = ref('');
  const actionMessage = ref('');
  const errorMessage = ref('');

  const isCheckerAuthorized = computed(() => {
    const role = authStore.currentRole;
    return (
      role === 'SUPERADMIN_GLOBAL' ||
      role === 'TENANT_ADMIN' ||
      role === 'SUPERVISOR' ||
      role === 'SUPPORT_L3'
    );
  });

  const filteredRequests = computed(() => {
    return requests.value.filter((r) => {
      if (activeTab.value === 'pending') return r.status === 'AWAITING_APPROVAL';
      if (activeTab.value === 'approved') return r.status === 'APPROVED';
      if (activeTab.value === 'rejected') return r.status === 'REJECTED' || r.status === 'EXPIRED';
      return true;
    });
  });

  async function loadApprovals() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.get<{ items: any[] } | any[]>(
        '/api/v1/operations/approvals',
      );
      const raw = Array.isArray(res.data) ? res.data : res.data?.items || [];
      requests.value = raw.map((item: any) => ({
        ...item,
        id: String(item.id),
        requested_by: String(item.requested_by || ''),
        requested_by_username: item.requested_by_username || 'operador_solicitante',
        requested_by_role: item.requested_by_role || 'SUPPORT_L2',
        router_id: item.router_id ? String(item.router_id) : 'N/A',
        router_name: item.router_name || item.summary || 'Router MikroTik',
        justification: item.justification || item.requester_justification || item.summary || 'Operación técnica',
        status: item.status === 'PENDING' ? 'AWAITING_APPROVAL' : (item.status?.startsWith('APPROVED') ? 'APPROVED' : item.status),
      }));
    } catch {
      // Sin datos de demostración en producción
      requests.value = [];
    } finally {
      isLoading.value = false;
      if (
        selectedRequest.value &&
        !filteredRequests.value.some((r) => r.id === selectedRequest.value?.id)
      ) {
        selectedRequest.value = filteredRequests.value[0] || null;
      } else if (filteredRequests.value.length > 0 && !selectedRequest.value) {
        selectedRequest.value = filteredRequests.value[0];
      }
    }
  }

  function isSelfApproval(request: ApprovalRequestItem): boolean {
    if (authStore.currentRole === 'SUPERADMIN_GLOBAL') return false;
    return Boolean(authStore.user?.id && request.requested_by === authStore.user.id);
  }

  async function handleApprove(request: ApprovalRequestItem) {
    if (isSelfApproval(request)) return;
    try {
      const res = await http.post<any>(`/api/v1/operations/approvals/${request.id}/approve`, {
        review_comment: reviewComment.value || 'Aprobado y ejecutado por Supervisor/Administrador',
      });
      request.status = 'APPROVED';
      if (res.data?.execution_result) {
        request.execution_result = res.data.execution_result;
      }
      actionMessage.value = `Solicitud ${request.id} aprobada y ejecutada en la flota MikroTik.`;
      reviewComment.value = '';
      setTimeout(() => {
        actionMessage.value = '';
      }, 4000);
      await loadApprovals();
    } catch (err: any) {
      errorMessage.value =
        err?.detail ||
        err?.response?.data?.detail ||
        err?.message ||
        'Error al aprobar solicitud en el servidor';
      setTimeout(() => {
        errorMessage.value = '';
      }, 4000);
    }
  }

  async function handleReject(request: ApprovalRequestItem) {
    try {
      await http.post(`/api/v1/operations/approvals/${request.id}/reject`, {
        review_comment: reviewComment.value || 'Rechazado por incumplimiento de política de seguridad',
      });
      request.status = 'REJECTED';
      actionMessage.value = `Solicitud ${request.id} rechazada.`;
      reviewComment.value = '';
      setTimeout(() => {
        actionMessage.value = '';
      }, 4000);
      await loadApprovals();
    } catch (err: any) {
      errorMessage.value =
        err?.detail ||
        err?.response?.data?.detail ||
        err?.message ||
        'Error al rechazar solicitud en el servidor';
      setTimeout(() => {
        errorMessage.value = '';
      }, 4000);
    }
  }

  onMounted(() => {
    loadApprovals();
  });
</script>

<template>
  <div class="approvals-view">
    <header class="view-header">
      <div>
        <h1 class="view-title">{{ t('approvals.title') }}</h1>
        <p class="view-subtitle">
          {{ t('approvals.subtitle') }}
        </p>
      </div>

      <!-- Pestañas de Aprobación -->
      <nav class="subtabs-bar" role="tablist" :aria-label="t('approvals.subtabs_aria')">
        <button
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === 'pending' }"
          role="tab"
          :aria-selected="activeTab === 'pending'"
          @click="activeTab = 'pending'"
        >
          {{ t('approvals.tab_pending') }}
        </button>
        <button
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === 'approved' }"
          role="tab"
          :aria-selected="activeTab === 'approved'"
          @click="activeTab = 'approved'"
        >
          {{ t('approvals.tab_approved') }}
        </button>
        <button
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === 'rejected' }"
          role="tab"
          :aria-selected="activeTab === 'rejected'"
          @click="activeTab = 'rejected'"
        >
          {{ t('approvals.tab_rejected') }}
        </button>
      </nav>
    </header>

    <div v-if="actionMessage" class="banner banner--success font-tabular" role="status">
      {{ actionMessage }}
    </div>

    <!-- Layout Dividido: Lista a la Izquierda, Inspección Técnica a la Derecha -->
    <div class="approvals-grid">
      <!-- Lista de Solicitudes -->
      <div class="inbox-list font-tabular">
        <div
          v-for="appr in filteredRequests"
          :key="appr.id"
          class="inbox-card"
          :class="{ 'inbox-card--selected': selectedRequest?.id === appr.id }"
          tabindex="0"
          role="button"
          :aria-label="t('approvals.inspect_aria', { id: appr.id })"
          @click="selectedRequest = appr"
          @keydown.enter="selectedRequest = appr"
        >
          <div class="card-header">
            <span class="badge-action">{{ appr.action_type }}</span>
            <span class="card-time">{{ new Date(appr.created_at).toLocaleTimeString() }}</span>
          </div>

          <strong class="router-target">📍 {{ appr.router_name }}</strong>
          <p class="card-justification">{{ appr.justification }}</p>

          <div class="card-footer">
            <span class="requester"
              >👤 @{{ appr.requested_by_username }} ({{ appr.requested_by_role }})</span
            >
            <span v-if="isSelfApproval(appr)" class="self-flag font-bold">{{ t('approvals.your_request') }}</span>
          </div>
        </div>

        <div v-if="filteredRequests.length === 0" class="empty-inbox">
          {{ t('approvals.empty_inbox') }}
        </div>
      </div>

      <!-- Tarjeta de Inspección Técnica (JSON Previo vs Propuesto) -->
      <div v-if="selectedRequest" class="inspector-panel font-tabular">
        <div class="inspector-header">
          <h2 class="inspector-title">{{ t('approvals.inspection_title', { id: selectedRequest.id }) }}</h2>
          <span class="badge-status">{{ selectedRequest.status }}</span>
        </div>

        <div class="inspector-details">
          <p>
            <strong>{{ t('approvals.target_device') }}</strong> {{ selectedRequest.router_name }} ({{
              selectedRequest.router_id
            }})
          </p>
          <p>
            <strong>{{ t('approvals.requester') }}</strong> @{{ selectedRequest.requested_by_username }} ({{ t('approvals.role_label') }}
            {{ selectedRequest.requested_by_role }})
          </p>
          <p><strong>{{ t('approvals.justification') }}</strong> {{ selectedRequest.justification }}</p>
        </div>

        <!-- Comparador JSON Previo vs Propuesto -->
        <div class="diff-json-grid">
          <div class="json-box">
            <span class="json-title text-amber">{{ t('approvals.prev_state') }}</span>
            <pre class="json-pre">{{
              JSON.stringify(selectedRequest.previous_state_snapshot, null, 2)
            }}</pre>
          </div>

          <div class="json-box">
            <span class="json-title text-emerald">{{ t('approvals.proposed_change') }}</span>
            <pre class="json-pre">{{
              JSON.stringify(selectedRequest.request_payload, null, 2)
            }}</pre>
          </div>
        </div>

        <!-- Acciones Maker-Checker -->
        <div v-if="selectedRequest.status === 'AWAITING_APPROVAL'" class="actions-panel">
          <div v-if="isSelfApproval(selectedRequest)" class="banner banner--warning font-bold">
            {{ t('approvals.self_approval_warning') }}
          </div>

          <div class="comment-group">
            <label for="review-comment" class="form-label">{{ t('approvals.review_comment_label') }}</label>
            <input
              id="review-comment"
              v-model="reviewComment"
              type="text"
              :placeholder="t('approvals.review_comment_placeholder')"
              class="form-input"
            />
          </div>

          <div class="buttons-row">
            <button
              type="button"
              class="btn-reject"
              :disabled="!isCheckerAuthorized"
              @click="handleReject(selectedRequest)"
            >
              {{ t('approvals.btn_reject') }}
            </button>

            <button
              type="button"
              class="btn-approve"
              :disabled="!isCheckerAuthorized || isSelfApproval(selectedRequest)"
              @click="handleApprove(selectedRequest)"
            >
              {{ t('approvals.btn_approve') }}
            </button>
          </div>
        </div>

        <!-- Resultado de la Ejecución en MikroTik -->
        <div v-else-if="selectedRequest.execution_result" class="execution-result-panel">
          <div class="result-header">
            <span class="font-bold text-cyan">{{ t('approvals.execution_result_title') }}</span>
            <span class="badge" :class="selectedRequest.status === 'APPROVED' ? 'badge--approved' : 'badge--rejected'">
              {{ selectedRequest.status === 'APPROVED' ? t('approvals.status_executed') : t('approvals.status_failed') }}
            </span>
          </div>
          <pre class="json-pre execution-json">{{ JSON.stringify(selectedRequest.execution_result, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .approvals-view {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .view-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
  }

  .view-title {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--rg-text-primary);
  }

  .view-subtitle {
    margin: 2px 0 0 0;
    font-size: 0.8rem;
    color: var(--rg-text-muted);
  }

  .subtabs-bar {
    display: flex;
    gap: 4px;
    background: var(--rg-bg-canvas);
    padding: 3px;
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
  }

  .btn-subtab {
    background: transparent;
    border: none;
    color: var(--rg-text-secondary);
    padding: 6px 14px;
    font-size: 0.8rem;
    border-radius: 4px;
    cursor: pointer;
  }

  .btn-subtab--active {
    background: var(--rg-bg-elevated);
    color: var(--rg-accent-cyan);
    font-weight: 600;
  }

  .banner--success {
    padding: 10px 14px;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    border-radius: 6px;
    color: #10b981;
    font-size: 0.85rem;
  }

  .banner--warning {
    padding: 8px 12px;
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid #f59e0b;
    border-radius: 6px;
    color: #f59e0b;
    font-size: 0.8rem;
  }

  .approvals-grid {
    display: grid;
    grid-template-columns: 360px 1fr;
    gap: 16px;
  }

  .inbox-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-height: calc(100vh - 200px);
    overflow-y: auto;
  }

  .inbox-card {
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-grid);
    border-radius: 8px;
    padding: 12px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .inbox-card:hover {
    border-color: var(--rg-accent-cyan);
  }

  .inbox-card--selected {
    border-color: var(--rg-accent-cyan);
    background: var(--rg-bg-elevated);
    box-shadow: 0 0 10px rgba(6, 182, 212, 0.2);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
  }

  .badge-action {
    background: rgba(6, 182, 212, 0.15);
    color: var(--rg-accent-cyan);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.72rem;
  }

  .card-time {
    font-size: 0.72rem;
    color: var(--rg-text-muted);
  }

  .router-target {
    font-size: 0.88rem;
    color: var(--rg-text-primary);
  }

  .card-justification {
    margin: 6px 0;
    font-size: 0.78rem;
    color: var(--rg-text-secondary);
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .card-footer {
    display: flex;
    justify-content: space-between;
    font-size: 0.72rem;
    color: var(--rg-text-muted);
    border-top: 1px solid var(--rg-border-grid);
    padding-top: 6px;
    margin-top: 4px;
  }

  .self-flag {
    color: #f59e0b;
  }

  .inspector-panel {
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-grid);
    border-radius: 8px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .inspector-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--rg-border-grid);
    padding-bottom: 10px;
  }

  .inspector-title {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 700;
  }

  .badge-status {
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    background: var(--rg-bg-elevated);
    color: var(--rg-accent-cyan);
  }

  .inspector-details {
    font-size: 0.82rem;
    color: var(--rg-text-secondary);
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .diff-json-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .json-box {
    background: #060911;
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .json-title {
    font-size: 0.75rem;
    font-weight: 600;
  }

  .json-pre {
    margin: 0;
    font-size: 0.75rem;
    color: #cbd5e1;
    max-height: 250px;
    overflow-y: auto;
  }

  .text-amber {
    color: #f59e0b;
  }

  .text-emerald {
    color: #10b981;
  }

  .actions-panel {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding-top: 10px;
    border-top: 1px solid var(--rg-border-grid);
  }

  .comment-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .form-label {
    font-size: 0.78rem;
    color: var(--rg-text-muted);
  }

  .form-input {
    padding: 6px 10px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    color: var(--rg-text-primary);
    font-size: 0.85rem;
  }

  .buttons-row {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }

  .btn-reject {
    padding: 8px 16px;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    border-radius: 6px;
    color: #ef4444;
    font-weight: 600;
    cursor: pointer;
  }

  .btn-approve {
    padding: 8px 18px;
    background: var(--rg-accent-cyan);
    border: none;
    border-radius: 6px;
    color: #0b0f19;
    font-weight: 700;
    cursor: pointer;
  }

  .btn-approve:disabled,
  .btn-reject:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .font-tabular {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  .font-bold {
    font-weight: 700;
  }

  .text-cyan {
    color: var(--rg-accent-cyan, #06b6d4);
  }

  .execution-result-panel {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: rgba(6, 182, 212, 0.05);
    border: 1px solid rgba(6, 182, 212, 0.3);
    border-radius: 6px;
    padding: 12px;
  }

  .result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .execution-json {
    max-height: 180px;
    font-size: 0.75rem;
  }

  @media (max-width: 900px) {
    .approvals-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
