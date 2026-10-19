<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
  import { useRouter } from 'vue-router';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useNocEventsStore } from '@/stores/useNocEventsStore';
  import type { SystemRole } from '@/types';

  const router = useRouter();
  const inventoryStore = useInventoryStore();
  const authStore = useAuthStore();
  const nocStore = useNocEventsStore();

  // Reloj táctico en tiempo real
  const currentTime = ref('');
  const currentUtc = ref('');
  let clockTimer: ReturnType<typeof setInterval> | null = null;

  function updateClock() {
    const now = new Date();
    currentTime.value = now.toLocaleTimeString('es-ES', { hour12: false });
    currentUtc.value = now.toISOString().substring(11, 19) + ' UTC';
  }

  onMounted(() => {
    updateClock();
    clockTimer = setInterval(updateClock, 1000);
    if (inventoryStore.routers.length === 0) {
      inventoryStore.fetchRouters();
    }
    inventoryStore.fetchNetworkRoles();
  });

  onBeforeUnmount(() => {
    if (clockTimer) clearInterval(clockTimer);
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
  }

  const userRole = computed<SystemRole>(() => authStore.currentRole || 'AUDITOR');

  const tools: ToolCard[] = [
    {
      id: 'inventory',
      title: 'Inventario de Flota',
      category: 'INFRAESTRUCTURA',
      description:
        'Supervisión de hardware RouterOS v7, mapa geográfico OSM y acceso a consola WebFig.',
      icon: '🖥️',
      route: '/inventory',
    },
    {
      id: 'wallboard',
      title: 'Wallboard NOC en Vivo',
      category: 'MONITOREO',
      description:
        'Telemetría de CPU, memoria y tráfico en tiempo real, alarmas sonoras y modo TV.',
      icon: '📊',
      route: '/noc-wallboard',
      badge:
        computed(() => nocStore.activeAlertsCount).value > 0
          ? `${nocStore.activeAlertsCount} Alertas`
          : undefined,
      badgeType: 'critical',
    },
    {
      id: 'maker-checker',
      title: 'Aprobaciones Maker-Checker',
      category: 'SEGURIDAD & GOBERNANZA',
      description:
        'Flujo de autorización de 4 ojos para comandos de alto impacto y reversión segura.',
      icon: '🛡️',
      route: '/approvals',
      badge:
        computed(() => nocStore.pendingApprovalsCount).value > 0
          ? `${nocStore.pendingApprovalsCount} Pendientes`
          : undefined,
      badgeType: 'warning',
    },
    {
      id: 'backups',
      title: 'Respaldos RSC & Git Diff',
      category: 'CONTINUIDAD',
      description:
        'Snapshots .rsc exportados de la flota, versionado Git de diferencias y respaldo WORM.',
      icon: '📦',
      route: '/backups',
    },
    {
      id: 'bulk-ops',
      title: 'Acciones Masivas & Scripts',
      category: 'OPERACIONES EN LOTE',
      description:
        'Despliegue simultáneo de configuraciones con Safe Mode integrado y dry-run pre-vuelo.',
      icon: '⚡',
      route: '/bulk-ops',
    },
    {
      id: 'sessions',
      title: 'Sesiones & Kill-Switch',
      category: 'DEFENSA ACTIVA',
      description:
        'Control de conexiones concurrentes y revocación inmediata de sesiones comprometidas.',
      icon: '🛑',
      route: '/sessions',
      requiredRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN', 'SECURITY_OFFICER'],
    },
    {
      id: 'users',
      title: 'Usuarios & Matriz RBAC',
      category: 'ACCESO',
      description:
        'Gestión de operadores, asignación de roles y control de acceso router por router.',
      icon: '👥',
      route: '/users',
      requiredRoles: ['SUPERADMIN_GLOBAL', 'TENANT_ADMIN'],
    },
    {
      id: 'audit',
      title: 'Auditoría Forense WORM',
      category: 'CUMPLIMIENTO',
      description:
        'Bitácora inmutable de eventos, autenticación 2FA y revelaciones de credenciales.',
      icon: '📜',
      route: '/audit-logs',
    },
  ];

  const authorizedTools = computed(() => {
    return tools.filter((tool) => {
      if (!tool.requiredRoles) return true;
      return tool.requiredRoles.includes(userRole.value);
    });
  });

  function navigateTo(path: string) {
    router.push(path);
  }

  function launchWebFig(routerId: string) {
    router.push(`/routers/${routerId}/webfig/live`);
  }
</script>

<template>
  <div class="mission-hub" role="region" aria-label="Centro de Mando Táctico">
    <!-- Header Principal del Hub -->
    <header class="hub-header">
      <div class="hub-identity">
        <div class="hub-title-row">
          <span class="hub-badge-pulse" aria-hidden="true"></span>
          <h1 class="hub-title">Centro de Mando — Mission Control</h1>
          <span class="hub-version-tag">Tactical NOC v1.0</span>
        </div>
        <p class="hub-subtitle">
          Supervisión unificada de flota MikroTik RouterOS v7 | Organización:
          <strong class="text-cyan">{{ authStore.tenantSlug || 'Global' }}</strong>
        </p>
      </div>

      <div class="hub-status-bar">
        <div class="clock-card" aria-label="Hora actual de operaciones">
          <div class="clock-time">{{ currentTime }}</div>
          <div class="clock-utc">{{ currentUtc }}</div>
        </div>

        <div class="telemetry-pill" :class="{ 'telemetry-pill--connected': nocStore.isConnected }">
          <span class="status-dot"></span>
          <span>{{ nocStore.isConnected ? 'NOC EN VIVO' : 'WS RECONECTANDO' }}</span>
        </div>
      </div>
    </header>

    <!-- Franja de KPIs Tácticos -->
    <section class="kpi-strip" aria-label="Indicadores Clave de Rendimiento">
      <div class="kpi-card" @click="navigateTo('/inventory')">
        <div class="kpi-icon-wrap kpi-icon--cyan">🖥️</div>
        <div class="kpi-content">
          <span class="kpi-label">Flota MikroTik</span>
          <div class="kpi-value-row">
            <span class="kpi-value">{{ totalRouters }}</span>
            <span class="kpi-subtext">equipos</span>
          </div>
          <div class="kpi-micro-status">
            <span class="micro-online">● {{ onlineRouters }} online</span>
            <span class="micro-sep">|</span>
            <span class="micro-offline">● {{ offlineRouters }} offline</span>
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
          <span class="kpi-label">Disponibilidad Flota</span>
          <div class="kpi-value-row">
            <span class="kpi-value">{{ availabilityPct }}%</span>
            <span
              class="kpi-badge"
              :class="availabilityPct >= 90 ? 'badge--online' : 'badge--warning'"
            >
              {{ availabilityPct >= 90 ? 'OPTIMO' : 'REVISIÓN' }}
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
          <span class="kpi-label">Alertas NOC Activas</span>
          <div class="kpi-value-row">
            <span class="kpi-value">{{ nocStore.activeAlertsCount }}</span>
            <span
              class="kpi-badge"
              :class="nocStore.activeAlertsCount > 0 ? 'badge--critical' : 'badge--online'"
            >
              {{ nocStore.activeAlertsCount > 0 ? 'EN CURSO' : 'DESPEJADO' }}
            </span>
          </div>
          <span class="kpi-subtext">Wallboard en tiempo real</span>
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
          <span class="kpi-label">Maker-Checker</span>
          <div class="kpi-value-row">
            <span class="kpi-value">{{ nocStore.pendingApprovalsCount }}</span>
            <span
              class="kpi-badge"
              :class="nocStore.pendingApprovalsCount > 0 ? 'badge--warning' : 'badge--online'"
            >
              {{ nocStore.pendingApprovalsCount > 0 ? 'PENDIENTES' : 'AL DÍA' }}
            </span>
          </div>
          <span class="kpi-subtext">Aprobaciones de 4 ojos</span>
        </div>
      </div>
    </section>

    <!-- Tiling de Herramientas y Módulos -->
    <section class="tools-section" aria-label="Módulos de Operaciones Disponibles">
      <div class="section-header">
        <h2 class="section-title">
          <span class="section-icon" aria-hidden="true">🎛️</span>
          Módulos y Herramientas del Operador
        </h2>
        <span class="section-count"
          >{{ authorizedTools.length }} disponibles para tu rol:
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
              Ingresar al módulo <span class="arrow" aria-hidden="true">→</span>
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
            Equipos Principales de la Flota
          </h2>
          <button type="button" class="btn-link" @click="navigateTo('/inventory')">
            Ver todo el inventario ({{ totalRouters }}) →
          </button>
        </div>

        <div v-if="inventoryStore.routers.length === 0" class="empty-state">
          <span class="empty-icon">📡</span>
          <p>No hay equipos registrados en el inventario.</p>
          <button type="button" class="btn-primary-sm" @click="navigateTo('/inventory')">
            + Importar Routers CSV
          </button>
        </div>

        <div v-else class="router-fast-list">
          <div v-for="r in inventoryStore.routers.slice(0, 5)" :key="r.id" class="router-fast-item">
            <div class="router-fast-info">
              <div class="router-name-line">
                <span
                  class="status-dot-sm"
                  :class="r.is_reachable ? 'status-dot--online' : 'status-dot--offline'"
                  :title="r.is_reachable ? 'Online' : 'Offline'"
                ></span>
                <span class="router-name">{{ r.display_name }}</span>
                <span v-if="r.network_role" class="badge-role-sm">{{ r.network_role }}</span>
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
            Feed de Actividad NOC en Tiempo Real
          </h2>
          <button type="button" class="btn-link" @click="navigateTo('/audit-logs')">
            Auditoría Forense WORM →
          </button>
        </div>

        <div v-if="nocStore.recentEvents.length === 0" class="empty-state">
          <span class="empty-icon">🛡️</span>
          <p>Sin alertas críticas pendientes. Flota operando normalmente.</p>
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

  .clock-card {
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-panel, #334155);
    border-radius: 6px;
    padding: 6px 14px;
    text-align: right;
    font-family: var(--rg-font-mono, monospace);
  }

  .clock-time {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--rg-accent-cyan, #22d3ee);
    line-height: 1.1;
  }

  .clock-utc {
    font-size: 0.7rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .telemetry-pill {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(100, 116, 139, 0.2);
    border: 1px solid rgba(100, 116, 139, 0.35);
    color: var(--rg-text-muted, #94a3b8);
    font-size: 0.75rem;
    font-weight: 700;
    padding: 8px 12px;
    border-radius: 6px;
    font-family: var(--rg-font-mono, monospace);
  }

  .telemetry-pill--connected {
    background: rgba(16, 185, 129, 0.15);
    border-color: rgba(16, 185, 129, 0.4);
    color: #6ee7b7;
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

  .router-fast-list,
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
</style>
