# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# 📡 Especificación Técnica 51: Consola Táctica Interactiva CAPsMAN v7, Aprovisionamiento Masivo de Wi-Fi y Gestión de Clientes en Tiempo Real

**Estándar:** Nivel 11X (QA Corporativo, Seguridad-by-Design, Paridad WebFig v7)  
**Módulos Afectados:** `fastapi/src/api/v1/wifi.py`, `vue3/src/views/EnterpriseComplianceView.vue`, `vue3/src/components/enterprise/`, `docs/specs/33`  
**Referencias Oficiales MikroTik RouterOS v7:**
- *WiFi CAPsMAN Documentation:* `https://manual.mikrotik.com/docs/wifi/`
- *Legacy CAPsMAN Documentation:* `https://manual.mikrotik.com/docs/capsman/`
- *MikroTik v7 CLI & REST Reference:* `https://manual.mikrotik.com/docs/cli-reference/`

---

## 1. Justificación y Fundamentación de Negocio

En entornos corporativos, campus universitarios, clínicas, centros de distribución y redes ISP comunitarias, la gestión de redes inalámbricas centralizadas requiere mucho más que un monitor pasivo de estado. Actualmente, la pestaña de Wi-Fi en `EnterpriseComplianceView.vue` opera de forma estrictamente read-only (consultando overview, SSIDs y clientes).

En estricto cumplimiento con la directiva arquitectónica del repositorio:
> **Zero Read-Only Operational Consoles (WebFig v7 Parity):**
> *«Ninguna pantalla de gestión de red puede permanecer en modo solo-lectura cuando la API REST de RouterOS v7 admite mutaciones de configuración. Se deben proveer acciones tácticas de creación, edición, alternancia de estado (toggle), eliminación y asistentes en 1 clic protegidos por Safe Mode de 60 segundos.»*

Esta especificación define la arquitectura técnica integral para transformar el módulo Wi-Fi & CAPsMAN de RoSGrid en una **consola operativa interactiva completa**, capaz de:
1. Activar y gobernar el gestor central CAPsMAN en hardware MikroTik v7.
2. Crear, editar y eliminar perfiles de seguridad WPA2-PSK / WPA3-SAE.
3. Desplegar múltiples SSIDs segmentados por VLAN (Corporativo, Invitados, IoT).
4. Configurar reglas de aprovisionamiento dinámico automático por bandas (2.4 GHz, 5 GHz, 6 GHz).
5. Forzar reprovisionamiento en caliente de los puntos de acceso (CAPs) conectados.
6. Ejecutar acciones en vivo sobre clientes (desconexión forzosa / *Kick Client* para roaming asistido o expulsión de intrusos).
7. Ofrecer un **Asistente de Despliegue en 1 Clic (Quick Setup Wizard)** con Safe Mode de 60 segundos.

---

## 2. Grounding Oficial RouterOS v7: Sintaxis y Comandos Canónicos

MikroTik RouterOS v7 implementa dos subsistemas inalámbricos completamente diferenciados según la arquitectura de hardware y paquetes instalados:
1. **RouterOS v7.13+ Moderno (`wifi-qcom` / `wifi` package):** Menús bajo `/interface/wifi/` (estándares 802.11ax / WiFi 6 / WiFi 6E / WiFi 7 y soporte Wave2 ac).
2. **Controlador Legado (`caps-man` package):** Menús bajo `/caps-man/` y `/interface/wireless/` (drivers legados para routers y APs 802.11a/b/g/n/ac tradicionales).

RoSGrid implementa compatibilidad bimodal transparente, detectando el subsistema soportado por el hardware y mapeando las operaciones REST canónicas:

### 2.1. Matriz de Comandos Nativos y Endpoints REST Oficiales

