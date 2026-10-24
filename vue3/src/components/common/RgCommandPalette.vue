<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
  import { useRouter } from 'vue-router';
  import { useAuthStore } from '@/stores/useAuthStore';
  import { useInventoryStore } from '@/stores/useInventoryStore';
  import { useThemeAndLayoutStore } from '@/stores/useThemeAndLayoutStore';

  const router = useRouter();
  const authStore = useAuthStore();
  const themeStore = useThemeAndLayoutStore();
  const inventoryStore = useInventoryStore();

  const query = ref<string>('');
  const selectedIndex = ref<number>(0);
  const searchInputRef = ref<HTMLInputElement | null>(null);

  interface CommandItem {
    id: string;
    category: 'ROUTER' | 'NAVIGATION' | 'ACTION';
    title: string;
    subtitle: string;
    icon: string;
    requiredFeature?: string;
    action: () => void;
  }

  const staticCommands: CommandItem[] = [
    {
      id: 'nav-inventory',
      category: 'NAVIGATION',
      title: 'Inventario de Routers',
      subtitle: 'Ver lista general y mapa OpenStreetMap',
      icon: '🖥️',
      action: () => router.push('/inventory'),
    },
    {
      id: 'nav-wallboard',
      category: 'NAVIGATION',
      title: 'Wallboard NOC 24/7',
      subtitle: 'Pantalla de monitoreo en tiempo real',
      icon: '📊',
      action: () => router.push('/noc-wallboard'),
    },
    {
      id: 'nav-approvals',
      category: 'NAVIGATION',
      title: 'Bandeja Maker-Checker',
      subtitle: 'Aprobar o rechazar cambios críticos',
      icon: '🛡️',
      action: () => router.push('/approvals'),
    },
    {
      id: 'nav-backups',
      category: 'NAVIGATION',
      title: 'Respaldos y Diff Git',
      subtitle: 'Historial y comparador de configuraciones .rsc',
      icon: '📦',
      action: () => router.push('/backups'),
    },
    {
      id: 'nav-ipam',
      category: 'NAVIGATION',
      title: 'IPAM Dual-Stack & FTTH',
      subtitle: 'Gestor universal de prefijos, pools y abonados',
      icon: '🌐',
      action: () => router.push('/ipam'),
    },
    {
      id: 'nav-subscribers-map',
      category: 'NAVIGATION',
      title: 'Mapa de Red & Clientes',
      subtitle: 'Geolocalización de cajas NAP, terminales FTTH o clientes DHCP',
      icon: '📍',
      action: () => router.push('/subscribers/map'),
    },
    {
      id: 'nav-field-ops',
      category: 'NAVIGATION',
      title: 'Técnico de Campo & Toolkit',
      subtitle: 'Aprovisionamiento NAP, altas de clientes y diagnósticos',
      icon: '🛠️',
      requiredFeature: 'isp_module_enabled',
      action: () => router.push('/field-ops'),
    },
    {
      id: 'action-theme-toggle',
      category: 'ACTION',
      title: 'Alternar Tema Visual',
      subtitle: 'Cambiar entre Dark, Light y NOC Alto Contraste',
      icon: '🎨',
      action: () => {
        const next =
          themeStore.theme === 'dark'
            ? 'light'
            : themeStore.theme === 'light'
              ? 'noc-high-contrast'
              : 'dark';
        themeStore.setTheme(next);
      },
    },
  ];

  const filteredCommands = computed<CommandItem[]>(() => {
    const q = query.value.trim().toLowerCase();
    const results: CommandItem[] = [];

    // Routers del Inventario
    for (const r of inventoryStore.routers) {
      const matchName = r.display_name.toLowerCase().includes(q);
      const matchIp = r.ip_address.toLowerCase().includes(q);
      const matchSerial = r.serial_number ? r.serial_number.toLowerCase().includes(q) : false;

      if (!q || matchName || matchIp || matchSerial) {
        results.push({
          id: `router-${r.id}`,
          category: 'ROUTER',
          title: r.display_name,
          subtitle: `${r.ip_address} • ROS v${r.ros_version} • ${r.admin_state}`,
          icon: '📡',
          action: () => router.push(`/routers/${r.id}/webfig/live`),
        });
      }
    }

    // Comandos de navegación
    for (const cmd of staticCommands) {
      if (cmd.requiredFeature && !authStore.isFeatureEnabled(cmd.requiredFeature)) {
        continue;
      }
      if (!q || cmd.title.toLowerCase().includes(q) || cmd.subtitle.toLowerCase().includes(q)) {
        results.push(cmd);
      }
    }

    return results.slice(0, 15);
  });

  watch(
    () => themeStore.isCommandPaletteOpen,
    (isOpen) => {
      if (isOpen) {
        query.value = '';
        selectedIndex.value = 0;
        nextTick(() => {
          searchInputRef.value?.focus();
        });
      }
    },
  );

  function handleKeyDown(e: KeyboardEvent): void {
    // Atajo global Ctrl+K o Cmd+K
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      themeStore.toggleCommandPalette();
      return;
    }

    if (!themeStore.isCommandPaletteOpen) return;

    if (e.key === 'Escape') {
      themeStore.closeCommandPalette();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      selectedIndex.value = (selectedIndex.value + 1) % Math.max(1, filteredCommands.value.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selectedIndex.value =
        (selectedIndex.value - 1 + filteredCommands.value.length) %
        Math.max(1, filteredCommands.value.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const item = filteredCommands.value[selectedIndex.value];
      if (item) {
        executeCommand(item);
      }
    }
  }

  function executeCommand(item: CommandItem): void {
    themeStore.closeCommandPalette();
    item.action();
  }

  onMounted(() => {
    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', handleKeyDown);
    }
  });

  onUnmounted(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('keydown', handleKeyDown);
    }
  });
