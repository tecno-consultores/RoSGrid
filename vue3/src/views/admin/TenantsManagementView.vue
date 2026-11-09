<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  /* eslint-disable security/detect-object-injection */
  import type { WebFigDynamic } from '@/types';
  import { ref, onMounted } from 'vue';
  import { useRouter } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useI18n } from '@/composables/useI18n';
  import type { TenantItem } from '@/types';
  import { useAuthStore } from '@/stores/useAuthStore';

  const { t } = useI18n();
  const router = useRouter();
  const authStore = useAuthStore();
  const isLoading = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');
  const tenants = ref<TenantItem[]>([]);

  // Modal de Crear Empresa
  const isCreateModalOpen = ref(false);
  const isCreating = ref(false);
  const newTenant = ref({
    slug: '',
    name: '',
    tax_id: '',
    admin_full_name: '',
    admin_email: '',
    admin_username: '',
    admin_password: '',
    max_routers_quota: 50,
    max_users_quota: 20,
    default_safemode_seconds: 60,
    hq_latitude: 10.4806,
    hq_longitude: -66.9036,
  });

  // Modal de Editar Empresa
  const isEditModalOpen = ref(false);
  const isUpdating = ref(false);
  const isCapturingGps = ref(false);
  const editingTenant = ref({
    id: '',
    slug: '',
    name: '',
    tax_id: '',
    max_routers_quota: 50,
    max_users_quota: 20,
    default_safemode_seconds: 60,
    require_2fa_all_users: true,
    hq_latitude: 10.4806,
    hq_longitude: -66.9036,
  });

  function captureBrowserGps(target: 'create' | 'edit'): void {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      errorMessage.value = 'Geolocalización no soportada en este navegador.';
      return;
    }
    isCapturingGps.value = true;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        isCapturingGps.value = false;
        const lat = Number(pos.coords.latitude.toFixed(6));
        const lng = Number(pos.coords.longitude.toFixed(6));
        if (target === 'create') {
          newTenant.value.hq_latitude = lat;
          newTenant.value.hq_longitude = lng;
        } else {
          editingTenant.value.hq_latitude = lat;
          editingTenant.value.hq_longitude = lng;
        }
      },
      (err) => {
        isCapturingGps.value = false;
        errorMessage.value = `No se pudo obtener la ubicación GPS: ${err.message}`;
      },
      { timeout: 10000, enableHighAccuracy: true },
    );
  }

  function openEditTenantModal(tenant: TenantItem): void {
    errorMessage.value = '';
    editingTenant.value = {
      id: tenant.id,
      slug: tenant.slug,
      name: tenant.name,
      tax_id: tenant.tax_id || '',
      max_routers_quota: tenant.max_routers_quota ?? 50,
      max_users_quota: tenant.max_users_quota ?? 20,
      default_safemode_seconds: tenant.default_safemode_seconds ?? 60,
      require_2fa_all_users: tenant.require_2fa_all_users ?? true,
      hq_latitude:
        tenant.hq_latitude !== undefined && tenant.hq_latitude !== null
          ? Number(tenant.hq_latitude)
          : 10.4806,
      hq_longitude:
        tenant.hq_longitude !== undefined && tenant.hq_longitude !== null
          ? Number(tenant.hq_longitude)
          : -66.9036,
    };
    isEditModalOpen.value = true;
  }

  async function handleUpdateTenant(): Promise<void> {
    if (!editingTenant.value.id) return;
    isUpdating.value = true;
    errorMessage.value = '';
    try {
      const payload = {
        name: editingTenant.value.name.trim(),
        slug: editingTenant.value.slug.trim().toLowerCase(),
        tax_id: editingTenant.value.tax_id.trim() || null,
        max_routers_quota: Number(editingTenant.value.max_routers_quota),
        max_users_quota: Number(editingTenant.value.max_users_quota),
        default_safemode_seconds: Number(editingTenant.value.default_safemode_seconds),
        require_2fa_all_users: Boolean(editingTenant.value.require_2fa_all_users),
        hq_latitude: Number(editingTenant.value.hq_latitude),
        hq_longitude: Number(editingTenant.value.hq_longitude),
      };
      const res = await http.patch<TenantItem>(
        `/api/v1/tenants/${editingTenant.value.id}`,
        payload,
      );
      const idx = tenants.value.findIndex((item) => item.id === editingTenant.value.id);
      if (idx !== -1) {
        tenants.value[idx] = {
          ...tenants.value[idx],
          ...payload,
          ...(res.data || {}),
          tax_id: res.data?.tax_id ?? (payload.tax_id || undefined),
        };
      }
      await loadTenants();
      if (
        String(authStore.user?.tenant_id) === String(editingTenant.value.id) ||
        authStore.tenantSlug === editingTenant.value.slug ||
        authStore.tenantSlug === payload.slug
      ) {
        authStore.updateTenantFeatures({
          hq_latitude: payload.hq_latitude,
          hq_longitude: payload.hq_longitude,
        });
        await authStore.fetchTenantFeatures();
      }
      isEditModalOpen.value = false;
      successMessage.value = `Datos y cuotas de "${payload.name}" actualizados exitosamente.`;
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value =
        error.detail || error.message || 'Error al actualizar los datos de la empresa.';
    } finally {
      isUpdating.value = false;
    }
  }

  function goToTenantModules(tenant: TenantItem): void {
    router.push(`/admin/tenants/${tenant.id}/modules`);
  }

  function countActiveModules(tenant: TenantItem): number {
    const feats = tenant.features || {};
    return Object.values(feats).filter((v) => v === true).length;
  }

  async function loadTenants() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.get<TenantItem[] | { items: TenantItem[] }>('/api/v1/tenants');
      tenants.value = Array.isArray(res.data) ? res.data : res.data?.items || [];
    } catch (err: unknown) {
      tenants.value = [];
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al cargar organizaciones.';
    } finally {
      isLoading.value = false;
    }
  }

  async function toggleSuspendTenant(tenant: TenantItem) {
    const action = tenant.status === 'ACTIVE' ? 'suspender' : 'activar';
    if (!confirm(`¿Estás seguro de que deseas ${action} la organización "${tenant.name}"?`)) {
      return;
    }

    try {
      const newStatus = tenant.status === 'ACTIVE' ? 'SUSPENDED' : 'ACTIVE';
      await http.patch(`/api/v1/tenants/${tenant.id}`, { status: newStatus });
      tenant.status = newStatus;
      successMessage.value = `Estado de "${tenant.name}" actualizado a ${newStatus}.`;
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value =
        error.detail || error.message || 'Error al cambiar estado de la empresa.';
    }
  }

  async function handleCreateTenant() {
    isCreating.value = true;
    errorMessage.value = '';
    try {
      const payload = {
        ...newTenant.value,
        slug: newTenant.value.slug.trim().toLowerCase(),
        name: newTenant.value.name.trim(),
        admin_username: newTenant.value.admin_username.trim(),
        admin_email: newTenant.value.admin_email.trim(),
        admin_full_name:
          newTenant.value.admin_full_name.trim() ||
          newTenant.value.admin_username.trim() ||
          newTenant.value.name.trim() ||
          'Administrador',
        hq_latitude: Number(newTenant.value.hq_latitude) || 10.4806,
        hq_longitude: Number(newTenant.value.hq_longitude) || -66.9036,
      };
      const res = await http.post<TenantItem | { tenant: TenantItem }>(
        '/api/v1/tenants',
        payload,
      );
      const created =
        res.data && 'tenant' in res.data && res.data.tenant
          ? res.data.tenant
          : (res.data as TenantItem);

      if (created && created.id) {
        tenants.value.push(created);
      }
      await loadTenants();

      isCreateModalOpen.value = false;
      successMessage.value = `Empresa "${newTenant.value.name}" creada exitosamente.`;
      // Reset form
      newTenant.value = {
        slug: '',
        name: '',
        tax_id: '',
        admin_full_name: '',
        admin_email: '',
        admin_username: '',
        admin_password: '',
        max_routers_quota: 50,
        max_users_quota: 20,
        default_safemode_seconds: 60,
        hq_latitude: 10.4806,
        hq_longitude: -66.9036,
      };
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al crear la empresa.';
    } finally {
      isCreating.value = false;
    }
  }

  onMounted(() => {
    loadTenants();
    loadBeaconStatus();
  });

  const beaconStatus = ref<{
    enabled: boolean;
    instance_id?: string;
    last_sent_at?: string | null;
    last_heartbeat_at?: string | null;
    fleet_bucket?: string;
    router_count?: number;
    last_status?: string;
    status?: string;
  } | null>(null);
  const isTriggeringBeacon = ref(false);

  function formatBeaconTimestamp(raw?: string | null): string {
    if (!raw) return 'Nunca';
    const d = new Date(raw);
    if (Number.isNaN(d.getTime())) return raw;
    return d.toLocaleString();
  }

  async function loadBeaconStatus() {
    try {
      const res = await http.get<WebFigDynamic>('/api/v1/system/telemetry-beacon/status');
      beaconStatus.value = res.data;
    } catch {
      beaconStatus.value = null;
    }
  }

  async function handleTriggerBeacon() {
    isTriggeringBeacon.value = true;
    errorMessage.value = '';
    try {
      const res = await http.post<WebFigDynamic>('/api/v1/system/telemetry-beacon/trigger');
      if (res.data && typeof res.data === 'object') {
        beaconStatus.value = { ...beaconStatus.value, ...res.data };
      }
      successMessage.value =
        res.data?.message || 'Latido de telemetría anónima emitido exitosamente.';
      await loadBeaconStatus();
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al emitir latido del beacon.';
    } finally {
      isTriggeringBeacon.value = false;
    }
  }
