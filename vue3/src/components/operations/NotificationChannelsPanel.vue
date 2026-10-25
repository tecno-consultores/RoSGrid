<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, onMounted } from 'vue';
  import { http } from '@/api/httpClient';
  import { useI18n } from '@/composables/useI18n';
  import type {
    AlertChannelType,
    NotificationChannelItem,
    NotificationChannelCreateRequest,
    NotificationTestResponse,
  } from '@/types';

  const { t } = useI18n();

  const channels = ref<NotificationChannelItem[]>([]);
  const isLoading = ref<boolean>(false);
  const errorMessage = ref<string>('');
  const successMessage = ref<string>('');

  // Modales
  const isCreateModalOpen = ref<boolean>(false);
  const isTestModalOpen = ref<boolean>(false);
  const activeChannelForTest = ref<NotificationChannelItem | null>(null);

  // Formulario de creación
  const formName = ref('');
  const formType = ref<AlertChannelType>('TELEGRAM_BOT');
  const formIsEnabled = ref(true);
  const formSubscribedEvents = ref<string[]>([
    'ROUTER_OFFLINE',
    'ROUTER_ONLINE',
    'DEGRADED_HIGH_LOAD',
    'SSL_MISMATCH',
  ]);

  // Configuraciones específicas
  const telegramBotToken = ref('');
  const telegramChatId = ref('');
  const smtpHost = ref('');
  const smtpPort = ref<number>(587);
  const smtpUser = ref('');
  const smtpPassword = ref('');
  const smtpFrom = ref('');
  const smtpTo = ref('');
  const webhookUrl = ref('');
  const webhookAuthHeader = ref('');

  // Modal de prueba
  const testMessage = ref('Prueba de alerta técnica desde el panel RoSGrid');
  const isTesting = ref(false);
  const testResult = ref<NotificationTestResponse | null>(null);

  const availableEvents = [
    { id: 'ROUTER_OFFLINE', label: 'Router Fuera de Línea (Offline)' },
    { id: 'ROUTER_ONLINE', label: 'Router Reconectado (Online)' },
    { id: 'DEGRADED_HIGH_LOAD', label: 'Carga Crítica de CPU / Memoria' },
    { id: 'SSL_MISMATCH', label: 'Discrepancia de Certificado TLS' },
    { id: 'CONFIG_DRIFT_DETECTED', label: 'Deriva de Configuración (Drift)' },
    { id: 'ROGUE_DHCP_ALERT', label: 'DHCP no Autorizado / Ataque L2' },
  ];

  async function fetchChannels() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.get<NotificationChannelItem[]>(
        '/api/v1/operations/notification-channels',
      );
      channels.value = res.data || [];
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value =
        error.detail || error.message || 'Error al cargar canales de notificación';
    } finally {
      isLoading.value = false;
    }
  }

  function openCreateModal() {
    formName.value = '';
    formType.value = 'TELEGRAM_BOT';
    formIsEnabled.value = true;
    formSubscribedEvents.value = [
      'ROUTER_OFFLINE',
      'ROUTER_ONLINE',
      'DEGRADED_HIGH_LOAD',
      'SSL_MISMATCH',
    ];
    telegramBotToken.value = '';
    telegramChatId.value = '';
    smtpHost.value = '';
    smtpPort.value = 587;
    smtpUser.value = '';
    smtpPassword.value = '';
    smtpFrom.value = '';
    smtpTo.value = '';
    webhookUrl.value = '';
    webhookAuthHeader.value = '';
    errorMessage.value = '';
    successMessage.value = '';
    isCreateModalOpen.value = true;
  }

  function closeCreateModal() {
    isCreateModalOpen.value = false;
  }

  function buildConfigPayload(): Record<string, unknown> {
    if (formType.value === 'TELEGRAM_BOT') {
      return {
        bot_token: telegramBotToken.value.trim(),
        chat_id: telegramChatId.value.trim(),
      };
    } else if (formType.value === 'SMTP_EMAIL') {
      return {
        smtp_host: smtpHost.value.trim(),
        smtp_port: Number(smtpPort.value),
        smtp_user: smtpUser.value.trim(),
        smtp_password: smtpPassword.value,
        from_email: smtpFrom.value.trim(),
        to_emails: smtpTo.value
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      };
    } else {
      return {
        webhook_url: webhookUrl.value.trim(),
        auth_header: webhookAuthHeader.value.trim() || undefined,
      };
    }
  }

  async function handleCreateChannel() {
    if (!formName.value.trim()) {
      errorMessage.value = 'Debe indicar un nombre identificador para el canal.';
      return;
    }

    const config = buildConfigPayload();
    if (formType.value === 'TELEGRAM_BOT' && (!config.bot_token || !config.chat_id)) {
      errorMessage.value = 'El Bot Token y el Chat ID de Telegram son requeridos.';
      return;
    }
    if (formType.value === 'GENERIC_WEBHOOK' && !config.webhook_url) {
      errorMessage.value = 'La URL de destino del Webhook es requerida.';
      return;
    }

    try {
      const payload: NotificationChannelCreateRequest = {
        name: formName.value.trim(),
        channel_type: formType.value,
        is_enabled: formIsEnabled.value,
        subscribed_events: formSubscribedEvents.value,
        config,
      };

      await http.post('/api/v1/operations/notification-channels', payload);
      successMessage.value = `Canal "${formName.value}" creado y cifrado con éxito.`;
      closeCreateModal();
      await fetchChannels();
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al registrar el canal.';
    }
  }

  async function handleToggleStatus(ch: NotificationChannelItem) {
    try {
      await http.patch(`/api/v1/operations/notification-channels/${ch.id}`, {
        is_enabled: !ch.is_enabled,
      });
      ch.is_enabled = !ch.is_enabled;
      successMessage.value = `Canal "${ch.name}" ${ch.is_enabled ? 'activado' : 'desactivado'}.`;
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al actualizar estado del canal.';
    }
  }

  async function handleDeleteChannel(ch: NotificationChannelItem) {
    if (!confirm(`¿Confirma la eliminación irreversible del canal "${ch.name}"?`)) {
      return;
    }
    try {
      await http.delete(`/api/v1/operations/notification-channels/${ch.id}`);
      successMessage.value = `Canal "${ch.name}" eliminado correctamente.`;
      await fetchChannels();
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al eliminar el canal.';
    }
  }

  function openTestModal(ch: NotificationChannelItem) {
    activeChannelForTest.value = ch;
    testMessage.value = `[RoSGrid Test] Verificación de despacho táctico para canal "${ch.name}"`;
    testResult.value = null;
    isTestModalOpen.value = true;
  }

  function closeTestModal() {
    isTestModalOpen.value = false;
    activeChannelForTest.value = null;
    testResult.value = null;
  }

  async function handleDispatchTest() {
    if (!activeChannelForTest.value) return;
    isTesting.value = true;
    testResult.value = null;
    try {
      const res = await http.post<NotificationTestResponse>(
        `/api/v1/operations/notification-channels/${activeChannelForTest.value.id}/test`,
        { message: testMessage.value },
      );
      testResult.value = res.data;
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      testResult.value = {
        status: 'FAILED',
        detail: error.detail || error.message || 'Fallo de conexión al despachar alerta de prueba',
      };
    } finally {
      isTesting.value = false;
    }
  }

  function getChannelTypeBadge(type: AlertChannelType): { label: string; class: string } {
    switch (type) {
      case 'TELEGRAM_BOT':
        return { label: '📱 Telegram Bot', class: 'badge-telegram' };
      case 'SMTP_EMAIL':
        return { label: '✉️ Correo SMTP', class: 'badge-smtp' };
      case 'GENERIC_WEBHOOK':
        return { label: '🔗 Webhook HTTP', class: 'badge-webhook' };
      default:
        return { label: type, class: 'badge-default' };
    }
  }

  onMounted(() => {
    fetchChannels();
  });