</script>

<template>
  <div
    v-if="themeStore.isCommandPaletteOpen"
    class="rg-palette-backdrop"
    @click.self="themeStore.closeCommandPalette()"
  >
    <div class="rg-palette" role="dialog" aria-modal="true" aria-labelledby="cmd-palette-title">
      <header class="rg-palette__header">
        <label for="cmd-palette-input" class="sr-only">Buscar comandos o routers</label>
        <span class="rg-palette__icon" aria-hidden="true">🔍</span>
        <input
          id="cmd-palette-input"
          ref="searchInputRef"
          v-model="query"
          type="search"
          autocomplete="off"
          placeholder="Escribe un router, IP o comando (ej. RB4011, firewall, noc)..."
          aria-autocomplete="list"
          aria-controls="cmd-palette-results"
        />
        <kbd class="rg-kbd" aria-hidden="true">ESC</kbd>
      </header>

      <ul
        id="cmd-palette-results"
        class="rg-palette__list"
        role="listbox"
        aria-label="Resultados de búsqueda"
      >
        <li
          v-for="(item, idx) in filteredCommands"
          :key="item.id"
          class="rg-palette__item"
          :class="{ 'rg-palette__item--selected': idx === selectedIndex }"
          role="option"
          :aria-selected="idx === selectedIndex"
          @click="executeCommand(item)"
          @mouseenter="selectedIndex = idx"
        >
          <span class="item-icon" aria-hidden="true">{{ item.icon }}</span>
          <div class="item-content">
            <span class="item-title">{{ item.title }}</span>
            <span class="item-subtitle">{{ item.subtitle }}</span>
          </div>
          <span class="item-badge">{{ item.category }}</span>
        </li>

        <li v-if="filteredCommands.length === 0" class="rg-palette__empty">
          No se encontraron resultados para "{{ query }}"
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
  .rg-palette-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(11, 15, 25, 0.75);
    backdrop-filter: blur(4px);
    z-index: 10000;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding-top: 15vh;
  }

  .rg-palette {
    width: 90%;
    max-width: 640px;
    background: var(--rg-bg-surface);
    border: 1px solid var(--rg-border-panel);
    border-radius: 8px;
    box-shadow:
      0 20px 40px rgba(0, 0, 0, 0.5),
      var(--rg-cyan-glow);
    overflow: hidden;
  }

  .rg-palette__header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 14px 16px;
    border-bottom: 1px solid var(--rg-border-grid);
  }

  .rg-palette__header input {
    flex: 1;
    background: transparent;
    border: none;
    color: var(--rg-text-primary);
    font-size: 15px;
    outline: none;
  }

  .rg-kbd {
    font-family: var(--rg-font-mono);
    font-size: 11px;
    color: var(--rg-text-muted);
    background: var(--rg-bg-elevated);
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid var(--rg-border-panel);
  }

  .rg-palette__list {
    max-height: 380px;
    overflow-y: auto;
    list-style: none;
    padding: 8px 0;
  }

  .rg-palette__item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 16px;
    cursor: pointer;
    transition: background-color 0.1s ease;
  }

  .rg-palette__item--selected {
    background: var(--rg-bg-elevated);
    border-left: 3px solid var(--rg-accent-cyan);
  }

  .item-icon {
    font-size: 18px;
  }

  .item-content {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .item-title {
    color: var(--rg-text-primary);
    font-weight: 500;
  }

  .item-subtitle {
    color: var(--rg-text-muted);
    font-size: 12px;
  }

  .item-badge {
    font-size: 10px;
    font-family: var(--rg-font-mono);
    color: var(--rg-accent-cyan);
    background: var(--rg-status-info-bg);
    padding: 2px 6px;
    border-radius: 4px;
  }

  .rg-palette__empty {
    padding: 24px;
    text-align: center;
    color: var(--rg-text-muted);
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
  }
</style>
