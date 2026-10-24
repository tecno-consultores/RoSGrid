# 13 — Manual Operativo: Mapa de Red Bimodal, Infraestructura Pasiva (Cajas NAP) y Toolkit de Campo

Este manual operativo describe el funcionamiento, flujos de trabajo y directivas de ingeniería para el **Mapa de Red Bimodal (`/subscribers/map`)** y el **Toolkit Táctico de Operaciones de Campo (`/field-ops`)** en RoSGrid.

---

## 1. Arquitectura Bimodal: Empresa Corporativa vs Operador ISP

RoSGrid adapta automáticamente su interfaz y lógica de negocio en función del tipo de organización autenticada (`tenant.isp_module_enabled`).

```mermaid
graph TD
    User([Operador o Técnico]) --> Session{Tipo de Tenant}
    
    Session -->|isp_module_enabled: false| EnterpriseFlow[Modo Empresa / Campus]
    Session -->|isp_module_enabled: true| IspFlow[Modo Telecom / ISP]
    
    EnterpriseFlow --> E1[Mapa de Dispositivos de Red]
    EnterpriseFlow --> E2[Descubrimiento Leases DHCP]
    EnterpriseFlow --> E3[Herencia Coordenadas Router]
    EnterpriseFlow --> E4[Ping 1-Click desde MikroTik]
    
    IspFlow --> I1[Mapa de Planta Externa FTTH]
    IspFlow --> I2[Cajas NAP con Matriz 1..16]
    IspFlow --> I3[Aprovisionamiento de ONUs]
    IspFlow --> I4[Toolkit de Campo /field-ops]
```

### 1.1. Modo Empresa / Campus (`isp_module_enabled: false`)
Diseñado para corporaciones, bancos, universidades, hospitales y redes industriales:
* **Entidades Gestionadas:** Computadoras portátiles, estaciones de trabajo, impresoras de red, cámaras CCTV, puntos de acceso Wi-Fi y servidores.
* **Auto-Descubrimiento:** Se alimenta de las asignaciones de direcciones IP en `/ip/dhcp-server/lease` de los routers MikroTik del tenant.
* **Herencia de Coordenadas:** Todo equipo nuevo toma automáticamente la latitud y longitud del router de su sede (`router.latitude`, `router.longitude`) y el nombre de la sede física (`router.physical_location`).
* **Edición Táctica:** El administrador puede arrastrar o ajustar manualmente las coordenadas de cualquier dispositivo para reflejar su ubicación física (piso, ala o departamento). Las coordenadas editadas se marcan como personalizadas (`is_custom_coordinates: true`) y quedan protegidas contra sobreescrituras automáticas.
* **Verificación de Respuesta:** Un botón `[ ⚡ Test Ping 1-Click ]` ejecuta un sondeo ICMP desde el router MikroTik asignador hacia la IP del dispositivo, reportando latencia media, pérdida y estado cromático inmediato.
* **Supresión de Ruido:** Las pantallas de alta de clientes FTTH y cajas de dispersión óptica quedan totalmente apagadas y ocultas para no saturar al personal de TI corporativo.

### 1.2. Modo Telecom / ISP (`isp_module_enabled: true`)
Diseñado para operadores de fibra óptica FTTH y proveedores WISP:
* **Entidades Gestionadas:** Cajas NAP (Network Access Points / Splitters en postes y fachadas) y Abonados ONUs/ONTs de fibra óptica.
* **Aprovisionamiento Controlado:** Cero altas automáticas indiscriminadas por DHCP. Cada cliente se asocia formalmente a una Caja NAP y a un puerto físico del splitter.
* **Telemetría Óptica:** Medición de potencia óptica en la entrada de la caja NAP y potencia de recepción en la roseta del cliente ($Rx\text{ dBm}$), con semáforo de calidad de enlace.
* **Toolkit Móvil de Campo (`/field-ops`):** Tres herramientas directas optimizadas para smartphones de instaladores en ruta:
  1. `[ 📦 Registrar Caja NAP ]`
  2. `[ 👤 Registrar Nuevo Cliente / ONU ]`
  3. `[ ⚡ Diagnósticos y Certificación 1-Click ]`

---

## 2. Gestión de Infraestructura Pasiva: Cajas NAP (Terminal Box / ODB)

### 2.1. Parámetros Técnicos de una Caja NAP
En redes de dispersión óptica, cada caja representa un punto de empalme y división:
* **Código / Identificador:** Alfanumérico único por tenant (ej. `NAP-CBO-01`).
* **Capacidad de Puertos:** 8, 16 o 24 puertos de splitter (usualmente conectores SC/APC).
* **Ratio del Splitter:** 1:8, 1:16, o cascadas desbalanceadas (1:2 + 1:8).
* **Potencia de Entrada (Input Power dBm):** Nivel óptico medido en el conector de entrada que alimenta el splitter (ej. `-14.80 dBm`).
* **Tipo de Anclaje:**
  * `POLE`: Poste de hormigón o madera (con número de poste).
  * `FAÇADE`: Fachada o muro exterior de edificio.
  * `UNDERGROUND`: Cámara o arqueta subterránea.
  * `INDOOR_ODF`: Repartidor o armario interior.