| Operación Táctica | RouterOS v7.13+ Moderno (`/interface/wifi/`) | RouterOS v6/v7 Legado (`/caps-man/`) | Endpoint REST RoSGrid |
| :--- | :--- | :--- | :--- |
| **Activar/Desactivar Manager** | `POST /rest/interface/wifi/capsman/set`<br>`{"enabled":"yes","ca-certificate":"auto","certificate":"auto","require-peer-certificate":"no"}` | `POST /rest/caps-man/manager/set`<br>`{"enabled":"yes","auto-certificate":"yes","require-peer-certificate":"no"}` | `POST /api/v1/wifi/capsman/{router_id}/manager/toggle` |
| **Crear Perfil de Seguridad** | `PUT /rest/interface/wifi/security`<br>`{"name":"sec-corp","authentication-types":"wpa2-psk,wpa3-psk","passphrase":"..."}` | `PUT /rest/caps-man/security`<br>`{"name":"sec-corp","authentication-types":"wpa2-psk","passphrase":"...","encryption":"aes-ccm"}` | `POST /api/v1/wifi/capsman/{router_id}/security-profiles` |
| **Crear Perfil Datapath (VLAN)** | `PUT /rest/interface/wifi/datapath`<br>`{"name":"dp-vlan100","bridge":"bridge","vlan-id":"100","client-isolation":"yes"}` | `PUT /rest/caps-man/datapath`<br>`{"name":"dp-vlan100","bridge":"bridge","vlan-id":"100","vlan-mode":"use-tag","client-to-client-forwarding":"no"}` | Integrado en Datapath o en modal de SSID |
| **Crear Configuración SSID** | `PUT /rest/interface/wifi/configuration`<br>`{"name":"cfg-corp","ssid":"CorpWiFi","security":"sec-corp","datapath":"dp-vlan100"}` | `PUT /rest/caps-man/configuration`<br>`{"name":"cfg-corp","ssid":"CorpWiFi","security":"sec-corp","datapath":"dp-vlan100"}` | `POST /api/v1/wifi/capsman/{router_id}/configurations` |
| **Regla de Provisioning** | `PUT /rest/interface/wifi/provisioning`<br>`{"action":"create-dynamic-enabled","supported-bands":"2ghz-ax,5ghz-ax","master-configuration":"cfg-corp"}` | `PUT /rest/caps-man/provisioning`<br>`{"action":"create-dynamic-enabled","master-configuration":"cfg-corp"}` | `POST /api/v1/wifi/capsman/{router_id}/provisioning` |
| **Reprovisionar Radios en Vivo** | `POST /rest/interface/wifi/radio/provision` o `/interface/wifi/provision` | `POST /rest/caps-man/remote-cap/provision` | `POST /api/v1/wifi/capsman/{router_id}/reprovision` |
| **Expulsar Cliente (Kick)** | `DELETE /rest/interface/wifi/registration-table/{id}` | `DELETE /rest/caps-man/registration-table/{id}` | `DELETE /api/v1/wifi/clients/{router_id}/{client_id}` |

---

## 3. Especificación de Endpoints Backend (`fastapi/src/api/v1/wifi.py`)

Todos los endpoints de mutación requieren:
- Autenticación JWT (`Bearer`) con perfil `SUPERADMIN_GLOBAL`, `TENANT_ADMIN`, `NETWORK_ENGINEER` o `SUPPORT_L2`.
- Cabecera obligatoria `Idempotency-Key: {uuid}` para operaciones `POST` y `PATCH`.
- Freno de seguridad transaccional: **Safe Mode automático de 60 segundos** en RouterOS v7.
- Intercepción **Maker-Checker (HTTP 202)** si el tenant tiene configurado `enforce_maker_checker = True` y la operación involucra borrado de SSIDs o alteración de credenciales globales.
- Registro en la pista inmutable de auditoría forense WORM (`audit_logs`).

### 3.1. Control del Gestor Central
#### `POST /api/v1/wifi/capsman/{router_id}/manager/toggle`
- **Propósito:** Conmutar el estado del servicio CAPsMAN en el router seleccionado.
- **Entrada:**
  ```json
  {
    "enabled": true,
    "require_peer_certificate": false,
    "auto_certificates": true
  }
  ```
- **Salida (200 OK):**
  ```json
  {
    "router_id": "9cd5a8f9-8e41-4efc-b208-8da08737a840",
    "driver": "wifi-qcom",
    "manager_enabled": true,
    "message": "Controlador CAPsMAN activado exitosamente."
  }
  ```

