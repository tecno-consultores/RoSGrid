# Especificación Técnica 93: Paridad Total de Internacionalización (i18n Español / Inglés) en CIS Hardening, Seguridad L2 & Rogue DHCP, Telemetría SLA, Canales de Alerta y Diagnóstico & SIEM

**Estado:** Pendiente de Implementación (`Hito 30.16` en `ROADMAP.md`)
**Componentes Afectados:**
- Diccionarios i18n Frontend:
  - `vue3/src/locales/es.json`
  - `vue3/src/locales/en.json`
- Vistas y Componentes Frontend:
  - `vue3/src/views/EnterpriseComplianceView.vue` (Pestañas: **CIS Hardening**, **Seguridad L2 & Rogue DHCP**, **Telemetría de SLA**)
  - `vue3/src/components/operations/NotificationChannelsPanel.vue` (Pestaña: **Canales de Alerta & Notificación**)
  - `vue3/src/components/operations/DiagnosticsAndSiemPanel.vue` (Pestaña: **Diagnóstico & SIEM**)
- Pruebas Nivel 11X (Creación y Ejecución Obligatoria):
  - `vue3/src/views/enterpriseComplianceView.unit.ts` (Suite Vitest validando traducción completa al inglés en CIS Hardening, Seguridad L2 & Rogue DHCP y Telemetría SLA)
  - `vue3/src/components/operations/NotificationChannelsPanel.unit.ts` (Suite Vitest validando traducción completa al inglés en Canales de Alerta & Notificación)
  - `vue3/src/components/operations/DiagnosticsAndSiemPanel.unit.ts` (Suite Vitest validando traducción completa al inglés en Diagnóstico & SIEM)
  - `vue3/test/ui_business_flow.feature` y `docs/examples/vue3/ui_business_flow.feature.example` (Escenario Karate Labs BDD 107)

---

## 1. Contexto y Diagnóstico Forense de Causa Raíz (5 Módulos en `/enterprise/compliance`)

Al cambiar el idioma de la interfaz a inglés (`EN`) en la vista **Gestión de Flota & Cumplimiento Normativo** (`/enterprise/compliance`), cinco pestañas mantienen textos en español:

### 1.1. Módulo 1 — CIS Hardening (`EnterpriseComplianceView.vue` líneas 1321–1786)
1. **34 claves `enterprise.*` invocadas con `t('enterprise.<clave>', 'Fallback en español')` no existen en `en.json` ni en `es.json`:**
   - Debido a que las claves (`filter_all`, `filter_isp`, `filter_corporate`, `filter_enabled`, `filter_disabled`, `cis_th_active`, `cis_th_standards`, `link_standard`, `link_mikrotik`, `status_disabled`, `status_inactive`, `modal_remediate_title`, `modal_close`, `safemode_shield_title`, `safemode_shield_desc`, `command_preview_label`, `applying_safemode`, `btn_confirm_safe_remediate`, `modal_policies_title`, `modal_policies_intro`, `preset_corp_title`, `preset_corp_desc`, `preset_isp_title`, `preset_isp_desc`, `preset_dc_title`, `preset_dc_desc`, `policies_th_active`, `policies_th_code`, `policies_th_title`, `policies_th_severity`, `policies_th_weight`, `policies_th_remediation`, `policies_enabled_count`, `policies_total_weight`, `policies_saving`, `policies_save_btn`, además de `safemode_title`, `select_router_fleet`, `syncing_state`, `drift_master_template`, `drift_default`, `drift_status`, `drift_detected`, `drift_clean`, `drift_unauth_lines`, `drift_diff_title`, `drift_diff_legend`) no están declaradas en `vue3/src/locales/en.json`, la función `t(key, fallback)` retorna siempre el texto en español pasado como segundo argumento.
2. **Columna `Hallazgo Técnico` (`d.finding`) renderizada directamente desde el backend sin traducción (`línea 1521`):**
   - Mientras que el título y la justificación de cada directiva usan `getDirectiveTitle(d)` y `getDirectiveRationale(d)` contra `cis_directives.<CODIGO>` en `en.json`, la celda `<td class="finding-cell">{{ d.finding }}</td>` imprime directamente la cadena `finding` generada en español por `fastapi/src/api/v1/compliance.py` (`run_cis_audit`, líneas 1260–1459).
   - **Solución:** Incorporar `finding_passed` y `finding_failed` en cada una de las 28 directivas bajo `cis_directives` en `en.json` y `es.json` (más `finding_disabled_by_policy` y `CIS_1_1.finding_failed_prefix`), y crear el helper `getDirectiveFinding(d)` en `EnterpriseComplianceView.vue`.

### 1.2. Módulo 2 — L2 Security & Rogue DHCP (`EnterpriseComplianceView.vue` líneas 1965–2193)
1. **Textos hardcodeados en español en las tarjetas de estado por Bridge y en el modal `#modal-dhcp-snooping-config`:**
   - El subtítulo de la barra de acciones (`Configure DHCP Snooping individualmente por Bridge...`), la clave faltante `enterprise.btn_bulk_dhcp_snooping`, las claves faltantes `common.status_active` / `common.status_inactive`, los botones `⚙️ Configurar / Desactivar` y `⚡ Activar DHCP Snooping`, los textos vacíos `Ningún puerto marcado como Trusted` y `Sin puertos Untrusted en este bridge`, y la totalidad del modal `#modal-dhcp-snooping-config` (título, aviso de Regla de Oro en RouterOS v7, checkboxes de DHCP Snooping y Option 82, selector de puertos Trusted, botones) están escritos directamente en español sin `t()`.

### 1.3. Módulo 3 — SLA Telemetry (`EnterpriseComplianceView.vue` líneas 2198–2424)
1. **Claves faltantes y `<optgroup>` / `<option>` hardcodeados en el formulario de sondeo SLA:**
   - Las claves `enterprise.quick_baseline_sla` y `enterprise.sla_target_preset_label` no existen en `en.json`.
   - En el `<select id="sla-target-preset">`, las etiquetas `label="🌐 Gateways WAN Detectados en Router (/ip/route)"`, `label="🖧 DNS Configurados en Router (/ip/dns)"`, `label="🛡️ Referencias Públicas DNS / Anycast"` y `<option value="CUSTOM">✍️ Otra IP / Host Personalizado...</option>` están hardcodeadas en español.
2. **Tarjeta de Detección de Anomalías de Tráfico & Mitigación en 1 Clic (`líneas 2362–2423`) 100% hardcodeada en español:**
   - El título `🚨 Detección de Anomalías de Tráfico & Mitigación en 1 Clic`, subtítulo `Monitoreo volumétrico en tiempo real con FastDrop automático...`, botón `Mitigar Anomalía (FastDrop 300s)`, estado vacío `✔ Cero anomalías volumétricas detectadas en el router en la ventana actual.` y encabezados de tabla (`IP Origen`, `Conexiones Concurrentes`, `Tasa de Tráfico`, `Severidad`, `Acción`) no usan `t()`.

### 1.4. Módulo 4 — Alert & Notification Channels (`NotificationChannelsPanel.vue` líneas 1–713)
1. **Componente con textos hardcodeados en español:**
   - Solamente el encabezado principal y 3 etiquetas usan `t('notifications_channels.*')` (cuyo namespace ni siquiera existe en `en.json` ni `es.json`).
   - Las etiquetas de `availableEvents` (`Router Fuera de Línea (Offline)`, etc.), `getChannelTypeBadge` (`📱 Telegram Bot`, `✉️ Correo SMTP`, `🔗 Webhook HTTP`), las tarjetas de canal (`● ACTIVO`, `○ INACTIVO`, `Eventos Suscritos`, `Registrado:`), el modal de crear/editar canal y el modal de prueba de despacho están hardcodeados en español.

### 1.5. Módulo 5 — Diagnostics & SIEM (`DiagnosticsAndSiemPanel.vue` líneas 1–455)
1. **Formulario de Paquete de Diagnóstico 1-Click y Conector SIEM del ISP hardcodeados en español:**
   - Únicamente los 2 títulos y 2 subtítulos de tarjeta usan `t('enterprise.diag_bundle_title')`, `t('enterprise.diag_bundle_desc')`, `t('enterprise.siem_forwarder_title')` y `t('enterprise.siem_forwarder_desc')`.
   - Todas las etiquetas de campos (`Ring Buffer UI: X eventos`, `Formato de Archivo`, `Líneas de Log Backend`, `Notas del Operador / Descripción de la Falla`, botón `📦 Descargar Paquete de Diagnóstico`, resumen `Archivo:`, `Secretos Sanitizados:`, `Artefactos Incluidos:`, toggle `Habilitado` / `Deshabilitado`, `Protocolo del Colector SIEM`, `Severidad Mínima`, `Host / IP del Servidor SIEM del ISP`, `Puerto`, `Etiqueta de Instancia / Stream`, `Ruta HTTP`, `Token Bearer Opcional`, checkboxes de inclusión de errores UI / auditoría / TLS, y botones `💾 Guardar Configuración SIEM` / `🧪 Enviar Log de Prueba`) están hardcodeadas en español.

