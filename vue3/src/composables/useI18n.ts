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

  function t(
    key: string,
    fallbackOrParams?: string | Record<string, string | number>,
    params?: Record<string, string | number>,
  ): string {
    const fallback = typeof fallbackOrParams === 'string' ? fallbackOrParams : undefined;
    const interpolationParams =
      typeof fallbackOrParams === 'object' && fallbackOrParams !== null
        ? fallbackOrParams
        : params;

    const currentDict = dictionaries[activeLocale.value] || dictionaries.es;
    let val = getNestedValue(currentDict, key);
    if (val === undefined && activeLocale.value !== 'es') {
      val = getNestedValue(dictionaries.es, key);
    }
    let result = val !== undefined ? val : fallback !== undefined ? fallback : key;
    if (interpolationParams) {
      for (const [k, v] of Object.entries(interpolationParams)) {
        result = result.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v));
      }
    }
    return result;
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
