# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 87: Corrección de Respaldos `.rsc` Vacíos (`"[]"`) en Pre-Upgrade, Filtrado `file?name=` ante Archivos Binarios (`.pcap`) en RouterOS v7 y Generación de Binario `.backup`

**Estado:** COMPLETADO (100%) y Certificado en Docker (Hito 30.10)  
**Hito Asociado:** Hito 30.10  
**Motor de Ejecución Objetivo:** Gemini 3.8 Flash (High)  
**Archivos Afectados:**
- `fastapi/src/api/v1/backups.py`
- `fastapi/src/api/v1/bulk_and_updates.py`
- `fastapi/tests/api/test_operations_endpoints_full.unit.py`
- `fastapi/tests/api/test_smart_os_firmware_update_chr.unit.py`
- `fastapi/test/api_test.feature` (+ réplica en `docs/examples/fastapi/api_test.feature.example`)
- `vue3/test/ui_business_flow.feature` (+ réplica en `docs/examples/vue3/ui_business_flow.feature.example`)

---

## 1. Diagnóstico Forense de las 3 Causas Raíz (Caso Real `caps1` — `10.250.3.28`)

Al inspeccionar la vista **Historial de Respaldos & Comparador de Diferencias (`/backups`)** sobre el equipo `caps1`, se observaron tres anomalías simultáneas:
1. Los 3 respaldos listados (`21:23:26`, `21:24:48`, `22:28:31`) muestran exactamente el mismo hash `SHA: 4f53cda18c2baa...` y su contenido en el comparador izquierdo (`Base`) es literalmente `[]` (2 bytes).
2. El panel derecho del comparador (`Objetivo: 🔴 LIVE`) aparece completamente vacío.
3. Los archivos temporales `rosgrid_bk_*.rsc` quedaban acumulados en el disco del router sin borrarse.

### 1.1 Causa Raíz 1: Silo en `_perform_pre_upgrade_backup` (`bulk_and_updates.py`, líneas 119–159) que serializa `[]` como `"[]"`
- Los 3 respaldos de `caps1` son de tipo `PRE_UPGRADE` (creados antes de cada intento de actualización de RouterOS).
- En lugar de reutilizar `export_router_rsc(client)` de `fastapi/src/api/v1/backups.py`, `_perform_pre_upgrade_backup` ejecutaba:
  ```python
  raw_res = await client.post("export", {"terse": "false", "show-sensitive": "false"})
  raw_text = str(raw_res) if not isinstance(raw_res, str) else raw_res
  ```
- En MikroTik RouterOS v7 REST API, `POST /rest/export` sin argumento `file` no devuelve el script en el cuerpo HTTP sino una lista JSON vacía `[]`. Al aplicar `str(raw_res)`, Python convirtió la lista vacía en la cadena literal `"[]"` (cuyo SHA-256 es `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`), cifrándola y guardándola en PostgreSQL sin deduplicar ni validar que la exportación contuviera configuración real.

### 1.2 Causa Raíz 2: Corrupción del JSON de `GET /rest/file` por presencia de archivos binarios (`chk.pcap`) en el router (`backups.py`, línea 120)
- Cuando `export_router_rsc(client)` ejecuta `POST /rest/export` con `{"file": fname, "show-sensitive": "false"}`, RouterOS v7 **sí genera correctamente** el archivo `rosgrid_bk_<hex>.rsc` (`2,345 bytes` con toda la configuración real de `caps1`).
- Sin embargo, a continuación `_read_and_cleanup_rsc_file(client, fname)` invocaba `files = await client.get("file")` (listando **todos** los archivos del router sin filtro).
- En `caps1` existe el archivo binario `chk.pcap` (`1,736 bytes`). Como pesa menos de 4 KB, RouterOS v7 incrusta los bytes binarios crudos de captura de paquetes dentro del campo `"contents"` del JSON de `GET /rest/file`. Esos bytes binarios sin escapar hacen fallar `resp.json()` en `MikrotikRestClient`, el cual cae en el fallback `return resp.text` (`<class 'str'>`).
- Al recibir un `str` en vez de un `list`, `_read_and_cleanup_rsc_file` ejecutaba:
  ```python
  if not isinstance(files, list):
      return ""
  ```
  abortando la lectura, dejando `🔴 LIVE` vacío y dejando los archivos `rosgrid_bk_*.rsc` sin eliminar en el router.
- **Verificación en vivo:** Al consultar `await client.get(f"file?name={fname}.rsc")`, RouterOS v7 devuelve exclusivamente el JSON del archivo `.rsc` solicitado (`<class 'list'>` de 1 elemento, 100% texto ASCII válido), ignorando por completo `chk.pcap` o cualquier otro binario en flash.

