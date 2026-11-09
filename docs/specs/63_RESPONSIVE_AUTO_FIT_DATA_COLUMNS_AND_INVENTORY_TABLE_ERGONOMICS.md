# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

# Especificación 63: Columnas Auto-Ajustables al Contenido (*Content-Hugging*) en `RgDataTable.vue` y Ergonomía Responsiva de la Tabla de Inventario (Hito 28.8)

**Estado:** ✅ Completado y Certificado al 100% en Hito 28  
**Hito Asociado:** Hito 28.8 (`ROADMAP.md`)  
**Fecha de Certificación:** Noviembre 2026  
**Módulos Afectados:**
- `vue3/src/components/common/RgDataTable.vue`
- `vue3/src/views/RouterInventoryView.vue`
- `vue3/src/locales/es.json`
- `vue3/src/locales/en.json`
- `vue3/src/views/inventory/routerInventoryView.unit.ts`

---

## 1. Diagnóstico Causa Raíz (Hallazgo UAT en `/inventory`)

En `http://localhost:8085/inventory` (**Inventario de Equipos**), las columnas previas a la botonera de `Acciones` (`Flags`, `Nombre / Identity`, `Rol de Red`, `Dirección IP / Puerto`, `Modelo y Arquitectura`, `Serial`, `RouterOS`, `Syslog`, `SSL TOFU`, `Estado`) desperdiciaban espacio horizontal y quedaban parcialmente ocultas detrás de la columna fija (`position: sticky; right: 0`) de **`Acciones`**:

1. **Ausencia de *Content-Hugging* (`width: 1%`) en las columnas de datos de `RgDataTable.vue`:**
   - Al tener `.rg-table { width: 100% }` sin `width: 1%; white-space: nowrap;` en las celdas de datos (`th` / `td.rg-data`), el navegador distribuye ancho sobrante entre las columnas de datos en lugar de ceñir cada columna desde `Flags` hasta `Estado` a la longitud real de su contenido y dejar que solo la columna final (`Acciones`) absorba el resto.
   - Además, `.col-flags` tenía `width: 65px; min-width: 65px;` fijos cuando `[R]` solo requiere `34px`.
2. **Cabeceras de columna mucho más anchas que sus valores (`es.json` / `en.json`):**
   - `Nombre / Identity` (17 caracteres) inflaba una columna cuyos valores son `r1`–`r6` o `caps1` (2–5 caracteres).
   - `Dirección IP / Puerto` (21 caracteres) inflaba una columna cuyos valores son `10.250.3.8`.
   - `Modelo y Arquitectura` (21 caracteres) junto con el string completo de QEMU (`"CHR QEMU Standard PC (i440FX + PIIX, 1996) (x86_64)"`) ocupaba `240px` por fila.

---

## 2. Solución Arquitectónica e Instrucciones Exactas (`Target` / `Replacement`)

### 2.1. Ceñido Automático al Contenido (*Auto-Fit / Content-Hugging*) en `vue3/src/components/common/RgDataTable.vue`

Hacer que todas las columnas de datos antes de los botones (`thead th:not(.col-custom-actions)` y `td.rg-data`) se ajusten exactamente al ancho de su contenido (`width: 1%; white-space: nowrap;`), reduciendo `.col-flags` a `34px` y compactando el padding horizontal en densidad compacta a `2px 6px`.

#### Bloque `Target` en `vue3/src/components/common/RgDataTable.vue` (líneas 500–560):
```css
  td.rg-data {
    max-width: 240px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .num-col {
    font-variant-numeric: tabular-nums lining-nums;
  }

  /* Densidad Compacta (32px WinBox) */
  .rg-density-compact th,
  .rg-density-compact td {
    height: 32px;
    padding: 2px 8px;
    border-right: 1px solid var(--rg-border-grid);
    border-bottom: 1px solid var(--rg-border-grid);
  }

  /* Densidad Cómoda (44px Táctil) */
  .rg-density-comfortable th,
  .rg-density-comfortable td {
    height: 44px;
    padding: 8px 12px;
    border-bottom: 1px solid var(--rg-border-grid);
  }

  thead th {
    position: sticky;
    top: 0;
    background: var(--rg-bg-elevated);
    color: var(--rg-text-secondary);
    font-weight: 600;
    font-size: var(--rg-text-xs, 0.75rem);
    text-align: left;
    white-space: nowrap;
    z-index: 10;
    user-select: none;
  }

  .rg-table-row {
    cursor: pointer;
    transition: background-color 0.15s ease;
  }

  .rg-table-row:hover {
    background-color: var(--rg-bg-elevated);
  }

  .col-flags {
    width: 65px;
    min-width: 65px;
    text-align: center;
  }
```

