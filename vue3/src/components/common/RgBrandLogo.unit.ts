// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RgBrandLogo from './RgBrandLogo.vue';

describe('RgBrandLogo.vue — Isotipo Vectorial de Alta Definición 512×512 (Hito 30.1)', () => {
  it('renderiza con tamaño por defecto de 28px y arte vectorial 512×512 completo', () => {
    const wrapper = mount(RgBrandLogo);

    const wrap = wrapper.find('.rg-brand-logo-wrap');
    expect(wrap.exists()).toBe(true);
    expect(wrap.attributes('style')).toContain('width: 28px');
    expect(wrap.attributes('style')).toContain('height: 28px');

    const svg = wrapper.find('svg.rg-brand-logo-svg');
    expect(svg.exists()).toBe(true);
    expect(svg.attributes('width')).toBe('28');
    expect(svg.attributes('height')).toBe('28');
    expect(svg.attributes('viewBox')).toBe('0 0 512 512');

    // Verificar contenedor táctico redondeado Deep Navy
    const rect = svg.find('rect');
    expect(rect.exists()).toBe(true);
    expect(rect.attributes('rx')).toBe('96');
    expect(rect.attributes('ry')).toBe('96');
    expect(rect.attributes('fill')).toBe('url(#rgBgGrad)');

    // Verificar constelaciones R (Cyber Blue) y G (Electric Orange)
    expect(wrapper.find('.rg-constellation-r').exists()).toBe(true);
    expect(wrapper.find('.rg-constellation-g').exists()).toBe(true);
    expect(wrapper.html()).toContain('id="rgNeonGlow"');
    expect(wrapper.html()).toContain('id="rgCyberBlue"');
    expect(wrapper.html()).toContain('id="rgElectricOrange"');

    // Fallback de imagen presente y clase por defecto
    const fallbackImg = wrapper.find('img.brand-logo-fallback');
    expect(fallbackImg.exists()).toBe(true);
    expect(fallbackImg.classes()).toContain('brand-logo');
    expect(fallbackImg.attributes('src')).toBe('/favicon.svg');
    expect(fallbackImg.attributes('width')).toBe('28');
    expect(fallbackImg.attributes('height')).toBe('28');
  });

  it('renderiza la malla vectorial R y G con dimensiones configurables y clase personalizada', () => {
    const wrapper = mount(RgBrandLogo, {
      props: {
        size: 64,
        imgClass: 'brand-logo-img',
      },
    });

    const wrap = wrapper.find('.rg-brand-logo-wrap');
    expect(wrap.attributes('style')).toContain('width: 64px');
    expect(wrap.attributes('style')).toContain('height: 64px');

    const svg = wrapper.find('svg.rg-brand-logo-svg');
    expect(svg.attributes('width')).toBe('64');
    expect(svg.attributes('height')).toBe('64');
    expect(svg.attributes('viewBox')).toBe('0 0 512 512');

    expect(wrapper.find('.rg-constellation-r').attributes('filter')).toBe('url(#rgNeonGlow)');
    expect(wrapper.find('.rg-constellation-g').attributes('filter')).toBe('url(#rgNeonGlow)');
    expect(wrapper.html()).toContain('--rg-brand-cyber-blue');
    expect(wrapper.html()).toContain('--rg-brand-electric-orange');

    const img = wrapper.find('img.brand-logo-img');
    expect(img.exists()).toBe(true);
    expect(img.attributes('src')).toBe('/favicon.svg');
    expect(img.attributes('width')).toBe('64');
    expect(img.attributes('height')).toBe('64');
  });
});
