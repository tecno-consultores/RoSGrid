<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { computed, onMounted, ref, watch } from 'vue';
  import { useI18n } from '@/composables/useI18n';
  import { http } from '@/api/httpClient';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import type {
    CapsmanOverviewResponse,
    CisAuditResponse,
    CisAutoHardenResponse,
    ConfigDriftCheckResponse,
    ConfigDriftRevertResponse,
    DhcpSnoopingState,
    GoldenConfigTemplate,
    RogueDhcpAlertItem,
    RogueDhcpIsolatePortResponse,
    SdwanMultiWanFailoverResponse,
    SdwanSpokeTunnel,
    SdwanTopologyResponse,
    SlaMetricItem,
    SlaReportSummary,
    WifiClientItem,
    WifiSsidProfile,
  } from '@/types';

  const { t } = useI18n();
  const authStore = useAuthStore();
  const inventoryStore = useInventoryStore();

  type TabType = 'drift' | 'cis' | 'sdwan' | 'switching' | 'sla' | 'wifi';
  const activeTab = ref<TabType>('drift');

  const selectedRouterId = ref<string>('');
  const isLoading = ref<boolean>(false);
  const actionLoading = ref<boolean>(false);
  const errorMessage = ref<string>('');
  const successMessage = ref<string>('');

  // 1. Config Drift State
  const goldenTemplates = ref<GoldenConfigTemplate[]>([]);
  const driftResult = ref<ConfigDriftCheckResponse | null>(null);
  const selectedTemplateId = ref<string>('');

  // 2. CIS Benchmark State
  const cisAudit = ref<CisAuditResponse | null>(null);

  // 3. SD-WAN State
  const sdwanTopology = ref<SdwanTopologyResponse | null>(null);
  const sdwanSpokes = ref<SdwanSpokeTunnel[]>([]);
  const newSpoke = ref({
    spoke_name: '',
    hub_router_id: '',
    spoke_router_id: '',
    routing_protocol: 'BGP',
    multi_wan_failover_enabled: true,
  });
  const multiWanForm = ref({
    primary_wan_interface: 'ether1-fiber',
    backup_wan_interface: 'lte1',
    check_host: '1.1.1.1',
    failover_threshold_ms: 80,
  });

  // 4. Switching & Rogue DHCP State
  const snoopingBridges = ref<DhcpSnoopingState[]>([]);
  const rogueAlerts = ref<RogueDhcpAlertItem[]>([]);

  // 5. SLA State
  const slaMetrics = ref<SlaMetricItem[]>([]);
  const slaProbeForm = ref({
    target_host: '8.8.8.8',
    target_name: 'Google-Primary-DNS',
    sla_threshold_ms: 45,
    count: 10,
  });
  const slaReport = ref<SlaReportSummary | null>(null);

  // 6. Wi-Fi CAPsMAN State
  const capsmanOverview = ref<CapsmanOverviewResponse | null>(null);
  const wifiSsids = ref<WifiSsidProfile[]>([]);
  const wifiClients = ref<WifiClientItem[]>([]);

  const routersList = computed(() => inventoryStore.routers);

  // Auto-seleccionar primer router disponible
  watch(
    () => inventoryStore.routers,
    (routers) => {
      if (routers && routers.length > 0 && !selectedRouterId.value) {
        selectedRouterId.value = routers[0].id;
        loadTabData();
      }
    },
    { immediate: true },
  );

  watch(selectedRouterId, () => {
    if (selectedRouterId.value) {
      loadTabData();
    }
  });

  watch(activeTab, () => {
    loadTabData();
  });

  async function loadDriftTab() {
    const [tplRes, driftRes] = await Promise.all([
      http.get<GoldenConfigTemplate[]>('/api/v1/compliance/golden-templates'),
      http.get<ConfigDriftCheckResponse>(
        `/api/v1/compliance/config-drift/${selectedRouterId.value}`,
      ),
    ]);
    goldenTemplates.value = tplRes.data || [];
    driftResult.value = driftRes.data;
  }

  async function loadCisTab() {
    const res = await http.get<CisAuditResponse>(
      `/api/v1/compliance/cis-audit/${selectedRouterId.value}`,
    );
    cisAudit.value = res.data;
  }

  async function loadSdwanTab() {
    const tenantId = authStore.user?.tenant_id;
    if (tenantId) {
      const topoRes = await http.get<SdwanTopologyResponse>(`/api/v1/sdwan/topology/${tenantId}`);
      sdwanTopology.value = topoRes.data;
      sdwanSpokes.value = topoRes.data?.tunnels || [];
    }
  }

  async function loadSwitchingTab() {
    const [bridgesRes, alertsRes] = await Promise.all([
      http.get<DhcpSnoopingState[]>(`/api/v1/switching/dhcp-snooping/${selectedRouterId.value}`),
      http.get<RogueDhcpAlertItem[]>(
        `/api/v1/switching/rogue-dhcp/alerts/${selectedRouterId.value}`,
      ),
    ]);
    snoopingBridges.value = bridgesRes.data || [];
    rogueAlerts.value = alertsRes.data || [];
  }

  async function loadSlaTab() {
    const metricsRes = await http.get<SlaMetricItem[]>(
      `/api/v1/sla/metrics/${selectedRouterId.value}?limit=20`,
    );
    slaMetrics.value = metricsRes.data || [];
  }

  async function loadWifiTab() {
    const [overviewRes, ssidsRes, clientsRes] = await Promise.all([
      http.get<CapsmanOverviewResponse>(`/api/v1/wifi/capsman/${selectedRouterId.value}/overview`),
      http.get<WifiSsidProfile[]>(`/api/v1/wifi/capsman/${selectedRouterId.value}/ssids`),
      http.get<WifiClientItem[]>(`/api/v1/wifi/clients/${selectedRouterId.value}`),
    ]);
    capsmanOverview.value = overviewRes.data;
    wifiSsids.value = ssidsRes.data || [];
    wifiClients.value = clientsRes.data || [];
  }

  async function loadTabData() {
    errorMessage.value = '';
    successMessage.value = '';
    if (!selectedRouterId.value) return;

    isLoading.value = true;
    try {
      switch (activeTab.value) {
        case 'drift':
          await loadDriftTab();
          break;
        case 'cis':
          await loadCisTab();
          break;
        case 'sdwan':
          await loadSdwanTab();
          break;
        case 'switching':
          await loadSwitchingTab();
          break;
        case 'sla':
          await loadSlaTab();
          break;
        case 'wifi':
          await loadWifiTab();
          break;
      }
    } catch (err: unknown) {
      const e = err as { message?: string; detail?: string };
      errorMessage.value =
        e.detail || e.message || 'Error al sincronizar datos del módulo corporativo';
    } finally {
      isLoading.value = false;
    }
  }

  // 1. Revert Config Drift
  async function handleRevertDrift() {
    if (!selectedRouterId.value) return;
    actionLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.post<ConfigDriftRevertResponse>(
        '/api/v1/compliance/config-drift/revert',
        {
          router_id: selectedRouterId.value,
          template_id: selectedTemplateId.value || undefined,
          enforce_safemode: true,
        },
      );
      successMessage.value = `${res.data.remediation_summary} (WORM Audit ID: ${res.data.audit_log_id})`;
      await loadTabData();
    } catch (err: unknown) {
      const e = err as { message?: string; detail?: string };
      errorMessage.value = e.detail || e.message || 'Fallo al revertir configuración';
    } finally {
      actionLoading.value = false;
    }
  }

  // 2. Auto-Harden CIS
  async function handleAutoHarden() {
    if (!selectedRouterId.value) return;
    actionLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.post<CisAutoHardenResponse>(
        `/api/v1/compliance/cis-audit/${selectedRouterId.value}/auto-harden`,
        {
          router_id: selectedRouterId.value,
        },
      );
      successMessage.value = `¡Endurecimiento completado! Nuevo puntaje de seguridad: ${res.data.new_security_score}/100. Directivas aplicadas: ${res.data.applied_directives_count}.`;
      await loadTabData();
    } catch (err: unknown) {
      const e = err as { message?: string; detail?: string };
      errorMessage.value = e.detail || e.message || 'Fallo durante el auto-hardening del router';
    } finally {
      actionLoading.value = false;
    }
  }

  // 3. Provision SD-WAN Spoke
  async function handleProvisionSpoke() {
    if (!newSpoke.value.spoke_name) {
      errorMessage.value = 'El nombre de la sucursal/spoke es obligatorio.';
      return;
    }
    actionLoading.value = true;
    errorMessage.value = '';
    try {
      await http.post('/api/v1/sdwan/spokes', {
        hub_router_id: newSpoke.value.hub_router_id || selectedRouterId.value,
        spoke_router_id: newSpoke.value.spoke_router_id || selectedRouterId.value,
        spoke_name: newSpoke.value.spoke_name,
        routing_protocol: newSpoke.value.routing_protocol,
        multi_wan_failover_enabled: newSpoke.value.multi_wan_failover_enabled,
      });
      successMessage.value = `Spoke ${newSpoke.value.spoke_name} aprovisionado con éxito.`;
      newSpoke.value.spoke_name = '';
      await loadTabData();
    } catch (err: unknown) {
      const e = err as { message?: string; detail?: string };
      errorMessage.value = e.detail || e.message || 'Error al aprovisionar túnel SD-WAN';
    } finally {
      actionLoading.value = false;
    }
  }

  // Multi-WAN Failover Deploy
  async function handleDeployMultiWan() {
    if (!selectedRouterId.value) return;
    actionLoading.value = true;
    try {
      const res = await http.post<SdwanMultiWanFailoverResponse>(
        '/api/v1/sdwan/multi-wan/failover',
        {
          router_id: selectedRouterId.value,
          ...multiWanForm.value,
        },
      );
      successMessage.value = `Política de failover recursivo desplegada exitosamente bajo Safe Mode. Script ID: ${res.data.netwatch_script_id}`;
    } catch (err: unknown) {
      const e = err as { message?: string; detail?: string };
      errorMessage.value = e.detail || e.message || 'Error al desplegar política Multi-WAN';
    } finally {
      actionLoading.value = false;
    }
  }

  // 4. Isolate Rogue DHCP Port
  async function handleIsolatePort(interfaceName: string) {
    if (!selectedRouterId.value) return;
    actionLoading.value = true;
    try {
      const res = await http.post<RogueDhcpIsolatePortResponse>(
        '/api/v1/switching/rogue-dhcp/isolate-port',
        {
          router_id: selectedRouterId.value,
          interface_name: interfaceName,
          reason: 'Servidor DHCP no autorizado detectado en bridge',
        },
      );
      successMessage.value = `Puerto ${res.data.interface_name} aislado y deshabilitado administrativamente (Safe Mode 60s).`;
      await loadTabData();
    } catch (err: unknown) {
      const e = err as { message?: string; detail?: string };
      errorMessage.value = e.detail || e.message || 'Error al aislar puerto';
    } finally {
      actionLoading.value = false;
    }
  }

  // 5. Trigger Immediate SLA Probe
  async function handleTriggerProbe() {
    if (!selectedRouterId.value) return;
    actionLoading.value = true;
    try {
      await http.post('/api/v1/sla/probes/run', {
        router_id: selectedRouterId.value,
        ...slaProbeForm.value,
      });
      successMessage.value = 'Ciclo de sondeo SLA ejecutado y persistido con éxito.';
      await loadTabData();
    } catch (err: unknown) {
      const e = err as { message?: string; detail?: string };
      errorMessage.value = e.detail || e.message || 'Error al ejecutar sondeo SLA';
    } finally {
      actionLoading.value = false;
    }
  }

  // Export SLA Report
  async function handleExportSlaReport() {
    actionLoading.value = true;
    try {
      const res = await http.get<SlaReportSummary>(
        `/api/v1/sla/reports/export?router_id=${selectedRouterId.value}`,
      );
      const report = res.data;
      slaReport.value = report;
      const dataStr =
        'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(report, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute(
        'download',
        `SLA_Report_${selectedRouterId.value}_${new Date().toISOString().slice(0, 10)}.json`,
      );
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      successMessage.value = 'Informe formal de SLA exportado para auditoría.';
    } catch (err: unknown) {
      const e = err as { message?: string; detail?: string };
      errorMessage.value = e.detail || e.message || 'Error al exportar informe SLA';
    } finally {
      actionLoading.value = false;
    }
  }

  onMounted(() => {
    if (inventoryStore.routers.length === 0) {
      inventoryStore.fetchRouters();
    } else {
      selectedRouterId.value = inventoryStore.routers[0].id;
      loadTabData();
    }
  });
