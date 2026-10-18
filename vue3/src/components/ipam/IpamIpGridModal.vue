<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useIpamStore } from '@/stores/useIpamStore';
import type { IPAMAddress, IPAMPrefix } from '@/types';

const props = defineProps<{
  prefix: IPAMPrefix;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const ipamStore = useIpamStore();
const selectedIpInfo = ref<IPAMAddress | null>(null);

onMounted(async () => {
  await ipamStore.fetchAddresses(props.prefix.id);
});

// Extraer octeto base de IPv4 (ej: 100.64.10.X)
const ipBase = computed(() => {
  const parts = props.prefix.prefix.split('/')[0].split('.');
  if (parts.length === 4) {
    return `${parts[0]}.${parts[1]}.${parts[2]}`;
  }
  return '';
});

// Mapa de IPs asignadas indexadas por el último octeto (0..255)
const allocatedMap = computed(() => {
  const map = new Map<number, IPAMAddress>();
  for (const addr of ipamStore.addresses) {
    const rawIp = addr.address.split('/')[0];
    const lastOctet = parseInt(rawIp.split('.').pop() || '-1', 10);
    if (!isNaN(lastOctet) && lastOctet >= 0 && lastOctet <= 255) {
      map.set(lastOctet, addr);
    }
  }
  return map;
});

function getTileClass(octet: number): string {
  if (octet === 0 || octet === 255) return 'tile--reserved';
  const item = allocatedMap.value.get(octet);
  if (!item) return 'tile--available';
  if (item.status === 'SOFT_LOCKED') return 'tile--soft-locked';
  if (item.status === 'DHCP_DYNAMIC') return 'tile--pool';
  return 'tile--allocated';
}

function handleSelectTile(octet: number) {
  const item = allocatedMap.value.get(octet);
  if (item) {
    selectedIpInfo.value = item;
  } else {
    selectedIpInfo.value = {
      id: '',
      tenant_id: props.prefix.tenant_id,
      prefix_id: props.prefix.id,
      address: `${ipBase.value}.${octet}/32`,
      ip_family: 'IPv4',
      status: 'RESERVED',
      description: 'Dirección Libre - Lista para aprovisionamiento',
      created_at: '',
      updated_at: '',
    };
  }
}
</script>

<template>
  <div class="rg-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="grid-modal-title">
    <div class="rg-modal rg-modal--grid">
      <header class="modal-header">
        <div class="header-left">
          <h3 id="grid-modal-title">🔲 Matriz Visual de Direcciones IP (/24)</h3>
          <span class="prefix-tag">{{ prefix.prefix }}</span>
        </div>
        <button type="button" class="btn-close" @click="emit('close')" aria-label="Cerrar matriz">✕</button>
      </header>

      <!-- Leyenda de colores -->
      <div class="grid-legend">
        <div class="legend-item"><span class="legend-dot tile--available" /> Disponible</div>
        <div class="legend-item"><span class="legend-dot tile--allocated" /> Asignada / Fija</div>
        <div class="legend-item"><span class="legend-dot tile--pool" /> Pool PPPoE/DHCP</div>
        <div class="legend-item"><span class="legend-dot tile--soft-locked" /> Soft-Lock (5 min)</div>
        <div class="legend-item"><span class="legend-dot tile--reserved" /> Red / Broadcast</div>
      </div>

      <!-- Cuadrícula 16x16 (256 hosts) -->
      <div class="grid-container" aria-label="Cuadrícula de 256 IPs">
        <button
          v-for="octet in 256"
          :key="octet - 1"
          type="button"
          :class="['ip-tile', getTileClass(octet - 1)]"
          :title="`IP: .${octet - 1}`"
          @click="handleSelectTile(octet - 1)"
        >
          {{ octet - 1 }}
        </button>
      </div>

      <!-- Detalle de la IP seleccionada -->
      <div v-if="selectedIpInfo" class="ip-detail-panel">
        <div class="detail-header">
          <span class="detail-ip">{{ selectedIpInfo.address }}</span>
          <span :class="['detail-status', `status--${selectedIpInfo.status}`]">
            {{ selectedIpInfo.status }}
          </span>
        </div>
        <div class="detail-body">
          <p><strong>Descripción:</strong> {{ selectedIpInfo.description || 'Sin notas' }}</p>
          <p v-if="selectedIpInfo.mac_address"><strong>MAC:</strong> {{ selectedIpInfo.mac_address }}</p>
          <p v-if="selectedIpInfo.interface_name"><strong>Interfaz:</strong> {{ selectedIpInfo.interface_name }}</p>
        </div>
      </div>

      <footer class="modal-footer">
        <button type="button" class="btn-rg btn-rg--cyan" @click="emit('close')">
          Cerrar Vista de Matriz
        </button>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.rg-modal--grid {
  max-width: 780px;
  width: 95%;
}

.prefix-tag {
  background: rgba(0, 243, 255, 0.15);
  color: #00f3ff;
  font-family: monospace;
  font-weight: bold;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
  margin-left: 0.75rem;
}

.grid-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 6px;
  font-size: 0.75rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  display: inline-block;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(16, 1fr);
  gap: 3px;
  background: #060a12;
  padding: 0.5rem;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  max-height: 380px;
  overflow-y: auto;
}

.ip-tile {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: monospace;
  font-size: 0.65rem;
  font-weight: 700;
  border-radius: 2px;
  border: none;
  cursor: pointer;
  transition: transform 0.1s, box-shadow 0.1s;
}

.ip-tile:hover {
  transform: scale(1.2);
  z-index: 2;
  box-shadow: 0 0 8px #fff;
}

.tile--available {
  background: rgba(0, 255, 136, 0.2);
  color: #00ff88;
}

.tile--allocated {
  background: rgba(255, 51, 102, 0.75);
  color: #fff;
}

.tile--pool {
  background: rgba(0, 150, 255, 0.6);
  color: #fff;
}

.tile--soft-locked {
  background: rgba(168, 85, 247, 0.7);
  color: #fff;
  animation: pulse 1.5s infinite;
}

.tile--reserved {
  background: rgba(255, 255, 255, 0.1);
  color: #64748b;
  cursor: not-allowed;
}

@keyframes pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.ip-detail-panel {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #1e293b;
  border-left: 3px solid #00f3ff;
  border-radius: 4px;
  font-size: 0.85rem;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.4rem;
}

.detail-ip {
  font-family: monospace;
  font-weight: bold;
  font-size: 1rem;
  color: #00f3ff;
}

.detail-status {
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  font-size: 0.7rem;
  font-weight: bold;
}

.status--ALLOCATED {
  background: rgba(255, 51, 102, 0.2);
  color: #ff3366;
}

.status--SOFT_LOCKED {
  background: rgba(168, 85, 247, 0.2);
  color: #c084fc;
}

.status--RESERVED {
  background: rgba(0, 255, 136, 0.2);
  color: #00ff88;
}

.detail-body p {
  margin: 0.25rem 0;
  color: #cbd5e1;
}
</style>
