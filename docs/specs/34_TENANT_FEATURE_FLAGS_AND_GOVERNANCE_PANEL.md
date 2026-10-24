# 34 — PANEL DE GOBERNANZA DE FEATURE FLAGS Y MÓDULOS POR EMPRESA (RoSGrid)

> **[DIRECTIVA DE SISTEMA]:** Esta especificación define la arquitectura del motor de Feature Flags y Gobernanza Modular de RoSGrid. Permite que una única instalación de RoSGrid se transforme dinámicamente entre un entorno de Operador ISP/FTTH, una red corporativa/bancaria, o un despliegue mixto, habilitando o deshabilitando módulos de forma granular por cada Organización (Tenant) sin requerir reinicios del sistema ni modificaciones en el código.

---

## 1. Esquema de Base de Datos y Persistencia (`fastapi/src/models/core.py`)

Se incorporan los siguientes atributos a la tabla `tenants` (gestionados mediante la migración Alembic `0005_tenant_feature_flags_and_technical_qos.py`):

| Campo | Tipo | Valor por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `isp_module_enabled` | Boolean | `true` | Habilita/deshabilita el módulo de Técnico de Campo, gestión de ONUs y mapa FTTH. |
| `bgp_looking_glass_enabled` | Boolean | `false` | Habilita/deshabilita la consola de BGP Looking Glass para redes con ASN propio. |
| `sfp_ddm_telemetry_enabled` | Boolean | `true` | Monitoreo continuo de transceptores ópticos SFP (dBm, temperatura, voltaje). |
| `ipfix_analytics_enabled` | Boolean | `false` | Captura de flujos IPFIX y detección de tráfico anómalo. |
| `enforce_maker_checker` | Boolean | `true` | Exige aprobación de un segundo operador (código 202) para cambios críticos de red. |
| `auto_safemode_enforced` | Boolean | `true` | Fuerza Safe Mode de 60s en cualquier cambio vía REST API en RouterOS. |
| `ai_mcp_integration_enabled` | Boolean | `true` | Permite el acceso de agentes autónomos de Inteligencia Artificial mediante `/api/v1/mcp`. |
| `nightly_backups_enabled` | Boolean | `true` | Activa la extracción nocturna automática de respaldos `.rsc` con cálculo de Git Diff. |
| `outbound_webhooks_enabled` | Boolean | `true` | Habilita el despacho HTTP de webhooks de eventos técnicos hacia CRMs o bots externos. |
| `config_drift_monitoring_enabled` | Boolean | `false` | Habilita la auditoría contra la Plantilla Maestra (*Golden Baseline*). |
| `cis_audit_enabled` | Boolean | `true` | Habilita el escáner de cumplimiento CIS Benchmark y cálculo de Security Score. |
| `sdwan_orchestrator_enabled` | Boolean | `false` | Habilita el aprovisionamiento automatizado de túneles WireGuard y failover multi-WAN. |
| `capsman_wifi_enabled` | Boolean | `false` | Habilita el panel de gestión centralizada de WiFi corporativo (CAPsMAN). |
| `sla_tracker_enabled` | Boolean | `false` | Habilita el monitor de cumplimiento de SLA para enlaces WAN dedicados. |
| `mass_outage_threshold` | Integer | `10` | Cantidad de equipos caídos simultáneamente para disparar la alarma NOC masiva. |
| `default_locale` | String | `'es'` | Código ISO del idioma por defecto para la interfaz del tenant (`es`, `en`). |

---

## 2. Gobernanza de Acceso y Capa de Seguridad API (FastAPI)

### 2.1. Middleware / Dependency Guard `require_feature(flag_name)`

- Antes de procesar cualquier endpoint perteneciente a un módulo modular, FastAPI evalúa el estado del Feature Flag en el contexto del tenant autenticado:

  ```python
  def require_feature(flag_name: str):
      async def dependency(tenant: Tenant = Depends(get_current_tenant)):
          if not getattr(tenant, flag_name, False):
              raise HTTPException(
                  status_code=status.HTTP_403_FORBIDDEN,
                  detail={
                      "code": "FEATURE_MODULE_DISABLED",
                      "message": f"El módulo '{flag_name}' no está habilitado para esta empresa.",
                  }
              )
          return True
      return dependency
  ```

- **Ejemplo:** Las rutas `/api/v1/field-ops/*` y `/api/v1/subscribers/*` exigen `require_feature("isp_module_enabled")`. Si una empresa corporativa tiene este flag en `false`, cualquier intento de invocar estas rutas es rechazado inmediatamente con HTTP 403.

---

## 3. Comportamiento Dinámico en el Frontend (Vue 3 + Pinia)

### 3.1. Store de Tenant y Reactividad (`useAuthStore` / `useTenantStore`)

- Al iniciar sesión, el payload de autenticación incluye el objeto `features` con los estados booleanos del tenant actual.
- **Barra de Navegación (`RgResponsiveShell.vue`):**
  - Si `isp_module_enabled === false`, los elementos de menú *"Técnico de Campo"* y *"Mapa de Abonados"* se omiten de la barra lateral.
  - Si `bgp_looking_glass_enabled === false`, se oculta la herramienta BGP Looking Glass.
  - Si `capsman_wifi_enabled === false`, se oculta la pestaña de WiFi Corporativo.
- **Paleta de Comandos (`RgCommandPalette.vue` / `Ctrl+K`):**
  - Los atajos y acciones de búsqueda filtran dinámicamente los comandos disponibles basándose en las capacidades activas del tenant.
- **Guardias de Enrutador (`router.beforeEach`):**
  - Si un usuario ingresa manualmente a una URL desactivada para su empresa (ej. `/field-ops` cuando `isp_module_enabled = false`), el router lo intercepta y redirige al dashboard principal con un mensaje toast informativo.

---

## 4. Interfaz de Administración de Feature Flags (`TenantsManagementView.vue`)

Exclusiva para el rol `SUPERADMIN_GLOBAL`:

- Modal o pestaña táctica **"Módulos & Capacidades"** con diseño de alta densidad:
  - **Sección 1: Perfil de Operación de Red:**
    - Switch `Módulo ISP & Operaciones de Campo (FTTH/ONUs)`.
    - Switch `BGP Looking Glass (Para redes con ASN)`.
    - Switch `Gestión Centralizada WiFi (CAPsMAN / Campus)`.
    - Switch `Orquestador SD-WAN & Malla WireGuard`.
  - **Sección 2: Ciberseguridad & Compliance:**
    - Switch `Auditoría CIS Benchmark & Hardening`.
    - Switch `Detección de Desviación de Configuración (Config Drift)`.
    - Switch `Gobernanza Maker-Checker Estricta (Aprobación 202)`.
    - Switch `Safe Mode Obligatorio (60s)`.
  - **Sección 3: Telemetría & Automatización:**
    - Switch `Monitoreo Óptico SFP DDM`.
    - Switch `Análisis de Flujos IPFIX`.
    - Switch `Integración de Agentes IA vía MCP`.
    - Switch `Respaldos Nocturnos Automáticos con Git Diff`.
    - Switch `Monitor de Cumplimiento de SLA`.
    - Campo numérico: `Umbral de Alarma de Caída Masiva (Dispositivos)`.
    - Selector: `Idioma Predeterminado del Sistema`.

Al guardar los cambios, las banderas se actualizan atómicamente en PostgreSQL y se invalida la caché de permisos en KeyDB para propagación inmediata a todas las sesiones activas del tenant.
