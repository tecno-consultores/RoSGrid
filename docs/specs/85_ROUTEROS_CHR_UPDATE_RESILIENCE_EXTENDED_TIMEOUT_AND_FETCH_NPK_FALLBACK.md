# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

# Especificación 85: Resiliencia de Actualización RouterOS v7 en CHR y RouterBOARD — Timeout Extendido (`180s`), Fallback `/tool/fetch` `.npk`, Tolerancia `/system/routerboard` y Verificación Real por Equipo en UI (Hito 30.8)

## 1. Diagnóstico Forense de Causa Raíz en Flota Real (`caps1` — RouterOS 7.25 CHR)

Durante las pruebas de aceptación en producción local sobre la flota real de 7 routers CHR (específicamente el equipo `caps1` en `10.250.3.20` ejecutando RouterOS `7.25`), la actualización desde `Acciones Masivas` presentó cuatro modos de fallo encadenados que las pruebas unitarias previas con `AsyncMock` instantáneo no detectaron:

1. **Aborto de Descarga `.npk` por Timeout Corto de `10.0s` (`MikrotikRestClient`):**
   - En RouterOS v7 REST API, el comando `POST /rest/system/package/update/install` descarga de forma síncrona el paquete `routeros-<ver>.npk` (~20.9 MB en `x86_64`) antes de reiniciar el router.
   - Al tener `MikrotikRestClient` un timeout fijo de `10.0s`, `httpx` cerraba el socket HTTP a los 10 segundos. RouterOS v7 interpreta el cierre de la conexión HTTP como la cancelación del comando `install`, abortando la descarga y dejando un archivo corrupto `downloads/routeros-7.25.1.npk` de `0 bytes`.
2. **Bloqueo del Actualizador Nativo en RouterOS `7.25` (`ERROR: bad HTTP response`):**
   - El corte abrupto de la descarga activa un bug conocido de RouterOS `7.25` (documentado oficialmente por MikroTik en el changelog de `7.25.1`: `*) fetch - fix HTTP fetch getting stuck in a "bad HTTP response" state;`), tras el cual `/system/package/update/check-for-updates` e `install` devuelven permanentemente `status: "ERROR: bad HTTP response"` con ` HTTP 200 OK`.
3. **Inexistencia del Menú `/rest/system/routerboard` en Equipos CHR Reales:**
   - En `_probe_single_router_update` (`bulk_and_updates.py`) y `get_live_status` (`webfig_system_tools.py`), se invocaba `await client.get("system/routerboard")` sin bloque `try/except` protector. En un CHR real (`x86_64`), dicho menú no existe y devuelve `HTTP 400 Bad Request: no such command or directory (routerboard)`, haciendo que el sondeo de actualizaciones cayera en el bloque `except` general y sobrescribiera el estado con `"Offline / Cache"`.
4. **Falso Positivo de Éxito en `BulkOperationsAndUpdatesView.vue`:**
   - El endpoint `POST /api/v1/operations/ros-updates/execute` responde con `HTTP 200 OK` y reporta el resultado individual de cada router dentro de `res.data.results[]` (`status: "UPGRADE_TRIGGERED"` vs `status: "FAILED"`). El componente `BulkOperationsAndUpdatesView.vue` no inspeccionaba `res.data.results[]`, mostrando un banner verde de éxito y actualizando `router.ros_version` en memoria aun cuando el router había devuelto `FAILED`.

---

## 2. Arquitectura de la Solución Implementada

### 2.1. Timeout Dinámico por Petición en `MikrotikRestClient` (`fastapi/src/mikrotik/client.py`)
- Se añadió el parámetro opcional `timeout: float | None = None` en `_raw_send`, `_execute_with_auth_fallback`, `request`, `get`, `put`, `patch`, `delete` y `post`.
- Operaciones estándar de telemetría mantienen el timeout ágil de `10.0s`, mientras que `system/package/update/check-for-updates` utiliza `timeout=30.0` y `system/package/update/install` / `tool/fetch` de paquetes `.npk` utilizan `timeout=180.0`.
- Si `install` cierra la conexión TCP o vence el timeout tras haber descargado el paquete porque el router inicia el `reboot`, se captura `(MikrotikConnectionError, MikrotikTimeoutError)` como `REBOOT_INITIATED_ON_INSTALL`.

### 2.2. Limpieza de `.npk` Corruptos y Fallback Directo vía `/tool/fetch` (`fastapi/src/api/v1/bulk_and_updates.py`)
- **`_cleanup_corrupted_npk_downloads(client)`:** Antes de iniciar una actualización, inspecciona `/rest/file` y elimina cualquier archivo `.npk` huérfano con `size == 0` (ej. `downloads/routeros-7.25.1.npk`).
- **`_fetch_latest_version_via_http_fallback(client, channel)`:** Cuando `/system/package/update` devuelve `ERROR:` o no reporta `latest-version`, consulta directamente `http://upgrade.mikrotik.com/routeros/NEWESTa7.<channel>` mediante `POST /rest/tool/fetch` (`output=user`) y extrae la versión publicada.
- **`_install_routeros_via_fetch_fallback(client, router_obj, target_version)`:** Cuando `/system/package/update/install` devuelve `status: "ERROR: bad HTTP response"` (bug de RouterOS `7.25`), resuelve el nombre del paquete según arquitectura (`routeros-<ver>.npk` para `x86_64`/CHR o `routeros-<ver>-<arch>.npk` para `arm64`, `arm`, `mmips`, `mipsbe`, `tile`, `smips`, `ppc`), lo descarga en la raíz del router mediante `POST /rest/tool/fetch` desde `http://upgrade.mikrotik.com/routeros/<ver>/<pkg>`, verifica en `/rest/file` que el tamaño sea `> 1 MB`, y dispara `POST /rest/system/reboot` para que RouterOS instale el paquete al arrancar.

### 2.3. Tolerancia a CHR en `/rest/system/routerboard`
- **`_probe_routerboard_safe(client, is_chr)`** en `bulk_and_updates.py` y **`_fetch_system_routerboard(client)`** en `webfig_system_tools.py` omiten o envuelven en `try/except` la consulta a `system/routerboard`, garantizando que ningún CHR falle con `HTTP 400: no such command or directory (routerboard)`.

### 2.4. Verificación Estricta de `results[]` en `BulkOperationsAndUpdatesView.vue`
- `triggerRosUpdate` y `triggerFleetPoeUpdate` inspeccionan el estado real por router en `res.data.results[]`.
- Si `itemResult.status !== 'UPGRADE_TRIGGERED'`, se presenta una alerta `.alert--error` (`⚠️ Error al actualizar ...`) y no se muta `router.ros_version` ni `router.upgraded_in_session`.