#### Bloque `Replacement` en `vue3/src/components/common/RgDataTable.vue`:
```css
  thead th:not(.col-custom-actions),
  td.rg-data {
    width: 1%;
    max-width: 210px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .num-col {
    font-variant-numeric: tabular-nums lining-nums;
  }

  /* Densidad Compacta (32px WinBox) */
  .rg-density-compact th,
  .rg-density-compact td {
    height: 32px;
    padding: 2px 6px;
    border-right: 1px solid var(--rg-border-grid);
    border-bottom: 1px solid var(--rg-border-grid);
  }

  /* Densidad Cómoda (44px Táctil) */
  .rg-density-comfortable th,
  .rg-density-comfortable td {
    height: 44px;
    padding: 6px 10px;
    border-bottom: 1px solid var(--rg-border-grid);
  }

  thead th {
    position: sticky;
    top: 0;
    background: var(--rg-bg-elevated);
    color: var(--rg-text-secondary);
    font-weight: 600;
    font-size: var(--rg-text-xs, 0.75rem);
    text-align: left;
    white-space: nowrap;
    z-index: 10;
    user-select: none;
  }

  .rg-table-row {
    cursor: pointer;
    transition: background-color 0.15s ease;
  }

  .rg-table-row:hover {
    background-color: var(--rg-bg-elevated);
  }

  .col-flags {
    width: 1%;
    min-width: 34px;
    white-space: nowrap;
    text-align: center;
  }
```

---

### 2.2. Normalización Compacta de Modelo Hardware (`CHR QEMU`) y Botonera en `vue3/src/views/RouterInventoryView.vue`

Acortar la representación en celda de `"CHR QEMU Standard PC (i440FX + PIIX, 1996)"` a `"CHR QEMU"` (conservando la arquitectura `"(x86_64)"`) y compactar el espaciado entre botones de fila.

#### Primer Bloque `Target` en `vue3/src/views/RouterInventoryView.vue` (líneas 103–113):
```typescript
    {
      key: 'hardware',
      label: t('inventory.col_hardware'),
      formatter: (row: Record<string, unknown>) => {
        const r = row as unknown as RouterItem;
        const model = r.model || (r as any).model_name || r.board_name || 'CHR';
        const arch = r.architecture_name ? ` (${r.architecture_name})` : '';
        return `${model}${arch}`;
      },
    },
```

#### Primer Bloque `Replacement` en `vue3/src/views/RouterInventoryView.vue`:
```typescript
    {
      key: 'hardware',
      label: t('inventory.col_hardware'),
      formatter: (row: Record<string, unknown>) => {
        const r = row as unknown as RouterItem;
        const rawModel = String(r.model || (r as any).model_name || r.board_name || 'CHR').trim();
        const compactModel = rawModel.replace(
          /QEMU Standard PC\s*\([^)]*\)/i,
          'QEMU',
        );
        const arch = r.architecture_name ? ` (${r.architecture_name})` : '';
        return `${compactModel}${arch}`;
      },
    },
```

#### Segundo Bloque `Target` en `vue3/src/views/RouterInventoryView.vue` (líneas 817–832):
```css
  .table-row-actions {
    display: flex;
    gap: var(--rg-space-1, 4px);
  }

  .btn-row-action {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 3px 8px;
    border-radius: var(--rg-radius-sm, 4px);
    font-size: var(--rg-text-2xs, 0.6875rem);
    cursor: pointer;
    transition: all 0.15s ease;
  }
```

#### Segundo Bloque `Replacement` en `vue3/src/views/RouterInventoryView.vue`:
```css
  .table-row-actions {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    white-space: nowrap;
  }

  .btn-row-action {
    background: transparent;
    border: 1px solid var(--rg-border-grid, #1e293b);
    color: var(--rg-text-secondary, #cbd5e1);
    padding: 2px 6px;
    border-radius: var(--rg-radius-sm, 4px);
    font-size: var(--rg-text-2xs, 0.6875rem);
    white-space: nowrap;
    cursor: pointer;
    transition: all 0.15s ease;
  }
```

---

### 2.3. Cabeceras Concisas de Columnas en `vue3/src/locales/es.json` y `vue3/src/locales/en.json`

Acortar las etiquetas de cabecera en `inventory` para que las columnas con datos breves (`caps1`, `r1`, `10.250.3.8`) se ajusten exactamente al ancho de su contenido.