---

## 2. Instrucciones Exactas de Implementación (Paso a Paso para Gemini 3.8 Flash High)

### Paso 1: Actualizar `vue3/src/locales/es.json` y `vue3/src/locales/en.json`

> **IMPORTANTE:** Verificar con `python3 .agents/scripts/verify_json_no_duplicate_keys.py` tras editar ambos archivos que no existan claves duplicadas.

#### 1.1. En `common` (`es.json` y `en.json`):
Añadir `status_active` y `status_inactive` dentro del objeto `"common"`:
- En `vue3/src/locales/es.json`:
```json
    "skip_link": "Saltar al contenido principal",
    "status_active": "ACTIVO",
    "status_inactive": "INACTIVO"
```
- En `vue3/src/locales/en.json`:
```json
    "skip_link": "Skip to main content",
    "status_active": "ACTIVE",
    "status_inactive": "INACTIVE"
```

#### 1.2. En `enterprise` (`es.json` y `en.json`):
Añadir las siguientes claves al final del objeto `"enterprise"` (justo después de `"presets_aria"`):

- En `vue3/src/locales/es.json`:
```json
    "presets_aria": "Perfiles Predefinidos de Empresa",
    "safemode_title": "Todas las mutaciones están protegidas bajo Safe Mode de 60s",
    "select_router_fleet": "Seleccionar router de la flota",
    "syncing_state": "Sincronizando estado técnico con RouterOS v7...",
    "drift_master_template": "Plantilla Maestra:",
    "drift_default": "Predeterminada",
    "drift_status": "Estado:",
    "drift_detected": "⚠️ DRIFT DETECTADO",
    "drift_clean": "✔ SINCRONIZADO (GOLDEN)",
    "drift_unauth_lines": "Líneas No Autorizadas:",
    "drift_diff_title": "Diferencial Unificado (Git-Style Diff)",
    "drift_diff_legend": "Verde (+): Línea agregada fuera de plantilla | Rojo (-): Línea eliminada respecto a Golden Config",
    "filter_cis_aria": "Filtrar directivas CIS",
    "filter_all": "Todas",
    "filter_isp": "🌐 ISP / Carrier",
    "filter_corporate": "🏢 Corporativo",
    "filter_enabled": "✅ Activas en Política",
    "filter_disabled": "⏸️ Excluidas",
    "cis_th_active": "Activa",
    "cis_th_standards": "Estándares Oficiales",
    "link_standard": "📜 Estándar Oficial",
    "link_mikrotik": "📘 MikroTik Docs",
    "status_disabled": "EXCLUIDA",
    "status_inactive": "Desactivada",
    "modal_remediate_title": "Confirmar Remediación Táctica CIS",
    "modal_close": "Cerrar",
    "safemode_shield_title": "Protección Safe Mode de 60 Segundos Activa",
    "safemode_shield_desc": "Si el cambio interrumpe la sesión administrativa con el router, RouterOS revertirá automáticamente la configuración tras 60 segundos.",
    "command_preview_label": "Comando CLI / REST Equivalente a Ejecutar en el Router:",
    "applying_safemode": "⏳ Aplicando bajo Safe Mode...",
    "btn_confirm_safe_remediate": "⚡ Confirmar y Aplicar en Router",
    "modal_policies_title": "Personalizar Políticas de Seguridad CIS de la Empresa",
    "modal_policies_intro": "Seleccione un perfil predefinido (ISP, Corporativo o Data Center) o active/desactive individualmente cada directiva y ajuste su peso en el puntaje global.",
    "preset_corp_title": "Empresa Corporativa / Finanzas",
    "preset_corp_desc": "Prioriza VLAN de gestión, DHCP Snooping L2, SNMPv3, bloqueo MAC-Server, SSH fuerte y respaldos cifrados.",
    "preset_isp_title": "Proveedor de Internet (ISP / WISP / Carrier)",
    "preset_isp_desc": "Prioriza filtrado Bogon/Martians en RAW, bloqueo DNS WAN, BGP MD5/TCP-AO, CoPP para CPU, OSPF Auth y VRF.",
    "preset_dc_title": "Máxima Seguridad (Data Center / Crítico)",
    "preset_dc_desc": "Habilita las 28 directivas simultáneamente para auditorías de misión crítica.",
    "policies_th_active": "Activa",
    "policies_th_code": "Código",
    "policies_th_title": "Directiva y Justificación Técnica",
    "policies_th_severity": "Severidad",
    "policies_th_weight": "Peso (Pts)",
    "policies_th_remediation": "Comando que Ejecutará en el Router",
    "policies_enabled_count": "Directivas Activas:",
    "policies_total_weight": "Peso Total Activo:",
    "policies_saving": "⏳ Guardando Política...",
    "policies_save_btn": "💾 Guardar Política de Empresa",
    "switching_intro_desc": "Configure DHCP Snooping individualmente por Bridge bajo Safe Mode (60s) o despliegue la política en toda la flota.",
    "btn_bulk_dhcp_snooping": "Desplegar en Flota (Acciones Masivas)",
    "switching_btn_configure_disable": "⚙️ Configurar / Desactivar",
    "switching_btn_enable_snooping": "⚡ Activar DHCP Snooping",
    "switching_no_trusted_ports": "Ningún puerto marcado como Trusted",
    "switching_no_untrusted_ports": "Sin puertos Untrusted en este bridge",
    "modal_snooping_title": "Configurar DHCP Snooping — Bridge:",
    "modal_snooping_golden_title": "Regla de Oro en RouterOS v7 (Puertos Trusted):",
    "modal_snooping_golden_desc": "Al activar dhcp-snooping=yes, el bridge descartará todos los mensajes DHCP Server (DHCPOFFER / DHCPACK) recibidos por puertos no confiables. Debe marcar como Trusted el puerto uplink o troncal donde reside su servidor DHCP legítimo.",
    "modal_snooping_enable_label": "Habilitar DHCP Snooping en",
    "modal_snooping_enable_hint": "(Filtra respuestas DHCP no autorizadas en Capa 2)",
    "modal_snooping_opt82_label": "Inyectar DHCP Option 82 (add-dhcp-option82=yes)",
    "modal_snooping_opt82_hint": "— Identifica circuito y puerto físico del suscriptor",
    "modal_snooping_trusted_title": "Seleccione los Puertos Confiables (Trusted Ports / Uplink DHCP):",
    "modal_snooping_no_ports": "Este bridge aún no tiene puertos miembros registrados en /interface/bridge/port. Escriba el nombre de la interfaz uplink para agregarla al bridge como Trusted:",
    "modal_snooping_uplink_placeholder": "Ej: ether1",
    "modal_snooping_port_trusted": "✔ TRUSTED (Uplink / Servidor DHCP)",
    "modal_snooping_port_untrusted": "🔒 UNTRUSTED (Puerto de Acceso Cliente)",
    "modal_snooping_add_trunk_label": "Añadir interfaz troncal adicional al bridge como Trusted (opcional):",
    "modal_snooping_add_trunk_placeholder": "Nombre de interfaz (ej. sfp-sfpplus1)",
    "modal_snooping_btn_add_trusted": "+ Añadir Trusted",
    "modal_snooping_btn_save": "⚡ Guardar y Aplicar (Safe Mode 60s)",
    "switching_saved_msg": "DHCP Snooping {state} en {bridge} ({count} puerto(s) Trusted) bajo Safe Mode (60s).",
    "switching_enabled_word": "ACTIVADO",
    "switching_disabled_word": "DESACTIVADO",
    "switching_port_isolated_msg": "Puerto {port} aislado inmediatamente bajo Safe Mode (60s).",
    "quick_baseline_sla": "Sondear Gateway WAN + Quad9 (9.9.9.9)",
    "sla_target_preset_label": "Destino Sugerido / Gateway",
    "sla_optgroup_gateways": "🌐 Gateways WAN Detectados en Router (/ip/route)",
    "sla_optgroup_dns": "🖧 DNS Configurados en Router (/ip/dns)",
    "sla_optgroup_public": "🛡️ Referencias Públicas DNS / Anycast",
    "sla_option_custom": "✍️ Otra IP / Host Personalizado...",
    "sla_custom_link_name": "Enlace Personalizado",
    "sla_anomalies_title": "Detección de Anomalías de Tráfico & Mitigación en 1 Clic",
    "sla_anomalies_subtitle": "Monitoreo volumétrico en tiempo real con FastDrop automático para mitigar ataques DoS / anomalías.",
    "sla_btn_mitigating": "Mitigando...",
    "sla_btn_mitigate_fastdrop": "Mitigar Anomalía (FastDrop 300s)",
    "sla_zero_anomalies": "✔ Cero anomalías volumétricas detectadas en el router en la ventana actual.",
    "sla_th_src_ip": "IP Origen",
    "sla_th_concurrent_conns": "Conexiones Concurrentes",
    "sla_th_traffic_rate": "Tasa de Tráfico",
    "sla_th_severity": "Severidad",
    "sla_th_anomaly_action": "Acción",
    "sla_anomaly_fallback": "ANOMALÍA"
```