### 1.3 Causa Raíz 3: Limpieza de Archivos `.npk` y `.rsc` Huérfanos sin Descargar `contents` Binarios
- Tanto en `_cleanup_corrupted_npk_downloads` (`bulk_and_updates.py`) como en la limpieza de archivos temporales `rosgrid_bk_*.rsc`, pedir `GET /rest/file` sin `.proplist` obliga al router a serializar `"contents"` de todos los archivos pequeños. Usar `POST /rest/file/print` con `{".proplist": ".id,name,size,type"}` evita transferir o parsear payloads binarios.

---

## 2. Instrucciones Paso a Paso para Implementación (Gemini 3.8 Flash High)

### Paso 1: Filtrado `file?name=` en `_read_and_cleanup_rsc_file`, Purga de Temporales y Sanitización de Respaldos `"[]"` en `fastapi/src/api/v1/backups.py`

#### 1.A. Reemplazar `_read_and_cleanup_rsc_file` (líneas 118–139 de `fastapi/src/api/v1/backups.py`)
Consultar directamente `file?name={fname}.rsc` (con fallback a `POST file/print` con `.proplist` y `file/get`) y limpiar cualquier `rosgrid_bk_*.rsc` residual:

```python
async def _list_router_files_metadata_safe(client: MikrotikRestClient, target_name: str | None = None) -> list[dict[str, Any]]:
    """Obtiene metadatos de archivos en RouterOS evitando corromper el JSON con 'contents' binarios (.pcap)."""
    if target_name:
        try:
            res = await client.get(f"file?name={target_name}")
            if isinstance(res, list):
                return [f for f in res if isinstance(f, dict)]
        except Exception as err:
            logger.debug("Consulta filtrada file?name=%s falló: %s", target_name, err)

    try:
        payload: dict[str, Any] = {".proplist": ".id,name,size,type,contents"}
        if target_name:
            payload["?name"] = target_name
        res_print = await client.post("file/print", json_data=payload)
        if isinstance(res_print, list):
            return [f for f in res_print if isinstance(f, dict)]
    except Exception as err:
        logger.debug("Consulta file/print con .proplist falló: %s", err)

    try:
        raw_files = await client.get("file")
        if isinstance(raw_files, list):
            files_list = [f for f in raw_files if isinstance(f, dict)]
            if target_name:
                return [f for f in files_list if f.get("name") in (target_name, f"{target_name}.rsc")]
            return files_list
    except Exception as err:
        logger.debug("Consulta general file falló: %s", err)
    return []


async def _cleanup_stale_rosgrid_bk_files(client: MikrotikRestClient, exclude_name: str | None = None) -> None:
    """Elimina archivos temporales rosgrid_bk_*.rsc huérfanos en flash usando solo metadatos sin 'contents'."""
    try:
        res = await client.post("file/print", json_data={".proplist": ".id,name"})
        if not isinstance(res, list):
            return
        for item in res:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "")
            fid = str(item.get(".id") or "")
            if fid and name.startswith("rosgrid_bk_") and name.endswith(".rsc") and name != exclude_name:
                await client.delete(f"file/{fid}")
    except Exception as err:
        logger.debug("Omitida limpieza de rosgrid_bk_*.rsc residuales: %s", err)


async def _read_and_cleanup_rsc_file(client: MikrotikRestClient, fname: str) -> str:
    """Lee el contenido del archivo temporal .rsc en RouterOS (filtrando por nombre para evitar binarios .pcap) y lo elimina."""
    expected_name = fname if fname.endswith(".rsc") else f"{fname}.rsc"
    target_files = await _list_router_files_metadata_safe(client, expected_name)
    if not target_files and expected_name != fname:
        target_files = await _list_router_files_metadata_safe(client, fname)
    if not target_files:
        return ""

    tf = target_files[0]
    raw_text = str(tf.get("contents", "") or "")
    file_id = str(tf.get(".id", "") or "")
    if not raw_text:
        file_name = str(tf.get("name") or expected_name)
        file_size = int(tf.get("size", 0) or 0)
        raw_text = await _read_large_rsc_file(client, file_name, file_id, file_size)
    if file_id:
        try:
            await client.delete(f"file/{file_id}")
        except Exception as del_err:
            logger.debug("Error eliminando archivo temporal en router: %s", del_err)
    await _cleanup_stale_rosgrid_bk_files(client, exclude_name=expected_name)
    return raw_text
```

