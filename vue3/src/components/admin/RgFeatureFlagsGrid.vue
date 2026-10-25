<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed } from 'vue';
  import type { TenantFeatureFlags } from '@/types';

  const props = defineProps<{
    modelValue: TenantFeatureFlags;
    isSaving?: boolean;
    tenantName?: string;
  }>();

  const emit = defineEmits<{
    (e: 'update:modelValue', value: TenantFeatureFlags): void;
    (e: 'save'): void;
  }>();

  // Modal de Radio de Impacto (Blast Radius Shield)
  const isImpactModalOpen = ref(false);
  const pendingCriticalFlag = ref<keyof TenantFeatureFlags | null>(null);
  const pendingCriticalLabel = ref('');
  const pendingCriticalDesc = ref('');

  interface FeatureDefinition {
    key: keyof TenantFeatureFlags;
    label: string;
    description: string;
    icon: string;
    severity: 'LOW' | 'OPS' | 'CRITICAL';
    requires?: keyof TenantFeatureFlags;
    routePath?: string;
  }

  interface FeatureQuadrant {
    id: string;
    title: string;
    icon: string;
    features: FeatureDefinition[];
  }

  const quadrants: FeatureQuadrant[] = [
    {
      id: 'isp',
      title: 'Núcleo de Red & Servicios ISP',
      icon: '🌐',
      features: [
        {
          key: 'isp_module_enabled',
          label: 'Módulo ISP & Abonados FTTH',
          description: 'Gestión de ONUs, cajas de empalme, perfil de ancho de banda y mapa de clientes.',
          icon: '📡',
          severity: 'OPS',
          routePath: '/subscribers/map',
        },
        {
          key: 'bgp_looking_glass_enabled',
          label: 'BGP Looking Glass v7',
          description: 'Consulta no interactiva de tablas de enrutamiento y prefijos anunciados a peers.',
          icon: '🔍',
          severity: 'OPS',
          requires: 'isp_module_enabled',
        },
        {
          key: 'capsman_wifi_enabled',
          label: 'Wi-Fi CAPsMAN & WiFi 6',
          description: 'Orquestación centralizada de perfiles SSID, radios WiFiWave2 y roaming 802.11r.',
          icon: '📶',
          severity: 'OPS',
          routePath: '/enterprise/compliance?tab=wifi',
        },
        {
          key: 'sdwan_orchestrator_enabled',
          label: 'Orquestador SD-WAN WireGuard',
          description: 'Aprovisionamiento dinámico Hub & Spoke con failover Multi-WAN recursivo.',
          icon: '🛡️',
          severity: 'OPS',
          routePath: '/enterprise/compliance?tab=sdwan',
        },
      ],
    },
    {
      id: 'security',
      title: 'Ciberseguridad & Gobernanza',
      icon: '🛡️',
      features: [
        {
          key: 'cis_audit_enabled',
          label: 'Auditoría CIS Hardening',
          description: 'Evaluación automatizada de las 10 directivas críticas CIS para MikroTik RouterOS v7.',
          icon: '📜',
          severity: 'OPS',
          routePath: '/enterprise/compliance?tab=cis',
        },
        {
          key: 'config_drift_monitoring_enabled',
          label: 'Monitoreo de Config Drift',
          description: 'Comparación semántica contra Golden Baseline y reversión atómica en 1 clic.',
          icon: '⚖️',
          severity: 'OPS',
          routePath: '/enterprise/compliance?tab=drift',
        },
        {
          key: 'rogue_dhcp_enabled',
          label: 'Rogue DHCP & DHCP Snooping',
          description: 'Inspección de DHCP Snooping en bridges L2 y aislamiento de puertos intrusos.',
          icon: '🚨',
          severity: 'OPS',
          routePath: '/enterprise/compliance?tab=rogue',
        },
        {
          key: 'enforce_maker_checker',
          label: 'Maker-Checker Estricto (4 Ojos)',
          description: 'Exige que toda operación crítica sobre routers sea aprobada por un segundo operador.',
          icon: '👥',
          severity: 'CRITICAL',
          routePath: '/approvals',
        },
        {
          key: 'auto_safemode_enforced',
          label: 'Safe Mode Forzado (60s)',
          description: 'Rollback automático ante desconexión en llamadas REST mutativas a RouterOS.',
          icon: '🔒',
          severity: 'CRITICAL',
        },
      ],
    },
    {
      id: 'telemetry',
      title: 'Telemetría & Observabilidad',
      icon: '📡',
      features: [
        {
          key: 'syslog_collector_enabled',
          label: 'Colector Syslog UDP en Vivo',
          description: 'Recepción y correlación en tiempo real de datagramas UDP 514/5514 con RingBuffer en KeyDB.',
          icon: '📟',
          severity: 'CRITICAL',
          routePath: '/inventory',
        },
        {
          key: 'sfp_ddm_telemetry_enabled',
          label: 'Telemetría Óptica SFP DDM',
          description: 'Muestreo en tiempo real de potencia Rx/Tx, temperatura y voltaje de módulos ópticos.',
          icon: '💡',
          severity: 'LOW',
        },
        {
          key: 'prometheus_fleet_exporter_enabled',
          label: 'Exportador Prometheus de Flota',
          description: 'Exposición de métricas agregadas en /api/v1/metrics/fleet para Grafana corporativo.',
          icon: '📊',
          severity: 'LOW',
        },
        {
          key: 'ipfix_analytics_enabled',
          label: 'Analítica de Flujo IPFIX / NetFlow',
          description: 'Detección de patrones de saturación de enlaces y top talkers mediante flujos de red.',
          icon: '📈',
          severity: 'OPS',
        },
        {
          key: 'cve_scanner_enabled',
          label: 'Matriz de Vulnerabilidades CVE',
          description: 'Cruce local semver de versiones de RouterOS contra base de vulnerabilidades.',
          icon: '🛡️',
          routePath: '/enterprise/compliance?tab=cves',
          severity: 'LOW',
        },
      ],
    },
    {
      id: 'automation',
      title: 'Automatización & Plataforma',
      icon: '⚙️',
      features: [
        {
          key: 'l2_topology_enabled',
          label: 'Topología L2 (MNDP / LLDP)',
          description: 'Descubrimiento continuo de adyacencias y renderizado dinámico en Canvas 2D.',
          icon: '🗺️',
          severity: 'OPS',
          routePath: '/topology/l2',
        },
        {
          key: 'nightly_backups_enabled',
          label: 'Respaldos Automáticos WORM',
          description: 'Snapshots .rsc cifrados con AES-256-GCM y versionado Git de diferencias de config.',
          icon: '📦',
          severity: 'OPS',
          routePath: '/backups',
        },
        {
          key: 'sla_tracker_enabled',
          label: 'Sondas SLA para Enlaces Dedicados',
          description: 'Sondeos de latencia, jitter RFC 3550 y reportes auditables para penalizaciones de carrier.',
          icon: '⏱️',
          severity: 'OPS',
          routePath: '/enterprise/compliance?tab=sla',
        },
        {
          key: 'outbound_webhooks_enabled',
          label: 'Webhooks Salientes Firmados',
          description: 'Despacho de eventos de red hacia sistemas externos con firma HMAC-SHA256.',
          icon: '🔗',
          severity: 'OPS',
        },
        {
          key: 'ai_mcp_integration_enabled',
          label: 'Servidor MCP para Agentes IA',
          description: 'Acceso a 22 herramientas semánticas de diagnóstico para agentes Hermes y Claude.',
          icon: '🤖',
          severity: 'OPS',
        },
      ],
    },
  ];

  const activeCount = computed(() => {
    return Object.values(props.modelValue).filter((v) => v === true).length;
  });

  const totalCount = computed(() => {
    return quadrants.reduce((acc, q) => acc + q.features.length, 0);
  });

  function isEnabled(key: keyof TenantFeatureFlags): boolean {
    return Boolean(props.modelValue[key]);
  }

  function toggleFeature(feat: FeatureDefinition): void {
    const current = isEnabled(feat.key);

    // Si se va a apagar una flag crítica, requerir confirmación
    if (current && feat.severity === 'CRITICAL') {
      pendingCriticalFlag.value = feat.key;
      pendingCriticalLabel.value = feat.label;
      pendingCriticalDesc.value = feat.description;
      isImpactModalOpen.value = true;
      return;
    }

    applyToggle(feat.key, !current);
  }

  function confirmDisableCritical(): void {
    if (pendingCriticalFlag.value) {
      applyToggle(pendingCriticalFlag.value, false);
    }
    isImpactModalOpen.value = false;
    pendingCriticalFlag.value = null;
  }

  function cancelDisableCritical(): void {
    isImpactModalOpen.value = false;
    pendingCriticalFlag.value = null;
  }

  function applyToggle(key: keyof TenantFeatureFlags, value: boolean): void {
    const updated = { ...props.modelValue, [key]: value };

    // Si se apaga una dependencia padre, apagar las hijas
    if (!value) {
      for (const q of quadrants) {
        for (const f of q.features) {
          if (f.requires === key) {
            (updated as any)[f.key] = false;
          }
        }
      }
    }

    emit('update:modelValue', updated);
  }

  // Presets / Arquetipos en 1 Clic
  function applyPreset(presetType: 'CORP' | 'ISP' | 'NOC' | 'ALL'): void {
    const current = { ...props.modelValue };

    if (presetType === 'CORP') {
      current.isp_module_enabled = false;
      current.bgp_looking_glass_enabled = false;
      current.sfp_ddm_telemetry_enabled = false;
      current.ipfix_analytics_enabled = false;
      current.capsman_wifi_enabled = false;
      current.cis_audit_enabled = true;
      current.auto_safemode_enforced = true;
      current.enforce_maker_checker = true;
      current.syslog_collector_enabled = true;
      current.l2_topology_enabled = true;
      current.nightly_backups_enabled = true;
      current.cve_scanner_enabled = true;
      current.prometheus_fleet_exporter_enabled = true;
      current.ai_mcp_integration_enabled = true;
      current.sla_tracker_enabled = true;
    } else if (presetType === 'ISP') {
      current.isp_module_enabled = true;
      current.bgp_looking_glass_enabled = true;
      current.sfp_ddm_telemetry_enabled = true;
      current.ipfix_analytics_enabled = true;
      current.capsman_wifi_enabled = true;
      current.rogue_dhcp_enabled = true;
      current.syslog_collector_enabled = true;
      current.l2_topology_enabled = true;
      current.nightly_backups_enabled = true;
      current.outbound_webhooks_enabled = true;
      current.prometheus_fleet_exporter_enabled = true;
      current.cve_scanner_enabled = true;
      current.auto_safemode_enforced = true;
      current.ai_mcp_integration_enabled = true;
    } else if (presetType === 'NOC') {
      // Mínimo operativo
      for (const q of quadrants) {
        for (const f of q.features) {
          (current as any)[f.key] = false;
        }
      }
      current.syslog_collector_enabled = true;
      current.l2_topology_enabled = true;
      current.nightly_backups_enabled = true;
      current.cve_scanner_enabled = true;
      current.prometheus_fleet_exporter_enabled = true;
    } else if (presetType === 'ALL') {
      for (const q of quadrants) {
        for (const f of q.features) {
          (current as any)[f.key] = true;
        }
      }
    }

    emit('update:modelValue', current);
  }