- En `vue3/src/locales/en.json`:
```json
    "presets_aria": "Enterprise Predefined Profiles",
    "safemode_title": "All mutations are protected under 60s Safe Mode",
    "select_router_fleet": "Select fleet router",
    "syncing_state": "Synchronizing technical state with RouterOS v7...",
    "drift_master_template": "Master Template:",
    "drift_default": "Default",
    "drift_status": "Status:",
    "drift_detected": "⚠️ DRIFT DETECTED",
    "drift_clean": "✔ SYNCHRONIZED (GOLDEN)",
    "drift_unauth_lines": "Unauthorized Lines:",
    "drift_diff_title": "Unified Differential (Git-Style Diff)",
    "drift_diff_legend": "Green (+): Line added outside template | Red (-): Line removed from Golden Config",
    "filter_cis_aria": "Filter CIS directives",
    "filter_all": "All",
    "filter_isp": "🌐 ISP / Carrier",
    "filter_corporate": "🏢 Corporate",
    "filter_enabled": "✅ Active in Policy",
    "filter_disabled": "⏸️ Excluded",
    "cis_th_active": "Active",
    "cis_th_standards": "Official Standards",
    "link_standard": "📜 Official Standard",
    "link_mikrotik": "📘 MikroTik Docs",
    "status_disabled": "EXCLUDED",
    "status_inactive": "Disabled",
    "modal_remediate_title": "Confirm Tactical CIS Remediation",
    "modal_close": "Close",
    "safemode_shield_title": "60-Second Safe Mode Protection Active",
    "safemode_shield_desc": "If this change interrupts the administrative session with the router, RouterOS will automatically roll back the configuration after 60 seconds.",
    "command_preview_label": "Equivalent CLI / REST Command to Execute on Router:",
    "applying_safemode": "⏳ Applying under Safe Mode...",
    "btn_confirm_safe_remediate": "⚡ Confirm & Apply on Router",
    "modal_policies_title": "Customize Enterprise CIS Security Policies",
    "modal_policies_intro": "Select a predefined profile (ISP, Corporate, or Data Center) or individually enable/disable each directive and adjust its weight in the overall score.",
    "preset_corp_title": "Corporate Enterprise / Finance",
    "preset_corp_desc": "Prioritizes Management VLAN, L2 DHCP Snooping, SNMPv3, MAC-Server lockdown, strong SSH, and encrypted backups.",
    "preset_isp_title": "Internet Service Provider (ISP / WISP / Carrier)",
    "preset_isp_desc": "Prioritizes Bogon/Martians RAW filtering, WAN DNS blocking, BGP MD5/TCP-AO, CPU CoPP, OSPF Auth, and Management VRF.",
    "preset_dc_title": "Maximum Security (Data Center / Mission Critical)",
    "preset_dc_desc": "Enables all 28 directives simultaneously for mission-critical compliance audits.",
    "policies_th_active": "Active",
    "policies_th_code": "Code",
    "policies_th_title": "Directive & Technical Rationale",
    "policies_th_severity": "Severity",
    "policies_th_weight": "Weight (Pts)",
    "policies_th_remediation": "Command Executed on Router",
    "policies_enabled_count": "Active Directives:",
    "policies_total_weight": "Total Active Weight:",
    "policies_saving": "⏳ Saving Policy...",
    "policies_save_btn": "💾 Save Enterprise Policy",
    "switching_intro_desc": "Configure DHCP Snooping individually per Bridge under Safe Mode (60s) or deploy the policy across the entire fleet.",
    "btn_bulk_dhcp_snooping": "Deploy Across Fleet (Bulk Ops)",
    "switching_btn_configure_disable": "⚙️ Configure / Disable",
    "switching_btn_enable_snooping": "⚡ Enable DHCP Snooping",
    "switching_no_trusted_ports": "No ports marked as Trusted",
    "switching_no_untrusted_ports": "No Untrusted ports on this bridge",
    "modal_snooping_title": "Configure DHCP Snooping — Bridge:",
    "modal_snooping_golden_title": "Golden Rule in RouterOS v7 (Trusted Ports):",
    "modal_snooping_golden_desc": "When enabling dhcp-snooping=yes, the bridge drops all DHCP Server messages (DHCPOFFER / DHCPACK) received on untrusted ports. You must mark as Trusted the uplink or trunk port where your legitimate DHCP server resides.",
    "modal_snooping_enable_label": "Enable DHCP Snooping on",
    "modal_snooping_enable_hint": "(Filters unauthorized Layer 2 DHCP responses)",
    "modal_snooping_opt82_label": "Inject DHCP Option 82 (add-dhcp-option82=yes)",
    "modal_snooping_opt82_hint": "— Identifies subscriber circuit and physical port",
    "modal_snooping_trusted_title": "Select Trusted Ports (Uplink / Legitimate DHCP Server):",
    "modal_snooping_no_ports": "This bridge has no member ports registered in /interface/bridge/port yet. Enter the uplink interface name to add it to the bridge as Trusted:",
    "modal_snooping_uplink_placeholder": "E.g. ether1",
    "modal_snooping_port_trusted": "✔ TRUSTED (Uplink / DHCP Server)",
    "modal_snooping_port_untrusted": "🔒 UNTRUSTED (Client Access Port)",
    "modal_snooping_add_trunk_label": "Add additional trunk interface to bridge as Trusted (optional):",
    "modal_snooping_add_trunk_placeholder": "Interface name (e.g. sfp-sfpplus1)",
    "modal_snooping_btn_add_trusted": "+ Add Trusted",
    "modal_snooping_btn_save": "⚡ Save & Apply (Safe Mode 60s)",
    "switching_saved_msg": "DHCP Snooping {state} on {bridge} ({count} Trusted port(s)) under Safe Mode (60s).",
    "switching_enabled_word": "ENABLED",
    "switching_disabled_word": "DISABLED",
    "switching_port_isolated_msg": "Port {port} isolated immediately under Safe Mode (60s).",
    "quick_baseline_sla": "Probe WAN Gateway + Quad9 (9.9.9.9)",
    "sla_target_preset_label": "Suggested Target / Gateway",
    "sla_optgroup_gateways": "🌐 WAN Gateways Detected on Router (/ip/route)",
    "sla_optgroup_dns": "🖧 DNS Servers Configured on Router (/ip/dns)",
    "sla_optgroup_public": "🛡️ Public DNS / Anycast References",
    "sla_option_custom": "✍️ Other Custom IP / Host...",
    "sla_custom_link_name": "Custom Link",
    "sla_anomalies_title": "Traffic Anomaly Detection & 1-Click Mitigation",
    "sla_anomalies_subtitle": "Real-time volumetric monitoring with automated FastDrop to mitigate DoS attacks and anomalies.",
    "sla_btn_mitigating": "Mitigating...",
    "sla_btn_mitigate_fastdrop": "Mitigate Anomaly (FastDrop 300s)",
    "sla_zero_anomalies": "✔ Zero volumetric anomalies detected on the router in the current window.",
    "sla_th_src_ip": "Source IP",
    "sla_th_concurrent_conns": "Concurrent Connections",
    "sla_th_traffic_rate": "Traffic Rate",
    "sla_th_severity": "Severity",
    "sla_th_anomaly_action": "Action",
    "sla_anomaly_fallback": "ANOMALY"
```

#### 1.3. En `cis_directives` (`es.json` y `en.json`):
Extender el objeto `"cis_directives"` en `es.json` y `en.json` para incluir `finding_disabled_by_policy` y, en cada directiva (`CIS_1_1` a `CIS_CORP_8`), las claves `finding_passed` y `finding_failed` (más `finding_failed_prefix` en `CIS_1_1`):