### 2.2. Visualización e Interacción en el Mapa Cartográfico
* **Marcador Cartográfico:** Icono táctico con badge de ocupación de puertos: `ocupados / capacidad` (ej. `6/16`).
* **Panel de Detalle de Caja (Drawer):**
  * **Matriz de Puertos Estilo Patch Panel (1 al 16):**
    * 🟢 **Puerto Ocupado (Online):** Abonado conectado y navegando normalmente.
    * 🔴 **Puerto Ocupado (Offline):** Abonado con pérdida de señal óptica o desconexión.
    * ⚪ **Puerto Libre:** Disponible para asignación de nueva acometida.
  * **Acciones Directas:**
    * `[ ➕ Conectar Cliente en este NAP ]`: Abre la pantalla del técnico preseleccionando la caja y el primer puerto libre disponible.
    * `[ ⚡ Diagnóstico Ráfaga ]`: Envía pruebas de ping secuenciales a todos los abonados de la caja para descartar fallas masivas de splitter.

---

## 3. Toolkit de Operaciones de Campo (`/field-ops`)

### 3.1. Eliminación de Bloqueos por Órdenes de Trabajo
El instalador en calle no depende de asignaciones burocráticas previas. Puede proceder de inmediato con el alta de infraestructura física o la regularización de acometidas.

### 3.2. Pestaña 1: Registrar Caja NAP
1. El técnico llega al poste o fachada donde se ubicará la caja.
2. Pulsa el botón prominente `[ 📍 Capturar GPS de la Caja ]`.
3. Ingresa el código (`NAP-01`), selecciona capacidad (`16 puertos`) y anclaje (`Poste`).
4. Mide la potencia óptica con el Power Meter en el latiguillo de entrada y registra el valor (ej. `-14.5 dBm`).
5. Pulsa `[ Guardar Caja NAP ]`. La caja aparece disponible de inmediato en el mapa de toda la organización.

### 3.3. Pestaña 2: Registrar Nuevo Cliente FTTH
1. El técnico ingresa el identificador de circuito o usuario PPPoE.
2. El sistema lista las Cajas NAP cercanas ordenadas automáticamente por proximidad GPS. El técnico selecciona la caja asignada.
3. Se despliega la matriz de puertos libres; pulsa el puerto a utilizar (ej. `Puerto 4`).
4. Escanea o escribe el número de serie de la ONU. El sistema formatea automáticamente prefijos de fabricantes conocidos (`HWTC` para Huawei, `ZTEG` para ZTE, etc.).
5. Conecta el latiguillo a la roseta y registra la lectura de potencia óptica $Rx\text{ dBm}$:
   * **$-15.0\text{ a }-24.0\text{ dBm}$ (Verde):** Señal óptima.
   * **$-24.1\text{ a }-27.0\text{ dBm}$ (Naranja):** Señal degradada / en alerta.
   * **$< -27.0\text{ dBm}$ (Rojo):** Señal crítica inaceptable.
6. Pulsa `[ 📍 Capturar GPS Domicilio ]` y certifica el alta del servicio.

### 3.4. Pestaña 3: Diagnósticos y Certificación 1-Click
1. El técnico selecciona el servicio recién instalado.
2. Pulsa `[ ⚡ Ejecutar Diagnóstico en Vivo ]`.
3. El sistema consulta al MikroTik vía API REST:
   * Valida sesión activa (`bound` en DHCP o activa en `/ppp/active`).
   * Envía paquetes ICMP hacia la IP del cliente y mide latencia y pérdida.
   * Compara `caller-id` con la MAC registrada de la ONU para confirmar si está en modo Router o Bridge.
4. Con todas las comprobaciones en verde, el servicio pasa a estado `ACTIVE`.

---

## 4. Gobernanza y Seguridad RLS

* **Aislamiento Multi-Tenant Estricto:** Toda consulta a `optical_boxes` y `subscriber_devices` filtra por `tenant_id` mediante políticas nativas de PostgreSQL Row Level Security (RLS).
* **Protección Anti-SSRF:** La comunicación con los routers de acceso utiliza exclusivamente el cliente `MikrotikRestClient` validado con pinning de certificados TOFU y credenciales descifradas de la bóveda AES-256-GCM.
* **Cero Datos Personales (GDPR):** RoSGrid almacena exclusivamente parámetros de red y telemetría física. Las identidades civiles, contratos y cobranzas residen en los sistemas BSS/CRM externos.
