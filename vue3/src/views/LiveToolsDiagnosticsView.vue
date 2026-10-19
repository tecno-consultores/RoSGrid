<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import { http } from '@/api/httpClient';
  import type { DiagnosticLogItem } from '@/types';

  interface DiagnosticRow {
    seq: number;
    host: string;
    size?: number;
    ttl?: number;
    time_ms: number;
    status: string;
  }

  const route = useRoute();
  const routerId = computed(() => String(route.params.routerId || ''));

  const activeTab = ref<'ping' | 'traceroute' | 'torch' | 'logs'>('ping');
  const targetHost = ref('8.8.8.8');
  const pingCount = ref(4);
  const selectedInterface = ref('ether1');
  const availableInterfaces = ref<string[]>(['ether1']);
  const isRunning = ref(false);

  const pingResults = ref<DiagnosticRow[]>([]);
  const logEntries = ref<DiagnosticLogItem[]>([]);

  async function loadRealInterfaces() {
    if (!routerId.value) return;
    try {
      const res = await http.get<Array<{ name?: string }> | { items: Array<{ name?: string }> }>(
        `/api/v1/routers/${routerId.value}/webfig/interfaces`,
      );
      const raw = Array.isArray(res.data) ? res.data : res.data?.items || [];
      const names = raw.map((i) => i.name).filter(Boolean) as string[];
      if (names.length > 0) {
        availableInterfaces.value = names;
        if (!names.includes(selectedInterface.value)) {
          selectedInterface.value = names[0];
        }
      }
    } catch {
      // Mantiene lista por defecto
    }
  }

  async function runDiagnostic() {
    isRunning.value = true;
    pingResults.value = [];
    try {
      const payload: Record<string, any> = {};
      if (activeTab.value === 'ping') {
        payload.address = targetHost.value.trim();
        payload.count = Number(pingCount.value) || 4;
        payload.size = 64;
      } else if (activeTab.value === 'traceroute') {
        payload.address = targetHost.value.trim();
        payload.count = 3;
      } else if (activeTab.value === 'torch') {
        payload.interface = selectedInterface.value;
        payload.duration_seconds = 3;
      }

      const res = await http.post<any>(
        `/api/v1/routers/${routerId.value}/webfig/tools/${activeTab.value}`,
        payload,
      );

      if (activeTab.value === 'ping') {
        const items = res.data?.results || (Array.isArray(res.data) ? res.data : []);
        pingResults.value = items.map((r: any, idx: number) => ({
          seq: r.seq !== undefined ? Number(r.seq) + 1 : idx + 1,
          host: r.host || r.address || targetHost.value,
          size: r.size ? Number(r.size) : 56,
          ttl: r.ttl ? Number(r.ttl) : 64,
          time_ms: r.time || r['avg-rtt'] || `${r.time_ms ?? 0} ms`,
          status: r.status || (r.loss === '100' ? 'timeout' : 'ok'),
        }));
      } else if (activeTab.value === 'traceroute') {
        const items = Array.isArray(res.data) ? res.data : res.data?.results || [];
        pingResults.value = items
          .filter((r: any) => r.address || r.last)
          .map((r: any, idx: number) => ({
            seq: r['.section'] ? Number(r['.section']) : idx + 1,
            host: r.address || '(sin respuesta)',
            size: 56,
            ttl: idx + 1,
            time_ms: r.avg ? `${r.avg} ms` : r.last || '*',
            status: r.loss === '100' ? 'timeout' : 'ok',
          }));
      } else if (activeTab.value === 'torch') {
        const items = Array.isArray(res.data) ? res.data : res.data?.results || [];
        pingResults.value = items.map((r: any, idx: number) => ({
          seq: idx + 1,
          host: `${r['src-address'] || '*'}:${r['src-port'] || '*'} -> ${r['dst-address'] || '*'}:${r['dst-port'] || '*'}`,
          size: Number(r.rx || 0) + Number(r.tx || 0),
          ttl: Number(r['rx-packets'] || 0) + Number(r['tx-packets'] || 0),
          time_ms: r['ip-protocol'] || r['mac-protocol'] || 'ip',
          status: `${r.tx || 0} TX / ${r.rx || 0} RX`,
        }));
      }
    } catch {
      pingResults.value = [];
    } finally {
      isRunning.value = false;
    }
  }

  async function loadLogs() {
    try {
      const res = await http.get<DiagnosticLogItem[] | { items: DiagnosticLogItem[] }>(
        `/api/v1/routers/${routerId.value}/webfig/tools/logs`,
      );
      const raw = Array.isArray(res.data) ? res.data : res.data?.items || [];
      logEntries.value = raw.map((l: any, idx: number) => ({
        id: l.id || l['.id'] || String(idx),
        time: l.time || '',
        topics: l.topics || 'system',
        message: l.message || '',
        severity: String(l.topics || '').includes('error')
          ? 'error'
          : String(l.topics || '').includes('warning')
            ? 'warning'
            : 'info',
      }));
    } catch {
      logEntries.value = [];
    }
  }

  function getSeverityClass(sev: string): string {
    if (sev === 'critical' || sev === 'error') return 'log--critical';
    if (sev === 'warning') return 'log--warning';
    return 'log--info';
  }

  onMounted(() => {
    loadRealInterfaces();
    loadLogs();
  });