### 3.2. Gestión de Configuraciones y SSIDs
#### `POST /api/v1/wifi/capsman/{router_id}/configurations`
- **Entrada:**
  ```json
  {
    "name": "cfg-corp-main",
    "ssid": "RoSGrid-Corporativo",
    "security_profile": "sec-corp-wpa3",
    "vlan_id": 100,
    "client_isolation": false,
    "hide_ssid": false,
    "comment": "SSID Corporativo Principal"
  }
  ```
- **Comportamiento:**
  1. Si `vlan_id` está definido y no existe el perfil de datapath correspondiente, crea automáticamente el datapath `dp-vlan-{vlan_id}` enlazado al bridge principal.
  2. Crea la configuración en RouterOS v7 bajo `/interface/wifi/configuration` (o `/caps-man/configuration`).
  3. Registra traza WORM: `WIFI_CONFIGURATION_CREATED`.
- **Salida (201 Created):** Retorna la configuración creada con su ID nativo de RouterOS (`*1A`).

#### `PATCH /api/v1/wifi/capsman/{router_id}/configurations/{cfg_id}`
- **Entrada:** Modificación de `ssid`, `disabled`, `vlan_id`, `security_profile` o `comment`.
- **Salida (200 OK):** Objeto actualizado.

#### `DELETE /api/v1/wifi/capsman/{router_id}/configurations/{cfg_id}`
- **Comportamiento:** Elimina la configuración del router bajo Safe Mode. Si está asignada a una regla de provisioning activa, retorna `HTTP 409 Conflict` detallando las dependencias.

### 3.3. Gestión de Perfiles de Seguridad
#### `POST /api/v1/wifi/capsman/{router_id}/security-profiles`
- **Entrada:**
  ```json
  {
    "name": "sec-corp-wpa3",
    "authentication_types": ["wpa2-psk", "wpa3-psk"],
    "passphrase": "ClaveSeguraEmpresarial2026!",
    "wps_disabled": true,
    "ft_enabled": true
  }
  ```
- **Salida (201 Created):** Confirmación con clave enmascarada en la respuesta (`***`).

### 3.4. Reglas de Aprovisionamiento Dinámico (Provisioning Rules)
#### `POST /api/v1/wifi/capsman/{router_id}/provisioning`
- **Entrada:**
  ```json
  {
    "name": "prov-corporate-all",
    "action": "create-dynamic-enabled",
    "master_configuration": "cfg-corp-main",
    "slave_configurations": ["cfg-guest-internet"],
    "supported_bands": ["2ghz-ax", "5ghz-ax"],
    "identity_regex": ".*"
  }
  ```
- **Salida (201 Created):** Regla registrada en el plan de radiofrecuencia.

### 3.5. Operaciones Tácticas en Caliente
#### `POST /api/v1/wifi/capsman/{router_id}/reprovision`
- **Propósito:** Fuerza a RouterOS a reenviar los perfiles de configuración a todos los puntos de acceso remotos registrados (`remote-caps`).
- **Salida (200 OK):**
  ```json
  {
    "success": true,
    "provisioned_radios_count": 8,
    "message": "Señales de aprovisionamiento emitidas a los puntos de acceso conectados."
  }
  ```

#### `DELETE /api/v1/wifi/clients/{router_id}/{client_id}`
- **Propósito:** Expulsa de forma inmediata al cliente inalámbrico indicado (*Kick Client*) de la tabla de registros (`registration-table`), provocando la renegociación de 802.11 o el roaming hacia otro punto de acceso.
- **Salida (204 No Content).**

### 3.6. Asistente Rápido en 1 Clic (Quick Setup Wizard)
#### `POST /api/v1/wifi/capsman/{router_id}/quick-setup`
- **Entrada:**
  ```json
  {
    "corporate_ssid": "MiEmpresa-WiFi",
    "corporate_passphrase": "ClaveCorporativa2026!",
    "guest_ssid_enabled": true,
    "guest_ssid": "MiEmpresa-Invitados",
    "guest_passphrase": "InvitadosSeguros2026",
    "guest_vlan_id": 200,
    "bridge_name": "bridge"
  }
  ```
