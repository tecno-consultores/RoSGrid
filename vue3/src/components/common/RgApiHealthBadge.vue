<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
  import { useApiHeartbeatStore } from '@/stores/useApiHeartbeatStore';

  const heartbeatStore = useApiHeartbeatStore();

  const isPopoverOpen = ref(false);
  const badgeContainerRef = ref<HTMLElement | null>(null);

  const statusLabel = computed(() => {
    switch (heartbeatStore.status) {
      case 'online':
        return heartbeatStore.latencyMs !== null ? `${heartbeatStore.latencyMs}ms` : 'ONLINE';
      case 'offline':
        return 'OFFLINE';
      case 'degraded':
        return 'DEGRADADO';
      case 'checking':
        return 'PING...';
      default:
        return 'DESCONOCIDO';
    }
  });

  const statusAriaText = computed(() => {
    switch (heartbeatStore.status) {
      case 'online':
        return `Backend API Operativo. Latencia: ${heartbeatStore.latencyMs ?? 0} milisegundos`;
      case 'offline':
        return 'Backend API Fuera de Línea. No hay conexión con el servidor';
      case 'degraded':
        return 'Backend API Degradado. Servicios dependientes no disponibles';
      case 'checking':
        return 'Comprobando conectividad con el backend';
      default:
        return 'Estado de conexión desconocido';
    }
  });

  function togglePopover(): void {
    isPopoverOpen.value = !isPopoverOpen.value;
  }

  function closePopover(): void {
    isPopoverOpen.value = false;
  }

  async function handleManualCheck(e?: Event): Promise<void> {
    if (e) e.stopPropagation();
    await heartbeatStore.checkHealth(true);
  }

  function onDocumentClick(e: MouseEvent): void {
    if (badgeContainerRef.value && !badgeContainerRef.value.contains(e.target as Node)) {
      isPopoverOpen.value = false;
    }
  }

  function onKeydown(e: KeyboardEvent): void {
    if (e.key === 'Escape' && isPopoverOpen.value) {
      isPopoverOpen.value = false;
    }
  }

  onMounted(() => {
    if (typeof document !== 'undefined') {
      document.addEventListener('click', onDocumentClick);
      document.addEventListener('keydown', onKeydown);
    }
  });

  onBeforeUnmount(() => {
    if (typeof document !== 'undefined') {
      document.removeEventListener('click', onDocumentClick);
      document.removeEventListener('keydown', onKeydown);
    }
  });
</script>

