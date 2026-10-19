<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { computed, ref } from 'vue';
  import { useIpamStore } from '@/stores/useIpamStore';

  const emit = defineEmits<{
    (e: 'close'): void;
  }>();

  const ipamStore = useIpamStore();

  const corpForm = ref({
    clientName: '',
    contractCode: '',
    prefixLength: 48,
    baseSupernetId: '',
    bgpAsn: '',
    reverseDnsNs: 'ns1.cliente-corp.com',
    description: '',
  });

  // Prefijos IPv6 disponibles para carving
  const availableV6Supernets = computed(() => {
    return ipamStore.prefixes.filter(
      (p) => p.ip_family === 'IPv6' && p.role === 'CUSTOMER_CORPORATE',
    );
  });

  const calculatedPrefixPreview = computed(() => {
    if (!corpForm.value.baseSupernetId) return '2803:cafe:corp::/48';
    const supernet = ipamStore.prefixes.find((p) => p.id === corpForm.value.baseSupernetId);
    if (!supernet) return '';
    const root = supernet.prefix.split('::')[0];
    return `${root}:b${corpForm.value.prefixLength}00::/${corpForm.value.prefixLength}`;
  });

  const generatedMikrotikCommand = computed(() => {
    return `/ipv6/route add dst-address=${calculatedPrefixPreview.value} blackhole comment="CORP-${corpForm.value.clientName || 'CLIENT'}"`;
  });

  async function handleAssignCorporatePrefix() {
    if (!corpForm.value.clientName.trim() || !calculatedPrefixPreview.value) return;

    try {
      const vrfId = ipamStore.vrfs.length > 0 ? ipamStore.vrfs[0].id : '';
      await ipamStore.createPrefix({
        vrf_id: vrfId,
        prefix: calculatedPrefixPreview.value,
        ip_family: 'IPv6',
        role: 'CUSTOMER_CORPORATE',
        default_child_prefix_len: 64,
        description: `Corporativo: ${corpForm.value.clientName} (Contrato: ${corpForm.value.contractCode || 'N/A'}) - DNS: ${corpForm.value.reverseDnsNs}`,
      });
      alert(`Prefijo Corporativo ${calculatedPrefixPreview.value} asignado exitosamente.`);
      emit('close');
    } catch (err: any) {
      alert(err?.response?.data?.detail || err?.message || 'Error al asignar prefijo corporativo');
    }
  }
</script>

<template>
  <div class="rg-modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="corp-modal-title">
    <div class="rg-modal rg-modal--corp">
      <header class="modal-header">
        <h3 id="corp-modal-title">🏢 Gestor de Asignación IPv6 Corporativo</h3>
        <button type="button" class="btn-close" @click="emit('close')" aria-label="Cerrar modal">
          ✕
        </button>
      </header>

      <form @submit.prevent="handleAssignCorporatePrefix" class="modal-body">
        <div class="info-banner">
          Permite segmentar bloques dedicados (<strong>/48</strong>, <strong>/52</strong> o
          <strong>/56</strong>) para empresas con múltiples VLANs, infraestructura interna o sesión
          BGP directa.
        </div>

        <div class="form-row">
          <div class="form-group flex-1">
            <label for="corp-client">Razón Social / Cliente Corporativo</label>
            <input
              id="corp-client"
              v-model="corpForm.clientName"
              type="text"
              class="rg-input"
              placeholder="Ej: Banco Mercantil / Torre Caracas"
              required
            />
          </div>
          <div class="form-group w-30">
            <label for="corp-contract">Contrato / RIF</label>
            <input
              id="corp-contract"
              v-model="corpForm.contractCode"
              type="text"
              class="rg-input"
              placeholder="J-12345678-0"
            />
          </div>
        </div>

        <div class="form-row">
          <div class="form-group flex-1">
            <label for="corp-supernet">Supernet Padre (Bloque Proveedor)</label>
            <select id="corp-supernet" v-model="corpForm.baseSupernetId" class="rg-input">
              <option value="">Seleccionar Supernet IPv6...</option>
              <option v-for="sup in availableV6Supernets" :key="sup.id" :value="sup.id">
                {{ sup.prefix }} ({{ sup.description || 'Corporativo' }})
              </option>
            </select>
          </div>
          <div class="form-group w-30">
            <label for="corp-len">Tamaño de Bloque</label>
            <select id="corp-len" v-model.number="corpForm.prefixLength" class="rg-input">
              <option :value="48">/48 (Enterprise - 65k subredes)</option>
              <option :value="52">/52 (Medium - 4k subredes)</option>
              <option :value="56">/56 (Branch - 256 subredes)</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group flex-1">
            <label for="corp-dns">Delegación Reverse DNS (ip6.arpa NS)</label>
            <input
              id="corp-dns"
              v-model="corpForm.reverseDnsNs"
              type="text"
              class="rg-input"
              placeholder="ns1.dominio-cliente.com"
            />
          </div>
          <div class="form-group w-30">
            <label for="corp-asn">ASN Propio (BGP)</label>
            <input
              id="corp-asn"
              v-model="corpForm.bgpAsn"
              type="text"
              class="rg-input"
              placeholder="Ej: AS65100"
            />
          </div>
        </div>

        <!-- Preview del Prefijo -->
        <div class="preview-box">
          <div class="preview-label">Prefijo Asignado a Delegar:</div>
          <div class="preview-cidr">{{ calculatedPrefixPreview }}</div>
          <div class="preview-command-label">Comando RouterOS CLI generado:</div>
          <code class="preview-command">{{ generatedMikrotikCommand }}</code>
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn-rg btn-rg--secondary" @click="emit('close')">
            Cancelar
          </button>
          <button type="submit" class="btn-rg btn-rg--purple">✅ Delegar Bloque Corporativo</button>
        </footer>
      </form>
    </div>
  </div>
</template>

<style scoped>
  .rg-modal--corp {
    max-width: 620px;
  }

  .info-banner {
    background: rgba(138, 43, 226, 0.15);
    border-left: 3px solid #8a2be2;
    color: #e9d5ff;
    padding: 0.65rem 0.85rem;
    border-radius: 4px;
    font-size: 0.8rem;
    margin-bottom: 1rem;
  }

  .preview-box {
    margin: 1.25rem 0;
    padding: 0.85rem;
    background: #060a12;
    border: 1px solid rgba(138, 43, 226, 0.4);
    border-radius: 6px;
  }

  .preview-label {
    font-size: 0.75rem;
    color: #94a3b8;
    margin-bottom: 0.25rem;
  }

  .preview-cidr {
    font-family: monospace;
    font-size: 1.35rem;
    font-weight: 800;
    color: #c084fc;
    margin-bottom: 0.5rem;
  }

  .preview-command-label {
    font-size: 0.7rem;
    color: #64748b;
    margin-bottom: 0.2rem;
  }

  .preview-command {
    display: block;
    font-family: monospace;
    font-size: 0.75rem;
    background: #020617;
    color: #38bdf8;
    padding: 0.4rem 0.6rem;
    border-radius: 4px;
    overflow-x: auto;
  }
</style>
