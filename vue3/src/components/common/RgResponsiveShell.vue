<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { computed } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useNocEventsStore } from '@/stores/useNocEventsStore';
  import { useThemeAndLayoutStore } from '@/stores/useThemeAndLayoutStore';
  import { useI18n } from '@/composables/useI18n';
  import RgCommandPalette from './RgCommandPalette.vue';
  import RgSafeModeBanner from './RgSafeModeBanner.vue';

  const route = useRoute();
  const router = useRouter();
  const authStore = useAuthStore();
  const themeStore = useThemeAndLayoutStore();
  const nocStore = useNocEventsStore();
  const { t, locale, toggleLocale } = useI18n();

  const isRouterContext = computed(() => route.path.includes('/routers/'));
  const currentRouterId = computed(() => String(route.params.routerId || ''));

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
        name: 'RscGitDiff',
        path: '/backups',
        label: t('nav.backups_diff', 'Respaldos Diff'),
        icon: '📦',
      },
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

    if (authStore.currentRole === 'SUPERADMIN_GLOBAL') {
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
        <div class="brand">
          <span class="brand-icon" aria-hidden="true">🌐</span>
          <span class="brand-name">RoSGrid</span>
          <span class="brand-version">v1.0</span>
        </div>
        <div v-if="authStore.tenantSlug" class="tenant-badge">
          <span
            >Tenant: <strong>{{ authStore.tenantSlug }}</strong></span
          >
        </div>
      </div>

      <div class="header-right">
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

        <!-- Conmutador de Temas -->
        <button
          type="button"
          class="btn-icon"
          :aria-label="`Tema actual: ${themeStore.theme}. Cambiar tema visual`"
          @click="
            themeStore.setTheme(
              themeStore.theme === 'dark'
                ? 'light'
                : themeStore.theme === 'light'
                  ? 'noc-high-contrast'
                  : 'dark',
            )
          "
        >
          <span v-if="themeStore.theme === 'dark'" aria-hidden="true">🌙</span>
          <span v-else-if="themeStore.theme === 'light'" aria-hidden="true">☀️</span>
          <span v-else aria-hidden="true">⚡</span>
        </button>

        <!-- Conmutador Táctico de Idioma i18n (ES / EN) -->
        <button
          type="button"
          class="btn-icon btn-lang-toggle"
          id="btn-global-lang-toggle"
          :aria-label="`Idioma actual: ${locale.toUpperCase()}. Presione para alternar idioma entre Español e Inglés`"
          :title="locale === 'es' ? 'Switch to English' : 'Cambiar a Español'"
          @click="toggleLocale"
        >
          <span class="lang-text">{{ locale.toUpperCase() }}</span>
        </button>

        <!-- Info Usuario & Salir -->
        <div v-if="authStore.user" class="user-info">
          <span class="user-role-badge">{{ authStore.user.role }}</span>
          <button type="button" class="btn-logout" aria-label="Cerrar sesión" @click="handleLogout">
            Salir
          </button>
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

  .btn-icon {
    background: transparent;
    border: 1px solid var(--rg-border-panel);
    color: var(--rg-text-primary);
    width: 32px;
    height: 32px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }

  .btn-lang-toggle {
    font-family: var(--rg-font-mono);
    font-size: 11px;
    font-weight: 700;
    color: var(--rg-accent-cyan);
    letter-spacing: 0.5px;
    transition: all 0.2s ease;
  }

  .btn-lang-toggle:hover {
    border-color: var(--rg-accent-cyan);
    background: rgba(0, 243, 255, 0.12);
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .user-role-badge {
    font-size: 11px;
    font-family: var(--rg-font-mono);
    background: var(--rg-bg-elevated);
    color: var(--rg-accent-cyan);
    padding: 3px 6px;
    border-radius: 4px;
    border: 1px solid var(--rg-border-grid);
  }

  .btn-logout {
    background: transparent;
    border: 1px solid var(--rg-status-critical);
    color: var(--rg-status-critical);
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
  }

  .btn-logout:hover {
    background: var(--rg-status-critical-bg);
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
