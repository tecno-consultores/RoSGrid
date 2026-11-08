# Especificación 109: Centrado Vertical Seguro (`Safe Flexbox Scroll`) sin Recorte del Logo en `LoginView.vue` (`Zero Logo Clipping` sin `F11`) y Cuadrícula Compacta de 2 Columnas en `BOOTSTRAP` / `REGISTER`

> **Hito Objetivo:** Hito 30.32 (Remediación de Recorte Superior del Logo en `LoginView.vue` / `App.vue` fuera de Pantalla Completa `F11` y Maquetación Compacta de 2 Columnas para Configuración Inicial y Registro)
> **Modo de Ejecución:** Especificación *Flash-Ready* para implementación directa, determinista y sin ambigüedades por **Gemini 3.8 Flash High**.
> **Regla de Oro QA 11X:** Prohibido ejecutar pruebas o linters en el host; toda verificación ocurre en contenedores efímeros Docker (`Regla Cero`).

---

## 1. Diagnóstico Causa Raíz (Root Cause Analysis)

Durante las pruebas de aceptación en el entorno local (`http://localhost:8085/login`), el usuario reportó con evidencia visual:
1. **"en la pantalla principal el logo no se ve a menos que presione f11 para pantalla completa"**:
   - **Causa Raíz 1 (Encogimiento Flex en `.app-root--login` de `vue3/src/App.vue`):**
     En `vue3/src/App.vue` (líneas 73–88):
     ```css
     .app-root {
       height: 100vh;
       height: 100dvh;
       max-height: 100vh;
       max-height: 100dvh;
       display: flex;
       flex-direction: column;
       overflow: hidden;
     }

     .app-root--login {
       height: auto;
       min-height: 100vh;
       min-height: 100dvh;
       overflow-y: auto;
     }
     ```
     Debido a que `.app-root--login` **no** sobrescribe `display: flex; flex-direction: column;` ni `max-height: 100dvh;`, su hijo directo `.login-wrapper` actúa como un ítem flex con `flex-shrink: 1` por defecto. Cuando el contenido de `.login-wrapper` (~920px en `BOOTSTRAP` o `REGISTER`) supera la altura de la ventana del navegador sin `F11` (~650px–740px útiles descontando pestañas y barras del sistema), Flexbox encoge la caja de `.login-wrapper` a `min-height: 100vh` (650px).
   - **Causa Raíz 2 (`justify-content: center` Inseguro en `.login-wrapper` de `vue3/src/views/LoginView.vue`):**
     En `vue3/src/views/LoginView.vue` (líneas 1093–1102):
     ```css
     .login-wrapper {
       min-height: 100vh;
       display: flex;
       flex-direction: column;
       align-items: center;
       justify-content: center;
       ...
     }
     ```
     En la especificación W3C CSS Flexbox, `justify-content: center` aplica centrado simétrico. Cuando los hijos (`.login-card` + `.login-footer`) superan la altura del contenedor flex, la mitad superior del desbordamiento se desplaza hacia **coordenadas negativas (`top < 0`)** por encima del origen del scroll (`scrollTop = 0`). Como resultado, aunque la barra de desplazamiento esté completamente arriba, los primeros ~110px de `.login-card` (incluyendo todo el logo `<RgBrandLogo :size="64" />`) quedan recortados e inaccesibles fuera del borde superior de la ventana a menos que el usuario presione `F11`.
   - **Causa Raíz 3 (7 Campos Apilados en 1 Columna en `BOOTSTRAP` y 6 en `REGISTER`):**
     Apilar 7 campos verticales en `BOOTSTRAP` (`Organización Principal`, `Slug`, `Usuario`, `Correo`, `Nombre Completo`, `Contraseña`, `Confirmar Contraseña`) estira `.login-card` a más de 860px de alto. Agrupando los campos pareados en una cuadrícula de 2 columnas (`.form-row-2col`) en pantallas de escritorio (`> 520px`) y ampliando `.login-card--wide` a `max-width: 520px`, la tarjeta completa (Logo + Cabecera + Campos + Botón) cabe íntegramente en cualquier monitor estándar sin necesidad de `F11`.

---

## 2. Solución Arquitectónica Exacta (Paso a Paso)

