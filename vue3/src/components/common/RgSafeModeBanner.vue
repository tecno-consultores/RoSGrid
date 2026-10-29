<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { computed } from 'vue';
  import { useWebFigStore } from '@/stores/useWebFigStore';

  const webFigStore = useWebFigStore();

  const isLowTime = computed(() => webFigStore.safeModeCountdownSeconds <= 15);
</script>

<template>
  <!-- Banner En Espera de Aprobación Humana (Maker-Checker — Sin cuenta regresiva de 60s) -->
  <aside
    v-if="webFigStore.isMakerCheckerPending"
    class="rg-maker-checker-banner"
    role="status"
    aria-live="polite"
    aria-label="Estado de Solicitud en Espera de Aprobación Maker-Checker"
  >
    <div class="banner-content">
      <span class="banner-icon" aria-hidden="true">⏳</span>
      <div class="banner-text">
        <strong class="banner-title">EN ESPERA DE APROBACIÓN HUMANA (Maker-Checker)</strong>
        <span class="banner-desc">
          {{
            webFigStore.makerCheckerMessage ||
            'Esta operación requiere autorización de un Supervisor, Nivel 3 o Administrador antes de aplicarse en el router (sin límite de 60s).'
          }}
        </span>
      </div>
      <div class="banner-badge-pending">
        <span class="badge-pending-val">PENDIENTE DE REVISIÓN</span>
      </div>
      <button
        type="button"
        class="banner-btn banner-btn--mc"
        aria-label="Cerrar notificación de espera Maker-Checker"
        @click="webFigStore.dismissMakerCheckerPending()"
      >
        Entendido
      </button>
    </div>
  </aside>

  <!-- Banner Safe Mode Activo (60s Rollback — Solo para cambios aplicados directamente en el router) -->
  <aside
    v-else-if="webFigStore.isSafeModeActive"
    class="rg-safemode-banner"
    :class="{ 'rg-safemode-banner--warning': isLowTime }"
    role="status"
    aria-live="polite"
    aria-label="Estado de Safe Mode y Dead Man's Switch"
  >
    <div class="banner-content">
      <span class="banner-icon" aria-hidden="true">⚠️</span>
      <div class="banner-text">
        <strong class="banner-title">SAFE MODE ACTIVO (Dead Man's Switch)</strong>
        <span class="banner-desc">
          Verificando conectividad con el router. Los cambios se revertirán automáticamente en:
        </span>
      </div>
      <div class="banner-countdown" :class="{ 'pulse-anim': isLowTime }">
        <span class="countdown-val">{{ webFigStore.safeModeCountdownSeconds }}s</span>
      </div>
      <button
        type="button"
        class="banner-btn"
        aria-label="Confirmar cambios y desactivar Safe Mode"
        @click="webFigStore.stopSafeMode()"
      >
        Confirmar Cambios
      </button>
    </div>
  </aside>
</template>

<style scoped>
  .rg-maker-checker-banner {
    background: var(--rg-accent-subtle, rgba(6, 182, 212, 0.14));
    border-bottom: 2px solid var(--rg-accent-primary, #06b6d4);
    color: var(--rg-text-primary);
    padding: 8px 16px;
    position: sticky;
    top: 0;
    z-index: 900;
    box-shadow: 0 4px 12px rgba(6, 182, 212, 0.18);
  }

  .banner-badge-pending {
    background: rgba(6, 182, 212, 0.15);
    padding: 4px 10px;
    border-radius: 4px;
    border: 1px solid var(--rg-accent-primary, #06b6d4);
  }

  .badge-pending-val {
    font-family: var(--rg-font-mono);
    font-weight: 700;
    font-size: 11px;
    color: var(--rg-accent-primary, #06b6d4);
    letter-spacing: 0.4px;
  }

  .banner-btn--mc {
    border-color: var(--rg-accent-primary, #06b6d4);
    color: var(--rg-accent-primary, #06b6d4);
  }

  .rg-safemode-banner {
    background: var(--rg-status-warning-bg);
    border-bottom: 2px solid var(--rg-status-warning);
    color: var(--rg-status-warning-text);
    padding: 8px 16px;
    position: sticky;
    top: 0;
    z-index: 900;
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
  }

  .rg-safemode-banner--warning {
    background: var(--rg-status-critical-bg);
    border-bottom-color: var(--rg-status-critical);
    color: var(--rg-status-critical-text);
  }

  .banner-content {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .banner-icon {
    font-size: 20px;
  }

  .banner-text {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .banner-title {
    font-size: 13px;
    letter-spacing: 0.5px;
  }

  .banner-desc {
    font-size: 12px;
    opacity: 0.9;
  }

  .banner-countdown {
    background: rgba(0, 0, 0, 0.3);
    padding: 4px 10px;
    border-radius: 4px;
    border: 1px solid currentColor;
  }

  .countdown-val {
    font-family: var(--rg-font-mono);
    font-weight: 700;
    font-size: 16px;
  }

  .banner-btn {
    background: var(--rg-bg-surface);
    border: 1px solid currentColor;
    color: inherit;
    padding: 6px 12px;
    border-radius: 4px;
    font-weight: 600;
    font-size: 12px;
    cursor: pointer;
  }

  .banner-btn:hover {
    background: var(--rg-bg-elevated);
  }

  @keyframes pulse {
    0% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.08);
    }
    100% {
      transform: scale(1);
    }
  }

  .pulse-anim {
    animation: pulse 1s infinite ease-in-out;
  }
</style>