#### Bloque `Target` en `vue3/src/locales/es.json` (líneas 387–397 y 422–423):
```json
    "col_flags": "Flags",
    "col_name": "Nombre / Identity",
    "col_role": "Rol de Red",
    "col_ip": "Dirección IP / Puerto",
    "col_hardware": "Modelo y Arquitectura",
    "col_serial": "Serial",
    "col_routeros": "RouterOS",
    "col_syslog": "Syslog",
    "col_ssl_tofu": "SSL TOFU",
    "col_state": "Estado",
    "col_actions": "Acciones",
```

#### Bloque `Replacement` en `vue3/src/locales/es.json`:
```json
    "col_flags": "Flags",
    "col_name": "Identity",
    "col_role": "Rol",
    "col_ip": "IP / Puerto",
    "col_hardware": "Modelo",
    "col_serial": "Serial",
    "col_routeros": "RouterOS",
    "col_syslog": "Syslog",
    "col_ssl_tofu": "SSL TOFU",
    "col_state": "Estado",
    "col_actions": "Acciones",
```

#### Bloque `Target` en `vue3/src/locales/en.json` (líneas 387–397):
```json
    "col_flags": "Flags",
    "col_name": "Name / Identity",
    "col_role": "Network Role",
    "col_ip": "IP Address / Port",
    "col_hardware": "Model & Architecture",
    "col_serial": "Serial",
    "col_routeros": "RouterOS",
    "col_syslog": "Syslog",
    "col_ssl_tofu": "SSL TOFU",
    "col_state": "State",
    "col_actions": "Actions",
```

#### Bloque `Replacement` en `vue3/src/locales/en.json`:
```json
    "col_flags": "Flags",
    "col_name": "Identity",
    "col_role": "Role",
    "col_ip": "IP / Port",
    "col_hardware": "Model",
    "col_serial": "Serial",
    "col_routeros": "RouterOS",
    "col_syslog": "Syslog",
    "col_ssl_tofu": "SSL TOFU",
    "col_state": "State",
    "col_actions": "Actions",
```

---

## 3. Pruebas Unitarias e Invariantes 11X (`vue3/src/views/inventory/routerInventoryView.unit.ts`)

Agregar verificación en `routerInventoryView.unit.ts` para comprobar que el formateador de `hardware` compacta `"CHR QEMU Standard PC (i440FX + PIIX, 1996)"` a `"CHR QEMU (x86_64)"`.

#### Bloque `Target` en `vue3/src/views/inventory/routerInventoryView.unit.ts` (líneas 291–303):
```typescript
    const dt = wrapper.findComponent({ name: 'RgDataTable' });
    const cols = dt.props('columns') as Array<{ key: string; formatter?: (row: Record<string, unknown>) => string }>;
    const sslCol = cols.find((c) => c.key === 'ssl_trust_status');
    expect(sslCol).toBeDefined();
    expect(sslCol?.formatter).toBeDefined();

    const formattedPending = sslCol!.formatter!({ ssl_trust_status: 'PENDING_TOFU' });
    expect(formattedPending).toBe('Pendiente TOFU');

    const formattedPinned = sslCol!.formatter!({ ssl_trust_status: 'TRUSTED_PINNED' });
    expect(formattedPinned).toBe('Certificado Válido (Pinned)');
  });
```

#### Bloque `Replacement` en `vue3/src/views/inventory/routerInventoryView.unit.ts`:
```typescript
    const dt = wrapper.findComponent({ name: 'RgDataTable' });
    const cols = dt.props('columns') as Array<{ key: string; formatter?: (row: Record<string, unknown>) => string }>;
    const sslCol = cols.find((c) => c.key === 'ssl_trust_status');
    expect(sslCol).toBeDefined();
    expect(sslCol?.formatter).toBeDefined();

    const formattedPending = sslCol!.formatter!({ ssl_trust_status: 'PENDING_TOFU' });
    expect(formattedPending).toBe('Pendiente TOFU');

    const formattedPinned = sslCol!.formatter!({ ssl_trust_status: 'TRUSTED_PINNED' });
    expect(formattedPinned).toBe('Certificado Válido (Pinned)');

    const hwCol = cols.find((c) => c.key === 'hardware');
    expect(hwCol?.formatter).toBeDefined();
    expect(
      hwCol!.formatter!({
        model: 'CHR QEMU Standard PC (i440FX + PIIX, 1996)',
        architecture_name: 'x86_64',
      }),
    ).toBe('CHR QEMU (x86_64)');
  });
```
