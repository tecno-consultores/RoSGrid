<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import QRCode from 'qrcode';
  import { http } from '@/api/httpClient';
  import { useAuthStore } from '@/stores/useAuthStore';
  import type { UserInfo } from '@/types';

  const route = useRoute();
  const router = useRouter();
  const authStore = useAuthStore();

  // Estados de etapas de Login
  type LoginStep = 'CREDENTIALS' | 'ENROLL_2FA' | 'VERIFY_2FA';
  const currentStep = ref<LoginStep>('CREDENTIALS');

  // Formulario Etapa 1
  const tenantSlug = ref('');
  const usernameOrEmail = ref('');
  const password = ref('');
  const showPassword = ref(false);
  const isLoading = ref(false);
  const errorMessage = ref('');

  // Formulario Etapa 2 (2FA)
  const challengeId = ref('');
  const totpCode = ref('');
  const provisioningUri = ref('');
  const secretKey = ref('');
  const backupCodes = ref<string[]>([]);
  const qrCanvasRef = ref<HTMLCanvasElement | null>(null);
  const challengeCountdown = ref(180);
  let countdownTimer: ReturnType<typeof setInterval> | null = null;

  // Banner accesible de redirección
  const redirectReason = computed(() => {
    const reason = route.query.reason;
    if (reason === 'session_revoked' || reason === 'killed_by_admin') {
      return 'Tu sesión fue revocada por un Administrador o por la activación del Kill-Switch.';
    }
    if (reason === 'session_expired') {
      return 'Tu sesión ha expirado por inactividad. Por favor, ingresa de nuevo.';
    }
    if (reason === 'unauthorized') {
      return 'Debes iniciar sesión para acceder a ese recurso.';
    }
    return '';
  });

  // Normalización automática de tenantSlug a minúsculas y caracteres válidos
  function onTenantSlugInput(e: Event) {
    const target = e.target as HTMLInputElement;
    tenantSlug.value = target.value.toLowerCase().replace(/[^a-z0-9-]/g, '');
  }

  function startCountdown(seconds = 180) {
    stopCountdown();
    challengeCountdown.value = seconds;
    countdownTimer = setInterval(() => {
      if (challengeCountdown.value > 0) {
        challengeCountdown.value--;
      } else {
        stopCountdown();
        errorMessage.value = 'El desafío 2FA ha expirado. Por favor, ingresa de nuevo.';
        currentStep.value = 'CREDENTIALS';
      }
    }, 1000);
  }

  function stopCountdown() {
    if (countdownTimer) {
      clearInterval(countdownTimer);
      countdownTimer = null;
    }
  }

  onBeforeUnmount(() => {
    stopCountdown();
  });

  // Renderizar QR local con librería qrcode
  async function renderQrCode(uri: string) {
    await nextTick();
    if (qrCanvasRef.value && uri) {
      try {
        await QRCode.toCanvas(qrCanvasRef.value, uri, {
          width: 200,
          margin: 1,
          color: {
            dark: '#000000',
            light: '#FFFFFF',
          },
        });
      } catch {
        // Fallback en caso de error de canvas
      }
    }
  }

  // Descarga local de códigos de respaldo
  function downloadBackupCodes() {
    if (backupCodes.value.length === 0) return;
    const content = `=== Códigos de Respaldo de Emergencia — RoSGrid ===\nEmpresa: ${tenantSlug.value}\nUsuario: ${usernameOrEmail.value}\nFecha: ${new Date().toISOString()}\n\n${backupCodes.value.join('\n')}\n\nGuarda estos códigos en un lugar seguro y fuera de línea.`;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url =
      typeof URL.createObjectURL === 'function' ? URL.createObjectURL(blob) : 'blob:sample';
    const link = document.createElement('a');
    link.href = url;
    link.download = `rosgrid-backup-codes-${tenantSlug.value}.txt`;
    link.click();
    if (typeof URL.revokeObjectURL === 'function') {
      URL.revokeObjectURL(url);
    }
  }

  // Etapa 1: Enviar credenciales
  async function handleCredentialsSubmit() {
    errorMessage.value = '';
    if (!tenantSlug.value.trim() || !usernameOrEmail.value.trim() || !password.value) {
      errorMessage.value = 'Todos los campos son obligatorios.';
      return;
    }

    isLoading.value = true;
    try {
      const res = await http.post<{
        next_step: 'ENROLL_2FA_REQUIRED' | 'VERIFY_2FA_TOTP' | 'AUTHENTICATED';
        challenge_id?: string;
        totp_provisioning_uri?: string;
        totp_secret?: string;
        backup_codes?: string[];
        user?: UserInfo;
        csrf_token?: string;
      }>('/api/v1/auth/login', {
        tenant_slug: tenantSlug.value.trim(),
        username_or_email: usernameOrEmail.value.trim(),
        password: password.value,
      });

      const data = res.data;
      if (data.next_step === 'ENROLL_2FA_REQUIRED') {
        currentStep.value = 'ENROLL_2FA';
        challengeId.value = data.challenge_id || '';
        provisioningUri.value = data.totp_provisioning_uri || '';
        secretKey.value = data.totp_secret || '';
        backupCodes.value = data.backup_codes || [];
        await renderQrCode(provisioningUri.value);
        startCountdown(300);
      } else if (data.next_step === 'VERIFY_2FA_TOTP') {
        currentStep.value = 'VERIFY_2FA';
        challengeId.value = data.challenge_id || '';
        startCountdown(180);
      } else if (data.user) {
        completeLogin(data.user, data.csrf_token);
      }
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value =
        error.detail || error.message || 'Credenciales inválidas o tenant no encontrado.';
    } finally {
      isLoading.value = false;
    }
  }

  // Etapa 2A: Confirmar Enrolamiento 2FA
  async function handleEnrollConfirm() {
    errorMessage.value = '';
    if (totpCode.value.length !== 6) {
      errorMessage.value = 'Ingresa el código de 6 dígitos generado por tu app autenticadora.';
      return;
    }

    isLoading.value = true;
    try {
      const res = await http.post<{ user: UserInfo; csrf_token?: string }>(
        '/api/v1/auth/2fa/confirm-enrollment',
        {
          challenge_id: challengeId.value,
          totp_code: totpCode.value,
        },
      );
      stopCountdown();
      completeLogin(res.data.user, res.data.csrf_token);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value =
        error.detail || error.message || 'Código TOTP incorrecto. Verifica la hora de tu app.';
    } finally {
      isLoading.value = false;
    }
  }

  // Etapa 2B: Verificar Desafío 2FA
  async function handleVerifySubmit() {
    errorMessage.value = '';
    if (totpCode.value.length !== 6) {
      errorMessage.value = 'El código debe tener exactamente 6 dígitos numéricos.';
      return;
    }

    isLoading.value = true;
    try {
      const res = await http.post<{ user: UserInfo; csrf_token?: string }>(
        '/api/v1/auth/2fa/verify',
        {
          challenge_id: challengeId.value,
          totp_code: totpCode.value,
        },
      );
      stopCountdown();
      completeLogin(res.data.user, res.data.csrf_token);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value =
        error.detail || error.message || 'Código de seguridad incorrecto o expirado.';
    } finally {
      isLoading.value = false;
    }
  }

  function onTotpInput() {
    totpCode.value = totpCode.value.replace(/[^0-9]/g, '').slice(0, 6);
    if (totpCode.value.length === 6 && currentStep.value === 'VERIFY_2FA') {
      handleVerifySubmit();
    }
  }

  function completeLogin(user: UserInfo, csrfToken?: string) {
    authStore.setAuth(user, csrfToken || 'csrf-session');
    const redirect =
      (route.query.redirect as string) ||
      (user.role === 'NOC_MONITOR' ? '/noc-wallboard' : '/inventory');
    router.push(redirect);
  }

  onMounted(() => {
    // Si viene pre-cargado el tenant_slug en la query
    if (route.query.tenant) {
      tenantSlug.value = String(route.query.tenant).toLowerCase();
    }
  });