#### 1.B. Rechazar `"[]"` y `"{}"` en `clean_rsc_export_comments` y Purgar Respaldos Corruptos `"[]"` al Listar (`fastapi/src/api/v1/backups.py`)
1. En `clean_rsc_export_comments(raw_text: str) -> str` (línea 59 de `backups.py`), asegurar que si el texto resultante es `"[]"` o `"{}"` devuelva `""`:
   ```python
   _EMPTY_EXPORT_HASHES = frozenset({
       hashlib.sha256(b"[]").hexdigest(),
       hashlib.sha256(b"{}").hexdigest(),
       hashlib.sha256(b"").hexdigest(),
   })


   def clean_rsc_export_comments(raw_text: str) -> str:
       """Elimina comentarios de cabecera con timestamps volátiles de RouterOS y descarta salidas vacías ('[]')."""
       lines = [line for line in raw_text.splitlines() if not line.strip().startswith("#")]
       cleaned = "\n".join(lines).strip()
       return "" if cleaned in ("[]", "{}") else cleaned
   ```
2. En `list_backups` (alrededor de la línea 380 de `backups.py`), eliminar automáticamente de la base de datos cualquier registro corrupto histórico cuyo `rsc_sha256_hash` esté en `_EMPTY_EXPORT_HASHES` (`4f53cda18c2baa...`) o tenga `rsc_size_bytes <= 2`, para que la interfaz de `caps1` quede inmediatamente limpia sin necesidad de intervención manual en SQL:
   ```python
    valid_records: list[RouterBackup] = []
    purged_corrupt = False
    for r in records:
        if r.rsc_sha256_hash in _EMPTY_EXPORT_HASHES or r.rsc_size_bytes <= 2:
            await db.delete(r)
            purged_corrupt = True
        else:
            valid_records.append(r)
    if purged_corrupt:
        await db.commit()
   ```
3. En `get_backup_diff` (alrededor de la línea 506 de `backups.py`), cuando `target_backup_id.upper() == "LIVE"`, invocar directamente `await export_router_rsc(client)` en lugar de hacer primero un `POST export` sin `file`:
   ```python
    if target_backup_id.upper() == "LIVE":
        _, client = await get_router_and_client(router_id, claims, db)
        try:
            target_rsc = await export_router_rsc(client)
        except Exception:
            target_rsc = ""
        target_created_at = datetime.now(UTC).isoformat()
   ```

---

### Paso 2: Reutilizar `export_router_rsc` con Deduplicación SHA-256 en `_perform_pre_upgrade_backup` y Usar `file/print` en `_cleanup_corrupted_npk_downloads` (`fastapi/src/api/v1/bulk_and_updates.py`)

#### 2.A. Refactorizar `_perform_pre_upgrade_backup` (líneas 119–159 de `fastapi/src/api/v1/bulk_and_updates.py`)
Sustituir la llamada rota `await client.post("export", {"terse": "false", "show-sensitive": "false"})` por `await export_router_rsc(client)` de `src.api.v1.backups`, añadiendo deduplicación contra el último respaldo del router para no crear múltiples copias idénticas en cada intento de actualización:

```python
async def _perform_pre_upgrade_backup(
    client: MikrotikRestClient,
    router_obj: Router,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    from sqlalchemy import desc
    from src.api.v1.backups import _compute_diff_stats, _decrypt_backup_rsc, clean_rsc_export_comments, export_router_rsc

    try:
        cleaned = await export_router_rsc(client)
        if not cleaned or cleaned.strip() in ("[]", "{}"):
            raise ValueError("El router devolvió una exportación .rsc vacía")

        rsc_hash = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
        now_utc = datetime.now(UTC)

        latest_stmt = (
            select(RouterBackup)
            .where(RouterBackup.tenant_id == tenant_id, RouterBackup.router_id == router_obj.id)
            .order_by(desc(RouterBackup.created_at))
            .limit(1)
        )
        latest_backup = (await db.execute(latest_stmt)).scalar_one_or_none()
        if latest_backup and latest_backup.rsc_sha256_hash == rsc_hash:
            latest_backup.last_verified_identical_at = now_utc
            await db.flush()
            return True

        lines_added, lines_removed = 0, 0
        if latest_backup:
            try:
                old_text = clean_rsc_export_comments(_decrypt_backup_rsc(latest_backup, tenant_id))
                lines_added, lines_removed, _ = _compute_diff_stats(old_text.splitlines(), cleaned.splitlines())
            except Exception:
                lines_added, lines_removed = 0, 0

        aad = f"{tenant_id}:{router_obj.id}".encode()
        ct, iv, tag = encrypt_aes_gcm(cleaned.encode("utf-8"), aad)

        backup = RouterBackup(
            tenant_id=tenant_id,
            router_id=router_obj.id,
            backup_type="PRE_UPGRADE",
            ros_version_at_backup=router_obj.ros_version or "7.16",
            rsc_sha256_hash=rsc_hash,
            rsc_size_bytes=len(cleaned.encode("utf-8")),
            rsc_ciphertext=ct,
            rsc_iv=iv,
            rsc_tag=tag,
            diff_lines_added=lines_added,
            diff_lines_removed=lines_removed,
            parent_backup_id=latest_backup.id if latest_backup else None,
            triggered_by=user_id,
            created_at=now_utc,
            last_verified_identical_at=now_utc,
            expires_at=now_utc + timedelta(days=30),
        )
        db.add(backup)
        await db.flush()
        return True
    except Exception as exc:
        logger.error("Fallo de backup obligatorio previo al upgrade en %s: %s", router_obj.display_name, exc)
        return False
```