- **Comportamiento Transaccional:** En una sola transacción bajo Safe Mode:
  1. Activa el gestor CAPsMAN (`enabled=yes`).
  2. Crea los perfiles de seguridad (`sec-corporate` y opcionalmente `sec-guest`).
  3. Crea el datapath para invitados con aislamiento de clientes (`client-isolation=yes`, `vlan-id=200`).
  4. Crea las configuraciones inalámbricas master y slave.
  5. Crea la regla universal de provisioning para radios 2.4 GHz y 5 GHz.
- **Salida (201 Created):** Resumen del despliegue masivo.

---

## 4. Arquitectura de Interfaz Táctica (Vue 3 + TypeScript)

La vista `EnterpriseComplianceView.vue` (pestaña `wifi`) se rediseña para mantener paridad táctica con WinBox v4 y WebFig v7:

### 4.1. Barra de Herramientas Táctica Superior
- **Selector de Estado del Manager:** Switch reactivo con badge de estado cromático:
  - 🟢 **CAPsMAN Activo** (con conteo en vivo de APs remotos y radios aprovisionados).
  - 🔴 **CAPsMAN Inactivo** (con botón directo `[ Activar Controlador ]`).
- **Botonera Operativa:**
  - `[ ⚡ Configuración Rápida en 1 Clic ]`: Abre el modal `RgWifiQuickSetupWizardModal.vue`.
  - `[ + Nuevo SSID / Red ]`: Abre el modal `RgWifiConfigurationModal.vue`.
  - `[ 🔑 Perfiles de Seguridad ]`: Abre el modal de administración de claves y suites criptográficas `RgWifiSecurityModal.vue`.
  - `[ 📡 Reglas de Aprovisionamiento ]`: Abre el gestor de políticas por bandas y nombres de APs `RgWifiProvisioningModal.vue`.
  - `[ 🔄 Re-provisionar APs ]`: Ejecuta el barrido de actualización hacia los APs con confirmación visual.

### 4.2. Componentes y Modales Nuevos

1. **`RgWifiConfigurationModal.vue`:**
   - Campos:
     - Nombre de la configuración interna (ej. `cfg-marketing`).
     - Nombre de red broadcast (SSID, ej. `Oficinas Centrales`).
     - Selector desplegable de Perfil de Seguridad (con enlace para crear uno nuevo).
     - Switch `Ocultar SSID (Hide SSID)`: flag nativo RouterOS.
     - Segmentación VLAN: Input numérico opcional (1..4094).
     - Aislamiento de clientes (`Client Isolation`): Evita ataques ARP/Man-in-the-Middle entre dispositivos en la misma celda.
   - Acciones: `[ Guardar con Safe Mode ]` y `[ Cancelar ]`.

2. **`RgWifiSecurityModal.vue`:**
   - Campos:
     - Nombre de perfil (ej. `sec-wpa3-enterprise`).
     - Tipo de autenticación: WPA2-PSK, WPA3-SAE o WPA2+WPA3 mixto.
     - Contraseña Wi-Fi con botón toggle de visibilidad (icono de ojo).
     - Soporte para *Fast BSS Transition (802.11r)* para roaming VoIP ultra-rápido.
   - Acciones: Validación de longitud mínima (8 caracteres) y botón guardar.

3. **`RgWifiProvisioningModal.vue`:**
   - Tabla de reglas ordenadas por prioridad de coincidencia.
   - Criterios: Bandas soportadas (`2.4GHz`, `5GHz-ax`, `6GHz`), máscara de identidad de APs (`identity-regex`).
   - Asignación de configuración maestra y configuraciones esclavas (Virtual APs).

4. **`RgWifiQuickSetupWizardModal.vue`:**
   - Asistente en 3 pasos:
     - *Paso 1:* Definición de la Red Corporativa Principal (SSID y clave segura).
     - *Paso 2:* Creación opcional de Red de Invitados con aislamiento L2 y VLAN automática.
     - *Paso 3:* Confirmación de despliegue con Safe Mode y previsualización de comandos RouterOS v7.

