<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, watch, onMounted, onBeforeUnmount } from 'vue';
  import { http } from '@/api/httpClient';
  import type { UserManagementItem, McpTokenResponse } from '@/types';

  const props = defineProps<{
    user: UserManagementItem | null;
    isOpen: boolean;
  }>();

  const emit = defineEmits<{
    (e: 'close'): void;
    (e: 'token-generated', res: McpTokenResponse): void;
  }>();

  const expiryDays = ref<number>(365);
  const isGenerating = ref(false);
  const errorMessage = ref('');
  const generatedTokenData = ref<McpTokenResponse | null>(null);
  const isCopied = ref(false);

  function resetState() {
    expiryDays.value = 365;
    isGenerating.value = false;
    errorMessage.value = '';
    generatedTokenData.value = null;
    isCopied.value = false;
  }

  watch(
    () => props.isOpen,
    (val) => {
      if (val) {
        resetState();
      }
    },
  );

  async function handleGenerateToken() {
    if (!props.user) return;
    isGenerating.value = true;
    errorMessage.value = '';

    try {
      const idempotencyKey =
        typeof crypto !== 'undefined' && crypto.randomUUID
          ? crypto.randomUUID()
          : `idemp-mcp-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

      const res = await http.post<McpTokenResponse>(
        `/api/v1/users/${props.user.id}/mcp-token`,
        { expiry_days: Number(expiryDays.value) },
        { headers: { 'Idempotency-Key': idempotencyKey } },
      );

      generatedTokenData.value = res.data;
      emit('token-generated', res.data);
    } catch (err: unknown) {
      const error = err as {
        detail?: string;
        message?: string;
        data?: { detail?: string };
      };
      errorMessage.value =
        error.data?.detail || error.detail || error.message || 'Error al generar el token MCP.';
    } finally {
      isGenerating.value = false;
    }
  }

  async function handleCopyToken() {
    if (!generatedTokenData.value?.token) return;
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard) {
        await navigator.clipboard.writeText(generatedTokenData.value.token);
      }
      isCopied.value = true;
      setTimeout(() => {
        isCopied.value = false;
      }, 3000);
    } catch {
      // Fallback si clipboard API no está disponible
      isCopied.value = true;
    }
  }

  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Escape' && props.isOpen) {
      emit('close');
    }
  }

  onMounted(() => {
    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', handleKeyDown);
    }
  });

  onBeforeUnmount(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('keydown', handleKeyDown);
    }
  });
</script>

<template>
  <div v-if="isOpen" class="rg-modal-backdrop" @click.self="emit('close')">
    <div
      class="rg-modal mcp-token-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="mcp-modal-title"
    >
      <header class="modal-header">
        <div>
          <h2 id="mcp-modal-title" class="modal-title">
            <span class="mcp-icon">🤖</span> Generador de Token MCP (Agentes IA)
          </h2>
          <p class="modal-subtitle">
            Emisión de Token Bearer de larga duración para Claude Desktop, Hermes Agent o NOC
            Autónomo.
          </p>
        </div>
        <button
          type="button"
          class="btn-close"
          aria-label="Cerrar modal de token MCP"
          @click="emit('close')"
        >
          ✕
        </button>
      </header>

      <div class="modal-body">
        <!-- Banner del Operador Objetivo -->
        <div v-if="user" class="target-account-card">
          <div class="target-field">
            <span class="field-label">Cuenta de Servicio:</span>
            <span class="field-value"
              >@{{ user.username }} ({{ user.full_name || 'Sin nombre' }})</span
            >
          </div>
          <div class="target-field">
            <span class="field-label">Rol Asignado:</span>
            <span class="role-badge">{{ user.role }}</span>
          </div>
          <div class="target-field">
            <span class="field-label">Lista Blanca CIDR:</span>
            <span class="cidr-badge">
              {{
                user.allowed_cidr_list && user.allowed_cidr_list.length > 0
                  ? user.allowed_cidr_list.join(', ')
                  : 'Cualquier IP permitida (127.0.0.1 / Sin restricción CIDR)'
              }}
            </span>
          </div>
        </div>

        <!-- Alerta de Error -->
        <div v-if="errorMessage" class="error-banner" role="alert">⚠ {{ errorMessage }}</div>

        <!-- Estado 1: Formulario de Emisión -->
        <form
          v-if="!generatedTokenData"
          class="generate-form"
          @submit.prevent="handleGenerateToken"
        >
          <div class="form-group">
            <label for="expiry-selector" class="form-label">Período de Validez del Token:</label>
            <select id="expiry-selector" v-model="expiryDays" class="form-select">
              <option :value="30">30 días (1 mes)</option>
              <option :value="90">90 días (3 meses)</option>
              <option :value="180">180 días (6 meses)</option>
              <option :value="365">365 días (1 año - Recomendado)</option>
              <option :value="730">730 días (2 años)</option>
            </select>
          </div>

          <div class="security-info-box">
            <div class="info-title">🛡️ Gobernanza Criptográfica de la Sesión:</div>
            <ul class="info-list">
              <li>
                El token se registrará automáticamente en la pantalla de
                <strong>Sesiones Activas & Kill-Switch</strong>.
              </li>
              <li>
                Podrás revocar la sesión en caliente en 1 clic en caso de anomalías del agente
                inteligente.
              </li>
              <li>Se asociará la IP autorizada según la lista blanca CIDR del operador.</li>
            </ul>
          </div>

          <footer class="modal-footer">
            <button type="button" class="btn-cancel" @click="emit('close')">Cancelar</button>
            <button type="submit" class="btn-generate" :disabled="isGenerating">
              <span v-if="isGenerating">Generando Criptográficamente...</span>
              <span v-else>⚡ Generar Token de Acceso MCP</span>
            </button>
          </footer>
        </form>

        <!-- Estado 2: Token Generado Exitosamente -->
        <div v-else class="generated-token-container">
          <div class="success-banner" role="status">
            ✔ ¡Token Bearer MCP emitido y registrado en KeyDB exitosamente!
          </div>

          <div class="warning-callout">
            <span class="warning-icon">⚠</span>
            <div>
              <strong>Importante:</strong> Este token es una credencial de larga duración. Por
              seguridad, <strong>no se volverá a mostrar</strong> una vez cerrada esta ventana.
              Cópialo y guárdalo en tu gestor de secretos.
            </div>
          </div>

          <div class="token-box-wrapper">
            <label for="generated-token-input" class="token-label">Token Bearer JWT:</label>
            <div class="token-input-group">
              <input
                id="generated-token-input"
                type="text"
                readonly
                :value="generatedTokenData.token"
                class="token-input"
                @focus="($event.target as HTMLInputElement).select()"
              />
              <button
                type="button"
                class="btn-copy"
                :class="{ 'btn-copy--copied': isCopied }"
                aria-label="Copiar token al portapapeles"
                @click="handleCopyToken"
              >
                {{ isCopied ? '✔ ¡Copiado!' : '📋 Copiar' }}
              </button>
            </div>
          </div>

          <!-- Metadatos de la Sesión -->
          <div class="session-meta-grid">
            <div class="meta-item">
              <span class="meta-title">ID de Sesión (KeyDB):</span>
              <span class="meta-val mono">{{ generatedTokenData.session_id }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-title">Fecha de Expiración:</span>
              <span class="meta-val">{{
                new Date(generatedTokenData.expires_at).toLocaleDateString()
              }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-title">Emitido por:</span>
              <span class="meta-val">@{{ generatedTokenData.issued_by }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-title">Organización:</span>
              <span class="meta-val">{{ generatedTokenData.tenant_slug }}</span>
            </div>
          </div>

          <!-- Snippet de Configuración para Agentes IA -->
          <details class="snippet-accordion">
            <summary class="snippet-summary">
              📖 Ver Configuración de Ejemplo para Claude Desktop y Hermes Agent
            </summary>
            <div class="snippet-content">
              <p class="snippet-instruction">
                Agrega este bloque en tu archivo <code>claude_desktop_config.json</code>:
              </p>
              <pre class="snippet-pre"><code>{
  "mcpServers": {
    "rosgrid": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-fetch",
        "http://localhost:8000/api/v1/mcp"
      ],
      "env": {
        "AUTHORIZATION": "Bearer {{ generatedTokenData.token.substring(0, 16) }}..."
      }
    }
  }
}</code></pre>
            </div>
          </details>

          <footer class="modal-footer">
            <button type="button" class="btn-primary" @click="emit('close')">
              Entendido y Copiado
            </button>
          </footer>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .rg-modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1050;
    padding: 1rem;
  }

  .rg-modal {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    width: 100%;
    max-width: 680px;
    box-shadow:
      0 20px 25px -5px rgba(0, 0, 0, 0.5),
      0 8px 10px -6px rgba(0, 0, 0, 0.5);
    display: flex;
    flex-direction: column;
    color: #f8fafc;
    overflow: hidden;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 1.25rem 1.5rem;
    background: #1e293b;
    border-bottom: 1px solid #334155;
  }

  .modal-title {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 700;
    color: #38bdf8;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .modal-subtitle {
    margin: 0.25rem 0 0;
    font-size: 0.8rem;
    color: #94a3b8;
  }

  .btn-close {
    background: transparent;
    border: none;
    color: #94a3b8;
    font-size: 1.25rem;
    cursor: pointer;
    padding: 0.25rem;
    line-height: 1;
    border-radius: 4px;
  }

  .btn-close:hover {
    color: #f8fafc;
    background: rgba(255, 255, 255, 0.1);
  }

  .modal-body {
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    max-height: calc(85vh - 120px);
    overflow-y: auto;
  }

  .target-account-card {
    background: #090d16;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 0.85rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.85rem;
  }

  .target-field {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .field-label {
    color: #64748b;
    font-weight: 600;
    min-width: 140px;
  }

  .field-value {
    color: #e2e8f0;
    font-family: monospace;
    font-weight: 600;
  }

  .role-badge {
    background: #1e293b;
    color: #38bdf8;
    border: 1px solid #0284c7;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: monospace;
  }

  .cidr-badge {
    color: #10b981;
    font-family: monospace;
    font-size: 0.8rem;
  }

  .error-banner {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fca5a5;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    font-size: 0.85rem;
  }

  .success-banner {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #6ee7b7;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
  }

  .warning-callout {
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid #f59e0b;
    color: #fde68a;
    padding: 0.75rem 1rem;
    border-radius: 6px;
    font-size: 0.82rem;
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    line-height: 1.4;
  }

  .warning-icon {
    font-size: 1.25rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .form-label {
    font-size: 0.85rem;
    color: #94a3b8;
    font-weight: 600;
  }

  .form-select {
    background: #090d16;
    border: 1px solid #334155;
    color: #f8fafc;
    padding: 0.6rem 0.85rem;
    border-radius: 6px;
    font-size: 0.9rem;
  }

  .form-select:focus {
    outline: none;
    border-color: #38bdf8;
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);
  }

  .security-info-box {
    background: #090d16;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 0.85rem 1rem;
    font-size: 0.8rem;
    color: #94a3b8;
  }

  .info-title {
    color: #cbd5e1;
    font-weight: 600;
    margin-bottom: 0.4rem;
  }

  .info-list {
    margin: 0;
    padding-left: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }

  .token-box-wrapper {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .token-label {
    font-size: 0.85rem;
    color: #94a3b8;
    font-weight: 600;
  }

  .token-input-group {
    display: flex;
    gap: 0.5rem;
  }

  .token-input {
    flex: 1;
    background: #090d16;
    border: 1px solid #0284c7;
    color: #38bdf8;
    padding: 0.6rem 0.85rem;
    border-radius: 6px;
    font-family: monospace;
    font-size: 0.85rem;
    overflow-x: auto;
  }

  .btn-copy {
    background: #0284c7;
    color: #ffffff;
    border: none;
    padding: 0 1.25rem;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
    white-space: nowrap;
  }

  .btn-copy:hover {
    background: #0369a1;
  }

  .btn-copy--copied {
    background: #10b981;
  }

  .session-meta-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    background: #090d16;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 0.85rem 1rem;
    font-size: 0.8rem;
  }

  .meta-item {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .meta-title {
    color: #64748b;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .meta-val {
    color: #f1f5f9;
  }

  .meta-val.mono {
    font-family: monospace;
    font-size: 0.75rem;
    word-break: break-all;
  }

  .snippet-accordion {
    background: #090d16;
    border: 1px solid #1e293b;
    border-radius: 6px;
    overflow: hidden;
    font-size: 0.82rem;
  }

  .snippet-summary {
    padding: 0.65rem 1rem;
    color: #38bdf8;
    cursor: pointer;
    font-weight: 600;
    user-select: none;
  }

  .snippet-content {
    padding: 0.75rem 1rem;
    border-top: 1px solid #1e293b;
  }

  .snippet-instruction {
    margin: 0 0 0.5rem;
    color: #94a3b8;
  }

  .snippet-pre {
    margin: 0;
    background: #020617;
    border: 1px solid #1e293b;
    border-radius: 4px;
    padding: 0.75rem;
    overflow-x: auto;
    color: #a5f3fc;
    font-size: 0.78rem;
    font-family: monospace;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    margin-top: 0.5rem;
  }

  .btn-cancel {
    background: #1e293b;
    color: #94a3b8;
    border: 1px solid #334155;
    padding: 0.6rem 1.25rem;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
  }

  .btn-cancel:hover {
    color: #f8fafc;
    background: #334155;
  }

  .btn-generate,
  .btn-primary {
    background: #0284c7;
    color: #ffffff;
    border: none;
    padding: 0.6rem 1.25rem;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .btn-generate:hover,
  .btn-primary:hover {
    background: #0369a1;
  }

  .btn-generate:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>
