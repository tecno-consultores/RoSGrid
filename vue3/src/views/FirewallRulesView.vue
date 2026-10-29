<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import type { TableColumn, FirewallRuleItem } from '@/types';
  import RgDataTable from '@/components/common/RgDataTable.vue';
  import RgFirewallRuleModal from '@/components/webfig/RgFirewallRuleModal.vue';

  const route = useRoute();
  const routerId = computed(() => String(route.params.routerId || ''));
  const webFigStore = useWebFigStore();

  const activeTab = ref<'filter' | 'nat' | 'mangle' | 'raw' | 'address-list' | 'connections'>(
    'filter',
  );
  const chainFilter = ref<string>('all');
  const isLoading = ref(false);
  const rulesList = ref<FirewallRuleItem[]>([]);
  const isMoving = ref(false);
  const isResetting = ref(false);
  const actionMessage = ref('');
  const errorMessage = ref('');

  // Modales
  const isRuleModalOpen = ref(false);
  const isEditingRule = ref(false);
  const selectedRule = ref<FirewallRuleItem | null>(null);

  // Wizards NAT
  const isMasqueradeWizardOpen = ref(false);
  const masqueradeWan = ref('ether1');

  const isPortForwardWizardOpen = ref(false);
  const portForward = ref({
    in_interface: 'ether1',
    protocol: 'tcp',
    dst_port: 8080,
    to_addresses: '192.168.88.50',
    to_ports: 80,
    auto_filter: true,
  });

  const columns: TableColumn<FirewallRuleItem>[] = [
    { key: 'chain', label: 'Cadena', sortable: true },
    { key: 'action', label: 'Acción', sortable: true },
    { key: 'src_address', label: 'Src Address' },
    { key: 'dst_address', label: 'Dst Address' },
    { key: 'protocol', label: 'Proto' },
    { key: 'dst_port', label: 'Dst Port' },
    {
      key: 'traffic',
      label: 'Bytes / Paquetes',
      align: 'right',
      formatter: (row) => `${formatBytes(row.bytes)} (${row.packets} pkts)`,
    },
    { key: 'comment', label: 'Comentario' },
  ];

  function formatBytes(bytes: number): string {
    if (bytes >= 1000000000) return `${(bytes / 1000000000).toFixed(2)} GB`;
    if (bytes >= 1000000) return `${(bytes / 1000000).toFixed(1)} MB`;
    if (bytes >= 1000) return `${(bytes / 1000).toFixed(0)} KB`;
    return `${bytes} B`;
  }

  const computedColumns = computed(() => {
    if (activeTab.value === 'address-list') {
      return [
        { key: 'chain', label: 'Nombre Lista', sortable: true },
        { key: 'action', label: 'Dirección IP / Red', sortable: true },
        { key: 'comment', label: 'Comentario / Timeout' },
      ];
    }
    if (activeTab.value === 'connections') {
      return [
        { key: 'protocol', label: 'Protocolo', sortable: true },
        { key: 'src_address', label: 'Origen (Src)' },
        { key: 'dst_address', label: 'Destino (Dst)' },
        { key: 'chain', label: 'Estado TCP' },
        { key: 'comment', label: 'Timeout' },
      ];
    }
    return columns;
  });

  const filteredRules = computed(() => {
    if (activeTab.value === 'address-list' || activeTab.value === 'connections') {
      return rulesList.value;
    }
    return rulesList.value.filter((r) => {
      if (chainFilter.value === 'all') return true;
      return r.chain.toLowerCase() === chainFilter.value.toLowerCase();
    });
  });

  async function loadFirewallRules() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.get<FirewallRuleItem[] | { items: FirewallRuleItem[] }>(
        `/api/v1/routers/${routerId.value}/webfig/firewall/ip/${activeTab.value}`,
      );
      const raw = Array.isArray(res.data) ? res.data : res.data?.items || [];
      rulesList.value = raw.map((item: any) => ({
        ...item,
        id: item.id || item['.id'] || '',
        chain:
          item.chain ||
          (activeTab.value === 'address-list'
            ? item.list || ''
            : activeTab.value === 'connections'
              ? item['tcp-state'] || 'active'
              : 'forward'),
        action:
          item.action ||
          (activeTab.value === 'address-list'
            ? item.address || ''
            : activeTab.value === 'connections'
              ? item.protocol || ''
              : 'accept'),
        src_address: item.src_address || item['src-address'] || '',
        dst_address: item.dst_address || item['dst-address'] || '',
        protocol: item.protocol || '',
        dst_port: item.dst_port || item['dst-port'] || '',
        bytes: Number(item.bytes || 0),
        packets: Number(item.packets || 0),
        comment: item.comment || item.timeout || '',
        disabled: item.disabled === true || item.disabled === 'true',
        dynamic: item.dynamic === true || item.dynamic === 'true',
        invalid: item.invalid === true || item.invalid === 'true',
      }));
    } catch (e: any) {
      rulesList.value = [];
      errorMessage.value =
        e?.detail || e?.response?.data?.detail || e?.message || 'Error al cargar las reglas de firewall.';
    } finally {
      isLoading.value = false;
    }
  }

  function isInterceptedResponse(res: any): boolean {
    return (
      res?.status === 202 ||
      Boolean(res?.isMakerCheckerIntercepted) ||
      (res?.data as any)?.status === 'INTERCEPTED_FOR_APPROVAL'
    );
  }

  function openCreateRuleModal() {
    isEditingRule.value = false;
    selectedRule.value = null;
    isRuleModalOpen.value = true;
  }

  function openEditRuleModal(rule: FirewallRuleItem) {
    isEditingRule.value = true;
    selectedRule.value = rule;
    isRuleModalOpen.value = true;
  }

  function handleDuplicateRule(rule: FirewallRuleItem) {
    isEditingRule.value = false;
    selectedRule.value = { ...rule, id: '', comment: `${rule.comment || ''} (Copia)` };
    isRuleModalOpen.value = true;
  }

  async function handleSaveRule(payload: Record<string, any>) {
    errorMessage.value = '';
    actionMessage.value = '';

    try {
      let res;
      if (isEditingRule.value && selectedRule.value?.id) {
        res = await http.patch(
          `/api/v1/routers/${routerId.value}/webfig/firewall/ip/${activeTab.value}/${selectedRule.value.id}`,
          payload,
        );
        const intercepted = webFigStore.handleMutationResponse(res, 60);
        actionMessage.value = intercepted
          ? (res.data as any)?.detail || 'Solicitud en espera de aprobación humana en la bandeja Maker-Checker.'
          : 'Regla modificada exitosamente con Safe Mode activo.';
      } else {
        res = await http.post(
          `/api/v1/routers/${routerId.value}/webfig/firewall/ip/${activeTab.value}`,
          payload,
        );
        const intercepted = webFigStore.handleMutationResponse(res, 60);
        actionMessage.value = intercepted
          ? (res.data as any)?.detail || 'Solicitud en espera de aprobación humana en la bandeja Maker-Checker.'
          : 'Nueva regla creada exitosamente bajo Safe Mode.';
      }
      isRuleModalOpen.value = false;
      await loadFirewallRules();
    } catch (e: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value =
        e?.detail || e?.response?.data?.detail || e?.message || 'Error al persistir la regla de firewall.';
    }
  }

  async function handleToggleRule(rule: FirewallRuleItem) {
    try {
      const res = await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/firewall/ip/${activeTab.value}/${rule.id}`,
        { disabled: !rule.disabled },
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      if (intercepted) {
        actionMessage.value =
          (res.data as any)?.detail || 'Solicitud en espera de aprobación humana en la bandeja Maker-Checker.';
      }
      await loadFirewallRules();
    } catch (e: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value =
        e?.detail || e?.response?.data?.detail || e?.message || 'Error al conmutar estado de la regla.';
    }
  }

  async function handleDeleteRule(rule: FirewallRuleItem) {
    if (!confirm(`¿Eliminar la regla ${rule.id} [${rule.chain}] ${rule.action}?`)) {
      return;
    }
    try {
      const res = await http.delete(
        `/api/v1/routers/${routerId.value}/webfig/firewall/ip/${activeTab.value}/${rule.id}`,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      if (intercepted) {
        actionMessage.value =
          (res.data as any)?.detail || 'Solicitud en espera de aprobación humana en la bandeja Maker-Checker.';
      } else {
        actionMessage.value = 'Regla eliminada exitosamente.';
      }
      await loadFirewallRules();
    } catch (e: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value =
        e?.detail || e?.response?.data?.detail || e?.message || 'Error al eliminar la regla de firewall.';
    }
  }

  async function handleResetCounters() {
    if (!confirm(`¿Resetear a cero los contadores de paquetes y bytes de la tabla ${activeTab.value.toUpperCase()}?`)) {
      return;
    }
    isResetting.value = true;
    try {
      await http.post(
        `/api/v1/routers/${routerId.value}/webfig/firewall/ip/${activeTab.value}/reset-counters`,
      );
      actionMessage.value = 'Contadores de tráfico reiniciados a cero.';
      await loadFirewallRules();
    } catch (e: any) {
      errorMessage.value =
        e?.detail || e?.response?.data?.detail || e?.message || 'Error al reiniciar contadores.';
    } finally {
      isResetting.value = false;
    }
  }

  async function handleReorder(event: {
    fromIndex: number;
    toIndex: number;
    row: FirewallRuleItem;
  }) {
    isMoving.value = true;

    const moved = rulesList.value.splice(event.fromIndex, 1)[0];
    rulesList.value.splice(event.toIndex, 0, moved);

    try {
      const res = await http.post(
        `/api/v1/routers/${routerId.value}/webfig/firewall/ip/${activeTab.value}/move`,
        {
          numbers: event.row.id,
          destination: String(event.toIndex),
        },
      );
      webFigStore.handleMutationResponse(res, 60);
    } catch {
      webFigStore.stopSafeMode?.();
    } finally {
      isMoving.value = false;
    }
  }

  async function handleExecuteMasquerade() {
    errorMessage.value = '';
    try {
      const res = await http.post(
        `/api/v1/routers/${routerId.value}/webfig/firewall/ip/nat`,
        {
          chain: 'srcnat',
          out_interface: masqueradeWan.value,
          action: 'masquerade',
          comment: 'NAT Masquerade RoSGrid Wizard',
        },
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      if (intercepted) {
        actionMessage.value =
          (res.data as any)?.detail || 'Solicitud Masquerade en espera de aprobación humana en Maker-Checker.';
      } else {
        actionMessage.value = `Regla Masquerade creada para salida WAN en ${masqueradeWan.value}.`;
      }
      isMasqueradeWizardOpen.value = false;
      await loadFirewallRules();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value =
        err?.detail || err?.response?.data?.detail || err?.message || 'Error al crear regla Masquerade.';
    }
  }

  async function handleExecutePortForward() {
    errorMessage.value = '';
    try {
      // 1. Regla Dst-NAT
      const resNat = await http.post(
        `/api/v1/routers/${routerId.value}/webfig/firewall/ip/nat`,
        {
          chain: 'dstnat',
          in_interface: portForward.value.in_interface,
          protocol: portForward.value.protocol,
          dst_port: String(portForward.value.dst_port),
          action: 'dst-nat',
          to_addresses: portForward.value.to_addresses,
          to_ports: String(portForward.value.to_ports),
          comment: `Port Forward :${portForward.value.dst_port} -> ${portForward.value.to_addresses}:${portForward.value.to_ports}`,
        },
      );

      // 2. Regla opcional en Filter forward
      let resFilter: any = null;
      if (portForward.value.auto_filter) {
        resFilter = await http.post(
          `/api/v1/routers/${routerId.value}/webfig/firewall/ip/filter`,
          {
            chain: 'forward',
            dst_address: portForward.value.to_addresses,
            protocol: portForward.value.protocol,
            dst_port: String(portForward.value.to_ports),
            action: 'accept',
            comment: `Permitir Port Forward a ${portForward.value.to_addresses}:${portForward.value.to_ports}`,
          },
        );
      }

      if (isInterceptedResponse(resNat) || isInterceptedResponse(resFilter)) {
        webFigStore.notifyMakerCheckerPending(
          (resNat.data as any)?.detail ||
            'Solicitud de Port Forwarding en espera de aprobación humana en Maker-Checker.',
        );
        actionMessage.value =
          (resNat.data as any)?.detail ||
          'Solicitud de Port Forwarding en espera de aprobación humana en Maker-Checker.';
      } else {
        webFigStore.startSafeModeCountdown(60);
        actionMessage.value = `Redirección de puertos :${portForward.value.dst_port} -> ${portForward.value.to_addresses}:${portForward.value.to_ports} completada con éxito.`;
      }
      isPortForwardWizardOpen.value = false;
      await loadFirewallRules();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value =
        err?.detail ||
        err?.response?.data?.detail ||
        err?.message ||
        'Error al ejecutar asistente de Port Forwarding.';
    }
  }

  onMounted(() => {
    loadFirewallRules();
  });
</script>

<template>
  <div class="firewall-view">
    <!-- Alertas informativas / de error -->
    <div v-if="actionMessage" class="feedback-banner feedback-banner--success" role="status">
      <span>✅ {{ actionMessage }}</span>
      <button type="button" class="btn-dismiss" @click="actionMessage = ''">✕</button>
    </div>
    <div v-if="errorMessage" class="feedback-banner feedback-banner--error" role="alert">
      <span>⚠️ {{ errorMessage }}</span>
      <button type="button" class="btn-dismiss" @click="errorMessage = ''">✕</button>
    </div>

    <header class="view-header">
      <div>
        <h2 class="view-title">Firewall RouterOS v7 & Filtrado de Paquetes</h2>
        <p class="view-subtitle">
          Reglas ordenadas con protección Safe Mode (60s Rollback) y barras de tráfico en vivo
        </p>
      </div>

      <div class="header-actions">
        <button
          v-if="activeTab === 'nat'"
          type="button"
          class="btn-wizard-action"
          @click="isMasqueradeWizardOpen = true"
        >
          🧙‍♂️ Masquerade
        </button>
        <button
          v-if="activeTab === 'nat'"
          type="button"
          class="btn-wizard-action"
          @click="isPortForwardWizardOpen = true"
        >
          🧙‍♂️ Port Forwarding
        </button>
        <button
          v-if="activeTab === 'filter' || activeTab === 'nat' || activeTab === 'mangle' || activeTab === 'raw'"
          type="button"
          class="btn-primary-action"
          @click="openCreateRuleModal"
        >
          + Nueva Regla
        </button>
        <button
          type="button"
          class="btn-secondary-action"
          :disabled="isResetting"
          @click="handleResetCounters"
        >
          🔄 Reset Contadores
        </button>
      </div>

      <!-- Pestañas de Tablas de Firewall -->
      <nav class="subtabs-bar" role="tablist" aria-label="Tablas de Firewall">
        <button
          v-for="tab in [
            { id: 'filter', label: 'Filter Rules' },
            { id: 'nat', label: 'NAT' },
            { id: 'mangle', label: 'Mangle' },
            { id: 'raw', label: 'RAW' },
            { id: 'address-list', label: 'Address Lists' },
            { id: 'connections', label: 'Connections' },
          ]"
          :key="tab.id"
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === tab.id }"
          role="tab"
          :aria-selected="activeTab === tab.id"
          @click="
            activeTab = tab.id as any;
            loadFirewallRules();
          "
        >
          {{ tab.label }}
        </button>
      </nav>
    </header>

    <!-- Filtro rápido por Cadena (Chain) -->
    <div v-if="activeTab !== 'address-list' && activeTab !== 'connections'" class="filter-toolbar">
      <div class="filter-item">
        <label for="filter-chain-select" class="filter-label">Filtrar por Cadena:</label>
        <select id="filter-chain-select" v-model="chainFilter" class="filter-select font-tabular">
          <option value="all">Todas las Cadenas (All)</option>
          <option value="input">input</option>
          <option value="forward">forward</option>
          <option value="output">output</option>
          <option value="prerouting">prerouting</option>
          <option value="postrouting">postrouting</option>
          <option value="srcnat">srcnat</option>
          <option value="dstnat">dstnat</option>
        </select>
      </div>

      <div class="reorder-info">
        <span class="info-icon">💡</span>
        <span
          >Arrastra filas o usa <strong>Alt + ↑ / Alt + ↓</strong> para reordenar con Safe
          Mode.</span
        >
      </div>
    </div>

    <!-- Tabla de Reglas con Barras de Tráfico Proporcionales -->
    <div class="table-card">
      <RgDataTable
        :columns="computedColumns as any"
        :rows="filteredRules"
        :sortable-rows="activeTab !== 'address-list' && activeTab !== 'connections'"
        caption="Reglas de Firewall RouterOS"
        row-key="id"
        @reorder="handleReorder"
      >
        <template #actions="{ row }">
          <div class="row-actions-group">
            <button
              type="button"
              class="btn-table-action"
              title="Editar regla"
              aria-label="Editar regla"
              @click="openEditRuleModal(row as FirewallRuleItem)"
            >
              ✏
            </button>
            <button
              type="button"
              class="btn-table-action"
              :title="(row as FirewallRuleItem).disabled ? 'Habilitar regla' : 'Deshabilitar regla'"
              :aria-label="(row as FirewallRuleItem).disabled ? 'Habilitar regla' : 'Deshabilitar regla'"
              @click="handleToggleRule(row as FirewallRuleItem)"
            >
              {{ (row as FirewallRuleItem).disabled ? '▶' : '⏸' }}
            </button>
            <button
              type="button"
              class="btn-table-action"
              title="Duplicar regla"
              aria-label="Duplicar regla"
              @click="handleDuplicateRule(row as FirewallRuleItem)"
            >
              📋
            </button>
            <button
              type="button"
              class="btn-table-action btn-table-action--danger"
              title="Eliminar regla"
              aria-label="Eliminar regla"
              @click="handleDeleteRule(row as FirewallRuleItem)"
            >
              🗑
            </button>
          </div>
        </template>
      </RgDataTable>
    </div>

    <!-- Modal Táctico de Creación/Edición -->
    <RgFirewallRuleModal
      v-if="activeTab === 'filter' || activeTab === 'nat' || activeTab === 'mangle' || activeTab === 'raw'"
      :is-open="isRuleModalOpen"
      :is-editing="isEditingRule"
      :table-type="activeTab"
      :initial-rule="selectedRule"
      :existing-rules="rulesList"
      @close="isRuleModalOpen = false"
      @save="handleSaveRule"
    />

    <!-- Wizard Masquerade -->
    <div v-if="isMasqueradeWizardOpen" class="modal-backdrop">
      <div class="modal-window">
        <h3 class="modal-title">🧙‍♂️ Asistente de Salida a Internet (Masquerade)</h3>
        <p class="modal-desc text-muted">
          Crea la regla de enmascaramiento NAT necesaria para que los equipos de la LAN salgan a Internet.
        </p>
        <form @submit.prevent="handleExecuteMasquerade">
          <div class="form-group">
            <label for="masq-wan">Interfaz WAN de Salida (Out-Interface)</label>
            <input id="masq-wan" v-model="masqueradeWan" type="text" class="form-input" placeholder="ether1" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary-action" @click="isMasqueradeWizardOpen = false">Cancelar</button>
            <button type="submit" class="btn-primary-action">Crear Regla Masquerade</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Wizard Port Forwarding -->
    <div v-if="isPortForwardWizardOpen" class="modal-backdrop">
      <div class="modal-window">
        <h3 class="modal-title">🧙‍♂️ Asistente de Apertura de Puertos (Port Forwarding)</h3>
        <p class="modal-desc text-muted">
          Publica servidores locales hacia Internet mapeando puertos externos hacia la IP interna con Safe Mode.
        </p>
        <form @submit.prevent="handleExecutePortForward">
          <div class="form-group">
            <label for="pf-wan">Interfaz WAN de Entrada (In-Interface)</label>
            <input id="pf-wan" v-model="portForward.in_interface" type="text" class="form-input" placeholder="ether1" required />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="pf-proto">Protocolo</label>
              <select id="pf-proto" v-model="portForward.protocol" class="form-input">
                <option value="tcp">TCP</option>
                <option value="udp">UDP</option>
              </select>
            </div>
            <div class="form-group">
              <label for="pf-ext-port">Puerto Externo</label>
              <input id="pf-ext-port" v-model="portForward.dst_port" type="number" class="form-input font-mono" min="1" max="65535" required />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="pf-int-ip">IP Interna del Servidor</label>
              <input id="pf-int-ip" v-model="portForward.to_addresses" type="text" class="form-input font-mono" placeholder="192.168.88.50" required />
            </div>
            <div class="form-group">
              <label for="pf-int-port">Puerto Interno</label>
              <input id="pf-int-port" v-model="portForward.to_ports" type="number" class="form-input font-mono" min="1" max="65535" required />
            </div>
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="portForward.auto_filter" type="checkbox" />
              Crear automáticamente regla de permiso en Filter Forward
            </label>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary-action" @click="isPortForwardWizardOpen = false">Cancelar</button>
            <button type="submit" class="btn-primary-action">Crear Port Forwarding</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .firewall-view {
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
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--rg-text-primary);
  }

  .view-subtitle {
    margin: 2px 0 0 0;
    font-size: 0.8rem;
    color: var(--rg-text-muted);
  }

  .header-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .btn-primary-action {
    padding: 7px 14px;
    background: rgba(34, 211, 238, 0.14);
    border: 1px solid var(--rg-accent-cyan, #22d3ee);
    border-radius: var(--rg-radius-md, 6px);
    color: var(--rg-accent-cyan, #22d3ee);
    font-size: var(--rg-text-sm, 0.8125rem);
    font-weight: 600;
    cursor: pointer;
    box-shadow: var(--rg-inset-highlight);
    transition: all 0.15s ease;
  }

  .btn-primary-action:hover {
    background: rgba(34, 211, 238, 0.25);
    border-color: var(--rg-cyan-300, #38bdf8);
    color: #ffffff;
    box-shadow: var(--rg-cyan-glow);
  }

  .btn-secondary-action {
    padding: 7px 12px;
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-panel, #334155);
    border-radius: var(--rg-radius-md, 6px);
    color: var(--rg-text-secondary, #cbd5e1);
    font-size: var(--rg-text-sm, 0.8125rem);
    font-weight: 600;
    cursor: pointer;
    box-shadow: var(--rg-inset-highlight);
    transition: all 0.15s ease;
  }

  .btn-secondary-action:hover:not(:disabled) {
    background: var(--rg-bg-elevated, #1e293b);
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-text-primary, #f8fafc);
  }

  /* Refactoring UI: Segmented Control con Radios Concéntricos (8px ext - 3px pad = 5px int) */
  .subtabs-bar {
    display: flex;
    gap: 4px;
    background: var(--rg-bg-canvas);
    padding: 3px;
    border: 1px solid var(--rg-border-grid);
    border-radius: var(--rg-radius-lg, 8px);
    box-shadow: var(--rg-inset-well);
    overflow-x: auto;
  }

  .btn-subtab {
    background: transparent;
    border: none;
    color: var(--rg-text-secondary);
    padding: 5px 12px;
    font-size: var(--rg-text-xs, 0.75rem);
    border-radius: var(--rg-radius-concentric, 5px);
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s ease;
  }

  .btn-subtab--active {
    background: var(--rg-bg-elevated);
    color: var(--rg-accent-cyan);
    font-weight: 600;
    box-shadow: var(--rg-inset-highlight), var(--rg-shadow-sm);
  }

  .feedback-banner {
    padding: 10px 14px;
    border-radius: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.85rem;
  }

  .feedback-banner--success {
    background-color: rgba(34, 197, 94, 0.15);
    border: 1px solid #22c55e;
    color: #86efac;
  }

  .feedback-banner--error {
    background-color: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fca5a5;
  }

  .btn-dismiss {
    background: transparent;
    border: none;
    color: inherit;
    font-size: 1rem;
    cursor: pointer;
    padding: 0 4px;
  }

  .filter-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    padding: 10px 14px;
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
  }

  .filter-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .filter-label {
    font-size: 0.8rem;
    color: var(--rg-text-muted);
  }

  .filter-select {
    padding: 4px 8px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 4px;
    color: var(--rg-text-primary);
    font-size: 0.8rem;
  }

  .reorder-info {
    font-size: 0.78rem;
    color: var(--rg-text-muted);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .row-actions-group {
    display: inline-flex;
    gap: 4px;
    align-items: center;
  }

  .btn-table-action {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 4px;
    color: var(--rg-text-secondary, #94a3b8);
    font-size: 0.8rem;
    padding: 2px 6px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-table-action:hover {
    border-color: var(--rg-accent-cyan, #00d2ff);
    color: var(--rg-accent-cyan, #00d2ff);
    background: rgba(0, 210, 255, 0.1);
  }

  .btn-table-action--danger:hover {
    border-color: #ef4444;
    color: #ef4444;
    background: rgba(239, 68, 68, 0.15);
  }

  .font-tabular {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  .btn-wizard-action {
    padding: 7px 12px;
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-panel, #334155);
    border-radius: var(--rg-radius-md, 6px);
    color: var(--rg-text-secondary, #cbd5e1);
    font-size: var(--rg-text-sm, 0.8125rem);
    font-weight: 600;
    cursor: pointer;
    box-shadow: var(--rg-inset-highlight);
    transition: all 0.15s ease;
  }

  .btn-wizard-action:hover,
  .btn-wizard-action:focus-visible {
    background: rgba(56, 189, 248, 0.15);
    border-color: var(--rg-status-info, #38bdf8);
    color: var(--rg-status-info-text, #bae6fd);
  }

  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal-window {
    background: #1e293b;
    border: 1px solid #38bdf8;
    border-radius: 8px;
    padding: 1.5rem;
    width: 90%;
    max-width: 480px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  }

  .modal-title {
    margin-top: 0;
    font-size: 1.15rem;
    color: #38bdf8;
  }

  .modal-desc {
    font-size: 0.8rem;
    margin-bottom: 1rem;
    color: #94a3b8;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    margin-bottom: 0.9rem;
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }

  .form-group label {
    font-size: 0.8rem;
    color: #94a3b8;
  }

  .form-input {
    background: #0f172a;
    border: 1px solid #334155;
    color: #f8fafc;
    padding: 0.5rem;
    border-radius: 4px;
    font-size: 0.85rem;
  }

  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-top: 1.25rem;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.82rem;
    color: #f8fafc;
    cursor: pointer;
  }

  .font-mono {
    font-family: monospace;
  }

  @media (max-width: 640px) {
    .form-row {
      grid-template-columns: 1fr;
    }

    .modal-actions {
      flex-wrap: wrap;
    }
  }
</style>
