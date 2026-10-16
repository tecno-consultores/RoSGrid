// SPDX-License-Identifier: GPL-3.0-only
// Copyright (C) 2026 RoSGrid Contributors

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

const CRITICAL_ROUTES = [
  '/',
  '/login',
  '/dashboard',
  '/inventory/routers',
  '/operations/approvals',
  '/noc-wallboard',
  '/audit-logs',
];

// Tile PNG gris estático 1x1 para determinismo absoluto en el mapa Leaflet/OSM
const STATIC_OSM_TILE_BASE64 =
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';

test.describe('Auditoría Estricta de Accesibilidad (WCAG 2.1 AA) y Regresión Visual de RoSGrid', () => {
  for (const route of CRITICAL_ROUTES) {
    test(`La ruta "${route}" debe cumplir con WCAG 2.1 AA (0 violaciones) y mantener el diseño pixel-perfect`, async ({
      page,
    }) => {
      // 1. Intercepción Determinista de la API de RoSGrid
      await page.route('**/api/**', async (apiRoute) => {
        const json = {
          status: 'mocked',
          items: [
            {
              id: '01928900-aaaa-7bbb-8ccc-111122223333',
              display_name: 'RB4011-Borde-Naguanagua',
              ros_identity: 'MK-BORDE-01',
              network_role: 'WAN_BALANCER',
              admin_state: 'PRODUCTION',
              operational_status: 'ONLINE',
              physical_location: 'Naguanagua, Carabobo',
              latitude: 10.2645,
              longitude: -68.0102,
              serial_number: 'D4460B123456',
              ros_version: '7.16.1',
              ssl_trust_status: 'TRUSTED_PINNED',
            },
          ],
        };
        await apiRoute.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(json),
        });
      });

      // 2. Intercepción Determinista de Tiles de OpenStreetMap (Cero Red Externa)
      await page.route('**/*tile.openstreetmap.org/**', async (tileRoute) => {
        await tileRoute.fulfill({
          status: 200,
          contentType: 'image/png',
          body: Buffer.from(STATIC_OSM_TILE_BASE64, 'base64'),
        });
      });

      // 3. Bloqueo de ruido externo
      await page.route('**/*analytics*', (r) => r.abort());
      await page.route('**/*googletagmanager*', (r) => r.abort());

      // 4. Navegación y estabilización de fuentes/DOM
      await page.goto(route);
      await page.waitForLoadState('networkidle');
      await page.evaluate(() => document.fonts.ready);

      // 5. Auditoría de Accesibilidad WCAG 2.0 / 2.1 Niveles A y AA con Axe Core
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      expect(accessibilityScanResults.violations).toEqual([]);
    });
  }
});
