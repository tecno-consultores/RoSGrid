# Registro de Tarea Activa: Hito 27.19 (RoSGrid) y Guía Prometheus/Grafana (rosgrid-web)

**Fecha de Inicio:** 2026-11-01
**Estado:** COMPLETED
**Objetivo Principal:**
1. RoSGrid: Ejecutar Hito 27.19 (Arquitectura Dual de Observabilidad Prometheus `GET /metrics` vs `GET /api/v1/metrics/fleet` e Integración con Grafana — Secciones 3 y 5.5 de Spec 55).
2. rosgrid-web: Actualizar y enriquecer la guía de Prometheus + Grafana con tabla de 8 métricas, configuración `prometheus.yml`, consultas PromQL esenciales y reglas Alertmanager.

---

## Diario de Progreso

- [x] **Fase 0: Inspección y Análisis de Radio de Impacto (Graphify AST)**
  - Identificado radio de impacto con `inspect_blast_radius.py "fleet_metrics"` (impacto localizado en `fleet_metrics.py`, `test_hito23_topology_and_fleet.unit.py`).
  - Verificada salud topológica con `verify_topological_health.py` (0 violaciones de acoplamiento de capas).

- [x] **Fase 1: Implementación Backend RoSGrid (Hito 27.19)**
  - [x] 1.1 Enriquecer `fastapi/src/api/v1/fleet_metrics.py`:
    - Incorporar `_UPTIME_MULTIPLIERS` y `_parse_ros_uptime_to_seconds(uptime_str: str) -> int` (Radon CC <= 3).
    - Incorporar `"ros_version"` en etiquetas de `_build_router_labels` ({`tenant_id`, `router_id`, `identity`, `model`, `ros_version`}).
    - Enriquecer `_get_router_ephemeral_telemetry` con `uptime_seconds`, `temperature_celsius`, `voltage_volts`, `syslog_critical_events_total`.
    - Generar las 8 métricas canónicas OpenMetrics / Prometheus.
    - Filtrar routers gobernados por `Tenant.prometheus_fleet_exporter_enabled`.
    - Certificada complejidad ciclomática Radon Grado A (promedio 3.16, 12 de 12 bloques con `CC <= 5`).
    - Certificado tipado estricto mypy (`Success: no issues found in 1 source file`).
  - [x] 1.2 Plantillas Oficiales de Observabilidad:
    - Creado `docs/examples/grafana/rosgrid_mikrotik_fleet_dashboard.json` (Dashboard JSON de Grafana con 12 paneles clave y variable `$router`).
    - Creado `docs/examples/prometheus/prometheus.yml` (Scraping job dual).
    - Creado `docs/examples/prometheus/rosgrid-alerts.rules.yml` (Reglas de Alertmanager).

- [x] **Fase 2: Actualización de Guía Prometheus/Grafana en rosgrid-web**
  - [x] 2.1 Enriquecido `src/pages/docs/QuickstartDoc.vue` con la guía completa (tabla de 8 métricas, `prometheus.yml`, PromQL y Alertmanager).
  - [x] 2.2 Sincronizados espejos Markdown `public/docs/quickstart.md` y `public/llms-full.txt`.
  - [x] 2.3 Ejecutadas pruebas en Docker: `pnpm run typecheck`, `pnpm run lint` y `pnpm run test:unit` (72/72 pruebas pasando al 100%).
  - [x] 2.4 Actualizados `CHANGELOG.md` en `rosgrid-web`, commit y push a `origin/main` exitoso.

- [x] **Fase 3: Pruebas Unitarias y BDD en RoSGrid**
  - [x] 3.1 Pruebas unitarias de backend: `fastapi/tests/api/test_fleet_metrics.unit.py` (9 de 9 pruebas aprobadas al 100%, 100% de cobertura en `fleet_metrics.py`).
  - [x] 3.2 Actualizado `fastapi/tests/api/test_hito23_topology_and_fleet.unit.py` (17 de 17 pruebas aprobadas al 100%).
  - [x] 3.3 Karate Labs BDD: Enriquecido escenario 60 en `fastapi/test/api_test.feature` y réplica en `docs/examples/fastapi/test/api_test.feature`.
  - [x] 3.4 Ejecutado en Docker efímero: 630 de 630 pruebas unitarias backend aprobadas al 100% (49.49s), 507 de 507 pruebas unitarias frontend Vitest en 79 suites aprobadas al 100%, 0 errores en `ruff`, `mypy` y `vue-tsc`.

- [x] **Fase 4: Gobernanza, Documentación, Graphify y Git**
  - [x] 4.1 Actualizada documentación en RoSGrid: `docs/MANUAL_ADMINISTRADOR_E_INSTALADOR.md`, `docs/06_REFERENCIA_COMPLETA_API_REST_Y_WEBSOCKETS.md`, `docs/12_DISENO_TOPOLOGIA_L2_SYSLOG_Y_AUTOMATIZACION.md`, `docs/specs/55_*.md`.
  - [x] 4.2 Actualizado `CHANGELOG.md` (`## [Unreleased]`), `ROADMAP.md` (marcado Hito 27.19 como completado), `TESTING.md`.
  - [x] 4.3 Mejoras incorporadas en `.agents/rules/secure_development_and_testing_guidelines.md`, `AGENTS.md` y `.agents/scripts/certify_task_completion.sh` (soporte de archivos untracked en verificación).
  - [x] 4.4 Regenerados grafos AST Graphify (`actualizar-grafos-graphify.sh`): Backend 3905 nodos, Frontend 2471 nodos.
  - [x] 4.5 Certificación final superada con `./.agents/scripts/certify_task_completion.sh` (8/8 etapas aprobadas).
  - [ ] 4.6 Commits semánticos y push a Git en RoSGrid.
