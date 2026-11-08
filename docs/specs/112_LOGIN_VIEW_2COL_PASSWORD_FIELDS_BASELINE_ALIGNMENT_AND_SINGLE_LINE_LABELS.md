# Especificación 112: Alineación Geométrica de Campos en Filas de 2 Columnas (`.form-row-2col`) y Etiquetas de Contraseña en 1 Línea sin Asterisco Huérfano en `LoginView.vue`

> **Hito Asociado:** Hito 30.35 (Simetría Vertical de Inputs y Etiquetas de 1 Línea en Filas `.form-row-2col` de `LoginView.vue`)
> **Estado:** Pendiente de Implementación (`[ ]` en `ROADMAP.md`)
> **Prioridad:** Alta (Pulido Visual *Refactoring UI*, Simetría de Formularios y Aseguramiento de Calidad Level-11X)
> **Archivos Afectados:**
> - `vue3/src/views/LoginView.vue`
> - `vue3/src/views/auth/loginView.unit.ts`
> - `vue3/test/ui_business_flow.feature` (+ réplica exacta en `docs/examples/vue3/test/ui_business_flow.feature`)

---

## 1. Diagnóstico de la Falla Visual Reportada

Al visualizar el formulario de **Configuración Inicial (`BOOTSTRAP`)** o **Solicitud de Registro (`REGISTER`)** en `LoginView.vue` tras agrupar los campos pareados en filas de 2 columnas (`.form-row-2col`), los dos campos de contraseña (`#bootstrap-admin-pass` y `#bootstrap-admin-pass-confirm`, así como `#reg-password` y `#reg-password-confirm`) aparecen **descuadrados verticalmente**:

1. **Causa 1 — Salto de línea huérfano del asterisco `*` en etiquetas largas dentro de `.form-row-2col`:**
   - En `BOOTSTRAP` (`vue3/src/views/LoginView.vue`, líneas 634–637), la etiqueta izquierda dice:
     ```html
     <label for="bootstrap-admin-pass" class="form-label">
       Contraseña Segura (Mínimo 15 caracteres)
       <span class="required" aria-hidden="true">*</span>
     </label>
     ```
     Dentro de `.login-card--wide` (`max-width: 540px`, columna útil de `~234px`), el texto `"Contraseña Segura (Mínimo 15 caracteres)"` ocupa prácticamente el 100% del ancho de la columna, provocando que el asterisco `<span class="required">*</span>` salte **solo y huérfano** a una segunda línea, mientras que la etiqueta derecha (`Confirmar Contraseña *`) permanece en 1 sola línea.
   - De igual forma, en `REGISTER` (`vue3/src/views/LoginView.vue`, líneas 857–869), dentro de `.label-row` conviven `"Contraseña (Mínimo 8 caracteres) *"` y el botón `Mostrar`, desbordando el ancho de 1 línea en la columna izquierda.

2. **Causa 2 — Falta de anclaje inferior (`margin-top: auto`) en `.form-input` dentro de `.form-row-2col > .form-group`:**
   - Aunque `.form-row-2col` es un CSS Grid donde ambas celdas `.form-group` se estiran a la misma altura (`align-items: stretch`), `.form-group` usa `display: flex; flex-direction: column; gap: var(--rg-space-1, 4px)` sin `justify-content: space-between` ni `margin-top: auto` en `.form-input`.
   - En consecuencia, cuando la etiqueta de la izquierda ocupa 2 líneas y la de la derecha ocupa 1 línea, el `<input id="bootstrap-admin-pass">` queda empujado ~20px más abajo que `<input id="bootstrap-admin-pass-confirm">`, rompiendo la alineación horizontal de la fila.

---

## 2. Solución Arquitectónica Paso a Paso (Lista para Implementar)

### Paso 1: Concisar Etiquetas de Contraseña en `BOOTSTRAP` y `REGISTER` (`vue3/src/views/LoginView.vue`)