- En `vue3/src/locales/en.json` (reemplazar el bloque `"cis_directives"` completo):
```json
  "cis_directives": {
    "finding_disabled_by_policy": "Directive disabled by operator policy (excluded from score calculation).",
    "CIS_1_1": {
      "title": "Disable unencrypted legacy management services (Telnet, FTP, WWW, plain API)",
      "rationale": "Cleartext protocols expose administrative credentials to passive sniffing on transit networks (MITM).",
      "finding_passed": "All insecure services (telnet, ftp, www, api) are disabled.",
      "finding_failed_prefix": "Insecure services active on router:",
      "finding_failed": "Insecure services active on the router."
    },
    "CIS_1_2": {
      "title": "Audit and disable default 'admin' user account",
      "rationale": "The default 'admin' account is the primary target of automated dictionary and botnet attacks.",
      "finding_passed": "Default 'admin' user is disabled or renamed.",
      "finding_failed": "Default 'admin' user is active on the router."
    },
    "CIS_1_3": {
      "title": "Restrict WinBox, SSH and API-SSL exclusively to authorized management subnets",
      "rationale": "Exposing management ports on 0.0.0.0/0 enables brute-force and zero-day exploitation from the WAN.",
      "finding_passed": "WinBox/SSH/WebFig access is restricted to authorized management subnets.",
      "finding_failed": "WinBox/API service is accessible from any address (0.0.0.0/0)."
    },
    "CIS_1_4": {
      "title": "Disable Open DNS Resolver on WAN interfaces (allow-remote-requests=no or WAN drop)",
      "rationale": "An open DNS resolver allows the router to be abused in DNS amplification DDoS attacks.",
      "finding_passed": "Open DNS Resolver is blocked (allow-remote-requests=no).",
      "finding_failed": "Router is configured as an Open DNS Resolver (allow-remote-requests=yes)."
    },
    "CIS_1_5": {
      "title": "Restrict Neighbor Discovery (MNDP/CDP/LLDP) to trusted management interfaces",
      "rationale": "Prevents leaking BoardName, RouterOS version, MAC, and IP topology details to untrusted L2 segments.",
      "finding_passed": "Neighbor Discovery (MNDP/CDP) is restricted to trusted interfaces or disabled.",
      "finding_failed": "Neighbor Discovery is active on unconfined interfaces."
    },
    "CIS_1_6": {
      "title": "Synchronize RouterBOOT firmware with patched RouterOS v7 release",
      "rationale": "Keeps bootloader and OS microcode aligned against known privilege escalation and CVE vulnerabilities.",
      "finding_passed": "RouterOS v7.14+ and RouterBOOT are synchronized with official security patches.",
      "finding_failed": "RouterOS or RouterBOOT firmware requires security patch synchronization."
    },
    "CIS_1_7": {
      "title": "Filter Bogon and spoofing prefixes (RFC 1918 / RFC 6890) on WAN ingress",
      "rationale": "Blocks packets with forged private or unallocated source IPs entering from external transit links.",
      "finding_passed": "Bogon / RFC 1918 filtering rules are present in RAW or Filter.",
      "finding_failed": "Missing Bogon / RFC 1918 filtering rules in IP Firewall Filter or RAW."
    },
    "CIS_1_8": {
      "title": "Active 3-stage dynamic blacklist defense against SSH/WinBox Brute-Force",
      "rationale": "Automatically jails offending source IPs attempting repeated authentication failures on management ports.",
      "finding_passed": "Active 3-stage blacklist defense against Brute-Force attacks is configured in Firewall Filter.",
      "finding_failed": "Missing 3-stage dynamic blacklists against Brute-Force attacks."
    },
    "CIS_1_9": {
      "title": "Enforce modern cryptographic suites (AES-256-GCM / SHA256 / DH Group 14+)",
      "rationale": "Eliminates weak legacy ciphers (3DES, MD5, SHA1, MODP-1024) vulnerable to cryptographic downgrade.",
      "finding_passed": "IPsec / WireGuard profiles enforce AES-256 and modern cipher suites.",
      "finding_failed": "Weak encryption detected in VPN profiles."
    },
    "CIS_1_10": {
      "title": "Isolate management plane in a dedicated Management VLAN",
      "rationale": "Segregates administrative control traffic from subscriber and corporate user data planes.",
      "finding_passed": "Administrative management is isolated in a dedicated VLAN.",
      "finding_failed": "No dedicated management VLAN interface detected (e.g., mgmt or vlan99)."
    },
    "CIS_2_1": {
      "title": "Cryptographic protection for BGP sessions (TCP-MD5 / TCP-AO)",
      "rationale": "Prevents unauthorized BGP session resets (RST spoofing) and route injection by unauthorized peers.",
      "finding_passed": "BGP session protection with TCP-AO/MD5 authentication verified.",
      "finding_failed": "BGP sessions lack TCP-MD5/TCP-AO cryptographic authentication."
    },
    "CIS_2_2": {
      "title": "Selective FastTrack preserving Simple Queues and QoS Queue Trees",
      "rationale": "Unconditional FastTrack bypasses mangle and queue trees, breaking subscriber bandwidth shaping.",
      "finding_passed": "Selective FastTrack implemented while preserving QoS queue trees.",
      "finding_failed": "FastTrack bypasses queue trees or lacks marked traffic exclusion."
    },
    "CIS_ISP_1": {
      "title": "Drop Bogons / Martians in Firewall RAW prerouting (BCP 38 / RFC 2827)",
      "rationale": "Discards invalid and spoofed source prefixes before connection tracking to protect router CPU.",
      "finding_passed": "Bogon / Martians filtering is active in RAW prerouting chain.",
      "finding_failed": "Missing Bogon / Martians drop rules in RAW for WAN interfaces."
    },
    "CIS_ISP_2": {
      "title": "Block external UDP/TCP 53 requests in WAN RAW to prevent DNS Amplification",
      "rationale": "Protects ISP infrastructure from acting as an involuntay reflector in volumetric DNS amplification attacks.",
      "finding_passed": "WAN Open DNS Resolver protection verified.",
      "finding_failed": "Port 53 (DNS) is exposed on WAN interface without filtering."
    },
    "CIS_ISP_3": {
      "title": "Mandatory BGP Peering authentication & prefix filter lists",
      "rationale": "Ensures routing table integrity across eBGP/iBGP peers in carrier topologies.",
      "finding_passed": "Cryptographic MD5/TCP-AO authentication present on BGP peers.",
      "finding_failed": "BGP connections detected without TCP-MD5 or TCP-AO authentication."
    },
    "CIS_ISP_4": {
      "title": "Control Plane Policing (CoPP) — ICMP/UDP/SYN Flood protection towards router CPU",
      "rationale": "Rate-limits control plane packets in the input chain so transit floods cannot exhaust CPU resources.",
      "finding_passed": "CoPP rate limits configured to protect control plane and CPU.",
      "finding_failed": "No rate-limiting (CoPP) rules detected in input chain."
    },
    "CIS_ISP_5": {
      "title": "Bind management services exclusively to Out-of-Band Management VRF",
      "rationale": "Isolates SSH, WinBox, and API sockets from the global routing table used by subscribers.",
      "finding_passed": "Administrative services isolated in Management VRF.",
      "finding_failed": "Management services are bound to the global routing table."
    },
    "CIS_ISP_6": {
      "title": "Cryptographic authentication (SHA-256 / MD5) on OSPF v2/v3 backbone interfaces",
      "rationale": "Prevents rogue OSPF adjacency formation and internal LSA poisoning on backbone links.",
      "finding_passed": "OSPF cryptographic authentication (SHA-256 or MD5) is active.",
      "finding_failed": "OSPF templates are operating without strong cryptographic authentication."
    },
    "CIS_ISP_7": {
      "title": "Disable ICMP Redirects (send-redirects=no) and IP Source Route",
      "rationale": "Prevents attackers from manipulating host routing tables via forged ICMP Redirect packets.",
      "finding_passed": "ICMP Redirects suppressed in IP Settings to mitigate MITM attacks.",
      "finding_failed": "Option send-redirects is enabled in general IP settings."
    },
    "CIS_ISP_8": {
      "title": "Disable auxiliary Web Proxy and SOCKS services (/ip/proxy and /ip/socks)",
      "rationale": "Prevents unauthorized open proxy abuse and traffic laundering through the router.",
      "finding_passed": "Auxiliary Web Proxy and SOCKS servers are disabled.",
      "finding_failed": "Web Proxy or SOCKS server is active without authorization."
    },
    "CIS_CORP_1": {
      "title": "Disable Bandwidth-Test Server (/tool/bandwidth-server) in production",
      "rationale": "Bandwidth-test can saturate link capacity and CPU if left enabled in production environments.",
      "finding_passed": "Bandwidth-Test server (btest) is disabled.",
      "finding_failed": "Bandwidth-Test server is enabled (CPU exhaustion risk)."
    },
    "CIS_CORP_2": {
      "title": "Disable MAC-Telnet, MAC-WinBox and MAC-Ping on access interfaces",
      "rationale": "Blocks Layer-2 administrative access from untrusted corporate LAN or guest switch ports.",
      "finding_passed": "MAC-Server and MAC-WinBox are restricted or confined outside access ports.",
      "finding_failed": "MAC-Server is active across all switching interfaces."
    },
    "CIS_CORP_3": {
      "title": "Enforce SSH Strong Crypto (strong-crypto=yes) and disable SSH Forwarding",
      "rationale": "Mandates modern key exchange and ciphers while blocking unauthorized SSH port tunneling.",
      "finding_passed": "SSH is hardened with strong cryptography (strong-crypto=yes).",
      "finding_failed": "SSH allows weak cryptographic algorithms or open password access."
    },
    "CIS_CORP_4": {
      "title": "Enable DHCP Snooping & Option 82 on corporate LAN Bridges",
      "rationale": "Drops unauthorized DHCP offers from rogue devices connected to access ports.",
      "finding_passed": "DHCP Snooping is active on bridges to eradicate Rogue DHCP servers.",
      "finding_failed": "DHCP Snooping is disabled on access bridges."
    },
    "CIS_CORP_5": {
      "title": "Enforce SNMPv3 with SHA/AES encryption and disable v1/v2c public communities",
      "rationale": "Protects network telemetry and MIB trees from cleartext community string interception.",
      "finding_passed": "SNMPv3 USM with encryption is implemented (public v1/v2c communities eradicated).",
      "finding_failed": "SNMP v1/v2c communities are active without payload encryption."
    },
    "CIS_CORP_6": {
      "title": "Comprehensive audit streaming to Centralized Syslog (account, system,info, firewall,info)",
      "rationale": "Guarantees real-time streaming of authentication records, configuration modifications, and firewall drops.",
      "finding_passed": "Syslog audit forwarding for configuration and account events verified.",
      "finding_failed": "Missing logging rules for account or system,info topics towards RoSGrid Syslog."
    },
    "CIS_CORP_7": {
      "title": "Disable RoMON and discovery protocols (MNDP/CDP/LLDP) on user segments",
      "rationale": "RoMON enables out-of-band L2 bridging and discovery; must remain deactivated on untrusted user segments.",
      "finding_passed": "RoMON protocol is disabled on user interfaces.",
      "finding_failed": "RoMON is active without segment isolation."
    },
    "CIS_CORP_8": {
      "title": "Mandatory AES-256 encryption on binary backups and exports",
      "rationale": "Router backups contain credentials and network secrets; mandatory AES encryption prevents unauthorized exfiltration.",
      "finding_passed": "Automated binary backups are scheduled with AES-256 encryption.",
      "finding_failed": "No scheduled encrypted backup tasks detected."
    }
  },
```
*(En `vue3/src/locales/es.json`, añadir las mismas subclaves `finding_disabled_by_policy`, `finding_passed`, `finding_failed_prefix` y `finding_failed` con los textos en español correspondientes de `compliance.py`).*

