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

  <!-- Banner Safe Mode Activo (60s Rollback con Verificación en Vivo y Confirmación Humana) -->
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
        <div class="banner-title-row">
          <strong class="banner-title">SAFE MODE ACTIVO (Dead Man's Switch)</strong>
          <span v-if="webFigStore.safeModeJobName" class="badge-job-name font-mono">
            Job: {{ webFigStore.safeModeJobName }}
          </span>
          <span
            v-if="webFigStore.safeModeLiveVerified"
            class="badge-verified safemode-badge--live font-tabular"
            id="badge-safemode-verified"
          >
            ✔ Verificado en RouterOS
            {{
              webFigStore.safeModeVerifyLatencyMs != null
                ? `(${webFigStore.safeModeVerifyLatencyMs} ms)`
                : ''
            }}
          </span>
        </div>
        <span class="banner-desc">
          {{
            webFigStore.safeModeSummary
              ? `Cambio en evaluación: ${webFigStore.safeModeSummary}. Reversión automática si expira el contador.`
              : 'Verificando conectividad con el router. Los cambios se revertirán automáticamente en:'
          }}
        </span>
      </div>

      <div class="banner-countdown" :class="{ 'pulse-anim': isLowTime }">
        <span class="countdown-val">{{ webFigStore.safeModeCountdownSeconds }}s</span>
      </div>

      <div class="banner-actions">
        <button
          id="btn-safemode-verify-live"
          type="button"
          class="banner-btn banner-btn--verify font-tabular"
          :disabled="webFigStore.isSafeModeBusy"
          aria-label="Verificar en vivo directamente en el router MikroTik sin usar WinBox"
          @click="webFigStore.verifySafeModeOnRouter()"
        >
          {{ webFigStore.isSafeModeBusy ? '🔍 Verificando...' : '🔍 Verificar en Equipo' }}
        </button>
        <button
          id="btn-safemode-rollback"
          type="button"
          class="banner-btn banner-btn--rollback font-tabular"
          :disabled="webFigStore.isSafeModeBusy"
          aria-label="Revertir el cambio inmediatamente en el router MikroTik"
          @click="webFigStore.rollbackSafeModeChanges(false)"
        >
          ↩️ Revertir Ahora
        </button>
        <button
          id="btn-safemode-confirm"
          type="button"
          class="banner-btn banner-btn--confirm font-tabular"
          :disabled="webFigStore.isSafeModeBusy"
          aria-label="Confirmar cambios y desactivar Safe Mode en el router"
          @click="webFigStore.confirmSafeModeChanges()"
        >
          ✅ Confirmar Cambios
        </button>
      </div>
    </div>
  </aside>

  <!-- Banner Informativo de Reversión Completada (Expiración o Rollback Manual) -->
  <aside
    v-else-if="webFigStore.safeModeRevertedNotice"
    class="rg-safemode-banner rg-safemode-banner--notice rg-safemode-reverted-notice"
    role="status"
    aria-live="polite"
    aria-label="Aviso de Reversión Safe Mode"
  >
    <div class="banner-content">
      <span class="banner-icon" aria-hidden="true">ℹ️</span>
      <div class="banner-text">
        <strong class="banner-title">REVERSIÓN EJECUTADA EN ROUTEROS</strong>
        <span class="banner-desc">{{ webFigStore.safeModeRevertedNotice }}</span>
      </div>
      <button
        id="btn-safemode-dismiss-notice"
        type="button"
        class="banner-btn"
        aria-label="Cerrar notificación de reversión"
        @click="webFigStore.dismissSafeModeRevertedNotice()"
      >
        Entendido
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

  .rg-safemode-banner--notice {
    background: var(--rg-accent-subtle, rgba(6, 182, 212, 0.14));
    border-bottom-color: var(--rg-accent-primary, #06b6d4);
    color: var(--rg-text-primary);
  }

  .banner-content {
    max-width: 1300px;
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
    min-width: 260px;
    gap: 2px;
  }

  .banner-title-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .banner-title {
    font-size: 13px;
    letter-spacing: 0.5px;
  }

  .badge-job-name {
    font-size: 10px;
    background: rgba(0, 0, 0, 0.25);
    padding: 2px 6px;
    border-radius: 3px;
    border: 1px solid currentColor;
    opacity: 0.85;
  }

  .badge-verified {
    font-size: 11px;
    background: var(--rg-status-success-bg, rgba(16, 185, 129, 0.2));
    color: var(--rg-status-success, #10b981);
    border: 1px solid currentColor;
    padding: 2px 6px;
    border-radius: 3px;
    font-weight: 700;
  }

  .banner-desc {
    font-size: 12px;
    opacity: 0.92;
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

  .banner-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
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
    transition: background 0.15s ease, opacity 0.15s ease;
  }

  .banner-btn:hover:not(:disabled) {
    background: var(--rg-bg-elevated);
  }

  .banner-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .banner-btn--verify {
    border-color: currentColor;
  }

  .banner-btn--rollback {
    border-color: var(--rg-status-critical, #ef4444);
    color: var(--rg-status-critical-text, #ef4444);
  }

  .banner-btn--confirm {
    border-color: var(--rg-status-success, #10b981);
    color: var(--rg-status-success, #10b981);
    font-weight: 700;
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