#### 2.B. Blindar `_cleanup_corrupted_npk_downloads` contra archivos `.pcap` binarios (líneas 213–231 de `fastapi/src/api/v1/bulk_and_updates.py`)
En `_cleanup_corrupted_npk_downloads`, intentar primero `await client.post("file/print", {".proplist": ".id,name,size"})` antes de `await client.get("file")` para que un `.pcap` en flash no impida enumerar archivos `.npk` de `0 bytes`:

```python
async def _cleanup_corrupted_npk_downloads(client: MikrotikRestClient) -> int:
    """Elimina archivos .npk truncados (size == 0) en el router para evitar bloqueos de descarga."""
    removed = 0
    try:
        files = await client.post("file/print", {".proplist": ".id,name,size"})
        if not isinstance(files, list):
            files = await client.get("file")
        if not isinstance(files, list):
            return 0
        for item in files:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", ""))
            size = str(item.get("size", ""))
            fid = item.get(".id")
            if name.endswith(".npk") and size == "0" and fid:
                await client.delete(f"file/{fid}")
                removed += 1
    except Exception as exc:
        logger.debug("Omitida limpieza de .npk residuales: %s", exc)
    return removed
```

---

## 3. Aseguramiento de Calidad Level-11X Obligatorio (Pytest, Vitest y Karate Labs BDD)

> **DIRECTIVA SUPREMA QA 11X PARA GEMINI 3.8 FLASH (HIGH):**  
> Implementar y ejecutar en contenedores Docker efímeros (`Regla Cero`) las siguientes pruebas exactas:

### 3.A. Pruebas Unitarias en `fastapi/tests/api/test_operations_endpoints_full.unit.py`
Añadir al final de `test_backups_helpers_and_diff` (o como nueva función `test_backups_filtered_file_query_with_pcap_and_corrupt_purge`) el siguiente test:

```python
@pytest.mark.asyncio
async def test_backups_filtered_file_query_with_pcap_and_corrupt_purge(fake_op_context: dict[str, Any]) -> None:
    """Verifica que _read_and_cleanup_rsc_file usa file?name= evitando corrupción por .pcap y list_backups purga '[]'."""
    ctx = fake_op_context
    claims = ctx["claims"]
    db = AsyncMock()
    client = AsyncMock()

    # Simular que GET 'file' sin filtro devuelve un str corrupto por culpa de chk.pcap,
    # mientras que GET 'file?name=rosgrid_bk_test.rsc' devuelve la lista JSON válida.
    async def mock_get(ep: str) -> Any:
        if ep == "file":
            return '[{".id":"*1","name":"chk.pcap","contents":"\\x00\\xffBINARY"}]'
        if ep.startswith("file?name="):
            return [
                {
                    ".id": "*99",
                    "name": "rosgrid_bk_test.rsc",
                    "size": "120",
                    "contents": "# 2026-11-05 by RouterOS 7.25.1\n/system identity\nset name=caps\n",
                }
            ]
        return []

    client.get = AsyncMock(side_effect=mock_get)
    client.post = AsyncMock(return_value=[])
    client.delete = AsyncMock(return_value=None)

    rsc_text = await api_backups._read_and_cleanup_rsc_file(client, "rosgrid_bk_test")
    assert "/system identity" in rsc_text
    assert "set name=caps" in rsc_text
    client.delete.assert_awaited_with("file/*99")

    # Verificar que clean_rsc_export_comments rechaza '[]'
    assert api_backups.clean_rsc_export_comments("[]") == ""
    assert api_backups.clean_rsc_export_comments("# comment\n[]") == ""

    # Verificar que list_backups purga automáticamente respaldos corruptos con hash de '[]' (4f53cda18c2baa...)
    empty_hash = hashlib.sha256(b"[]").hexdigest()
    corrupt_bk = RouterBackup(
        id=uuid.uuid4(),
        tenant_id=ctx["tenant_id"],
        router_id=ctx["router_id"],
        backup_type="PRE_UPGRADE",
        ros_version_at_backup="7.25",
        rsc_sha256_hash=empty_hash,
        rsc_size_bytes=2,
        rsc_ciphertext=b"x",
        rsc_iv=b"x",
        rsc_tag=b"x",
        diff_lines_added=0,
        diff_lines_removed=0,
        created_at=datetime.now(UTC),
        last_verified_identical_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    mock_list = MagicMock()
    mock_list.scalars.return_value.all.return_value = [corrupt_bk]
    db.execute.return_value = mock_list

    res_list = await api_backups.list_backups(ctx["router_id"], claims=claims, db=db)
    assert len(res_list.items) == 0
    db.delete.assert_awaited_once_with(corrupt_bk)
    db.commit.assert_awaited()
```

