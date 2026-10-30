// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import RgLayer2RscExportDiffModal from './RgLayer2RscExportDiffModal.vue';

describe('RgLayer2RscExportDiffModal.vue (Spec 54 — 27.16.6)', () => {
  const sampleExport = {
    ros_path: 'certificate',
    exported_rsc: '/certificate\nadd name=rosgrid-ca common-name=rosgrid-ca trusted=yes',
    baseline_rsc: '/certificate\nadd name=rosgrid-ca common-name=rosgrid-ca trusted=no',
    unified_diff:
      '--- backup/certificate.rsc\n+++ live/certificate.rsc\n@@ -1,2 +1,2 @@\n-add name=rosgrid-ca common-name=rosgrid-ca trusted=no\n+add name=rosgrid-ca common-name=rosgrid-ca trusted=yes',
    has_drift: true,
    backup_timestamp: '2026-10-30T12:00:00Z',
  };

  it('renderiza script .rsc y alterna a la pestaña de Diff unificado coloreado', async () => {
    const wrapper = mount(RgLayer2RscExportDiffModal, {
      props: {
        isOpen: true,
        exportData: sampleExport,
      },
    });

    expect(wrapper.find('#layer2-rsc-code').text()).toContain('add name=rosgrid-ca');
    expect(wrapper.find('.drift-badge--warn').exists()).toBe(true);

    await wrapper.find('#tab-rsc-diff').trigger('click');
    expect(wrapper.find('#layer2-rsc-diff-view').exists()).toBe(true);
    expect(wrapper.findAll('.diff-line--add').length).toBeGreaterThan(0);
    expect(wrapper.findAll('.diff-line--del').length).toBeGreaterThan(0);

    await wrapper.find('#btn-copy-rsc').trigger('click');
    await wrapper.find('.btn-close').trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });
});
