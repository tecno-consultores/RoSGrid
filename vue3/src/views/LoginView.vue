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
  type LoginStep = 'CREDENTIALS' | 'ENROLL_2FA' | 'VERIFY_2FA' | 'BOOTSTRAP' | 'REGISTER';
  const currentStep = ref<LoginStep>('CREDENTIALS');
  const isBootstrapped = ref(true);
  const registrationEnabled = ref(true);
  const registerSuccess = ref('');

  // Formulario Etapa Bootstrap (Primer Usuario / Super Admin Inicial)
  const bootstrapTenantName = ref('Empresa Principal');
  const bootstrapTenantSlug = ref('master');
  const bootstrapAdminUsername = ref('superadmin');
  const bootstrapAdminEmail = ref('');
  const bootstrapAdminFullName = ref('Super Administrador');
  const bootstrapAdminPassword = ref('');
  const bootstrapAdminPasswordConfirm = ref('');

  // Formulario Etapa Registro de Operador
  const registerTenantSlug = ref('');
  const registerUsername = ref('');
  const registerEmail = ref('');
  const registerFullName = ref('');
  const registerPassword = ref('');
  const registerPasswordConfirm = ref('');
  const showRegisterPassword = ref(false);

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
  const isUsingBackupCode = ref(false);
  const provisioningUri = ref('');
  const secretKey = ref('');
  const backupCodes = ref<string[]>([]);
  const qrCanvasRef = ref<HTMLCanvasElement | null>(null);
  const challengeCountdown = ref(180);
  let countdownTimer: ReturnType<typeof setInterval> | null = null;

  // Banner accesible de redirección
  const redirectReason = computed(() => {
    if (!isBootstrapped.value || currentStep.value === 'BOOTSTRAP') {
      return '';
    }
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
    link.style.display = 'none';
    link.href = url;
    link.download = `rosgrid-backup-codes-${tenantSlug.value}.txt`;
    link.setAttribute('download', `rosgrid-backup-codes-${tenantSlug.value}.txt`);
    if (typeof document !== 'undefined' && document.body) {
      document.body.appendChild(link);
    }
    link.click();
    setTimeout(() => {
      if (link.parentNode) {
        link.parentNode.removeChild(link);
      }
      if (typeof URL.revokeObjectURL === 'function') {
        URL.revokeObjectURL(url);
      }
    }, 15000);
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
      const trimmedIdent = usernameOrEmail.value.trim();
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
        email: trimmedIdent,
        username_or_email: trimmedIdent,
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
    if (isUsingBackupCode.value) {
      if (totpCode.value.length !== 8) {
        errorMessage.value =
          'El código de respaldo debe tener exactamente 8 caracteres alfanuméricos.';
        return;
      }
    } else {
      if (totpCode.value.length !== 6) {
        errorMessage.value = 'El código debe tener exactamente 6 dígitos numéricos.';
        return;
      }
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
        error.detail || error.message || 'Código de seguridad o de respaldo incorrecto o expirado.';
    } finally {
      isLoading.value = false;
    }
  }

  function onTotpInput() {
    if (isUsingBackupCode.value) {
      totpCode.value = totpCode.value
        .replace(/[^a-zA-Z0-9]/g, '')
        .slice(0, 8)
        .toUpperCase();
      if (totpCode.value.length === 8 && currentStep.value === 'VERIFY_2FA') {
        handleVerifySubmit();
      }
    } else {
      totpCode.value = totpCode.value.replace(/[^0-9]/g, '').slice(0, 6);
      if (totpCode.value.length === 6 && currentStep.value === 'VERIFY_2FA') {
        handleVerifySubmit();
      }
    }
  }

  function toggleBackupCodeMode() {
    isUsingBackupCode.value = !isUsingBackupCode.value;
    totpCode.value = '';
    errorMessage.value = '';
  }

  function completeLogin(user: UserInfo, csrfToken?: string) {
    authStore.setAuth(user, csrfToken || 'csrf-session');
    const redirect =
      (route.query.redirect as string) || (user.role === 'NOC_MONITOR' ? '/noc-wallboard' : '/');
    router.push(redirect);
  }

  async function handleBootstrapSubmit() {
    errorMessage.value = '';
    if (
      !bootstrapTenantName.value.trim() ||
      !bootstrapTenantSlug.value.trim() ||
      !bootstrapAdminUsername.value.trim() ||
      !bootstrapAdminEmail.value.trim()
    ) {
      errorMessage.value = 'Todos los campos marcados con asterisco son obligatorios.';
      return;
    }
    if (bootstrapAdminPassword.value.length < 12) {
      errorMessage.value = 'La contraseña debe tener al menos 12 caracteres.';
      return;
    }
    if (bootstrapAdminPassword.value !== bootstrapAdminPasswordConfirm.value) {
      errorMessage.value = 'Las contraseñas no coinciden.';
      return;
    }

    isLoading.value = true;
    try {
      const res = await http.post<{
        status: string;
        tenant_slug: string;
        admin_username: string;
        totp_secret: string;
        totp_provisioning_uri: string;
        backup_codes: string[];
        challenge_id?: string;
      }>('/api/v1/auth/bootstrap', {
        tenant_name: bootstrapTenantName.value.trim(),
        tenant_slug: bootstrapTenantSlug.value.trim().toLowerCase(),
        admin_username: bootstrapAdminUsername.value.trim(),
        admin_email: bootstrapAdminEmail.value.trim().toLowerCase(),
        admin_full_name: bootstrapAdminFullName.value.trim(),
        admin_password: bootstrapAdminPassword.value,
      });

      tenantSlug.value = res.data.tenant_slug;
      usernameOrEmail.value = res.data.admin_username;
      secretKey.value = res.data.totp_secret;
      provisioningUri.value = res.data.totp_provisioning_uri;
      backupCodes.value = res.data.backup_codes;
      challengeId.value = res.data.challenge_id || '';

      currentStep.value = 'ENROLL_2FA';
      await renderQrCode(provisioningUri.value);
      startCountdown(300);
    } catch (err: unknown) {
      const error = err as { detail?: string };
      errorMessage.value = error.detail || 'Error al aprovisionar el Super Administrador inicial.';
    } finally {
      isLoading.value = false;
    }
  }

  async function handleRegisterSubmit() {
    errorMessage.value = '';
    registerSuccess.value = '';
    if (
      !registerTenantSlug.value.trim() ||
      !registerUsername.value.trim() ||
      !registerEmail.value.trim() ||
      !registerFullName.value.trim() ||
      !registerPassword.value
    ) {
      errorMessage.value = 'Todos los campos son obligatorios.';
      return;
    }
    if (registerPassword.value.length < 8) {
      errorMessage.value = 'La contraseña debe tener al menos 8 caracteres.';
      return;
    }
    if (registerPassword.value !== registerPasswordConfirm.value) {
      errorMessage.value = 'Las contraseñas no coinciden.';
      return;
    }

    isLoading.value = true;
    try {
      const res = await http.post<{ status: string; message: string }>('/api/v1/auth/register', {
        tenant_slug: registerTenantSlug.value.trim().toLowerCase(),
        username: registerUsername.value.trim(),
        email: registerEmail.value.trim().toLowerCase(),
        full_name: registerFullName.value.trim(),
        password: registerPassword.value,
      });

      registerSuccess.value =
        res.data.message ||
        'Solicitud enviada con éxito. Tu cuenta se encuentra PENDIENTE DE APROBACIÓN por un Administrador.';

      // Pre-cargar valores en el formulario de login para agilizar
      tenantSlug.value = registerTenantSlug.value.trim().toLowerCase();
      usernameOrEmail.value = registerUsername.value.trim();

      // Limpiar campos sensibles
      registerPassword.value = '';
      registerPasswordConfirm.value = '';

      currentStep.value = 'CREDENTIALS';
    } catch (err: unknown) {
      const error = err as {
        detail?: string;
        message?: string;
        data?: { detail?: string | Array<{ msg: string }> };
      };
      let detailStr = '';
      if (typeof error.data?.detail === 'string') {
        detailStr = error.data.detail;
      } else if (Array.isArray(error.data?.detail)) {
        detailStr = error.data.detail.map((d) => d.msg).join(', ');
      } else if (error.detail) {
        detailStr = error.detail;
      } else if (error.message) {
        detailStr = error.message;
      }
      errorMessage.value = detailStr || 'Error al procesar la solicitud de registro.';
    } finally {
      isLoading.value = false;
    }
  }

  function applyQueryTenant(): void {
    if (route.query.tenant) {
      const q = String(route.query.tenant).toLowerCase();
      tenantSlug.value = q;
      registerTenantSlug.value = q;
    }
  }

  function applyBootstrapData(data: {
    is_bootstrapped: boolean;
    registration_enabled?: boolean;
    default_tenant_slug?: string;
    default_tenant_name?: string;
  }): void {
    if (!data) return;
    if (data.is_bootstrapped === false) {
      currentStep.value = 'BOOTSTRAP';
      isBootstrapped.value = false;
      return;
    }
    isBootstrapped.value = true;
    if (data.registration_enabled !== undefined) {
      registrationEnabled.value = data.registration_enabled;
    }
    if (data.default_tenant_slug) {
      tenantSlug.value ||= data.default_tenant_slug;
      registerTenantSlug.value ||= data.default_tenant_slug;
    }
  }

  onMounted(async () => {
    applyQueryTenant();
    try {
      const res = await http.get<{
        is_bootstrapped: boolean;
        registration_enabled?: boolean;
        default_tenant_slug?: string;
        default_tenant_name?: string;
      }>('/api/v1/auth/bootstrap-status');
      applyBootstrapData(res.data);
    } catch {
      // Si falla la consulta, se mantiene el formulario estándar
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

      <!-- Banner de éxito de registro -->
      <div
        v-if="registerSuccess"
        class="alert-banner alert-banner--success"
        role="status"
        aria-live="polite"
      >
        <span class="alert-icon" aria-hidden="true">✅</span>
        <span class="alert-text">{{ registerSuccess }}</span>
      </div>

      <!-- ETAPA 0: Inicialización del Sistema (Bootstrap / Primer Usuario) -->
      <form
        v-if="currentStep === 'BOOTSTRAP'"
        class="login-form"
        novalidate
        @submit.prevent="handleBootstrapSubmit"
      >
        <div class="bootstrap-intro">
          <h2 class="section-title">🚀 Configuración Inicial de RoSGrid</h2>
          <p class="section-desc">
            No se detectaron usuarios en la base de datos. Registra la Organización Principal y la
            cuenta del
            <strong>Super Administrador Global</strong>.
          </p>
        </div>

        <div class="form-group">
          <label for="bootstrap-tenant-name" class="form-label">
            Organización Principal <span class="required" aria-hidden="true">*</span>
          </label>
          <input
            id="bootstrap-tenant-name"
            v-model="bootstrapTenantName"
            type="text"
            required
            placeholder="ej. Empresa Principal"
            class="form-input"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="bootstrap-tenant-slug" class="form-label">
            Slug de Organización <span class="required" aria-hidden="true">*</span>
          </label>
          <input
            id="bootstrap-tenant-slug"
            v-model="bootstrapTenantSlug"
            type="text"
            required
            placeholder="ej. master"
            class="form-input"
            :disabled="isLoading"
            @input="
              (e) =>
                (bootstrapTenantSlug = (e.target as HTMLInputElement).value
                  .toLowerCase()
                  .replace(/[^a-z0-9-]/g, ''))
            "
          />
        </div>

        <div class="form-group">
          <label for="bootstrap-admin-user" class="form-label">
            Usuario Super Administrador <span class="required" aria-hidden="true">*</span>
          </label>
          <input
            id="bootstrap-admin-user"
            v-model="bootstrapAdminUsername"
            type="text"
            required
            placeholder="ej. superadmin"
            class="form-input"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="bootstrap-admin-email" class="form-label">
            Correo Electrónico <span class="required" aria-hidden="true">*</span>
          </label>
          <input
            id="bootstrap-admin-email"
            v-model="bootstrapAdminEmail"
            type="email"
            required
            placeholder="ej. admin@tuempresa.com"
            class="form-input"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="bootstrap-admin-name" class="form-label">
            Nombre Completo <span class="required" aria-hidden="true">*</span>
          </label>
          <input
            id="bootstrap-admin-name"
            v-model="bootstrapAdminFullName"
            type="text"
            required
            placeholder="ej. Administrador Global"
            class="form-input"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="bootstrap-admin-pass" class="form-label">
            Contraseña Segura (Mínimo 12 caracteres)
            <span class="required" aria-hidden="true">*</span>
          </label>
          <input
            id="bootstrap-admin-pass"
            v-model="bootstrapAdminPassword"
            type="password"
            required
            autocomplete="new-password"
            placeholder="••••••••••••"
            class="form-input"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="bootstrap-admin-pass-confirm" class="form-label">
            Confirmar Contraseña <span class="required" aria-hidden="true">*</span>
          </label>
          <input
            id="bootstrap-admin-pass-confirm"
            v-model="bootstrapAdminPasswordConfirm"
            type="password"
            required
            autocomplete="new-password"
            placeholder="••••••••••••"
            class="form-input"
            :disabled="isLoading"
          />
        </div>

        <button type="submit" class="btn btn-primary" :disabled="isLoading">
          <span v-if="isLoading" class="spinner" aria-hidden="true"></span>
          <span>{{
            isLoading ? 'Inicializando...' : 'Crear Super Administrador y Continuar'
          }}</span>
        </button>
      </form>

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

        <div v-if="isBootstrapped && registrationEnabled" class="register-footer-hint">
          <span class="register-hint-text">¿No tienes cuenta de operador?</span>
          <button
            type="button"
            class="btn-switch-register"
            @click="
              errorMessage = '';
              registerSuccess = '';
              currentStep = 'REGISTER';
            "
          >
            Solicitar Registro de Operador →
          </button>
        </div>
      </form>

      <!-- ETAPA 0B: Solicitud de Auto-Registro de Operador -->
      <form
        v-if="currentStep === 'REGISTER'"
        class="login-form"
        novalidate
        @submit.prevent="handleRegisterSubmit"
      >
        <div class="bootstrap-intro">
          <h2 class="section-title">📝 Solicitud de Registro</h2>
          <p class="section-desc">
            Ingresa tus datos para registrarte. Tu cuenta quedará en estado
            <strong>Pendiente de Aprobación</strong> y deberá ser autorizada por un Administrador
            antes de tu primer ingreso.
          </p>
        </div>

        <div class="form-group">
          <label for="reg-tenant-slug" class="form-label">
            Organización / Empresa <span class="required" aria-hidden="true">*</span>
          </label>
          <input
            id="reg-tenant-slug"
            v-model="registerTenantSlug"
            type="text"
            required
            placeholder="ej. sistemas"
            class="form-input"
            :disabled="isLoading"
            @input="
              (e) =>
                (registerTenantSlug = (e.target as HTMLInputElement).value
                  .toLowerCase()
                  .replace(/[^a-z0-9-]/g, ''))
            "
          />
        </div>

        <div class="form-group">
          <label for="reg-username" class="form-label">
            Nombre de Usuario <span class="required" aria-hidden="true">*</span>
          </label>
          <input
            id="reg-username"
            v-model="registerUsername"
            type="text"
            required
            autocomplete="username"
            placeholder="ej. operador1"
            class="form-input"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="reg-email" class="form-label">
            Correo Electrónico <span class="required" aria-hidden="true">*</span>
          </label>
          <input
            id="reg-email"
            v-model="registerEmail"
            type="email"
            required
            autocomplete="email"
            placeholder="ej. operador@empresa.com"
            class="form-input"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="reg-fullname" class="form-label">
            Nombre y Apellido <span class="required" aria-hidden="true">*</span>
          </label>
          <input
            id="reg-fullname"
            v-model="registerFullName"
            type="text"
            required
            placeholder="ej. Carlos Rodríguez"
            class="form-input"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <div class="label-row">
            <label for="reg-password" class="form-label">
              Contraseña (Mínimo 8 caracteres) <span class="required" aria-hidden="true">*</span>
            </label>
            <button
              type="button"
              class="btn-toggle-visibility"
              :aria-label="showRegisterPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
              @click="showRegisterPassword = !showRegisterPassword"
            >
              {{ showRegisterPassword ? 'Ocultar' : 'Mostrar' }}
            </button>
          </div>
          <input
            id="reg-password"
            v-model="registerPassword"
            :type="showRegisterPassword ? 'text' : 'password'"
            required
            autocomplete="new-password"
            placeholder="••••••••••••"
            class="form-input"
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="reg-password-confirm" class="form-label">
            Confirmar Contraseña <span class="required" aria-hidden="true">*</span>
          </label>
          <input
            id="reg-password-confirm"
            v-model="registerPasswordConfirm"
            :type="showRegisterPassword ? 'text' : 'password'"
            required
            autocomplete="new-password"
            placeholder="••••••••••••"
            class="form-input"
            :disabled="isLoading"
          />
        </div>

        <button type="submit" class="btn-submit" :disabled="isLoading">
          <span v-if="isLoading" class="spinner" aria-hidden="true">⏳</span>
          <span>{{ isLoading ? 'Enviando...' : 'Enviar Solicitud de Registro' }}</span>
        </button>

        <button
          type="button"
          class="btn-back"
          :disabled="isLoading"
          @click="
            errorMessage = '';
            registerSuccess = '';
            currentStep = 'CREDENTIALS';
          "
        >
          ← Volver al Inicio de Sesión
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
          <code class="secret-key">{{ secretKey }}</code>
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
        <h2 class="step-title">
          {{
            isUsingBackupCode
              ? 'Código de Respaldo de Emergencia'
              : 'Verificación de Segundo Factor (2FA)'
          }}
        </h2>
        <p class="step-desc">
          {{
            isUsingBackupCode
              ? 'Introduce uno de tus códigos de recuperación de 8 caracteres alfanuméricos.'
              : 'Introduce el código de 6 dígitos que muestra tu aplicación autenticadora.'
          }}
        </p>

        <form class="verify-form" @submit.prevent="handleVerifySubmit">
          <div class="form-group">
            <label for="verify-totp-input" class="form-label">
              {{ isUsingBackupCode ? 'Código de Respaldo' : 'Código de Seguridad TOTP' }}
              <span class="required" aria-hidden="true">*</span>
            </label>
            <input
              id="verify-totp-input"
              v-model="totpCode"
              type="text"
              :inputmode="isUsingBackupCode ? 'text' : 'numeric'"
              :maxlength="isUsingBackupCode ? 8 : 6"
              required
              autocomplete="one-time-code"
              :placeholder="isUsingBackupCode ? 'ej. 8BB8B5C7' : '000000'"
              class="form-input form-input--totp"
              :style="
                isUsingBackupCode ? 'letter-spacing: 0.25rem; text-transform: uppercase;' : ''
              "
              :disabled="isLoading"
              autofocus
              @input="onTotpInput"
            />
          </div>

          <div class="timer-countdown" aria-live="polite">
            Desafío válido por: <strong>{{ challengeCountdown }}s</strong>
          </div>

          <button
            type="submit"
            class="btn-submit"
            :disabled="
              isLoading || (isUsingBackupCode ? totpCode.length !== 8 : totpCode.length !== 6)
            "
          >
            <span>{{ isLoading ? 'Validando...' : 'Acceder al Sistema' }}</span>
          </button>

          <button
            type="button"
            class="btn-toggle-backup"
            :disabled="isLoading"
            @click="toggleBackupCodeMode"
          >
            {{
              isUsingBackupCode
                ? '← Usar código dinámico de la app (6 dígitos)'
                : '🔑 ¿No tienes tu app? Usar código de respaldo (8 caracteres)'
            }}
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

    <!-- Pie de página Institucional y Enlaces Oficiales (Subtarea 16.5) -->
    <footer class="login-footer" role="contentinfo">
      <div class="login-footer-content">
        <span class="footer-attribution">
          Elaborado por
          <a
            href="https://www.tecnoconsultores.net/"
            target="_blank"
            rel="noopener noreferrer"
            class="footer-link"
          >
            Tecno Consultores 2023 C.A.
          </a>
        </span>
        <span class="footer-divider" aria-hidden="true">•</span>
        <span class="footer-version">v1.0</span>
        <span class="footer-divider" aria-hidden="true">•</span>
        <a
          href="https://www.gnu.org/licenses/gpl-3.0.html"
          target="_blank"
          rel="noopener noreferrer"
          class="badge-license"
        >
          Licencia GNU GPLv3
        </a>
        <a
          href="https://github.com/tecno-consultores/RoSGrid/"
          target="_blank"
          rel="noopener noreferrer"
          class="footer-github-link"
          aria-label="Repositorio GitHub oficial de RoSGrid"
        >
          <svg
            class="github-icon"
            viewBox="0 0 24 24"
            width="16"
            height="16"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"
            />
          </svg>
        </a>
      </div>
    </footer>
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

  .alert-banner--success {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #34d399;
  }

  .register-footer-hint {
    margin-top: var(--rg-space-3, 12px);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding-top: var(--rg-space-3, 12px);
    border-top: 1px solid var(--rg-border-grid, #1e293b);
  }

  .register-hint-text {
    font-size: 0.8rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .btn-switch-register {
    background: transparent;
    border: none;
    color: var(--rg-accent-cyan, #22d3ee);
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    padding: 4px 8px;
    border-radius: 4px;
    transition:
      color 0.2s,
      background-color 0.2s;
  }

  .btn-switch-register:hover {
    color: #38bdf8;
    background-color: rgba(34, 211, 238, 0.08);
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

  .btn-toggle-backup {
    background: transparent;
    border: 1px dashed var(--rg-border, #334155);
    border-radius: var(--rg-radius-md, 6px);
    color: var(--rg-accent-cyan, #22d3ee);
    font-size: 0.85rem;
    padding: 8px 12px;
    cursor: pointer;
    margin-top: var(--rg-space-2, 8px);
    text-align: center;
    transition:
      border-color 0.2s,
      background-color 0.2s;
  }

  .btn-toggle-backup:hover:not(:disabled) {
    border-color: var(--rg-accent-cyan, #22d3ee);
    background-color: rgba(34, 211, 238, 0.05);
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

  .bootstrap-intro {
    margin-bottom: var(--rg-space-4, 16px);
    text-align: center;
  }

  .bootstrap-intro .section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--rg-accent-cyan, #22d3ee);
    margin: 0 0 6px 0;
  }

  .bootstrap-intro .section-desc {
    font-size: 0.85rem;
    color: var(--rg-text-secondary, #cbd5e1);
    line-height: 1.4;
    margin: 0;
  }

  /* Pie de página Institucional (Subtarea 16.5) */
  .login-footer {
    margin-top: var(--rg-space-6, 24px);
    text-align: center;
    font-size: 0.75rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .login-footer-content {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .footer-link,
  .footer-github-link,
  .badge-license {
    color: var(--rg-accent-cyan, #22d3ee);
    text-decoration: none;
    transition: color 0.15s ease;
  }

  .footer-link:hover,
  .footer-github-link:hover,
  .badge-license:hover {
    text-decoration: underline;
    color: #67e8f9;
  }

  .badge-license {
    background: rgba(34, 211, 238, 0.1);
    border: 1px solid rgba(34, 211, 238, 0.25);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 500;
  }

  .footer-divider {
    color: var(--rg-border-grid, #334155);
  }

  .github-icon {
    display: inline-block;
    vertical-align: middle;
  }
</style>