</script>

<template>
  <main
    class="enterprise-compliance-view"
    role="main"
    aria-label="Gestión de Flota & Cumplimiento Normativo"
  >
    <!-- Header Corporativo -->
    <header class="view-header">
      <div class="header-titles">
        <h1 class="tactical-heading">
          <span class="icon" aria-hidden="true">🛡️</span>
          {{ t('enterprise.title', 'Gestión de Flota & Cumplimiento Normativo') }}
        </h1>
        <p class="tactical-subtitle">
          {{
            t(
              'enterprise.subtitle',
              'Config Drift, Auditoría CIS Benchmark, SD-WAN WireGuard, Rogue DHCP, SLA & Wi-Fi',
            )
          }}
        </p>
      </div>

      <!-- Selector de Router & Safe Mode Status -->
      <div class="header-controls">
        <div
          class="safemode-badge"
          title="Todas las mutaciones están protegidas bajo Safe Mode de 60s"
        >
          <span class="indicator-dot pulse"></span>
          <span>{{ t('enterprise.safemode_notice', 'Safe Mode (60s) Activo') }}</span>
        </div>

        <div class="router-selector-box">
          <label for="compliance-router-select" class="sr-only"
            >Seleccionar Router de la Flota</label
          >
          <select
            id="compliance-router-select"
            v-model="selectedRouterId"
            class="tactical-select"
            aria-label="Seleccionar router de la flota"
          >
            <option value="" disabled>Seleccione un equipo...</option>
            <option v-for="r in routersList" :key="r.id" :value="r.id">
              {{ r.display_name }} ({{ r.ip_address }}) [{{ r.network_role }}]
            </option>
          </select>
        </div>
      </div>
    </header>

    <!-- Feedback Banners -->
    <div v-if="errorMessage" class="alert-banner alert-error" role="alert" aria-live="assertive">
      <span class="alert-icon">⚠️</span>
      <span>{{ errorMessage }}</span>
    </div>
    <div v-if="successMessage" class="alert-banner alert-success" role="status" aria-live="polite">
      <span class="alert-icon">✅</span>
      <span>{{ successMessage }}</span>
    </div>

    <!-- Barra de Pestañas Tácticas (6 Módulos de Hito 20) -->
    <nav class="tactical-tabs-nav" aria-label="Módulos de Cumplimiento">
      <button
        id="tab-btn-drift"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'drift' }"
        :aria-selected="activeTab === 'drift'"
        role="tab"
        aria-controls="panel-drift"
        @click="activeTab = 'drift'"
      >
        <span class="tab-icon">📑</span>
        <span>{{ t('enterprise.tab_drift', 'Config Drift & Baselines') }}</span>
      </button>

      <button
        id="tab-btn-cis"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'cis' }"
        :aria-selected="activeTab === 'cis'"
        role="tab"
        aria-controls="panel-cis"
        @click="activeTab = 'cis'"
      >
        <span class="tab-icon">🔒</span>
        <span>{{ t('enterprise.tab_cis', 'CIS Benchmark Hardening') }}</span>
      </button>

      <button
        id="tab-btn-sdwan"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'sdwan' }"
        :aria-selected="activeTab === 'sdwan'"
        role="tab"
        aria-controls="panel-sdwan"
        @click="activeTab = 'sdwan'"
      >
        <span class="tab-icon">🌐</span>
        <span>{{ t('enterprise.tab_sdwan', 'SD-WAN Hub & Spoke') }}</span>
      </button>

      <button
        id="tab-btn-switching"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'switching' }"
        :aria-selected="activeTab === 'switching'"
        role="tab"
        aria-controls="panel-switching"
        @click="activeTab = 'switching'"
      >
        <span class="tab-icon">⚡</span>
        <span>{{ t('enterprise.tab_switching', 'Seguridad L2 & Rogue DHCP') }}</span>
      </button>

      <button
        id="tab-btn-sla"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'sla' }"
        :aria-selected="activeTab === 'sla'"
        role="tab"
        aria-controls="panel-sla"
        @click="activeTab = 'sla'"
      >
        <span class="tab-icon">⏱️</span>
        <span>{{ t('enterprise.tab_sla', 'Telemetría de SLA') }}</span>
      </button>

      <button
        id="tab-btn-wifi"
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'wifi' }"
        :aria-selected="activeTab === 'wifi'"
        role="tab"
        aria-controls="panel-wifi"
        @click="activeTab = 'wifi'"
      >
        <span class="tab-icon">📶</span>
        <span>{{ t('enterprise.tab_wifi', 'Wi-Fi CAPsMAN') }}</span>
      </button>
    </nav>

    <!-- Contenedor Principal de Pestañas -->
    <div class="tab-content-container">
      <div v-if="isLoading" class="loading-state" aria-busy="true">
        <div class="tactical-spinner"></div>
        <p>Sincronizando estado técnico con RouterOS v7...</p>
      </div>

      <!-- ================================================================= -->
      <!-- TAB 1: Config Drift & Baselines (Sub-tarea 20.1)                  -->
      <!-- ================================================================= -->
      <section
        v-else-if="activeTab === 'drift'"
        id="panel-drift"
        role="tabpanel"
        aria-labelledby="tab-btn-drift"
        class="tab-panel"
      >
        <div class="panel-action-bar">
          <div class="drift-summary-meta">
            <span class="meta-item">
              <strong>Plantilla Maestra:</strong>
              {{ driftResult?.baseline_template_name || 'Predeterminada' }}
            </span>
            <span class="meta-item">
              <strong>Estado:</strong>
              <span
                class="badge"
                :class="driftResult?.drift_detected ? 'badge-danger' : 'badge-success'"
              >
                {{
                  driftResult?.drift_detected ? 'DESVIACIÓN DETECTADA' : 'CONFIGURACIÓN HOMOLOGADA'
                }}
              </span>
            </span>
            <span class="meta-item">
              <strong>Líneas no autorizadas:</strong>
              {{ driftResult?.total_drift_lines || 0 }}
            </span>
          </div>

          <button
            id="btn-revert-drift"
            type="button"
            class="tactical-btn btn-danger"
            :disabled="actionLoading || !driftResult?.drift_detected"
            @click="handleRevertDrift"
          >
            <span>🔄</span>
            {{ t('enterprise.revert_drift', 'Revertir a Plantilla Homologada') }}
          </button>
        </div>

        <!-- Visor de Git Diff Unificado -->
        <div class="git-diff-viewer" aria-label="Diferencias de configuración">
          <div class="diff-header">
            <span>Diferencias contra Línea Base Golden Template</span>
            <span class="diff-sub">Verde: Añadido en router | Rojo: Faltante según estándar</span>
          </div>
          <pre class="diff-pre"><code><span
            v-for="(line, lineIdx) in (driftResult?.diff_unified || '').split('\n')"
            :key="lineIdx"
            :class="line.startsWith('+') ? 'diff-line-add' : line.startsWith('-') ? 'diff-line-del' : 'diff-line-ctx'"
          >{{ line }}
