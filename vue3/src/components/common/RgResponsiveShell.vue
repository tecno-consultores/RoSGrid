<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useNocEventsStore } from '@/stores/useNocEventsStore';
  import { useThemeAndLayoutStore } from '@/stores/useThemeAndLayoutStore';
  import { useI18n } from '@/composables/useI18n';
  import { http } from '@/api/httpClient';
  import RgCommandPalette from './RgCommandPalette.vue';
  import RgSafeModeBanner from './RgSafeModeBanner.vue';
  import ChangePasswordModal from '@/components/common/ChangePasswordModal.vue';
  import RgStepUp2FAModal from '@/components/common/RgStepUp2FAModal.vue';
  import RgMcpTokenModal from '@/components/admin/RgMcpTokenModal.vue';

  const route = useRoute();
  const router = useRouter();
  const authStore = useAuthStore();
  const themeStore = useThemeAndLayoutStore();
  const nocStore = useNocEventsStore();
  const { t, locale, toggleLocale } = useI18n();

  const isRouterContext = computed(() => route.path.includes('/routers/'));
  const currentRouterId = computed(() => String(route.params.routerId || ''));

  // Estado del Menú Desplegable de Usuario
  const isUserMenuOpen = ref(false);
  const userMenuRef = ref<HTMLElement | null>(null);

  // Reloj Global del Sistema en Barra Superior (HH:MM sin segundos, reactivo a 24h/12h)
  const currentHeaderTime = ref('');
  let headerClockTimer: ReturnType<typeof setInterval> | null = null;

  function updateHeaderClock(): void {
    const now = new Date();
    currentHeaderTime.value = now.toLocaleTimeString(locale.value === 'en' ? 'en-US' : 'es-ES', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: themeStore.timeFormat === '12h',
    });
  }

  updateHeaderClock();

  watch(
    () => [themeStore.timeFormat, locale.value],
    () => {
      updateHeaderClock();
    },
  );

  // Modales de Gestión de Cuenta y Seguridad
  const isChangePasswordModalOpen = ref(false);
  const isReset2FAModalOpen = ref(false);
  const isMcpTokenModalOpen = ref(false);

  function toggleUserMenu(): void {
    isUserMenuOpen.value = !isUserMenuOpen.value;
  }

  function closeUserMenu(): void {
    isUserMenuOpen.value = false;
  }

  function openChangePasswordModal(): void {
    closeUserMenu();
    isChangePasswordModalOpen.value = true;
  }

  function openReset2FAModal(): void {
    closeUserMenu();
    isReset2FAModalOpen.value = true;
  }

  function openMcpTokenModal(): void {
    closeUserMenu();
    isMcpTokenModalOpen.value = true;
  }

  async function handleStepUpReset2FA(totpCode: string): Promise<void> {
    if (!authStore.user?.id) return;
    try {
      await http.post(`/api/v1/users/${authStore.user.id}/reset-2fa`, { admin_totp_code: totpCode });
      isReset2FAModalOpen.value = false;
      handleLogout();
    } catch {
      // Manejado por el modal
    }
  }

  function onDocumentClick(e: MouseEvent): void {
    if (userMenuRef.value && !userMenuRef.value.contains(e.target as Node)) {
      isUserMenuOpen.value = false;
    }
  }

  function onKeydown(e: KeyboardEvent): void {
    if (e.key === 'Escape' && isUserMenuOpen.value) {
      isUserMenuOpen.value = false;
    }
  }

  onMounted(() => {
    headerClockTimer = setInterval(updateHeaderClock, 1000);
    if (typeof document !== 'undefined') {
      document.addEventListener('click', onDocumentClick);
      document.addEventListener('keydown', onKeydown);
    }
  });

  onBeforeUnmount(() => {
    if (headerClockTimer) {
      clearInterval(headerClockTimer);
    }
    if (typeof document !== 'undefined') {
      document.removeEventListener('click', onDocumentClick);
      document.removeEventListener('keydown', onKeydown);
    }
  });

  interface NavItem {
    name: string;
    path: string;
    label: string;
    icon: string;
    badge?: number;
  }

  const globalNavItems = computed<NavItem[]>(() => {
    const items: NavItem[] = [
      {
        name: 'DashboardRoot',
        path: '/',
        label: t('nav.dashboard', 'Centro de Mando'),
        icon: '🎛️',
      },
      {
        name: 'RouterInventory',
        path: '/inventory',
        label: t('nav.inventory', 'Inventario'),
        icon: '🖥️',
      },
      {
        name: 'NocWallboard',
        path: '/noc-wallboard',
        label: t('nav.noc_wallboard', 'Wallboard NOC'),
        icon: '📊',
        badge: nocStore.activeAlertsCount,
      },
      {
        name: 'ApprovalsInbox',
        path: '/approvals',
        label: t('nav.maker_checker', 'Maker-Checker'),
        icon: '🛡️',
        badge: nocStore.pendingApprovalsCount,
      },
      {
        name: 'IpamManagement',
        path: '/ipam',
        label: t('nav.ipam_ftth', 'IPAM & FTTH'),
        icon: '🌐',
      },
    ];

    if (authStore.isFeatureEnabled('isp_module_enabled')) {
      items.push({
        name: 'SubscribersMap',
        path: '/subscribers/map',
        label: t('nav.subscribers_map', 'Mapa Clientes (ONUs)'),
        icon: '📍',
      });
      items.push({
        name: 'FieldTechOperations',
        path: '/field-ops',
        label: t('nav.field_ops', 'Técnico de Campo'),
        icon: '🛠️',
      });
    }

    items.push(
      {
        name: 'L2Topology',
        path: '/topology/l2',
        label: t('nav.l2_topology', 'Topología L2'),
        icon: '🗺️',
      },
      {
        name: 'FleetCveMatrix',
        path: '/inventory/cves',
        label: t('nav.cve_matrix', 'Matriz de CVEs'),
        icon: '🛡️',
      },
    );

    if (authStore.isFeatureEnabled('nightly_backups_enabled')) {
      items.push({
        name: 'RscGitDiff',
        path: '/backups',
        label: t('nav.backups_diff', 'Respaldos Diff'),
        icon: '📦',
      });
    }

    items.push(
      {
        name: 'BulkOperations',
        path: '/bulk-ops',
        label: t('nav.bulk_ops', 'Acciones Masivas'),
        icon: '⚡',
      },
      {
        name: 'ActiveSessionsKillSwitch',
        path: '/sessions',
        label: t('nav.sessions_killswitch', 'Sesiones & Kill-Switch'),
        icon: '🛑',
      },
      {
        name: 'UsersAndPermissions',
        path: '/users',
        label: t('nav.users_rbac', 'Usuarios & RBAC'),
        icon: '👥',
      },
      {
        name: 'ImmutableAuditLogs',
        path: '/audit-logs',
        label: t('nav.audit_worm', 'Auditoría WORM'),
        icon: '📜',
      },
    );

    if (authStore.currentRole === 'SUPERADMIN_GLOBAL' || authStore.currentRole === 'TENANT_ADMIN') {
      items.push({
        name: 'TenantsManagement',
        path: '/admin/tenants',
        label: t('nav.tenants', 'Empresas (Tenants)'),
        icon: '🏢',
      });
    }

    items.push({
      name: 'EnterpriseCompliance',
      path: '/enterprise/compliance',
      label: t('nav.compliance', 'Flota & Seguridad'),
      icon: '🛡️',
    });

    return items;
  });

  function handleLogout(): void {
    authStore.clearAuth();
    router.push('/login');
  }
