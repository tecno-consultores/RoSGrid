# 28 — ESTÁNDAR QA 11X FRONTEND (VUE 3): PLAYWRIGHT E2E, ACCESIBILIDAD WCAG 2.1 AA (@axe-core), REGRESIÓN VISUAL, LIGHTHOUSE CI Y KARATE UI (RoSGrid)

**\[DIRECTIVA PARA ANTIGRAVITY\]:** Este documento especifica las pruebas End-to-End, la auditoría de accesibilidad automatizada con @axe-core/playwright, la regresión visual pixel-perfect (toHaveScreenshot), los umbrales de rendimiento en Lighthouse CI y los flujos de negocio en Karate UI para el Frontend de **RoSGrid** (vue3/).




## **1. Configuración de vue3/playwright.config.ts (Frontera Estricta \*\*/\*.e2e.ts)**

// SPDX-License-Identifier: GPL-3.0-only


// Copyright (C) 2026 RoSGrid Contributors


import \{ defineConfig, devices \} from '@playwright/test';


export default defineConfig(\{


  testDir: './e2e',


  // FRONTERA ESTRICTA (TOOL BOUNDARY): Playwright solo ejecuta archivos .e2e.ts


  testMatch: '\*\*/\*.e2e.ts',


  fullyParallel: true,


  forbidOnly: !!process.env.CI,


  retries: process.env.CI ? 2 : 0,


  workers: process.env.CI ? 1 : undefined,


  reporter: \[\['html', \{ open: 'never' \}\], \['list'\]\],


  use: \{


    baseURL: 'http://ui-prod:80',


    trace: 'retain-on-failure',


    video: 'retain-on-failure',


    screenshot: 'only-on-failure',


    timezoneId: 'America/Caracas',


    locale: 'es-VE',


  \},


  projects: \[


    \{


      name: 'chromium',


      use: \{ ...devices\['Desktop Chrome'\] \},


    \},


  \],


  expect: \{


    toHaveScreenshot: \{


      maxDiffPixelRatio: 0.01,


      animations: 'disabled',


      threshold: 0.1,


    \},


  \},


\});




## **2. Suite de Accesibilidad WCAG 2.1 AA y Regresión Visual Determinista (vue3/e2e/accessibility.e2e.ts)**

En **RoSGrid**, vistas como /dashboard o /inventory/routers incluyen el mapa interactivo **OpenStreetMap (Leaflet)** y gráficas alimentadas en vivo. Si Playwright tomara una captura de pantalla con tiles reales descargados de internet o con gráficas moviéndose, la regresión visual (maxDiffPixelRatio: 0.01) fallaría por diferencias de píxeles.


Por ello, vue3/e2e/accessibility.e2e.ts DEBE interceptar tanto \*\*/api/\*\* como los tiles de \*\*/\*openstreetmap\* devolviendo un PNG/SVG estático de 256x256 píxeles en base64 y datos mockeados fijos:


// SPDX-License-Identifier: GPL-3.0-only


// Copyright (C) 2026 RoSGrid Contributors


import \{ test, expect \} from '@playwright/test';


import AxeBuilder from '@axe-core/playwright';


const CRITICAL\_ROUTES = \[


  '/',


  '/login',


  '/dashboard',


  '/inventory/routers',


  '/operations/approvals',


  '/noc-wallboard',


  '/audit-logs',


\];


// Tile PNG gris estático 1x1 para determinismo absoluto en el mapa Leaflet/OSM


const STATIC\_OSM\_TILE\_BASE64 =


  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';


