<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { onMounted, ref } from 'vue';
  import { http } from '@/api/httpClient';
  import { useI18n } from '@/composables/useI18n';
  import { useDiagnosticsCollector } from '@/composables/useDiagnosticsCollector';

  export type BundleFormat = 'zip' | 'tar.gz';
  export type SiemProtocol = 'GELF_UDP' | 'GELF_HTTP' | 'SYSLOG_UDP' | 'SYSLOG_TCP' | 'LOKI_HTTP';
  export type SiemMinLevel = 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';

  interface DiagnosticBundleResponse {
    filename: string;
    format: BundleFormat;
    content_type: string;
    size_bytes: number;
    redacted_secrets_count: number;
    included_files: string[];
    generated_at: string;
    bundle_base64: string;
  }

  interface SiemConfigResponse {
    enabled: boolean;
    protocol: SiemProtocol;
    host: string;
    port: number;
    endpoint_path: string;
    use_tls: boolean;
    min_level: SiemMinLevel;
    include_frontend_errors: boolean;
    include_audit_events: boolean;
    custom_stream_label: string;
    has_auth_token: boolean;
    updated_at: string | null;
  }

  interface SiemTestResponse {
    success: boolean;
    protocol: SiemProtocol;
    target: string;
    latency_ms: number;
    detail: string;
  }

  const { t } = useI18n();
  const { uiDiagnosticBuffer, pushDiagnosticEvent, reportDiagnosticEventToBackend } =
    useDiagnosticsCollector();

  const bundleFormat = ref<BundleFormat>('zip');
  const logLinesLimit = ref<number>(500);
  const operatorNotes = ref<string>('');
  const isGeneratingBundle = ref<boolean>(false);
  const lastBundleResult = ref<DiagnosticBundleResponse | null>(null);

  const siemEnabled = ref<boolean>(false);
  const siemProtocol = ref<SiemProtocol>('GELF_UDP');
  const siemHost = ref<string>('127.0.0.1');
  const siemPort = ref<number>(12201);
  const siemEndpointPath = ref<string>('/gelf');
  const siemUseTls = ref<boolean>(false);
  const siemMinLevel = ref<SiemMinLevel>('WARNING');
  const siemIncludeFrontend = ref<boolean>(true);
  const siemIncludeAudit = ref<boolean>(true);
  const siemStreamLabel = ref<string>('rosgrid-noc');
  const siemAuthToken = ref<string>('');
  const siemHasSavedToken = ref<boolean>(false);

  const isLoadingConfig = ref<boolean>(false);
  const isSavingSiem = ref<boolean>(false);
  const isTestingSiem = ref<boolean>(false);
  const siemTestResult = ref<SiemTestResponse | null>(null);
  const feedbackSuccess = ref<string>('');
  const feedbackError = ref<string>('');

  function applySiemConfigState(cfg: SiemConfigResponse) {
    siemEnabled.value = cfg.enabled;
    siemProtocol.value = cfg.protocol;
    siemHost.value = cfg.host;
    siemPort.value = cfg.port;
    siemEndpointPath.value = cfg.endpoint_path;
    siemUseTls.value = cfg.use_tls;
    siemMinLevel.value = cfg.min_level;
    siemIncludeFrontend.value = cfg.include_frontend_errors;
    siemIncludeAudit.value = cfg.include_audit_events;
    siemStreamLabel.value = cfg.custom_stream_label;
    siemHasSavedToken.value = cfg.has_auth_token;
  }

  async function loadSiemConfiguration() {
    isLoadingConfig.value = true;
    feedbackError.value = '';
    try {
      const res = await http.get<SiemConfigResponse>('/api/v1/system/siem-config');
      applySiemConfigState(res.data);
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      feedbackError.value = e.detail || e.message || 'Error al consultar configuración SIEM.';
    } finally {
      isLoadingConfig.value = false;
    }
  }

  function triggerBase64Download(base64Data: string, filename: string, contentType: string) {
    if (typeof window === 'undefined' || typeof document === 'undefined') return;
    const link = document.createElement('a');
    link.href = `data:${contentType};base64,${base64Data}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  async function handleGenerateSupportBundle() {
    isGeneratingBundle.value = true;
    feedbackError.value = '';
    feedbackSuccess.value = '';
    try {
      if (operatorNotes.value.trim()) {
        const manualItem = pushDiagnosticEvent({
          category: 'MANUAL_NOTE',
          message: operatorNotes.value.trim(),
        });
        await reportDiagnosticEventToBackend(manualItem);
      }
      const res = await http.post<DiagnosticBundleResponse>('/api/v1/system/diagnostics/bundle', {
        format: bundleFormat.value,
        log_lines_limit: logLinesLimit.value,
        operator_notes: operatorNotes.value.trim() || null,
        include_frontend_buffer: uiDiagnosticBuffer.value,
      });
      lastBundleResult.value = res.data;
      triggerBase64Download(res.data.bundle_base64, res.data.filename, res.data.content_type);
      feedbackSuccess.value = `Paquete ${res.data.filename} generado (${res.data.redacted_secrets_count} secretos sanitizados).`;
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      feedbackError.value = e.detail || e.message || 'Error al generar paquete de diagnóstico.';
    } finally {
      isGeneratingBundle.value = false;
    }
  }

  async function handleSaveSiemConfig() {
    isSavingSiem.value = true;
    feedbackError.value = '';
    feedbackSuccess.value = '';
    try {
      const res = await http.put<SiemConfigResponse>('/api/v1/system/siem-config', {
        enabled: siemEnabled.value,
        protocol: siemProtocol.value,
        host: siemHost.value,
        port: Number(siemPort.value),
        endpoint_path: siemEndpointPath.value,
        use_tls: siemUseTls.value,
        min_level: siemMinLevel.value,
        include_frontend_errors: siemIncludeFrontend.value,
        include_audit_events: siemIncludeAudit.value,
        custom_stream_label: siemStreamLabel.value,
        auth_token: siemAuthToken.value || null,
      });
      applySiemConfigState(res.data);
      siemAuthToken.value = '';
      feedbackSuccess.value = 'Configuración del conector SIEM del ISP guardada correctamente.';
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      feedbackError.value = e.detail || e.message || 'Error al guardar configuración SIEM.';
    } finally {
      isSavingSiem.value = false;
    }
  }

  async function handleTestSiemDelivery() {
    isTestingSiem.value = true;
    feedbackError.value = '';
    siemTestResult.value = null;
    try {
      const res = await http.post<SiemTestResponse>('/api/v1/system/siem-config/test', {});
      siemTestResult.value = res.data;
      if (res.data.success) {
        feedbackSuccess.value = `${res.data.detail} (${res.data.latency_ms} ms)`;
      } else {
        feedbackError.value = res.data.detail;
      }
    } catch (err: unknown) {
      const e = err as { detail?: string; message?: string };
      feedbackError.value = e.detail || e.message || 'Fallo al ejecutar prueba SIEM.';
    } finally {
      isTestingSiem.value = false;
    }
  }

  onMounted(() => {
    loadSiemConfiguration();
  });
</script>

<template>
  <div class="diagnostics-siem-panel">
    <div v-if="feedbackError" class="diag-alert diag-alert-error" role="alert">
      ⚠️ {{ feedbackError }}
    </div>
    <div v-if="feedbackSuccess" class="diag-alert diag-alert-success" role="status">
      ✅ {{ feedbackSuccess }}
    </div>

    <div class="diag-grid">
      <!-- Card 1: 1-Click Support Bundle -->
      <section class="diag-card" aria-labelledby="bundle-card-title">
        <header class="diag-card-header">
          <div>
            <h2 id="bundle-card-title" class="diag-card-title">
              📦
              {{
                t(
                  'enterprise.diag_bundle_title',
                  'Paquete de Soporte y Diagnóstico Unificado (1-Click Bundle)',
                )
              }}
            </h2>
            <p class="diag-card-subtitle">
              {{
                t(
                  'enterprise.diag_bundle_desc',
                  'Recopila trazas del navegador (Frontend), logs recientes de FastAPI (Backend) y metadatos de salud con sanitización automática de contraseñas y llaves.',
                )
              }}
            </p>
          </div>
          <span class="diag-badge-cyan">
            Ring Buffer UI: {{ uiDiagnosticBuffer.length }} eventos
          </span>
        </header>

        <div class="diag-form-row">
          <div class="diag-field">
            <label for="bundle-format-select">Formato de Archivo</label>
            <select id="bundle-format-select" v-model="bundleFormat" class="diag-input">
              <option value="zip">.zip (Estándar Windows / Linux / macOS)</option>
              <option value="tar.gz">.tar.gz (Tarball Gzip Linux / Unix)</option>
            </select>
          </div>

          <div class="diag-field">
            <label for="bundle-lines-input">Líneas de Log Backend</label>
            <input
              id="bundle-lines-input"
              v-model.number="logLinesLimit"
              type="number"
              min="50"
              max="2000"
              class="diag-input"
            />
          </div>
        </div>

        <div class="diag-field">
          <label for="bundle-operator-notes">Notas del Operador / Descripción de la Falla</label>
          <textarea
            id="bundle-operator-notes"
            v-model="operatorNotes"
            rows="3"
            class="diag-input"
            placeholder="Describa los pasos previos al incidente o el comportamiento observado..."
          ></textarea>
        </div>

        <div class="diag-actions">
          <button
            id="btn-download-support-bundle"
            type="button"
            class="diag-btn diag-btn-primary"
            :disabled="isGeneratingBundle"
            @click="handleGenerateSupportBundle"
          >
            {{
              isGeneratingBundle
                ? '⏳ Empaquetando y Sanitizando...'
                : `📦 Descargar Paquete de Diagnóstico (.${bundleFormat})`
            }}
          </button>
        </div>

        <div v-if="lastBundleResult" class="diag-summary-box" data-testid="bundle-summary">
          <div><strong>Archivo:</strong> {{ lastBundleResult.filename }}</div>
          <div>
            <strong>Secretos Sanitizados:</strong> {{ lastBundleResult.redacted_secrets_count }}
          </div>
          <div>
            <strong>Artefactos Incluidos:</strong>
            {{ lastBundleResult.included_files.join(', ') }}
          </div>
        </div>
      </section>

      <!-- Card 2: Conector SIEM Multi-Protocolo del ISP -->
      <section class="diag-card" aria-labelledby="siem-card-title">
        <header class="diag-card-header">
          <div>
            <h2 id="siem-card-title" class="diag-card-title">
              📡
              {{
                t(
                  'enterprise.siem_forwarder_title',
                  'Conector SIEM del ISP (Graylog / Grafana Loki / Syslog)',
                )
              }}
            </h2>
            <p class="diag-card-subtitle">
              {{
                t(
                  'enterprise.siem_forwarder_desc',
                  'Reenvía eventos y errores sanitizados hacia el colector central propio del ISP o empresa.',
                )
              }}
            </p>
          </div>
          <label class="diag-toggle-label">
            <input id="siem-enabled-checkbox" v-model="siemEnabled" type="checkbox" />
            <span>{{ siemEnabled ? 'Habilitado' : 'Deshabilitado' }}</span>
          </label>
        </header>

        <div class="diag-form-row">
          <div class="diag-field">
            <label for="siem-protocol-select">Protocolo del Colector SIEM</label>
            <select id="siem-protocol-select" v-model="siemProtocol" class="diag-input">
              <option value="GELF_UDP">Graylog GELF UDP</option>
              <option value="GELF_HTTP">Graylog GELF HTTP/HTTPS</option>
              <option value="LOKI_HTTP">Grafana Loki HTTP Push (/loki/api/v1/push)</option>
              <option value="SYSLOG_UDP">Syslog RFC 5424 UDP</option>
              <option value="SYSLOG_TCP">Syslog RFC 5424 TCP</option>
            </select>
          </div>

          <div class="diag-field">
            <label for="siem-min-level-select">Severidad Mínima</label>
            <select id="siem-min-level-select" v-model="siemMinLevel" class="diag-input">
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>
        </div>

        <div class="diag-form-row">
          <div class="diag-field">
            <label for="siem-host-input">Host / IP del Servidor SIEM del ISP</label>
            <input
              id="siem-host-input"
              v-model="siemHost"
              type="text"
              class="diag-input"
              placeholder="graylog.isp.interno"
            />
          </div>

          <div class="diag-field">
            <label for="siem-port-input">Puerto</label>
            <input
              id="siem-port-input"
              v-model.number="siemPort"
              type="number"
              min="1"
              max="65535"
              class="diag-input"
            />
          </div>
        </div>

        <div class="diag-form-row">
          <div class="diag-field">
            <label for="siem-stream-input">Etiqueta de Instancia / Stream</label>
            <input
              id="siem-stream-input"
              v-model="siemStreamLabel"
              type="text"
              class="diag-input"
              placeholder="rosgrid-noc-principal"
            />
          </div>

          <div class="diag-field">
            <label for="siem-endpoint-input">Ruta HTTP (GELF_HTTP / LOKI_HTTP)</label>
            <input
              id="siem-endpoint-input"
              v-model="siemEndpointPath"
              type="text"
              class="diag-input"
              placeholder="/gelf o /loki/api/v1/push"
            />
          </div>
        </div>

        <div class="diag-field">
          <label for="siem-token-input">
            Token Bearer Opcional
            <span v-if="siemHasSavedToken" class="diag-badge-cyan">(Token configurado)</span>
          </label>
          <input
            id="siem-token-input"
            v-model="siemAuthToken"
            type="password"
            class="diag-input"
            placeholder="Dejar en blanco para conservar el token actual"
          />
        </div>

        <div class="diag-checkbox-group">
          <label>
            <input v-model="siemIncludeFrontend" type="checkbox" />
            Incluir errores de interfaz (Frontend UI)
          </label>
          <label>
            <input v-model="siemIncludeAudit" type="checkbox" />
            Incluir eventos de auditoría administrativa
          </label>
          <label>
            <input v-model="siemUseTls" type="checkbox" />
            Usar TLS (HTTPS)
          </label>
        </div>

        <div class="diag-actions">
          <button
            id="btn-save-siem-config"
            type="button"
            class="diag-btn diag-btn-primary"
            :disabled="isSavingSiem"
            @click="handleSaveSiemConfig"
          >
            {{ isSavingSiem ? '⏳ Guardando...' : '💾 Guardar Configuración SIEM' }}
          </button>

          <button
            id="btn-test-siem-config"
            type="button"
            class="diag-btn diag-btn-secondary"
            :disabled="isTestingSiem"
            @click="handleTestSiemDelivery"
          >
            {{ isTestingSiem ? '⏳ Probando...' : '🧪 Enviar Log de Prueba' }}
          </button>
        </div>

        <div v-if="siemTestResult" class="diag-summary-box" data-testid="siem-test-summary">
          <strong>Resultado Prueba ({{ siemTestResult.protocol }}):</strong>
          {{ siemTestResult.detail }} — {{ siemTestResult.latency_ms }} ms
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
  .diagnostics-siem-panel {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .diag-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
    gap: 1.25rem;
  }

  .diag-card {
    background: #080f1d;
    border: 1px solid #1a2a40;
    border-radius: 8px;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .diag-card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .diag-card-title {
    margin: 0;
    font-size: 1.05rem;
    color: #00e5ff;
  }

  .diag-card-subtitle {
    margin: 0.35rem 0 0 0;
    font-size: 0.82rem;
    color: #94a3b8;
  }

  .diag-form-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.85rem;
  }

  .diag-field {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    font-size: 0.82rem;
    color: #cbd5e1;
  }

  .diag-input {
    background: #04070e;
    border: 1px solid #1e293b;
    border-radius: 6px;
    color: #f8fafc;
    padding: 0.5rem 0.65rem;
    font-size: 0.85rem;
  }

  .diag-checkbox-group {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    font-size: 0.82rem;
    color: #cbd5e1;
  }

  .diag-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .diag-btn {
    border: none;
    border-radius: 6px;
    padding: 0.55rem 1rem;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
  }

  .diag-btn-primary {
    background: #00e5ff;
    color: #04070e;
  }

  .diag-btn-secondary {
    background: #1a2a40;
    color: #e2e8f0;
  }

  .diag-badge-cyan {
    background: rgba(0, 229, 255, 0.12);
    border: 1px solid rgba(0, 229, 255, 0.4);
    color: #00e5ff;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .diag-summary-box {
    background: #04070e;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 0.75rem;
    font-size: 0.8rem;
    color: #cbd5e1;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .diag-alert {
    padding: 0.75rem 1rem;
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .diag-alert-error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fecaca;
  }

  .diag-alert-success {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #a7f3d0;
  }
</style>