</script>

<template>
  <div class="rg-shell">
    <!-- Enlace de Accesibilidad WCAG 2.1 AA -->
    <a href="#main-content" class="skip-link">Saltar al contenido principal</a>

    <!-- Banner Superior de Safe Mode -->
    <RgSafeModeBanner />

    <!-- Barra Superior Global -->
    <header class="rg-header" role="banner">
      <div class="header-left">
        <button
          v-if="!themeStore.isDesktopView"
          type="button"
          class="btn-hamburger"
          aria-label="Abrir menú de navegación"
          @click="themeStore.toggleMobileDrawer()"
        >
          ☰
        </button>
        <router-link to="/" class="brand" aria-label="Ir al Centro de Mando">
          <span class="brand-icon" aria-hidden="true">🌐</span>
          <span class="brand-name">RoSGrid</span>
          <span class="brand-version">v1.0</span>
        </router-link>
        <div v-if="authStore.tenantSlug" class="tenant-badge" :title="`Organización: ${authStore.tenantSlug}`">
          <strong>{{ authStore.tenantSlug }}</strong>
        </div>
      </div>

      <div class="header-right">
        <!-- Reloj Global del Sistema (HH:MM según 24h / 12h) -->
        <div class="header-clock font-mono" aria-label="Hora actual del sistema">
          <span class="clock-icon" aria-hidden="true">🕒</span>
          <span class="clock-time">{{ currentHeaderTime }}</span>
        </div>

        <!-- Botón Buscador Global Ctrl+K -->
        <button
          type="button"
          class="btn-search-trigger"
          aria-label="Buscar recursos y comandos (Ctrl+K)"
          @click="themeStore.openCommandPalette()"
        >
          <span aria-hidden="true">🔍</span>
          <span class="search-label">Buscar...</span>
          <kbd class="search-kbd" aria-hidden="true">Ctrl K</kbd>
        </button>

        <!-- Menú Desplegable Táctico de Usuario -->
        <div v-if="authStore.user" class="user-menu-container" ref="userMenuRef">
          <button
            type="button"
            class="user-profile-btn"
            id="user-profile-trigger"
            :aria-expanded="isUserMenuOpen"
            aria-haspopup="true"
            :aria-label="t('user_menu.aria_label')"
            @click="toggleUserMenu"
          >
            <span class="user-avatar-badge" aria-hidden="true">👤</span>
            <span class="user-username">{{ authStore.user.username }}</span>
            <span
              class="dropdown-chevron"
              :class="{ 'dropdown-chevron--open': isUserMenuOpen }"
              aria-hidden="true"
            >▾</span>
          </button>

          <div
            v-if="isUserMenuOpen"
            class="user-dropdown-menu"
            role="menu"
            aria-labelledby="user-profile-trigger"
          >
            <!-- Encabezado de Usuario -->
            <div class="dropdown-user-header">
              <div class="dropdown-user-name">
                {{ authStore.user.username }}
              </div>
              <div class="dropdown-user-role-tag">{{ authStore.user.role }}</div>
            </div>

            <div class="dropdown-divider"></div>

            <!-- Preferencia 1: Formato de Hora (24h vs 12h AM/PM) -->
            <div class="dropdown-section dropdown-section--time">
              <span class="dropdown-section-title">{{ t('user_menu.time_format') }}</span>
              <div class="dropdown-toggle-group" role="radiogroup" aria-label="Formato de reloj">
                <button
                  type="button"
                  class="toggle-btn"
                  :class="{ 'toggle-btn--active': themeStore.timeFormat === '24h' }"
                  @click="themeStore.setTimeFormat('24h')"
                >
                  {{ t('user_menu.time_24h') }}
                </button>
                <button
                  type="button"
                  class="toggle-btn"
                  :class="{ 'toggle-btn--active': themeStore.timeFormat === '12h' }"
                  @click="themeStore.setTimeFormat('12h')"
                >
                  {{ t('user_menu.time_12h') }}
                </button>
              </div>
            </div>

            <!-- Preferencia 2: Tema Gráfico -->
            <div class="dropdown-section dropdown-section--theme">
              <span class="dropdown-section-title">{{ t('user_menu.visual_theme') }}</span>
              <div class="dropdown-toggle-group" role="radiogroup" aria-label="Tema visual">
                <button
                  type="button"
                  class="toggle-btn"
                  :class="{ 'toggle-btn--active': themeStore.theme === 'dark' }"
                  :title="t('user_menu.theme_dark_title')"
                  @click="themeStore.setTheme('dark')"
                >
                  {{ t('user_menu.theme_dark') }}
                </button>
                <button
                  type="button"
                  class="toggle-btn"
                  :class="{ 'toggle-btn--active': themeStore.theme === 'light' }"
                  :title="t('user_menu.theme_light_title')"
                  @click="themeStore.setTheme('light')"
                >
                  {{ t('user_menu.theme_light') }}
                </button>
                <button
                  type="button"
                  class="toggle-btn"
                  :class="{ 'toggle-btn--active': themeStore.theme === 'noc-high-contrast' }"
                  :title="t('user_menu.theme_noc_title')"
                  @click="themeStore.setTheme('noc-high-contrast')"
                >
                  {{ t('user_menu.theme_noc') }}
                </button>
              </div>
            </div>

            <!-- Preferencia 3: Idioma -->
            <div class="dropdown-section dropdown-section--lang">
              <span class="dropdown-section-title">{{ t('user_menu.language') }}</span>
              <div class="dropdown-toggle-group" role="radiogroup" aria-label="Idioma del sistema">
                <button
                  type="button"
                  class="toggle-btn"
                  :class="{ 'toggle-btn--active': locale === 'es' }"
                  @click="locale !== 'es' && toggleLocale()"
                >
                  {{ t('user_menu.lang_es') }}
                </button>
                <button
                  type="button"
                  class="toggle-btn"
                  :class="{ 'toggle-btn--active': locale === 'en' }"
                  @click="locale !== 'en' && toggleLocale()"
                >
                  {{ t('user_menu.lang_en') }}
                </button>
              </div>
            </div>

            <div class="dropdown-divider"></div>

            <!-- Acciones de Cuenta y Seguridad -->
            <button
              type="button"
              class="dropdown-item btn-change-password-menu"
              role="menuitem"
              @click="openChangePasswordModal"
            >
              <span class="dropdown-item-icon" aria-hidden="true">🔑</span>
              <span>{{ t('user_menu.change_password') }}</span>
            </button>

            <button
              type="button"
              class="dropdown-item btn-reset-2fa-menu"
              role="menuitem"
              @click="openReset2FAModal"
            >
              <span class="dropdown-item-icon" aria-hidden="true">↺</span>
              <span>{{ t('user_menu.reset_2fa') }}</span>
            </button>

            <button
              type="button"
              class="dropdown-item btn-mcp-token-menu"
              role="menuitem"
              @click="openMcpTokenModal"
            >
              <span class="dropdown-item-icon" aria-hidden="true">⚡</span>
              <span>{{ t('user_menu.mcp_token') }}</span>
            </button>

            <div class="dropdown-divider"></div>

            <!-- Salir / Cerrar Sesión al fondo -->
            <button
              type="button"
              class="dropdown-item dropdown-item--logout btn-logout"
              role="menuitem"
              @click="handleLogout"
            >
              <span class="dropdown-item-icon" aria-hidden="true">🚪</span>
              <span>{{ t('user_menu.logout') }}</span>
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Cuerpo Principal con Riel de Navegación -->
    <div class="rg-shell-body">
      <!-- Riel Izquierdo Global (Desktop y Tablet) -->
      <nav
        class="rg-rail"
        :class="{ 'rg-rail--open': themeStore.isMobileDrawerOpen }"
        aria-label="Navegación principal"
      >
        <ul class="rail-list">
          <li v-for="item in globalNavItems" :key="item.path">
            <router-link
              :to="item.path"
              class="rail-link"
              :class="{
                'rail-link--active':
                  route.path === item.path || (item.path === '/' && route.path === '/dashboard'),
              }"
              @click="themeStore.closeMobileDrawer()"
            >
              <span class="rail-icon" aria-hidden="true">{{ item.icon }}</span>
              <span class="rail-label">{{ item.label }}</span>
              <span v-if="item.badge && item.badge > 0" class="rail-badge">
                {{ item.badge }}
              </span>
            </router-link>
          </li>
        </ul>
      </nav>

      <!-- Área de Contenido Principal -->
      <main id="main-content" class="rg-main" tabindex="-1">
        <slot></slot>
      </main>
    </div>

    <!-- Pie de Página Global Autenticado (Subtarea 16.5) -->
    <footer class="rg-global-footer" role="contentinfo">
      <div class="footer-content">
        <span class="footer-text">
          Elaborado por
          <a
            href="https://www.tecnoconsultores.net/"
            target="_blank"
            rel="noopener noreferrer"
            class="footer-link"
          >
            Tecno Consultores 2023 C.A.
          </a>
          • Licencia GNU GPLv3
        </span>
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
            width="14"
            height="14"
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

    <!-- Barra Inferior Fija para Móvil (< 768px) -->
    <nav
      v-if="themeStore.isMobileView"
      class="rg-mobile-bottom-bar"
      aria-label="Navegación móvil rápida de campo"
    >
      <router-link
        :to="isRouterContext ? `/routers/${currentRouterId}/webfig/live` : '/noc-wallboard'"
        class="mobile-touch-item"
        aria-label="Vista de monitoreo en vivo"
      >
        <span class="touch-icon" aria-hidden="true">📊</span>
        <span class="touch-label">Vivo</span>
      </router-link>

      <router-link
        :to="isRouterContext ? `/routers/${currentRouterId}/webfig/interfaces` : '/inventory'"
        class="mobile-touch-item"
        aria-label="Interfaces y diagnóstico SFP"
      >
        <span class="touch-icon" aria-hidden="true">🔌</span>
        <span class="touch-label">SFP/Red</span>
      </router-link>

      <router-link
        :to="isRouterContext ? `/routers/${currentRouterId}/webfig/ppp` : '/approvals'"
        class="mobile-touch-item"
        aria-label="Sesiones PPPoE y Colas"
      >
        <span class="touch-icon" aria-hidden="true">⚡</span>
        <span class="touch-label">PPP/Colas</span>
      </router-link>

      <router-link
        :to="isRouterContext ? `/routers/${currentRouterId}/webfig/tools` : '/backups'"
        class="mobile-touch-item"
        aria-label="Herramientas Ping y Diagnóstico"
      >
        <span class="touch-icon" aria-hidden="true">🛠️</span>
        <span class="touch-label">Tools</span>
      </router-link>

      <button
        type="button"
        class="mobile-touch-item btn-mobile-menu"
        aria-label="Abrir menú completo"
        @click="themeStore.toggleMobileDrawer()"
      >
        <span class="touch-icon" aria-hidden="true">☰</span>
        <span class="touch-label">Menú</span>
      </button>
    </nav>

    <!-- Modal Command Palette Global (Ctrl+K) -->
    <RgCommandPalette />

    <!-- Modales de Cuenta Invocados desde el Menú de Usuario -->
    <ChangePasswordModal
      :is-open="isChangePasswordModalOpen"
      :target-user="{ id: authStore.user?.id || '', username: authStore.user?.username || '' }"
      @close="isChangePasswordModalOpen = false"
    />

    <RgStepUp2FAModal
      :is-open="isReset2FAModalOpen"
      title="Step-Up 2FA: Confirmar Reseteo de 2FA"
      @close="isReset2FAModalOpen = false"
      @submit-totp="handleStepUpReset2FA"
    />

    <RgMcpTokenModal
      :is-open="isMcpTokenModalOpen"
      :user="authStore.user as any"
      @close="isMcpTokenModalOpen = false"
    />
  </div>