</script>

<template>
  <div class="diagnostics-view">
    <header class="view-header">
      <div>
        <h2 class="view-title">Herramientas de Diagnóstico & Registro del Router</h2>
        <p class="view-subtitle">
          Ejecución acotada de Ping, Traceroute, Torch y visualización del Log de eventos
        </p>
      </div>

      <nav class="subtabs-bar" role="tablist" aria-label="Herramientas disponibles">
        <button
          v-for="tool in [
            { id: 'ping', label: 'Ping' },
            { id: 'traceroute', label: 'Traceroute' },
            { id: 'torch', label: 'Torch en Vivo' },
            { id: 'logs', label: 'Router Log' },
          ]"
          :key="tool.id"
          type="button"
          class="btn-subtab"
          :class="{ 'btn-subtab--active': activeTab === tool.id }"
          role="tab"
          :aria-selected="activeTab === tool.id"
          @click="
            activeTab = tool.id as any;
            if (activeTab === 'logs') loadLogs();
          "
        >
          {{ tool.label }}
        </button>
      </nav>
    </header>

    <!-- Panel de Ejecución de Ping / Traceroute / Torch -->
    <div v-if="activeTab !== 'logs'" class="tool-runner-card">
      <form class="runner-form" @submit.prevent="runDiagnostic">
        <div v-if="activeTab !== 'torch'" class="form-group">
          <label for="diag-target" class="form-label">Destino (IP / Hostname):</label>
          <input
            id="diag-target"
            v-model="targetHost"
            type="text"
            required
            class="form-input font-tabular"
            placeholder="ej. 8.8.8.8 o core.isp.net"
          />
        </div>

        <div v-if="activeTab === 'ping'" class="form-group">
          <label for="diag-count" class="form-label">Paquetes:</label>
          <input
            id="diag-count"
            v-model.number="pingCount"
            type="number"
            min="1"
            max="10"
            class="form-input font-tabular input-small"
          />
        </div>

        <div v-if="activeTab === 'torch'" class="form-group">
          <label for="diag-iface" class="form-label">Interfaz:</label>
          <select id="diag-iface" v-model="selectedInterface" class="form-input font-tabular">
            <option v-for="iface in availableInterfaces" :key="iface" :value="iface">
              {{ iface }}
            </option>
          </select>
        </div>

        <button type="submit" class="btn-primary" :disabled="isRunning">
          <span v-if="isRunning">⏳ Ejecutando...</span>
          <span v-else>🚀 Iniciar {{ activeTab.toUpperCase() }}</span>
        </button>
      </form>

      <!-- Tabla de Resultados de la Herramienta -->
      <div v-if="pingResults.length > 0" class="results-table-container font-tabular">
        <table class="rg-table" aria-label="Resultados de la prueba">
          <thead>
            <tr>
              <th scope="col"># Seq</th>
              <th scope="col">Host</th>
              <th scope="col">Tamaño</th>
              <th scope="col">TTL</th>
              <th scope="col">Latencia</th>
              <th scope="col">Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in pingResults" :key="row.seq">
              <td>{{ row.seq }}</td>
              <td>{{ row.host }}</td>
              <td>{{ row.size || 56 }} B</td>
              <td>{{ row.ttl || 64 }}</td>
              <td class="text-cyan font-bold">{{ row.time_ms }} ms</td>
              <td>
                <span class="badge-status-ok">{{ row.status }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Panel de Log del Router -->
    <div v-if="activeTab === 'logs'" class="logs-card font-tabular">
      <div class="logs-container">
        <div
          v-for="log in logEntries"
          :key="log.id"
          class="log-row"
          :class="getSeverityClass(log.severity)"
        >
          <span class="log-time">{{ log.time }}</span>
          <span class="log-topics">[{{ log.topics }}]</span>
          <span class="log-msg">{{ log.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .diagnostics-view {
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

  .subtabs-bar {
    display: flex;
    gap: 4px;
    background: var(--rg-bg-canvas);
    padding: 3px;
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
  }

  .btn-subtab {
    background: transparent;
    border: none;
    color: var(--rg-text-secondary);
    padding: 5px 12px;
    font-size: 0.78rem;
    border-radius: 4px;
    cursor: pointer;
  }

  .btn-subtab--active {
    background: var(--rg-bg-elevated);
    color: var(--rg-accent-cyan);
    font-weight: 600;
  }

  .tool-runner-card,
  .logs-card {
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-grid);
    border-radius: 8px;
    padding: 16px;
  }

  .runner-form {
    display: flex;
    align-items: flex-end;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 16px;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .form-label {
    font-size: 0.75rem;
    color: var(--rg-text-muted);
  }

  .form-input {
    padding: 6px 10px;
    background: var(--rg-bg-elevated);
    border: 1px solid var(--rg-border-grid);
    border-radius: 6px;
    color: var(--rg-text-primary);
    font-size: 0.85rem;
  }

  .input-small {
    width: 80px;
  }

  .btn-primary {
    padding: 7px 16px;
    background: var(--rg-accent-cyan);
    border: none;
    border-radius: 6px;
    color: #0b0f19;
    font-weight: 700;
    cursor: pointer;
    font-size: 0.85rem;
  }

  .btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .results-table-container {
    overflow-x: auto;
  }

  .rg-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
  }

  .rg-table th,
  .rg-table td {
    padding: 8px 12px;
    border: 1px solid var(--rg-border-grid);
    text-align: left;
  }

  .badge-status-ok {
    color: #10b981;
  }

  .logs-container {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 0.8rem;
    background: #060911;
    padding: 12px;
    border-radius: 6px;
    max-height: 400px;
    overflow-y: auto;
  }

  .log-row {
    display: flex;
    gap: 8px;
    padding: 2px 4px;
  }

  .log-time {
    color: var(--rg-text-muted);
    min-width: 70px;
  }

  .log-topics {
    color: #38bdf8;
    min-width: 130px;
  }

  .log--info {
    color: var(--rg-text-secondary);
  }

  .log--warning {
    color: #f59e0b;
    background: rgba(245, 158, 11, 0.08);
  }

  .log--critical {
    color: #ef4444;
    background: rgba(239, 68, 68, 0.12);
    font-weight: 600;
  }

  .font-tabular {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
  }

  .text-cyan {
    color: var(--rg-accent-cyan);
  }

  .font-bold {
    font-weight: 700;
  }
</style>
