<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { onMounted, ref } from 'vue';
  import { useIpamStore } from '@/stores/useIpamStore';
  import type { IPAMPrefix, IPFamily, IPPrefixRole } from '@/types';

  const ipamStore = useIpamStore();

  const emit = defineEmits<{
    (e: 'open-ip-grid', prefix: IPAMPrefix): void;
    (e: 'open-corporate-modal', prefix?: IPAMPrefix): void;
  }>();

  const newPrefixModalOpen = ref(false);
  const newPrefix = ref({
    vrf_id: '',
    prefix: '',
    ip_family: 'IPv4' as IPFamily,
    role: 'CUSTOMER_RESIDENTIAL' as IPPrefixRole,
    is_pool: false,
    default_child_prefix_len: 56,
    description: '',
  });

  const nextAvailableModalOpen = ref(false);
  const nextAvailableResult = ref<{
    next_available: string;
    is_subnet: boolean;
    message: string;
  } | null>(null);

  onMounted(async () => {
    await ipamStore.fetchVrfs();
    await ipamStore.fetchPrefixes();
    if (ipamStore.vrfs.length > 0 && !newPrefix.value.vrf_id) {
      newPrefix.value.vrf_id = ipamStore.vrfs[0].id;
    }
  });

  function getUtilizationColor(pct: number): string {
    if (pct >= 90) return 'var(--rg-danger, #ff3366)';
    if (pct >= 75) return 'var(--rg-warning, #ffaa00)';
    return 'var(--rg-success, #00ff88)';
  }

  function getErrorMessage(err: unknown, defaultMsg: string): string {
    if (err && typeof err === 'object') {
      const resData = (err as { response?: { data?: { detail?: string } } }).response?.data;
      if (resData?.detail) return resData.detail;
      const msg = (err as { message?: string }).message;
      if (msg) return msg;
    }
    return defaultMsg;
  }

  async function handleGetNextAvailable(pfx: IPAMPrefix) {
    try {
      nextAvailableResult.value = await ipamStore.getNextAvailable(pfx.id);
      nextAvailableModalOpen.value = true;
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Error al obtener recurso libre'));
    }
  }

  async function handleCreatePrefix() {
    if (!newPrefix.value.prefix.trim()) return;
    try {
      await ipamStore.createPrefix({
        vrf_id: newPrefix.value.vrf_id,
        prefix: newPrefix.value.prefix.trim(),
        ip_family: newPrefix.value.ip_family,
        role: newPrefix.value.role,
        is_pool: newPrefix.value.is_pool,
        default_child_prefix_len:
          newPrefix.value.ip_family === 'IPv6'
            ? newPrefix.value.default_child_prefix_len
            : undefined,
        description: newPrefix.value.description.trim() || undefined,
      });
      newPrefixModalOpen.value = false;
      newPrefix.value.prefix = '';
      newPrefix.value.description = '';
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Error al registrar prefijo'));
    }
  }

  const isSyncingFleet = ref(false);
  const syncFeedbackMessage = ref<string | null>(null);

  async function handleSyncFleet() {
    isSyncingFleet.value = true;
    syncFeedbackMessage.value = null;
    try {
      const res = await ipamStore.syncAllMikrotikIpam();
      syncFeedbackMessage.value =
        res.message ||
        `✅ Sincronizados ${res.synced_prefixes} prefijos/pools y ${res.synced_ips} IPs en la flota.`;
      setTimeout(() => {
        syncFeedbackMessage.value = null;
      }, 7000);
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Error al sincronizar flota MikroTik'));
    } finally {
      isSyncingFleet.value = false;
    }
  }

  function extractPoolRange(pfx: IPAMPrefix): string | null {
    if (pfx.description) {
      // Coincidir con rangos en descripción: (192.168.10.2-192.168.10.254) o (192.168.10.2 - 192.168.10.254)
      const match = pfx.description.match(/\(([\d.]+\s*-\s*[\d.]+)\)/);
      if (match) return match[1];
    }

    // Si es IPv4 CIDR, calcular rango utilizable estándar
    if (pfx.ip_family === 'IPv4' && pfx.prefix.includes('/')) {
      const [ip, maskStr] = pfx.prefix.split('/');
      const mask = parseInt(maskStr, 10);
      if (mask >= 24 && mask <= 30) {
        const parts = ip.split('.').map(Number);
        if (parts.length === 4) {
          const base = `${parts[0]}.${parts[1]}.${parts[2]}`;
          const blockSize = Math.pow(2, 32 - mask);
          const startHost = parts[3] + 1;
          const endHost = parts[3] + blockSize - 2;
          return `${base}.${startHost} - ${base}.${endHost}`;
        }
      }
    }
    return null;
  }
