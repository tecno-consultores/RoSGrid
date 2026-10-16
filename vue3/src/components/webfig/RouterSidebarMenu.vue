<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { ref, onMounted } from 'vue';
  import { useRoute, useRouter } from 'vue-router';
  import { http } from '@/api/httpClient';
  import type { Layer2CatalogItem } from '@/types';

  const props = defineProps<{
    routerId: string;
    isOpenMobile: boolean;
  }>();

  const emit = defineEmits<{
    (e: 'close-mobile'): void;
  }>();

  const route = useRoute();
  const router = useRouter();

  const layer2Catalog = ref<Layer2CatalogItem[]>([
    { ros_path: 'mpls', title: 'MPLS & VPLS', category: 'Transport', is_singleton: false },
    { ros_path: 'zerotier', title: 'ZeroTier SDN', category: 'VPN', is_singleton: false },
    { ros_path: 'capsman', title: 'CAPsMAN WiFi', category: 'Wireless', is_singleton: false },
    {
      ros_path: 'container',
      title: 'Docker Containers',
      category: 'Virtualization',
      is_singleton: false,
    },
    { ros_path: 'snmp', title: 'SNMP Community', category: 'Management', is_singleton: true },
  ]);

  async function loadLayer2Catalog() {
    try {
      const res = await http.get<{ items: Layer2CatalogItem[] }>(
        `/api/v1/routers/${props.routerId}/webfig/layer2/catalog`,
      );
      if (res.data?.items && res.data.items.length > 0) {
        layer2Catalog.value = res.data.items;
      }
    } catch {
      // Usa el catálogo estático predeterminado
    }
  }

  function navigateTo(path: string) {
    router.push(`/routers/${props.routerId}/webfig/${path}`);
    emit('close-mobile');
  }

  function navigateToLayer2(rosPath: string) {
    router.push(`/routers/${props.routerId}/webfig/layer2/${rosPath}`);
    emit('close-mobile');
  }

  onMounted(() => {
    loadLayer2Catalog();
  });
</script>

<template>
  <div>
    <!-- Backdrop en móvil -->
    <div
      v-if="isOpenMobile"
      class="sidebar-backdrop"
      aria-hidden="true"
      @click="emit('close-mobile')"
    ></div>

    <aside
      class="router-sidebar"
      :class="{ 'router-sidebar--open-mobile': isOpenMobile }"
      aria-label="Menú de navegación de módulos RouterOS"
    >
      <div class="sidebar-header">
        <span class="sidebar-title">Módulos WebFig v7</span>
        <button
          type="button"
          class="btn-close-sidebar"
          aria-label="Cerrar menú lateral"
          @click="emit('close-mobile')"
        >
          ✕
        </button>
      </div>

      <nav class="sidebar-nav">
        <!-- Sección 1: Principal -->
        <div class="nav-group">
          <span class="group-label">Principal</span>
          <button
            type="button"
            class="nav-item"
            :class="{ 'nav-item--active': route.path.endsWith('/live') }"
            @click="navigateTo('live')"
          >
            <span class="item-icon">📊</span>
            <span class="item-text">Dashboard en Vivo</span>
          </button>
        </div>

        <!-- Sección 2: Capa 1 Nativos -->
        <div class="nav-group">
          <span class="group-label">Capa 1 — Red y Seguridad</span>
          <button
            type="button"
            class="nav-item"
            :class="{ 'nav-item--active': route.path.includes('/interfaces') }"
            @click="navigateTo('interfaces')"
          >
            <span class="item-icon">🔌</span>
            <span class="item-text">Interfaces & SFP DDM</span>
          </button>

          <button
            type="button"
            class="nav-item"
            :class="{ 'nav-item--active': route.path.includes('/firewall') }"
            @click="navigateTo('firewall')"
          >
            <span class="item-icon">🛡️</span>
            <span class="item-text">Firewall (Filter, NAT, RAW)</span>
          </button>

          <button
            type="button"
            class="nav-item"
            :class="{ 'nav-item--active': route.path.includes('/routing') }"
            @click="navigateTo('routing')"
          >
            <span class="item-icon">🌐</span>
            <span class="item-text">Routing v7 (BGP / OSPF)</span>
          </button>

          <button
            type="button"
            class="nav-item"
            :class="{ 'nav-item--active': route.path.includes('/ppp') }"
            @click="navigateTo('ppp')"
          >
            <span class="item-icon">⚡</span>
            <span class="item-text">PPPoE & Colas de Ancho de Banda</span>
          </button>

          <button
            type="button"
            class="nav-item"
            :class="{ 'nav-item--active': route.path.includes('/tools') }"
            @click="navigateTo('tools')"
          >
            <span class="item-icon">🛠️</span>
            <span class="item-text">Tools (Ping, Torch, Logs)</span>
          </button>

          <button
            type="button"
            class="nav-item"
            :class="{ 'nav-item--active': route.path.includes('/backups') }"
            @click="navigateTo('backups')"
          >
            <span class="item-icon">💾</span>
            <span class="item-text">Respaldos & Git Diff</span>
          </button>
        </div>

        <!-- Sección 3: Capa 2 Dinámica -->
        <div class="nav-group">
          <span class="group-label">Capa 2 — Motor Universal</span>
          <button
            v-for="item in layer2Catalog"
            :key="item.ros_path"
            type="button"
            class="nav-item"
            :class="{ 'nav-item--active': route.path.includes(`/layer2/${item.ros_path}`) }"
            @click="navigateToLayer2(item.ros_path)"
          >
            <span class="item-icon">⚙️</span>
            <span class="item-text">{{ item.title }}</span>
          </button>
        </div>
      </nav>
    </aside>
  </div>
</template>

<style scoped>
  .router-sidebar {
    width: 260px;
    background: var(--rg-bg-surface);
    border: 1px solid var(--rg-border-grid);
    border-radius: 8px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: calc(100vh - 120px);
    overflow-y: auto;
  }

  .sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--rg-border-grid);
  }

  .sidebar-title {
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--rg-text-primary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .btn-close-sidebar {
    display: none;
    background: transparent;
    border: none;
    color: var(--rg-text-muted);
    font-size: 1rem;
    cursor: pointer;
  }

  .sidebar-nav {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .nav-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .group-label {
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--rg-text-muted);
    text-transform: uppercase;
    margin-bottom: 2px;
    padding-left: 6px;
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 7px 10px;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    color: var(--rg-text-secondary);
    font-size: 0.82rem;
    text-align: left;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .nav-item:hover {
    background: var(--rg-bg-elevated);
    color: var(--rg-text-primary);
  }

  .nav-item--active {
    background: rgba(6, 182, 212, 0.15);
    border-color: var(--rg-accent-cyan);
    color: var(--rg-accent-cyan);
    font-weight: 600;
  }

  .item-icon {
    font-size: 0.95rem;
  }

  .item-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  @media (max-width: 1024px) {
    .router-sidebar {
      position: fixed;
      top: 0;
      bottom: 0;
      left: -280px;
      width: 270px;
      height: 100vh;
      max-height: 100vh;
      border-radius: 0;
      z-index: 1000;
      transition: left 0.25s ease;
      box-shadow: 2px 0 16px rgba(0, 0, 0, 0.5);
    }

    .router-sidebar--open-mobile {
      left: 0;
    }

    .btn-close-sidebar {
      display: block;
    }

    .sidebar-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.6);
      backdrop-filter: blur(2px);
      z-index: 999;
    }
  }
</style>