</script>

<template>
  <div class="tenants-view">
    <header class="view-header">
      <div>
        <h1 class="view-title">{{ t('tenants_mgmt.title', 'Administración de Empresas (Multi-Tenant)') }}</h1>
        <p class="view-subtitle">
          {{ t('tenants_mgmt.subtitle', 'Gestión de organizaciones, cuotas de hardware MikroTik y suspensión de Tenants.') }}
        </p>
      </div>
      <button
        v-if="authStore.currentRole === 'SUPERADMIN_GLOBAL'"
        id="btn-open-create-tenant"
        type="button"
        class="btn-create"
        @click="isCreateModalOpen = true"
      >
        {{ t('tenants_mgmt.btn_register_tenant', '+ Registrar Empresa') }}
      </button>
    </header>

    <!-- Tarjeta Compacta: Telemetría Anónima de Instancia (Beacon) -->
    <div class="beacon-card">
      <div class="beacon-card__info">
        <div class="beacon-card__header">
          📡 Telemetría Anónima de Instancia (Heartbeat Beacon)
          <span
            class="badge-status"
            :class="beaconStatus?.enabled ? 'badge-status--active' : 'badge-status--silent'"
          >
            {{ beaconStatus?.enabled ? 'ACTIVO' : 'FAIL-SILENT' }}
          </span>
        </div>
        <p class="beacon-card__meta">
          Instance ID (HMAC-SHA256): <code class="beacon-mono">{{ beaconStatus?.instance_id || 'anónimo' }}</code> |
          Flota: <strong class="beacon-fleet">{{ beaconStatus?.router_count ?? beaconStatus?.fleet_bucket ?? '0' }} routers ({{ beaconStatus?.fleet_bucket || '0' }})</strong> |
          Último Latido: <span class="beacon-timestamp">{{ formatBeaconTimestamp(beaconStatus?.last_sent_at || beaconStatus?.last_heartbeat_at) }}</span>
        </p>
      </div>
      <button
        id="btn-trigger-beacon"
        type="button"
        class="btn-beacon btn-rg btn-rg--cyan btn-sm"
        :disabled="isTriggeringBeacon"
        @click="handleTriggerBeacon"
      >
        {{ isTriggeringBeacon ? 'Emitiendo...' : '📡 Emitir Latido Ahora' }}
      </button>
    </div>

    <div v-if="errorMessage" class="banner banner--error" role="alert">
      {{ errorMessage }}
    </div>
    <div v-if="successMessage" class="banner banner--success" role="status">
      {{ successMessage }}
    </div>

    <div class="table-container">
      <table class="rg-table" aria-label="Listado de empresas y cuotas">
        <thead>
          <tr>
            <th scope="col">{{ t('tenants_mgmt.th_tenant', 'Organización') }}</th>
            <th scope="col">{{ t('tenants_mgmt.th_slug', 'Slug') }}</th>
            <th scope="col">RIF / Tax ID</th>
            <th scope="col">{{ t('tenants_mgmt.th_status', 'Estado') }}</th>
            <th scope="col">{{ t('tenants_mgmt.th_quotas', 'Cuota Routers') }}</th>
            <th scope="col">Cuota Usuarios</th>
            <th scope="col">Safe Mode</th>
            <th scope="col" class="col-actions">{{ t('tenants_mgmt.th_actions', 'Acciones') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tenant in tenants" :key="tenant.id">
            <td class="cell-name">
              <strong>{{ tenant.name }}</strong>
            </td>
            <td class="cell-slug">
              <code>{{ tenant.slug }}</code>
            </td>
            <td>{{ tenant.tax_id || '—' }}</td>
            <td>
              <span
                class="badge-status"
                :class="{
                  'badge-status--active': tenant.status === 'ACTIVE',
                  'badge-status--suspended': tenant.status === 'SUSPENDED',
                }"
              >
                {{ tenant.status }}
              </span>
            </td>
            <td class="cell-quota">
              <div class="quota-bar-track">
                <div
                  class="quota-bar-fill"
                  :style="{
                    width: `${Math.min(100, ((tenant.active_routers_count ?? 0) / Math.max(1, tenant.max_routers_quota)) * 100)}%`,
                  }"
                ></div>
              </div>
              <span class="quota-text"
                >{{ tenant.active_routers_count ?? 0 }} / {{ tenant.max_routers_quota }}</span
              >
            </td>
            <td class="cell-quota">
              <div class="quota-bar-track">
                <div
                  class="quota-bar-fill"
                  :style="{
                    width: `${Math.min(100, ((tenant.active_users_count ?? 0) / Math.max(1, tenant.max_users_quota)) * 100)}%`,
                  }"
                ></div>
              </div>
              <span class="quota-text">{{ tenant.active_users_count ?? 0 }} / {{ tenant.max_users_quota }}</span>
            </td>
            <td class="cell-safemode">{{ tenant.default_safemode_seconds }}s</td>
            <td class="col-actions">
              <button
                v-if="authStore.currentRole === 'SUPERADMIN_GLOBAL'"
                :id="`btn-edit-tenant-${tenant.slug}`"
                type="button"
                class="btn-action btn-action--edit"
                :aria-label="`Editar datos y cuotas de ${tenant.name}`"
                @click="openEditTenantModal(tenant)"
              >
                {{ t('tenants_mgmt.btn_edit_tenant', '✏️ Editar') }}
              </button>
              <button
                type="button"
                class="btn-action btn-action--features"
                :aria-label="`Configurar módulos y capacidades de ${tenant.name}`"
                @click="goToTenantModules(tenant)"
              >
                {{ t('tenants_mgmt.btn_modules_studio', '⚙️ Módulos Studio') }}
                <span v-if="countActiveModules(tenant) > 0" class="badge-modules-count">
                  {{ countActiveModules(tenant) }}
                </span>
              </button>
              <button
                v-if="authStore.currentRole === 'SUPERADMIN_GLOBAL'"
                type="button"
                class="btn-action"
                :class="{ 'btn-action--danger': tenant.status === 'ACTIVE' }"
                @click="toggleSuspendTenant(tenant)"
              >
                {{ tenant.status === 'ACTIVE' ? t('tenants_mgmt.btn_suspend_tenant', 'Suspender') : t('tenants_mgmt.btn_activate_tenant', 'Reactivar') }}
              </button>
            </td>
          </tr>
          <tr v-if="tenants.length === 0 && !isLoading">
            <td colspan="8" class="cell-empty">No hay organizaciones registradas.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal de Creación de Empresa -->
    <div
      v-if="isCreateModalOpen"
      id="modal-create-tenant"
      class="rg-modal-backdrop"
      @click.self="isCreateModalOpen = false"
    >
      <div class="rg-modal" role="dialog" aria-modal="true" aria-labelledby="modal-tenant-title">
        <header class="modal-header">
          <h2 id="modal-tenant-title" class="modal-title">Registrar Nueva Organización</h2>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar modal"
            @click="isCreateModalOpen = false"
          >
            ✕
          </button>
        </header>

        <form class="modal-form" @submit.prevent="handleCreateTenant">
          <div class="form-row">
            <div class="form-group">
              <label for="tenant-name" class="form-label">Nombre Comercial *</label>
              <input
                id="tenant-name"
                v-model="newTenant.name"
                type="text"
                required
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="tenant-slug-new" class="form-label">Slug de Subdominio *</label>
              <input
                id="tenant-slug-new"
                v-model="newTenant.slug"
                type="text"
                required
                pattern="[a-z0-9-]+"
                placeholder="ej. isp-este"
                class="form-input"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="tenant-tax-id" class="form-label">RIF / Identificación Fiscal</label>
              <input id="tenant-tax-id" v-model="newTenant.tax_id" type="text" class="form-input" />
            </div>
            <div class="form-group">
              <label for="tenant-safemode" class="form-label"
                >Safe Mode por Defecto (segundos)</label
              >
              <input
                id="tenant-safemode"
                v-model.number="newTenant.default_safemode_seconds"
                type="number"
                min="10"
                max="300"
                class="form-input"
              />
            </div>
          </div>

          <fieldset class="form-fieldset">
            <legend class="fieldset-legend">Cuotas Asignadas</legend>
            <div class="form-row">
              <div class="form-group">
                <label for="max-routers" class="form-label">Límite de Routers *</label>
                <input
                  id="max-routers"
                  v-model.number="newTenant.max_routers_quota"
                  type="number"
                  min="1"
                  required
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <label for="max-users" class="form-label">Límite de Usuarios *</label>
                <input
                  id="max-users"
                  v-model.number="newTenant.max_users_quota"
                  type="number"
                  min="1"
                  required
                  class="form-input"
                />
              </div>
            </div>
          </fieldset>

          <fieldset class="form-fieldset">
            <legend class="fieldset-legend">Administrador Inicial (TENANT_ADMIN)</legend>
            <div class="form-row">
              <div class="form-group">
                <label for="admin-user" class="form-label">Username *</label>
                <input
                  id="admin-user"
                  v-model="newTenant.admin_username"
                  type="text"
                  required
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <label for="admin-email" class="form-label">Correo *</label>
                <input
                  id="admin-email"
                  v-model="newTenant.admin_email"
                  type="email"
                  required
                  class="form-input"
                />
              </div>
            </div>
            <div class="form-group">
              <label for="admin-pass" class="form-label">Contraseña Temporal *</label>
              <input
                id="admin-pass"
                v-model="newTenant.admin_password"
                type="password"
                required
                class="form-input"
              />
            </div>
          </fieldset>

          <fieldset class="form-fieldset">
            <legend class="fieldset-legend">Geolocalización Sede Principal (Spec 104)</legend>
            <div class="form-row">
              <div class="form-group">
                <label for="input-tenant-hq-lat" class="form-label">Latitud Sede Principal</label>
                <input
                  id="input-tenant-hq-lat"
                  v-model.number="newTenant.hq_latitude"
                  type="number"
                  step="0.000001"
                  min="-90"
                  max="90"
                  class="form-input"
                  placeholder="ej. 10.480600"
                />
              </div>
              <div class="form-group">
                <label for="input-tenant-hq-lng" class="form-label">Longitud Sede Principal</label>
                <input
                  id="input-tenant-hq-lng"
                  v-model.number="newTenant.hq_longitude"
                  type="number"
                  step="0.000001"
                  min="-180"
                  max="180"
                  class="form-input"
                  placeholder="ej. -66.903600"
                />
              </div>
            </div>
            <button
              id="btn-tenant-capture-gps"
              type="button"
              class="btn-gps"
              style="margin-top: var(--rg-space-2);"
              :disabled="isCapturingGps"
              @click="captureBrowserGps('create')"
            >
              📍 {{ isCapturingGps ? 'Capturando...' : 'Capturar GPS Sede' }}
            </button>
          </fieldset>

          <footer class="modal-footer">
            <button type="button" class="btn-cancel" @click="isCreateModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-submit" :disabled="isCreating">
              {{ isCreating ? 'Creando...' : 'Crear Organización' }}
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal de Edición de Empresa y Cuotas -->
    <div
      v-if="isEditModalOpen"
      id="modal-edit-tenant"
      class="rg-modal-backdrop"
      @click.self="isEditModalOpen = false"
    >
      <div class="rg-modal" role="dialog" aria-modal="true" aria-labelledby="modal-edit-tenant-title">
        <header class="modal-header">
          <h2 id="modal-edit-tenant-title" class="modal-title">
            {{ t('tenants_mgmt.modal_edit_title', 'Editar Organización y Cuotas') }}
          </h2>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar modal de edición"
            @click="isEditModalOpen = false"
          >
            ✕
          </button>
        </header>

        <form id="form-edit-tenant" class="modal-form" @submit.prevent="handleUpdateTenant">
          <div class="form-row">
            <div class="form-group">
              <label for="edit-tenant-name" class="form-label">Nombre Comercial *</label>
              <input
                id="edit-tenant-name"
                v-model="editingTenant.name"
                type="text"
                required
                minlength="2"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="edit-tenant-slug" class="form-label">Slug de Subdominio *</label>
              <input
                id="edit-tenant-slug"
                v-model="editingTenant.slug"
                type="text"
                required
                pattern="[a-z0-9-]+"
                class="form-input"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="edit-tenant-tax-id" class="form-label">RIF / Identificación Fiscal</label>
              <input
                id="edit-tenant-tax-id"
                v-model="editingTenant.tax_id"
                type="text"
                placeholder="ej. J-12345678-9"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="edit-tenant-safemode" class="form-label">
                Safe Mode por Defecto (segundos)
              </label>
              <input
                id="edit-tenant-safemode"
                v-model.number="editingTenant.default_safemode_seconds"
                type="number"
                min="10"
                max="300"
                required
                class="form-input"
              />
            </div>
          </div>

          <fieldset class="form-fieldset">
            <legend class="fieldset-legend">Cuotas de Hardware y Operadores</legend>
            <div class="form-row">
              <div class="form-group">
                <label for="edit-max-routers" class="form-label">Límite de Routers *</label>
                <input
                  id="edit-max-routers"
                  v-model.number="editingTenant.max_routers_quota"
                  type="number"
                  min="1"
                  required
                  class="form-input"
                />
              </div>
              <div class="form-group">
                <label for="edit-max-users" class="form-label">Límite de Usuarios *</label>
                <input
                  id="edit-max-users"
                  v-model.number="editingTenant.max_users_quota"
                  type="number"
                  min="1"
                  required
                  class="form-input"
                />
              </div>
            </div>
            <label class="switch-row" for="edit-require-2fa">
              <input
                id="edit-require-2fa"
                v-model="editingTenant.require_2fa_all_users"
                type="checkbox"
                class="switch-input"
              />
              <span>Exigir autenticación 2FA TOTP obligatoria para todos los usuarios</span>
            </label>
          </fieldset>

          <fieldset class="form-fieldset">
            <legend class="fieldset-legend">Geolocalización Sede Principal (Spec 104)</legend>
            <div class="form-row">
              <div class="form-group">
                <label for="edit-tenant-hq-lat" class="form-label">Latitud Sede Principal</label>
                <input
                  id="edit-tenant-hq-lat"
                  v-model.number="editingTenant.hq_latitude"
                  type="number"
                  step="0.000001"
                  min="-90"
                  max="90"
                  class="form-input"
                  placeholder="ej. 10.480600"
                />
              </div>
              <div class="form-group">
                <label for="edit-tenant-hq-lng" class="form-label">Longitud Sede Principal</label>
                <input
                  id="edit-tenant-hq-lng"
                  v-model.number="editingTenant.hq_longitude"
                  type="number"
                  step="0.000001"
                  min="-180"
                  max="180"
                  class="form-input"
                  placeholder="ej. -66.903600"
                />
              </div>
            </div>
            <button
              id="btn-tenant-capture-gps-edit"
              type="button"
              class="btn-gps"
              style="margin-top: var(--rg-space-2);"
              :disabled="isCapturingGps"
              @click="captureBrowserGps('edit')"
            >
              📍 {{ isCapturingGps ? 'Capturando...' : 'Capturar GPS Sede' }}
            </button>
          </fieldset>

          <footer class="modal-footer">
            <button
              id="btn-cancel-edit-tenant"
              type="button"
              class="btn-cancel"
              @click="isEditModalOpen = false"
            >
              Cancelar
            </button>
            <button
              id="btn-save-edit-tenant"
              type="submit"
              class="btn-submit"
              :disabled="isUpdating"
            >
              {{ isUpdating ? 'Guardando...' : 'Guardar Cambios' }}
            </button>
          </footer>
        </form>
      </div>
    </div>

  </div>