</script>


<template>
  <div class="ipam-prefix-table-container">
    <!-- Barra de herramientas táctica -->
    <header class="ipam-toolbar">
      <div class="toolbar-left">
        <h2 class="ipam-title">
          <span class="icon" aria-hidden="true">🌐</span> GESTOR IPAM DUAL-STACK
        </h2>
        <span class="prefix-count-badge">{{ ipamStore.filteredPrefixes.length }} Prefijos</span>
      </div>

      <div class="toolbar-filters">
        <select v-model="ipamStore.selectedVrfId" class="rg-select" aria-label="Filtrar por VRF">
          <option :value="null">Todas las VRFs</option>
          <option v-for="vrf in ipamStore.vrfs" :key="vrf.id" :value="vrf.id">
            VRF: {{ vrf.name }}
          </option>
        </select>

        <select
          v-model="ipamStore.filterFamily"
          class="rg-select"
          aria-label="Filtrar por Familia IP"
        >
          <option :value="null">IPv4 & IPv6</option>
          <option value="IPv4">Solo IPv4</option>
          <option value="IPv6">Solo IPv6</option>
        </select>

        <input
          v-model="ipamStore.searchQuery"
          type="search"
          class="rg-search-input"
          placeholder="Buscar prefijo, CIDR o descripción..."
          aria-label="Buscar prefijos"
        />
      </div>

      <div class="toolbar-actions">
        <button
          type="button"
          class="btn-rg btn-rg--cyan"
          :disabled="isSyncingFleet"
          aria-label="Sincronizar pools y DHCP de la flota"
          @click="handleSyncFleet"
        >
          <span v-if="isSyncingFleet">⏳ Sincronizando...</span>
          <span v-else>🔄 Sincronizar Flota (DHCP)</span>
        </button>
        <button
          type="button"
          class="btn-rg btn-rg--cyan"
          aria-label="Añadir nuevo prefijo"
          @click="newPrefixModalOpen = true"
        >
          ➕ Nuevo Bloque / Subred
        </button>
        <button
          type="button"
          class="btn-rg btn-rg--purple"
          aria-label="Gestor IPv6 Corporativo"
          @click="emit('open-corporate-modal')"
        >
          🏢 IPv6 Corporativo (/48)
        </button>
      </div>
    </header>

    <!-- Feedback Banner de Sincronización -->
    <div v-if="syncFeedbackMessage" class="sync-feedback-banner" role="status">
      {{ syncFeedbackMessage }}
    </div>

    <!-- Tabla de Prefijos -->
    <div class="table-scroll-wrapper">
      <table class="rg-table" aria-label="Listado de Prefijos IPAM">
        <thead>
          <tr>
            <th scope="col">Prefijo CIDR & Rango</th>
            <th scope="col">Familia</th>
            <th scope="col">Rol Operativo</th>
            <th scope="col">Utilización</th>
            <th scope="col">Subred Hija /56</th>
            <th scope="col">Descripción</th>
            <th scope="col" class="th-actions">Acciones Tácticas</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="ipamStore.filteredPrefixes.length === 0">
            <td colspan="7" class="empty-state-cell">
              No se encontraron prefijos que coincidan con los filtros seleccionados.
            </td>
          </tr>
          <tr v-for="pfx in ipamStore.filteredPrefixes" :key="pfx.id" class="table-row">
            <td class="td-prefix">
              <div class="prefix-header-line">
                <span class="cidr-badge">{{ pfx.prefix }}</span>
                <span v-if="pfx.is_pool" class="pool-tag" title="Pool Dinámico PPPoE/DHCP">POOL</span>
              </div>
              <div
                v-if="extractPoolRange(pfx)"
                class="range-subtext"
                :title="`Rango de direcciones asignables: ${extractPoolRange(pfx)}`"
              >
                <span class="range-icon" aria-hidden="true">🎯</span>
                <span class="range-val">{{ extractPoolRange(pfx) }}</span>
              </div>
            </td>

            <td>
              <span
                :class="[
                  'family-badge',
                  pfx.ip_family === 'IPv6' ? 'family-badge--v6' : 'family-badge--v4',
                ]"
              >
                {{ pfx.ip_family }}
              </span>
            </td>
            <td>
              <span class="role-badge">{{ pfx.role }}</span>
            </td>
            <td class="td-utilization">
              <div class="utilization-bar-wrapper" :title="`${pfx.utilization_pct}% utilizado`">
                <div
                  class="utilization-bar-fill"
                  :style="{
                    width: `${Math.min(100, Math.max(0, pfx.utilization_pct))}%`,
                    backgroundColor: getUtilizationColor(pfx.utilization_pct),
                  }"
                />
              </div>
              <span class="utilization-text">{{ pfx.utilization_pct }}%</span>
            </td>
            <td>
              <span v-if="pfx.default_child_prefix_len" class="child-len-tag">
                /{{ pfx.default_child_prefix_len }} PD
              </span>
              <span v-else class="text-muted">—</span>
            </td>
            <td class="td-desc">{{ pfx.description || 'Sin notas' }}</td>
            <td class="td-actions">
              <button
                type="button"
                class="btn-cell btn-cell--free"
                title="Calcular siguiente IP o subred libre"
                @click="handleGetNextAvailable(pfx)"
              >
                ⚡ Siguiente Libre
              </button>
              <button
                v-if="pfx.ip_family === 'IPv4'"
                type="button"
                class="btn-cell btn-cell--grid"
                title="Ver matriz de IPs libres y ocupadas"
                @click="emit('open-ip-grid', pfx)"
              >
                🔲 Matriz IPs
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Nuevo Prefijo -->
    <div
      v-if="newPrefixModalOpen"
      class="rg-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-pfx-title"
    >
      <div class="rg-modal">
        <header class="modal-header">
          <h3 id="modal-pfx-title">Registrar Nuevo Prefijo IPAM</h3>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar modal"
            @click="newPrefixModalOpen = false"
          >
            ✕
          </button>
        </header>

        <form class="modal-body" @submit.prevent="handleCreatePrefix">

          <div class="form-group">
            <label for="pfx-vrf">VRF de Enrutamiento</label>
            <select id="pfx-vrf" v-model="newPrefix.vrf_id" class="rg-input" required>
              <option v-for="vrf in ipamStore.vrfs" :key="vrf.id" :value="vrf.id">
                {{ vrf.name }} {{ vrf.route_distinguisher ? `(${vrf.route_distinguisher})` : '' }}
              </option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label for="pfx-cidr">Prefijo CIDR (ej: 100.64.10.0/24 o 2803:cafe::/32)</label>
              <input
                id="pfx-cidr"
                v-model="newPrefix.prefix"
                type="text"
                class="rg-input"
                placeholder="100.64.10.0/24"
                required
              />
            </div>
            <div class="form-group w-30">
              <label for="pfx-family">Familia IP</label>
              <select id="pfx-family" v-model="newPrefix.ip_family" class="rg-input">
                <option value="IPv4">IPv4</option>
                <option value="IPv6">IPv6</option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label for="pfx-role">Rol Operativo</label>
              <select id="pfx-role" v-model="newPrefix.role" class="rg-input">
                <option value="CUSTOMER_RESIDENTIAL">CUSTOMER_RESIDENTIAL (Hogares / PyMEs)</option>
                <option value="CUSTOMER_CORPORATE">CUSTOMER_CORPORATE (Empresas)</option>
                <option value="CGNAT">CGNAT (Carrier Grade NAT)</option>
                <option value="PUBLIC_DYNAMIC">PUBLIC_DYNAMIC (Pools Públicos Dinámicos)</option>
                <option value="PUBLIC_STATIC">PUBLIC_STATIC (IPs Fijas Públicas)</option>
                <option value="INFRA_P2P">INFRA_P2P (Enlaces Punto a Punto /30)</option>
                <option value="LOOPBACK">LOOPBACK (Gestión de Routers)</option>
              </select>
            </div>
            <div v-if="newPrefix.ip_family === 'IPv6'" class="form-group w-30">
              <label for="pfx-child-len">Delegación /X</label>
              <input
                id="pfx-child-len"
                v-model.number="newPrefix.default_child_prefix_len"
                type="number"
                min="48"
                max="64"
                class="rg-input"
              />
            </div>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="newPrefix.is_pool" type="checkbox" />
              <span>Marcar como Pool Dinámico para PPPoE / DHCP</span>
            </label>
          </div>

          <div class="form-group">
            <label for="pfx-desc">Descripción / Observaciones</label>
            <input
              id="pfx-desc"
              v-model="newPrefix.description"
              type="text"
              class="rg-input"
              placeholder="Ej: Prefijo asignado a OLT Centro Pon 1"
            />
          </div>

          <footer class="modal-footer">
            <button
              type="button"
              class="btn-rg btn-rg--secondary"
              @click="newPrefixModalOpen = false"
            >
              Cancelar
            </button>
            <button type="submit" class="btn-rg btn-rg--cyan">Guardar en IPAM</button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Siguiente Recurso Libre -->
    <div
      v-if="nextAvailableModalOpen && nextAvailableResult"
      class="rg-modal-backdrop"
      role="dialog"
      aria-modal="true"
    >
      <div class="rg-modal rg-modal--sm">
        <header class="modal-header">
          <h3>⚡ Recurso Libre Asignado</h3>
          <button type="button" class="btn-close" @click="nextAvailableModalOpen = false">✕</button>
        </header>
        <div class="modal-body text-center">
          <p class="recurso-label">
            {{ nextAvailableResult.is_subnet ? 'Subred Delegada' : 'Dirección IP' }} Disponible:
          </p>
          <div class="recurso-highlight">{{ nextAvailableResult.next_available }}</div>
          <p class="recurso-msg">{{ nextAvailableResult.message }}</p>
        </div>
        <footer class="modal-footer justify-center">
          <button type="button" class="btn-rg btn-rg--cyan" @click="nextAvailableModalOpen = false">
            Entendido
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .ipam-prefix-table-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    background: var(--rg-surface, #0a101d);
    color: #fff;
    border: 1px solid rgba(0, 243, 255, 0.2);
    border-radius: 8px;
    padding: 1.25rem;
  }

  .ipam-toolbar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .toolbar-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .ipam-title {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 700;
    color: #00f3ff;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    letter-spacing: 0.5px;
  }

  .prefix-count-badge {
    background: rgba(0, 243, 255, 0.15);
    color: #00f3ff;
    font-size: 0.75rem;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-weight: 600;
  }

  .toolbar-filters {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex: 1;
    max-width: 600px;
  }

  .rg-select,
  .rg-search-input,
  .rg-input {
    background: #121b2d;
    color: #fff;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 4px;
    padding: 0.45rem 0.65rem;
    font-size: 0.85rem;
  }

  .rg-search-input {
    flex: 1;
  }

  .rg-select:focus,
  .rg-search-input:focus,
  .rg-input:focus {
    border-color: #00f3ff;
    outline: none;
  }

  .toolbar-actions {
    display: flex;
    gap: 0.5rem;
  }

  .btn-rg {
    padding: 0.5rem 0.85rem;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    border: none;
    transition: all 0.2s;
  }

  .btn-rg--cyan {
    background: #00f3ff;
    color: #000;
  }
  .btn-rg--cyan:hover {
    background: #33f6ff;
    box-shadow: 0 0 10px rgba(0, 243, 255, 0.4);
  }

  .btn-rg--purple {
    background: #8a2be2;
    color: #fff;
  }
  .btn-rg--purple:hover {
    background: #9d46ea;
    box-shadow: 0 0 10px rgba(138, 43, 226, 0.4);
  }

  .btn-rg--secondary {
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
  }

  .table-scroll-wrapper {
    overflow-x: auto;
  }

  .rg-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
    text-align: left;
  }

  .rg-table th {
    background: rgba(18, 27, 45, 0.8);
    color: #8da4be;
    padding: 0.65rem 0.75rem;
    font-weight: 600;
    border-bottom: 2px solid rgba(0, 243, 255, 0.2);
  }

  .rg-table td {
    padding: 0.65rem 0.75rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }

  .table-row:hover {
    background: rgba(0, 243, 255, 0.04);
  }

  .sync-feedback-banner {
    background: rgba(0, 255, 136, 0.12);
    border: 1px solid #00ff88;
    color: #a7f3d0;
    padding: 0.6rem 1rem;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .prefix-header-line {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .range-subtext {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    margin-top: 0.25rem;
    font-size: 0.72rem;
    color: #a5f3fc;
    font-family: monospace;
    background: rgba(0, 243, 255, 0.08);
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    border: 1px dashed rgba(0, 243, 255, 0.35);
  }

  .range-icon {
    font-size: 0.75rem;
  }

  .range-val {
    font-weight: 600;
    letter-spacing: 0.3px;
  }

  .cidr-badge {
    font-family: monospace;
    font-weight: 700;
    color: #00f3ff;
  }

  .pool-tag {
    background: rgba(0, 255, 136, 0.15);
    color: #00ff88;
    font-size: 0.65rem;
    padding: 0.15rem 0.35rem;
    border-radius: 3px;
    margin-left: 0.5rem;
    font-weight: bold;
  }


  .family-badge {
    font-size: 0.75rem;
    font-weight: bold;
    padding: 0.2rem 0.45rem;
    border-radius: 4px;
  }
  .family-badge--v4 {
    background: rgba(0, 150, 255, 0.2);
    color: #60a5fa;
  }
  .family-badge--v6 {
    background: rgba(168, 85, 247, 0.2);
    color: #c084fc;
  }

  .role-badge {
    font-size: 0.75rem;
    background: rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
  }

  .td-utilization {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .utilization-bar-wrapper {
    width: 70px;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
  }

  .utilization-bar-fill {
    height: 100%;
    border-radius: 4px;
  }

  .utilization-text {
    font-size: 0.75rem;
    font-weight: 600;
  }

  .child-len-tag {
    background: rgba(255, 255, 255, 0.1);
    padding: 0.2rem 0.4rem;
    border-radius: 3px;
    font-size: 0.75rem;
  }

  .td-desc {
    max-width: 250px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .td-actions {
    display: flex;
    gap: 0.4rem;
  }

  .btn-cell {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #fff;
    border-radius: 4px;
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-cell--free:hover {
    background: rgba(0, 243, 255, 0.2);
    border-color: #00f3ff;
    color: #00f3ff;
  }

  .btn-cell--grid:hover {
    background: rgba(0, 255, 136, 0.2);
    border-color: #00ff88;
    color: #00ff88;
  }

  /* Modales */
  .rg-modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.75);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
  }

  .rg-modal {
    background: #0f172a;
    border: 1px solid #00f3ff;
    border-radius: 8px;
    width: 90%;
    max-width: 550px;
    padding: 1.5rem;
    box-shadow: 0 0 25px rgba(0, 243, 255, 0.2);
  }

  .rg-modal--sm {
    max-width: 400px;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 0.5rem;
  }

  .modal-header h3 {
    margin: 0;
    font-size: 1.1rem;
    color: #00f3ff;
  }

  .btn-close {
    background: none;
    border: none;
    color: #8da4be;
    font-size: 1.25rem;
    cursor: pointer;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    margin-bottom: 0.85rem;
  }

  .form-row {
    display: flex;
    gap: 0.75rem;
  }

  .flex-1 {
    flex: 1;
  }

  .w-30 {
    width: 35%;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
    cursor: pointer;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    margin-top: 1.25rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 0.75rem;
  }

  .recurso-highlight {
    font-family: monospace;
    font-size: 1.5rem;
    font-weight: 800;
    color: #00ff88;
    margin: 1rem 0;
    padding: 0.5rem;
    background: rgba(0, 255, 136, 0.1);
    border-radius: 6px;
    border: 1px dashed #00ff88;
  }

  .justify-center {
    justify-content: center;
  }
</style>
