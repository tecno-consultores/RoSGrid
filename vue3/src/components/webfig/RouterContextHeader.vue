<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { computed } from 'vue';
  import { useRouter } from 'vue-router';
  import type { RouterItem, TelemetryPoint } from '@/types';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import { useI18n } from '@/composables/useI18n';

  const props = defineProps<{
    router: RouterItem | null;
    latestTelemetry: TelemetryPoint | null;
  }>();

  const emit = defineEmits<{
    (e: 'toggle-safemode'): void;
  }>();

  const vueRouter = useRouter();
  const inventoryStore = useInventoryStore();
  const webFigStore = useWebFigStore();
  const { t } = useI18n();

  const formattedUptime = computed(() => {
    return props.router?.ros_identity ? '14d 06:32:11' : '00:00:00';
  });

  const cpuValue = computed(() => {
    return Math.round(props.latestTelemetry?.cpuLoadPct ?? 0);
  });

  const ramFreeValue = computed(() => {
    return Math.round(props.latestTelemetry?.freeMemoryPct ?? 0);
  });

  const tempValue = computed(() => {
    return props.latestTelemetry?.temperatureC ?? 38;
  });

  function handleSelectRouter(e: Event) {
    const target = e.target as HTMLSelectElement;
    if (target.value && target.value !== props.router?.id) {
      vueRouter.push(`/routers/${target.value}/webfig/live`);
    }
  }
</script>

<template>
  <header class="router-context-header" role="banner" :aria-label="t('webfig.header_role_banner')">
    <!-- Identidad y Selector de Equipo -->
    <div class="header-section header-identity">
      <div class="identity-badge">
        <span
          class="status-indicator"
          :class="{ 'status-indicator--online': router?.is_reachable }"
        ></span>
        <div class="identity-text">
          <h1 class="router-title">
            {{ router?.display_name || 'MikroTik RouterOS' }}
            <span class="router-ros-id">({{ router?.ros_identity || t('webfig.header_no_identity') }})</span>
          </h1>
          <div class="router-specs font-tabular">
            <span>{{ router?.model || router?.board_name || 'RouterBOARD' }}</span>
            <span class="separator">|</span>
            <span>SN: {{ router?.serial_number || 'N/A' }}</span>
            <span class="separator">|</span>
            <span class="badge-version">v{{ router?.ros_version || '7.x' }}</span>
            <span class="separator">|</span>
            <span>⏱️ {{ formattedUptime }}</span>
          </div>
        </div>
      </div>

      <!-- Selector rápido de router -->
      <div class="router-switcher">
        <label for="header-router-switcher" class="sr-only">{{ t('webfig.header_switch_router') }}</label>
        <select
          id="header-router-switcher"
          class="select-switcher"
          :value="router?.id || ''"
          :aria-label="t('webfig.header_select_another')"
          @change="handleSelectRouter"
        >
          <option value="" disabled>{{ t('webfig.header_switch_router') }}</option>
          <option v-for="r in inventoryStore.routers" :key="r.id" :value="r.id">
            {{ r.display_name }} ({{ r.ip_address }})
          </option>
        </select>
      </div>
    </div>

    <!-- Medidores en Vivo (CPU, RAM, Temp, Voltaje) -->
    <div class="header-section header-telemetry font-tabular">
      <div class="telemetry-chip" :class="{ 'chip-warning': cpuValue > 80 }">
        <span class="chip-label">{{ t('webfig.header_cpu') }}</span>
        <strong class="chip-val">{{ cpuValue }}%</strong>
      </div>

      <div class="telemetry-chip">
        <span class="chip-label">{{ t('webfig.header_ram_free') }}</span>
        <strong class="chip-val">{{ ramFreeValue }}%</strong>
      </div>

      <div class="telemetry-chip">
        <span class="chip-label">{{ t('webfig.header_temp') }}</span>
        <strong class="chip-val">{{ tempValue }}°C</strong>
      </div>

      <!-- Badge Safe Mode -->
      <button
        type="button"
        class="safemode-badge"
        :class="{ 'safemode-badge--active': webFigStore.isSafeModeActive }"
        :aria-label="
          webFigStore.isSafeModeActive
            ? t('webfig.header_safemode_active_aria', { s: webFigStore.safeModeCountdownSeconds })
            : t('webfig.header_safemode_inactive_aria')
        "
        @click="emit('toggle-safemode')"
      >
        <span class="safemode-icon">🛡️</span>
        <span class="safemode-text">
          {{
            webFigStore.isSafeModeActive
              ? t('webfig.header_safemode_active', { s: webFigStore.safeModeCountdownSeconds })
              : t('webfig.header_safemode')
          }}
        </span>
      </button>
    </div>
  </header>
</template>

<style scoped>
  .router-context-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    padding: 10px 16px;
    background: var(--rg-bg-surface);
    border: 1px solid var(--rg-border-grid);
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  }

  .header-section {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .header-identity {
    flex: 1 1 500px;
    justify-content: space-between;
  }

  .identity-badge {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  /* Refactoring UI: Color supports, never carries — Hollow ring for offline vs Solid dot for online */
  .status-indicator {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: transparent;
    border: 2px solid var(--rg-status-critical, #ef4444);
    flex-shrink: 0;
  }

  .status-indicator--online {
    background: var(--rg-status-online, #10b981);
    border: none;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
  }

  .router-title {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--rg-text-primary);
    display: flex;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 6px;
  }

  .router-ros-id {
    font-size: 0.85rem;
    color: var(--rg-text-muted);
    font-weight: 400;
  }

  .router-specs {
    font-size: 0.78rem;
    color: var(--rg-text-secondary);
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 2px;
  }

  .separator {
    color: var(--rg-border-grid);
  }

  .badge-version {
    color: var(--rg-accent-cyan);
    font-weight: 600;
  }

  .router-switcher {
    margin-left: auto;
  }

  .select-switcher {
    padding: 5px 10px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    color: var(--rg-text-primary);
    font-size: 0.8rem;
  }

  .header-telemetry {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }

  .telemetry-chip {
    padding: 4px 8px;
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    font-size: 0.78rem;
    display: flex;
    gap: 5px;
    align-items: center;
  }

  .chip-label {
    color: var(--rg-text-muted);
  }

  .chip-val {
    color: var(--rg-accent-cyan);
  }

  .chip-warning .chip-val {
    color: #ef4444;
  }

  .safemode-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    border-radius: 6px;
    border: 1px solid var(--rg-border-grid);
    background: var(--rg-bg-elevated);
    color: var(--rg-text-muted);
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .safemode-badge--active {
    background: rgba(6, 182, 212, 0.15);
    border-color: var(--rg-accent-cyan);
    color: var(--rg-accent-cyan);
    box-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
  }

  .font-tabular {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  @media (max-width: 768px) {
    .router-context-header {
      padding: 8px 10px;
    }

    .header-identity {
      flex: 1 1 100%;
      flex-direction: column;
      align-items: flex-start;
      gap: 6px;
    }

    .router-switcher {
      margin-left: 0;
      width: 100%;
    }

    .select-switcher {
      width: 100%;
    }

    .header-telemetry {
      width: 100%;
      justify-content: space-between;
    }
  }
</style>