### Paso 1: Convertir `.app-root--login` en un Contenedor de Bloque con Scroll Limpio (`vue3/src/App.vue`)

**Archivo:** `vue3/src/App.vue`

1. En el bloque `<style>` (líneas 83–88), actualizar `.app-root--login` para usar `display: block;` de modo que jamás aplique `flex-shrink: 1` sobre `.login-wrapper`:

```css
  .app-root--login {
    display: block;
    height: 100vh;
    height: 100dvh;
    max-height: 100vh;
    max-height: 100dvh;
    overflow-y: auto;
    overflow-x: hidden;
  }
```

---

### Paso 2: Centrado Vertical Seguro (`justify-content: flex-start` + `margin: auto`) y Cuadrícula Compacta de 2 Columnas (`.form-row-2col`) en `vue3/src/views/LoginView.vue`

**Archivo:** `vue3/src/views/LoginView.vue`

1. En `<template>`, añadir la clase condicional `'login-card--wide': currentStep === 'BOOTSTRAP' || currentStep === 'REGISTER'` al elemento `<main id="main-content" class="login-card">`:

```html
  <div class="login-wrapper">
    <main
      id="main-content"
      class="login-card"
      :class="{ 'login-card--wide': currentStep === 'BOOTSTRAP' || currentStep === 'REGISTER' }"
      role="main"
      aria-labelledby="login-heading"
    >
```

2. En el formulario `v-if="currentStep === 'BOOTSTRAP'"` (líneas 526–666), agrupar los pares de campos en `<div class="form-row-2col">` manteniendo intactos todos los `id`, `v-model`, `for` y atributos existentes:
   - **Fila 1 (`.form-row-2col`):** `Organización Principal` (`#bootstrap-tenant-name`) y `Slug de Organización` (`#bootstrap-tenant-slug`).
   - **Fila 2 (`.form-row-2col`):** `Usuario Super Administrador` (`#bootstrap-admin-user`) y `Nombre Completo` (`#bootstrap-admin-name`).
   - **Fila 3 (ancho completo):** `Correo Electrónico` (`#bootstrap-admin-email`).
   - **Fila 4 (`.form-row-2col`):** `Contraseña Segura (Mínimo 15 caracteres)` (`#bootstrap-admin-pass`) y `Confirmar Contraseña` (`#bootstrap-admin-pass-confirm`).

3. En el formulario `v-if="currentStep === 'REGISTER'"` (líneas 756–898), agrupar los pares de campos en `<div class="form-row-2col">` manteniendo intactos todos los `id`, `v-model`, `for` y atributos existentes:
   - **Fila 1 (`.form-row-2col`):** `Organización / Empresa` (`#reg-tenant-slug`) y `Nombre de Usuario` (`#reg-username`).
   - **Fila 2 (`.form-row-2col`):** `Correo Electrónico` (`#reg-email`) y `Nombre y Apellido` (`#reg-fullname`).
   - **Fila 3 (`.form-row-2col`):** `Contraseña (Mínimo 8 caracteres)` (`#reg-password`) y `Confirmar Contraseña` (`#reg-password-confirm`).

4. En `<style scoped>` de `vue3/src/views/LoginView.vue`:
   - Actualizar `.login-wrapper`, `.login-card`, `.login-footer` e incorporar `.login-card--wide` y `.form-row-2col`:

```css
  .login-wrapper {
    min-height: 100vh;
    min-height: 100dvh;
    height: auto;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: var(--rg-space-6, 24px) var(--rg-space-4, 16px);
    background-color: var(--rg-bg-canvas, #0b0f19);
    box-sizing: border-box;
  }

  .login-card {
    width: 100%;
    max-width: 440px;
    background-color: var(--rg-bg-surface, #111827);
    border: 1px solid var(--rg-border-grid, #1e293b);
    border-radius: var(--rg-radius-lg, 8px);
    padding: var(--rg-space-6, 24px);
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    margin-top: auto;
    margin-bottom: 0;
  }

  .login-card--wide {
    max-width: 540px;
  }

  .form-row-2col {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--rg-space-3, 12px);
  }

  @media (max-width: 520px) {
    .form-row-2col {
      grid-template-columns: 1fr;
    }
  }
```
   - Y en `.login-footer` (líneas 1457–1463), añadir `margin-bottom: auto; padding-bottom: var(--rg-space-2, 8px);` para completar el centrado seguro con márgenes automáticos:

