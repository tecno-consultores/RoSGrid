<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { http } from '@/api/httpClient';
  import { useAuthStore } from '@/stores/useAuthStore';
  import type { SystemRole, UserManagementItem, McpTokenResponse } from '@/types';
  import RgStepUp2FAModal from '@/components/common/RgStepUp2FAModal.vue';
  import ChangePasswordModal from '@/components/common/ChangePasswordModal.vue';
  import UserRouterMatrixModal from '@/components/admin/UserRouterMatrixModal.vue';
  import RbacRoleMatrixPanel from '@/components/admin/RbacRoleMatrixPanel.vue';
  import RgMcpTokenModal from '@/components/admin/RgMcpTokenModal.vue';

  const route = useRoute();
  const router = useRouter();

  // Control de Pestañas: 'users' (Operadores) | 'roles' (Matriz de Políticas RBAC)
  const activeTab = ref<'users' | 'roles'>((route?.query?.tab as 'users' | 'roles') || 'users');

  function selectTab(tab: 'users' | 'roles') {
    activeTab.value = tab;
    if (router && route) {
      router.replace({ query: { ...route.query, tab } }).catch(() => {});
    }
  }

  const authStore = useAuthStore();

  const isWriteAuthorized = computed(() => {
    const r = authStore.currentRole;
    return r === 'SUPERADMIN_GLOBAL' || r === 'TENANT_ADMIN';
  });

  const isLoading = ref(false);
  const errorMessage = ref('');
  const successMessage = ref('');
  const usersList = ref<UserManagementItem[]>([]);

  // Filtros
  const searchFilter = ref('');
  const roleFilter = ref<string>('ALL');
  const statusFilter = ref<string>('ALL');

  // Modal Crear Usuario
  const isCreateUserModalOpen = ref(false);
  const isCreating = ref(false);
  const newUser = ref({
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'SUPPORT_L2' as SystemRole,
    allowed_cidr_list: '',
    has_all_routers_access: false,
  });

  // Modal Step-Up para Reset 2FA
  const isStepUpReset2FAOpen = ref(false);
  const targetUserForReset = ref<UserManagementItem | null>(null);

  // Modal Matriz de Routers
  const isMatrixModalOpen = ref(false);
  const selectedUserForMatrix = ref<UserManagementItem | null>(null);

  // Modal Generador de Token MCP (Agentes IA)
  const isMcpTokenModalOpen = ref(false);
  const targetUserForMcp = ref<UserManagementItem | null>(null);

  // Modal de Cambio de Clave
  const isChangePasswordModalOpen = ref(false);
  const targetUserForPassword = ref<{ id: string; username: string } | null>(null);

  function openChangePasswordModal(user: UserManagementItem) {
    targetUserForPassword.value = { id: user.id, username: user.username };
    isChangePasswordModalOpen.value = true;
  }

  function handlePasswordChanged() {
    successMessage.value = `Contraseña actualizada exitosamente.`;
    setTimeout(() => {
      successMessage.value = '';
    }, 4000);
  }

  function openMcpTokenModal(user: UserManagementItem) {
    targetUserForMcp.value = user;
    isMcpTokenModalOpen.value = true;
  }

  function handleMcpTokenGenerated(res: McpTokenResponse) {
    successMessage.value = `Token MCP generado exitosamente para @${res.username}.`;
    setTimeout(() => {
      successMessage.value = '';
    }, 4000);
  }

  // 11 Roles Oficiales del Sistema RoSGrid
  const availableRoles: SystemRole[] = [
    'SUPERADMIN_GLOBAL',
    'TENANT_ADMIN',
    'SUPERVISOR',
    'SUPPORT_L3',
    'SUPPORT_L2',
    'SUPPORT_L1',
    'FIELD_TECH',
    'INVENTORY_MANAGER',
    'AUDITOR',
    'NOC_MONITOR',
    'SERVICE_ACCOUNT',
  ];

  // Metadatos y Descripciones de Roles para Administradores de Empresa
  const ROLE_DETAILS: Record<
    string,
    { title: string; description: string; level: number; badgeColor: string }
  > = {
    SUPERADMIN_GLOBAL: {
      title: 'Superadministrador Global',
      description:
        'Control total de la plataforma multitenant, administración de empresas, auditoría WORM forense y configuración de infraestructura central.',
      level: 0,
      badgeColor: '#a855f7',
    },
    TENANT_ADMIN: {
      title: 'Administrador de Organización',
      description:
        'Máxima autoridad dentro de la empresa o tenant. Gestiona operadores, asigna routers, aprueba cambios Maker-Checker, descarga respaldos y configura redes.',
      level: 1,
      badgeColor: '#22d3ee',
    },
    SUPERVISOR: {
      title: 'Supervisor de Operaciones NOC',
      description:
        'Supervisión técnica de cuadrillas. Aprueba cambios Maker-Checker, visualiza auditorías, programa mantenimientos y aprueba operaciones de Soporte L1/L2.',
      level: 2,
      badgeColor: '#10b981',
    },
    SUPPORT_L3: {
      title: 'Soporte Técnico Nivel 3 (Senior)',
      description:
        'Ingeniería de red avanzada. Ejecuta diagnósticos profundos, modifica configuraciones L1/L2, despliega túneles VPN, enrutamiento BGP/OSPF y aprueba cambios técnicos.',
      level: 3,
      badgeColor: '#3b82f6',
    },
    SUPPORT_L2: {
      title: 'Soporte Técnico Nivel 2',
      description:
        'Operador de segundo nivel. Gestiona interfaces, diagnostica enlaces en vivo (Ping/Torch/Logs) y reinicia sesiones PPPoE. Cambios críticos pasan por Maker-Checker.',
      level: 4,
      badgeColor: '#f59e0b',
    },
    SUPPORT_L1: {
      title: 'Soporte Técnico Nivel 1 (Helpdesk)',
      description:
        'Atención primaria a clientes e incidencias. Monitorea estado de routers, visualiza sesiones activas y ejecuta diagnósticos básicos sin modificar configuración directamente.',
      level: 5,
      badgeColor: '#94a3b8',
    },
    FIELD_TECH: {
      title: 'Técnico de Campo (Terreno)',
      description:
        'Personal técnico en sitio. Diagnostica puertos físicos, prueba transceptores ópticos SFP DDM y cableado TDR para validar conectividad en torres y racks.',
      level: 6,
      badgeColor: '#f97316',
    },
    INVENTORY_MANAGER: {
      title: 'Gestor de Inventario y Activos',
      description:
        'Responsable de hardware MikroTik. Da de alta routers, realiza importaciones masivas por CSV, programa ventanas de mantenimiento y rota credenciales en bóveda.',
      level: 7,
      badgeColor: '#14b8a6',
    },
    AUDITOR: {
      title: 'Auditor de Seguridad y Cumplimiento',
      description:
        'Auditoría forense de solo lectura estricta. Inspecciona la cadena inmutable WORM SHA-256, revisa logs de acceso y exporta informes certificados sin alterar nada.',
      level: 8,
      badgeColor: '#6366f1',
    },
    NOC_MONITOR: {
      title: 'Operador de Monitoreo NOC 24/7',
      description:
        'Vigilancia continua del estado de red. Visualiza Wallboard, mapas de topología OSM, métricas de telemetría y alarmas sin permisos de escritura ni cambios.',
      level: 9,
      badgeColor: '#38bdf8',
    },
    SERVICE_ACCOUNT: {
      title: 'Cuenta de Servicio / API / Agentes IA',
      description:
        'Identidad para integraciones automatizadas, agentes IA MCP, sondas externas y recolección de telemetría con permisos específicos de ejecución.',
      level: 10,
      badgeColor: '#8b5cf6',
    },
  };

  // Gestión de Auto-Registro Público
  const isRegistrationEnabled = ref(true);
  const isTogglingRegistration = ref(false);

  // Modal y Acciones de Aprobación
  const isApproveModalOpen = ref(false);
  const targetUserForApproval = ref<UserManagementItem | null>(null);
  const isApproving = ref(false);
  const approvalForm = ref({
    role: 'SUPPORT_L2' as SystemRole,
    has_all_routers_access: false,
    allowed_cidr_list: '',
  });

  const filteredUsers = computed(() => {
    return usersList.value.filter((u) => {
      const q = searchFilter.value.trim().toLowerCase();
      const matchesSearch =
        !q ||
        u.username.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        (u.full_name && u.full_name.toLowerCase().includes(q));

      const matchesRole = roleFilter.value === 'ALL' || u.role === roleFilter.value;
      const matchesStatus =
        statusFilter.value === 'ALL' ||
        (statusFilter.value === 'ACTIVE' && u.is_active) ||
        (statusFilter.value === 'PENDING' && !u.is_active && !u.totp_enabled) ||
        (statusFilter.value === 'INACTIVE' && !u.is_active && u.totp_enabled);

      return matchesSearch && matchesRole && matchesStatus;
    });
  });

  async function loadRegistrationStatus() {
    try {
      const res = await http.get<{ registration_enabled?: boolean }>(
        '/api/v1/auth/bootstrap-status',
      );
      if (res.data && res.data.registration_enabled !== undefined) {
        isRegistrationEnabled.value = res.data.registration_enabled;
      }
    } catch {
      // Ignorar fallback
    }
  }

  async function toggleRegistration() {
    isTogglingRegistration.value = true;
    try {
      const nextVal = !isRegistrationEnabled.value;
      await http.post('/api/v1/users/registration-toggle', { enabled: nextVal });
      isRegistrationEnabled.value = nextVal;
      successMessage.value = nextVal
        ? 'Auto-registro público HABILITADO. Nuevos operadores pueden registrarse desde el login.'
        : 'Auto-registro público DESHABILITADO. Se bloquean nuevos registros externos.';
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      errorMessage.value =
        error.detail || error.message || 'Error al cambiar estado de auto-registro.';
    } finally {
      isTogglingRegistration.value = false;
    }
  }

  function openApproveModal(user: UserManagementItem) {
    targetUserForApproval.value = user;
    approvalForm.value = {
      role: 'SUPPORT_L2',
      has_all_routers_access: false,
      allowed_cidr_list: '',
    };
    isApproveModalOpen.value = true;
  }

  async function handleApproveUser() {
    if (!targetUserForApproval.value) return;
    isApproving.value = true;
    try {
      const cidrList = approvalForm.value.allowed_cidr_list
        ? approvalForm.value.allowed_cidr_list
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean)
        : undefined;

      await http.put(`/api/v1/users/${targetUserForApproval.value.id}/approve`, {
        role: approvalForm.value.role,
        has_all_routers_access: approvalForm.value.has_all_routers_access,
        allowed_cidr_list: cidrList,
      });

      targetUserForApproval.value.is_active = true;
      targetUserForApproval.value.role = approvalForm.value.role;
      targetUserForApproval.value.has_all_routers_access =
        approvalForm.value.has_all_routers_access;
      if (cidrList) targetUserForApproval.value.allowed_cidr_list = cidrList;

      isApproveModalOpen.value = false;
      successMessage.value = `Operador @${targetUserForApproval.value.username} aprobado y activado con rol ${approvalForm.value.role}.`;
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      errorMessage.value = error.detail || error.message || 'Error al aprobar usuario.';
    } finally {
      isApproving.value = false;
    }
  }

  async function handleRejectUser(user: UserManagementItem) {
    const confirmed = window.confirm(
      `¿Confirmas el rechazo y eliminación de la solicitud del operador @${user.username}?`,
    );
    if (!confirmed) return;

    try {
      await http.delete(`/api/v1/users/${user.id}/reject`);
      usersList.value = usersList.value.filter((u) => u.id !== user.id);
      successMessage.value = `Solicitud de @${user.username} rechazada y eliminada del sistema.`;
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const error = err as { detail?: string; message?: string };
      errorMessage.value = error.detail || error.message || 'Error al rechazar usuario.';
    }
  }

  async function loadUsers() {
    isLoading.value = true;
    errorMessage.value = '';
    try {
      const res = await http.get<UserManagementItem[] | { items: UserManagementItem[] }>(
        '/api/v1/users',
      );
      const raw = Array.isArray(res.data) ? res.data : res.data?.items || [];
      usersList.value = raw;
    } catch {
      // Sin datos de demostración en producción
      usersList.value = [];
    } finally {
      isLoading.value = false;
    }
  }

  function openReset2FAModal(user: UserManagementItem) {
    targetUserForReset.value = user;
    isStepUpReset2FAOpen.value = true;
  }

  async function handleStepUpReset2FA(totpCode: string) {
    if (!targetUserForReset.value) return;
    try {
      await http.post(`/api/v1/users/${targetUserForReset.value.id}/reset-2fa`, {
        stepup_totp_code: totpCode,
      });

      targetUserForReset.value.totp_enabled = false;
      isStepUpReset2FAOpen.value = false;
      successMessage.value = `2FA reiniciado con éxito para @${targetUserForReset.value.username}.`;
      setTimeout(() => {
        successMessage.value = '';
      }, 4000);
    } catch (err: unknown) {
      const error = err as { message?: string; detail?: string };
      errorMessage.value = error.detail || error.message || 'Error al reiniciar 2FA con Step-Up.';
    }
  }

  function openMatrixModal(user: UserManagementItem) {
    selectedUserForMatrix.value = user;
    isMatrixModalOpen.value = true;
  }

  async function handleCreateUser() {
    isCreating.value = true;
    errorMessage.value = '';

    const cidrList = newUser.value.allowed_cidr_list
      ? newUser.value.allowed_cidr_list
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean)
      : [];

    try {
      const payload = {
        username: newUser.value.username.trim(),
        email: newUser.value.email.trim(),
        temporary_password: newUser.value.password,
        password: newUser.value.password,
        full_name: newUser.value.full_name.trim() || newUser.value.username.trim(),
        role: newUser.value.role,
        allowed_cidr_list: cidrList,
        has_all_routers_access: Boolean(newUser.value.has_all_routers_access),
      };

      const res = await http.post<UserManagementItem | { user: UserManagementItem }>(
        '/api/v1/users',
        payload,
      );

      const createdUser = (
        res.data && 'user' in res.data ? res.data.user : res.data
      ) as UserManagementItem;
      if (createdUser && createdUser.id) {
        usersList.value.push(createdUser);
      }

      isCreateUserModalOpen.value = false;
      successMessage.value = `Usuario @${newUser.value.username} creado exitosamente.`;
      // Limpiar formulario
      newUser.value = {
        username: '',
        email: '',
        password: '',
        full_name: '',
        role: 'SUPPORT_L2',
        allowed_cidr_list: '',
        has_all_routers_access: false,
      };
      await loadUsers();
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
      errorMessage.value = detailStr || 'Error al crear el operador.';
    } finally {
      isCreating.value = false;
    }
  }

  onMounted(() => {
    loadUsers();
    loadRegistrationStatus();
  });