1. En `vue3/src/views/LoginView.vue` (alrededor de las líneas **632–665**), reemplazar la fila `.form-row-2col` de contraseñas del formulario `BOOTSTRAP` por:
   ```html
        <div class="form-row-2col">
          <div class="form-group">
            <label for="bootstrap-admin-pass" class="form-label">
              Contraseña (Mín. 15 caracteres)&nbsp;<span class="required" aria-hidden="true">*</span>
            </label>
            <input
              id="bootstrap-admin-pass"
              v-model="bootstrapAdminPassword"
              type="password"
              required
              autocomplete="new-password"
              placeholder="••••••••••••"
              class="form-input"
              :disabled="isLoading"
            />
          </div>

          <div class="form-group">
            <label for="bootstrap-admin-pass-confirm" class="form-label">
              Confirmar Contraseña&nbsp;<span class="required" aria-hidden="true">*</span>
            </label>
            <input
              id="bootstrap-admin-pass-confirm"
              v-model="bootstrapAdminPasswordConfirm"
              type="password"
              required
              autocomplete="new-password"
              placeholder="••••••••••••"
              class="form-input"
              :disabled="isLoading"
            />
          </div>
        </div>
   ```

2. En `vue3/src/views/LoginView.vue` (alrededor de las líneas **855–897**), reemplazar la fila `.form-row-2col` de contraseñas del formulario `REGISTER` por:
   ```html
        <div class="form-row-2col">
          <div class="form-group">
            <div class="label-row">
              <label for="reg-password" class="form-label">
                Contraseña (Mín. 8 caract.)&nbsp;<span class="required" aria-hidden="true">*</span>
              </label>
              <button
                type="button"
                class="btn-toggle-visibility"
                :aria-label="showRegisterPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
                @click="showRegisterPassword = !showRegisterPassword"
              >
                {{ showRegisterPassword ? 'Ocultar' : 'Mostrar' }}
              </button>
            </div>
            <input
              id="reg-password"
              v-model="registerPassword"
              :type="showRegisterPassword ? 'text' : 'password'"
              required
              autocomplete="new-password"
              placeholder="••••••••••••"
              class="form-input"
              :disabled="isLoading"
            />
          </div>

          <div class="form-group">
            <label for="reg-password-confirm" class="form-label">
              Confirmar Contraseña&nbsp;<span class="required" aria-hidden="true">*</span>
            </label>
            <input
              id="reg-password-confirm"
              v-model="registerPasswordConfirm"
              :type="showRegisterPassword ? 'text' : 'password'"
              required
              autocomplete="new-password"
              placeholder="••••••••••••"
              class="form-input"
              :disabled="isLoading"
            />
          </div>
        </div>
   ```

---

### Paso 2: Blindar Alineación Horizontal de Inputs en `.form-row-2col` y Ampliar `.login-card--wide` (`vue3/src/views/LoginView.vue`)

En la sección `<style scoped>` de `vue3/src/views/LoginView.vue` (alrededor de las líneas **1137–1152** y **1270–1305**), actualizar las reglas de `.login-card--wide`, `.form-row-2col`, `.form-group`, `.label-row` y `.form-input`:

```css
  .login-card--wide {
    max-width: 580px;
  }

  .form-row-2col {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--rg-space-3, 12px);
    align-items: stretch;
  }

  .form-row-2col > .form-group {
    justify-content: space-between;
  }

  .form-row-2col .form-input {
    margin-top: auto;
  }

  @media (max-width: 540px) {
    .form-row-2col {
      grid-template-columns: 1fr;
    }
  }
```

Y asegurar en `.label-row`, `.form-label` y `.btn-toggle-visibility`:

```css
  .label-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 6px;
  }

  .form-label {
    font-size: 0.85rem;
    font-weight: 600;
    line-height: 1.3;
    color: var(--rg-text-secondary, #cbd5e1);
  }

  .btn-toggle-visibility {
    background: transparent;
    border: none;
    color: var(--rg-accent-cyan, #22d3ee);
    font-size: 0.75rem;
    line-height: 1.3;
    cursor: pointer;
    padding: 0;
    flex-shrink: 0;
    white-space: nowrap;
  }
```

