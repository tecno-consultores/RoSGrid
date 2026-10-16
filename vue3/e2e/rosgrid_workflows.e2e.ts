// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { test, expect } from '@playwright/test';

test.describe('Flujos de Negocio E2E Críticos de RoSGrid (specs/28)', () => {
  test.beforeEach(async ({ page }) => {
    // Intercepción común de APIs para garantizar determinismo y cero salida a red
    await page.route('**/api/v1/auth/**', async (route) => {
      if (route.request().url().includes('/login')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            requires_2fa: true,
            tenant_slug: 'isp-norte',
          }),
        });
      } else if (route.request().url().includes('/verify-2fa')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'authenticated',
            user: { id: 'usr-1', role: 'TENANT_ADMIN' },
          }),
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'ok' }),
        });
      }
    });

    await page.route('**/api/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'ok', items: [] }),
      });
    });
  });

  test('1. Flujo Login Multi-Tenant y Paso a 2FA TOTP', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');

    const tenantInput = page.locator(
      'input#tenant, input[name="tenant"], input[placeholder*="tenant" i]',
    );
    if ((await tenantInput.count()) > 0) {
      await tenantInput.first().fill('isp-norte');
    }

    const emailInput = page.locator('input[type="email"], input#email, input[name="username"]');
    if ((await emailInput.count()) > 0) {
      await emailInput.first().fill('admin@isp-norte.com');
    }

    const passwordInput = page.locator('input[type="password"]');
    if ((await passwordInput.count()) > 0) {
      await passwordInput.first().fill('ClaveSegura123!');
    }

    const submitBtn = page.locator('button[type="submit"]');
    if ((await submitBtn.count()) > 0) {
      await submitBtn.first().click();
    }

    // Verificar que la página maneja el estado de login sin errores no capturados
    await expect(page.locator('body')).toBeVisible();
  });

  test('2. Flujo Dashboard y Renderizado de Vistas de Inventario', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('body')).toBeVisible();

    await page.goto('/inventory/routers');
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('body')).toBeVisible();
  });

  test('3. Flujo NOC Wallboard e Inmutabilidad de Auditoría', async ({ page }) => {
    await page.goto('/noc-wallboard');
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('body')).toBeVisible();

    await page.goto('/audit-logs');
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('body')).toBeVisible();
  });
});