</script>

<template>
  <div class="users-view">
    <header class="view-header">
      <div>
        <h1 class="view-title">Gestión de Usuarios y Roles RBAC (11 Roles)</h1>
        <p class="view-subtitle">
          Control de acceso técnico, definición de permisos por rol, reinicio de 2FA y matriz de
          routers.
        </p>
      </div>

      <div v-if="activeTab === 'users' && isWriteAuthorized" class="header-actions">
        <button
          type="button"
          class="btn-toggle-reg"
          :class="{
            'btn-toggle-reg--enabled': isRegistrationEnabled,
            'btn-toggle-reg--disabled': !isRegistrationEnabled,
          }"
          :disabled="isTogglingRegistration"
          @click="toggleRegistration"
        >
          {{
            isRegistrationEnabled ? '🔓 Auto-Registro: Activado' : '🔒 Auto-Registro: Desactivado'
          }}
        </button>

        <button type="button" class="btn-create" @click="isCreateUserModalOpen = true">
          + Nuevo Operador
        </button>
      </div>
    </header>

    <!-- Navegación de Pestañas de la Sección Usuarios & RBAC -->
    <div class="rbac-tabs-nav" role="tablist" aria-label="Secciones de Usuarios y RBAC">
      <button
        id="tab-users"
        type="button"
        role="tab"
        class="rbac-tab-btn"
        :class="{ 'rbac-tab-btn--active': activeTab === 'users' }"
        :aria-selected="activeTab === 'users'"
        aria-controls="tabpanel-users"
        @click="selectTab('users')"
      >
        <span class="tab-btn-icon" aria-hidden="true">👥</span>
        <span class="tab-btn-text">Operadores &amp; Cuentas</span>
        <span class="tab-btn-badge">{{ usersList.length }}</span>
      </button>

      <button
        id="tab-roles"
        type="button"
        role="tab"
        class="rbac-tab-btn"
        :class="{ 'rbac-tab-btn--active': activeTab === 'roles' }"
        :aria-selected="activeTab === 'roles'"
        aria-controls="tabpanel-roles"
        @click="selectTab('roles')"
      >
        <span class="tab-btn-icon" aria-hidden="true">🛡️</span>
        <span class="tab-btn-text">Perfiles &amp; Matriz de Permisos</span>
        <span class="tab-btn-badge tab-btn-badge--cyan">11 Roles</span>
      </button>
    </div>

    <!-- Pestaña 1: Operadores y Usuarios -->
    <div
      v-show="activeTab === 'users'"
      id="tabpanel-users"
      role="tabpanel"
      aria-labelledby="tab-users"
    >
      <div v-if="errorMessage" class="banner banner--error" role="alert">
        {{ errorMessage }}
      </div>
      <div v-if="successMessage" class="banner banner--success" role="status">
        {{ successMessage }}
      </div>

      <!-- Barra de Filtros Accesibles -->
      <div class="filters-bar">
        <div class="filter-item">
          <label for="filter-search" class="filter-label">Buscar Operador:</label>
          <input
            id="filter-search"
            v-model="searchFilter"
            type="search"
            placeholder="Nombre, username o correo..."
            class="filter-input"
          />
        </div>

        <div class="filter-item">
          <label for="filter-role" class="filter-label">Rol RBAC:</label>
          <select id="filter-role" v-model="roleFilter" class="filter-select">
            <option value="ALL">Todos los Roles (11)</option>
            <option v-for="r in availableRoles" :key="r" :value="r">{{ r }}</option>
          </select>
        </div>

        <div class="filter-item">
          <label for="filter-status" class="filter-label">Estado:</label>
          <select id="filter-status" v-model="statusFilter" class="filter-select">
            <option value="ALL">Todos los Estados</option>
            <option value="ACTIVE">Activos</option>
            <option value="PENDING">Pendientes de Aprobación</option>
            <option value="INACTIVE">Bloqueados</option>
          </select>
        </div>
      </div>

      <div class="table-container">
        <table class="rg-table" aria-label="Listado de usuarios y matriz RBAC">
          <thead>
            <tr>
              <th scope="col">Operador / Username</th>
              <th scope="col">Correo Electrónico</th>
              <th scope="col">Rol RBAC</th>
              <th scope="col">Estado 2FA</th>
              <th scope="col">Acceso Routers</th>
              <th scope="col">Estado</th>
              <th scope="col" class="col-actions">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in filteredUsers" :key="u.id">
              <td class="cell-user">
                <strong>{{ u.full_name || u.username }}</strong>
                <code class="user-handle">@{{ u.username }}</code>
              </td>
              <td>{{ u.email }}</td>
              <td>
                <span class="badge-role">{{ u.role }}</span>
              </td>
              <td>
                <span
                  class="badge-2fa"
                  :class="{
                    'badge-2fa--active': u.totp_enabled,
                    'badge-2fa--pending': !u.totp_enabled,
                  }"
                >
                  {{ u.totp_enabled ? '✓ Activo' : 'Pendiente' }}
                </span>
              </td>
              <td>
                <span v-if="u.has_all_routers_access" class="badge-access badge-access--all">
                  Todos (Global)
                </span>
                <span v-else class="badge-access badge-access--custom">
                  {{
                    u.assigned_router_ids ? `${u.assigned_router_ids.length} equipos` : 'Por Matriz'
                  }}
                </span>
              </td>
              <td>
                <span
                  class="badge-status"
                  :class="{
                    'badge-status--active': u.is_active,
                    'badge-status--pending': !u.is_active && !u.totp_enabled,
                    'badge-status--disabled': !u.is_active && u.totp_enabled,
                  }"
                >
                  {{ u.is_active ? 'Habilitado' : !u.totp_enabled ? '⏳ Pendiente' : 'Bloqueado' }}
                </span>
              </td>
              <td class="col-actions">
                <template v-if="!u.is_active && !u.totp_enabled">
                  <button
                    v-if="isWriteAuthorized"
                    type="button"
                    class="btn-approve"
                    aria-label="Aprobar operador y asignar rol"
                    @click="openApproveModal(u)"
                  >
                    ✓ Aprobar
                  </button>
                  <button
                    v-if="isWriteAuthorized"
                    type="button"
                    class="btn-reject"
                    aria-label="Rechazar solicitud"
                    @click="handleRejectUser(u)"
                  >
                    ✕ Rechazar
                  </button>
                </template>
                <template v-else>
                  <button
                    type="button"
                    class="btn-matrix"
                    aria-label="Abrir matriz de asignación de routers"
                    @click="openMatrixModal(u)"
                  >
                    ⚙ Matriz Routers
                  </button>

                  <button
                    v-if="isWriteAuthorized"
                    type="button"
                    class="btn-change-password"
                    aria-label="Cambiar o restablecer contraseña de este operador"
                    @click="openChangePasswordModal(u)"
                  >
                    🔑 Clave
                  </button>

                  <button
                    v-if="isWriteAuthorized && u.totp_enabled"
                    type="button"
                    class="btn-reset-2fa"
                    aria-label="Reiniciar 2FA de este operador"
                    @click="openReset2FAModal(u)"
                  >
                    ↺ Reset 2FA
                  </button>

                  <button
                    v-if="
                      isWriteAuthorized &&
                      (u.role === 'SERVICE_ACCOUNT' ||
                        u.role === 'TENANT_ADMIN' ||
                        u.role === 'SUPERADMIN_GLOBAL')
                    "
                    type="button"
                    class="btn-mcp"
                    aria-label="Generar Token de Acceso MCP para agentes IA"
                    @click="openMcpTokenModal(u)"
                  >
                    ⚡ Token MCP
                  </button>
                </template>
              </td>
            </tr>
            <tr v-if="filteredUsers.length === 0 && !isLoading">
              <td colspan="7" class="cell-empty">No se encontraron usuarios coincidentes.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Pestaña 2: Matriz de Roles y Permisos RBAC -->
    <div
      v-show="activeTab === 'roles'"
      id="tabpanel-roles"
      role="tabpanel"
      aria-labelledby="tab-roles"
    >
      <RbacRoleMatrixPanel />
    </div>

    <!-- Modal para Crear Usuario -->
    <div
      v-if="isCreateUserModalOpen"
      class="rg-modal-backdrop"
      @click.self="isCreateUserModalOpen = false"
    >
      <div class="rg-modal" role="dialog" aria-modal="true" aria-labelledby="modal-user-title">
        <header class="modal-header">
          <h2 id="modal-user-title" class="modal-title">Registrar Nuevo Operador</h2>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar modal"
            @click="isCreateUserModalOpen = false"
          >
            ✕
          </button>
        </header>

        <form class="modal-form" @submit.prevent="handleCreateUser">
          <div class="form-row">
            <div class="form-group">
              <label for="u-username" class="form-label">Username *</label>
              <input
                id="u-username"
                v-model="newUser.username"
                type="text"
                required
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="u-email" class="form-label">Correo Electrónico *</label>
              <input
                id="u-email"
                v-model="newUser.email"
                type="email"
                required
                class="form-input"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="u-fullname" class="form-label">Nombre y Apellido *</label>
              <input
                id="u-fullname"
                v-model="newUser.full_name"
                type="text"
                required
                placeholder="ej. Carlos Rodríguez"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="u-password" class="form-label"
                >Contraseña Temporal (Mínimo 8 car.) *</label
              >
              <input
                id="u-password"
                v-model="newUser.password"
                type="password"
                required
                minlength="8"
                placeholder="••••••••"
                class="form-input"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="u-role" class="form-label">Rol en la Organización *</label>
              <select id="u-role" v-model="newUser.role" class="form-select">
                <option v-for="r in availableRoles" :key="r" :value="r">{{ r }}</option>
              </select>
            </div>
            <div class="form-group">
              <label for="u-cidr" class="form-label">IPs / CIDRs Permitidos (Opcional)</label>
              <input
                id="u-cidr"
                v-model="newUser.allowed_cidr_list"
                type="text"
                placeholder="ej. 10.10.50.10/32, 192.168.1.0/24"
                class="form-input"
              />
            </div>
          </div>

          <!-- Cuadro de Información y Descripción del Rol para nuevos administradores -->
          <div
            v-if="ROLE_DETAILS[newUser.role]"
            class="role-desc-preview"
            role="region"
            aria-label="Descripción del rol seleccionado"
          >
            <div class="preview-header">
              <span
                class="preview-badge"
                :style="{
                  borderColor: ROLE_DETAILS[newUser.role].badgeColor,
                  color: ROLE_DETAILS[newUser.role].badgeColor,
                }"
              >
                Nivel {{ ROLE_DETAILS[newUser.role].level }}
              </span>
              <strong class="preview-title">{{ ROLE_DETAILS[newUser.role].title }}</strong>
            </div>
            <p class="preview-text">{{ ROLE_DETAILS[newUser.role].description }}</p>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="newUser.has_all_routers_access" type="checkbox" />
              <span>Conceder acceso global a todos los MikroTiks del Tenant</span>
            </label>
          </div>

          <footer class="modal-footer">
            <button type="button" class="btn-cancel" @click="isCreateUserModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-submit" :disabled="isCreating">
              {{ isCreating ? 'Creando...' : 'Crear Operador' }}
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal Step-Up para Confirmar Reset de 2FA -->
    <RgStepUp2FAModal
      :is-open="isStepUpReset2FAOpen"
      title="Step-Up 2FA Requerido para Resetear Credencial"
      @close="isStepUpReset2FAOpen = false"
      @submit-totp="handleStepUpReset2FA"
    />

    <!-- Modal de Matriz de Asignación de Equipos -->
    <UserRouterMatrixModal
      :is-open="isMatrixModalOpen"
      :user="selectedUserForMatrix"
      @close="isMatrixModalOpen = false"
      @saved="loadUsers"
    />

    <!-- Modal para Aprobar Operador y Asignar Rol Inicial -->
    <div
      v-if="isApproveModalOpen && targetUserForApproval"
      class="rg-modal-backdrop"
      @click.self="isApproveModalOpen = false"
    >
      <div class="rg-modal" role="dialog" aria-modal="true" aria-labelledby="modal-approve-title">
        <header class="modal-header">
          <h2 id="modal-approve-title" class="modal-title">
            Aprobar Operador: @{{ targetUserForApproval.username }}
          </h2>
          <button
            type="button"
            class="btn-close"
            aria-label="Cerrar modal"
            @click="isApproveModalOpen = false"
          >
            ✕
          </button>
        </header>

        <form class="modal-form" @submit.prevent="handleApproveUser">
          <p class="modal-desc">
            Asigna el rol técnico y permisos operativos para activar la cuenta de
            <strong>{{ targetUserForApproval.full_name || targetUserForApproval.username }}</strong>
            ({{ targetUserForApproval.email }}).
          </p>

          <div class="form-group">
            <label for="app-role" class="form-label">Rol RBAC Asignado *</label>
            <select id="app-role" v-model="approvalForm.role" class="form-select">
              <option v-for="r in availableRoles" :key="r" :value="r">{{ r }}</option>
            </select>
          </div>

          <!-- Cuadro de Información y Descripción del Rol para aprobación -->
          <div
            v-if="ROLE_DETAILS[approvalForm.role]"
            class="role-desc-preview"
            role="region"
            aria-label="Descripción del rol asignado"
          >
            <div class="preview-header">
              <span
                class="preview-badge"
                :style="{
                  borderColor: ROLE_DETAILS[approvalForm.role].badgeColor,
                  color: ROLE_DETAILS[approvalForm.role].badgeColor,
                }"
              >
                Nivel {{ ROLE_DETAILS[approvalForm.role].level }}
              </span>
              <strong class="preview-title">{{ ROLE_DETAILS[approvalForm.role].title }}</strong>
            </div>
            <p class="preview-text">{{ ROLE_DETAILS[approvalForm.role].description }}</p>
          </div>

          <div class="form-group">
            <label for="app-cidr" class="form-label">IPs / CIDRs Permitidos (Opcional)</label>
            <input
              id="app-cidr"
              v-model="approvalForm.allowed_cidr_list"
              type="text"
              placeholder="ej. 192.168.1.0/24, 10.0.0.5/32"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="approvalForm.has_all_routers_access" type="checkbox" />
              <span>Conceder acceso global a todos los MikroTiks del Tenant</span>
            </label>
          </div>

          <footer class="modal-footer">
            <button type="button" class="btn-cancel" @click="isApproveModalOpen = false">
              Cancelar
            </button>
            <button type="submit" class="btn-submit" :disabled="isApproving">
              {{ isApproving ? 'Activando...' : '✓ Aprobar y Activar Cuenta' }}
            </button>
          </footer>
        </form>
      </div>
    </div>

    <!-- Modal para Generación de Token MCP para Agentes IA -->
    <RgMcpTokenModal
      :is-open="isMcpTokenModalOpen"
      :user="targetUserForMcp"
      @close="isMcpTokenModalOpen = false"
      @token-generated="handleMcpTokenGenerated"
    />

    <!-- Modal para Cambio de Contraseña -->
    <ChangePasswordModal
      :is-open="isChangePasswordModalOpen"
      :target-user="targetUserForPassword"
      @close="isChangePasswordModalOpen = false"
      @password-changed="handlePasswordChanged"
    />
  </div>
