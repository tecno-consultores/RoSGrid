<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useWebFigStore } from '@/stores/useWebFigStore';
  import type { TableColumn, BgpSessionItem } from '@/types';
  import RgDataTable from '@/components/common/RgDataTable.vue';

  interface OspfNeighborItem extends Record<string, unknown> {
    id: string;
    instance: string;
    router_id: string;
    address: string;
    interface: string;
    state: string;
    priority: number;
  }

  interface StaticRouteItem extends Record<string, unknown> {
    id: string;
    dst_address: string;
    gateway: string;
    distance: number;
    routing_table: string;
    check_gateway?: string;
    comment?: string;
    disabled?: boolean;
    active?: boolean;
    dynamic?: boolean;
  }

  const route = useRoute();
  const webFigStore = useWebFigStore();
  const routerId = computed(() => String(route.params.routerId || ''));

  type RoutingTab = 'bgp' | 'ospf' | 'routes' | 'policy-routing';
  const activeTab = ref<RoutingTab>('bgp');
  const isLoading = ref(false);
  const actionMessage = ref('');
  const errorMessage = ref('');

  // Colecciones
  const bgpSessions = ref<BgpSessionItem[]>([]);
  const ospfNeighbors = ref<OspfNeighborItem[]>([]);
  const staticRoutes = ref<StaticRouteItem[]>([]);
  const routingTables = ref<any[]>([]);
  const routingRules = ref<any[]>([]);

  // Modales
  const isRouteModalOpen = ref(false);
  const newRoute = ref({
    dst_address: '0.0.0.0/0',
    gateway: '',
    distance: 1,
    routing_table: 'main',
    check_gateway: 'none',
    comment: '',
    disabled: false,
  });
  const isEditRouteModalOpen = ref(false);
  const editingRouteId = ref('');
  const editRouteForm = ref({
    dst_address: '',
    gateway: '',
    distance: 1,
    routing_table: 'main',
    check_gateway: 'none',
    comment: '',
    disabled: false,
  });

  const isBgpModalOpen = ref(false);
  const newBgp = ref({
    name: 'peer-isp',
    remote_address: '',
    remote_as: 65001,
    local_as: 65000,
    templates: 'default',
    connect: true,
    listen: true,
  });
  const isEditBgpModalOpen = ref(false);
  const editingBgpId = ref('');
  const editBgpForm = ref({
    name: '',
    remote_address: '',
    remote_as: 65001,
    disabled: false,
  });

  const isTableModalOpen = ref(false);
  const newTable = ref({ name: 'to_wan2', fib: true });
  const isEditTableModalOpen = ref(false);
  const editingTableId = ref('');
  const editTableForm = ref({ name: '', fib: true, comment: '' });

  const isRuleModalOpen = ref(false);
  const newRule = ref({
    src_address: '192.168.88.100/32',
    action: 'lookup-only-in-table',
    table: 'to_wan2',
  });
  const isEditRuleModalOpen = ref(false);
  const editingRuleId = ref('');
  const editRuleForm = ref({
    src_address: '',
    dst_address: '',
    action: 'lookup-only-in-table',
    table: 'to_wan2',
    comment: '',
  });

  const bgpColumns: TableColumn<BgpSessionItem>[] = [
    { key: 'name', label: 'Sesión BGP', sortable: true },
    { key: 'remote_address', label: 'Remote IP' },
    { key: 'remote_as', label: 'Remote AS', align: 'center' },
    {
      key: 'state',
      label: 'Estado',
      formatter: (row) => row.state ? row.state.toUpperCase() : 'UNKNOWN',
    },
    { key: 'prefixes_received', label: 'Prefijos RX', align: 'right' },
    { key: 'uptime', label: 'Uptime', align: 'right' },
    { key: 'actions', label: 'Acciones', align: 'center' },
  ];

  const ospfColumns: TableColumn<OspfNeighborItem>[] = [
    { key: 'instance', label: 'Instancia' },
    { key: 'router_id', label: 'Router ID' },
    { key: 'address', label: 'Dirección IP' },
    { key: 'interface', label: 'Interfaz' },
    { key: 'state', label: 'Estado', align: 'center' },
    { key: 'priority', label: 'Prioridad', align: 'center' },
  ];

  async function loadRoutingData() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      if (activeTab.value === 'bgp') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/routing/bgp/sessions`);
        const data: any = res.data;
        bgpSessions.value = Array.isArray(data) ? data : data?.sessions || data?.peers || data?.items || [];
      } else if (activeTab.value === 'ospf') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/routing/ospf/neighbors`);
        ospfNeighbors.value = Array.isArray(res.data) ? res.data : res.data?.items || [];
      } else if (activeTab.value === 'routes') {
        const res = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/ip/routes`);
        const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
        staticRoutes.value = items.map((r: any) => ({
          ...r,
          id: r.id || r['.id'],
          dst_address: r.dst_address || r['dst-address'] || '0.0.0.0/0',
          gateway: r.gateway || '',
          distance: Number(r.distance || 1),
          routing_table: r.routing_table || r['routing-table'] || 'main',
          check_gateway: r.check_gateway || r['check-gateway'] || 'none',
          disabled: r.disabled === 'true' || r.disabled === true,
          active: r.active === 'true' || r.active === true,
          dynamic: r.dynamic === 'true' || r.dynamic === true,
        }));
      } else if (activeTab.value === 'policy-routing') {
        const resT = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/routing/tables`);
        routingTables.value = Array.isArray(resT.data) ? resT.data : resT.data?.items || [];
        const resR = await http.get<any>(`/api/v1/routers/${routerId.value}/webfig/routing/rules`);
        routingRules.value = Array.isArray(resR.data) ? resR.data : resR.data?.items || [];
      }
    } catch (err: any) {
      errorMessage.value = err?.detail || err?.message || 'Error al cargar datos de enrutamiento.';
    } finally {
      isLoading.value = false;
    }
  }

  // --- Operaciones de Rutas Estáticas ---
  async function handleCreateRoute() {
    try {
      const res = await http.post(`/api/v1/routers/${routerId.value}/webfig/ip/routes`, {
        dst_address: newRoute.value.dst_address,
        gateway: newRoute.value.gateway,
        distance: Number(newRoute.value.distance),
        routing_table: newRoute.value.routing_table,
        check_gateway: newRoute.value.check_gateway !== 'none' ? newRoute.value.check_gateway : undefined,
        comment: newRoute.value.comment || undefined,
        disabled: newRoute.value.disabled,
      });
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      actionMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud en espera de aprobación humana en Maker-Checker.'
        : `Ruta hacia ${newRoute.value.dst_address} creada con éxito.`;
      isRouteModalOpen.value = false;
      loadRoutingData();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value = err?.detail || err?.message || 'Error al crear ruta estática.';
    }
  }

  async function handleToggleRoute(r: StaticRouteItem) {
    try {
      const res = await http.patch(`/api/v1/routers/${routerId.value}/webfig/ip/routes/${r.id}`, {
        disabled: !r.disabled,
      });
      webFigStore.handleMutationResponse(res, 60);
      loadRoutingData();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value = err?.detail || 'Error al conmutar ruta.';
    }
  }

  async function handleDeleteRoute(r: StaticRouteItem) {
    if (!confirm(`¿Eliminar la ruta hacia ${r.dst_address}?`)) return;
    try {
      const res = await http.delete(`/api/v1/routers/${routerId.value}/webfig/ip/routes/${r.id}`);
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      actionMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud en espera de aprobación humana en Maker-Checker.'
        : `Ruta hacia ${r.dst_address} eliminada.`;
      loadRoutingData();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value = err?.detail || 'Error al eliminar ruta.';
    }
  }

  function openEditRouteModal(r: StaticRouteItem) {
    editingRouteId.value = r.id;
    editRouteForm.value = {
      dst_address: r.dst_address,
      gateway: r.gateway,
      distance: Number(r.distance || 1),
      routing_table: r.routing_table || 'main',
      check_gateway: r.check_gateway || 'none',
      comment: String(r.comment || ''),
      disabled: Boolean(r.disabled),
    };
    isEditRouteModalOpen.value = true;
  }

  async function handleUpdateRoute() {
    if (!editingRouteId.value) return;
    try {
      const res = await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/ip/routes/${encodeURIComponent(editingRouteId.value)}`,
        {
          gateway: editRouteForm.value.gateway,
          distance: Number(editRouteForm.value.distance),
          routing_table: editRouteForm.value.routing_table,
          check_gateway: editRouteForm.value.check_gateway !== 'none' ? editRouteForm.value.check_gateway : undefined,
          comment: editRouteForm.value.comment,
          disabled: editRouteForm.value.disabled,
        },
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      actionMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud en espera de aprobación humana en Maker-Checker.'
        : `Ruta hacia ${editRouteForm.value.dst_address} actualizada.`;
      isEditRouteModalOpen.value = false;
      loadRoutingData();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value = err?.detail || 'Error al actualizar ruta.';
    }
  }

  function openEditBgpModal(peer: any) {
    editingBgpId.value = String(peer.id || peer['.id'] || '');
    editBgpForm.value = {
      name: String(peer.name || ''),
      remote_address: String(peer.remote_address || peer['remote.address'] || ''),
      remote_as: Number(peer.remote_as || peer['remote.as'] || 65001),
      disabled: Boolean(peer.disabled),
    };
    isEditBgpModalOpen.value = true;
  }

  async function handleUpdateBgpConnection() {
    if (!editingBgpId.value) return;
    try {
      const res = await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/routing/bgp/connections/${encodeURIComponent(editingBgpId.value)}`,
        {
          remote_address: editBgpForm.value.remote_address,
          remote_as: Number(editBgpForm.value.remote_as),
          disabled: editBgpForm.value.disabled,
        },
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      actionMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud BGP en espera de aprobación humana en Maker-Checker.'
        : `Conexión BGP "${editBgpForm.value.name}" actualizada.`;
      isEditBgpModalOpen.value = false;
      loadRoutingData();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value = err?.detail || 'Error al actualizar conexión BGP.';
    }
  }

  async function handleDeleteBgpConnection(peer: any) {
    if (!confirm(`¿Eliminar la conexión BGP "${peer.name}"?`)) return;
    try {
      const res = await http.delete(
        `/api/v1/routers/${routerId.value}/webfig/routing/bgp/connections/${encodeURIComponent(peer.id || peer['.id'])}`,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      actionMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud BGP en espera de aprobación humana en Maker-Checker.'
        : `Conexión BGP "${peer.name}" eliminada.`;
      loadRoutingData();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value = err?.detail || 'Error al eliminar conexión BGP.';
    }
  }

  function openEditTableModal(tbl: any) {
    editingTableId.value = String(tbl.id || tbl['.id'] || '');
    editTableForm.value = {
      name: String(tbl.name || ''),
      fib: tbl.fib === 'true' || tbl.fib === true,
      comment: String(tbl.comment || ''),
    };
    isEditTableModalOpen.value = true;
  }

  async function handleUpdateTable() {
    if (!editingTableId.value) return;
    try {
      const res = await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/routing/tables/${encodeURIComponent(editingTableId.value)}`,
        editTableForm.value,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      actionMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud FIB en espera de aprobación humana en Maker-Checker.'
        : `Tabla FIB "${editTableForm.value.name}" actualizada.`;
      isEditTableModalOpen.value = false;
      loadRoutingData();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value = err?.detail || 'Error al actualizar tabla FIB.';
    }
  }

  async function handleDeleteTable(tbl: any) {
    if (!confirm(`¿Eliminar la tabla FIB "${tbl.name}"?`)) return;
    try {
      const res = await http.delete(
        `/api/v1/routers/${routerId.value}/webfig/routing/tables/${encodeURIComponent(tbl.id || tbl['.id'])}`,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      actionMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud FIB en espera de aprobación humana en Maker-Checker.'
        : `Tabla FIB "${tbl.name}" eliminada.`;
      loadRoutingData();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value = err?.detail || 'Error al eliminar tabla FIB.';
    }
  }

  function openEditRuleModal(rule: any) {
    editingRuleId.value = String(rule.id || rule['.id'] || '');
    editRuleForm.value = {
      src_address: String(rule['src-address'] || rule.src_address || ''),
      dst_address: String(rule['dst-address'] || rule.dst_address || ''),
      action: String(rule.action || 'lookup-only-in-table'),
      table: String(rule.table || 'main'),
      comment: String(rule.comment || ''),
    };
    isEditRuleModalOpen.value = true;
  }

  async function handleUpdateRule() {
    if (!editingRuleId.value) return;
    try {
      const res = await http.patch(
        `/api/v1/routers/${routerId.value}/webfig/routing/rules/${encodeURIComponent(editingRuleId.value)}`,
        editRuleForm.value,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      actionMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud PBR en espera de aprobación humana en Maker-Checker.'
        : `Regla PBR actualizada.`;
      isEditRuleModalOpen.value = false;
      loadRoutingData();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value = err?.detail || 'Error al actualizar regla PBR.';
    }
  }

  async function handleDeleteRule(rule: any) {
    if (!confirm(`¿Eliminar la regla PBR hacia tabla "${rule.table}"?`)) return;
    try {
      const res = await http.delete(
        `/api/v1/routers/${routerId.value}/webfig/routing/rules/${encodeURIComponent(rule.id || rule['.id'])}`,
      );
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      actionMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud PBR en espera de aprobación humana en Maker-Checker.'
        : `Regla PBR eliminada.`;
      loadRoutingData();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value = err?.detail || 'Error al eliminar regla PBR.';
    }
  }

  // --- Operaciones BGP Connections ---
  async function handleCreateBgpConnection() {
    try {
      const res = await http.post(`/api/v1/routers/${routerId.value}/webfig/routing/bgp/connections`, {
        name: newBgp.value.name,
        remote_address: newBgp.value.remote_address,
        remote_as: Number(newBgp.value.remote_as),
        local_as: Number(newBgp.value.local_as),
        templates: newBgp.value.templates,
        connect: newBgp.value.connect,
        listen: newBgp.value.listen,
      });
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      actionMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud de conexión BGP en espera de aprobación humana en Maker-Checker.'
        : `Conexión BGP "${newBgp.value.name}" configurada.`;
      isBgpModalOpen.value = false;
      loadRoutingData();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value = err?.detail || 'Error al crear conexión BGP.';
    }
  }

  // --- Operaciones Policy Routing ---
  async function handleCreateTable() {
    try {
      const res = await http.post(`/api/v1/routers/${routerId.value}/webfig/routing/tables`, newTable.value);
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      actionMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud de tabla FIB en espera de aprobación humana en Maker-Checker.'
        : `Tabla de enrutamiento FIB "${newTable.value.name}" creada.`;
      isTableModalOpen.value = false;
      loadRoutingData();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value = err?.detail || 'Error al crear tabla FIB.';
    }
  }

  async function handleCreateRule() {
    try {
      const res = await http.post(`/api/v1/routers/${routerId.value}/webfig/routing/rules`, newRule.value);
      const intercepted = webFigStore.handleMutationResponse(res, 60);
      actionMessage.value = intercepted
        ? (res.data as any)?.detail || 'Solicitud de regla PBR en espera de aprobación humana en Maker-Checker.'
        : `Regla de enrutamiento PBR creada.`;
      isRuleModalOpen.value = false;
      loadRoutingData();
    } catch (err: any) {
      webFigStore.stopSafeMode?.();
      errorMessage.value = err?.detail || 'Error al crear regla PBR.';
    }
  }

  onMounted(() => {
    loadRoutingData();
  });
</script>

<template>
  <div class="routing-view">
    <header class="view-header">
      <div>
        <h2 class="view-title">🌐 Routing v7 — Protocolos BGP, OSPF, Rutas y PBR</h2>
        <p class="view-subtitle">
          Supervisión de sesiones de tránsito BGP, adyacencias OSPF, rutas estáticas Dual-Stack y balanceo Multi-WAN
        </p>
      </div>

      <div class="header-actions">
        <button
          v-if="activeTab === 'routes'"
          type="button"
          class="btn-tactical btn-cyan"
          @click="isRouteModalOpen = true"
        >
          + Nueva Ruta Estática
        </button>

        <button
          v-else-if="activeTab === 'bgp'"
          type="button"
          class="btn-tactical btn-cyan"
          @click="isBgpModalOpen = true"
        >
          + Nueva Conexión BGP
        </button>

        <button
          v-else-if="activeTab === 'policy-routing'"
          type="button"
          class="btn-tactical btn-cyan"
          @click="isTableModalOpen = true"
        >
          + Crear Tabla FIB
        </button>

        <button
          v-if="activeTab === 'policy-routing'"
          type="button"
          class="btn-tactical btn-outline"
          @click="isRuleModalOpen = true"
        >
          + Crear Regla PBR
        </button>

        <button
          type="button"
          class="btn-tactical btn-outline"
          :disabled="isLoading"
          @click="loadRoutingData"
        >
          🔄 Actualizar
        </button>
      </div>

      <!-- Pestañas de Routing -->
      <nav class="subtabs-bar" role="tablist" aria-label="Módulos de Routing v7">
        <button
          v-for="tab in [
            { id: 'bgp', label: 'BGP v7 Sessions' },
            { id: 'ospf', label: 'OSPF Neighbors' },
            { id: 'routes', label: 'Rutas Estáticas' },
            { id: 'policy-routing', label: 'Policy Routing (PBR)' },
          ]"
          :key="tab.id"
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === tab.id }"
          role="tab"
          :aria-selected="activeTab === tab.id"
          @click="
            activeTab = tab.id as any;
            loadRoutingData();
          "
        >
          {{ tab.label }}
        </button>
      </nav>
    </header>

    <!-- Alertas -->
    <div v-if="actionMessage" class="alert-box alert-success" role="status">
      <span>✔ {{ actionMessage }}</span>
    </div>
    <div v-if="errorMessage" class="alert-box alert-danger" role="alert">
      <span>⚠ {{ errorMessage }}</span>
    </div>

    <!-- VISTA 1: SESIONES BGP -->
    <div v-if="activeTab === 'bgp'" class="table-card font-tabular">
      <RgDataTable
        :columns="bgpColumns"
        :rows="bgpSessions"
        caption="Sesiones de Enrutamiento BGP v7"
        row-key="id"
      >
        <template #actions="{ row }">
          <div class="row-actions-group">
            <button
              type="button"
              class="btn-icon"
              title="Editar Conexión BGP"
              @click="openEditBgpModal(row)"
            >
              ✏️
            </button>
            <button
              type="button"
              class="btn-icon btn-danger"
              title="Eliminar Conexión BGP"
              @click="handleDeleteBgpConnection(row)"
            >
              🗑
            </button>
          </div>
        </template>
      </RgDataTable>
    </div>

    <!-- VISTA 2: VECINOS OSPF -->
    <div v-else-if="activeTab === 'ospf'" class="table-card font-tabular">
      <RgDataTable
        :columns="ospfColumns"
        :rows="ospfNeighbors"
        caption="Adyacencias OSPF RouterOS"
        row-key="id"
      />
    </div>

    <!-- VISTA 3: TABLA DE RUTAS ESTÁTICAS -->
    <div v-else-if="activeTab === 'routes'" class="table-container font-tabular">
      <table class="tactical-table">
        <thead>
          <tr>
            <th>Destino (Dst-Address)</th>
            <th>Gateway</th>
            <th>Distancia</th>
            <th>Check Gateway</th>
            <th>Tabla</th>
            <th>Estado</th>
            <th class="actions-col">Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="staticRoutes.length === 0">
            <td colspan="7" class="empty-cell">No hay rutas configuradas.</td>
          </tr>
          <tr v-for="r in staticRoutes" :key="r.id">
            <td class="font-mono font-bold text-cyan">{{ r.dst_address }}</td>
            <td class="font-mono">{{ r.gateway || 'directamente conectada' }}</td>
            <td class="font-mono">{{ r.distance }}</td>
            <td><span class="badge-tag">{{ r.check_gateway || 'none' }}</span></td>
            <td><span class="badge-tag">{{ r.routing_table }}</span></td>
            <td>
              <span :class="r.disabled ? 'status-down' : 'status-up'">
                {{ r.disabled ? 'Deshabilitada' : (r.active ? 'Activa' : 'Inactiva') }}
              </span>
            </td>
            <td class="actions-col">
              <button
                type="button"
                class="btn-icon"
                title="Editar Ruta Estática"
                @click="openEditRouteModal(r)"
              >
                ✏️
              </button>
              <button
                type="button"
                class="btn-icon"
                :title="r.disabled ? 'Habilitar Ruta' : 'Deshabilitar Ruta'"
                @click="handleToggleRoute(r)"
              >
                {{ r.disabled ? '▶' : '⏸' }}
              </button>
              <button
                type="button"
                class="btn-icon btn-danger"
                title="Eliminar Ruta"
                @click="handleDeleteRoute(r)"
              >
                🗑
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- VISTA 4: POLICY-BASED ROUTING (PBR) -->
    <div v-else-if="activeTab === 'policy-routing'" class="pbr-dashboard">
      <div class="table-container font-tabular">
        <h3 class="section-title">Tablas de Enrutamiento FIB (/routing/table)</h3>
        <table class="tactical-table">
          <thead>
            <tr>
              <th>Nombre de la Tabla</th>
              <th>FIB</th>
              <th>Deshabilitada</th>
              <th class="actions-col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="routingTables.length === 0">
              <td colspan="4" class="empty-cell">No hay tablas FIB personalizadas.</td>
            </tr>
            <tr v-for="t in routingTables" :key="t.id || t['.id']">
              <td class="font-bold text-cyan">{{ t.name }}</td>
              <td>{{ t.fib === 'true' || t.fib === true ? 'Sí' : 'No' }}</td>
              <td>{{ t.disabled === 'true' || t.disabled === true ? 'Sí' : 'No' }}</td>
              <td class="actions-col">
                <button type="button" class="btn-icon" title="Editar Tabla FIB" @click="openEditTableModal(t)">✏️</button>
                <button type="button" class="btn-icon btn-danger" title="Eliminar Tabla FIB" @click="handleDeleteTable(t)">🗑</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="table-container font-tabular">
        <h3 class="section-title">Reglas de Enrutamiento (/routing/rule)</h3>
        <table class="tactical-table">
          <thead>
            <tr>
              <th>IP Origen</th>
              <th>Acción</th>
              <th>Tabla de Consulta</th>
              <th class="actions-col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="routingRules.length === 0">
              <td colspan="4" class="empty-cell">No hay reglas PBR definidas.</td>
            </tr>
            <tr v-for="rule in routingRules" :key="rule.id || rule['.id']">
              <td class="font-mono text-cyan">{{ rule['src-address'] || rule.src_address || 'any' }}</td>
              <td>{{ rule.action }}</td>
              <td class="font-bold">{{ rule.table }}</td>
              <td class="actions-col">
                <button type="button" class="btn-icon" title="Editar Regla PBR" @click="openEditRuleModal(rule)">✏️</button>
                <button type="button" class="btn-icon btn-danger" title="Eliminar Regla PBR" @click="handleDeleteRule(rule)">🗑</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- MODAL: CREAR RUTA ESTÁTICA -->
    <div v-if="isRouteModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Nueva Ruta Estática</h2>
        <form @submit.prevent="handleCreateRoute">
          <div class="form-group">
            <label for="route-dst">Destino (Dst-Address CIDR)</label>
            <input id="route-dst" v-model="newRoute.dst_address" type="text" class="form-input font-mono" placeholder="0.0.0.0/0" required />
          </div>
          <div class="form-group">
            <label for="route-gw">Puerta de Enlace (Gateway)</label>
            <input id="route-gw" v-model="newRoute.gateway" type="text" class="form-input font-mono" placeholder="192.168.1.1 o ether1" required />
          </div>
          <div class="form-group">
            <label for="route-dist">Distancia Administrativa</label>
            <input id="route-dist" v-model="newRoute.distance" type="number" class="form-input font-mono" min="1" max="255" required />
          </div>
          <div class="form-group">
            <label for="route-check">Detección de Caída (Check Gateway)</label>
            <select id="route-check" v-model="newRoute.check_gateway" class="form-input">
              <option value="none">Sin chequeo (none)</option>
              <option value="ping">Ping ICMP</option>
              <option value="arp">ARP Probe</option>
            </select>
          </div>
          <div class="form-group">
            <label for="route-table">Tabla de Enrutamiento</label>
            <input id="route-table" v-model="newRoute.routing_table" type="text" class="form-input" placeholder="main" required />
          </div>
          <div class="form-group">
            <label for="route-comm">Comentario</label>
            <input id="route-comm" v-model="newRoute.comment" type="text" class="form-input" placeholder="Ruta WAN Primaria" />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isRouteModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Crear Ruta</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: CREAR CONEXIÓN BGP -->
    <div v-if="isBgpModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Nueva Conexión BGP v7</h2>
        <form @submit.prevent="handleCreateBgpConnection">
          <div class="form-group">
            <label for="bgp-name">Nombre de la Conexión</label>
            <input id="bgp-name" v-model="newBgp.name" type="text" class="form-input" required />
          </div>
          <div class="form-group">
            <label for="bgp-rem-ip">IP Remota del Peer</label>
            <input id="bgp-rem-ip" v-model="newBgp.remote_address" type="text" class="form-input font-mono" placeholder="203.0.113.1" required />
          </div>
          <div class="form-group">
            <label for="bgp-rem-as">AS Remoto</label>
            <input id="bgp-rem-as" v-model="newBgp.remote_as" type="number" class="form-input font-mono" required />
          </div>
          <div class="form-group">
            <label for="bgp-loc-as">AS Local</label>
            <input id="bgp-loc-as" v-model="newBgp.local_as" type="number" class="form-input font-mono" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isBgpModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Guardar Peer BGP</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: CREAR TABLA FIB -->
    <div v-if="isTableModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Crear Tabla de Enrutamiento FIB</h2>
        <form @submit.prevent="handleCreateTable">
          <div class="form-group">
            <label for="tbl-name">Nombre de la Tabla</label>
            <input id="tbl-name" v-model="newTable.name" type="text" class="form-input" placeholder="to_wan2" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isTableModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Crear Tabla</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: CREAR REGLA PBR -->
    <div v-if="isRuleModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Crear Regla de Enrutamiento PBR</h2>
        <form @submit.prevent="handleCreateRule">
          <div class="form-group">
            <label for="rul-src">IP Origen</label>
            <input id="rul-src" v-model="newRule.src_address" type="text" class="form-input font-mono" placeholder="192.168.88.100/32" required />
          </div>
          <div class="form-group">
            <label for="rul-tbl">Tabla Destino</label>
            <input id="rul-tbl" v-model="newRule.table" type="text" class="form-input" placeholder="to_wan2" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isRuleModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Crear Regla</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: EDITAR RUTA ESTÁTICA -->
    <div v-if="isEditRouteModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Editar Ruta Estática ({{ editRouteForm.dst_address }})</h2>
        <form @submit.prevent="handleUpdateRoute">
          <div class="form-group">
            <label for="edit-route-gw">Puerta de Enlace (Gateway)</label>
            <input id="edit-route-gw" v-model="editRouteForm.gateway" type="text" class="form-input font-mono" required />
          </div>
          <div class="form-group">
            <label for="edit-route-dist">Distancia Administrativa</label>
            <input id="edit-route-dist" v-model.number="editRouteForm.distance" type="number" class="form-input font-mono" min="1" max="255" required />
          </div>
          <div class="form-group">
            <label for="edit-route-check">Check Gateway</label>
            <select id="edit-route-check" v-model="editRouteForm.check_gateway" class="form-input">
              <option value="none">Sin chequeo (none)</option>
              <option value="ping">Ping ICMP</option>
              <option value="arp">ARP Probe</option>
            </select>
          </div>
          <div class="form-group">
            <label for="edit-route-table">Tabla de Enrutamiento</label>
            <input id="edit-route-table" v-model="editRouteForm.routing_table" type="text" class="form-input" required />
          </div>
          <div class="form-group">
            <label for="edit-route-comm">Comentario</label>
            <input id="edit-route-comm" v-model="editRouteForm.comment" type="text" class="form-input" />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isEditRouteModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Guardar Cambios</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: EDITAR CONEXIÓN BGP -->
    <div v-if="isEditBgpModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Editar Conexión BGP ({{ editBgpForm.name }})</h2>
        <form @submit.prevent="handleUpdateBgpConnection">
          <div class="form-group">
            <label for="edit-bgp-rem-ip">IP Remota del Peer</label>
            <input id="edit-bgp-rem-ip" v-model="editBgpForm.remote_address" type="text" class="form-input font-mono" required />
          </div>
          <div class="form-group">
            <label for="edit-bgp-rem-as">AS Remoto</label>
            <input id="edit-bgp-rem-as" v-model.number="editBgpForm.remote_as" type="number" class="form-input font-mono" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isEditBgpModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Guardar Cambios</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: EDITAR TABLA FIB -->
    <div v-if="isEditTableModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Editar Tabla FIB</h2>
        <form @submit.prevent="handleUpdateTable">
          <div class="form-group">
            <label for="edit-tbl-name">Nombre de la Tabla</label>
            <input id="edit-tbl-name" v-model="editTableForm.name" type="text" class="form-input" required />
          </div>
          <div class="form-group">
            <label for="edit-tbl-comm">Comentario</label>
            <input id="edit-tbl-comm" v-model="editTableForm.comment" type="text" class="form-input" />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isEditTableModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Guardar Cambios</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL: EDITAR REGLA PBR -->
    <div v-if="isEditRuleModalOpen" class="modal-backdrop">
      <div class="modal-window">
        <h2 class="modal-title">Editar Regla PBR</h2>
        <form @submit.prevent="handleUpdateRule">
          <div class="form-group">
            <label for="edit-rul-src">IP Origen</label>
            <input id="edit-rul-src" v-model="editRuleForm.src_address" type="text" class="form-input font-mono" required />
          </div>
          <div class="form-group">
            <label for="edit-rul-tbl">Tabla Destino</label>
            <input id="edit-rul-tbl" v-model="editRuleForm.table" type="text" class="form-input" required />
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-tactical btn-outline" @click="isEditRuleModalOpen = false">Cancelar</button>
            <button type="submit" class="btn-tactical btn-cyan">Guardar Cambios</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .routing-view {
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
    font-size: 1.2rem;
    font-weight: 700;
    color: #38bdf8;
  }

  .view-subtitle {
    margin: 2px 0 0 0;
    font-size: 0.8rem;
    color: #94a3b8;
  }

  .header-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .subtabs-bar {
    display: flex;
    gap: 4px;
    background: #0f172a;
    padding: 3px;
    border: 1px solid #334155;
    border-radius: 6px;
    width: 100%;
  }

  .btn-subtab {
    background: transparent;
    border: none;
    color: #94a3b8;
    padding: 6px 14px;
    font-size: 0.8rem;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.2s;
  }

  .btn-subtab:hover {
    color: #f8fafc;
  }

  .btn-subtab--active {
    background: #0284c7;
    color: #ffffff;
    font-weight: 600;
  }

  .table-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 1rem;
  }

  .table-container {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    overflow-x: auto;
    padding: 1rem;
  }

  .section-title {
    font-size: 0.95rem;
    color: #38bdf8;
    margin-top: 0;
    margin-bottom: 0.75rem;
  }

  .tactical-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    text-align: left;
  }

  .tactical-table th {
    background-color: rgba(15, 23, 42, 0.8);
    color: #94a3b8;
    padding: 0.65rem 1rem;
    font-weight: 600;
    border-bottom: 1px solid #334155;
  }

  .tactical-table td {
    padding: 0.6rem 1rem;
    border-bottom: 1px solid #1e293b;
  }

  .tactical-table tr:hover {
    background-color: rgba(255, 255, 255, 0.02);
  }

  .empty-cell {
    text-align: center;
    padding: 2rem;
    color: #64748b;
  }

  .actions-col {
    text-align: right;
    white-space: nowrap;
  }

  .btn-tactical {
    font-size: 0.82rem;
    font-weight: 600;
    padding: 0.45rem 0.9rem;
    border-radius: 6px;
    cursor: pointer;
    border: none;
  }

  .btn-cyan {
    background-color: #0284c7;
    color: #ffffff;
  }

  .btn-outline {
    background: transparent;
    border: 1px solid #475569;
    color: #f8fafc;
  }

  .btn-icon {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.25rem 0.5rem;
    font-size: 0.95rem;
    border-radius: 4px;
    color: #f8fafc;
  }

  .btn-icon:hover {
    background: rgba(255, 255, 255, 0.1);
  }

  .badge-tag {
    background: #334155;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.75rem;
  }

  .status-up {
    color: #34d399;
  }

  .status-down {
    color: #f87171;
  }

  .alert-box {
    padding: 0.75rem 1rem;
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .alert-success {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #059669;
    color: #6ee7b7;
  }

  .alert-danger {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #dc2626;
    color: #fca5a5;
  }

  .pbr-dashboard {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
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
    max-width: 500px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  }

  .modal-title {
    margin-top: 0;
    font-size: 1.15rem;
    color: #38bdf8;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    margin-bottom: 0.9rem;
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

  .font-tabular {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  .font-mono {
    font-family: monospace;
  }

  .font-bold {
    font-weight: 700;
  }

  .text-cyan {
    color: #38bdf8;
  }
</style>
