// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import FieldTechOperationsView from './FieldTechOperationsView.vue';
import { useAuthStore } from '@/stores/useAuthStore';

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useRoute: () => ({ params: {}, query: {} }),
}));

describe('FieldTechOperationsView.vue — Envoltorio de Operaciones de Campo', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.restoreAllMocks();
    window.alert = vi.fn();
    HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
      beginPath: vi.fn(),
      moveTo: vi.fn(),
      lineTo: vi.fn(),
      stroke: vi.fn(),
      clearRect: vi.fn(),
    });
    HTMLCanvasElement.prototype.toDataURL = vi.fn().mockReturnValue('data:image/png;base64,mock');
  });

  it('monta correctamente el componente táctico FieldTechMobileView dentro de main', () => {
    const authStore = useAuthStore();
    authStore.updateTenantFeatures({ isp_module_enabled: true });

    const wrapper = mount(FieldTechOperationsView);
    expect(wrapper.find('main.field-tech-operations-view').exists()).toBe(true);
    expect(wrapper.find('#tab-btn-nap').exists()).toBe(true);
  });
});
