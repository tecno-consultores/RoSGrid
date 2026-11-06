# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 86: Plantilla Golden Config para Configuración Masiva de Huso Horario del Sistema (`HUSO_HORARIO_SISTEMA` — `/system/clock`) y Soporte Dinámico de Variables `select` en Acciones Masivas

**Estado:** Completado y Certificado en Docker (Hito 30.9)  
**Hito Asociado:** Hito 30.9  
**Motor de Ejecución Objetivo:** Gemini 3.8 Flash (High)  
**Archivos Afectados:**
- `fastapi/src/api/v1/bulk_and_updates.py`
- `vue3/src/views/BulkOperationsAndUpdatesView.vue`
- `vue3/src/locales/es.json`
- `vue3/src/locales/en.json`
- `fastapi/tests/api/test_smart_os_firmware_update_chr.unit.py`
- `vue3/src/views/operationsViews.unit.ts`
- `fastapi/test/api_test.feature` (+ réplica en `docs/examples/fastapi/api_test.feature.example`)
- `vue3/test/ui_business_flow.feature` (+ réplica en `docs/examples/vue3/ui_business_flow.feature.example`)

---

## 1. Contexto Operativo y Fundamentación Oficial MikroTik RouterOS v7

En despliegues multi-router (ISP / Enterprise), homologar el huso horario (`time-zone-name`) de toda la flota MikroTik RouterOS v7 es indispensable para que:
1. Las marcas de tiempo locales de `/log` y Syslog BSD (`system,info`, `account`, `firewall,info`, `pppoe,ppp`) coincidan con la hora oficial del NOC y de la Consola Forense WORM.
2. Las tareas programadas en `/system/scheduler` y las colas o reglas basadas en tiempo se ejecuten a la hora esperada.

### 1.1 Mecánica del Menú Singleton `/system/clock` en RouterOS v7 REST API
- En MikroTik RouterOS v7, `/system/clock` es un **menú singleton** (no admite creación de filas con `PUT`, sino modificación de parámetros globales mediante `POST /rest/system/clock/set`).
- **Trampa Operativa de `time-zone-autodetect`:** En RouterOS v7, si la propiedad `time-zone-autodetect` está activa (`yes`), el servicio MikroTik IP Cloud puede sobrescribir automáticamente `time-zone-name` según la geolocalización de la IP pública de salida (lo cual falla frecuentemente cuando el ISP usa tránsito internacional o prefijos arrendados). Por ello, para fijar el huso horario de manera determinista se debe enviar simultáneamente:
  - `time-zone-autodetect`: `"no"` (valor por defecto recomendado, parametrizable a `"yes"`).
  - `time-zone-name`: Nombre IANA estándar soportado por RouterOS v7 (ej. `"America/Caracas"`, `"America/Bogota"`, `"America/Lima"`, `"America/Santiago"`, `"America/Argentina/Buenos_Aires"`, `"America/Mexico_City"`, `"America/New_York"`, `"Europe/Madrid"`, `"UTC"`, o `"manual"`).
- **Comando CLI equivalente:**
  ```routeros
  /system clock set time-zone-autodetect={{ time_zone_autodetect }} time-zone-name={{ time_zone_name }}
  ```
- **Invocación REST API RouterOS v7:**
  - Método: `POST`
  - Endpoint: `/rest/system/clock/set`
  - Payload JSON:
    ```json
    {
      "time-zone-autodetect": "{{ time_zone_autodetect }}",
      "time-zone-name": "{{ time_zone_name }}"
    }
    ```

---

## 2. Instrucciones Paso a Paso para Implementación (Gemini 3.8 Flash High)

### Paso 1: Backend — Registro de `system/clock` en `singleton_menus` y Plantilla #17 `HUSO_HORARIO_SISTEMA` (`fastapi/src/api/v1/bulk_and_updates.py`)

#### 1.A. Añadir `"system/clock"` a la tupla `singleton_menus` en `_execute_single_step`
En `fastapi/src/api/v1/bulk_and_updates.py` (alrededor de la línea 1389, dentro de `async def _execute_single_step`), incluir `"system/clock"` dentro de `singleton_menus` para garantizar que cualquier invocación `PATCH system/clock` o `POST system/clock/set` se enrute siempre como `POST /rest/system/clock/set`:

```python
    singleton_menus = (
        "system/ntp/client",
        "system/clock",
        "ip/dns",
        "snmp",
        "ip/settings",
        "system/identity",
        "system/note",
        "system/package/update",
        "system/routerboard/settings",
        "interface/ovpn-server/server",
        "interface/sstp-server/server",
        "interface/l2tp-server/server",
        "interface/pptp-server/server",
    )
```

#### 1.B. Incorporar la plantilla #17 `HUSO_HORARIO_SISTEMA` en `_DEFAULT_STARTER_TEMPLATES`
En `fastapi/src/api/v1/bulk_and_updates.py` (al final de la lista `_DEFAULT_STARTER_TEMPLATES`, justo después de la plantilla #16 `SEGURIDAD_L2_DHCP_SNOOPING_Y_OPTION82`, alrededor de la línea 1054), agregar el bloque:

```python
    # 17. Huso Horario del Sistema (/system/clock)
    {
        "name": "HUSO_HORARIO_SISTEMA",
        "category": "SYSTEM",
        "description": (
            "Configura el huso horario oficial IANA del sistema (/system/clock) en toda la flota "
            "MikroTik RouterOS v7 y ajusta la autodetección por IP Cloud (time-zone-autodetect) "
            "para garantizar marcas de tiempo exactas en Syslog y auditoría WORM."
        ),
        "requires_safemode": True,
        "variables_schema": [
            {
                "key": "time_zone_name",
                "label": "Huso Horario IANA (time-zone-name)",
                "default_val": "America/Caracas",
                "required": True,
                "var_type": "select",
                "options": [
                    "America/Caracas",
                    "America/Bogota",
                    "America/Lima",
                    "America/Guayaquil",
                    "America/La_Paz",
                    "America/Santiago",
                    "America/Argentina/Buenos_Aires",
                    "America/Asuncion",
                    "America/Montevideo",
                    "America/Sao_Paulo",
                    "America/Panama",
                    "America/Costa_Rica",
                    "America/Guatemala",
                    "America/Santo_Domingo",
                    "America/Mexico_City",
                    "America/New_York",
                    "America/Chicago",
                    "America/Los_Angeles",
                    "Europe/Madrid",
                    "UTC",
                ],
            },
            {
                "key": "time_zone_autodetect",
                "label": "Autodetección de Zona Horaria por Cloud (yes / no)",
                "default_val": "no",
                "required": True,
                "var_type": "select",
                "options": ["no", "yes"],
            },
        ],
        "rest_steps_template": [
            {
                "method": "POST",
                "endpoint": "system/clock/set",
                "payload": {
                    "time-zone-autodetect": "{{ time_zone_autodetect }}",
                    "time-zone-name": "{{ time_zone_name }}",
                },
                "cli_command": (
                    "/system clock set time-zone-autodetect={{ time_zone_autodetect }} "
                    "time-zone-name={{ time_zone_name }}"
                ),
            },
        ],
    },
```

---

### Paso 2: Frontend — Mapeo de Catálogo, Previsualización CLI y Selector Dinámico `var_type === 'select'` (`vue3/src/views/BulkOperationsAndUpdatesView.vue`)

#### 2.A. Ampliar la interfaz `ConfigTemplate['variables_schema']`
En `vue3/src/views/BulkOperationsAndUpdatesView.vue` (alrededor de las líneas 38–48), añadir `var_type?: string` y `options?: string[]` a la definición de elementos en `variables_schema`:

```typescript
  interface ConfigTemplate {
    id: string;
    name: string;
    category: string;
    description: string;
    requires_safemode: boolean;
    variables_schema: Array<{
      key: string;
      label: string;
      default_val?: string;
      required?: boolean;
      var_type?: string;
      options?: string[];
    }>;
    rest_steps_template: Array<Record<string, unknown>>;
  }
```

#### 2.B. Registrar `HUSO_HORARIO_SISTEMA` en `getTemplateKey` y `FALLBACK_COMMAND_MAP`
1. En `getTemplateKey(name: string)` (alrededor de la línea 294 de `vue3/src/views/BulkOperationsAndUpdatesView.vue`), añadir:
   ```typescript
      ACTUALIZACION_ROUTEROS_Y_FIRMWARE: 'actualizacion_routeros_y_firmware',
      SEGURIDAD_L2_DHCP_SNOOPING_Y_OPTION82: 'seguridad_l2_dhcp_snooping_y_option82',
      HUSO_HORARIO_SISTEMA: 'huso_horario_sistema',
   ```
2. En `FALLBACK_COMMAND_MAP` (alrededor de la línea 354 de `vue3/src/views/BulkOperationsAndUpdatesView.vue`), añadir el soporte de respaldo para `system/clock`:
   ```typescript
    ['system/clock:PATCH', (p) => `/system clock set ${p}`],
    ['system/clock/set:POST', (p) => `/system clock set ${p}`],
   ```

#### 2.C. Renderizar `<select>` dinámico para cualquier variable con `v.var_type === 'select' && v.options?.length`
En el Paso 2 de `vue3/src/views/BulkOperationsAndUpdatesView.vue` (dentro de `.vars-grid`, alrededor de las líneas 1015–1048), añadir una rama `v-else-if="v.var_type === 'select' && Array.isArray(v.options) && v.options.length > 0"` antes del `<input v-else ... />` final:

```vue
              <select
                v-else-if="v.var_type === 'select' && Array.isArray(v.options) && v.options.length > 0"
                :id="'tpl-var-' + v.key"
                v-model="templateVars[v.key]"
                class="form-input"
                @change="generatePreview"
              >
                <option v-for="opt in v.options" :key="opt" :value="opt">
                  {{ opt }}
                </option>
              </select>

              <input
                v-else
                :id="'tpl-var-' + v.key"
                v-model="templateVars[v.key]"
                type="text"
                class="form-input font-mono"
                @input="generatePreview"
              />
```

---

### Paso 3: Internacionalización Bilingüe (`vue3/src/locales/es.json` y `vue3/src/locales/en.json`)

1. En `vue3/src/locales/es.json`, dentro de `"template_catalog"` (alrededor de la línea 1194), añadir:
   ```json
    "huso_horario_sistema": {
      "name": "Huso Horario del Sistema (/system/clock)",
      "description": "Configura el huso horario oficial IANA del sistema (/system/clock) en toda la flota MikroTik RouterOS v7 y ajusta la autodetección por IP Cloud para garantizar marcas de tiempo exactas en Syslog y auditoría WORM."
    }
   ```
2. En `vue3/src/locales/en.json`, dentro de `"template_catalog"` (alrededor de la línea 1194), añadir:
   ```json
    "huso_horario_sistema": {
      "name": "System Clock & IANA Timezone (/system/clock)",
      "description": "Configures the official IANA system timezone (/system/clock) across the MikroTik RouterOS v7 fleet and controls IP Cloud time-zone-autodetect for accurate Syslog and WORM audit timestamps."
    }
   ```

---

### Paso 4: Aseguramiento de Calidad Level-11X Obligatorio (Pytest, Vitest y Karate Labs BDD)

> **DIRECTIVA SUPREMA QA 11X PARA GEMINI 3.8 FLASH (HIGH):**  
> Ninguna implementación de esta especificación puede darse por concluida sin crear y ejecutar en contenedores Docker efímeros (`Regla Cero`) las siguientes 4 capas de pruebas exactas:

#### 4.A. Prueba Unitaria e Integración Backend (`fastapi/tests/api/test_smart_os_firmware_update_chr.unit.py`)
Al final de `fastapi/tests/api/test_smart_os_firmware_update_chr.unit.py` (después de la línea 410), agregar el siguiente test completo verificando esquema, renderizado de variables y enrutamiento singleton `POST system/clock/set`:

```python
@pytest.mark.asyncio
async def test_starter_template_17_system_clock_timezone_schema_and_execution() -> None:
    """Verifica la plantilla #17 HUSO_HORARIO_SISTEMA (/system/clock/set) y su ejecución REST."""
    from src.api.v1.bulk_and_updates import _execute_single_step, _render_template_steps

    tpl = next((t for t in _DEFAULT_STARTER_TEMPLATES if t["name"] == "HUSO_HORARIO_SISTEMA"), None)
    assert tpl is not None, "Plantilla HUSO_HORARIO_SISTEMA debe existir en _DEFAULT_STARTER_TEMPLATES"
    assert tpl["category"] == "SYSTEM"
    assert tpl["requires_safemode"] is True

    vars_by_key = {v["key"]: v for v in tpl["variables_schema"]}
    assert "time_zone_name" in vars_by_key
    assert vars_by_key["time_zone_name"]["default_val"] == "America/Caracas"
    assert vars_by_key["time_zone_name"]["var_type"] == "select"
    assert "America/Caracas" in vars_by_key["time_zone_name"]["options"]
    assert "UTC" in vars_by_key["time_zone_name"]["options"]

    assert "time_zone_autodetect" in vars_by_key
    assert vars_by_key["time_zone_autodetect"]["default_val"] == "no"
    assert vars_by_key["time_zone_autodetect"]["var_type"] == "select"
    assert vars_by_key["time_zone_autodetect"]["options"] == ["no", "yes"]

    rendered = _render_template_steps(
        tpl["rest_steps_template"],
        {"time_zone_name": "America/Caracas", "time_zone_autodetect": "no"},
    )
    assert len(rendered) == 1
    assert rendered[0]["method"] == "POST"
    assert rendered[0]["endpoint"] == "system/clock/set"
    assert rendered[0]["payload"] == {
        "time-zone-autodetect": "no",
        "time-zone-name": "America/Caracas",
    }

    client = AsyncMock()
    client.post = AsyncMock(return_value={"status": "ok"})
    router_chr = Router(
        id=uuid.uuid4(),
        display_name="caps1",
        board_name="CHR VMware",
    )

    summary = await _run_router_template_steps(
        client=client,
        router_obj=router_chr,
        rendered_steps=rendered,
        vars_dict={"time_zone_name": "America/Caracas", "time_zone_autodetect": "no"},
    )
    assert "POST /rest/system/clock/set -> OK" in summary
    client.post.assert_awaited_once_with(
        "system/clock/set",
        json={"time-zone-autodetect": "no", "time-zone-name": "America/Caracas"},
    )

    # Verificar que PATCH sobre el menú singleton 'system/clock' también se convierte a POST 'system/clock/set'
    client.post.reset_mock()
    await _execute_single_step(
        client,
        "PATCH",
        "system/clock",
        {"time-zone-name": "UTC"},
    )
    client.post.assert_awaited_once_with("system/clock/set", json={"time-zone-name": "UTC"})
```

#### 4.B. Prueba Unitaria Frontend (`vue3/src/views/operationsViews.unit.ts`)
Al final del bloque `describe` en `vue3/src/views/operationsViews.unit.ts` (antes del cierre `});` en la línea 1178), agregar la prueba que valida el selector `<select>` dinámico (`var_type: 'select'`) y la generación del comando CLI `/system clock set`:

```typescript
  it('BulkOperationsAndUpdatesView — plantilla HUSO_HORARIO_SISTEMA renderiza selectores dinámicos var_type=select y previsualización CLI (Hito 30.9)', async () => {
    vi.spyOn(http, 'get').mockImplementation(async (url: string) => {
      if (url.includes('/operations/templates')) {
        return {
          status: 200,
          data: [
            {
              id: 'tpl-tz',
              name: 'HUSO_HORARIO_SISTEMA',
              category: 'SYSTEM',
              description: 'Configura el huso horario oficial IANA del sistema (/system/clock)',
              requires_safemode: true,
              variables_schema: [
                {
                  key: 'time_zone_name',
                  label: 'Huso Horario IANA (time-zone-name)',
                  default_val: 'America/Caracas',
                  required: true,
                  var_type: 'select',
                  options: ['America/Caracas', 'America/Bogota', 'UTC'],
                },
                {
                  key: 'time_zone_autodetect',
                  label: 'Autodetección de Zona Horaria por Cloud (yes / no)',
                  default_val: 'no',
                  required: true,
                  var_type: 'select',
                  options: ['no', 'yes'],
                },
              ],
              rest_steps_template: [
                {
                  method: 'POST',
                  endpoint: 'system/clock/set',
                  payload: {
                    'time-zone-autodetect': '{{ time_zone_autodetect }}',
                    'time-zone-name': '{{ time_zone_name }}',
                  },
                  cli_command:
                    '/system clock set time-zone-autodetect={{ time_zone_autodetect }} time-zone-name={{ time_zone_name }}',
                },
              ],
            },
          ],
          headers: new Headers(),
        };
      }
      return { status: 200, data: [], headers: new Headers() };
    });

    const wrapper = mount(BulkOperationsAndUpdatesView);
    await flushPromises();

    // Ir al Paso 2 y seleccionar la plantilla HUSO_HORARIO_SISTEMA
    (wrapper.vm as any).wizardStep = 2;
    (wrapper.vm as any).onSelectTemplate('tpl-tz');
    await flushPromises();

    const tzSelect = wrapper.find('select#tpl-var-time_zone_name');
    const autoSelect = wrapper.find('select#tpl-var-time_zone_autodetect');
    expect(tzSelect.exists()).toBe(true);
    expect(autoSelect.exists()).toBe(true);
    expect((wrapper.vm as any).previewPayload).toContain(
      '/system clock set time-zone-autodetect=no time-zone-name=America/Caracas',
    );

    // Cambiar zona horaria a UTC y verificar reactividad del preview CLI
    await tzSelect.setValue('UTC');
    await tzSelect.trigger('change');
    await flushPromises();
    expect((wrapper.vm as any).previewPayload).toContain(
      '/system clock set time-zone-autodetect=no time-zone-name=UTC',
    );
  });
```

#### 4.C. Escenario 162 Karate Labs BDD API (`fastapi/test/api_test.feature` y `docs/examples/fastapi/api_test.feature.example`)
Al final de ambos archivos, añadir:

```gherkin
  Scenario: 162. Catálogo de Presets Golden Config e Inclusión de HUSO_HORARIO_SISTEMA (/system/clock/set) (Hito 30.9)
    Given path '/api/v1/operations/templates/presets'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }
```

#### 4.D. Escenario 100 Karate Labs BDD UI (`vue3/test/ui_business_flow.feature` y `docs/examples/vue3/ui_business_flow.feature.example`)
Al final de ambos archivos, añadir:

```gherkin
  Scenario: 100. Plantilla Golden Config de Huso Horario del Sistema (/system/clock) y Selectores Dinámicos var_type=select en Acciones Masivas (Hito 30.9)
    * def systemClockTemplateContract = { templateName: 'HUSO_HORARIO_SISTEMA', category: 'SYSTEM', endpoint: 'system/clock/set', method: 'POST', tzSelectId: '#tpl-var-time_zone_name', autodetectSelectId: '#tpl-var-time_zone_autodetect', defaultTz: 'America/Caracas', defaultAutodetect: 'no' }
    * match systemClockTemplateContract.templateName == 'HUSO_HORARIO_SISTEMA'
    * match systemClockTemplateContract.endpoint == 'system/clock/set'
    * match systemClockTemplateContract.method == 'POST'
    * match systemClockTemplateContract.tzSelectId == '#tpl-var-time_zone_name'
    * match systemClockTemplateContract.autodetectSelectId == '#tpl-var-time_zone_autodetect'
    * match systemClockTemplateContract.defaultTz == 'America/Caracas'
    * match systemClockTemplateContract.defaultAutodetect == 'no'
```

#### 4.E. Comandos de Verificación en Contenedores Docker Efímeros (`Regla Cero`)
Una vez aplicados los pasos 1 a 4, Gemini 3.8 Flash (High) deberá ejecutar:

```bash
# 1. Pruebas unitarias y tipado Backend en Docker efímero
docker compose -f docker-compose.qa.yml run --rm --entrypoint pytest api-test -q tests/api/test_smart_os_firmware_update_chr.unit.py tests/api/test_operations_endpoints_full.unit.py
docker compose -f docker-compose.qa.yml run --rm --entrypoint ruff api-test check src/api/v1/bulk_and_updates.py tests/api/test_smart_os_firmware_update_chr.unit.py

# 2. Pruebas unitarias y tipado Frontend en Docker efímero
docker compose -f docker-compose.qa.yml run --rm --entrypoint npx ui-test vitest run src/views/operationsViews.unit.ts
docker compose -f docker-compose.qa.yml run --rm --entrypoint npx ui-test vue-tsc --noEmit

# 3. Compuerta integral de certificación 9/9
./.agents/scripts/certify_task_completion.sh
```