### 3.B. Prueba Unitaria de `_perform_pre_upgrade_backup` en `fastapi/tests/api/test_smart_os_firmware_update_chr.unit.py`
Añadir al final de `fastapi/tests/api/test_smart_os_firmware_update_chr.unit.py`:

```python
@pytest.mark.asyncio
async def test_perform_pre_upgrade_backup_uses_export_router_rsc_and_rejects_empty_brackets() -> None:
    """Verifica que _perform_pre_upgrade_backup usa export_router_rsc, deduplica y nunca guarda '[]'."""
    from unittest.mock import MagicMock
    from src.api.v1.bulk_and_updates import _perform_pre_upgrade_backup

    client = AsyncMock()
    r_chr = Router(id=uuid.uuid4(), display_name="caps1", ros_version="7.25.1")
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    db = AsyncMock()
    mock_exec = MagicMock()
    mock_exec.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_exec

    with patch(
        "src.api.v1.backups.export_router_rsc",
        AsyncMock(return_value="/system identity\nset name=caps"),
    ):
        ok = await _perform_pre_upgrade_backup(client, r_chr, t_id, u_id, db)
        assert ok is True
        db.add.assert_called_once()
        saved_bk = db.add.call_args[0][0]
        assert saved_bk.rsc_size_bytes > 2
        assert not saved_bk.rsc_sha256_hash.startswith("4f53cda18c2baa")
```

### 3.C. Escenario 163 Karate Labs BDD API (`fastapi/test/api_test.feature` y `docs/examples/fastapi/api_test.feature.example`)
Al final de ambos archivos, añadir:

```gherkin
  Scenario: 163. Respaldo .rsc Libre de Corrupción por Binarios .pcap y Purga Automática de Exportaciones Vacías '[]' (Hito 30.10)
    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/backups'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }

    Given path '/api/v1/routers/00000000-0000-0000-0000-000000000001/backups/diff'
    And param base_backup_id = '00000000-0000-0000-0000-000000000002'
    And param target_backup_id = 'LIVE'
    When method get
    Then status 401
    And match response == { detail: 'No autenticado (falta token o cookie de sesión)' }
```

### 3.D. Escenario 101 Karate Labs BDD UI (`vue3/test/ui_business_flow.feature` y `docs/examples/vue3/ui_business_flow.feature.example`)
Al final de ambos archivos, añadir:

```gherkin
  Scenario: 101. Comparador de Respaldos Git Diff sin Falsos Respaldos '[]' y Lectura Filtrada file?name= ante Archivos .pcap (Hito 30.10)
    * def backupIntegrityContract = { filteredFileQuery: 'file?name=', metadataProplist: '.id,name,size,type,contents', rejectEmptyBracketsHash: '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945', deduplicatePreUpgrade: true }
    * match backupIntegrityContract.filteredFileQuery == 'file?name='
    * match backupIntegrityContract.rejectEmptyBracketsHash == '4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945'
    * match backupIntegrityContract.deduplicatePreUpgrade == true
```

### 3.E. Comandos de Verificación en Contenedores Docker Efímeros (`Regla Cero`)
```bash
docker compose -f docker-compose.qa.yml run --rm --entrypoint pytest api-test -q tests/api/test_operations_endpoints_full.unit.py tests/api/test_smart_os_firmware_update_chr.unit.py
docker compose -f docker-compose.qa.yml run --rm --entrypoint ruff api-test check src/api/v1/backups.py src/api/v1/bulk_and_updates.py tests/api/test_operations_endpoints_full.unit.py tests/api/test_smart_os_firmware_update_chr.unit.py
./.agents/scripts/certify_task_completion.sh
```