</script>

<template>
  <div class="login-wrapper">
    <main id="main-content" class="login-card" role="main" aria-labelledby="login-heading">
      <header class="login-header">
        <div class="brand-logo" aria-hidden="true">⚡</div>
        <h1 id="login-heading" class="brand-title">RoSGrid</h1>
        <p class="brand-subtitle">Gestión Multi-Tenant para Flotas MikroTik RouterOS v7+</p>
      </header>

      <!-- Banner de advertencia/motivo de redirección -->
      <div
        v-if="redirectReason"
        class="alert-banner alert-banner--warning"
        role="alert"
        aria-live="polite"
      >
        <span class="alert-icon" aria-hidden="true">⚠️</span>
        <span class="alert-text">{{ redirectReason }}</span>
      </div>

      <!-- Banner de error accesible -->
      <div
        v-if="errorMessage"
        class="alert-banner alert-banner--danger"
        role="alert"
        aria-live="assertive"
      >
        <span class="alert-icon" aria-hidden="true">⛔</span>
        <span class="alert-text">{{ errorMessage }}</span>
      </div>

      <!-- ETAPA 1: Identificación de Empresa y Credenciales -->
      <form
        v-if="currentStep === 'CREDENTIALS'"
        class="login-form"
        novalidate
        @submit.prevent="handleCredentialsSubmit"
      >
        <div class="form-group">
          <label for="tenant-slug" class="form-label">
            Organización / Empresa <span class="required" aria-hidden="true">*</span>
          </label>
          <input
            id="tenant-slug"
            v-model="tenantSlug"
            type="text"
            required
            autocomplete="organization"
            placeholder="ej. isp-norte"
            class="form-input"
            :disabled="isLoading"
            @input="onTenantSlugInput"
          />
        </div>

        <div class="form-group">
          <label for="login-email" class="form-label">
            Usuario o Correo <span class="required" aria-hidden="true">*</span>
          </label>
          <input
            id="login-email"
            v-model="usernameOrEmail"
            type="text"
            required
            autocomplete="username"
            placeholder="admin@isp-norte.net"
            class="form-input"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <div class="label-row">
            <label for="login-password" class="form-label">
              Contraseña <span class="required" aria-hidden="true">*</span>
            </label>
            <button
              type="button"
              class="btn-toggle-visibility"
              :aria-label="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
              @click="showPassword = !showPassword"
            >
              {{ showPassword ? 'Ocultar' : 'Mostrar' }}
            </button>
          </div>
          <input
            id="login-password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            required
            autocomplete="current-password"
            placeholder="••••••••••••"
            class="form-input"
            :disabled="isLoading"
          />
        </div>

        <button type="submit" class="btn-submit" :disabled="isLoading">
          <span v-if="isLoading" class="spinner" aria-hidden="true">⏳</span>
          <span>{{ isLoading ? 'Verificando...' : 'Continuar con 2FA →' }}</span>
        </button>
      </form>

      <!-- ETAPA 2A: Enrolamiento Inicial 2FA TOTP -->
      <div v-else-if="currentStep === 'ENROLL_2FA'" class="enroll-container">
        <h2 class="step-title">Enrolamiento de Seguridad 2FA (Obligatorio)</h2>
        <p class="step-desc">
          Escanea el código QR desde tu aplicación autenticadora (Google Authenticator, Aegis o
          FreeOTP).
        </p>

        <div class="qr-canvas-box">
          <canvas
            ref="qrCanvasRef"
            class="qr-canvas"
            aria-label="Código QR de enrolamiento TOTP"
          ></canvas>
        </div>

        <div class="secret-manual-box">
          <span class="secret-label">Clave Secreta Manual:</span>
          <code class="secret-key">{{ secretKey || 'Cargando secreto...' }}</code>
        </div>

        <div v-if="backupCodes.length > 0" class="backup-codes-box">
          <p class="backup-note">
            Guarda estos códigos de recuperación en caso de pérdida de tu dispositivo:
          </p>
          <button type="button" class="btn-download-backup" @click="downloadBackupCodes">
            💾 Descargar Códigos de Emergencia (.txt)
          </button>
        </div>

        <form class="confirm-form" @submit.prevent="handleEnrollConfirm">
          <label for="enroll-totp-input" class="form-label">
            Ingresa el código de 6 dígitos generado por tu app:
          </label>
          <input
            id="enroll-totp-input"
            v-model="totpCode"
            type="text"
            inputmode="numeric"
            pattern="[0-9]{6}"
            maxlength="6"
            autocomplete="one-time-code"
            placeholder="123456"
            class="form-input form-input--totp"
            :disabled="isLoading"
            @input="onTotpInput"
          />

          <div class="timer-countdown" aria-live="polite">
            Tiempo restante: <strong>{{ challengeCountdown }}s</strong>
          </div>

          <button type="submit" class="btn-submit" :disabled="isLoading || totpCode.length !== 6">
            <span>{{ isLoading ? 'Confirmando...' : 'Confirmar y Acceder' }}</span>
          </button>
        </form>
      </div>

      <!-- ETAPA 2B: Verificación de Código 2FA TOTP -->
      <div v-else-if="currentStep === 'VERIFY_2FA'" class="verify-container">
        <h2 class="step-title">Verificación de Segundo Factor (2FA)</h2>
        <p class="step-desc">
          Introduce el código de 6 dígitos que muestra tu aplicación autenticadora.
        </p>

        <form class="verify-form" @submit.prevent="handleVerifySubmit">
          <div class="form-group">
            <label for="verify-totp-input" class="form-label">
              Código de Seguridad TOTP <span class="required" aria-hidden="true">*</span>
            </label>
            <input
              id="verify-totp-input"
              v-model="totpCode"
              type="text"
              inputmode="numeric"
              pattern="[0-9]{6}"
              maxlength="6"
              required
              autocomplete="one-time-code"
              placeholder="000000"
              class="form-input form-input--totp"
              :disabled="isLoading"
              autofocus
              @input="onTotpInput"
            />
          </div>

          <div class="timer-countdown" aria-live="polite">
            Desafío válido por: <strong>{{ challengeCountdown }}s</strong>
          </div>

          <button type="submit" class="btn-submit" :disabled="isLoading || totpCode.length !== 6">
            <span>{{ isLoading ? 'Validando...' : 'Acceder al Sistema' }}</span>
          </button>

          <button
            type="button"
            class="btn-back"
            :disabled="isLoading"
            @click="
              currentStep = 'CREDENTIALS';
              stopCountdown();
            "
          >
            ← Volver a ingresar credenciales
          </button>
        </form>
      </div>
    </main>
  </div>