### 4.3. Acciones en Tablas Tácticas
- **Tabla de SSIDs Configurados:**
  - Botón de estado `[ Habilitar / Deshabilitar ]` (flag nativo `[X]`).
  - Botón `[ ✏️ Editar ]` para modificar parámetros sin borrar la red.
  - Botón `[ 🗑️ Eliminar ]` con modal de advertencia de desvinculación de clientes.
- **Tabla de Clientes en Tiempo Real:**
  - Botón táctico `[ ⏏️ Expulsar ]` (*Kick Session*): Envía la señal de desautenticación inmediata al AP para desconectar al cliente seleccionado.

---

## 5. Gobernanza, Seguridad-by-Design y Safe Mode

1. **Safe Mode Transaccional de 60 Segundos:**
   - Toda llamada a RouterOS que modifique el estado de CAPsMAN o interfaces inalámbricas se encapsula en una sesión de Safe Mode.
   - Si la aplicación de una regla de provisioning o VLAN corta la conectividad de gestión de RoSGrid hacia el router, RouterOS v7 revierte automáticamente la transacción a los 60 segundos.
2. **Maker-Checker (HTTP 202 Interception):**
   - Si el tenant tiene activo `enforce_maker_checker = True`, el apagado del controlador CAPsMAN o el cambio de contraseñas de SSIDs corporativos no se aplica de inmediato; se envía como solicitud de cambio pendiente a la bandeja de aprobaciones para autorización por un segundo ingeniero.
3. **Auditoría Forense Inmutable WORM:**
   - Eventos registrados en `audit_logs`:
     - `WIFI_CAPSMAN_MANAGER_TOGGLED`
     - `WIFI_SECURITY_PROFILE_CREATED`
     - `WIFI_CONFIGURATION_CREATED` / `UPDATED` / `DELETED`
     - `WIFI_PROVISIONING_RULE_APPLIED`
     - `WIFI_FLEET_REPROVISIONED`
     - `WIFI_CLIENT_KICKED`

---

## 6. Plan de Pruebas y Certificación Nivel 11X

### 6.1. Pruebas Unitarias Backend (`fastapi/tests/api/test_wifi.unit.py`)
- Cobertura mínima obligatoria: `>= 95%`.
- Pruebas requeridas:
  - Toggle de manager (activación y desactivación en v7 moderno y legado).
  - Creación de configuración con datapath y perfiles de seguridad.
  - Rechazo de contraseñas menores a 8 caracteres (HTTP 422).
  - Manejo de dependencias y rechazo ante borrado de configuraciones activas (HTTP 409).
  - Reprovisionamiento exitoso y manejo de errores de comunicación.
  - Desconexión de clientes (HTTP 204).
  - Intercepción Maker-Checker (HTTP 202) cuando `enforce_maker_checker` está activo.

### 6.2. Pruebas Unitarias Frontend (`vue3/src/views/EnterpriseComplianceView.unit.ts` y modales)
- 100% de suites Vitest aprobadas.
- Verificación de renderizado de la botonera táctica, apertura de modales, submit reactivo y actualización de tablas tras operaciones de mutación.

### 6.3. Fixtures Trimodales RouterOS v7 (Regla Ground Truth)
- **Fixture A (Fábrica / No Configurado):** Manager inactivo, colecciones vacías (`[]`), validación de banner informativo.
- **Fixture B (Nominal RoSGrid):** Manager activo, 2 SSIDs (Corp e Invitados), 1 regla de provisioning, 8 clientes conectados.
- **Fixture C (Degradado):** Error de timeout o controlador caído sin colapso HTTP 500 de la API.

### 6.4. Escenarios BDD Karate Labs (API & UI)
- **API (`fastapi/test/api_test.feature`):** Escenario de creación de SSID, verificación de datapath y expulsión de cliente.
- **UI (`vue3/test/ui_business_flow.feature`):** Escenario de navegación a Enterprise Compliance > pestaña Wi-Fi, apertura del modal de nuevo SSID, diligenciamiento de formulario y verificación de la fila en la tabla.
