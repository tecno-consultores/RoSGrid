// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RgBrandLogo from './RgBrandLogo.vue';

describe('RgBrandLogo.vue — Isotipo Vectorial Reactivo al Tema (Hito 27.15)', () => {
  it('renderiza la malla vectorial R (Cyber Blue) y G (Electric Orange) con dimensiones configurables', () => {
    const wrapper = mount(RgBrandLogo, {
      props: {
        size: 64,
        imgClass: 'brand-logo-img',
      },
    });

    const svg = wrapper.find('svg.rg-brand-logo-svg');
    expect(svg.exists()).toBe(true);
    expect(svg.attributes('width')).toBe('64');
    expect(svg.attributes('height')).toBe('64');
    expect(wrapper.find('.rg-constellation-r').exists()).toBe(true);
    expect(wrapper.find('.rg-constellation-g').exists()).toBe(true);
    expect(wrapper.html()).toContain('--rg-brand-cyber-blue');
    expect(wrapper.html()).toContain('--rg-brand-electric-orange');
    expect(wrapper.find('img.brand-logo-img').attributes('src')).toBe('/favicon.svg');
  });
});