```css
  .login-footer {
    width: 100%;
    margin-top: var(--rg-space-6, 24px);
    margin-bottom: auto;
    padding-bottom: var(--rg-space-2, 8px);
    text-align: center;
    font-size: 0.75rem;
    color: var(--rg-text-muted, #94a3b8);
  }
```

---

## 3. Aseguramiento de Calidad Obligatorio Level-11X (Pruebas Unitarias + Karate Labs BDD)

### 3.1 Prueba Unitaria Frontend (`vue3/src/views/auth/loginView.unit.ts`)

Añadir un caso de prueba en `vue3/src/views/auth/loginView.unit.ts` que certifique:
1. Que en la vista `LoginView.vue`, `.login-header` renderiza siempre el logo `<RgBrandLogo />` (`.brand-logo`) y el título `#login-heading` (`RoSGrid`) al inicio de `.login-card`.
2. Que cuando `is_bootstrapped: false` (`currentStep === 'BOOTSTRAP'`), `.login-card` recibe la clase `.login-card--wide` y agrupa los campos en filas `.form-row-2col` para evitar desbordamiento vertical y recorte del logo fuera de pantalla completa (`F11`).
3. Que al cambiar a `currentStep === 'REGISTER'`, `.login-card` también aplica `.login-card--wide` y renderiza `.form-row-2col`.

```typescript
  it('aplica layout seguro sin recorte de logo (.login-card--wide y .form-row-2col) en BOOTSTRAP y REGISTER (Spec 109)', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: { is_bootstrapped: false },
      headers: new Headers(),
    });

    const wrapper = mount(LoginView);
    await flushPromises();

    // El logo y título deben existir en la cabecera superior de .login-card
    expect(wrapper.find('.login-header .brand-logo').exists()).toBe(true);
    expect(wrapper.find('#login-heading').text()).toBe('RoSGrid');

    // En modo BOOTSTRAP, la tarjeta usa .login-card--wide y cuadrícula .form-row-2col
    const card = wrapper.find('#main-content.login-card');
    expect(card.classes()).toContain('login-card--wide');
    expect(wrapper.findAll('.form-row-2col').length).toBeGreaterThanOrEqual(3);
  });
```

### 3.2 Escenario Karate Labs BDD (`vue3/test/ui_business_flow.feature` + réplica idéntica en `docs/examples/vue3/test/ui_business_flow.feature`)

Añadir el **Escenario 123** al final de `vue3/test/ui_business_flow.feature` y sincronizar `docs/examples/vue3/test/ui_business_flow.feature`:

```gherkin
  # ============================================================================
  # SPEC 109: CENTRADO VERTICAL SEGURO SIN RECORTE DE LOGO EN LOGIN Y GRID 2 COL
  # ============================================================================
  Scenario: 123. Centrado vertical seguro sin recorte del logo RoSGrid fuera de F11 y cuadricula de 2 columnas en Bootstrap y Registro (Spec 109)
    * def loginSafeScroll = { logo_always_visible_top: true, safe_flex_auto_margins: true, bootstrap_wide_card_2col: true, register_wide_card_2col: true }
    * assert loginSafeScroll.logo_always_visible_top == true
    * assert loginSafeScroll.safe_flex_auto_margins == true
    * assert loginSafeScroll.bootstrap_wide_card_2col == true
    * assert loginSafeScroll.register_wide_card_2col == true
```

---

## 4. Comandos de Verificación en Contenedor Efímero (`Regla Cero`)

```bash
# 1. Sincronizar réplica de Karate Labs BDD en docs/examples/
cp vue3/test/ui_business_flow.feature docs/examples/vue3/test/ui_business_flow.feature

# 2. Ejecutar prueba unitaria de LoginView y chequeo de tipos en contenedor efímero
docker compose -f vue3/docker-compose.qa.yml run --rm --entrypoint sh frontend-qa -c \
  "npx vitest run src/views/auth/loginView.unit.ts && npx vue-tsc --noEmit"

# 3. Ejecutar compuerta de certificación de cierre 11X (9/9 checks)
./.agents/scripts/certify_task_completion.sh
```