</template>

<style scoped>
  .tenants-view {
    padding: 24px;
    background-color: var(--rg-bg-canvas, #0b0f19);
    min-height: 100%;
  }

  .view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 16px;
  }

  .view-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--rg-accent-cyan, #22d3ee);
    margin: 0;
  }

  .view-subtitle {
    font-size: 0.85rem;
    color: var(--rg-text-muted, #94a3b8);
    margin: 4px 0 0 0;
  }

  .btn-create {
    background-color: var(--rg-accent-cyan, #22d3ee);
    color: #0b0f19;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-weight: 700;
    cursor: pointer;
    transition: background-color 0.15s ease, box-shadow 0.15s ease;
  }

  .btn-create:hover {
    background-color: var(--rg-cyan-300, #67e8f9);
    box-shadow: var(--rg-cyan-glow, 0 0 12px rgba(6, 182, 212, 0.28));
  }

  .beacon-card {
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-left: 3px solid var(--rg-accent-cyan, #22d3ee);
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 14px;
    box-shadow: var(--rg-shadow-sm);
  }

  .beacon-card__info {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .beacon-card__header {
    font-size: 0.92rem;
    font-weight: 700;
    color: var(--rg-accent-cyan, #22d3ee);
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .beacon-card__meta {
    margin: 0;
    font-size: 0.8rem;
    color: var(--rg-text-muted, #94a3b8);
    line-height: 1.5;
  }

  .beacon-mono {
    font-family: var(--rg-font-mono, 'JetBrains Mono', monospace);
    color: var(--rg-text-secondary, #cbd5e1);
    background: rgba(34, 211, 238, 0.08);
    padding: 1px 6px;
    border-radius: 4px;
  }

  .beacon-fleet {
    color: #38bdf8;
    font-weight: 600;
  }

  .beacon-timestamp {
    font-family: var(--rg-font-mono, 'JetBrains Mono', monospace);
    color: var(--rg-text-secondary, #cbd5e1);
  }

  .beacon-status-code {
    margin-left: 6px;
    font-family: var(--rg-font-mono, 'JetBrains Mono', monospace);
    font-weight: 600;
    color: #34d399;
  }

  .btn-beacon {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid #38bdf8;
    color: #38bdf8;
    padding: 8px 14px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition:
      background-color 0.15s ease,
      border-color 0.15s ease,
      color 0.15s ease,
      box-shadow 0.15s ease,
      transform 0.1s ease;
    white-space: nowrap;
  }

  .btn-beacon:hover:not(:disabled) {
    background: rgba(56, 189, 248, 0.2);
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-text-primary, #f8fafc);
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.25);
  }

  .btn-beacon:active:not(:disabled) {
    transform: translateY(1px);
  }

  .btn-beacon:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .badge-status--silent {
    background: rgba(100, 116, 139, 0.2);
    color: var(--rg-text-muted, #94a3b8);
    border: 1px solid var(--rg-border-panel, #334155);
  }

  .banner {
    padding: 12px 16px;
    border-radius: 6px;
    margin-bottom: 16px;
    font-size: 0.85rem;
  }

  .banner--error {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #f87171;
  }

  .banner--success {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #34d399;
  }

  .table-container {
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 8px;
    overflow-x: auto;
  }

  .rg-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    text-align: left;
  }

  .rg-table th {
    background-color: var(--rg-bg-elevated, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 10px 14px;
    border-bottom: 1px solid var(--rg-border-grid, #334155);
  }

  .rg-table td {
    padding: 12px 14px;
    border-bottom: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-primary, #f8fafc);
  }

  .cell-slug code {
    font-family: 'JetBrains Mono', monospace;
    color: var(--rg-accent-cyan, #22d3ee);
    background: rgba(34, 211, 238, 0.1);
    padding: 2px 6px;
    border-radius: 4px;
  }

  .badge-status {
    font-size: 0.75rem;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 600;
  }

  .badge-status--active {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid #10b981;
  }

  .badge-status--suspended {
    background: rgba(239, 68, 68, 0.15);
    color: #f87171;
    border: 1px solid #ef4444;
  }

  .quota-bar-track {
    width: 100px;
    height: 6px;
    background: var(--rg-bg-canvas, #0b0f19);
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 4px;
  }

  .quota-bar-fill {
    height: 100%;
    background: var(--rg-accent-cyan, #22d3ee);
  }

  .quota-text {
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
    color: var(--rg-text-muted, #94a3b8);
  }

  .cell-safemode {
    font-family: 'JetBrains Mono', monospace;
    font-variant-numeric: tabular-nums;
  }

  .btn-action {
    background: transparent;
    border: 1px solid var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    padding: 4px 10px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.75rem;
  }

  .btn-action--danger {
    border-color: #ef4444;
    color: #f87171;
  }

  .cell-empty {
    text-align: center;
    padding: 32px;
    color: var(--rg-text-muted, #94a3b8);
  }

  .rg-modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(11, 15, 25, 0.8);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1050;
    padding: 16px;
  }

  .rg-modal {
    width: 100%;
    max-width: 600px;
    background: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 8px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid var(--rg-border-grid, #1e293b);
  }

  .modal-title {
    font-size: 1.15rem;
    color: var(--rg-accent-cyan, #22d3ee);
    margin: 0;
  }

  .btn-close {
    background: transparent;
    border: none;
    color: var(--rg-text-muted, #94a3b8);
    font-size: 1.2rem;
    cursor: pointer;
  }

  .modal-form {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .form-row {
    display: flex;
    gap: 12px;
  }

  .form-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .form-label {
    font-size: 0.8rem;
    color: var(--rg-text-secondary, #cbd5e1);
  }

  .form-input {
    padding: 8px 12px;
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    color: var(--rg-text-primary, #f8fafc);
    font-size: 0.85rem;
  }

  .form-fieldset {
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .fieldset-legend {
    font-size: 0.75rem;
    color: var(--rg-accent-cyan, #22d3ee);
    padding: 0 6px;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 8px;
  }

  .btn-submit {
    background: var(--rg-accent-cyan, #22d3ee);
    color: #0b0f19;
    border: none;
    padding: 8px 18px;
    border-radius: 6px;
    font-weight: 700;
    cursor: pointer;
  }

  .btn-cancel {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 8px 18px;
    border-radius: 6px;
    cursor: pointer;
  }

  .rg-modal--features {
    max-width: 720px;
    max-height: 90vh;
    overflow-y: auto;
  }

  .modal-subtitle {
    font-size: 0.8rem;
    color: var(--rg-text-muted, #94a3b8);
    margin: 2px 0 0;
  }

  .switches-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 8px 16px;
  }

  .switch-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    color: var(--rg-text-primary, #f8fafc);
    cursor: pointer;
    user-select: none;
  }

  .switch-input {
    accent-color: var(--rg-accent-cyan, #22d3ee);
    width: 16px;
    height: 16px;
    cursor: pointer;
  }

  .btn-action--edit {
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    margin-right: 6px;
  }

  .btn-action--features {
    border-color: #38bdf8;
    color: #38bdf8;
    margin-right: 6px;
  }

  .btn-action--features:hover {
    background: rgba(56, 189, 248, 0.15);
  }

  .badge-modules-count {
    display: inline-block;
    font-size: 10px;
    font-family: var(--rg-font-mono, monospace);
    background: rgba(56, 189, 248, 0.2);
    color: #38bdf8;
    padding: 1px 5px;
    border-radius: 4px;
    font-weight: 700;
    margin-left: 3px;
  }

  .btn-gps {
    display: inline-flex;
    align-items: center;
    gap: var(--rg-space-2, 8px);
    padding: var(--rg-space-2, 8px) var(--rg-space-3, 12px);
    background: var(--rg-surface-hover, rgba(255, 255, 255, 0.05));
    border: 1px solid var(--rg-border, #334155);
    border-radius: var(--rg-radius-md, 6px);
    color: var(--rg-text, #f8fafc);
    font-size: var(--rg-font-sm, 0.875rem);
    font-weight: 500;
    cursor: pointer;
    transition: background 0.15s ease, border-color 0.15s ease;
  }

  .btn-gps:hover:not(:disabled) {
    background: rgba(6, 182, 212, 0.15);
    border-color: var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
  }

  .btn-gps:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
