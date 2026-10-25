<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRouter } from 'vue-router';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useNocEventsStore } from '@/stores/useNocEventsStore';
  import { useI18n } from '@/composables/useI18n';
  import type { SystemRole, TenantFeatureFlags } from '@/types';

  const router = useRouter();
  const inventoryStore = useInventoryStore();
  const authStore = useAuthStore();
  const nocStore = useNocEventsStore();
  const { t } = useI18n();

  onMounted(() => {
    if (inventoryStore.routers.length === 0) {
      inventoryStore.fetchRouters();
    }
    inventoryStore.fetchNetworkRoles();
    nocStore.connectEventsWebSocket();
    nocStore.fetchRecentAuditLogs();
  });

  // Métricas calculadas
  const totalRouters = computed(() => inventoryStore.routers.length);
  const onlineRouters = computed(() => inventoryStore.routers.filter((r) => r.is_reachable).length);
  const offlineRouters = computed(
    () => inventoryStore.routers.filter((r) => !r.is_reachable).length,
  );
  const availabilityPct = computed(() => {
    if (totalRouters.value === 0) return 100;
    return Math.round((onlineRouters.value / totalRouters.value) * 100);
  });

  interface ToolCard {
    id: string;
    title: string;
    category: string;
    description: string;
    icon: string;
    route: string;
    badge?: number | string;
    badgeType?: 'warning' | 'info' | 'success' | 'critical';
    requiredRoles?: SystemRole[];
    requiredFeature?: keyof TenantFeatureFlags;
  }

  const userRole = computed<SystemRole>(() => authStore.currentRole || 'AUDITOR');

  const tools = computed<ToolCard[]>(() => [
    {
      id: 'inventory',
      title: t('dashboard.tools.inventory_title'),
      category: t('dashboard.tools.inventory_cat'),
      description: t('dashboard.tools.inventory_desc'),
      icon: '🖥️',
      route: '/inventory',
    },
    {
      id: 'wallboard',
      title: t('dashboard.tools.wallboard_title'),
      category: t('dashboard.tools.wallboard_cat'),
      description: t('dashboard.tools.wallboard_desc'),
      icon: '📊',
      route: '/noc-wallboard',
      badge:
        nocStore.activeAlertsCount > 0
          ? t('dashboard.tools.wallboard_alerts_badge', { count: nocStore.activeAlertsCount })
          : undefined,
      badgeType: 'critical',
    },
    {
      id: 'cve-matrix',
      title: t('dashboard.tools.cve_matrix_title'),
      category: t('dashboard.tools.cve_matrix_cat'),
      description: t('dashboard.tools.cve_matrix_desc'),
      icon: '🛡️',
      route: '/enterprise/compliance?tab=cves',
      requiredFeature: 'cve_scanner_enabled',
    },
    {
      id: 'subscribers-map',
      title: t('dashboard.tools.subscribers_map_title'),
      category: t('dashboard.tools.subscribers_map_cat'),
      description: t('dashboard.tools.subscribers_map_desc'),
      icon: '📦',
      route: '/subscribers/map',
      requiredFeature: 'isp_module_enabled',
    },
    {
      id: 'field-ops',
      title: t('dashboard.tools.field_ops_title'),
      category: t('dashboard.tools.field_ops_cat'),
      description: t('dashboard.tools.field_ops_desc'),
      icon: '📱',
      route: '/field-ops',
      requiredFeature: 'isp_module_enabled',
    },
    {
      id: 'topology-l2',
      title: t('dashboard.tools.topology_l2_title'),
      category: t('dashboard.tools.topology_l2_cat'),
      description: t('dashboard.tools.topology_l2_desc'),
      icon: '🕸️',
      route: '/topology/l2',
      requiredFeature: 'l2_topology_enabled',
    },
    {
      id: 'syslog',
      title: t('dashboard.tools.syslog_title'),
      category: t('dashboard.tools.syslog_cat'),
      description: t('dashboard.tools.syslog_desc'),
      icon: '📡',
      route: '/routers/syslog',
      requiredFeature: 'syslog_collector_enabled',
    },
    {
      id: 'maker-checker',
      title: t('dashboard.tools.maker_checker_title'),
      category: t('dashboard.tools.maker_checker_cat'),
      description: t('dashboard.tools.maker_checker_desc'),
      icon: '🛡️',
      route: '/approvals',
      badge:
        nocStore.pendingApprovalsCount > 0
          ? t('dashboard.tools.maker_checker_pending_badge', { count: nocStore.pendingApprovalsCount })
          : undefined,
      badgeType: 'warning',
      requiredFeature: 'enforce_maker_checker',
    },
    {
      id: 'backups',
      title: t('dashboard.tools.backups_title'),
      category: t('dashboard.tools.backups_cat'),
      description: t('dashboard.tools.backups_desc'),
      icon: '📦',
      route: '/backups',
      requiredFeature: 'nightly_backups_enabled',
    },
    {
      id: 'bulk-ops',
      title: t('dashboard.tools.bulk_ops_title'),
      category: t('dashboard.tools.bulk_ops_cat'),
      description: t('dashboard.tools.bulk_ops_desc'),
      icon: '⚡',
      route: '/bulk-ops',
    },
    {
      id: 'compliance',
      title: t('dashboard.tools.compliance_title', 'Flota & Seguridad'),
      category: t('dashboard.tools.compliance_cat', 'Gobernanza'),
      description: t('dashboard.tools.compliance_desc', 'Auditoría WORM, Matriz CVE, Drift y CIS Benchmark'),
      icon: '🛡️',
      route: '/enterprise/compliance',
    },
    {
      id: 'sessions',
      title: t('dashboard.tools.sessions_title'),
      category: t('dashboard.tools.sessions_cat'),
      description: t('dashboard.tools.sessions_desc'),
      icon: '🛑',
      route: '/users?tab=sessions',
      requiredRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SECURITY_OFFICER'],
    },
    {
      id: 'users',
      title: t('dashboard.tools.users_title'),
      category: t('dashboard.tools.users_cat'),
      description: t('dashboard.tools.users_desc'),
      icon: '👥',
      route: '/users',
      requiredRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN'],
    },
    {
      id: 'audit',
      title: t('dashboard.tools.audit_title'),
      category: t('dashboard.tools.audit_cat'),
      description: t('dashboard.tools.audit_desc'),
      icon: '📜',
      route: '/enterprise/compliance?tab=audit',
    },
  ]);

  const authorizedTools = computed(() => {
    return tools.value.filter((tool) => {
      // 1. Filtrar por rol RBAC
      if (tool.requiredRoles && !tool.requiredRoles.includes(userRole.value)) {
        return false;
      }
      // 2. Filtrar por Feature Flags del Tenant (dinámico según empresa/ISP)
      if (tool.requiredFeature) {
        const flagVal = authStore.tenantFeatures?.[tool.requiredFeature];
        if (!flagVal) return false;
      }
      return true;
    });
  });

  function navigateTo(path: string) {
    if (path === '/routers/syslog') {
      const target =
        inventoryStore.routers.find((r) => r.is_reachable) || inventoryStore.routers[0];
      if (target) {
        router.push(`/routers/${target.id}/webfig/syslog`);
      } else {
        router.push('/inventory');
      }
      return;
    }
    router.push(path);
  }

  function launchWebFig(routerId: string) {
    router.push(`/routers/${routerId}/webfig/live`);
  }

  const isRefreshing = ref(false);
  const isFleetUpdated = ref(false);

  async function refreshFleetData() {
    isRefreshing.value = true;
    try {
      await Promise.allSettled([
        inventoryStore.fetchRouters(),
        nocStore.fetchRecentAuditLogs(true),
      ]);
      isFleetUpdated.value = true;
      setTimeout(() => {
        isFleetUpdated.value = false;
      }, 3500);
    } finally {
      isRefreshing.value = false;
    }
  }