#### 1.4. Añadir los bloques `"notifications_channels"` y `"diagnostics_siem"` en `es.json` y `en.json`:

- En `vue3/src/locales/es.json`:
```json
  "notifications_channels": {
    "title": "Canales de Alerta y Notificación Multi-Canal",
    "subtitle": "Configure bots de Telegram, servidores de correo SMTP y Webhooks HTTP para recibir alertas críticas del NOC en tiempo real (Offline, Degradación, TOFU SSL, Drift).",
    "btn_new_channel": "+ Nuevo Canal de Alerta",
    "loading_channels": "Cargando canales de alerta configurados...",
    "empty_title": "No hay canales de notificación configurados",
    "empty_desc": "Cree un canal de Telegram, Servidor SMTP o Webhook para recibir alarmas críticas en tiempo real.",
    "btn_configure_first": "+ Configurar Primer Canal",
    "status_active": "● ACTIVO",
    "status_inactive": "○ INACTIVO",
    "badge_telegram": "📱 Telegram Bot",
    "badge_smtp": "✉️ Correo SMTP",
    "badge_webhook": "🔗 Webhook HTTP",
    "label_chat_id": "Chat ID:",
    "label_bot_token": "Bot Token:",
    "token_encrypted_aes": "🔒 Cifrado en Vault (AES-256-GCM)",
    "unconfigured": "Sin configurar",
    "label_smtp_server": "Servidor SMTP:",
    "label_sender": "Remitente:",
    "label_recipients": "Destinatarios:",
    "label_endpoint": "Endpoint:",
    "label_Subscribed_events": "Eventos Suscritos",
    "label_registered": "Registrado:",
    "btn_test": "🧪 Probar",
    "btn_test_title": "Enviar mensaje de prueba a este canal",
    "btn_edit": "✏️ Editar",
    "btn_edit_title": "Editar configuración del canal",
    "btn_disable": "⏸ Desactivar",
    "btn_enable": "▶ Activar",
    "btn_delete_title": "Eliminar canal",
    "modal_edit_title": "✏️ Editar Canal de Notificación",
    "modal_create_title": "➕ Configurar Nuevo Canal de Notificación",
    "field_name": "Nombre del Canal *",
    "field_name_placeholder": "Ej: Canal Telegram Guardia NOC",
    "field_type": "Tipo de Notificación *",
    "option_telegram": "📱 Bot de Telegram",
    "option_smtp": "✉️ Servidor de Correo SMTP",
    "option_webhook": "🔗 Webhook HTTP (JSON Post)",
    "field_bot_token": "Bot Token de Telegram *",
    "keep_current_secret_placeholder": "(Sin cambios — se conserva el secreto cifrado actual)",
    "hint_keep_token": "Dejar en blanco para conservar el Bot Token cifrado actual.",
    "hint_botfather": "Token proporcionado por @BotFather. Se almacenará cifrado con AES-256-GCM.",
    "field_chat_id": "Chat ID o Canal *",
    "field_smtp_host": "Host SMTP *",
    "field_port": "Puerto",
    "field_smtp_user": "Usuario SMTP",
    "field_smtp_pass": "Contraseña SMTP",
    "field_smtp_from": "Remitente (From)",
    "field_smtp_to": "Destinatarios (Separados por coma)",
    "field_webhook_url": "URL del Webhook (HTTPS) *",
    "field_webhook_auth": "Cabecera de Autorización (Opcional)",
    "field_events_legend": "Eventos Suscritos",
    "field_enable_immediately": "Habilitar canal inmediatamente al guardar",
    "btn_saving": "Guardando...",
    "btn_update_channel": "💾 Actualizar Canal",
    "btn_save_encrypt": "🔒 Guardar y Cifrar Canal",
    "modal_test_title": "🧪 Probar Canal:",
    "modal_test_desc": "Se enviará una carga útil de prueba real al destino configurado para certificar la conectividad.",
    "field_test_message": "Mensaje de Prueba",
    "default_test_message": "🔔 Prueba operativa de canal de alerta desde RoSGrid NOC.",
    "dispatch_success": "Despacho Exitoso",
    "dispatch_error": "Error en Despacho",
    "btn_sending": "Enviando...",
    "btn_dispatch_test": "🚀 Despachar Prueba",
    "confirm_delete": "¿Eliminar permanentemente el canal \"{name}\"?",
    "err_load": "Error al cargar canales de notificación.",
    "err_name_required": "El nombre del canal es obligatorio.",
    "err_save": "Error al guardar el canal de notificación.",
    "err_toggle": "No se pudo actualizar el estado del canal.",
    "err_delete": "Error al eliminar el canal.",
    "err_test": "Fallo al despachar notificación de prueba.",
    "events": {
      "ROUTER_OFFLINE": "Router Fuera de Línea (Offline)",
      "ROUTER_ONLINE": "Router Reconectado (Online)",
      "DEGRADED_HIGH_LOAD": "Carga Crítica de CPU / Memoria",
      "SSL_MISMATCH": "Discrepancia de Certificado TLS",
      "CONFIG_DRIFT_DETECTED": "Deriva de Configuración (Drift)",
      "ROGUE_DHCP_DETECTED": "DHCP no Autorizado / Ataque L2"
    }
  },
  "diagnostics_siem": {
    "ring_buffer_badge": "Ring Buffer UI: {count} eventos",
    "field_archive_format": "Formato de Archivo",
    "option_zip": ".zip (Estándar Windows / Linux / macOS)",
    "option_targz": ".tar.gz (Tarball Gzip Linux / Unix)",
    "field_log_lines": "Líneas de Log Backend",
    "field_operator_notes": "Notas del Operador / Descripción de la Falla",
    "field_operator_notes_placeholder": "Describa los pasos previos al incidente para el equipo de ingeniería...",
    "btn_bundling": "⏳ Empaquetando y Sanitizando...",
    "btn_download_bundle": "📦 Descargar Paquete de Diagnóstico (.{format})",
    "summary_file": "Archivo:",
    "summary_redacted": "Secretos Sanitizados:",
    "summary_artifacts": "Artefactos Incluidos:",
    "siem_enabled": "Habilitado",
    "siem_disabled": "Deshabilitado",
    "field_protocol": "Protocolo del Colector SIEM",
    "field_min_severity": "Severidad Mínima",
    "field_host": "Host / IP del Servidor SIEM del ISP",
    "field_port": "Puerto",
    "field_stream_label": "Etiqueta de Instancia / Stream",
    "field_http_path": "Ruta HTTP (GELF_HTTP / LOKI_HTTP)",
    "field_bearer_token": "Token Bearer Opcional",
    "token_configured_hint": "(Token configurado)",
    "token_keep_placeholder": "Dejar en blanco para conservar el token actual",
    "check_include_ui_errors": "Incluir errores de interfaz (Frontend UI)",
    "check_include_audit": "Incluir eventos de auditoría administrativa",
    "check_use_tls": "Usar TLS (HTTPS)",
    "btn_saving_siem": "⏳ Guardando...",
    "btn_save_siem": "💾 Guardar Configuración SIEM",
    "btn_testing_siem": "⏳ Probando...",
    "btn_test_siem": "🧪 Enviar Log de Prueba",
    "test_result_label": "Resultado Prueba ({protocol}):",
    "msg_bundle_generated": "Paquete {filename} generado ({redacted} secretos sanitizados).",
    "err_bundle_generate": "No se pudo generar el paquete de soporte.",
    "msg_siem_saved": "Configuración del conector SIEM guardada correctamente.",
    "err_siem_save": "Error al guardar la configuración SIEM.",
    "err_siem_test": "Error al probar el envío al servidor SIEM."
  }
```

