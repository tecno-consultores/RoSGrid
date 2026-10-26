<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, watch, computed } from 'vue';
  import type { FirewallRuleItem } from '@/types';

  const props = defineProps<{
    isOpen: boolean;
    isEditing: boolean;
    tableType: 'filter' | 'nat' | 'mangle' | 'raw';
    initialRule?: FirewallRuleItem | null;
    existingRules: FirewallRuleItem[];
  }>();

  const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'save', payload: Record<string, any>): void;
  }>();

  const chain = ref('forward');
  const action = ref('accept');
  const protocol = ref('any');
  const srcAddress = ref('');
  const dstAddress = ref('');
  const srcPort = ref('');
  const dstPort = ref('');
  const inInterface = ref('');
  const outInterface = ref('');
  const toAddresses = ref('');
  const toPorts = ref('');
  const placeBefore = ref('');
  const comment = ref('');
  const disabled = ref(false);

  // Opciones de cadena según el tipo de tabla
  const chainOptions = computed(() => {
    switch (props.tableType) {
      case 'nat':
        return [
          { value: 'srcnat', label: 'srcnat (Tráfico Saliente / Masquerade)' },
          { value: 'dstnat', label: 'dstnat (Tráfico Entrante / Port Forwarding)' },
        ];
      case 'mangle':
        return [
          { value: 'prerouting', label: 'prerouting' },
          { value: 'input', label: 'input' },
          { value: 'forward', label: 'forward' },
          { value: 'output', label: 'output' },
          { value: 'postrouting', label: 'postrouting' },
        ];
      case 'raw':
        return [
          { value: 'prerouting', label: 'prerouting' },
          { value: 'output', label: 'output' },
        ];
      case 'filter':
      default:
        return [
          { value: 'input', label: 'input (Tráfico hacia el propio Router)' },
          { value: 'forward', label: 'forward (Tráfico cruzando el Router)' },
          { value: 'output', label: 'output (Tráfico originado en el Router)' },
        ];
    }
  });

  // Opciones de acción según el tipo de tabla
  const actionOptions = computed(() => {
    switch (props.tableType) {
      case 'nat':
        return [
          { value: 'masquerade', label: 'masquerade (Enmascaramiento Dinámico)' },
          { value: 'dst-nat', label: 'dst-nat (Reenvío a Servidor Interno)' },
          { value: 'src-nat', label: 'src-nat (Traducción a IP Pública Estática)' },
          { value: 'redirect', label: 'redirect (Redirección a Puerto Local)' },
        ];
      case 'mangle':
        return [
          { value: 'mark-packet', label: 'mark-packet (Marcar Paquete para QoS)' },
          { value: 'mark-connection', label: 'mark-connection (Marcar Conexión)' },
          { value: 'mark-routing', label: 'mark-routing (Marcar para Policy Routing)' },
          { value: 'change-mss', label: 'change-mss (Ajuste MSS TCP / VPN)' },
          { value: 'accept', label: 'accept' },
        ];
      case 'raw':
        return [
          { value: 'drop', label: 'drop (Descarte en Silicio / Anti-DDoS)' },
          { value: 'accept', label: 'accept' },
          { value: 'jump', label: 'jump (Saltar a Cadena Personalizada)' },
        ];
      case 'filter':
      default:
        return [
          { value: 'accept', label: 'accept (Permitir)' },
          { value: 'drop', label: 'drop (Descartar Silenciosamente)' },
          { value: 'reject', label: 'reject (Rechazar con Notificación ICMP)' },
          { value: 'fasttrack-connection', label: 'fasttrack-connection (Aceleración L3HW)' },
          { value: 'jump', label: 'jump (Saltar a Cadena Personalizada)' },
          { value: 'return', label: 'return (Volver de Cadena)' },
          { value: 'log', label: 'log (Solo Registrar en Syslog)' },
        ];
    }
  });

  const isInputDropCritical = computed(() => {
    return chain.value === 'input' && (action.value === 'drop' || action.value === 'reject');
  });

  watch(
    () => props.isOpen,
    (open) => {
      if (open) {
        if (props.isEditing && props.initialRule) {
          const r = props.initialRule as any;
          chain.value = r.chain || chainOptions.value[0]?.value || 'forward';
          action.value = r.action || actionOptions.value[0]?.value || 'accept';
          protocol.value = r.protocol || 'any';
          srcAddress.value = r.src_address || '';
          dstAddress.value = r.dst_address || '';
          srcPort.value = r.src_port || '';
          dstPort.value = r.dst_port || '';
          inInterface.value = r.in_interface || '';
          outInterface.value = r.out_interface || '';
          toAddresses.value = r.to_addresses || '';
          toPorts.value = r.to_ports || '';
          comment.value = r.comment || '';
          disabled.value = Boolean(r.disabled);
          placeBefore.value = '';
        } else {
          // Valores por defecto al crear
          chain.value = chainOptions.value[0]?.value || 'forward';
          action.value = actionOptions.value[0]?.value || 'accept';
          protocol.value = 'any';
          srcAddress.value = '';
          dstAddress.value = '';
          srcPort.value = '';
          dstPort.value = '';
          inInterface.value = '';
          outInterface.value = '';
          toAddresses.value = '';
          toPorts.value = '';
          comment.value = '';
          disabled.value = false;
          placeBefore.value = '';
        }
      }
    },
    { immediate: true },
  );

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      emit('close');
    }
  }

  function handleSubmit() {
    const payload: Record<string, any> = {
      chain: chain.value,
      action: action.value,
      disabled: disabled.value,
    };

    if (protocol.value && protocol.value !== 'any') payload.protocol = protocol.value;
    if (srcAddress.value.trim()) payload.src_address = srcAddress.value.trim();
    if (dstAddress.value.trim()) payload.dst_address = dstAddress.value.trim();
    if (srcPort.value.trim()) payload.src_port = srcPort.value.trim();
    if (dstPort.value.trim()) payload.dst_port = dstPort.value.trim();
    if (inInterface.value.trim()) payload.in_interface = inInterface.value.trim();
    if (outInterface.value.trim()) payload.out_interface = outInterface.value.trim();
    if (comment.value.trim()) payload.comment = comment.value.trim();

    // Parámetros NAT
    if (action.value === 'dst-nat') {
      if (toAddresses.value.trim()) payload.to_addresses = toAddresses.value.trim();
      if (toPorts.value.trim()) payload.to_ports = toPorts.value.trim();
    } else if (action.value === 'src-nat') {
      if (toAddresses.value.trim()) payload.to_addresses = toAddresses.value.trim();
    }

    // Posicionamiento antes de otra regla
    if (!props.isEditing && placeBefore.value) {
      payload.place_before = placeBefore.value;
    }

    emit('save', payload);
  }