</script>

<template>
  <div class="features-grid-container">
    <!-- Barra Superior Táctica de Métricas y Presets -->
    <div class="tactical-header-card">
      <div class="metrics-row">
        <div class="metric-pill">
          <span class="pill-label">Módulos Activos</span>
          <span class="pill-value font-mono">{{ activeCount }} / {{ totalCount }}</span>
        </div>
        <div class="metric-pill">
          <span class="pill-label">Tenant</span>
          <span class="pill-value font-mono">{{ tenantName || 'Actual' }}</span>
        </div>
        <div class="actions-group">
          <button
            type="button"
            class="btn-save-features"
            :disabled="isSaving"
            @click="emit('save')"
          >
            {{ isSaving ? 'Guardando...' : '💾 Guardar Capacidades' }}
          </button>
        </div>
      </div>

      <!-- Selector de Arquetipos en 1 Clic -->
      <div class="presets-row">
        <span class="presets-title">Arquetipos Rápidos:</span>
        <div class="presets-buttons">
          <button type="button" class="btn-preset" @click="applyPreset('CORP')">
            🏢 Modo Corporativo
          </button>
          <button type="button" class="btn-preset" @click="applyPreset('ISP')">
            🌐 Modo ISP & WISP
          </button>
          <button type="button" class="btn-preset" @click="applyPreset('NOC')">
            ⚡ Modo NOC Mínimo
          </button>
          <button type="button" class="btn-preset" @click="applyPreset('ALL')">
            ✨ Todos los Módulos
          </button>
        </div>
      </div>
    </div>

    <!-- 4 Cuadrantes de Dominio Táctico -->
    <div class="quadrants-grid">
      <section v-for="q in quadrants" :key="q.id" class="quadrant-card">
        <div class="quadrant-header">
          <span class="quadrant-icon">{{ q.icon }}</span>
          <h3 class="quadrant-title">{{ q.title }}</h3>
        </div>

        <div class="cards-list">
          <div
            v-for="feat in q.features"
            :key="feat.key"
            class="feature-item-card"
            :class="{
              'feature-item-card--active': isEnabled(feat.key),
              'feature-item-card--disabled': feat.requires && !isEnabled(feat.requires),
            }"
          >
            <div class="card-top">
              <span class="feat-icon">{{ feat.icon }}</span>
              <div class="feat-info">
                <span class="feat-label">{{ feat.label }}</span>
                <span class="feat-key font-mono">{{ feat.key }}</span>
              </div>
              <span
                class="severity-badge"
                :class="`severity-badge--${feat.severity.toLowerCase()}`"
              >
                {{ feat.severity === 'CRITICAL' ? 'Crítico' : feat.severity === 'OPS' ? 'Operativo' : 'Bajo' }}
              </span>
            </div>

            <p class="feat-desc">{{ feat.description }}</p>

            <!-- Alerta de Dependencia -->
            <div v-if="feat.requires && !isEnabled(feat.requires)" class="dependency-alert">
              ⚠️ Requiere activar primero: <strong>{{ feat.requires }}</strong>
            </div>

            <div class="card-bottom">
              <router-link
                v-if="isEnabled(feat.key) && feat.routePath"
                :to="feat.routePath"
                class="context-link"
              >
                Ir al módulo ➔
              </router-link>
              <span v-else class="context-placeholder"></span>

              <label class="switch-toggle" :title="`Alternar ${feat.label}`">
                <input
                  type="checkbox"
                  :checked="isEnabled(feat.key)"
                  :disabled="Boolean(feat.requires && !isEnabled(feat.requires))"
                  @change="toggleFeature(feat)"
                />
                <span class="slider"></span>
              </label>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- Modal de Radio de Impacto (Blast Radius Shield) -->
    <div v-if="isImpactModalOpen" class="impact-modal-backdrop" @click.self="cancelDisableCritical">
      <div class="impact-modal-card" role="dialog" aria-modal="true">
        <div class="impact-modal-header">
          <span class="impact-icon">⚠️</span>
          <h4 class="impact-title">Advertencia de Radio de Impacto</h4>
        </div>

        <p class="impact-text">
          Estás a punto de desactivar un componente de <strong>Gobernanza Crítica</strong>:
        </p>

        <div class="impact-target-box">
          <span class="target-title">{{ pendingCriticalLabel }}</span>
          <span class="target-desc">{{ pendingCriticalDesc }}</span>
        </div>

        <p class="impact-warning">
          Desactivar esta función puede suspender la telemetría viva de routers en producción o suprimir candados obligatorios de seguridad en el NOC.
        </p>

        <div class="impact-modal-actions">
          <button type="button" class="btn-cancel" @click="cancelDisableCritical">
            Cancelar
          </button>
          <button type="button" class="btn-confirm-danger" @click="confirmDisableCritical">
            Confirmar Desactivación
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .features-grid-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  /* Encabezado Táctico */
  .tactical-header-card {
    background: var(--rg-bg-surface, #0f172a);
    border: 1px solid var(--rg-border-panel, #1e293b);
    border-radius: 8px;
    padding: 14px 18px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .metrics-row {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
  }

  .metric-pill {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.2);
    padding: 6px 12px;
    border-radius: 6px;
  }

  .pill-label {
    font-size: 11px;
    color: var(--rg-text-muted, #94a3b8);
    text-transform: uppercase;
  }

  .pill-value {
    font-size: 13px;
    font-weight: 700;
    color: var(--rg-accent-cyan, #06b6d4);
  }

  .actions-group {
    margin-left: auto;
  }

  .btn-save-features {
    padding: 7px 16px;
    background: var(--rg-accent-cyan, #06b6d4);
    color: #0b0f19;
    border: none;
    border-radius: 6px;
    font-weight: 700;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn-save-features:hover {
    box-shadow: 0 0 12px rgba(6, 182, 212, 0.4);
    filter: brightness(1.1);
  }

  .btn-save-features:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  /* Fila de Arquetipos */
  .presets-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-top: 10px;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    flex-wrap: wrap;
  }

  .presets-title {
    font-size: 11px;
    color: var(--rg-text-muted, #94a3b8);
    font-weight: 600;
    text-transform: uppercase;
  }

  .presets-buttons {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .btn-preset {
    padding: 4px 10px;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(148, 163, 184, 0.25);
    border-radius: 4px;
    color: var(--rg-text-primary, #f1f5f9);
    font-size: 11px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-preset:hover {
    background: rgba(6, 182, 212, 0.15);
    border-color: var(--rg-accent-cyan, #06b6d4);
    color: var(--rg-accent-cyan, #06b6d4);
  }

  /* Grid de Cuadrantes */
  .quadrants-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
    gap: 16px;
  }

  .quadrant-card {
    background: var(--rg-bg-surface, #0f172a);
    border: 1px solid var(--rg-border-panel, #1e293b);
    border-radius: 8px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .quadrant-header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  .quadrant-icon {
    font-size: 16px;
  }

  .quadrant-title {
    font-size: 13px;
    font-weight: 700;
    color: var(--rg-text-primary, #f1f5f9);
    margin: 0;
  }

  .cards-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .feature-item-card {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 6px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    transition: all 0.2s ease;
  }

  .feature-item-card--active {
    border-color: rgba(6, 182, 212, 0.35);
    background: rgba(6, 182, 212, 0.04);
  }

  .feature-item-card--disabled {
    opacity: 0.5;
  }

  .card-top {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .feat-icon {
    font-size: 16px;
  }

  .feat-info {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-width: 0;
  }

  .feat-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--rg-text-primary, #f1f5f9);
  }

  .feat-key {
    font-size: 10px;
    color: var(--rg-text-muted, #94a3b8);
  }

  .severity-badge {
    font-size: 9px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    text-transform: uppercase;
  }

  .severity-badge--low {
    background: rgba(148, 163, 184, 0.2);
    color: #94a3b8;
  }

  .severity-badge--ops {
    background: rgba(234, 179, 8, 0.2);
    color: #eab308;
  }

  .severity-badge--critical {
    background: rgba(239, 68, 68, 0.2);
    color: #ef4444;
  }

  .feat-desc {
    font-size: 11px;
    color: var(--rg-text-muted, #94a3b8);
    margin: 0;
    line-height: 1.4;
  }

  .dependency-alert {
    font-size: 10px;
    color: #eab308;
    background: rgba(234, 179, 8, 0.1);
    padding: 4px 8px;
    border-radius: 4px;
  }

  .card-bottom {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 4px;
  }

  .context-link {
    font-size: 11px;
    color: var(--rg-accent-cyan, #06b6d4);
    text-decoration: none;
    transition: underline 0.15s ease;
  }

  .context-link:hover {
    text-decoration: underline;
  }

  .context-placeholder {
    width: 1px;
  }

  /* Switch Táctico */
  .switch-toggle {
    position: relative;
    display: inline-block;
    width: 36px;
    height: 20px;
  }

  .switch-toggle input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #334155;
    transition: 0.2s ease;
    border-radius: 20px;
  }

  .slider:before {
    position: absolute;
    content: '';
    height: 14px;
    width: 14px;
    left: 3px;
    bottom: 3px;
    background-color: #ffffff;
    transition: 0.2s ease;
    border-radius: 50%;
  }

  input:checked + .slider {
    background-color: var(--rg-accent-cyan, #06b6d4);
  }

  input:checked + .slider:before {
    transform: translateX(16px);
  }

  input:disabled + .slider {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Modal de Impacto */
  .impact-modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1200;
  }

  .impact-modal-card {
    background: var(--rg-bg-surface, #0f172a);
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: 8px;
    padding: 20px;
    width: 440px;
    max-width: 90vw;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8);
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .impact-modal-header {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .impact-icon {
    font-size: 24px;
  }

  .impact-title {
    font-size: 15px;
    font-weight: 700;
    color: #ef4444;
    margin: 0;
  }

  .impact-text {
    font-size: 12px;
    color: var(--rg-text-primary, #f1f5f9);
    margin: 0;
  }

  .impact-target-box {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 6px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .target-title {
    font-size: 13px;
    font-weight: 700;
    color: var(--rg-text-primary, #f1f5f9);
  }

  .target-desc {
    font-size: 11px;
    color: var(--rg-text-muted, #94a3b8);
  }

  .impact-warning {
    font-size: 11px;
    color: #eab308;
    margin: 0;
    line-height: 1.4;
  }

  .impact-modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding-top: 10px;
  }

  .btn-cancel {
    padding: 6px 14px;
    background: transparent;
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 5px;
    color: var(--rg-text-muted, #94a3b8);
    font-size: 12px;
    cursor: pointer;
  }

  .btn-confirm-danger {
    padding: 6px 14px;
    background: #ef4444;
    border: none;
    border-radius: 5px;
    color: #ffffff;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
  }

  .btn-confirm-danger:hover {
    background: #dc2626;
  }
</style>