</template>

<style scoped>
  .rg-shell {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: var(--rg-bg-canvas);
  }

  .rg-header {
    height: 52px;
    background: var(--rg-bg-surface);
    border-bottom: 1px solid var(--rg-border-panel);
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 16px;
    z-index: 800;
  }

  .header-left,
  .header-right {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .header-clock {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--rg-bg-canvas, rgba(15, 23, 42, 0.6));
    border: 1px solid var(--rg-border-panel, rgba(56, 189, 248, 0.25));
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 0.85rem;
    color: var(--rg-accent-cyan, #22d3ee);
    font-weight: 700;
    letter-spacing: 0.05em;
  }

  .header-clock .clock-icon {
    font-size: 0.85rem;
  }

  .header-clock .clock-time {
    line-height: 1;
  }

  .btn-hamburger {
    background: transparent;
    border: none;
    color: var(--rg-text-primary);
    font-size: 20px;
    cursor: pointer;
    padding: 4px 8px;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 6px;
    text-decoration: none;
    cursor: pointer;
    transition: opacity 0.15s ease;
  }

  .brand:hover {
    opacity: 0.85;
  }

  .brand-icon {
    font-size: 20px;
  }

  .brand-name {
    font-weight: 700;
    font-size: 16px;
    color: var(--rg-text-primary);
    letter-spacing: -0.5px;
  }

  .brand-version {
    font-size: 10px;
    color: var(--rg-accent-cyan);
    font-family: var(--rg-font-mono);
    background: var(--rg-status-info-bg);
    padding: 1px 4px;
    border-radius: 2px;
  }

  .tenant-badge {
    font-size: 12px;
    color: var(--rg-text-secondary);
    background: var(--rg-bg-elevated);
    padding: 4px 8px;
    border-radius: 4px;
    border: 1px solid var(--rg-border-grid);
  }

  .btn-search-trigger {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--rg-bg-canvas);
    border: 1px solid var(--rg-border-panel);
    color: var(--rg-text-muted);
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
  }

  .btn-search-trigger:hover {
    border-color: var(--rg-accent-cyan);
    color: var(--rg-accent-cyan);
  }

  .search-kbd {
    font-family: var(--rg-font-mono);
    font-size: 10px;
    background: var(--rg-bg-elevated);
    padding: 1px 4px;
    border-radius: 3px;
    border: 1px solid var(--rg-border-panel);
  }

  /* Menú Desplegable de Usuario Táctico */
  .user-menu-container {
    position: relative;
    display: inline-block;
  }

  .user-profile-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-panel, #1f293d);
    color: var(--rg-text-primary, #f9fafb);
    padding: 6px 12px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 600;
    transition: all 0.2s ease;
  }

  .user-profile-btn:hover,
  .user-profile-btn[aria-expanded="true"] {
    border-color: var(--rg-accent-cyan, #00f3ff);
    box-shadow: 0 0 10px rgba(0, 243, 255, 0.15);
  }

  .user-avatar-badge {
    font-size: 1rem;
  }

  .user-username {
    font-family: var(--rg-font-mono, monospace);
    color: var(--rg-accent-cyan, #00f3ff);
  }

  .dropdown-chevron {
    font-size: 0.75rem;
    color: var(--rg-text-muted, #9ca3af);
    transition: transform 0.2s ease;
  }

  .dropdown-chevron--open {
    transform: rotate(180deg);
  }

  .user-dropdown-menu {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    background-color: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border, #1f293d);
    border-radius: 10px;
    width: 280px;
    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.65);
    z-index: 2000;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    animation: fadeInMenu 0.15s ease-out;
  }

  @keyframes fadeInMenu {
    from {
      opacity: 0;
      transform: translateY(-6px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .dropdown-user-header {
    padding: 4px 6px;
  }

  .dropdown-user-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--rg-text-primary, #fff);
  }

  .dropdown-user-role-tag {
    font-size: 0.75rem;
    font-family: var(--rg-font-mono, monospace);
    color: var(--rg-accent-cyan, #00f3ff);
    margin-top: 2px;
  }

  .dropdown-divider {
    height: 1px;
    background-color: var(--rg-border-grid, #1f293d);
    margin: 4px 0;
  }

  .dropdown-section {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 2px 4px;
  }

  .dropdown-section-title {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--rg-text-muted, #94a3b8);
  }

  .dropdown-toggle-group {
    display: flex;
    gap: 4px;
    background: rgba(0, 0, 0, 0.4);
    padding: 3px;
    border-radius: 6px;
    border: 1px solid var(--rg-border, #1f293d);
  }

  .toggle-btn {
    flex: 1;
    background: transparent;
    border: none;
    color: var(--rg-text-secondary, #cbd5e1);
    font-size: 0.78rem;
    font-weight: 600;
    padding: 5px 8px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: center;
  }

  .toggle-btn:hover {
    color: #fff;
    background: rgba(255, 255, 255, 0.08);
  }

  .toggle-btn--active {
    background: var(--rg-accent-cyan, #00f3ff) !important;
    color: #000 !important;
    font-weight: 700;
  }

  .dropdown-item {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 8px 10px;
    border-radius: 6px;
    border: none;
    background: transparent;
    color: var(--rg-text-primary, #f3f4f6);
    font-size: 0.88rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.15s ease, color 0.15s ease;
    text-align: left;
  }

  .dropdown-item:hover {
    background: rgba(0, 243, 255, 0.08);
    color: var(--rg-accent-cyan, #00f3ff);
  }

  .dropdown-item-icon {
    font-size: 1rem;
    width: 20px;
    text-align: center;
  }

  .dropdown-item--logout {
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
    background: rgba(239, 68, 68, 0.06);
    margin-top: 2px;
  }

  .dropdown-item--logout:hover {
    background: rgba(239, 68, 68, 0.18);
    color: #fff;
  }

  .rg-shell-body {
    flex: 1;
    display: flex;
    position: relative;
  }

  .rg-rail {
    width: 220px;
    background: var(--rg-bg-surface);
    border-right: 1px solid var(--rg-border-panel);
    padding: 12px 8px;
  }

  .rail-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .rail-link {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    color: var(--rg-text-secondary);
    text-decoration: none;
    border-radius: 6px;
    font-size: 13px;
    transition: all 0.15s ease;
  }

  .rail-link:hover {
    background: var(--rg-bg-elevated);
    color: var(--rg-text-primary);
  }

  .rail-link--active {
    background: var(--rg-bg-elevated);
    color: var(--rg-accent-cyan);
    font-weight: 600;
    border-left: 3px solid var(--rg-accent-cyan);
  }

  .rail-badge {
    margin-left: auto;
    font-size: 10px;
    font-family: var(--rg-font-mono);
    background: var(--rg-status-warning);
    color: #000000;
    padding: 1px 6px;
    border-radius: 10px;
    font-weight: 700;
  }

  .rg-main {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
    outline: none;
  }

  /* Barra Móvil Inferior Fija */
  .rg-mobile-bottom-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 56px;
    background: var(--rg-bg-surface);
    border-top: 1px solid var(--rg-border-panel);
    display: flex;
    justify-content: space-around;
    align-items: center;
    z-index: 900;
  }

  .mobile-touch-item {
    flex: 1;
    height: 44px;
    min-width: 44px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: var(--rg-text-muted);
    text-decoration: none;
    font-size: 10px;
    background: transparent;
    border: none;
    cursor: pointer;
  }

  .mobile-touch-item.router-link-active,
  .mobile-touch-item:hover {
    color: var(--rg-accent-cyan);
  }

  .touch-icon {
    font-size: 18px;
  }

  /* Drawer móvil */
  @media (max-width: 1023px) {
    .rg-rail {
      position: fixed;
      top: 52px;
      bottom: 56px;
      left: -260px;
      width: 240px;
      z-index: 850;
      transition: left 0.25s ease;
      box-shadow: 4px 0 16px rgba(0, 0, 0, 0.5);
    }

    .rg-rail--open {
      left: 0;
    }
  }

  @media (max-width: 767px) {
    .rg-main {
      padding-bottom: 72px; /* Espacio para barra inferior */
    }

    .search-label,
    .search-kbd {
      display: none;
    }

    .rg-global-footer {
      margin-bottom: 56px; /* Para no solaparse con mobile bottom bar */
    }
  }

  /* Pie de Página Global Autenticado (Subtarea 16.5) */
  .rg-global-footer {
    height: 32px;
    background: var(--rg-bg-surface);
    border-top: 1px solid var(--rg-border-panel);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 16px;
    font-size: 11px;
    color: var(--rg-text-muted);
    z-index: 700;
  }

  .footer-content {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .footer-link,
  .footer-github-link {
    color: var(--rg-accent-cyan);
    text-decoration: none;
    transition: color 0.15s ease;
  }

  .footer-link:hover,
  .footer-github-link:hover {
    text-decoration: underline;
  }

  .github-icon {
    display: inline-block;
    vertical-align: middle;
  }
</style>