</template>

<style scoped>
  .users-view {
    padding: 24px;
    background-color: var(--rg-bg-canvas, #0b0f19);
    min-height: 100%;
  }

  .view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 16px;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .btn-toggle-reg {
    padding: 9px 14px;
    border-radius: 6px;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition:
      background-color 0.2s,
      border-color 0.2s,
      color 0.2s;
  }

  .btn-toggle-reg--enabled {
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid #10b981;
    color: #34d399;
  }

  .btn-toggle-reg--enabled:hover:not(:disabled) {
    background: rgba(16, 185, 129, 0.25);
  }

  .btn-toggle-reg--disabled {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #f87171;
  }

  .btn-toggle-reg--disabled:hover:not(:disabled) {
    background: rgba(239, 68, 68, 0.25);
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

  .filters-bar {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
    flex-wrap: wrap;
    background: var(--rg-bg-surface, #111827);
    padding: 12px 16px;
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 8px;
  }

  .filter-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
    min-width: 180px;
  }

  .filter-label {
    font-size: 0.75rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .filter-input,
  .filter-select {
    padding: 8px 12px;
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    color: var(--rg-text-primary, #f8fafc);
    font-size: 0.85rem;
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
    white-space: nowrap;
  }

  .rg-table td {
    padding: 12px 14px;
    border-bottom: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-primary, #f8fafc);
  }

  .cell-user {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .user-handle {
    font-size: 0.75rem;
    color: var(--rg-accent-cyan, #22d3ee);
  }

  .badge-role {
    font-size: 0.75rem;
    background: rgba(34, 211, 238, 0.12);
    color: #22d3ee;
    padding: 3px 8px;
    border-radius: 4px;
    border: 1px solid rgba(34, 211, 238, 0.3);
  }

  .badge-2fa {
    font-size: 0.75rem;
    padding: 2px 6px;
    border-radius: 4px;
  }

  .badge-2fa--active {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
  }

  .badge-2fa--pending {
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
  }

  .badge-access {
    font-size: 0.75rem;
    padding: 2px 6px;
    border-radius: 4px;
  }

  .badge-access--all {
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
  }

  .badge-access--custom {
    background: rgba(148, 163, 184, 0.15);
    color: #cbd5e1;
  }

  .badge-status {
    font-size: 0.75rem;
    padding: 2px 6px;
    border-radius: 4px;
  }

  .badge-status--active {
    color: #34d399;
  }

  .badge-status--pending {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid #f59e0b;
    color: #fbbf24;
    animation: pulse-badge 2s infinite ease-in-out;
  }

  @keyframes pulse-badge {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.65;
    }
  }

  .badge-status--disabled {
    color: #f87171;
  }

  .btn-approve {
    background: rgba(16, 185, 129, 0.2);
    border: 1px solid #10b981;
    color: #34d399;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    margin-right: 6px;
    transition:
      background-color 0.2s,
      color 0.2s;
  }

  .btn-approve:hover {
    background: #10b981;
    color: #0b0f19;
  }

  .btn-reject {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid #ef4444;
    color: #f87171;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    cursor: pointer;
    transition:
      background-color 0.2s,
      color 0.2s;
  }

  .btn-reject:hover {
    background: #ef4444;
    color: #ffffff;
  }

  .modal-desc {
    font-size: 0.85rem;
    color: var(--rg-text-secondary, #cbd5e1);
    margin: 0;
    line-height: 1.4;
  }

  .btn-matrix {
    background: transparent;
    border: 1px solid var(--rg-accent-cyan, #22d3ee);
    color: var(--rg-accent-cyan, #22d3ee);
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    cursor: pointer;
    margin-right: 6px;
  }

  .btn-reset-2fa {
    background: transparent;
    border: 1px solid #f59e0b;
    color: #fbbf24;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    cursor: pointer;
    margin-right: 6px;
  }

  .btn-change-password {
    background: transparent;
    border: 1px solid #38bdf8;
    color: #38bdf8;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    cursor: pointer;
    margin-right: 6px;
    transition: background-color 0.15s, color 0.15s;
  }

  .btn-change-password:hover {
    background: rgba(56, 189, 248, 0.15);
    color: #fff;
  }

  .btn-mcp {
    background: transparent;
    border: 1px solid #a855f7;
    color: #c084fc;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    cursor: pointer;
    margin-right: 6px;
    transition: background-color 0.15s, color 0.15s;
  }

  .btn-mcp:hover {
    background: rgba(168, 85, 247, 0.15);
    color: #fff;
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

  .form-input,
  .form-select {
    padding: 8px 12px;
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 6px;
    color: var(--rg-text-primary, #f8fafc);
    font-size: 0.85rem;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-size: 0.85rem;
    color: var(--rg-text-secondary, #cbd5e1);
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

  /* Pestañas de Navegación Sección Usuarios & RBAC */
  .rbac-tabs-nav {
    display: flex;
    gap: 8px;
    margin-bottom: 20px;
    border-bottom: 1px solid var(--rg-border-grid, #1e293b);
    padding-bottom: 2px;
  }

  .rbac-tab-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 18px;
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--rg-text-muted, #94a3b8);
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    border-radius: 6px 6px 0 0;
  }

  .rbac-tab-btn:hover {
    color: var(--rg-text-primary, #f8fafc);
    background: rgba(255, 255, 255, 0.03);
  }

  .rbac-tab-btn--active {
    color: var(--rg-accent-cyan, #22d3ee);
    border-bottom-color: var(--rg-accent-cyan, #22d3ee);
    background: rgba(34, 211, 238, 0.06);
  }

  .tab-btn-icon {
    font-size: 1.1rem;
  }

  .tab-btn-text {
    font-weight: 600;
  }

  .tab-btn-badge {
    background: rgba(148, 163, 184, 0.15);
    color: var(--rg-text-muted, #94a3b8);
    font-size: 0.72rem;
    padding: 2px 7px;
    border-radius: 12px;
    font-weight: 600;
  }

  .tab-btn-badge--cyan {
    background: rgba(34, 211, 238, 0.15);
    color: #22d3ee;
  }

  /* Previsualización de Descripción del Rol en Modales */
  .role-desc-preview {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-left: 3px solid var(--rg-accent-cyan, #22d3ee);
    border-radius: 6px;
    padding: 10px 14px;
    margin-top: 8px;
    margin-bottom: 12px;
  }

  .preview-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
  }

  .preview-badge {
    font-size: 0.7rem;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 4px;
    border: 1px solid currentColor;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .preview-title {
    font-size: 0.82rem;
    color: var(--rg-text-primary, #f8fafc);
  }

  .preview-text {
    font-size: 0.78rem;
    line-height: 1.35;
    color: var(--rg-text-secondary, #cbd5e1);
    margin: 0;
  }

  .btn-mcp {
    background: rgba(56, 189, 248, 0.12);
    color: #38bdf8;
    border: 1px solid #0284c7;
    padding: 6px 10px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition:
      background-color 0.15s,
      color 0.15s;
    white-space: nowrap;
  }

  .btn-mcp:hover {
    background-color: #0284c7;
    color: #ffffff;
  }
</style>
