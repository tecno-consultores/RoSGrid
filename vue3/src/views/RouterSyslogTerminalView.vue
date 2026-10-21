<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { http } from '@/api/httpClient';
import type { RouterSyslogResponse, SyslogEvent, SyslogTemplateResponse } from '@/types';

const route = useRoute();
const routerId = computed(() => String(route.params.routerId || ''));

const loading = ref(false);
const autoRefresh = ref(true);
const autoScroll = ref(true);
const syslogData = ref<RouterSyslogResponse | null>(null);
const errorMessage = ref<string | null>(null);

const searchQuery = ref('');
const selectedSeverity = ref('ALL');

// Modal de plantilla de enrolamiento
const isTemplateModalOpen = ref(false);
const templateLoading = ref(false);
const syslogTemplate = ref<SyslogTemplateResponse | null>(null);
const copiedToClipboard = ref(false);

const terminalContainerRef = ref<HTMLElement | null>(null);
let refreshInterval: number | null = null;

async function loadSyslogEvents(): Promise<void> {
  if (!routerId.value) return;
  loading.value = true;
  try {
    const res = await http.get<RouterSyslogResponse>(`/api/v1/routers/${routerId.value}/syslog?limit=200`);
    syslogData.value = res.data;
    if (autoScroll.value) {
      await nextTick();
      scrollToBottom();
    }
  } catch (err: unknown) {
    const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
    errorMessage.value = errorObj.response?.data?.detail || errorObj.message || 'Error al obtener eventos syslog.';
  } finally {
    loading.value = false;
  }
}

async function openTemplateModal(): Promise<void> {
  isTemplateModalOpen.value = true;
  templateLoading.value = true;
  copiedToClipboard.value = false;
  try {
    const res = await http.get<SyslogTemplateResponse>('/api/v1/routers/syslog/template');
    syslogTemplate.value = res.data;
  } catch (err: unknown) {
    const errorObj = err as { response?: { data?: { detail?: string } }; message?: string };
    alert(errorObj.response?.data?.detail || 'Error al cargar plantilla syslog.');
  } finally {
    templateLoading.value = false;
  }
}

function copyTemplateToClipboard(): void {
  if (!syslogTemplate.value) return;
  if (typeof navigator !== 'undefined' && navigator.clipboard) {
    navigator.clipboard.writeText(syslogTemplate.value.template_content);
    copiedToClipboard.value = true;
    setTimeout(() => {
      copiedToClipboard.value = false;
    }, 3000);
  }
}

const filteredEvents = computed<SyslogEvent[]>(() => {
  if (!syslogData.value || !syslogData.value.events) return [];
  let list = syslogData.value.events;

  if (selectedSeverity.value !== 'ALL') {
    list = list.filter((e) => e.severity.toUpperCase() === selectedSeverity.value);
  }

  const q = searchQuery.value.trim().toLowerCase();
  if (q) {
    list = list.filter(
      (e) =>
        e.message.toLowerCase().includes(q) ||
        e.topics.toLowerCase().includes(q) ||
        e.facility.toLowerCase().includes(q),
    );
  }
  return list;
});

function scrollToBottom(): void {
  const el = terminalContainerRef.value;
  if (el) {
    el.scrollTop = el.scrollHeight;
  }
}

function handleTerminalScroll(): void {
  const el = terminalContainerRef.value;
  if (!el) return;
  // Si el usuario subió, pausar autoscroll
  const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 30;
  autoScroll.value = isAtBottom;
}

function clearLocalBuffer(): void {
  if (syslogData.value) {
    syslogData.value.events = [];
    syslogData.value.total_events = 0;
    syslogData.value.critical_count = 0;
  }
}

onMounted(() => {
  loadSyslogEvents();
  refreshInterval = window.setInterval(() => {
    if (autoRefresh.value) {
      loadSyslogEvents();
    }
  }, 3000);
});

onBeforeUnmount(() => {
  if (refreshInterval !== null) {
    clearInterval(refreshInterval);
  }
});
</script>

