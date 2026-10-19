// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { ref, computed } from 'vue';
import esDict from '@/locales/es.json';
import enDict from '@/locales/en.json';

export type SupportedLocale = 'es' | 'en';

type TranslationDict = { [key: string]: string | TranslationDict };

const dictionaries: Record<SupportedLocale, TranslationDict> = {
  es: esDict as TranslationDict,
  en: enDict as TranslationDict,
};

function getStoredLocale(): SupportedLocale {
  if (typeof window !== 'undefined' && window.localStorage) {
    const saved = window.localStorage.getItem('rg_locale');
    if (saved === 'es' || saved === 'en') {
      return saved;
    }
  }
  return 'es';
}

const activeLocale = ref<SupportedLocale>(getStoredLocale());

export function useI18n() {
  function getNestedValue(obj: TranslationDict, path: string): string | undefined {
    const parts = path.split('.');
    let current: string | TranslationDict | undefined = obj;
    for (const part of parts) {
      if (current === null || current === undefined || typeof current !== 'object') {
        return undefined;
      }
      // eslint-disable-next-line security/detect-object-injection
      current = (current as TranslationDict)[part];
    }
    return typeof current === 'string' ? current : undefined;
  }

  function t(key: string, fallback?: string): string {
    const currentDict = dictionaries[activeLocale.value] || dictionaries.es;
    const val = getNestedValue(currentDict, key);
    if (val !== undefined) {
      return val;
    }
    // Fallback al diccionario en español si el idioma actual no tiene la clave
    if (activeLocale.value !== 'es') {
      const fallbackVal = getNestedValue(dictionaries.es, key);
      if (fallbackVal !== undefined) {
        return fallbackVal;
      }
    }
    return fallback !== undefined ? fallback : key;
  }

  function setLocale(locale: SupportedLocale): void {
    if (locale !== 'es' && locale !== 'en') return;
    activeLocale.value = locale;
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem('rg_locale', locale);
    }
    if (typeof document !== 'undefined') {
      document.documentElement.lang = locale;
    }
  }

  function toggleLocale(): void {
    const next = activeLocale.value === 'es' ? 'en' : 'es';
    setLocale(next);
  }

  return {
    locale: computed(() => activeLocale.value),
    t,
    setLocale,
    toggleLocale,
    availableLocales: ['es', 'en'] as const,
  };
}