</script>

<template>
  <div class="mission-hub" role="region" aria-label="Centro de Mando Táctico">
    <!-- Header Principal del Hub -->
    <header class="hub-header">
      <div class="hub-identity">
        <div class="hub-title-row">
          <span class="hub-badge-pulse" aria-hidden="true"></span>
          <h1 class="hub-title">{{ t('dashboard.title') }}</h1>
        </div>
        <p class="hub-subtitle">
          {{ t('dashboard.subtitle') }}
        </p>
      </div>

      <div class="hub-status-bar">
        <button
          type="button"
          class="btn btn-primary"
          :class="{ 'btn-primary--loading': isRefreshing }"
          :disabled="isRefreshing"
          aria-label="Actualizar datos de la flota"
          @click="refreshFleetData"
        >
          <span v-if="isRefreshing" class="btn-spinner" aria-hidden="true">⏳</span>
          <span v-else class="btn-icon" aria-hidden="true">🔄</span>
          <span>{{ isRefreshing ? t('dashboard.refreshing') : t('dashboard.refresh_data') }}</span>
        </button>

        <div v-if="isFleetUpdated" class="status-indicator success" role="status" aria-live="polite">
          <span class="status-dot"></span>
          <span class="status-icon" aria-hidden="true">✓</span>
          <span class="status-text">{{ t('dashboard.updated') }}</span>
        </div>
      </div>
    </header>

    <!-- Franja de KPIs Tácticos -->
    <section class="kpi-strip" aria-label="Indicadores Clave de Rendimiento">
      <div class="kpi-card" @click="navigateTo('/inventory')">
        <div class="kpi-icon-wrap kpi-icon--cyan">🖥️</div>
        <div class="kpi-content">
          <span class="kpi-label">{{ t('dashboard.kpi_fleet') }}</span>
          <div class="kpi-value-row">
            <span class="kpi-value">{{ totalRouters }}</span>
            <span class="kpi-subtext">{{ t('dashboard.devices') }}</span>
          </div>
          <div class="kpi-micro-status">
            <span class="micro-online">● {{ onlineRouters }} {{ t('common.online').toLowerCase() }}</span>
            <span class="micro-sep">|</span>
            <span class="micro-offline">● {{ offlineRouters }} {{ t('common.offline').toLowerCase() }}</span>
          </div>
        </div>
      </div>

      <div class="kpi-card" @click="navigateTo('/inventory')">
        <div
          class="kpi-icon-wrap"
          :class="availabilityPct >= 90 ? 'kpi-icon--green' : 'kpi-icon--amber'"
        >
          ⚡
        </div>
        <div class="kpi-content">
          <span class="kpi-label">{{ t('dashboard.kpi_availability') }}</span>
          <div class="kpi-value-row">
            <span class="kpi-value">{{ availabilityPct }}%</span>
            <span
              class="kpi-badge"
              :class="availabilityPct >= 90 ? 'badge--online' : 'badge--warning'"
            >
              {{ availabilityPct >= 90 ? t('dashboard.optimal') : t('dashboard.review') }}
            </span>
          </div>
          <div class="kpi-progress-bar">
            <div class="kpi-progress-fill" :style="{ width: `${availabilityPct}%` }"></div>
          </div>
        </div>
      </div>

      <div class="kpi-card" @click="navigateTo('/noc-wallboard')">
        <div
          class="kpi-icon-wrap"
          :class="nocStore.activeAlertsCount > 0 ? 'kpi-icon--red' : 'kpi-icon--green'"
        >
          🚨
        </div>
        <div class="kpi-content">
          <span class="kpi-label">{{ t('dashboard.kpi_alerts') }}</span>
          <div class="kpi-value-row">
            <span class="kpi-value">{{ nocStore.activeAlertsCount }}</span>
            <span
              class="kpi-badge"
              :class="nocStore.activeAlertsCount > 0 ? 'badge--critical' : 'badge--online'"
            >
              {{ nocStore.activeAlertsCount > 0 ? t('dashboard.in_progress') : t('dashboard.clear') }}
            </span>
          </div>
          <span class="kpi-subtext">{{ t('dashboard.wallboard_realtime') }}</span>
        </div>
      </div>

      <div class="kpi-card" @click="navigateTo('/approvals')">
        <div
          class="kpi-icon-wrap"
          :class="nocStore.pendingApprovalsCount > 0 ? 'kpi-icon--amber' : 'kpi-icon--cyan'"
        >
          🛡️
        </div>
        <div class="kpi-content">
          <span class="kpi-label">{{ t('dashboard.maker_checker') }}</span>
          <div class="kpi-value-row">
            <span class="kpi-value">{{ nocStore.pendingApprovalsCount }}</span>
            <span
              class="kpi-badge"
              :class="nocStore.pendingApprovalsCount > 0 ? 'badge--warning' : 'badge--online'"
            >
              {{ nocStore.pendingApprovalsCount > 0 ? t('dashboard.pending') : t('dashboard.up_to_date') }}
            </span>
          </div>
          <span class="kpi-subtext">{{ t('dashboard.approvals_4eyes') }}</span>
        </div>
      </div>
    </section>

    <!-- Tiling de Herramientas y Módulos -->
    <section class="tools-section" aria-label="Módulos de Operaciones Disponibles">
      <div class="section-header">
        <h2 class="section-title">
          <span class="section-icon" aria-hidden="true">🎛️</span>
          {{ t('dashboard.tools_title') }}
        </h2>
        <span class="section-count"
          >{{ t('dashboard.tools_available_for_role', { count: authorizedTools.length }) }}
          <strong>{{ userRole }}</strong></span
        >
      </div>

      <div class="tiling-grid">
        <article
          v-for="tool in authorizedTools"
          :key="tool.id"
          class="tile-card"
          tabindex="0"
          role="button"
          :aria-label="`Abrir módulo ${tool.title}`"
          @click="navigateTo(tool.route)"
          @keydown.enter="navigateTo(tool.route)"
          @keydown.space.prevent="navigateTo(tool.route)"
        >
          <div class="tile-header">
            <div class="tile-icon-box">{{ tool.icon }}</div>
            <div class="tile-meta">
              <span class="tile-category">{{ tool.category }}</span>
              <h3 class="tile-title">{{ tool.title }}</h3>
            </div>
            <span
              v-if="tool.badge"
              class="tile-badge"
              :class="`tile-badge--${tool.badgeType || 'info'}`"
            >
              {{ tool.badge }}
            </span>
          </div>

          <p class="tile-description">{{ tool.description }}</p>

          <div class="tile-footer">
            <span class="tile-action-link">
              {{ t('dashboard.enter_module') }} <span class="arrow" aria-hidden="true">→</span>
            </span>
          </div>
        </article>
      </div>
    </section>

    <!-- Fila Inferior: Acceso Rápido a Routers & Eventos Recientes -->
    <div class="bottom-split-row">
      <!-- Acceso Rápido a Equipos de la Flota -->
      <section class="quick-routers-card" aria-label="Acceso Rápido a Routers">
        <div class="card-header-bar">
          <h2 class="card-title">
            <span aria-hidden="true">⚡</span>
            {{ t('dashboard.main_fleet_routers') }}
          </h2>
          <button type="button" class="btn-link" @click="navigateTo('/inventory')">
            {{ t('dashboard.view_all_inventory', { count: totalRouters }) }}
          </button>
        </div>

        <div v-if="inventoryStore.routers.length === 0" class="empty-state">
          <span class="empty-icon">📡</span>
          <p>{{ t('dashboard.no_routers_registered') }}</p>
          <button type="button" class="btn-primary-sm" @click="navigateTo('/inventory')">
            {{ t('dashboard.import_csv_btn') }}
          </button>
        </div>

        <div v-else class="router-fast-list">
          <div v-for="r in inventoryStore.routers" :key="r.id" class="router-fast-item">
            <div class="router-fast-info">
              <div class="router-name-line">
                <span
                  class="status-dot-sm"
                  :class="r.is_reachable ? 'status-dot--online' : 'status-dot--offline'"
                  :title="r.is_reachable ? 'Online' : 'Offline'"
                ></span>
                <span class="router-name">{{ r.display_name }}</span>
                <span v-if="r.network_role" class="badge-role-sm">{{ t(`enums.network_role.${r.network_role}`, r.network_role) }}</span>
              </div>
              <div class="router-sub-line">
                <span class="router-ip">{{ r.ip_address }}</span>
                <span v-if="r.ros_identity" class="router-id-text">({{ r.ros_identity }})</span>
              </div>
            </div>

            <button
              type="button"
              class="btn-open-webfig"
              title="Abrir consola WebFig táctica"
              @click="launchWebFig(r.id)"
            >
              📊 WebFig
            </button>
          </div>
        </div>
      </section>

      <!-- Feed de Alertas & Auditoría en Vivo -->
      <section class="quick-alerts-card" aria-label="Feed de Telemetría y Alertas">
        <div class="card-header-bar">
          <h2 class="card-title">
            <span aria-hidden="true">📡</span>
            {{ t('dashboard.realtime_feed_title') }}
          </h2>
          <button type="button" class="btn-link" @click="navigateTo('/audit-logs')">
            {{ t('dashboard.forensic_audit_link') }}
          </button>
        </div>

        <div v-if="nocStore.recentEvents.length === 0" class="empty-state">
          <span class="empty-icon">🛡️</span>
          <p>{{ t('dashboard.no_critical_alerts') }}</p>
        </div>

        <div v-else class="events-fast-list">
          <div v-for="ev in nocStore.recentEvents.slice(0, 5)" :key="ev.id" class="event-fast-item">
            <span class="event-badge-sev" :class="`sev--${ev.severity.toLowerCase()}`">
              {{ ev.severity }}
            </span>
            <div class="event-details">
              <div class="event-msg">{{ ev.message }}</div>
              <div class="event-time">{{ new Date(ev.timestampIso).toLocaleTimeString() }}</div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
  .mission-hub {
    padding: 24px;
    background-color: var(--rg-bg-canvas, #0b0f19);
    min-height: 100%;
    display: flex;
    flex-direction: column;
    gap: 24px;
    color: var(--rg-text-primary, #f8fafc);
  }

  /* Header */
  .hub-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
    border-bottom: 1px solid var(--rg-border-panel, #334155);
    padding-bottom: 18px;
  }

  .hub-title-row {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .hub-badge-pulse {
    width: 12px;
    height: 12px;
    background-color: var(--rg-accent-cyan, #22d3ee);
    border-radius: 50%;
    box-shadow: 0 0 10px var(--rg-accent-cyan, #22d3ee);
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.4;
      transform: scale(0.85);
    }
  }

  .hub-title {
    font-size: 1.6rem;
    font-weight: 800;
    margin: 0;
    color: var(--rg-text-primary, #f8fafc);
    letter-spacing: -0.5px;
  }

  .hub-version-tag {
    background: rgba(34, 211, 238, 0.15);
    border: 1px solid rgba(34, 211, 238, 0.4);
    color: var(--rg-accent-cyan, #22d3ee);
    font-size: 0.72rem;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: var(--rg-font-mono, monospace);
    font-weight: 600;
  }

  .hub-subtitle {
    margin: 6px 0 0 0;
    font-size: 0.9rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .text-cyan {
    color: var(--rg-accent-cyan, #22d3ee);
  }

  .hub-status-bar {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
  }

  /* KPIs Strip */
  .kpi-strip {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
  }

  .kpi-card {
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-panel, #334155);
    border-radius: 8px;
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 14px;
    cursor: pointer;
    transition:
      transform 0.15s,
      border-color 0.15s,
      box-shadow 0.15s;
  }

  .kpi-card:hover {
    transform: translateY(-2px);
    border-color: var(--rg-accent-cyan, #22d3ee);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  }

  .kpi-icon-wrap {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.4rem;
    flex-shrink: 0;
  }

  .kpi-icon--cyan {
    background: rgba(34, 211, 238, 0.15);
    color: #22d3ee;
  }
  .kpi-icon--green {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
  }
  .kpi-icon--amber {
    background: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
  }
  .kpi-icon--red {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
  }

  .kpi-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }

  .kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--rg-text-muted, #94a3b8);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .kpi-value-row {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .kpi-value {
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--rg-text-primary, #f8fafc);
    font-family: var(--rg-font-mono, monospace);
  }

  .kpi-subtext {
    font-size: 0.75rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .kpi-badge {
    font-size: 0.65rem;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 700;
    font-family: var(--rg-font-mono, monospace);
  }

  .badge--online {
    background: rgba(16, 185, 129, 0.2);
    color: #6ee7b7;
  }
  .badge--warning {
    background: rgba(245, 158, 11, 0.2);
    color: #fde68a;
  }
  .badge--critical {
    background: rgba(239, 68, 68, 0.2);
    color: #fca5a5;
  }

  .kpi-micro-status {
    font-size: 0.72rem;
    display: flex;
    gap: 6px;
    align-items: center;
    font-family: var(--rg-font-mono, monospace);
  }

  .micro-online {
    color: #6ee7b7;
  }
  .micro-offline {
    color: #f87171;
  }
  .micro-sep {
    color: var(--rg-border-panel, #334155);
  }

  .kpi-progress-bar {
    width: 100%;
    height: 4px;
    background: rgba(148, 163, 184, 0.2);
    border-radius: 2px;
    overflow: hidden;
    margin-top: 4px;
  }

  .kpi-progress-fill {
    height: 100%;
    background: #10b981;
    border-radius: 2px;
    transition: width 0.3s;
  }

  /* Tools Tiling Section */
  .tools-section {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    flex-wrap: wrap;
    gap: 8px;
  }

  .section-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--rg-text-primary, #f8fafc);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .section-icon {
    font-size: 1.1rem;
  }

  .section-count {
    font-size: 0.8rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .tiling-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
    gap: 16px;
  }

  .tile-card {
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-panel, #334155);
    border-radius: 8px;
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
  }

  .tile-card:hover,
  .tile-card:focus-visible {
    outline: none;
    border-color: var(--rg-accent-cyan, #22d3ee);
    background: var(--rg-bg-elevated, #1e293b);
    transform: translateY(-3px);
    box-shadow:
      0 8px 24px rgba(0, 0, 0, 0.4),
      var(--rg-cyan-glow, 0 0 12px rgba(6, 182, 212, 0.28));
  }

  .tile-header {
    display: flex;
    align-items: flex-start;
    gap: 12px;
  }

  .tile-icon-box {
    font-size: 1.6rem;
    width: 42px;
    height: 42px;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid var(--rg-border-panel, #334155);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .tile-meta {
    flex: 1;
    min-width: 0;
  }

  .tile-category {
    font-size: 0.68rem;
    font-weight: 700;
    color: var(--rg-accent-cyan, #22d3ee);
    text-transform: uppercase;
    letter-spacing: 0.6px;
    font-family: var(--rg-font-mono, monospace);
  }

  .tile-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--rg-text-primary, #f8fafc);
    margin: 2px 0 0 0;
    line-height: 1.25;
  }

  .tile-badge {
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: var(--rg-font-mono, monospace);
    white-space: nowrap;
  }

  .tile-badge--critical {
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid #ef4444;
    color: #fca5a5;
  }

  .tile-badge--warning {
    background: rgba(245, 158, 11, 0.2);
    border: 1px solid #f59e0b;
    color: #fde68a;
  }

  .tile-badge--info {
    background: rgba(56, 189, 248, 0.2);
    border: 1px solid #38bdf8;
    color: #bae6fd;
  }

  .tile-description {
    font-size: 0.82rem;
    color: var(--rg-text-secondary, #cbd5e1);
    margin: 0;
    line-height: 1.45;
    flex: 1;
  }

  .tile-footer {
    display: flex;
    justify-content: flex-end;
    margin-top: 4px;
    padding-top: 8px;
    border-top: 1px dashed rgba(148, 163, 184, 0.15);
  }

  .tile-action-link {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--rg-accent-cyan, #22d3ee);
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: var(--rg-font-mono, monospace);
    transition: gap 0.15s;
  }

  .tile-card:hover .arrow {
    transform: translateX(4px);
  }

  .arrow {
    transition: transform 0.15s;
  }

  /* Bottom Split Row */
  .bottom-split-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  @media (max-width: 992px) {
    .bottom-split-row {
      grid-template-columns: 1fr;
    }
  }

  .quick-routers-card,
  .quick-alerts-card {
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-panel, #334155);
    border-radius: 8px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .card-header-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(148, 163, 184, 0.15);
    padding-bottom: 10px;
  }

  .card-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--rg-text-primary, #f8fafc);
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .btn-link {
    background: transparent;
    border: none;
    color: var(--rg-accent-cyan, #22d3ee);
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    font-family: var(--rg-font-mono, monospace);
  }

  .btn-link:hover {
    text-decoration: underline;
  }

  .empty-state {
    padding: 24px;
    text-align: center;
    color: var(--rg-text-muted, #94a3b8);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
  }

  .empty-icon {
    font-size: 1.8rem;
    opacity: 0.6;
  }

  .btn-primary-sm {
    background: var(--rg-accent-cyan, #22d3ee);
    color: #0b0f19;
    border: none;
    padding: 6px 14px;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 700;
    cursor: pointer;
    font-family: var(--rg-font-mono, monospace);
  }

  .router-fast-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 290px;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 6px;
    scrollbar-width: thin;
    scrollbar-color: rgba(0, 240, 255, 0.3) rgba(15, 23, 42, 0.5);
  }

  .router-fast-list::-webkit-scrollbar {
    width: 6px;
  }

  .router-fast-list::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.5);
    border-radius: 3px;
  }

  .router-fast-list::-webkit-scrollbar-thumb {
    background: rgba(0, 240, 255, 0.25);
    border-radius: 3px;
  }

  .router-fast-list::-webkit-scrollbar-thumb:hover {
    background: rgba(0, 240, 255, 0.5);
  }

  .events-fast-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .router-fast-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid rgba(148, 163, 184, 0.1);
    border-radius: 6px;
    padding: 8px 12px;
    transition: background-color 0.15s;
  }

  .router-fast-item:hover {
    background: rgba(30, 41, 59, 0.6);
  }

  .router-fast-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  .router-name-line {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .status-dot-sm {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .status-dot--online {
    background: #10b981;
  }
  .status-dot--offline {
    background: #ef4444;
  }

  .router-name {
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--rg-text-primary, #f8fafc);
  }

  .badge-role-sm {
    font-size: 0.62rem;
    background: rgba(100, 116, 139, 0.25);
    color: #94a3b8;
    padding: 1px 5px;
    border-radius: 3px;
    font-family: var(--rg-font-mono, monospace);
  }

  .router-sub-line {
    display: flex;
    gap: 6px;
    font-size: 0.72rem;
    color: var(--rg-text-muted, #94a3b8);
    font-family: var(--rg-font-mono, monospace);
  }

  .btn-open-webfig {
    background: rgba(34, 211, 238, 0.15);
    border: 1px solid rgba(34, 211, 238, 0.35);
    color: var(--rg-accent-cyan, #22d3ee);
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: var(--rg-font-mono, monospace);
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-open-webfig:hover {
    background: var(--rg-accent-cyan, #22d3ee);
    color: #0b0f19;
  }

  .event-fast-item {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid rgba(148, 163, 184, 0.1);
    border-radius: 6px;
    padding: 8px 12px;
  }

  .event-badge-sev {
    font-size: 0.65rem;
    font-weight: 800;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: var(--rg-font-mono, monospace);
    flex-shrink: 0;
  }

  .sev--critical {
    background: rgba(239, 68, 68, 0.2);
    color: #fca5a5;
    border: 1px solid #ef4444;
  }
  .sev--warning {
    background: rgba(245, 158, 11, 0.2);
    color: #fde68a;
    border: 1px solid #f59e0b;
  }
  .sev--info {
    background: rgba(56, 189, 248, 0.2);
    color: #bae6fd;
    border: 1px solid #38bdf8;
  }

  .event-details {
    flex: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }

  .event-msg {
    font-size: 0.8rem;
    color: var(--rg-text-secondary, #cbd5e1);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .event-time {
    font-size: 0.7rem;
    color: var(--rg-text-muted, #94a3b8);
    font-family: var(--rg-font-mono, monospace);
    white-space: nowrap;
  }

  .btn.btn-primary,
  .btn-primary {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(34, 211, 238, 0.12);
    border: 1px solid var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn.btn-primary:hover:not(:disabled),
  .btn-primary:hover:not(:disabled) {
    background: rgba(34, 211, 238, 0.25);
    border-color: #38bdf8;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(34, 211, 238, 0.35);
  }

  .btn.btn-primary:active,
  .btn-primary:active {
    transform: scale(0.98);
  }

  .btn.btn-primary:disabled,
  .btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .status-indicator.success {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    background: rgba(16, 185, 129, 0.18);
    border: 1px solid #10b981;
    border-radius: 6px;
    color: #34d399;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    animation: fadeInScale 0.25s ease-out;
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.25);
  }

  .status-indicator.success .status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: #10b981;
    box-shadow: 0 0 6px #10b981;
    animation: pulseGlow 1.5s infinite;
  }

  .status-indicator.success .status-icon {
    font-size: 0.85rem;
    font-weight: 800;
  }

  @keyframes fadeInScale {
    from {
      opacity: 0;
      transform: translateY(-2px) scale(0.96);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  @keyframes pulseGlow {
    0%, 100% {
      opacity: 1;
      transform: scale(1);
    }
    50% {
      opacity: 0.5;
      transform: scale(1.2);
    }
  }
</style>