test.describe('Auditoría Estricta de Accesibilidad (WCAG 2.1 AA) y Regresión Visual de RoSGrid', () =\> \{


  for (const route of CRITICAL\_ROUTES) \{


    test(\`La ruta "$\{route\}" debe cumplir con WCAG 2.1 AA (0 violaciones) y mantener el diseño pixel-perfect\`, async (\{ page \}) =\> \{


      // 1. Intercepción Determinista de la API de RoSGrid


      await page.route('\*\*/api/\*\*', async (apiRoute) =\> \{


        const json = \{


          status: 'mocked',


          items: \[


            \{


              id: '01928900-aaaa-7bbb-8ccc-111122223333',


              display\_name: 'RB4011-Borde-Naguanagua',


              ros\_identity: 'MK-BORDE-01',


              network\_role: 'WAN\_BALANCER',


              admin\_state: 'PRODUCTION',


              operational\_status: 'ONLINE',


              physical\_location: 'Naguanagua, Carabobo',


              latitude: 10.2645,


              longitude: -68.0102,


              serial\_number: 'D4460B123456',


              ros\_version: '7.16.1',


              ssl\_trust\_status: 'TRUSTED\_PINNED',


            \},


          \],


        \};


        await apiRoute.fulfill(\{ status: 200, contentType: 'application/json', body: JSON.stringify(json) \});


      \});


      // 2. Intercepción Determinista de Tiles de OpenStreetMap (Cero Red Externa)


      await page.route('\*\*/\*tile.openstreetmap.org/\*\*', async (tileRoute) =\> \{


        await tileRoute.fulfill(\{


          status: 200,


          contentType: 'image/png',


          body: Buffer.from(STATIC\_OSM\_TILE\_BASE64, 'base64'),


        \});


      \});


      // 3. Bloqueo de ruido externo


      await page.route('\*\*/\*analytics\*', (r) =\> r.abort());


      await page.route('\*\*/\*googletagmanager\*', (r) =\> r.abort());


      // 4. Navegación y estabilización de fuentes/DOM


      await page.goto(route);


      await page.waitForLoadState('networkidle');


      await page.evaluate(() =\> document.fonts.ready);


      // 5. Auditoría de Accesibilidad WCAG 2.0 / 2.1 Niveles A y AA con Axe Core


      const accessibilityScanResults = await new AxeBuilder(\{ page \})


        .withTags(\['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'\])


        .analyze();


      expect(accessibilityScanResults.violations).toEqual(\[\]);


      // 6. Regresión Visual (Snapshot Testing Pixel-Perfect)


      const snapshotName = \`snapshot-$\{route.replace(/\\//g, '\_') || 'home'\}.png\`;


      await expect(page).toHaveScreenshot(snapshotName, \{


        fullPage: true,


      \});


    \});


  \}


\});




## **3. Suite de Flujos E2E Funcionales (vue3/e2e/rosgrid\_workflows.e2e.ts)**

Además de accessibility.e2e.ts, AntiGravity DEBE crear vue3/e2e/rosgrid\_workflows.e2e.ts validando:


1. **Flujo Login Multi-Tenant + 2FA TOTP:** Ingresar tenant\_slug (isp-norte), correo y contraseña -\> pasar al paso 2FA -\> ingresar código de 6 dígitos -\> verificar redirección a /dashboard.

2. **Flujo Bóveda *Step-Up Auth* de 30s:** Con sesión de TENANT\_ADMIN, abrir VaultRevealModal, ingresar código 2FA y motivo, verificar que aparece la clave desencriptada y la barra de cuenta regresiva de 30s.

3. **Flujo Consola WebFig + Gráficas Efímeras:** Entrar a un MikroTik, verificar que el RingBuffer renderiza la gráfica de CPU/Tráfico al recibir un frame simulado, salir a /inventory/routers y volver a entrar verificando que el buffer se reinició desde cero (igual que en WinBox).

4. **Flujo *Kill-Switch* en Tiempo Real:** Simular la recepción del evento WebSocket SESSION\_KILLED y verificar que la aplicación limpia el estado y redirige en el acto a /login?reason=session\_revoked.




## **4. Auditoría de Rendimiento con Lighthouse CI (vue3/lighthouserc.js)**

module.exports = \{


  ci: \{


    collect: \{


      url: \['http://ui-prod:80/', 'http://ui-prod:80/login'\],


      numberOfRuns: 3,


    \},


    assert: \{


      assertions: \{


        'categories:performance': \['error', \{ minScore: 0.9 \}\],


        'categories:accessibility': \['error', \{ minScore: 0.95 \}\],


        'categories:best-practices': \['error', \{ minScore: 0.9 \}\],


        'categories:seo': \['error', \{ minScore: 0.9 \}\],


      \},


    \},


    upload: \{


      target: 'filesystem',


      outputDir: './lhci-reports',


    \},


  \},


\};




## **5. Pruebas de Aceptación BDD con Karate UI (vue3/test/ui\_business\_flow.feature)**

Feature: Flujo principal de negocio de la interfaz Vue 3 de RoSGrid


  Background:


    \* configure driver = \{ type: 'chrome', headless: true, addOptions: \['--no-sandbox'\] \}


    \* def baseUrl = karate.env == 'local' ? 'http://localhost:8080' : karate.properties\['UI\_BASE\_URL'\]


  Scenario: El operador accede al Dashboard/Inventario de RoSGrid y actualiza el estado de la flota


    Given driver baseUrl + '/'


    And waitFor("h1:contains('Dashboard')")


    When click("button.btn-primary:contains('Actualizar Datos')")


    Then waitFor(".status-indicator.success")


    And match text(".status-text") == 'Actualizado'


*(Nota importante para AntiGravity: En la vista principal / y /dashboard de RoSGrid, asegúrate de incluir el encabezado \<h1\>Dashboard — Flota MikroTik\</h1\>, el botón button.btn-primary con texto 'Actualizar Datos' y el indicador .status-indicator.success con .status-text 'Actualizado' al refrescar el estado de los routers, garantizando compatibilidad 100% nativa con el escenario corporativo de Karate UI).*