- En `vue3/src/locales/en.json`:
```json
  "notifications_channels": {
    "title": "Multi-Channel Alert & Notification Channels",
    "subtitle": "Configure Telegram bots, SMTP mail servers, and HTTP Webhooks to receive real-time critical NOC alerts (Offline, Degradation, SSL TOFU, Config Drift).",
    "btn_new_channel": "+ New Alert Channel",
    "loading_channels": "Loading configured alert channels...",
    "empty_title": "No notification channels configured",
    "empty_desc": "Create a Telegram channel, SMTP Server, or Webhook to receive critical real-time alarms.",
    "btn_configure_first": "+ Configure First Channel",
    "status_active": "● ACTIVE",
    "status_inactive": "○ INACTIVE",
    "badge_telegram": "📱 Telegram Bot",
    "badge_smtp": "✉️ SMTP Email",
    "badge_webhook": "🔗 HTTP Webhook",
    "label_chat_id": "Chat ID:",
    "label_bot_token": "Bot Token:",
    "token_encrypted_aes": "🔒 Encrypted in Vault (AES-256-GCM)",
    "unconfigured": "Unconfigured",
    "label_smtp_server": "SMTP Server:",
    "label_sender": "Sender:",
    "label_recipients": "Recipients:",
    "label_endpoint": "Endpoint:",
    "label_Subscribed_events": "Subscribed Events",
    "label_registered": "Registered:",
    "btn_test": "🧪 Test",
    "btn_test_title": "Send a test message to this channel",
    "btn_edit": "✏️ Edit",
    "btn_edit_title": "Edit channel configuration",
    "btn_disable": "⏸ Disable",
    "btn_enable": "▶ Enable",
    "btn_delete_title": "Delete channel",
    "modal_edit_title": "✏️ Edit Notification Channel",
    "modal_create_title": "➕ Configure New Notification Channel",
    "field_name": "Channel Name *",
    "field_name_placeholder": "E.g. NOC On-Call Telegram Channel",
    "field_type": "Notification Type *",
    "option_telegram": "📱 Telegram Bot",
    "option_smtp": "✉️ SMTP Mail Server",
    "option_webhook": "🔗 HTTP Webhook (JSON Post)",
    "field_bot_token": "Telegram Bot Token *",
    "keep_current_secret_placeholder": "(Unchanged — keeps current encrypted secret)",
    "hint_keep_token": "Leave blank to keep the current encrypted Bot Token.",
    "hint_botfather": "Token provided by @BotFather. Stored encrypted with AES-256-GCM.",
    "field_chat_id": "Chat ID or Channel *",
    "field_smtp_host": "SMTP Host *",
    "field_port": "Port",
    "field_smtp_user": "SMTP User",
    "field_smtp_pass": "SMTP Password",
    "field_smtp_from": "Sender (From)",
    "field_smtp_to": "Recipients (Comma-separated)",
    "field_webhook_url": "Webhook URL (HTTPS) *",
    "field_webhook_auth": "Authorization Header (Optional)",
    "field_events_legend": "Subscribed Events",
    "field_enable_immediately": "Enable channel immediately upon saving",
    "btn_saving": "Saving...",
    "btn_update_channel": "💾 Update Channel",
    "btn_save_encrypt": "🔒 Save & Encrypt Channel",
    "modal_test_title": "🧪 Test Channel:",
    "modal_test_desc": "A live test payload will be dispatched to the configured destination to certify connectivity.",
    "field_test_message": "Test Message",
    "default_test_message": "🔔 Operational alert channel test from RoSGrid NOC.",
    "dispatch_success": "Dispatch Successful",
    "dispatch_error": "Dispatch Failed",
    "btn_sending": "Sending...",
    "btn_dispatch_test": "🚀 Dispatch Test",
    "confirm_delete": "Permanently delete channel \"{name}\"?",
    "err_load": "Failed to load notification channels.",
    "err_name_required": "Channel name is required.",
    "err_save": "Failed to save notification channel.",
    "err_toggle": "Failed to update channel status.",
    "err_delete": "Failed to delete channel.",
    "err_test": "Failed to dispatch test notification.",
    "events": {
      "ROUTER_OFFLINE": "Router Offline (Unreachable)",
      "ROUTER_ONLINE": "Router Reconnected (Online)",
      "DEGRADED_HIGH_LOAD": "Critical CPU / Memory Load",
      "SSL_MISMATCH": "TLS Certificate Mismatch",
      "CONFIG_DRIFT_DETECTED": "Configuration Drift Detected",
      "ROGUE_DHCP_DETECTED": "Unauthorized DHCP / L2 Attack"
    }
  },
  "diagnostics_siem": {
    "ring_buffer_badge": "UI Ring Buffer: {count} events",
    "field_archive_format": "Archive Format",
    "option_zip": ".zip (Standard Windows / Linux / macOS)",
    "option_targz": ".tar.gz (Linux / Unix Gzip Tarball)",
    "field_log_lines": "Backend Log Lines",
    "field_operator_notes": "Operator Notes / Incident Description",
    "field_operator_notes_placeholder": "Describe the steps leading up to the incident for the engineering team...",
    "btn_bundling": "⏳ Packaging & Sanitizing...",
    "btn_download_bundle": "📦 Download Diagnostic Bundle (.{format})",
    "summary_file": "File:",
    "summary_redacted": "Sanitized Secrets:",
    "summary_artifacts": "Included Artifacts:",
    "siem_enabled": "Enabled",
    "siem_disabled": "Disabled",
    "field_protocol": "SIEM Collector Protocol",
    "field_min_severity": "Minimum Severity",
    "field_host": "ISP SIEM Server Host / IP",
    "field_port": "Port",
    "field_stream_label": "Instance / Stream Label",
    "field_http_path": "HTTP Path (GELF_HTTP / LOKI_HTTP)",
    "field_bearer_token": "Optional Bearer Token",
    "token_configured_hint": "(Token configured)",
    "token_keep_placeholder": "Leave blank to keep current token",
    "check_include_ui_errors": "Include frontend UI errors",
    "check_include_audit": "Include administrative audit events",
    "check_use_tls": "Use TLS (HTTPS)",
    "btn_saving_siem": "⏳ Saving...",
    "btn_save_siem": "💾 Save SIEM Configuration",
    "btn_testing_siem": "⏳ Testing...",
    "btn_test_siem": "🧪 Send Test Log",
    "test_result_label": "Test Result ({protocol}):",
    "msg_bundle_generated": "Bundle {filename} generated ({redacted} secrets sanitized).",
    "err_bundle_generate": "Could not generate support diagnostic bundle.",
    "msg_siem_saved": "SIEM connector configuration saved successfully.",
    "err_siem_save": "Failed to save SIEM configuration.",
    "err_siem_test": "Failed to send test log to SIEM server."
  }
```

---

