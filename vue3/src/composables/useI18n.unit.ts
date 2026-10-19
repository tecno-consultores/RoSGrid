// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach } from 'vitest';
import { useI18n } from './useI18n';

describe('useI18n — Composable de Internacionalización Reactivo', () => {
  beforeEach(() => {
    window.localStorage.clear();
    const { setLocale } = useI18n();
    setLocale('es');
  });

  it('inicia por defecto en idioma español ("es")', () => {
    const { locale } = useI18n();
    expect(locale.value).toBe('es');
  });

  it('traduce claves existentes en el diccionario español', () => {
    const { t } = useI18n();
    expect(t('common.save')).toBe('Guardar');
    expect(t('nav.inventory')).toBe('Inventario');
    expect(t('nav.subscribers_map')).toBe('Mapa de Clientes (ONUs)');
    expect(t('field_tech.capture_gps')).toBe('📍 Capturar Coordenadas GPS');
  });

  it('retorna la clave o el fallback provisto si la clave no existe', () => {
    const { t } = useI18n();
    expect(t('non.existent.key')).toBe('non.existent.key');
    expect(t('another.missing.key', 'Texto por defecto')).toBe('Texto por defecto');
  });

  it('permite cambiar el idioma a inglés ("en") y actualiza traducciones', () => {
    const { locale, setLocale, t } = useI18n();
    setLocale('en');
    expect(locale.value).toBe('en');
    expect(t('common.save')).toBe('Save');
    expect(t('nav.inventory')).toBe('Inventory');
    expect(t('nav.subscribers_map')).toBe('Subscribers Map (ONUs)');
    expect(t('field_tech.capture_gps')).toBe('📍 Capture GPS Coordinates');
    expect(window.localStorage.getItem('rg_locale')).toBe('en');
    expect(document.documentElement.lang).toBe('en');
  });

  it('alterna el idioma entre "es" y "en" con toggleLocale()', () => {
    const { locale, toggleLocale, setLocale } = useI18n();
    setLocale('es');
    expect(locale.value).toBe('es');

    toggleLocale();
    expect(locale.value).toBe('en');

    toggleLocale();
    expect(locale.value).toBe('es');
  });

  it('ignora códigos de idioma no soportados', () => {
    const { locale, setLocale } = useI18n();
    setLocale('es');
    (setLocale as (l: string) => void)('fr');
    expect(locale.value).toBe('es');
  });

  it('expone la lista de idiomas disponibles', () => {
    const { availableLocales } = useI18n();
    expect(availableLocales).toContain('es');
    expect(availableLocales).toContain('en');
  });
});
