// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const CRITICAL_ROUTES = ['/login', '/inventory'];

test.describe('Auditoría Estricta de Accesibilidad (WCAG) y Regresión Visual del DOM', () => {
  for (const route of CRITICAL_ROUTES) {
    test(`La ruta "${route}" debe cumplir con WCAG 2.1 AA`, async ({ page }) => {
      await page.route('**/api/**', async (routeHandler) => {
        const json = { status: 'mocked', data: [] };
        await routeHandler.fulfill({ json });
      });

      await page.goto(route);
      await page.waitForLoadState('domcontentloaded');

      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    });
  }
});