</script>

<template>
  <div class="notification-channels-panel">
    <!-- Feedback Alerts -->
    <div v-if="errorMessage" class="tactical-banner banner-error" role="alert">
      <span>⚠️ {{ errorMessage }}</span>
    </div>
    <div v-if="successMessage" class="tactical-banner banner-success" role="status">
      <span>✅ {{ successMessage }}</span>
    </div>

    <!-- Barra Superior de Acciones -->
    <div class="panel-toolbar">
      <div>
        <h2 class="section-title">{{ t('notification_channels.title', 'Canales de Alerta y Notificación Multicanal') }}</h2>
        <p class="section-desc">
          {{ t('notification_channels.subtitle', 'Configure la integración segura con Telegram, Servidores SMTP y Webhooks cifrados en AES-256-GCM para notificaciones instantáneas de eventos de red y fallas de la flota.') }}
        </p>
      </div>
      <div class="toolbar-actions">
        <button
          type="button"
          class="btn-tactical btn-refresh"
          title="Actualizar listado"
          :disabled="isLoading"
          @click="fetchChannels"
        >
          🔄 {{ t('inventory.btn_refresh', 'Refrescar') }}
        </button>
        <button type="button" class="btn-tactical btn-primary" @click="openCreateModal">
          {{ t('notification_channels.btn_new_channel', '➕ Nuevo Canal de Alerta') }}
        </button>
      </div>
    </div>

    <!-- Lista de Canales -->
    <div v-if="isLoading" class="panel-loading" aria-busy="true">
      <div class="tactical-spinner"></div>
      <p>Cargando canales de alerta configurados...</p>
    </div>

    <div v-else-if="channels.length === 0" class="empty-state">
      <div class="empty-icon">🔔</div>
      <p class="empty-title">{{ t('notification_channels.empty_channels', 'No hay canales de notificación configurados') }}</p>
      <p class="empty-subtitle">
        Cree un canal de Telegram, Servidor SMTP o Webhook para recibir alarmas críticas en tiempo
        real.
      </p>
      <button type="button" class="btn-tactical btn-primary" @click="openCreateModal">
        {{ t('notification_channels.btn_new_channel', '➕ Configurar Primer Canal') }}
      </button>
    </div>

    <div v-else class="channels-grid">
      <article
        v-for="ch in channels"
        :key="ch.id"
        class="channel-card"
        :class="{ disabled: !ch.is_enabled }"
      >
        <div class="card-header">
          <div class="card-type-row">
            <span class="type-badge" :class="getChannelTypeBadge(ch.channel_type).class">
              {{ getChannelTypeBadge(ch.channel_type).label }}
            </span>
            <span class="status-pill" :class="ch.is_enabled ? 'status-enabled' : 'status-disabled'">
              {{ ch.is_enabled ? '● ACTIVO' : '○ INACTIVO' }}
            </span>
          </div>
          <h3 class="channel-name">{{ ch.name }}</h3>
        </div>

        <div class="card-body">
          <div class="events-section">
            <span class="events-label">Eventos Suscritos ({{ ch.subscribed_events.length }}):</span>
            <div class="event-tags">
              <span v-for="evt in ch.subscribed_events" :key="evt" class="event-tag">
                {{ evt }}
              </span>
            </div>
          </div>

          <div class="metadata-row">
            <span class="meta-label">ID:</span>
            <code class="meta-val">{{ ch.id.slice(0, 8) }}...{{ ch.id.slice(-4) }}</code>
          </div>
          <div class="metadata-row">
            <span class="meta-label">Registrado:</span>
            <span class="meta-val">{{ new Date(ch.created_at).toLocaleString() }}</span>
          </div>
        </div>

        <div class="card-actions">
          <button
            type="button"
            class="btn-card-action btn-test"
            title="Despachar mensaje de prueba a este canal"
            @click="openTestModal(ch)"
          >
            {{ t('notification_channels.btn_test', '🧪 Probar') }}
          </button>
          <button
            type="button"
            class="btn-card-action btn-toggle"
            :class="{ active: ch.is_enabled }"
            :title="ch.is_enabled ? 'Desactivar canal' : 'Activar canal'"
            @click="handleToggleStatus(ch)"
          >
            {{ ch.is_enabled ? t('notification_channels.btn_deactivate', 'Desactivar') : t('notification_channels.btn_activate', 'Activar') }}
          </button>
          <button
            type="button"
            class="btn-card-action btn-delete"
            :title="t('notification_channels.btn_delete', 'Eliminar canal de notificación')"
            @click="handleDeleteChannel(ch)"
          >
            🗑️
          </button>
        </div>
      </article>
    </div>

    <!-- ================================================================= -->
    <!-- MODAL CREACIÓN DE CANAL                                           -->
    <!-- ================================================================= -->
    <div
      v-if="isCreateModalOpen"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-channel-title"
    >
      <div class="modal-card">
        <header class="modal-header">
          <h3 id="create-channel-title" class="modal-title">
            ➕ Configurar Nuevo Canal de Notificación
          </h3>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar modal"
            @click="closeCreateModal"
          >
            ✕
          </button>
        </header>

        <form class="modal-body" @submit.prevent="handleCreateChannel">
          <div class="form-group">
            <label for="ch-name" class="form-label">Nombre del Canal *</label>
            <input
              id="ch-name"
              v-model="formName"
              type="text"
              class="tactical-input"
              placeholder="Ej: Canal Telegram Guardia NOC"
              required
            />
          </div>

          <div class="form-group">
            <label for="ch-type" class="form-label">Tipo de Notificación *</label>
            <select id="ch-type" v-model="formType" class="tactical-select">
              <option value="TELEGRAM_BOT">📱 Bot de Telegram</option>
              <option value="SMTP_EMAIL">✉️ Servidor de Correo SMTP</option>
              <option value="GENERIC_WEBHOOK">🔗 Webhook HTTP (JSON Post)</option>
            </select>
          </div>

          <!-- Campos para Telegram -->
          <div v-if="formType === 'TELEGRAM_BOT'" class="type-fields-box">
            <div class="form-group">
              <label for="tg-bot-token" class="form-label">Bot Token de Telegram *</label>
              <input
                id="tg-bot-token"
                v-model="telegramBotToken"
                type="password"
                class="tactical-input"
                placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"
                required
              />
              <span class="input-hint"
                >Token proporcionado por @BotFather. Se cifra con AES-256-GCM.</span
              >
            </div>
            <div class="form-group">
              <label for="tg-chat-id" class="form-label">Chat ID o Canal *</label>
              <input
                id="tg-chat-id"
                v-model="telegramChatId"
                type="text"
                class="tactical-input"
                placeholder="-1001234567890 o @micanalnoc"
                required
              />
            </div>
          </div>

          <!-- Campos para SMTP -->
          <div v-else-if="formType === 'SMTP_EMAIL'" class="type-fields-box">
            <div class="form-row">
              <div class="form-group flex-2">
                <label for="smtp-host" class="form-label">Host SMTP *</label>
                <input
                  id="smtp-host"
                  v-model="smtpHost"
                  type="text"
                  class="tactical-input"
                  placeholder="smtp.empresa.com"
                  required
                />
              </div>
              <div class="form-group flex-1">
                <label for="smtp-port" class="form-label">Puerto</label>
                <input
                  id="smtp-port"
                  v-model.number="smtpPort"
                  type="number"
                  class="tactical-input"
                  placeholder="587"
                />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group flex-1">
                <label for="smtp-user" class="form-label">Usuario SMTP</label>
                <input
                  id="smtp-user"
                  v-model="smtpUser"
                  type="text"
                  class="tactical-input"
                  placeholder="alertas@empresa.com"
                />
              </div>
              <div class="form-group flex-1">
                <label for="smtp-pass" class="form-label">Contraseña SMTP</label>
                <input
                  id="smtp-pass"
                  v-model="smtpPassword"
                  type="password"
                  class="tactical-input"
                  placeholder="••••••••••••"
                />
              </div>
            </div>
            <div class="form-group">
              <label for="smtp-from" class="form-label">Remitente (From)</label>
              <input
                id="smtp-from"
                v-model="smtpFrom"
                type="email"
                class="tactical-input"
                placeholder="noreply-noc@empresa.com"
              />
            </div>
            <div class="form-group">
              <label for="smtp-to" class="form-label">Destinatarios (Separados por coma)</label>
              <input
                id="smtp-to"
                v-model="smtpTo"
                type="text"
                class="tactical-input"
                placeholder="noc@empresa.com, guard@empresa.com"
              />
            </div>
          </div>

          <!-- Campos para Webhook -->
          <div v-else-if="formType === 'GENERIC_WEBHOOK'" class="type-fields-box">
            <div class="form-group">
              <label for="webhook-url" class="form-label">URL del Webhook (HTTPS) *</label>
              <input
                id="webhook-url"
                v-model="webhookUrl"
                type="url"
                class="tactical-input"
                placeholder="https://noc.empresa.com/api/alerts/webhook"
                required
              />
            </div>
            <div class="form-group">
              <label for="webhook-auth" class="form-label"
                >Cabecera de Autorización (Opcional)</label
              >
              <input
                id="webhook-auth"
                v-model="webhookAuthHeader"
                type="text"
                class="tactical-input"
                placeholder="Bearer eyJhbGci..."
              />
            </div>
          </div>

          <!-- Eventos Suscritos -->
          <div class="form-group">
            <label class="form-label">Eventos Suscritos</label>
            <div class="events-checkbox-grid">
              <label v-for="evt in availableEvents" :key="evt.id" class="checkbox-label">
                <input
                  v-model="formSubscribedEvents"
                  type="checkbox"
                  :value="evt.id"
                  class="tactical-checkbox"
                />
                <span>{{ evt.label }}</span>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="formIsEnabled" type="checkbox" class="tactical-checkbox" />
              <span>Habilitar canal inmediatamente al guardar</span>
            </label>
          </div>

          <footer class="modal-footer">
            <button type="button" class="btn-tactical btn-secondary" @click="closeCreateModal">
              Cancelar
            </button>
            <button type="submit" class="btn-tactical btn-primary">
              🔒 Guardar y Cifrar Canal
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- ================================================================= -->
    <!-- MODAL PRUEBA DE DESPACHO                                          -->
    <!-- ================================================================= -->
    <div
      v-if="isTestModalOpen"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="test-channel-title"
    >
      <div class="modal-card">
        <header class="modal-header">
          <h3 id="test-channel-title" class="modal-title">
            🧪 Probar Canal: {{ activeChannelForTest?.name }}
          </h3>
          <button type="button" class="btn-close" aria-label="Cerrar modal" @click="closeTestModal">
            ✕
          </button>
        </header>

        <div class="modal-body">
          <p class="modal-hint">
            Se enviará una carga útil de prueba al canal configurado para validar la conectividad y
            las credenciales cifradas.
          </p>

          <div class="form-group">
            <label for="test-msg" class="form-label">Mensaje de Prueba</label>
            <input id="test-msg" v-model="testMessage" type="text" class="tactical-input" />
          </div>

          <div v-if="testResult" class="test-result-box" :class="testResult.status.toLowerCase()">
            <div class="result-header">
              <span class="result-icon">
                {{ testResult.status === 'SUCCESS' ? '✅' : '❌' }}
              </span>
              <strong class="result-title">
                {{ testResult.status === 'SUCCESS' ? 'Despacho Exitoso' : 'Error en Despacho' }}
              </strong>
            </div>
            <p class="result-detail">{{ testResult.detail }}</p>
          </div>
        </div>

        <footer class="modal-footer">
          <button type="button" class="btn-tactical btn-secondary" @click="closeTestModal">
            Cerrar
          </button>
          <button
            type="button"
            class="btn-tactical btn-primary"
            :disabled="isTesting"
            @click="handleDispatchTest"
          >
            {{ isTesting ? 'Enviando...' : '🚀 Despachar Prueba' }}
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<style scoped>
  .notification-channels-panel {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    color: #e2e8f0;
  }

  .tactical-banner {
    padding: 0.75rem 1rem;
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .banner-error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #fca5a5;
  }

  .banner-success {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #6ee7b7;
  }

  .panel-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1.5rem;
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 1.25rem 1.5rem;
  }

  .section-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #38bdf8;
    margin: 0 0 0.25rem 0;
  }

  .section-desc {
    font-size: 0.875rem;
    color: #94a3b8;
    margin: 0;
    max-width: 750px;
    line-height: 1.4;
  }

  .toolbar-actions {
    display: flex;
    gap: 0.75rem;
    flex-shrink: 0;
  }

  .btn-tactical {
    font-family: inherit;
    font-size: 0.85rem;
    font-weight: 600;
    padding: 0.55rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 1px solid transparent;
  }

  .btn-primary {
    background: #0284c7;
    color: #ffffff;
    border-color: #38bdf8;
  }

  .btn-primary:hover:not(:disabled) {
    background: #0369a1;
  }

  .btn-secondary {
    background: #1e293b;
    color: #cbd5e1;
    border-color: #334155;
  }

  .btn-secondary:hover:not(:disabled) {
    background: #334155;
  }

  .btn-refresh {
    background: #1e293b;
    color: #94a3b8;
    border-color: #334155;
  }

  .btn-refresh:hover:not(:disabled) {
    color: #e2e8f0;
    background: #334155;
  }

  .panel-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem;
    color: #94a3b8;
    gap: 1rem;
  }

  .tactical-spinner {
    width: 28px;
    height: 28px;
    border: 3px solid rgba(56, 189, 248, 0.2);
    border-top-color: #38bdf8;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    background: #0f172a;
    border: 1px dashed #334155;
    border-radius: 6px;
    padding: 3rem 1.5rem;
  }

  .empty-icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
  }

  .empty-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #f1f5f9;
    margin: 0 0 0.25rem 0;
  }

  .empty-subtitle {
    font-size: 0.85rem;
    color: #94a3b8;
    margin: 0 0 1.25rem 0;
    max-width: 500px;
  }

  .channels-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 1.25rem;
  }

  .channel-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 6px;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    transition: border-color 0.2s;
  }

  .channel-card:hover {
    border-color: #334155;
  }

  .channel-card.disabled {
    opacity: 0.65;
    border-color: #27272a;
  }

  .card-header {
    padding: 1rem 1.25rem;
    background: #1e293b;
    border-bottom: 1px solid #334155;
  }

  .card-type-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
  }

  .type-badge {
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.2rem 0.5rem;
    border-radius: 3px;
    letter-spacing: 0.05em;
  }

  .badge-telegram {
    background: rgba(14, 165, 233, 0.2);
    color: #38bdf8;
    border: 1px solid rgba(14, 165, 233, 0.4);
  }

  .badge-smtp {
    background: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.4);
  }

  .badge-webhook {
    background: rgba(168, 85, 247, 0.2);
    color: #c084fc;
    border: 1px solid rgba(168, 85, 247, 0.4);
  }

  .badge-default {
    background: #334155;
    color: #cbd5e1;
  }

  .status-pill {
    font-size: 0.7rem;
    font-weight: 700;
    padding: 0.15rem 0.45rem;
    border-radius: 3px;
    letter-spacing: 0.05em;
  }

  .status-enabled {
    background: rgba(16, 185, 129, 0.2);
    color: #34d399;
  }

  .status-disabled {
    background: rgba(100, 116, 139, 0.2);
    color: #94a3b8;
  }

  .channel-name {
    font-size: 1.05rem;
    font-weight: 600;
    color: #f8fafc;
    margin: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .card-body {
    padding: 1rem 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    flex: 1;
  }

  .events-section {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .events-label {
    font-size: 0.75rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .event-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
  }

  .event-tag {
    font-size: 0.7rem;
    font-family: monospace;
    background: #1e293b;
    color: #cbd5e1;
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    border: 1px solid #334155;
  }

  .metadata-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.75rem;
    color: #64748b;
  }

  .meta-val {
    color: #94a3b8;
  }

  .card-actions {
    display: flex;
    border-top: 1px solid #1e293b;
    background: #090d16;
  }

  .btn-card-action {
    flex: 1;
    background: transparent;
    border: none;
    border-right: 1px solid #1e293b;
    padding: 0.6rem 0.5rem;
    font-size: 0.8rem;
    font-weight: 600;
    color: #94a3b8;
    cursor: pointer;
    transition: all 0.2s;
  }

  .btn-card-action:last-child {
    border-right: none;
    flex: 0 0 45px;
  }

  .btn-card-action:hover {
    background: #1e293b;
    color: #f1f5f9;
  }

  .btn-card-action.btn-test:hover {
    color: #38bdf8;
  }

  .btn-card-action.btn-delete:hover {
    color: #ef4444;
  }

  /* Modales */
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.75);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    padding: 1rem;
  }

  .modal-card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    width: 100%;
    max-width: 580px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem 1.5rem;
    background: #1e293b;
    border-bottom: 1px solid #334155;
  }

  .modal-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #38bdf8;
    margin: 0;
  }

  .btn-close {
    background: transparent;
    border: none;
    color: #94a3b8;
    font-size: 1.25rem;
    cursor: pointer;
    padding: 0.25rem;
    line-height: 1;
  }

  .btn-close:hover {
    color: #ffffff;
  }

  .modal-body {
    padding: 1.5rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
  }

  .modal-hint {
    font-size: 0.85rem;
    color: #94a3b8;
    margin: 0;
    line-height: 1.4;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .form-row {
    display: flex;
    gap: 1rem;
  }

  .flex-1 {
    flex: 1;
  }

  .flex-2 {
    flex: 2;
  }

  .form-label {
    font-size: 0.8rem;
    font-weight: 600;
    color: #cbd5e1;
  }

  .input-hint {
    font-size: 0.72rem;
    color: #64748b;
  }

  .tactical-input,
  .tactical-select {
    background: #020617;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 0.55rem 0.75rem;
    color: #f1f5f9;
    font-size: 0.875rem;
    outline: none;
    transition: border-color 0.2s;
  }

  .tactical-input:focus,
  .tactical-select:focus {
    border-color: #38bdf8;
  }

  .type-fields-box {
    background: #020617;
    border: 1px dashed #334155;
    border-radius: 6px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .events-checkbox-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0.5rem;
    background: #020617;
    border: 1px solid #1e293b;
    border-radius: 4px;
    padding: 0.75rem;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.82rem;
    color: #cbd5e1;
    cursor: pointer;
  }

  .tactical-checkbox {
    accent-color: #0284c7;
    cursor: pointer;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
    padding: 1rem 1.5rem;
    background: #1e293b;
    border-top: 1px solid #334155;
  }

  .test-result-box {
    margin-top: 1rem;
    padding: 1rem;
    border-radius: 4px;
    border: 1px solid transparent;
  }

  .test-result-box.success {
    background: rgba(16, 185, 129, 0.1);
    border-color: #10b981;
    color: #6ee7b7;
  }

  .test-result-box.failed {
    background: rgba(239, 68, 68, 0.1);
    border-color: #ef4444;
    color: #fca5a5;
  }

  .result-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.35rem;
  }

  .result-detail {
    font-size: 0.85rem;
    margin: 0;
  }
</style>
