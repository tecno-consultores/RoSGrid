<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { http } from '@/api/httpClient';
  import { useAuthStore } from '@/stores/useAuthStore';
  import type { ApprovalRequestItem } from '@/types';

  const authStore = useAuthStore();

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
      const res = await http.get<{ items: ApprovalRequestItem[] } | ApprovalRequestItem[]>(
        '/api/v1/operations/approvals',
      );
      const raw = Array.isArray(res.data) ? res.data : res.data?.items || [];
      requests.value = raw;
    } catch {
      // Sin datos de demostración en producción
      requests.value = [];
    } finally {
      isLoading.value = false;
      if (filteredRequests.value.length > 0 && !selectedRequest.value) {
        selectedRequest.value = filteredRequests.value[0];
      }
    }
  }

  function isSelfApproval(request: ApprovalRequestItem): boolean {
    return Boolean(authStore.user?.id && request.requested_by === authStore.user.id);
  }

  async function handleApprove(request: ApprovalRequestItem) {
    if (isSelfApproval(request)) return;
    try {
      await http.post(`/api/v1/operations/approvals/${request.id}/approve`, {
        comment: reviewComment.value || 'Aprobado con Safe Mode (60s)',
      });
      request.status = 'APPROVED';
      actionMessage.value = `Solicitud ${request.id} aprobada y ejecutada en ${request.router_name}.`;
      reviewComment.value = '';
      setTimeout(() => {
        actionMessage.value = '';
      }, 4000);
    } catch (err: any) {
      errorMessage.value =
        err?.response?.data?.detail || err?.message || 'Error al aprobar solicitud en el servidor';
      setTimeout(() => {
        errorMessage.value = '';
      }, 4000);
    }
  }

  async function handleReject(request: ApprovalRequestItem) {
    try {
      await http.post(`/api/v1/operations/approvals/${request.id}/reject`, {
        comment: reviewComment.value || 'Rechazado por incumplimiento de política de seguridad',
      });
      request.status = 'REJECTED';
      actionMessage.value = `Solicitud ${request.id} rechazada.`;
      reviewComment.value = '';
      setTimeout(() => {
        actionMessage.value = '';
      }, 4000);
    } catch (err: any) {
      errorMessage.value =
        err?.response?.data?.detail || err?.message || 'Error al rechazar solicitud en el servidor';
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
        <h1 class="view-title">Bandeja de Aprobaciones — Maker-Checker</h1>
        <p class="view-subtitle">
          Control de cuatro ojos (Four-Eyes Principle) para cambios críticos de red con Safe Mode
          (60s)
        </p>
      </div>

      <!-- Pestañas de Aprobación -->
      <nav class="subtabs-bar" role="tablist" aria-label="Estados de solicitudes Maker-Checker">
        <button
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === 'pending' }"
          role="tab"
          :aria-selected="activeTab === 'pending'"
          @click="activeTab = 'pending'"
        >
          Pendientes de Firma
        </button>
        <button
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === 'approved' }"
          role="tab"
          :aria-selected="activeTab === 'approved'"
          @click="activeTab = 'approved'"
        >
          Aprobadas y Ejecutadas
        </button>
        <button
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === 'rejected' }"
          role="tab"
          :aria-selected="activeTab === 'rejected'"
          @click="activeTab = 'rejected'"
        >
          Rechazadas / Expiradas
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
          :aria-label="`Inspeccionar solicitud ${appr.id}`"
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
            <span v-if="isSelfApproval(appr)" class="self-flag font-bold">🚫 Tu solicitud</span>
          </div>
        </div>

        <div v-if="filteredRequests.length === 0" class="empty-inbox">
          No hay solicitudes en esta bandeja.
        </div>
      </div>

      <!-- Tarjeta de Inspección Técnica (JSON Previo vs Propuesto) -->
      <div v-if="selectedRequest" class="inspector-panel font-tabular">
        <div class="inspector-header">
          <h2 class="inspector-title">Inspección de Solicitud #{{ selectedRequest.id }}</h2>
          <span class="badge-status">{{ selectedRequest.status }}</span>
        </div>

        <div class="inspector-details">
          <p>
            <strong>Equipo Destino:</strong> {{ selectedRequest.router_name }} ({{
              selectedRequest.router_id
            }})
          </p>
          <p>
            <strong>Solicitante:</strong> @{{ selectedRequest.requested_by_username }} (Rol:
            {{ selectedRequest.requested_by_role }})
          </p>
          <p><strong>Motivo / Justificación:</strong> {{ selectedRequest.justification }}</p>
        </div>

        <!-- Comparador JSON Previo vs Propuesto -->
        <div class="diff-json-grid">
          <div class="json-box">
            <span class="json-title text-amber">Estado Previo en MikroTik</span>
            <pre class="json-pre">{{
              JSON.stringify(selectedRequest.previous_state_snapshot, null, 2)
            }}</pre>
          </div>

          <div class="json-box">
            <span class="json-title text-emerald">Cambio Propuesto (A Aplicar)</span>
            <pre class="json-pre">{{
              JSON.stringify(selectedRequest.request_payload, null, 2)
            }}</pre>
          </div>
        </div>

        <!-- Acciones Maker-Checker -->
        <div v-if="selectedRequest.status === 'AWAITING_APPROVAL'" class="actions-panel">
          <div v-if="isSelfApproval(selectedRequest)" class="banner banner--warning font-bold">
            ⛔ Segregación de funciones: Como solicitante no puedes aprobar tu propio cambio. Se
            requiere firma de otro Supervisor o N3.
          </div>

          <div class="comment-group">
            <label for="review-comment" class="form-label">Comentario de Revisión:</label>
            <input
              id="review-comment"
              v-model="reviewComment"
              type="text"
              placeholder="Escribe un comentario técnico o ticket de respaldo..."
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
              ✕ Rechazar Solicitud
            </button>

            <button
              type="button"
              class="btn-approve"
              :disabled="!isCheckerAuthorized || isSelfApproval(selectedRequest)"
              @click="handleApprove(selectedRequest)"
            >
              ✓ Aprobar y Ejecutar con Safe Mode (60s)
            </button>
          </div>
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

  @media (max-width: 900px) {
    .approvals-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