<template>
  <div
    ref="badgeContainerRef"
    class="rg-health-badge-container"
    role="region"
    aria-label="Indicador de salud y disponibilidad del API"
  >
    <button
      type="button"
      id="api-health-badge"
      class="rg-health-badge font-mono"
      :class="[
        `rg-health-badge--${heartbeatStore.status}`,
        { 'rg-health-badge--active': isPopoverOpen },
      ]"
      role="status"
      aria-live="polite"
      :aria-label="`${statusAriaText}. Haga clic para ver detalles o reintentar ping.`"
      :aria-expanded="isPopoverOpen"
      aria-haspopup="dialog"
      :title="`${statusAriaText}. Clic para detalles.`"
      @click="togglePopover"
    >
      <span class="status-dot" :class="`status-dot--${heartbeatStore.status}`" aria-hidden="true">
        <span v-if="heartbeatStore.isChecking" class="dot-spinner"></span>
      </span>
      <span class="status-prefix">API</span>
      <span class="status-val">{{ statusLabel }}</span>
    </button>

    <!-- Popover Táctico con Diagnóstico de Conexión en Vivo -->
    <transition name="popover-fade">
      <div
        v-if="isPopoverOpen"
        class="rg-health-popover"
        role="dialog"
        aria-modal="false"
        aria-labelledby="health-popover-title"
      >
        <div class="popover-header">
          <span class="popover-title" id="health-popover-title">
            <span class="popover-icon" aria-hidden="true">⚡</span>
            Telemetría Backend
          </span>
          <div class="popover-actions">
            <span
              class="popover-status-tag font-mono"
              :class="`status-tag--${heartbeatStore.status}`"
            >
              {{ heartbeatStore.status.toUpperCase() }}
            </span>
            <button
              type="button"
              class="btn-popover-close"
              aria-label="Cerrar panel de telemetría"
              @click="closePopover"
            >
              ✕
            </button>
          </div>
        </div>

        <div class="popover-body font-mono">
          <div class="metric-row">
            <span class="metric-label">Latencia:</span>
            <span class="metric-value" :class="{ 'text-success': heartbeatStore.isOnline }">
              {{ heartbeatStore.latencyMs !== null ? `${heartbeatStore.latencyMs} ms` : 'N/A' }}
            </span>
          </div>

          <div class="metric-row">
            <span class="metric-label">FastAPI Core:</span>
            <span
              class="metric-value"
              :class="heartbeatStore.isOnline ? 'text-success' : 'text-danger'"
            >
              {{ heartbeatStore.isOnline ? 'RESPONDIENDO (200 OK)' : 'SIN RESPUESTA' }}
            </span>
          </div>

          <div class="metric-row">
            <span class="metric-label">PostgreSQL:</span>
            <span
              class="metric-value"
              :class="heartbeatStore.services?.database === 'connected' ? 'text-success' : 'text-warning'"
            >
              {{ heartbeatStore.services?.database === 'connected' ? 'CONECTADO' : (heartbeatStore.services?.database || 'DESCONOCIDO') }}
            </span>
          </div>

          <div class="metric-row">
            <span class="metric-label">KeyDB Caché:</span>
            <span
              class="metric-value"
              :class="heartbeatStore.services?.redis === 'connected' ? 'text-success' : 'text-warning'"
            >
              {{ heartbeatStore.services?.redis === 'connected' ? 'CONECTADO' : (heartbeatStore.services?.redis || 'DESCONOCIDO') }}
            </span>
          </div>

          <div v-if="heartbeatStore.lastError" class="metric-error">
            <span class="error-label">Diagnóstico:</span>
            <span class="error-msg">{{ heartbeatStore.lastError }}</span>
          </div>
        </div>

        <div class="popover-footer">
          <button
            type="button"
            class="btn-ping-action"
            :disabled="heartbeatStore.isChecking"
            aria-label="Ejecutar comprobación de salud del API ahora"
            @click="handleManualCheck"
          >
            <span v-if="heartbeatStore.isChecking" class="btn-spinner" aria-hidden="true">⏳</span>
            <span v-else class="btn-icon" aria-hidden="true">🔄</span>
            {{ heartbeatStore.isChecking ? 'Verificando...' : 'Reintentar Ping Ahora' }}
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
  .rg-health-badge-container {
    position: relative;
    display: inline-flex;
    align-items: center;
  }

  .rg-health-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: var(--rg-bg-canvas, rgba(15, 23, 42, 0.7));
    border: 1px solid var(--rg-border-panel, rgba(56, 189, 248, 0.25));
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    color: var(--rg-text-primary, #f8fafc);
  }

  .rg-health-badge:hover {
    border-color: var(--rg-accent-cyan, #22d3ee);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }

  .rg-health-badge:focus-visible {
    outline: 2px solid var(--rg-accent-cyan, #22d3ee);
    outline-offset: 2px;
  }

  .rg-health-badge--online {
    border-color: rgba(16, 185, 129, 0.35);
  }

  .rg-health-badge--online .status-val {
    color: var(--rg-status-online, #10b981);
  }

  .rg-health-badge--offline {
    background: rgba(239, 68, 68, 0.12);
    border-color: rgba(239, 68, 68, 0.6);
  }

  .rg-health-badge--offline .status-val {
    color: var(--rg-status-critical, #ef4444);
    font-weight: 800;
  }

  .rg-health-badge--degraded {
    background: rgba(245, 158, 11, 0.12);
    border-color: rgba(245, 158, 11, 0.6);
  }

  .rg-health-badge--degraded .status-val {
    color: var(--rg-status-warning, #f59e0b);
  }

  .rg-health-badge--checking {
    border-color: var(--rg-accent-cyan, #22d3ee);
  }

  .status-prefix {
    color: var(--rg-text-secondary, #94a3b8);
    font-size: 0.72rem;
    letter-spacing: 0.06em;
  }

  .status-dot {
    position: relative;
    width: 9px;
    height: 9px;
    border-radius: 50%;
    display: inline-block;
  }

  .status-dot--online {
    background: #10b981;
    box-shadow: 0 0 8px #10b981;
    animation: pulse-online 2.5s infinite;
  }

  .status-dot--offline {
    background: #ef4444;
    box-shadow: 0 0 10px #ef4444;
    animation: flash-offline 1s infinite alternate;
  }

  .status-dot--degraded {
    background: #f59e0b;
    box-shadow: 0 0 8px #f59e0b;
    animation: pulse-online 2s infinite;
  }

  .status-dot--checking {
    background: #06b6d4;
    box-shadow: 0 0 6px #06b6d4;
  }

  @keyframes pulse-online {
    0% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.6;
      transform: scale(0.9);
    }
    100% {
      opacity: 1;
      transform: scale(1);
    }
  }

  @keyframes flash-offline {
    0% {
      opacity: 1;
      transform: scale(1.15);
    }
    100% {
      opacity: 0.3;
      transform: scale(0.85);
    }
  }

  /* Popover Táctico */
  .rg-health-popover {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    width: 290px;
    background: var(--rg-bg-surface, #0f172a);
    border: 1px solid var(--rg-border-panel, rgba(56, 189, 248, 0.3));
    border-radius: 8px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 0 15px rgba(6, 182, 212, 0.15);
    z-index: 1000;
    padding: 12px;
    backdrop-filter: blur(8px);
  }

  .popover-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--rg-border-grid, rgba(255, 255, 255, 0.1));
    padding-bottom: 8px;
    margin-bottom: 10px;
  }

  .popover-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--rg-accent-cyan, #22d3ee);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .popover-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .btn-popover-close {
    background: transparent;
    border: none;
    color: var(--rg-text-secondary, #94a3b8);
    cursor: pointer;
    font-size: 0.8rem;
    padding: 2px 4px;
    border-radius: 3px;
    line-height: 1;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .btn-popover-close:hover {
    color: var(--rg-text-primary, #f8fafc);
    background: rgba(255, 255, 255, 0.1);
  }

  .popover-status-tag {
    font-size: 0.7rem;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 700;
  }

  .status-tag--online {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.4);
  }

  .status-tag--offline {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.4);
  }

  .status-tag--degraded {
    background: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.4);
  }

  .status-tag--checking {
    background: rgba(6, 182, 212, 0.15);
    color: #06b6d4;
    border: 1px solid rgba(6, 182, 212, 0.4);
  }

  .popover-body {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 0.78rem;
    margin-bottom: 12px;
  }

  .metric-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .metric-label {
    color: var(--rg-text-secondary, #94a3b8);
  }

  .metric-value {
    font-weight: 600;
  }

  .text-success {
    color: #10b981;
  }

  .text-danger {
    color: #ef4444;
  }

  .text-warning {
    color: #f59e0b;
  }

  .metric-error {
    background: rgba(239, 68, 68, 0.1);
    border-left: 2px solid #ef4444;
    padding: 4px 6px;
    margin-top: 4px;
    border-radius: 0 4px 4px 0;
    font-size: 0.72rem;
  }

  .error-label {
    color: #ef4444;
    font-weight: 700;
    display: block;
  }

  .error-msg {
    color: var(--rg-text-primary, #f8fafc);
    word-break: break-all;
  }

  .popover-footer {
    border-top: 1px solid var(--rg-border-grid, rgba(255, 255, 255, 0.1));
    padding-top: 8px;
  }

  .btn-ping-action {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid var(--rg-border-panel, rgba(56, 189, 248, 0.3));
    color: var(--rg-accent-cyan, #22d3ee);
    padding: 6px 12px;
    border-radius: 5px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-ping-action:hover:not(:disabled) {
    background: rgba(56, 189, 248, 0.2);
    border-color: var(--rg-accent-cyan, #22d3ee);
  }

  .btn-ping-action:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .popover-fade-enter-active,
  .popover-fade-leave-active {
    transition: opacity 0.15s ease, transform 0.15s ease;
  }

  .popover-fade-enter-from,
  .popover-fade-leave-to {
    opacity: 0;
    transform: translateY(-4px);
  }

  /* Accesibilidad WCAG 2.1 AA - Respetar preferencia de reducción de movimiento */
  @media (prefers-reduced-motion: reduce) {
    .status-dot--online,
    .status-dot--offline,
    .status-dot--degraded {
      animation: none !important;
    }
  }

  @media (max-width: 640px) {
    .rg-health-badge {
      padding: 4px 7px;
      gap: 5px;
      font-size: 0.75rem;
    }

    .status-prefix {
      display: none;
    }

    .rg-health-popover {
      position: fixed;
      top: 58px;
      left: 8px;
      right: 8px;
      width: auto;
      max-width: calc(100dvw - 16px);
    }
  }
</style>
