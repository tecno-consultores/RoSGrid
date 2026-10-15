<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->
<template>
  <div class="active-sessions-view" role="main" aria-label="Sesiones Activas y Kill-Switch">
    <header class="view-header">
      <h1 class="view-title">Sesiones Activas y Kill-Switch Global</h1>
      <p class="view-subtitle">
        Supervisión en tiempo real de tokens JWT/KeyDB activos y revocación inmediata de
        credenciales.
      </p>
    </header>
    <div class="view-content">
      <p class="placeholder-text">Módulo de control de sesiones activas (Hito 13).</p>
    </div>
  </div>
</template>

<script setup lang="ts">
  // ActiveSessionsKillSwitchView placeholder
</script>

<style scoped>
  .active-sessions-view {
    display: flex;
    flex-direction: column;
    gap: var(--space-4, 16px);
  }
  .view-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--color-text-primary);
    margin: 0;
  }
  .view-subtitle {
    font-size: 0.875rem;
    color: var(--color-text-muted);
    margin-top: var(--space-1, 4px);
  }
  .view-content {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md, 6px);
    padding: var(--space-6, 24px);
  }
  .placeholder-text {
    color: var(--color-text-secondary);
    font-family: var(--font-mono, monospace);
    font-size: 0.8125rem;
  }
</style>
