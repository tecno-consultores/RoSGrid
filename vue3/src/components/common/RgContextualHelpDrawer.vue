<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 RoSGrid Contributors -->

<script setup lang="ts">
  import { onMounted, onBeforeUnmount } from 'vue';
  import { useContextualHelp } from '@/composables/useContextualHelp';

  const {
    isHelpOpen,
    manualHelpKey,
    routeHelpKey,
    activeHelpKey,
    currentHelpEntry,
    allHelpTopics,
    isMarkdownCopied,
    closeHelp,
    selectHelpTopic,
    resetToRouteTopic,
    copyCurrentHelpAsMarkdown,
    handleHelpKeydown,
  } = useContextualHelp();

  function onTopicSelectChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    selectHelpTopic(target.value);
  }

  onMounted(() => {
    if (typeof window !== 'undefined') {
      window.addEventListener('keydown', handleHelpKeydown);
    }
  });

  onBeforeUnmount(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('keydown', handleHelpKeydown);
    }
  });
</script>

<template>
  <div
    v-if="isHelpOpen"
    class="rg-help-backdrop"
    data-testid="help-drawer-backdrop"
    @click.self="closeHelp()"
  >
    <aside
      id="rg-contextual-help-drawer"
      class="rg-help-drawer"
      role="dialog"
      aria-modal="true"
      aria-labelledby="help-drawer-title"
    >
      <!-- Cabecera del Cajón de Ayuda Contextual -->
      <header class="help-drawer-header">
        <div class="help-header-title-row">
          <div class="help-badge-group">
            <span class="help-context-badge">❓ Ayuda Contextual In-App</span>
            <span class="help-shortcut-hint" aria-hidden="true">F1 / Alt+H</span>
          </div>
          <button
            id="btn-close-contextual-help"
            type="button"
            class="btn-close-help"
            aria-label="Cerrar cajón de ayuda contextual"
            @click="closeHelp()"
          >
            ✕
          </button>
        </div>

        <h2 id="help-drawer-title" class="help-drawer-title">
          {{ currentHelpEntry.title }}
        </h2>

        <!-- Selector de Tópico y Acción Copiar como Markdown LLM-Ready -->
        <div class="help-toolbar">
          <div class="help-topic-selector-wrap">
            <label for="help-topic-selector" class="sr-only">
              Seleccionar pantalla o módulo de ayuda
            </label>
            <select
              id="help-topic-selector"
              class="help-topic-select"
              :value="activeHelpKey"
              aria-label="Seleccionar pantalla o módulo de ayuda"
              @change="onTopicSelectChange"
            >
              <option
                v-for="topic in allHelpTopics"
                :key="topic.routeKey"
                :value="topic.routeKey"
              >
                {{ topic.title }}
              </option>
            </select>
            <button
              v-if="manualHelpKey && manualHelpKey !== routeHelpKey"
              id="btn-reset-help-topic"
              type="button"
              class="btn-reset-topic"
              title="Volver a la ayuda de la pantalla actual"
              @click="resetToRouteTopic()"
            >
              ↺ Pantalla actual
            </button>
          </div>

          <button
            id="btn-copy-help-markdown"
            type="button"
            class="btn-copy-markdown"
            :class="{ 'btn-copy-markdown--copied': isMarkdownCopied }"
            aria-label="Copiar guía de ayuda actual como Markdown"
            @click="copyCurrentHelpAsMarkdown()"
          >
            {{
              isMarkdownCopied
                ? '✔ Guía Copiada (Markdown)'
                : '📋 Copiar Guía como Markdown'
            }}
          </button>
        </div>
      </header>

      <!-- Cuerpo de la Guía Contextual -->
      <div class="help-drawer-body">
        <!-- Resumen de Pantalla -->
        <section class="help-section help-section--summary" aria-label="Propósito de la pantalla">
          <p class="help-summary-text">{{ currentHelpEntry.summary }}</p>
        </section>

        <!-- Acciones Clave Paso a Paso -->
        <section class="help-section" aria-labelledby="help-sec-actions">
          <h3 id="help-sec-actions" class="help-section-title">
            ⚡ ¿Qué puedes hacer en esta pantalla?
          </h3>
          <ol class="help-ordered-list">
            <li
              v-for="(action, idx) in currentHelpEntry.keyActions"
              :key="idx"
              class="help-list-item"
            >
              <strong>{{ action.title }}:</strong> {{ action.description }}
            </li>
          </ol>
        </section>

        <!-- Gobernanza, Seguridad y Safe Mode -->
        <section class="help-section help-section--governance" aria-labelledby="help-sec-gov">
          <h3 id="help-sec-gov" class="help-section-title">
            🛡️ Gobernanza, Seguridad y Safe Mode
          </h3>
          <ul class="help-bullet-list">
            <li
              v-for="(item, idx) in currentHelpEntry.safetyAndGovernance"
              :key="idx"
              class="help-list-item"
            >
              {{ item }}
            </li>
          </ul>
        </section>

        <!-- Notas Técnicas MikroTik RouterOS v7.1+ -->
        <section class="help-section help-section--mikrotik" aria-labelledby="help-sec-ros">
          <h3 id="help-sec-ros" class="help-section-title">
            🔧 Notas Técnicas MikroTik RouterOS v7.1+
          </h3>
          <ul class="help-bullet-list">
            <li
              v-for="(note, idx) in currentHelpEntry.mikrotikV7Notes"
              :key="idx"
              class="help-list-item font-mono-note"
            >
              {{ note }}
            </li>
          </ul>
        </section>

        <!-- Roles RBAC Relacionados -->
        <section class="help-section" aria-labelledby="help-sec-roles">
          <h3 id="help-sec-roles" class="help-section-title">
            👥 Roles RBAC con Acceso Operativo
          </h3>
          <div class="help-roles-badges">
            <span
              v-for="role in currentHelpEntry.relatedRoles"
              :key="role"
              class="help-role-pill"
            >
              {{ role }}
            </span>
          </div>
        </section>
      </div>

      <!-- Pie del Cajón con Enlace al Portal Documental Oficial -->
      <footer class="help-drawer-footer">
        <span class="help-footer-hint">
          Manuales completos de Usuario y Administrador disponibles en el portal documental:
        </span>
        <a
          href="https://rosgrid.net/docs/quickstart"
          target="_blank"
          rel="noopener noreferrer"
          class="help-portal-link"
        >
          🌐 Abrir Documentación Oficial en rosgrid.net ↗
        </a>
      </footer>
    </aside>
  </div>