</template>

<style scoped>
  .login-wrapper {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--rg-space-4, 16px);
    background-color: var(--rg-bg-canvas, #0b0f19);
  }

  .login-card {
    width: 100%;
    max-width: 440px;
    background-color: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: var(--rg-radius-lg, 8px);
    padding: var(--rg-space-6, 24px);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
  }

  .login-header {
    text-align: center;
    margin-bottom: var(--rg-space-6, 24px);
  }

  .brand-logo {
    font-size: 2.2rem;
    margin-bottom: var(--rg-space-2, 8px);
  }

  .brand-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--rg-accent-cyan, #22d3ee);
    margin: 0 0 var(--rg-space-1, 4px) 0;
  }

  .brand-subtitle {
    font-size: 0.85rem;
    color: var(--rg-text-muted, #94a3b8);
    margin: 0;
  }

  .alert-banner {
    display: flex;
    align-items: center;
    gap: var(--rg-space-2, 8px);
    padding: var(--rg-space-3, 12px);
    border-radius: var(--rg-radius-md, 6px);
    margin-bottom: var(--rg-space-4, 16px);
    font-size: 0.85rem;
  }

  .alert-banner--warning {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid #f59e0b;
    color: #fbbf24;
  }

  .alert-banner--danger {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #f87171;
  }

  .login-form,
  .confirm-form,
  .verify-form {
    display: flex;
    flex-direction: column;
    gap: var(--rg-space-4, 16px);
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: var(--rg-space-1, 4px);
  }

  .label-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .form-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--rg-text-secondary, #cbd5e1);
  }

  .required {
    color: var(--rg-status-critical, #ef4444);
  }

  .btn-toggle-visibility {
    background: transparent;
    border: none;
    color: var(--rg-accent-cyan, #22d3ee);
    font-size: 0.75rem;
    cursor: pointer;
    padding: 0;
  }

  .form-input {
    width: 100%;
    padding: 10px 12px;
    background-color: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: var(--rg-radius-md, 6px);
    color: var(--rg-text-primary, #f8fafc);
    font-size: 0.95rem;
    outline: none;
    transition:
      border-color 0.2s,
      box-shadow 0.2s;
  }

  .form-input:focus {
    border-color: var(--rg-accent-cyan-border, #06b6d4);
    box-shadow: var(--rg-cyan-glow, 0 0 12px rgba(6, 182, 212, 0.28));
  }

  .form-input--totp {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
    font-size: 1.5rem;
    letter-spacing: 0.35em;
    text-align: center;
  }

  .btn-submit {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--rg-space-2, 8px);
    width: 100%;
    padding: 12px;
    background-color: var(--rg-accent-cyan, #22d3ee);
    color: #0b0f19;
    border: none;
    border-radius: var(--rg-radius-md, 6px);
    font-weight: 700;
    font-size: 0.95rem;
    cursor: pointer;
    transition:
      background-color 0.2s,
      opacity 0.2s;
  }

  .btn-submit:hover:not(:disabled) {
    background-color: #38bdf8;
  }

  .btn-submit:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-back {
    background: transparent;
    border: none;
    color: var(--rg-text-muted, #94a3b8);
    font-size: 0.85rem;
    cursor: pointer;
    margin-top: var(--rg-space-2, 8px);
    text-align: center;
  }

  .btn-back:hover {
    color: var(--rg-text-primary, #f8fafc);
  }

  .step-title {
    font-size: 1.1rem;
    color: var(--rg-text-primary, #f8fafc);
    margin: 0 0 var(--rg-space-1, 4px) 0;
  }

  .step-desc {
    font-size: 0.85rem;
    color: var(--rg-text-muted, #94a3b8);
    margin: 0 0 var(--rg-space-4, 16px) 0;
  }

  .qr-canvas-box {
    display: flex;
    justify-content: center;
    margin-bottom: var(--rg-space-4, 16px);
    background: #ffffff;
    padding: 12px;
    border-radius: var(--rg-radius-md, 6px);
    width: fit-content;
    margin-left: auto;
    margin-right: auto;
  }

  .secret-manual-box {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 8px 12px;
    background-color: var(--rg-bg-canvas, #0b0f19);
    border: 1px dashed var(--rg-border-grid, #1e293b);
    border-radius: var(--rg-radius-md, 6px);
    margin-bottom: var(--rg-space-4, 16px);
  }

  .secret-label {
    font-size: 0.75rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .secret-key {
    font-family: 'JetBrains Mono', 'Ubuntu Mono', ui-monospace, monospace;
    font-variant-numeric: tabular-nums;
    font-size: 0.85rem;
    color: var(--rg-accent-cyan, #22d3ee);
    word-break: break-all;
  }

  .backup-codes-box {
    margin-bottom: var(--rg-space-4, 16px);
  }

  .backup-note {
    font-size: 0.75rem;
    color: var(--rg-text-secondary, #cbd5e1);
    margin: 0 0 6px 0;
  }

  .btn-download-backup {
    background: transparent;
    border: 1px solid var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    border-radius: var(--rg-radius-md, 6px);
    padding: 6px 12px;
    font-size: 0.8rem;
    cursor: pointer;
  }

  .timer-countdown {
    font-size: 0.8rem;
    color: var(--rg-text-muted, #94a3b8);
    text-align: center;
  }

  .timer-countdown strong {
    color: var(--rg-accent-cyan, #22d3ee);
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
  }
</style>
