// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import {
  HELP_CATALOG_LIST,
  formatHelpEntryAsMarkdown,
  getHelpEntryByKey,
  resolveHelpKeyFromRoute,
  type ContextualHelpEntry,
} from '@/data/helpCatalog';

const isHelpOpen = ref<boolean>(false);
const manualHelpKey = ref<string | null>(null);
const isMarkdownCopied = ref<boolean>(false);
let copyResetTimer: ReturnType<typeof setTimeout> | null = null;

export function useContextualHelp() {
  let route: ReturnType<typeof useRoute> | undefined;
  try {
    route = useRoute();
  } catch {
    route = undefined;
  }

  const routeHelpKey = computed<string>(() => {
    return resolveHelpKeyFromRoute(route?.path, route?.name);
  });

  if (route) {
    watch(
      () => route?.path,
      () => {
        manualHelpKey.value = null;
      },
    );
  }

  const activeHelpKey = computed<string>(() => {
    return manualHelpKey.value || routeHelpKey.value;
  });

  const currentHelpEntry = computed<ContextualHelpEntry>(() => {
    return getHelpEntryByKey(activeHelpKey.value);
  });

  function openHelp(key?: string): void {
    if (key && key.trim()) {
      manualHelpKey.value = key.trim();
    } else {
      manualHelpKey.value = null;
    }
    isHelpOpen.value = true;
  }

  function closeHelp(): void {
    isHelpOpen.value = false;
    manualHelpKey.value = null;
  }

  function toggleHelp(key?: string): void {
    if (key && key.trim()) {
      if (isHelpOpen.value && activeHelpKey.value === key.trim()) {
        closeHelp();
      } else {
        openHelp(key.trim());
      }
      return;
    }
    if (isHelpOpen.value) {
      closeHelp();
    } else {
      openHelp();
    }
  }

  function selectHelpTopic(key: string): void {
    if (key && key.trim()) {
      manualHelpKey.value = key.trim();
    }
  }

  function resetToRouteTopic(): void {
    manualHelpKey.value = null;
  }

  async function copyCurrentHelpAsMarkdown(): Promise<string> {
    const markdown = formatHelpEntryAsMarkdown(currentHelpEntry.value);
    isMarkdownCopied.value = true;
    if (copyResetTimer) {
      clearTimeout(copyResetTimer);
    }
    copyResetTimer = setTimeout(() => {
      isMarkdownCopied.value = false;
    }, 3000);
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(markdown);
      }
    } catch {
      // Ignorar fallo de permisos del portapapeles
    }
    return markdown;
  }

  function handleHelpKeydown(e: KeyboardEvent): void {
    if (e.key === 'F1' || (e.altKey && (e.key === 'h' || e.key === 'H'))) {
      e.preventDefault();
      toggleHelp();
      return;
    }
    if (e.key === 'Escape' && isHelpOpen.value) {
      e.preventDefault();
      closeHelp();
    }
  }

  return {
    isHelpOpen,
    manualHelpKey,
    routeHelpKey,
    activeHelpKey,
    currentHelpEntry,
    allHelpTopics: HELP_CATALOG_LIST,
    isMarkdownCopied,
    openHelp,
    closeHelp,
    toggleHelp,
    selectHelpTopic,
    resetToRouteTopic,
    copyCurrentHelpAsMarkdown,
    handleHelpKeydown,
  };
}
