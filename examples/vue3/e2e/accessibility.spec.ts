import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// Definimos las rutas críticas de la aplicación para garantizar cobertura total
const CRITICAL_ROUTES = ['/', '/dashboard', '/login'];

test.describe('Auditoría Estricta de Accesibilidad (WCAG) y Regresión Visual del DOM', () => {
  
  for (const route of CRITICAL_ROUTES) {
    test(`La ruta "${route}" debe cumplir con WCAG 2.1 AA y mantener el diseño pixel-perfect`, async ({ page }) => {
      
      // 1. Intercepción de Red y Mocking (Determinismo)
      // GARANTÍA: Los datos dinámicos, fechas o telemetría romperían la regresión visual.
      // Interceptamos la API para devolver datos estáticos siempre que Playwright navegue.
      await page.route('**/api/**', async (route) => {
        const json = { status: 'mocked', data: [{ id: 1, name: 'Test Data' }] };
        await route.fulfill({ json });
      });

      // Bloqueamos recursos de terceros que introducen ruido (Analytics, Ads, fuentes lentas)
      await page.route('**/*analytics*', route => route.abort());
      await page.route('**/*googletagmanager*', route => route.abort());

      // 2. Navegación y Estabilización
      await page.goto(route);
      // Esperamos a que la red esté inactiva para asegurar que Vue renderizó todos los componentes asíncronos
      await page.waitForLoadState('networkidle');
      // Forzamos la resolución de fuentes y animaciones iniciales
      await page.evaluate(() => document.fonts.ready);

      // 3. Auditoría de Accesibilidad (Axe Core)
      // Exigencia corporativa: Validar contra WCAG 2.0 y 2.1 niveles A y AA
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        // Si usas componentes de terceros incontrolables que violan a11y, exclúyelos explícitamente:
        // .exclude('.clase-del-widget-externo')
        .analyze();

      // Si hay violaciones, Playwright fallará el pipeline detallando el nodo exacto del DOM que incumplió
      expect(accessibilityScanResults.violations).toEqual([]);

      // 4. Regresión Visual (Snapshot Testing)
      // Aprovechando que la app está en un estado estático y validado, tomamos una captura.
      // La primera vez generará la imagen base. Las ejecuciones futuras fallarán si un pixel cambia en el CSS.
      await expect(page).toHaveScreenshot(`snapshot-${route.replace(/\//g, '') || 'home'}.png`, {
        fullPage: true,
      });
    });
  }
});