</script>

<template>
  <div
    v-if="isOpen"
    class="modal-backdrop"
    role="dialog"
    aria-modal="true"
    aria-labelledby="rule-modal-title"
    @keydown="handleKeydown"
  >
    <div class="modal-card" @click.stop>
      <header class="modal-header">
        <div>
          <h3 id="rule-modal-title" class="modal-title">
            {{ isEditing ? 'Editar Regla de Firewall' : 'Nueva Regla de Firewall' }}
            <span class="table-badge">[{{ tableType.toUpperCase() }}]</span>
          </h3>
          <p class="modal-subtitle">
            Configuración atómica con protección Safe Mode (60s Dead Man's Switch)
          </p>
        </div>
        <button
          type="button"
          class="btn-close"
          aria-label="Cerrar modal"
          @click="emit('close')"
        >
          ✕
        </button>
      </header>

      <!-- Alerta crítica ante regla drop en input -->
      <div v-if="isInputDropCritical" class="critical-warning" role="alert">
        <span class="warning-icon">⚠️</span>
        <div class="warning-text">
          <strong>Regla Crítica de Entrada (Input Drop):</strong>
          Puede interrumpir la conexión de RoSGrid si no permite el puerto REST/HTTPS. Se activará Safe Mode obligatorio de 60s. Si tu rol es menor a Support L3, requerirá aprobación Maker-Checker.
        </div>
      </div>

      <form class="modal-form" @submit.prevent="handleSubmit">
        <div class="form-grid">
          <!-- Cadena (Chain) -->
          <div class="form-group">
            <label for="rule-chain" class="form-label">Cadena (Chain) *</label>
            <select id="rule-chain" v-model="chain" class="form-select font-tabular" required>
              <option v-for="opt in chainOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>

          <!-- Acción (Action) -->
          <div class="form-group">
            <label for="rule-action" class="form-label">Acción (Action) *</label>
            <select id="rule-action" v-model="action" class="form-select font-tabular" required>
              <option v-for="opt in actionOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>

          <!-- Protocolo -->
          <div class="form-group">
            <label for="rule-protocol" class="form-label">Protocolo</label>
            <select id="rule-protocol" v-model="protocol" class="form-select font-tabular">
              <option value="any">Cualquiera (Any)</option>
              <option value="tcp">tcp (6)</option>
              <option value="udp">udp (17)</option>
              <option value="icmp">icmp (1)</option>
              <option value="gre">gre (47)</option>
              <option value="esp">esp (50)</option>
            </select>
          </div>

          <!-- Src Address -->
          <div class="form-group">
            <label for="rule-src-addr" class="form-label">Dirección Origen (Src Address)</label>
            <input
              id="rule-src-addr"
              v-model="srcAddress"
              type="text"
              class="form-input font-tabular"
              placeholder="Ej: 192.168.88.0/24 o 10.0.0.5"
            />
          </div>

          <!-- Dst Address -->
          <div class="form-group">
            <label for="rule-dst-addr" class="form-label">Dirección Destino (Dst Address)</label>
            <input
              id="rule-dst-addr"
              v-model="dstAddress"
              type="text"
              class="form-input font-tabular"
              placeholder="Ej: 0.0.0.0/0 o 8.8.8.8"
            />
          </div>

          <!-- Dst Port (solo si proto es tcp o udp) -->
          <div class="form-group">
            <label for="rule-dst-port" class="form-label">Puerto Destino (Dst Port)</label>
            <input
              id="rule-dst-port"
              v-model="dstPort"
              type="text"
              class="form-input font-tabular"
              placeholder="Ej: 80,443 o 1000-2000"
            />
          </div>

          <!-- In-Interface -->
          <div class="form-group">
            <label for="rule-in-iface" class="form-label">Interfaz Entrada (In-Interface)</label>
            <input
              id="rule-in-iface"
              v-model="inInterface"
              type="text"
              class="form-input font-tabular"
              placeholder="Ej: ether1, bridge1, wan"
            />
          </div>

          <!-- Out-Interface -->
          <div class="form-group">
            <label for="rule-out-iface" class="form-label">Interfaz Salida (Out-Interface)</label>
            <input
              id="rule-out-iface"
              v-model="outInterface"
              type="text"
              class="form-input font-tabular"
              placeholder="Ej: ether1, sfp-sfpplus1"
            />
          </div>

          <!-- Campos condicionales para Dst-NAT -->
          <template v-if="action === 'dst-nat'">
            <div class="form-group">
              <label for="rule-to-addr" class="form-label">IP Servidor Interno (To Addresses) *</label>
              <input
                id="rule-to-addr"
                v-model="toAddresses"
                type="text"
                class="form-input font-tabular"
                placeholder="Ej: 192.168.88.50"
                required
              />
            </div>
            <div class="form-group">
              <label for="rule-to-ports" class="form-label">Puerto Interno (To Ports)</label>
              <input
                id="rule-to-ports"
                v-model="toPorts"
                type="text"
                class="form-input font-tabular"
                placeholder="Ej: 80 (opcional si es idéntico)"
              />
            </div>
          </template>

          <!-- Posicionamiento place-before (solo al crear) -->
          <div v-if="!isEditing && existingRules.length > 0" class="form-group form-group--full">
            <label for="rule-place-before" class="form-label">Posicionar Antes de la Regla (Place-Before):</label>
            <select id="rule-place-before" v-model="placeBefore" class="form-select font-tabular">
              <option value="">Al final de la tabla (predeterminado)</option>
              <option
                v-for="r in existingRules"
                :key="r.id"
                :value="r.id"
              >
                Regla {{ r.id }} — [{{ r.chain }}] {{ r.action }} ({{ r.comment || 'Sin comentario' }})
              </option>
            </select>
          </div>

          <!-- Comentario Obligatorio -->
          <div class="form-group form-group--full">
            <label for="rule-comment" class="form-label">Comentario de Auditoría WORM *</label>
            <input
              id="rule-comment"
              v-model="comment"
              type="text"
              class="form-input"
              placeholder="Ej: Permitir acceso HTTPS desde NOC Central"
              required
            />
          </div>

          <!-- Switch Deshabilitada -->
          <div class="form-group form-group--full">
            <label class="checkbox-label">
              <input v-model="disabled" type="checkbox" class="form-checkbox" />
              <span>Crear regla deshabilitada inicialmente (disabled=yes)</span>
            </label>
          </div>
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn-cancel" @click="emit('close')">
            Cancelar
          </button>
          <button type="submit" class="btn-submit">
            {{ isEditing ? 'Guardar Cambios' : 'Aplicar Regla con Safe Mode' }}
          </button>
        </footer>
      </form>
    </div>
  </div>
</template>

<style scoped>
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(5, 10, 20, 0.85);
    backdrop-filter: blur(4px);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    padding: 16px;
    box-sizing: border-box;
  }

  .modal-card {
    background-color: var(--rg-bg-card, #0d1527);
    border: 1px solid var(--rg-border, #1e293b);
    border-radius: var(--rg-radius-lg, 12px);
    width: 100%;
    max-width: 680px;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
    display: flex;
    flex-direction: column;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 16px 20px;
    border-bottom: 1px solid var(--rg-border, #1e293b);
  }

  .modal-title {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--rg-text-primary, #f8fafc);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .table-badge {
    background-color: rgba(0, 210, 255, 0.15);
    color: var(--rg-accent-cyan, #00d2ff);
    font-size: 0.8rem;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: monospace;
  }

  .modal-subtitle {
    margin: 4px 0 0 0;
    font-size: 0.82rem;
    color: var(--rg-text-secondary, #94a3b8);
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-secondary, #94a3b8);
    font-size: 1.25rem;
    cursor: pointer;
    line-height: 1;
    padding: 4px;
  }

  .btn-close:hover {
    color: var(--rg-text-primary, #f8fafc);
  }

  .critical-warning {
    margin: 16px 20px 0 20px;
    background-color: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    border-radius: var(--rg-radius-md, 8px);
    padding: 12px;
    display: flex;
    gap: 10px;
    align-items: flex-start;
    color: #fca5a5;
    font-size: 0.85rem;
  }

  .modal-form {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .form-group--full {
    grid-column: 1 / -1;
  }

  .form-label {
    display: block;
    margin-bottom: 6px;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--rg-text-secondary, #94a3b8);
  }

  .form-input,
  .form-select {
    width: 100%;
    padding: 8px 12px;
    background-color: var(--rg-bg-input, #090e1a);
    border: 1px solid var(--rg-border, #1e293b);
    border-radius: var(--rg-radius-md, 8px);
    color: var(--rg-text-primary, #f8fafc);
    font-size: 0.9rem;
    box-sizing: border-box;
    transition: border-color 0.2s;
  }

  .form-input:focus,
  .form-select:focus {
    outline: none;
    border-color: var(--rg-accent-cyan, #00d2ff);
  }

  .font-tabular {
    font-family: monospace;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    color: var(--rg-text-secondary, #94a3b8);
    cursor: pointer;
  }

  .form-checkbox {
    width: 16px;
    height: 16px;
    accent-color: var(--rg-accent-cyan, #00d2ff);
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--rg-border, #1e293b);
  }

  .btn-cancel {
    padding: 8px 16px;
    background-color: transparent;
    border: 1px solid var(--rg-border, #1e293b);
    border-radius: var(--rg-radius-md, 8px);
    color: var(--rg-text-secondary, #94a3b8);
    font-weight: 600;
    cursor: pointer;
  }

  .btn-cancel:hover {
    background-color: rgba(255, 255, 255, 0.05);
  }

  .btn-submit {
    padding: 8px 20px;
    background: linear-gradient(135deg, #00d2ff, #0077b6);
    border: none;
    border-radius: var(--rg-radius-md, 8px);
    color: #ffffff;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 210, 255, 0.3);
  }

  .btn-submit:hover {
    filter: brightness(1.1);
  }

  @media (max-width: 600px) {
    .form-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