</span></code></pre>
        </div>
      </section>

      <!-- ================================================================= -->
      <!-- TAB 2: CIS Benchmark Hardening (Sub-tarea 20.3)                   -->
      <!-- ================================================================= -->
      <section
        v-else-if="activeTab === 'cis'"
        id="panel-cis"
        role="tabpanel"
        aria-labelledby="tab-btn-cis"
        class="tab-panel"
      >
        <div class="cis-score-dashboard">
          <div class="score-card">
            <div class="score-number">{{ cisAudit?.security_score ?? '--' }}/100</div>
            <div class="score-grade" :class="'grade-' + (cisAudit?.compliance_grade || 'C')">
              Grado {{ cisAudit?.compliance_grade || 'C' }}
            </div>
            <p class="score-desc">Puntaje Global de Cumplimiento Normativo CIS</p>
          </div>

          <div class="score-meta-card">
            <div class="metric-row">
              <span>Directivas Evaluadas:</span>
              <strong>{{ cisAudit?.total_directives || 10 }}</strong>
            </div>
            <div class="metric-row">
              <span>Directivas Aprobadas:</span>
              <strong class="text-success">{{ cisAudit?.passed_directives || 0 }}</strong>
            </div>
            <div class="metric-row">
              <span>Directivas Fallidas / Riesgo:</span>
              <strong class="text-danger">{{ cisAudit?.failed_directives || 0 }}</strong>
            </div>
            <button
              id="btn-auto-harden"
              type="button"
              class="tactical-btn btn-primary"
              :disabled="actionLoading"
              @click="handleAutoHarden"
            >
              <span>🚀</span>
              {{ t('enterprise.auto_harden', 'Endurecer Router (Auto-Hardening)') }}
            </button>
          </div>
        </div>

        <!-- Tabla de las 10 Directivas CIS -->
        <div class="tactical-table-wrapper">
          <table class="tactical-table" aria-label="Directivas CIS Benchmark">
            <thead>
              <tr>
                <th scope="col">Código</th>
                <th scope="col">Directiva Técnica</th>
                <th scope="col">Peso</th>
                <th scope="col">Estado</th>
                <th scope="col">Hallazgo Técnico</th>
                <th scope="col">Remediación Automática</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in cisAudit?.directives || []" :key="d.code">
                <td class="font-mono text-cyan">{{ d.code }}</td>
                <td>{{ d.title }}</td>
                <td>{{ d.weight }} pts</td>
                <td>
                  <span class="badge" :class="d.passed ? 'badge-success' : 'badge-danger'">
                    {{ d.passed ? 'APROBADO' : 'FALLIDO' }}
                  </span>
                </td>
                <td class="text-subtle">{{ d.finding }}</td>
                <td>
                  <code class="remediation-snippet">{{ d.remediation_cmd }}</code>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ================================================================= -->
      <!-- TAB 3: SD-WAN WireGuard Hub & Spoke (Sub-tarea 20.2)              -->
      <!-- ================================================================= -->
      <section
        v-else-if="activeTab === 'sdwan'"
        id="panel-sdwan"
        role="tabpanel"
        aria-labelledby="tab-btn-sdwan"
        class="tab-panel"
      >
        <div class="sdwan-grid">
          <!-- Formulario de Aprovisionamiento Spoke -->
          <div class="sdwan-card">
            <h2 class="card-title">Aprovisionar Sucursal Spoke</h2>
            <form class="tactical-form" @submit.prevent="handleProvisionSpoke">
              <div class="form-group">
                <label for="spoke-name-input">Nombre de la Sucursal</label>
                <input
                  id="spoke-name-input"
                  v-model="newSpoke.spoke_name"
                  type="text"
                  class="tactical-input"
                  placeholder="Ej: Sucursal-Valencia-Norte"
                  required
                />
              </div>

              <div class="form-group">
                <label for="spoke-proto-select">Protocolo de Enrutamiento</label>
                <select
                  id="spoke-proto-select"
                  v-model="newSpoke.routing_protocol"
                  class="tactical-select"
                >
                  <option value="BGP">BGP (Border Gateway Protocol v7)</option>
                  <option value="OSPF">OSPFv3</option>
                  <option value="STATIC">Rutas Estáticas / PBR</option>
                </select>
              </div>

              <button type="submit" class="tactical-btn btn-primary" :disabled="actionLoading">
                <span>➕</span>
                {{ t('enterprise.provision_spoke', 'Aprovisionar Spoke WireGuard') }}
              </button>
            </form>
          </div>

          <!-- Failover Multi-WAN PBR -->
          <div class="sdwan-card">
            <h2 class="card-title">Políticas Multi-WAN & Netwatch Failover</h2>
            <form class="tactical-form" @submit.prevent="handleDeployMultiWan">
              <div class="form-row">
                <div class="form-group">
                  <label for="wan-primary-input">WAN Primaria</label>
                  <input
                    id="wan-primary-input"
                    v-model="multiWanForm.primary_wan_interface"
                    type="text"
                    class="tactical-input"
                    required
                  />
                </div>
                <div class="form-group">
                  <label for="wan-backup-input">WAN Respaldo (LTE/Radio)</label>
                  <input
                    id="wan-backup-input"
                    v-model="multiWanForm.backup_wan_interface"
                    type="text"
                    class="tactical-input"
                    required
                  />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="wan-check-host">Host Sondeo (Netwatch)</label>
                  <input
                    id="wan-check-host"
                    v-model="multiWanForm.check_host"
                    type="text"
                    class="tactical-input"
                    required
                  />
                </div>
                <div class="form-group">
                  <label for="wan-threshold-ms">Umbral Conmutación (ms)</label>
                  <input
                    id="wan-threshold-ms"
                    v-model="multiWanForm.failover_threshold_ms"
                    type="number"
                    class="tactical-input"
                    required
                  />
                </div>
              </div>

              <button type="submit" class="tactical-btn btn-secondary" :disabled="actionLoading">
                <span>⚡</span>
                {{ t('enterprise.deploy_failover', 'Desplegar Failover Multi-WAN') }}
              </button>
            </form>
          </div>
        </div>

        <!-- Lista de Túneles Spoke Activos -->
        <div class="tactical-table-wrapper" style="margin-top: 1.5rem">
          <table class="tactical-table" aria-label="Túneles SD-WAN Spoke">
            <thead>
              <tr>
                <th scope="col">Sucursal Spoke</th>
                <th scope="col">Interfaz</th>
                <th scope="col">Subred Punto a Punto</th>
                <th scope="col">Endpoint Hub</th>
                <th scope="col">Protocolo</th>
                <th scope="col">Failover Multi-WAN</th>
                <th scope="col">Estado</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in sdwanSpokes" :key="s.id">
                <td class="font-bold text-cyan">{{ s.spoke_name }}</td>
                <td class="font-mono">{{ s.interface_name }}</td>
                <td class="font-mono">{{ s.allocated_subnet }}</td>
                <td class="font-mono text-subtle">{{ s.hub_endpoint }}</td>
                <td>
                  <span class="badge badge-info">{{ s.routing_protocol }}</span>
                </td>
                <td>{{ s.multi_wan_failover_enabled ? 'Habilitado' : 'Deshabilitado' }}</td>
                <td>
                  <span
                    class="badge"
                    :class="s.status === 'ACTIVE' ? 'badge-success' : 'badge-warning'"
                  >
                    {{ s.status }}
                  </span>
                </td>
              </tr>
              <tr v-if="sdwanSpokes.length === 0">
                <td colspan="7" class="text-center text-subtle">
                  No hay túneles Spoke aprovisionados en el tenant actual.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ================================================================= -->
      <!-- TAB 4: Seguridad L2 & Rogue DHCP (Sub-tarea 20.4)                 -->
      <!-- ================================================================= -->
      <section
        v-else-if="activeTab === 'switching'"
        id="panel-switching"
        role="tabpanel"
        aria-labelledby="tab-btn-switching"
        class="tab-panel"
      >
        <div class="snooping-cards-grid">
          <div v-for="b in snoopingBridges" :key="b.bridge_name" class="bridge-card">
            <div class="bridge-header">
              <h2 class="bridge-name">Bridge: {{ b.bridge_name }}</h2>
              <span
                class="badge"
                :class="b.dhcp_snooping_enabled ? 'badge-success' : 'badge-danger'"
              >
                DHCP Snooping: {{ b.dhcp_snooping_enabled ? 'ACTIVO' : 'INACTIVO' }}
              </span>
            </div>

            <div class="ports-classification">
              <div>
                <span class="ports-title text-success">Puertos Confiables (Trusted / Uplink):</span>
                <div class="tags-group">
                  <span v-for="p in b.trusted_ports" :key="p" class="port-tag tag-trusted">
                    {{ p }}
                  </span>
                </div>
              </div>

              <div>
                <span class="ports-title text-warning"
                  >Puertos de Acceso (Untrusted / Confinados):</span
                >
                <div class="tags-group">
                  <span v-for="p in b.untrusted_ports" :key="p" class="port-tag tag-untrusted">
                    {{ p }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Alertas de Rogue DHCP -->
        <h2 class="section-subtitle" style="margin-top: 1.5rem">
          Servidores DHCP No Autorizados Detectados (Rogue DHCP)
        </h2>
        <div class="tactical-table-wrapper">
          <table class="tactical-table" aria-label="Alertas Rogue DHCP">
            <thead>
              <tr>
                <th scope="col">ID Alerta</th>
                <th scope="col">MAC Atacante/Rogue</th>
                <th scope="col">IP Ofrecida</th>
                <th scope="col">Puerto / Interfaz</th>
                <th scope="col">Estado</th>
                <th scope="col">Acción Inmediata</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in rogueAlerts" :key="a.id">
                <td class="font-mono text-subtle">{{ a.id }}</td>
                <td class="font-mono text-danger font-bold">{{ a.rogue_server_mac }}</td>
                <td class="font-mono">{{ a.rogue_server_ip }}</td>
                <td class="font-mono text-cyan">{{ a.interface_name }}</td>
                <td>
                  <span
                    class="badge"
                    :class="a.status === 'BLOCKED_BY_HARDWARE' ? 'badge-success' : 'badge-danger'"
                  >
                    {{ a.status }}
                  </span>
                </td>
                <td>
                  <button
                    type="button"
                    class="tactical-btn btn-sm btn-danger"
                    :disabled="actionLoading"
                    @click="handleIsolatePort(a.interface_name)"
                  >
                    <span>🚨</span>
                    {{ t('enterprise.isolate_port', 'Aislar Puerto') }}
                  </button>
                </td>
              </tr>
              <tr v-if="rogueAlerts.length === 0">
                <td colspan="6" class="text-center text-success">
                  Cero servidores DHCP no autorizados detectados en la red.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- ================================================================= -->
      <!-- TAB 5: Telemetría de SLA en Tiempo Real (Sub-tarea 20.5)          -->
      <!-- ================================================================= -->
      <section
        v-else-if="activeTab === 'sla'"
        id="panel-sla"
        role="tabpanel"
        aria-labelledby="tab-btn-sla"
        class="tab-panel"
      >
        <div class="panel-action-bar">
          <div class="sla-actions">
            <button
              id="btn-export-sla"
              type="button"
              class="tactical-btn btn-secondary"
              :disabled="actionLoading"
              @click="handleExportSlaReport"
            >
              <span>📥</span>
              {{ t('enterprise.export_sla', 'Exportar Reporte Formal de SLA') }}
            </button>
          </div>
        </div>

        <!-- Tabla de Métricas de SLA -->
        <div class="tactical-table-wrapper">
          <table class="tactical-table" aria-label="Métricas de Cumplimiento de SLA">
            <thead>
              <tr>
                <th scope="col">Destino / Gateway</th>
                <th scope="col">Nombre Enlace</th>
                <th scope="col">Uptime %</th>
                <th scope="col">Latencia Media</th>
                <th scope="col">P95 Latency</th>
                <th scope="col">P99 Latency</th>
                <th scope="col">Jitter</th>
                <th scope="col">Pérdida %</th>
                <th scope="col">Umbral SLA</th>
                <th scope="col">Estado Contrato</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in slaMetrics" :key="m.id">
                <td class="font-mono text-cyan">{{ m.target_host }}</td>
                <td>{{ m.target_name }}</td>
                <td class="font-bold">{{ m.uptime_percent }}%</td>
                <td>{{ m.avg_latency_ms }} ms</td>
                <td>{{ m.p95_latency_ms }} ms</td>
                <td>{{ m.p99_latency_ms }} ms</td>
                <td>{{ m.jitter_ms }} ms</td>
                <td>{{ m.packet_loss_pct }}%</td>
                <td>&lt;= {{ m.sla_threshold_ms }} ms</td>
                <td>
                  <span
                    class="badge"
                    :class="m.compliance_status === 'COMPLIANT' ? 'badge-success' : 'badge-danger'"
                  >
                    {{ m.compliance_status }}
                  </span>
                </td>
              </tr>
              <tr v-if="slaMetrics.length === 0">
                <td colspan="10" class="text-center text-subtle">
                  No se han registrado ciclos de sondeo SLA para este router.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Formulario de Ejecución de Sondeo Inmediato -->
        <div class="sla-form-card" style="margin-top: 1.5rem">
          <h2 class="card-title">Ejecutar Ciclo de Sondeo Inmediato</h2>
          <form class="tactical-form form-inline" @submit.prevent="handleTriggerProbe">
            <div class="form-group">
              <label for="sla-target-host">Host / IP Destino</label>
              <input
                id="sla-target-host"
                v-model="slaProbeForm.target_host"
                type="text"
                class="tactical-input"
                required
              />
            </div>
            <div class="form-group">
              <label for="sla-target-name">Nombre del Enlace</label>
              <input
                id="sla-target-name"
                v-model="slaProbeForm.target_name"
                type="text"
                class="tactical-input"
              />
            </div>
            <div class="form-group">
              <label for="sla-threshold">Umbral Máximo (ms)</label>
              <input
                id="sla-threshold"
                v-model="slaProbeForm.sla_threshold_ms"
                type="number"
                class="tactical-input"
                required
              />
            </div>
            <button type="submit" class="tactical-btn btn-primary" :disabled="actionLoading">
              <span>⏱️</span>
              Ejecutar Sondeo
            </button>
          </form>
        </div>
      </section>

      <!-- ================================================================= -->
      <!-- TAB 6: Wi-Fi CAPsMAN / WiFiWave2 (Sub-tarea 20.6)                 -->
      <!-- ================================================================= -->
      <section
        v-else-if="activeTab === 'wifi'"
        id="panel-wifi"
        role="tabpanel"
        aria-labelledby="tab-btn-wifi"
        class="tab-panel"
      >
        <div class="wifi-overview-grid">
          <div class="wifi-stat-card">
            <div class="stat-number text-cyan">{{ capsmanOverview?.managed_aps_count || 0 }}</div>
            <div class="stat-label">Puntos de Acceso (APs) Gestionados</div>
          </div>
          <div class="wifi-stat-card">
            <div class="stat-number text-success">
              {{ capsmanOverview?.active_radios_count || 0 }}
            </div>
            <div class="stat-label">Radios Activas (2.4GHz / 5GHz / 6GHz)</div>
          </div>
          <div class="wifi-stat-card">
            <div class="stat-number text-primary">
              {{ capsmanOverview?.connected_clients_count || 0 }}
            </div>
            <div class="stat-label">Clientes Inalámbricos Conectados</div>
          </div>
        </div>

        <!-- Perfiles de SSIDs -->
        <h2 class="section-subtitle" style="margin-top: 1.5rem">
          Perfiles de Redes Inalámbricas (SSIDs)
        </h2>
        <div class="tactical-table-wrapper">
          <table class="tactical-table" aria-label="SSIDs CAPsMAN">
            <thead>
              <tr>
                <th scope="col">Nombre Perfil</th>
                <th scope="col">SSID Emitido</th>
                <th scope="col">Protocolo de Seguridad</th>
                <th scope="col">VLAN</th>
                <th scope="col">Aislamiento de Clientes</th>
                <th scope="col">Perfil Ancho de Banda</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in wifiSsids" :key="s.id">
                <td class="font-bold">{{ s.name }}</td>
                <td class="font-mono text-cyan">{{ s.ssid }}</td>
                <td>
                  <span class="badge badge-info">{{ s.security_type }}</span>
                </td>
                <td class="font-mono">{{ s.vlan_id ? `VLAN ${s.vlan_id}` : 'Nativa' }}</td>
                <td>{{ s.client_isolation ? 'Sí (Aislado)' : 'No' }}</td>
                <td class="font-mono text-subtle">{{ s.rate_limit_profile || 'Ilimitado' }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Clientes WiFi Conectados -->
        <h2 class="section-subtitle" style="margin-top: 1.5rem">
          Clientes WiFi en Tiempo Real (Fast Roaming 802.11r/k/v)
        </h2>
        <div class="tactical-table-wrapper">
          <table class="tactical-table" aria-label="Clientes WiFi">
            <thead>
              <tr>
                <th scope="col">MAC Address</th>
                <th scope="col">Hostname / Dispositivo</th>
                <th scope="col">AP Conectado</th>
                <th scope="col">SSID</th>
                <th scope="col">Señal RSSI (dBm)</th>
                <th scope="col">SNR</th>
                <th scope="col">Estándar Wi-Fi</th>
                <th scope="col">Fast Roaming</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in wifiClients" :key="c.mac_address">
                <td class="font-mono font-bold">{{ c.mac_address }}</td>
                <td>{{ c.hostname || 'Desconocido' }}</td>
                <td class="text-cyan">{{ c.ap_name }}</td>
                <td>{{ c.ssid }}</td>
                <td
                  class="font-mono"
                  :class="c.signal_rssi_dbm > -65 ? 'text-success' : 'text-warning'"
                >
                  {{ c.signal_rssi_dbm }} dBm
                </td>
                <td class="font-mono">{{ c.snr_db }} dB</td>
                <td>
                  <span class="badge badge-secondary">{{ c.wifi_standard }}</span>
                </td>
                <td>
                  <span
                    class="badge"
                    :class="c.fast_roaming_supported ? 'badge-success' : 'badge-subtle'"
                  >
                    {{ c.fast_roaming_supported ? '802.11r/k/v OK' : 'Legacy' }}
                  </span>
                </td>
              </tr>
              <tr v-if="wifiClients.length === 0">
                <td colspan="8" class="text-center text-subtle">
                  No hay clientes inalámbricos conectados en este momento.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
  .enterprise-compliance-view {
    padding: 1.5rem;
    background: #04070e;
    color: #e2e8f0;
    min-height: calc(100vh - 60px);
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    font-family:
      -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  }

  .view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
    background: #080f1d;
    border: 1px solid #1a2a40;
    padding: 1rem 1.25rem;
    border-radius: 8px;
  }

  .tactical-heading {
    margin: 0;
    font-size: 1.4rem;
    font-weight: 700;
    color: #00e5ff;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .tactical-subtitle {
    margin: 0.25rem 0 0 0;
    font-size: 0.85rem;
    color: #94a3b8;
  }

  .header-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .safemode-badge {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(0, 229, 255, 0.08);
    border: 1px solid #00e5ff;
    color: #00e5ff;
    padding: 0.35rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .indicator-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #00e5ff;
  }

  .pulse {
    box-shadow: 0 0 0 rgba(0, 229, 255, 0.4);
    animation: pulse-ring 1.8s infinite;
  }

  @keyframes pulse-ring {
    0% {
      box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.7);
    }
    70% {
      box-shadow: 0 0 0 8px rgba(0, 229, 255, 0);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(0, 229, 255, 0);
    }
  }

  .tactical-select,
  .tactical-input {
    background: #02050b;
    border: 1px solid #1a2a40;
    color: #e2e8f0;
    padding: 0.5rem 0.75rem;
    border-radius: 4px;
    font-size: 0.85rem;
    outline: none;
    transition: border-color 0.2s;
  }

  .tactical-select:focus,
  .tactical-input:focus {
    border-color: #00e5ff;
    box-shadow: 0 0 0 1px #00e5ff;
  }

  /* Navigation Tabs */
  .tactical-tabs-nav {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    background: #080f1d;
    padding: 0.4rem;
    border-radius: 6px;
    border: 1px solid #1a2a40;
  }

  .tab-btn {
    background: transparent;
    border: none;
    color: #94a3b8;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 0.4rem;
    transition: all 0.2s ease;
  }

  .tab-btn:hover {
    color: #e2e8f0;
    background: rgba(255, 255, 255, 0.05);
  }

  .tab-btn.active {
    background: #00e5ff;
    color: #04070e;
    font-weight: 700;
  }

  /* Banners */
  .alert-banner {
    padding: 0.75rem 1rem;
    border-radius: 6px;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .alert-error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fca5a5;
  }

  .alert-success {
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid #22c55e;
    color: #86efac;
  }

  /* Panel Action Bar */
  .panel-action-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .drift-summary-meta {
    display: flex;
    gap: 1.5rem;
    font-size: 0.85rem;
    flex-wrap: wrap;
  }

  .meta-item strong {
    color: #94a3b8;
    margin-right: 0.35rem;
  }

  /* Tactical Buttons */
  .tactical-btn {
    border: none;
    border-radius: 4px;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    transition:
      background 0.2s,
      opacity 0.2s;
  }

  .tactical-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary {
    background: #00e5ff;
    color: #04070e;
  }

  .btn-primary:hover:not(:disabled) {
    background: #33ebff;
  }

  .btn-secondary {
    background: #1a2a40;
    color: #e2e8f0;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #253b59;
  }

  .btn-danger {
    background: #ef4444;
    color: #ffffff;
  }

  .btn-danger:hover:not(:disabled) {
    background: #dc2626;
  }

  .btn-sm {
    padding: 0.3rem 0.6rem;
    font-size: 0.75rem;
  }

  /* Git Diff Viewer */
  .git-diff-viewer {
    background: #02050b;
    border: 1px solid #1a2a40;
    border-radius: 6px;
    overflow: hidden;
  }

  .diff-header {
    background: #080f1d;
    padding: 0.5rem 1rem;
    font-size: 0.75rem;
    color: #94a3b8;
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid #1a2a40;
  }

  .diff-pre {
    margin: 0;
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace, Consolas;
    font-size: 0.8rem;
    overflow-x: auto;
    line-height: 1.5;
  }

  .diff-line-add {
    color: #4ade80;
    background: rgba(34, 197, 94, 0.1);
    display: block;
  }

  .diff-line-del {
    color: #f87171;
    background: rgba(239, 68, 68, 0.1);
    display: block;
  }

  .diff-line-ctx {
    color: #94a3b8;
    display: block;
  }

  /* CIS Score Dashboard */
  .cis-score-dashboard {
    display: grid;
    grid-template-columns: 240px 1fr;
    gap: 1.25rem;
    margin-bottom: 1.5rem;
  }

  .score-card {
    background: #080f1d;
    border: 1px solid #1a2a40;
    border-radius: 8px;
    padding: 1.5rem;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .score-number {
    font-size: 2.5rem;
    font-weight: 800;
    color: #00e5ff;
  }

  .score-grade {
    font-size: 1.1rem;
    font-weight: 700;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    margin: 0.5rem 0;
  }

  .grade-A {
    background: rgba(34, 197, 94, 0.2);
    color: #4ade80;
    border: 1px solid #4ade80;
  }
  .grade-B {
    background: rgba(59, 130, 246, 0.2);
    color: #60a5fa;
    border: 1px solid #60a5fa;
  }
  .grade-C {
    background: rgba(234, 179, 8, 0.2);
    color: #facc15;
    border: 1px solid #facc15;
  }
  .grade-F {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
    border: 1px solid #f87171;
  }

  .score-desc {
    margin: 0;
    font-size: 0.75rem;
    color: #94a3b8;
  }

  .score-meta-card {
    background: #080f1d;
    border: 1px solid #1a2a40;
    border-radius: 8px;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    justify-content: space-around;
  }

  .metric-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.9rem;
  }

  /* Tactical Table */
  .tactical-table-wrapper {
    overflow-x: auto;
    border: 1px solid #1a2a40;
    border-radius: 6px;
    background: #080f1d;
  }

  .tactical-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    text-align: left;
  }

  .tactical-table th,
  .tactical-table td {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid #1a2a40;
  }

  .tactical-table th {
    background: #02050b;
    color: #94a3b8;
    font-weight: 600;
  }

  .tactical-table tr:hover td {
    background: rgba(255, 255, 255, 0.02);
  }

  /* Badges */
  .badge {
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    display: inline-block;
  }

  .badge-success {
    background: rgba(34, 197, 94, 0.2);
    color: #4ade80;
  }
  .badge-danger {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
  }
  .badge-warning {
    background: rgba(234, 179, 8, 0.2);
    color: #facc15;
  }
  .badge-info {
    background: rgba(0, 229, 255, 0.2);
    color: #00e5ff;
  }
  .badge-secondary {
    background: #1a2a40;
    color: #94a3b8;
  }

  .remediation-snippet {
    font-family: monospace;
    font-size: 0.75rem;
    background: #02050b;
    color: #38bdf8;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    border: 1px solid #1a2a40;
  }

  /* SD-WAN & Grid Layouts */
  .sdwan-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 1.25rem;
  }

  .sdwan-card,
  .bridge-card,
  .sla-form-card {
    background: #080f1d;
    border: 1px solid #1a2a40;
    border-radius: 8px;
    padding: 1.25rem;
  }

  .card-title {
    margin: 0 0 1rem 0;
    font-size: 1.05rem;
    color: #00e5ff;
    font-weight: 700;
  }

  .section-subtitle {
    margin: 0 0 0.75rem 0;
    font-size: 1rem;
    color: #e2e8f0;
    font-weight: 700;
  }

  .tactical-form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .form-group label {
    font-size: 0.75rem;
    color: #94a3b8;
    font-weight: 600;
  }

  .form-inline {
    flex-direction: row;
    align-items: flex-end;
    flex-wrap: wrap;
  }

  /* Switching Cards */
  .snooping-cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 1.25rem;
  }

  .bridge-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .bridge-name {
    margin: 0;
    font-size: 1.05rem;
    color: #00e5ff;
  }

  .ports-classification {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .ports-title {
    font-size: 0.8rem;
    font-weight: 600;
    display: block;
    margin-bottom: 0.25rem;
  }

  .tags-group {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
  }

  .port-tag {
    font-family: monospace;
    font-size: 0.75rem;
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
  }

  .tag-trusted {
    background: rgba(34, 197, 94, 0.15);
    border: 1px solid #22c55e;
    color: #86efac;
  }

  .tag-untrusted {
    background: rgba(234, 179, 8, 0.15);
    border: 1px solid #eab308;
    color: #fef08a;
  }

  /* Wi-Fi Stats Grid */
  .wifi-overview-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.25rem;
  }

  .wifi-stat-card {
    background: #080f1d;
    border: 1px solid #1a2a40;
    border-radius: 8px;
    padding: 1.25rem;
    text-align: center;
  }

  .stat-number {
    font-size: 2rem;
    font-weight: 800;
  }

  .stat-label {
    font-size: 0.75rem;
    color: #94a3b8;
    margin-top: 0.25rem;
  }

  /* Utilities */
  .font-mono {
    font-family: 'JetBrains Mono', monospace, Consolas;
  }
  .font-bold {
    font-weight: 700;
  }
  .text-cyan {
    color: #00e5ff;
  }
  .text-success {
    color: #4ade80;
  }
  .text-danger {
    color: #f87171;
  }
  .text-warning {
    color: #facc15;
  }
  .text-subtle {
    color: #64748b;
  }
  .text-center {
    text-align: center;
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

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem;
    gap: 1rem;
    color: #00e5ff;
  }

  .tactical-spinner {
    width: 36px;
    height: 36px;
    border: 3px solid rgba(0, 229, 255, 0.2);
    border-top-color: #00e5ff;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  @media (max-width: 768px) {
    .enterprise-compliance-view {
      padding: 0.75rem;
    }
    .view-header {
      flex-direction: column;
      align-items: flex-start;
    }
    .cis-score-dashboard {
      grid-template-columns: 1fr;
    }
    .form-row {
      grid-template-columns: 1fr;
    }
  }
</style>