</template>

<style scoped>
  .rg-help-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(5, 8, 15, 0.68);
    backdrop-filter: blur(3px);
    display: flex;
    justify-content: flex-end;
    z-index: 1100;
  }

  .rg-help-drawer {
    width: min(480px, 100vw);
    height: 100vh;
    height: 100dvh;
    background: var(--rg-bg-surface, #111827);
    border-left: 1px solid var(--rg-border-panel, #334155);
    box-shadow: var(--rg-shadow-lg, -8px 0 30px rgba(0, 0, 0, 0.6));
    display: flex;
    flex-direction: column;
    color: var(--rg-text-primary, #f8fafc);
    overflow: hidden;
  }

  .help-drawer-header {
    padding: 16px 18px;
    background: var(--rg-bg-elevated, #1e293b);
    border-bottom: 1px solid var(--rg-border-panel, #334155);
    display: flex;
    flex-direction: column;
    gap: 10px;
    flex-shrink: 0;
  }

  .help-header-title-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .help-badge-group {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .help-context-badge {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--rg-accent-cyan, #22d3ee);
    background: var(--rg-status-info-bg, #0c4a6e);
    border: 1px solid var(--rg-accent-cyan-border, #06b6d4);
    padding: 2px 8px;
    border-radius: 9999px;
  }

  .help-shortcut-hint {
    font-family: var(--rg-font-mono, monospace);
    font-size: 0.7rem;
    color: var(--rg-text-muted, #94a3b8);
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    padding: 2px 6px;
    border-radius: 4px;
  }

  .btn-close-help {
    background: transparent;
    border: 1px solid transparent;
    color: var(--rg-text-secondary, #cbd5e1);
    font-size: 1.1rem;
    width: 30px;
    height: 30px;
    border-radius: 6px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  .btn-close-help:hover {
    background: var(--rg-bg-canvas, #0b0f19);
    color: var(--rg-text-primary, #f8fafc);
    border-color: var(--rg-border-panel, #334155);
  }

  .help-drawer-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--rg-text-primary, #f8fafc);
    line-height: 1.3;
    margin: 0;
  }

  .help-toolbar {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .help-topic-selector-wrap {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .help-topic-select {
    flex: 1;
    min-width: 0;
    background: var(--rg-bg-input, #0b0f19);
    color: var(--rg-text-primary, #f8fafc);
    border: 1px solid var(--rg-border-panel, #334155);
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 0.8rem;
  }

  .btn-reset-topic {
    background: var(--rg-bg-canvas, #0b0f19);
    color: var(--rg-accent-cyan, #22d3ee);
    border: 1px solid var(--rg-border-panel, #334155);
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
  }

  .btn-copy-markdown {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    background: var(--rg-bg-canvas, #0b0f19);
    color: var(--rg-accent-cyan, #22d3ee);
    border: 1px solid var(--rg-accent-cyan-border, #06b6d4);
    border-radius: 6px;
    padding: 7px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .btn-copy-markdown:hover {
    background: var(--rg-status-info-bg, #0c4a6e);
    color: var(--rg-text-primary, #f8fafc);
  }

  .btn-copy-markdown--copied {
    background: var(--rg-status-online-bg, #064e3b);
    color: var(--rg-status-online-text, #6ee7b7);
    border-color: var(--rg-status-online, #10b981);
  }

  .help-drawer-body {
    flex: 1;
    overflow-y: auto;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .help-section {
    background: var(--rg-bg-canvas, #0b0f19);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: 8px;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .help-section--summary {
    border-left: 3px solid var(--rg-accent-cyan, #22d3ee);
  }

  .help-section--governance {
    border-left: 3px solid var(--rg-status-warning, #f59e0b);
  }

  .help-section--mikrotik {
    border-left: 3px solid var(--rg-status-online, #10b981);
  }

  .help-summary-text {
    font-size: 0.85rem;
    color: var(--rg-text-secondary, #cbd5e1);
    line-height: 1.5;
    margin: 0;
  }

  .help-section-title {
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--rg-text-primary, #f8fafc);
    margin: 0;
  }

  .help-ordered-list,
  .help-bullet-list {
    margin: 0;
    padding-left: 18px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .help-list-item {
    font-size: 0.8rem;
    color: var(--rg-text-secondary, #cbd5e1);
    line-height: 1.45;
  }

  .font-mono-note {
    font-family: var(--rg-font-mono, monospace);
    font-size: 0.76rem;
  }

  .help-roles-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .help-role-pill {
    font-family: var(--rg-font-mono, monospace);
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    background: var(--rg-bg-elevated, #1e293b);
    color: var(--rg-accent-cyan, #22d3ee);
    border: 1px solid var(--rg-border-panel, #334155);
  }

  .help-drawer-footer {
    padding: 12px 18px;
    background: var(--rg-bg-elevated, #1e293b);
    border-top: 1px solid var(--rg-border-panel, #334155);
    display: flex;
    flex-direction: column;
    gap: 6px;
    flex-shrink: 0;
  }

  .help-footer-hint {
    font-size: 0.74rem;
    color: var(--rg-text-muted, #94a3b8);
  }

  .help-portal-link {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--rg-accent-cyan, #22d3ee);
    text-decoration: none;
  }

  .help-portal-link:hover {
    text-decoration: underline;
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