### Paso 2: Actualizar `vue3/src/views/EnterpriseComplianceView.vue`

1. **En `<script setup>` (junto a `getDirectiveRationale`, alrededor de la línea 1020):**
   Añadir la función `getDirectiveFinding`:
```ts
  function getDirectiveFinding(d: {
    code: string;
    finding: string;
    passed: boolean;
    enabled?: boolean;
  }): string {
    if (d.enabled === false) {
      return t(
        'cis_directives.finding_disabled_by_policy',
        d.finding ||
          'Directiva desactivada por política del operador (excluida del cálculo de puntuación).',
      );
    }
    const codeKey = getDirectiveCodeKey(d.code);
    if (d.passed) {
      return t(`cis_directives.${codeKey}.finding_passed`, d.finding);
    }
    if (d.code === 'CIS-1.1' && d.finding && d.finding.includes(':')) {
      const servicesPart = d.finding.split(':').slice(1).join(':').trim();
      const prefix = t(
        'cis_directives.CIS_1_1.finding_failed_prefix',
        'Servicios inseguros activos en el router:',
      );
      return `${prefix} ${servicesPart}`;
    }
    return t(`cis_directives.${codeKey}.finding_failed`, d.finding);
  }
```
2. **En la tabla de CIS Hardening (`línea 1521` de `EnterpriseComplianceView.vue`):**
   Reemplazar:
```html
                <td class="finding-cell">{{ d.finding }}</td>
```
   por:
```html
                <td class="finding-cell">{{ getDirectiveFinding(d) }}</td>
```
3. **En la pestaña Seguridad L2 & Rogue DHCP (`líneas 1974–2145` de `EnterpriseComplianceView.vue`):**
   Reemplazar los textos hardcodeados en español por sus llamadas `t('enterprise.*')`:
   - Línea 1975: `{{ t('enterprise.switching_intro_desc', 'Configure DHCP Snooping individualmente por Bridge bajo Safe Mode (60s) o despliegue la política en toda la flota.') }}`
   - Líneas 2009–2010: `{{ sw.dhcp_snooping_enabled ? t('enterprise.switching_btn_configure_disable', '⚙️ Configurar / Desactivar') : t('enterprise.switching_btn_enable_snooping', '⚡ Activar DHCP Snooping') }}`
   - Línea 2022: `{{ t('enterprise.switching_no_trusted_ports', 'Ningún puerto marcado como Trusted') }}`
   - Línea 2034: `{{ t('enterprise.switching_no_untrusted_ports', 'Sin puertos Untrusted en este bridge') }}`
   - Modal `#modal-dhcp-snooping-config` (líneas 2053–2139): envolver el título, la caja de Regla de Oro, los checkboxes (`modal_snooping_enable_label`, `modal_snooping_enable_hint`, `modal_snooping_opt82_label`, `modal_snooping_opt82_hint`), los badges (`modal_snooping_port_trusted`, `modal_snooping_port_untrusted`), el input de interfaz troncal y el botón `#btn-save-dhcp-snooping` (`modal_snooping_btn_save`) con `t('enterprise.*')`.
4. **En la pestaña Telemetría de SLA (`líneas 2289–2423` de `EnterpriseComplianceView.vue`):**
   - En `<select id="sla-target-preset">` (líneas 2290–2322): usar `:label="t('enterprise.sla_optgroup_gateways', '🌐 Gateways WAN Detectados en Router (/ip/route)')"`, `:label="t('enterprise.sla_optgroup_dns', '🖧 DNS Configurados en Router (/ip/dns)')"`, `:label="t('enterprise.sla_optgroup_public', '🛡️ Referencias Públicas DNS / Anycast')"` y `{{ t('enterprise.sla_option_custom', '✍️ Otra IP / Host Personalizado...') }}`.
   - En la tarjeta de Anomalías de Tráfico (líneas 2365–2422):
     - Título: `🚨 {{ t('enterprise.sla_anomalies_title', 'Detección de Anomalías de Tráfico & Mitigación en 1 Clic') }}`
     - Subtítulo: `{{ t('enterprise.sla_anomalies_subtitle', 'Monitoreo volumétrico en tiempo real con FastDrop automático para mitigar ataques DoS / anomalías.') }}`
     - Botón `#btn-mitigate-traffic-anomaly`: `{{ isMitigatingTraffic ? t('enterprise.sla_btn_mitigating', 'Mitigando...') : t('enterprise.sla_btn_mitigate_fastdrop', 'Mitigar Anomalía (FastDrop 300s)') }}`
     - Estado vacío: `{{ t('enterprise.sla_zero_anomalies', '✔ Cero anomalías volumétricas detectadas en el router en la ventana actual.') }}`
     - Encabezados `<th>`: `{{ t('enterprise.sla_th_src_ip', 'IP Origen') }}`, `{{ t('enterprise.sla_th_concurrent_conns', 'Conexiones Concurrentes') }}`, `{{ t('enterprise.sla_th_traffic_rate', 'Tasa de Tráfico') }}`, `{{ t('enterprise.sla_th_severity', 'Severidad') }}`, `{{ t('enterprise.sla_th_anomaly_action', 'Acción') }}`.

---

### Paso 3: Actualizar `vue3/src/components/operations/NotificationChannelsPanel.vue`

1. Convertir `availableEvents` en un `computed` reactivo al idioma:
```ts
  const availableEvents = computed(() => [
    {
      code: 'ROUTER_OFFLINE',
      label: t('notifications_channels.events.ROUTER_OFFLINE', 'Router Fuera de Línea (Offline)'),
    },
    {
      code: 'ROUTER_ONLINE',
      label: t('notifications_channels.events.ROUTER_ONLINE', 'Router Reconectado (Online)'),
    },
    {
      code: 'DEGRADED_HIGH_LOAD',
      label: t(
        'notifications_channels.events.DEGRADED_HIGH_LOAD',
        'Carga Crítica de CPU / Memoria',
      ),
    },
    {
      code: 'SSL_MISMATCH',
      label: t('notifications_channels.events.SSL_MISMATCH', 'Discrepancia de Certificado TLS'),
    },
    {
      code: 'CONFIG_DRIFT_DETECTED',
      label: t(
        'notifications_channels.events.CONFIG_DRIFT_DETECTED',
        'Deriva de Configuración (Drift)',
      ),
    },
    {
      code: 'ROGUE_DHCP_DETECTED',
      label: t(
        'notifications_channels.events.ROGUE_DHCP_DETECTED',
        'DHCP no Autorizado / Ataque L2',
      ),
    },
  ]);
```
2. Actualizar `getChannelTypeBadge` y `getEventLabel` para usar `t('notifications_channels.*')`:
```ts
  const getChannelTypeBadge = (type: NotificationChannelType) => {
    switch (type) {
      case 'TELEGRAM_BOT':
        return {
          label: t('notifications_channels.badge_telegram', '📱 Telegram Bot'),
          css: 'badge-telegram',
        };
      case 'SMTP_EMAIL':
        return {
          label: t('notifications_channels.badge_smtp', '✉️ Correo SMTP'),
          css: 'badge-smtp',
        };
      case 'WEBHOOK_HTTP':
        return {
          label: t('notifications_channels.badge_webhook', '🔗 Webhook HTTP'),
          css: 'badge-webhook',
        };
    }
  };

  const getEventLabel = (code: string) => {
    const found = availableEvents.value.find((e) => e.code === code);
    return found ? found.label : code;
  };
```
3. Reemplazar todas las cadenas en español del `<template>` (tarjetas de canal, estado vacío, modal de crear/editar canal y modal de prueba de despacho) por sus claves `t('notifications_channels.*')` definidas en el Paso 1.4.

---

### Paso 4: Actualizar `vue3/src/components/operations/DiagnosticsAndSiemPanel.vue`

Reemplazar todas las cadenas hardcodeadas en español del `<template>` y `<script setup>` por sus equivalentes con `t('diagnostics_siem.*')`:
- Badge: `{{ t('diagnostics_siem.ring_buffer_badge', { count: uiDiagnosticBuffer.length }) }}`
- Etiquetas de Paquete de Soporte: `t('diagnostics_siem.field_archive_format')`, `t('diagnostics_siem.option_zip')`, `t('diagnostics_siem.option_targz')`, `t('diagnostics_siem.field_log_lines')`, `t('diagnostics_siem.field_operator_notes')`, `:placeholder="t('diagnostics_siem.field_operator_notes_placeholder')"`, botón `#btn-download-support-bundle` con `isBundling ? t('diagnostics_siem.btn_bundling') : t('diagnostics_siem.btn_download_bundle', { format: bundleFormat })`, y resumen `bundle-summary` (`summary_file`, `summary_redacted`, `summary_artifacts`).
- Etiquetas de Conector SIEM: toggle `siemEnabled ? t('diagnostics_siem.siem_enabled') : t('diagnostics_siem.siem_disabled')`, `field_protocol`, `field_min_severity`, `field_host`, `field_port`, `field_stream_label`, `field_http_path`, `field_bearer_token`, `token_configured_hint`, `:placeholder="siemConfig?.has_auth_token ? t('diagnostics_siem.token_keep_placeholder') : 'eyJhbGciOi...'"`, checkboxes (`check_include_ui_errors`, `check_include_audit`, `check_use_tls`), botones `#btn-save-siem-config` y `#btn-test-siem-config`, y caja `siem-test-result` (`t('diagnostics_siem.test_result_label', { protocol: siemTestResult.protocol })`).

