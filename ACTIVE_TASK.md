# Registro de Tarea Activa: Hitos 28.2, 28.3, 28.7 y 28.8 (RoSGrid)

**Fecha de Inicio:** 2026-11-01  
**Estado:** COMPLETED  
**Objetivo Principal:**
Implementar de forma completa y determinista los Hitos 28.2, 28.3, 28.7 y 28.8 siguiendo al pie de la letra los bloques Target/Replacement de sus especificaciones oficiales:
1. Hito 28.2: `docs/specs/57_FTTH_NAP_BOX_DETAIL_GREENLET_FIX_AND_SUBSCRIBER_REGISTRATION_CONTRACT.md`
2. Hito 28.3: `docs/specs/58_BACKUP_EXPORT_FTP_POLICY_STALE_SESSION_BYPASS_AND_DOC_PARITY.md`
3. Hito 28.7: `docs/specs/62_SESSION_KILLSWITCH_TARGET_SCOPING_AND_WS_ISOLATION.md`
4. Hito 28.8: `docs/specs/63_RESPONSIVE_AUTO_FIT_DATA_COLUMNS_AND_INVENTORY_TABLE_ERGONOMICS.md`

---

## Diario de Progreso

- [x] **Fase 0: Inspección y Análisis de Radio de Impacto (Graphify AST)**
  - Verificada salud topológica con `.agents/scripts/verify_topological_health.py` (0 violaciones de acoplamiento de capas).
  - Inspeccionado radio de impacto con `inspect_blast_radius.py` para `optical_boxes`, `export_router_rsc` y `kill_session`.

- [x] **Fase 1: Implementación Hito 28.2 (Spec 57 - Detalle NAP Greenlet Fix y Contrato Registro FTTH)**
  - [x] 1.1 Blindaje async-safe en `SubscriberDevice.assigned_ipv4` (`fastapi/src/models/ipam.py`).
  - [x] 1.2 Normalización de alias FTTH en `SubscriberDeviceCreate` y `SubscriberDeviceUpdate` (`fastapi/src/schemas/ipam.py`).
  - [x] 1.3 Eliminación de `MissingGreenlet` y carga asíncrona segura en `get_optical_box_detail` (`fastapi/src/api/v1/optical_boxes.py`).
  - [x] 1.4 Helper `_resolve_and_validate_nap_port`, rol `FIELD_TECH` y persistencia FTTH en `create_subscriber_device` (`fastapi/src/api/v1/subscribers.py`).
  - [x] 1.5 Formulario FTTH, watcher de puerto NAP ocupado y selector de modo ONU en `vue3/src/components/field/FieldTechMobileView.vue`.

- [x] **Fase 2: Implementación Hito 28.3 (Spec 58 - Bypass Caché Sesión RouterOS 10m y Diagnóstico Política FTP)**
  - [x] 2.1 Helpers modulares `_read_and_cleanup_rsc_file`, `_resolve_user_group_ftp_status`, `_export_via_fresh_ephemeral_session`, `_try_fallback_rsc_export` y actualización de `export_router_rsc` (`fastapi/src/api/v1/backups.py`).
  - [x] 2.2 Actualización de política MikroTik v7 en `vue3/src/data/helpCatalog.ts`.
  - [x] 2.3 Sincronización documental de `rosgrid-api-group` en los 6 archivos (`README.md`, `docs/INSTALL.md`, `docs/FAQ.md`, `docs/02_PREPARACION_MIKROTIK_ROUTEROS_V7.md`, `docs/MANUAL_ADMINISTRADOR_E_INSTALADOR.md`, `docs/specs/08_MIKROTIK_REST_V7_CLIENT_TOFU_AND_SAFEMODE.md`).

- [x] **Fase 3: Implementación Hito 28.7 (Spec 62 - Aislamiento de Destinatario en Kill-Switch de Sesiones)**
  - [x] 3.1 Normalización de payload Pub/Sub en `kill_session` (`fastapi/src/redis_layer/sessions.py`).
  - [x] 3.2 Helper `_classify_session_kill_event` y filtrado estricto en multiplexor WebSocket (`fastapi/src/api/v1/websockets.py`).
  - [x] 3.3 Candado de verificación de destinatario en Pinia (`vue3/src/stores/useNocEventsStore.ts`).

- [x] **Fase 4: Implementación Hito 28.8 (Spec 63 - Columnas Auto-Fit en RgDataTable y Ergonomía de Inventario)**
  - [x] 4.1 Content-Hugging (`width: 1%`) y compactación de celdas en `vue3/src/components/common/RgDataTable.vue`.
  - [x] 4.2 Formateador compacto de modelo (`CHR QEMU`) y espaciado de acciones en `vue3/src/views/RouterInventoryView.vue`.
  - [x] 4.3 Cabeceras concisas en `vue3/src/locales/es.json` y `vue3/src/locales/en.json`.

- [x] **Fase 5: Pruebas Unitarias, BDD Karate Labs y Certificación Docker**
  - [x] 5.1 Pruebas unitarias backend: `fastapi/tests/api/test_optical_boxes_and_bimodal_ops.unit.py`, `fastapi/tests/api/test_subscribers.unit.py`, `fastapi/tests/api/test_backups_diff_and_bulk_ops.unit.py`, `fastapi/tests/api/test_websockets_and_workers.unit.py` (633 de 633 pruebas Pytest pasadas al 100%).
  - [x] 5.2 Pruebas unitarias frontend: `vue3/src/components/field/FieldTechMobileView.unit.ts`, `vue3/src/stores/useNocEventsStore.unit.ts`, `vue3/src/views/inventory/routerInventoryView.unit.ts` (509 de 509 pruebas Vitest pasadas en 79 suites al 100%).
  - [x] 5.3 Escenarios BDD Karate Labs: `fastapi/test/api_test.feature` (Escenarios 131 y 132), `vue3/test/ui_business_flow.feature` (Escenarios 74 y 75) y réplicas en `docs/examples/`.
  - [x] 5.4 Ejecución de suites en Docker efímero (`Rule Zero`): Pytest (633 tests, 100%), Vitest (509 tests, 100%), Ruff (0 errores), Vue-tsc (0 errores).

- [x] **Fase 6: Gobernanza, Sincronización Documental, Regeneración de Grafos y Git Push**
  - [x] 6.1 Actualización de `ROADMAP.md` (marcados [x] 28.2, 28.3, 28.7, 28.8), `CHANGELOG.md`, `TESTING.md` y `docs/specs/` (57, 58, 62, 63 marcadas como certificadas).
  - [x] 6.2 Actualización de scripts de gobernanza, limpieza, gitignore y mejoras en `.agents/rules/secure_development_and_testing_guidelines.md` y `AGENTS.md` (cláusula anti-replay de Idempotency-Key y prevención de MissingGreenlet en AsyncSession).
  - [x] 6.3 Regeneración de grafos AST Graphify (`actualizar-grafos-graphify.sh`) — Backend y Frontend actualizados en Docker efímero.
  - [x] 6.4 Certificación final (`certify_task_completion.sh`) — 8 de 8 fases certificadas exitosamente.
  - [x] 6.5 Git commit semántico en español y git push a origin/main.