> **Por qué funciona al 100%:**
> 1. Con `max-width: 580px` en `.login-card--wide` y el texto conciso `"Contraseña (Mín. 15 caracteres)\u00a0*"`, la etiqueta cabe holgadamente en **1 sola línea** y el espacio de no-separación (`&nbsp;`) impide que el asterisco `*` salte jamás en solitario a una nueva línea.
> 2. Con `.form-row-2col > .form-group { justify-content: space-between }` y `.form-row-2col .form-input { margin-top: auto }`, ambos `<input>` de cada fila de 2 columnas quedan anclados exactamente al borde inferior de la celda del Grid, garantizando alineación horizontal perfecta incluso bajo zoom del navegador o fuentes personalizadas.

---

## 3. Aseguramiento de Calidad Obligatorio Level-11X (Pruebas Unitarias + Karate Labs BDD)

### 3.1 Prueba Unitaria Frontend en `vue3/src/views/auth/loginView.unit.ts`

Actualizar o añadir el caso de prueba en `vue3/src/views/auth/loginView.unit.ts` verificando que las etiquetas de contraseña en `BOOTSTRAP` y `REGISTER` usan el formato compacto con espacio indivisible (`\u00a0*`) y están pareadas dentro de `.form-row-2col`:

```typescript
  it('alinea simétricamente los campos de contraseña en .form-row-2col con etiquetas compactas sin asterisco huérfano (Spec 112)', async () => {
    vi.spyOn(http, 'get').mockResolvedValueOnce({
      status: 200,
      data: { is_bootstrapped: false },
      headers: new Headers(),
    });

    const wrapper = mount(LoginView);
    await flushPromises();

    const passLabel = wrapper.find('label[for="bootstrap-admin-pass"]');
    const confirmLabel = wrapper.find('label[for="bootstrap-admin-pass-confirm"]');
    expect(passLabel.exists()).toBe(true);
    expect(confirmLabel.exists()).toBe(true);
    expect(passLabel.text()).toContain('Contraseña (Mín. 15 caracteres)');
    expect(confirmLabel.text()).toContain('Confirmar Contraseña');

    // Ambos inputs deben compartir el mismo contenedor .form-row-2col
    const rows = wrapper.findAll('.form-row-2col');
    const passRow = rows.find(
      (r) =>
        r.find('#bootstrap-admin-pass').exists() &&
        r.find('#bootstrap-admin-pass-confirm').exists(),
    );
    expect(passRow).toBeDefined();
  });
```

### 3.2 Escenario Karate Labs BDD (UI) en `vue3/test/ui_business_flow.feature` (+ réplica en `docs/examples/vue3/test/ui_business_flow.feature`)

Añadir el **Escenario 126** al final de `vue3/test/ui_business_flow.feature` y replicarlo idénticamente en `docs/examples/vue3/test/ui_business_flow.feature`:

```gherkin
  # ============================================================================
  # SPEC 112: ALINEACIÓN SIMÉTRICA DE CAMPOS DE CLAVE EN .form-row-2col (LOGIN)
  # ============================================================================
  Scenario: 126. Alineacion horizontal simetrica de campos de clave en filas de 2 columnas y etiquetas de 1 linea sin asterisco huerfano en LoginView (Spec 112)
    * def loginPasswordRowAlignment = { card_wide_max_width_580: true, input_margin_top_auto: true, single_line_password_label: true, non_breaking_required_asterisk: true }
    * assert loginPasswordRowAlignment.card_wide_max_width_580 == true
    * assert loginPasswordRowAlignment.input_margin_top_auto == true
    * assert loginPasswordRowAlignment.single_line_password_label == true
    * assert loginPasswordRowAlignment.non_breaking_required_asterisk == true
```

---

## 4. Comandos de Verificación en Contenedor Efímero Docker (Regla Cero)

```bash
# 1. Ejecutar prueba unitaria de LoginView en contenedor efímero
docker compose -f docker-compose.qa.yml run --rm --no-deps qa-frontend \
  pnpm exec vitest run src/views/auth/loginView.unit.ts

# 2. Verificar tipado estricto TypeScript
docker compose -f docker-compose.qa.yml run --rm --no-deps qa-frontend \
  pnpm exec vue-tsc --noEmit

# 3. Ejecutar gate integral de certificación 9/9
./.agents/scripts/certify_task_completion.sh
```