---

## 3. Creación y Ejecución Obligatoria de Pruebas Nivel 11X

### 3.1. Pruebas Unitarias en `vue3/src/views/enterpriseComplianceView.unit.ts`
Añadir al final de `vue3/src/views/enterpriseComplianceView.unit.ts` un test que cambie el idioma activo a inglés (`setLocale('en')` desde `@/i18n`) y verifique que las pestañas **CIS Hardening**, **L2 Security & Rogue DHCP** y **SLA Telemetry** rendericen el 100% de sus etiquetas, hallazgos técnicos (`d.finding`) y modales en inglés (cero textos residuales en español):

```ts
  it('traduce completamente al inglés CIS Hardening (incluyendo hallazgos d.finding), L2 Security & Rogue DHCP y SLA Telemetry al activar locale en (Hito 30.16 - Spec 93)', async () => {
    const { setLocale } = await import('@/i18n');
    setLocale('en');

    try {
      const wrapper = mount(EnterpriseComplianceView);

      // 1. Verificar pestaña CIS Hardening en inglés
      await wrapper.find('#tab-btn-cis').trigger('click');
      await vi.waitFor(() => {
        expect(wrapper.text()).toContain('Overall CIS Security Compliance Score');
      });
      expect(wrapper.text()).toContain('Customize Enterprise Policies');
      expect(wrapper.text()).toContain('Active in Policy');
      expect(wrapper.text()).toContain('Official Standards');
      // El hallazgo técnico de CIS-1.1 / CIS-1.2 debe mostrarse traducido al inglés
      expect(wrapper.text()).not.toContain('Servicios inseguros activos en el router');

      // 2. Verificar pestaña L2 Security & Rogue DHCP en inglés
      await wrapper.find('#tab-btn-switching').trigger('click');
      await vi.waitFor(() => {
        expect(wrapper.text()).toContain('Deploy Across Fleet (Bulk Ops)');
      });
      expect(wrapper.text()).toContain(
        'Configure DHCP Snooping individually per Bridge under Safe Mode (60s)',
      );
      expect(wrapper.text()).toContain('Unauthorized DHCP Servers Detected (Rogue DHCP)');

      // 3. Verificar pestaña SLA Telemetry & Traffic Anomalies en inglés
      await wrapper.find('#tab-btn-sla').trigger('click');
      await vi.waitFor(() => {
        expect(wrapper.text()).toContain('Traffic Anomaly Detection & 1-Click Mitigation');
      });
      expect(wrapper.text()).toContain('Probe WAN Gateway + Quad9 (9.9.9.9)');
      expect(wrapper.text()).toContain('Suggested Target / Gateway');
      expect(wrapper.text()).toContain('Mitigate Anomaly (FastDrop 300s)');
    } finally {
      setLocale('es');
    }
  });
```

### 3.2. Pruebas Unitarias en `vue3/src/components/operations/NotificationChannelsPanel.unit.ts`
Añadir un test en `NotificationChannelsPanel.unit.ts` verificando la traducción completa al inglés:

```ts
  it('renderiza todos los textos, insignias, eventos y modales en inglés cuando el locale es en (Hito 30.16 - Spec 93)', async () => {
    const { setLocale } = await import('@/i18n');
    setLocale('en');

    try {
      vi.spyOn(http, 'get').mockResolvedValueOnce({
        data: mockChannels,
        status: 200,
        headers: new Headers(),
      } as unknown as ApiResponse);

      const wrapper = mount(NotificationChannelsPanel);
      await flushPromises();

      expect(wrapper.text()).toContain('Multi-Channel Alert & Notification Channels');
      expect(wrapper.text()).toContain('+ New Alert Channel');
      expect(wrapper.text()).toContain('● ACTIVE');
      expect(wrapper.text()).toContain('○ INACTIVE');
      expect(wrapper.text()).toContain('Router Offline (Unreachable)');
      expect(wrapper.text()).toContain('Encrypted in Vault (AES-256-GCM)');

      // Abrir modal de edición y verificar etiquetas en inglés
      await wrapper.find(`#btn-edit-channel-${CH_TELEGRAM_ID}`).trigger('click');
      expect(wrapper.find('#create-channel-title').text()).toContain('Edit Notification Channel');
      expect(wrapper.text()).toContain('Channel Name *');
      expect(wrapper.text()).toContain('Update Channel');
    } finally {
      setLocale('es');
    }
  });
```

### 3.3. Pruebas Unitarias en `vue3/src/components/operations/DiagnosticsAndSiemPanel.unit.ts`
Añadir un test en `DiagnosticsAndSiemPanel.unit.ts` verificando la traducción completa al inglés:

```ts
  it('renderiza el formulario de paquete de diagnóstico y el conector SIEM completamente en inglés cuando el locale es en (Hito 30.16 - Spec 93)', async () => {
    const { setLocale } = await import('@/i18n');
    setLocale('en');

    try {
      const wrapper = mount(DiagnosticsAndSiemPanel);
      await flushPromises();

      expect(wrapper.text()).toContain('Unified Support & Diagnostic Bundle (1-Click Bundle)');
      expect(wrapper.text()).toContain('Archive Format');
      expect(wrapper.text()).toContain('Backend Log Lines');
      expect(wrapper.text()).toContain('Operator Notes / Incident Description');
      expect(wrapper.text()).toContain('Download Diagnostic Bundle (.zip)');
      expect(wrapper.text()).toContain('ISP SIEM Connector (Graylog / Grafana Loki / Syslog)');
      expect(wrapper.text()).toContain('SIEM Collector Protocol');
      expect(wrapper.text()).toContain('Minimum Severity');
      expect(wrapper.text()).toContain('Save SIEM Configuration');
      expect(wrapper.text()).toContain('Send Test Log');
    } finally {
      setLocale('es');
    }
  });
```

### 3.4. Escenario Karate Labs BDD (`vue3/test/ui_business_flow.feature` y `docs/examples/vue3/ui_business_flow.feature.example`)
Añadir el **Escenario 107**:

```cucumber
  Scenario: 107. Paridad total de traducción al inglés (i18n EN) en CIS Hardening, Seguridad L2, Telemetría SLA, Alertas y SIEM (Hito 30.16 - Spec 93)
    * def i18nComplianceEnContract = { cisScoreTitle: 'Overall CIS Security Compliance Score', l2BulkBtn: 'Deploy Across Fleet (Bulk Ops)', slaAnomalyTitle: 'Traffic Anomaly Detection & 1-Click Mitigation', notificationsTitle: 'Multi-Channel Alert & Notification Channels', siemSaveBtn: 'Save SIEM Configuration' }
    * match i18nComplianceEnContract.cisScoreTitle == 'Overall CIS Security Compliance Score'
    * match i18nComplianceEnContract.l2BulkBtn == 'Deploy Across Fleet (Bulk Ops)'
    * match i18nComplianceEnContract.slaAnomalyTitle == 'Traffic Anomaly Detection & 1-Click Mitigation'
    * match i18nComplianceEnContract.notificationsTitle == 'Multi-Channel Alert & Notification Channels'
    * match i18nComplianceEnContract.siemSaveBtn == 'Save SIEM Configuration'
```

---

## 4. Comandos de Verificación (Regla Cero — Docker Efímero)

```bash
# 1. Certificar cero claves JSON duplicadas en locales i18n
python3 .agents/scripts/verify_json_no_duplicate_keys.py

# 2. Ejecutar pruebas unitarias de las 3 vistas/componentes afectados en contenedor efímero
docker compose -f docker-compose.qa.yml run --rm frontend-test npx vitest run \
  src/views/enterpriseComplianceView.unit.ts \
  src/components/operations/NotificationChannelsPanel.unit.ts \
  src/components/operations/DiagnosticsAndSiemPanel.unit.ts

# 3. Certificar tipado estático y linter sin advertencias
docker compose -f docker-compose.qa.yml run --rm frontend-test npm run type-check
docker compose -f docker-compose.qa.yml run --rm frontend-test npm run lint
```