<template>
  <div class="syslog-view">
    <header class="syslog-header">
      <div>
        <h2 class="syslog-title">Consola Syslog en Vivo (RingBuffer Efímero)</h2>
        <p class="syslog-subtitle">
          Recepción en tiempo real UDP/TCP 5514 BSD con retención de 500 eventos en KeyDB
        </p>
      </div>

      <div class="syslog-actions">
        <button
          type="button"
          class="btn-action btn-template"
          aria-label="Ver script CLI de enrolamiento RouterOS"
          @click="openTemplateModal"
        >
          <span aria-hidden="true">📋</span>
          <span>Script RouterOS</span>
        </button>

        <button
          type="button"
          class="btn-action btn-refresh"
          :disabled="loading"
          aria-label="Refrescar eventos syslog manualmente"
          @click="loadSyslogEvents"
        >
          <span aria-hidden="true">↻</span>
          <span>Refrescar</span>
        </button>

        <button
          type="button"
          class="btn-action btn-clear"
          aria-label="Limpiar pantalla de consola"
          @click="clearLocalBuffer"
        >
          <span>Limpiar</span>
        </button>
      </div>
    </header>

    <!-- Barra de Controles y Filtros -->
    <section class="syslog-controls" aria-label="Filtros y configuración de terminal">
      <div class="filter-item">
        <label for="syslog-search" class="visually-hidden">Buscar en logs</label>
        <input
          id="syslog-search"
          v-model="searchQuery"
          type="text"
          class="input-search"
          placeholder="Filtrar por mensaje, interfaz (ether1) o tópico..."
        />
      </div>

      <div class="filter-item">
        <label for="syslog-severity-filter" class="filter-label">Severidad:</label>
        <select id="syslog-severity-filter" v-model="selectedSeverity" class="select-filter">
          <option value="ALL">Todas las severidades</option>
          <option value="ERROR">ERROR / CRITICAL</option>
          <option value="WARNING">WARNING</option>
          <option value="INFO">INFO</option>
          <option value="DEBUG">DEBUG</option>
        </select>
      </div>

      <label class="toggle-label">
        <input v-model="autoRefresh" type="checkbox" />
        <span>Auto-refresco (3s)</span>
      </label>

      <label class="toggle-label">
        <input v-model="autoScroll" type="checkbox" />
        <span>Auto-scroll</span>
      </label>

      <div class="kpi-tag-wrap">
        <span class="badge-kpi">Eventos: {{ filteredEvents.length }}</span>
        <span v-if="syslogData?.critical_count" class="badge-kpi badge-kpi--crit">
          🚨 {{ syslogData.critical_count }} Críticos
        </span>
      </div>
    </section>

    <!-- Terminal de Logs -->
    <div
      ref="terminalContainerRef"
      class="terminal-container"
      role="log"
      aria-label="Consola de eventos Syslog"
      aria-live="polite"
      @scroll="handleTerminalScroll"
    >
      <div v-if="filteredEvents.length === 0" class="terminal-empty">
        <p>No hay eventos registrados en el RingBuffer para este router.</p>
        <p class="empty-hint">
          Asegúrate de haber configurado el reenvío en RouterOS con el
          <button type="button" class="btn-link" @click="openTemplateModal">Script de Enrolamiento</button>.
        </p>
      </div>

      <div v-else class="log-stream font-mono">
        <div
          v-for="(ev, idx) in filteredEvents"
          :key="`${ev.timestamp}-${idx}`"
          class="log-line"
          :class="[
            `log-line--${ev.severity.toLowerCase()}`,
            { 'log-line--critical': ev.is_critical },
          ]"
        >
          <span class="log-time tabular-nums">{{ ev.timestamp }}</span>
          <span class="log-badge-sev" :class="`sev--${ev.severity.toLowerCase()}`">
            {{ ev.severity.toUpperCase() }}
          </span>
          <span v-if="ev.is_critical" class="log-badge-crit">CRIT 🚨</span>
          <span class="log-topic">[{{ ev.topics }}]</span>
          <span class="log-msg">{{ ev.message }}</span>
        </div>
      </div>
    </div>

    <!-- Modal de Plantilla de Enrolamiento RouterOS -->
    <div v-if="isTemplateModalOpen" class="modal-backdrop" @click.self="isTemplateModalOpen = false">
      <div class="modal-dialog" role="dialog" aria-labelledby="modal-tpl-title" aria-modal="true">
        <div class="modal-header">
          <h3 id="modal-tpl-title" class="modal-title">Aprovisionamiento Syslog en RouterOS v7</h3>
          <button
            type="button"
            class="btn-close-modal"
            aria-label="Cerrar modal"
            @click="isTemplateModalOpen = false"
          >
            ✕
          </button>
        </div>

        <div class="modal-body">
          <p class="modal-desc">
            Aplica los siguientes comandos CLI en la terminal de tu equipo MikroTik para comenzar a
            reenviar eventos críticos (link down, advertencias de interfaces, logins y errores) hacia
            RoSGrid vía UDP en el puerto {{ syslogTemplate?.default_port || 5514 }}:
          </p>

          <pre class="cli-code-block font-mono"><code>{{ syslogTemplate?.template_content }}</code></pre>

          <div class="modal-footer">
            <button
              type="button"
              class="btn-copy-code"
              aria-label="Copiar comandos al portapapeles"
              @click="copyTemplateToClipboard"
            >
              <span>{{ copiedToClipboard ? '✅ ¡Copiado!' : '📋 Copiar al Portapapeles' }}</span>
            </button>
            <button type="button" class="btn-cancel" @click="isTemplateModalOpen = false">
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.syslog-view {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem;
  background-color: var(--rg-bg-canvas, #0b0f19);
  color: var(--rg-text-primary, #f8fafc);
  height: 100%;
  box-sizing: border-box;
}

.syslog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.syslog-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0 0 0.25rem 0;
  color: var(--rg-text-primary, #f8fafc);
}

.syslog-subtitle {
  font-size: 0.85rem;
  color: var(--rg-text-secondary, #cbd5e1);
  margin: 0;
}

.syslog-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-action {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.45rem 0.85rem;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid var(--rg-border-grid, #334155);
  transition: all 0.15s ease;
}

.btn-template {
  background-color: var(--rg-bg-elevated, #1e293b);
  color: var(--rg-accent-cyan, #22d3ee);
  border-color: var(--rg-accent-cyan, #22d3ee);
}

.btn-template:hover {
  background-color: rgba(34, 211, 238, 0.15);
}

.btn-refresh,
.btn-clear {
  background-color: var(--rg-bg-surface, #111827);
  color: var(--rg-text-secondary, #cbd5e1);
}

.btn-refresh:hover,
.btn-clear:hover {
  color: var(--rg-text-primary, #f8fafc);
  border-color: var(--rg-accent-cyan, #22d3ee);
}

.syslog-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
  background-color: var(--rg-bg-surface, #111827);
  padding: 0.65rem 1rem;
  border-radius: 8px;
  border: 1px solid var(--rg-border-grid, #1e293b);
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-label {
  font-size: 0.8rem;
  color: var(--rg-text-secondary, #cbd5e1);
}

.input-search,
.select-filter {
  background-color: var(--rg-bg-canvas, #0b0f19);
  border: 1px solid var(--rg-border-grid, #334155);
  border-radius: 6px;
  color: var(--rg-text-primary, #f8fafc);
  padding: 0.35rem 0.65rem;
  font-size: 0.825rem;
  outline: none;
}

.input-search {
  width: 280px;
}

.input-search:focus,
.select-filter:focus {
  border-color: var(--rg-accent-cyan, #22d3ee);
}

.toggle-label {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  color: var(--rg-text-secondary, #cbd5e1);
  cursor: pointer;
}

.kpi-tag-wrap {
  margin-left: auto;
  display: flex;
  gap: 0.5rem;
}

.badge-kpi {
  background-color: var(--rg-bg-canvas, #0b0f19);
  border: 1px solid var(--rg-border-grid, #1e293b);
  color: var(--rg-text-primary, #f8fafc);
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

.badge-kpi--crit {
  border-color: #ef4444;
  color: #f87171;
  background-color: rgba(239, 68, 68, 0.15);
  font-weight: 700;
}

.terminal-container {
  flex: 1;
  background-color: #070a12;
  border: 1px solid var(--rg-border-grid, #1e293b);
  border-radius: 8px;
  padding: 1rem;
  overflow-y: auto;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.6);
  min-height: 350px;
}

.terminal-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--rg-text-muted, #94a3b8);
  font-size: 0.875rem;
  text-align: center;
}

.empty-hint {
  font-size: 0.8rem;
  margin-top: 0.25rem;
}

.btn-link {
  background: transparent;
  border: none;
  color: var(--rg-accent-cyan, #22d3ee);
  text-decoration: underline;
  cursor: pointer;
  padding: 0;
  font-size: 0.8rem;
}

.log-stream {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.8rem;
  line-height: 1.4;
}

.log-line {
  display: flex;
  gap: 0.5rem;
  align-items: baseline;
  word-break: break-all;
  padding: 0.15rem 0.35rem;
  border-radius: 3px;
}

.log-line:hover {
  background-color: rgba(255, 255, 255, 0.04);
}

.log-line--error {
  color: #f87171;
}

.log-line--warning {
  color: #fbbf24;
}

.log-line--info {
  color: #e2e8f0;
}

.log-line--debug {
  color: #94a3b8;
}

.log-line--critical {
  background-color: rgba(239, 68, 68, 0.12);
  border-left: 2px solid #ef4444;
}

.log-time {
  color: var(--rg-text-muted, #94a3b8);
  font-size: 0.75rem;
  white-space: nowrap;
}

.log-badge-sev {
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
}

.sev--error {
  background-color: #ef4444;
  color: #ffffff;
}

.sev--warning {
  background-color: #f59e0b;
  color: #000000;
}

.sev--info {
  background-color: var(--rg-bg-elevated, #1e293b);
  color: var(--rg-accent-cyan, #22d3ee);
}

.sev--debug {
  background-color: #334155;
  color: #cbd5e1;
}

.log-badge-crit {
  background-color: #dc2626;
  color: #ffffff;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.1rem 0.35rem;
  border-radius: 3px;
  animation: pulse-crit 1.5s infinite;
}

@keyframes pulse-crit {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.log-topic {
  color: var(--rg-accent-cyan, #22d3ee);
  font-size: 0.75rem;
}

.log-msg {
  flex: 1;
}

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 1rem;
}

.modal-dialog {
  background-color: var(--rg-bg-surface, #111827);
  border: 1px solid var(--rg-border-grid, #334155);
  border-radius: 8px;
  width: 100%;
  max-width: 650px;
  overflow: hidden;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  background-color: var(--rg-bg-elevated, #1e293b);
  border-bottom: 1px solid var(--rg-border-grid, #334155);
}

.modal-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0;
  color: var(--rg-text-primary, #f8fafc);
}

.btn-close-modal {
  background: transparent;
  border: none;
  color: var(--rg-text-muted, #94a3b8);
  font-size: 1.2rem;
  cursor: pointer;
}

.modal-body {
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.modal-desc {
  font-size: 0.85rem;
  color: var(--rg-text-secondary, #cbd5e1);
  margin: 0;
  line-height: 1.4;
}

.cli-code-block {
  background-color: #070a12;
  border: 1px solid var(--rg-border-grid, #1e293b);
  border-radius: 6px;
  padding: 1rem;
  color: #38bdf8;
  font-size: 0.825rem;
  overflow-x: auto;
  white-space: pre-wrap;
  margin: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.btn-copy-code {
  background-color: #0284c7;
  color: #ffffff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
}

.btn-copy-code:hover {
  background-color: #0369a1;
}

.btn-cancel {
  background-color: var(--rg-bg-elevated, #1e293b);
  color: var(--rg-text-secondary, #cbd5e1);
  border: 1px solid var(--rg-border-grid, #334155);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
}

.font-mono {
  font-family: 'JetBrains Mono', 'Ubuntu Mono', monospace;
}

.tabular-nums {
  font-variant-numeric: tabular-nums;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
