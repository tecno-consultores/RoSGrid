# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 77: Alta de Campo FTTH Centrada en MAC WAN, Aprovisionamiento Automático MikroTik desde IPAM (Reserva DHCP / Secreto PPPoE) y Arquitectura Desacoplada Nodo Físico L2 Bridge (`r3`) vs. Router Cabecera BNG (`r111`) (Hito 28.20)

> **Estado:** Aprobado para Ejecución (*Flash-Ready Specification*)  
> **Motor de Ejecución Objetivo:** Gemini 3.8 Flash (High)  
> **Hito Asociado:** Hito 28 — Subhito `28.20` (`ROADMAP.md`)  
> **Archivos Afectados:**
> 1. `fastapi/src/schemas/ipam.py`
> 2. `fastapi/src/api/v1/subscribers.py`
> 3. `vue3/src/types/index.ts`
> 4. `vue3/src/stores/useIpamStore.ts`
> 5. `vue3/src/components/field/FieldTechMobileView.vue`
> 6. `vue3/src/views/IpamManagementView.vue`
> 7. `fastapi/tests/api/test_ftth_subscriber_pairing_and_ping.unit.py`
> 8. `vue3/src/views/IpamSubscriberPairing.unit.ts`

---

## 1. Diagnóstico Arquitectónico y Operativo (3 Ejes de Diseño)

### 1.1. Eje 1 — Simplificación del Alta en Técnico de Campo (`/field-ops`): Solo Planta Física + MAC WAN de la ONU
- **Situación Actual:** En [`vue3/src/components/field/FieldTechMobileView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/field/FieldTechMobileView.vue) (líneas 250–283 y 748–879), el formulario de registro de cliente FTTH obliga al instalador de calle a capturar obligatoriamente el Serial GPON (`device_serial`), elegir el protocolo L3 (`service_type`: DHCP/PPPoE/Estático), el modo de la ONU (`ROUTER`/`BRIDGE`) y la IPv4 asignada (`assigned_ipv4`), mientras que deja la **Dirección MAC WAN / ONU (`onu_mac_address`)** como opcional.
- **Problema Operativo:**
  1. En redes FTTH con **DHCP** o **PPPoE**, el dato que realmente ve el router MikroTik en Capa 2/3 es la **Dirección MAC WAN de la ONU (`onu_mac_address`)** (en `/ip/dhcp-server/lease` como `mac-address` y en `/ppp/active` o `/ppp/secret` como `caller-id`).
  2. El instalador de campo no administra pools IPAM ni secretos PPPoE; su responsabilidad es conectar la acometida óptica al puerto de la Caja NAP, certificar la potencia óptica Rx (`dBm`) y escaneando/anotando la **MAC WAN de la ONU**.
- **Solución:**
  - En `FieldTechMobileView.vue`, hacer que **`MAC WAN de la ONU (`onu_mac_address`)`** sea el identificador de equipo **obligatorio** con botón de normalización en 1 clic (`🔤`, que convierte `aabb.ccdd.eeff`, `AA-BB-CC-11-22-33` o `aabbcc112233` al formato canónico MikroTik `AA:BB:CC:11:22:33`).
  - Pasar el Serial GPON (`device_serial`) a campo **opcional** de inventario físico (si se deja vacío, se deriva automáticamente `MAC-<HEX>` para trazabilidad sin bloquear al técnico).
  - Retirar del formulario de campo los selectores L3 (`Protocolo de Acceso WAN`, `Modo ONU`, `IPv4 Asignada`), que pasan a ser gobernados exclusivamente por el operador NOC desde `/ipam`.

---

### 1.2. Eje 2 — Aprovisionamiento Automático en MikroTik desde IPAM (`🔗 Emparejar Red`) para DHCP y PPPoE (ONUs Pre-Configuradas en Almacén)
- **Situación Actual:** Cuando el operador NOC abre `#modal-pair-subscriber` en [`vue3/src/views/IpamManagementView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/IpamManagementView.vue) y pulsa `🔗 Guardar Emparejamiento`, `PATCH /api/v1/subscriber-devices/{device_id}` solo actualiza PostgreSQL (`SubscriberDevice` e `IPAMAddress`), pero **no escribe la reserva DHCP ni el secreto PPPoE en el router MikroTik**.
- **Flujo Estándar ISP FTTH sin SSH a la ONU (Staging en Almacén + Aprovisionamiento NOC en MikroTik):**
  1. **Caso DHCP (`service_type == 'DHCP'`):**
     - La ONU sale de almacén en modo DHCP WAN (estándar de fábrica) y el técnico de campo registra su `onu_mac_address`.
     - Al abrir `🔗 Emparejar` en IPAM, RoSGrid auto-selecciona el lease activo si la MAC ya pidió IP, o permite al operador NOC escoger cualquier IP del Pool IPAM / escribir la IP deseada.
     - Al guardar con **`⚡ Aprovisionar en MikroTik RouterOS v7` (`provision_on_router = True`)**, el backend consulta `/rest/ip/dhcp-server/lease` en el router BNG:
       - Si ya existe un lease dinámico con esa `mac-address`, lo convierte en estático (`/rest/ip/dhcp-server/lease/make-static`) y actualiza su `address` y `comment="FTTH: <endpoint_identifier>"`.
       - Si no existe aún en la tabla de leases, crea directamente la reserva estática mediante `POST /rest/ip/dhcp-server/lease` con `{"address": assigned_ipv4, "mac-address": onu_mac_address, "comment": "FTTH: <endpoint_identifier>"}`.
  2. **Caso PPPoE (`service_type == 'PPPOE'`):**
     - Las ONUs no requieren acceso SSH desde RoSGrid: salen pre-configuradas desde almacén (*staging*) con un usuario/clave PPPoE estándar (ej. basado en el código de abonado o últimos 6 dígitos de la MAC) o en modo Bridge.
     - En el modal `🔗 Emparejar Red` de IPAM, cuando el operador NOC elige `PPPoE`, se habilitan los campos **`Usuario PPPoE (`pppoe_username`)`** y **`Contraseña PPPoE (`pppoe_password`)`**, junto con la **`IPv4 Fija Remota (`assigned_ipv4`)`** y la **`MAC WAN (`onu_mac_address`)`** registrada por el técnico en casa del cliente.
     - Al guardar, el backend crea o actualiza automáticamente en el MikroTik BNG (`/rest/ppp/secret`) el secreto PPPoE con:
       - `name = pppoe_username`
       - `password = pppoe_password` (si fue suministrada)
       - `service = "pppoe"`
       - `remote-address = assigned_ipv4`
       - `caller-id = onu_mac_address` *(candado de seguridad L2 que ata la sesión PPPoE a la MAC física de la ONU instalada por el técnico de campo)*.
       - `comment = "FTTH: <endpoint_identifier>"`

---

### 1.3. Eje 3 — Arquitectura Desacoplada: Caja NAP en Nodo de Acceso L2 Bridge (`r3`) vs. Servidor DHCP / BRAS PPPoE en Router Cabecera (`r111`)
- **Escenario Real del Laboratorio (6 Routers):**
  - En el laboratorio (y en la mayoría de redes FTTH reales con anillos de agregación MikroTik CRS/CCR), la Caja NAP física se conecta a un nodo de distribución/acceso cercano (por ejemplo **`r3`**), el cual está configurado como un **Bridge L2 transparente**.
  - Sin embargo, el servidor DHCP (`/ip/dhcp-server`) y/o el concentrador PPPoE (`/ppp/secret`) residen centralizados en el router cabecera **`r111`**.
- **Problema Actual:**
  - Como el técnico de campo registra la Caja NAP asociada a `r3` (`OpticalBox.router_id = r3.id`), el abonado nace con `SubscriberDevice.router_id = r3.id`.
  - Cuando el operador NOC abre `🔗 Emparejar Red` en IPAM, `GET /api/v1/subscriber-devices/{device_id}/live-candidates` interroga únicamente a `r3`, obteniendo **0 Leases DHCP y 0 Sesiones PPPoE** porque `r3` es un bridge L2 y los leases están en `r111`.
- **Solución Arquitectónica Dual (Preservando Topología Física en `r3` y Operación L3 en `r111`):**
  1. **Vínculo Físico L2 (`OpticalBox.router_id = r3`):** La Caja NAP conserva intacto su `router_id = r3`. Así, el Mapa de Red y el motor de *Root-Cause Analysis (RCA)* saben que físicamente la Caja NAP cuelga de `r3`.
  2. **Auto-Descubrimiento de Cabecera BNG (`r111`) + Selector Explícito en IPAM (`bng_router_id`):**
     - `GET /api/v1/subscriber-devices/{device_id}/live-candidates` acepta un parámetro opcional `?bng_router_id=<uuid>`.
     - Si el router inicial del abonado (`r3`) es un bridge L2 sin leases DHCP ni sesiones PPPoE (o no contiene la `onu_mac_address` del cliente), el backend **escanea automáticamente los demás routers activos del tenant (como `r111`)** precargando `.options(selectinload(Router.vault))`:
       - Prioriza cualquier router donde aparezca la `onu_mac_address` del abonado en `/ip/dhcp-server/lease` o `/ppp/active`.
       - En su defecto, selecciona automáticamente el router cabecera del tenant que tenga leases DHCP o secretos PPPoE activos (ej. `r111`).
     - Devuelve en `SubscriberLiveCandidatesResponse`:
       - `router_id` / `router_name`: el **Router Cabecera BNG / DHCP** efectivo (`r111`).
       - `access_router_id` / `access_router_name`: el **Nodo Físico de Acceso** de la Caja NAP (`r3`).
       - `auto_switched_bng: bool`: `True` cuando RoSGrid detectó automáticamente que `r3` era un Bridge L2 y conmutó la consulta de leases hacia la cabecera `r111`.
     - En `#modal-pair-subscriber` (`IpamManagementView.vue`), el operador NOC ve:
       - El badge informativo: `Nodo Físico NAP: r3 • Cabecera BNG/DHCP: r111 (Auto-detectado)`.
       - Un selector **`Router Cabecera BNG / Servidor DHCP-PPPoE (`bng_router_id`)`** que permite cambiar en caliente qué router cabecera consultar y en cuál router aprovisionar la reserva DHCP o el secreto PPPoE.
     - Al guardar el emparejamiento, `SubscriberDevice.router_id` se actualiza al `bng_router_id` (`r111`) para que tanto el aprovisionamiento (`/ip/dhcp-server/lease` / `/ppp/secret`) como el diagnóstico **Ping 1-Click / 360°** se ejecuten desde `r111`, mientras `SubscriberDevice.optical_box_id` sigue apuntando a la Caja NAP conectada a `r3`.

---

## 2. Instrucciones de Implementación Paso a Paso (Flash-Ready)

### Paso 1: Ampliar Esquemas Pydantic en `fastapi/src/schemas/ipam.py`

En [`fastapi/src/schemas/ipam.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/schemas/ipam.py) (líneas 260–336), añadir `router_id` y `provision_on_router` en `SubscriberDeviceUpdate`, añadir metadatos de nodo físico vs. cabecera BNG en `SubscriberLiveCandidatesResponse` y exponer `mikrotik_provision_status` en `SubscriberDeviceResponse`:

#### `Target` en `fastapi/src/schemas/ipam.py`:
```python
class SubscriberDeviceUpdate(BaseModel):
    endpoint_identifier: Optional[str] = None
    service_type: Optional[CustomerServiceTypeEnum] = None
    auth_backend: Optional[AuthBackendEnum] = None
    pppoe_password: Optional[str] = None
    ipv4_address_id: Optional[uuid.UUID] = None
    assigned_ipv4: Optional[str] = Field(None, max_length=45)
    ipv6_delegated_prefix: Optional[str] = None
    bandwidth_profile_id: Optional[uuid.UUID] = None
    onu_mode: Optional[ONUModeEnum] = None
    onu_mac_address: Optional[str] = None
    device_serial: Optional[str] = None
    cpe_wifi_mac_address: Optional[str] = None
    pon_port: Optional[str] = None
    optical_box: Optional[str] = None
    optical_box_id: Optional[uuid.UUID] = None
    optical_box_port: Optional[int] = None
    rx_optical_power_dbm: Optional[Decimal] = None
    drop_cable_meters: Optional[int] = None
    is_custom_coordinates: Optional[bool] = None
    reset_to_router_coordinates: Optional[bool] = None
    status: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    # Compatibilidad con llamadas heredadas
    customer_name: Optional[str] = None
    customer_code: Optional[str] = None
    pppoe_username: Optional[str] = None
    onu_serial_number: Optional[str] = None
    physical_address: Optional[str] = None

    @field_validator("service_type", mode="before")
    @classmethod
    def normalize_service_type(cls, v: Any) -> Any:
        return _normalize_service_type_input(v)

    @field_validator("onu_mode", mode="before")
    @classmethod
    def normalize_onu_mode(cls, v: Any) -> Any:
        return _normalize_onu_mode_input(v)


class SubscriberLiveCandidateDhcpLease(BaseModel):
    address: str
    mac_address: Optional[str] = None
    host_name: Optional[str] = None
    server: Optional[str] = None
    status: Optional[str] = None
    comment: Optional[str] = None


class SubscriberLiveCandidatePppoe(BaseModel):
    name: str
    address: Optional[str] = None
    caller_id: Optional[str] = None
    service: Optional[str] = None
    uptime: Optional[str] = None
    source: str = "active"


class SubscriberLiveCandidatesResponse(BaseModel):
    device_id: uuid.UUID
    router_id: uuid.UUID
    router_name: str
    dhcp_leases: list[SubscriberLiveCandidateDhcpLease] = Field(default_factory=list)
    pppoe_sessions: list[SubscriberLiveCandidatePppoe] = Field(default_factory=list)
    ipam_addresses: list[IPAMAddressResponse] = Field(default_factory=list)
```

#### `Replacement` en `fastapi/src/schemas/ipam.py`:
```python
class SubscriberDeviceUpdate(BaseModel):
    router_id: Optional[uuid.UUID] = None
    bng_router_id: Optional[uuid.UUID] = None
    provision_on_router: bool = True
    endpoint_identifier: Optional[str] = None
    service_type: Optional[CustomerServiceTypeEnum] = None
    auth_backend: Optional[AuthBackendEnum] = None
    pppoe_password: Optional[str] = None
    ipv4_address_id: Optional[uuid.UUID] = None
    assigned_ipv4: Optional[str] = Field(None, max_length=45)
    ipv6_delegated_prefix: Optional[str] = None
    bandwidth_profile_id: Optional[uuid.UUID] = None
    onu_mode: Optional[ONUModeEnum] = None
    onu_mac_address: Optional[str] = None
    device_serial: Optional[str] = None
    cpe_wifi_mac_address: Optional[str] = None
    pon_port: Optional[str] = None
    optical_box: Optional[str] = None
    optical_box_id: Optional[uuid.UUID] = None
    optical_box_port: Optional[int] = None
    rx_optical_power_dbm: Optional[Decimal] = None
    drop_cable_meters: Optional[int] = None
    is_custom_coordinates: Optional[bool] = None
    reset_to_router_coordinates: Optional[bool] = None
    status: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    # Compatibilidad con llamadas heredadas
    customer_name: Optional[str] = None
    customer_code: Optional[str] = None
    pppoe_username: Optional[str] = None
    onu_serial_number: Optional[str] = None
    physical_address: Optional[str] = None

    @field_validator("service_type", mode="before")
    @classmethod
    def normalize_service_type(cls, v: Any) -> Any:
        return _normalize_service_type_input(v)

    @field_validator("onu_mode", mode="before")
    @classmethod
    def normalize_onu_mode(cls, v: Any) -> Any:
        return _normalize_onu_mode_input(v)


class SubscriberLiveCandidateDhcpLease(BaseModel):
    address: str
    mac_address: Optional[str] = None
    host_name: Optional[str] = None
    server: Optional[str] = None
    status: Optional[str] = None
    comment: Optional[str] = None


class SubscriberLiveCandidatePppoe(BaseModel):
    name: str
    address: Optional[str] = None
    caller_id: Optional[str] = None
    service: Optional[str] = None
    uptime: Optional[str] = None
    source: str = "active"


class SubscriberLiveCandidatesResponse(BaseModel):
    device_id: uuid.UUID
    router_id: uuid.UUID
    router_name: str
    access_router_id: Optional[uuid.UUID] = None
    access_router_name: Optional[str] = None
    auto_switched_bng: bool = False
    matched_mac_address: Optional[str] = None
    matched_ipv4: Optional[str] = None
    dhcp_leases: list[SubscriberLiveCandidateDhcpLease] = Field(default_factory=list)
    pppoe_sessions: list[SubscriberLiveCandidatePppoe] = Field(default_factory=list)
    ipam_addresses: list[IPAMAddressResponse] = Field(default_factory=list)
```

---

### Paso 2: Auto-Descubrimiento de Cabecera BNG (`r111`) y Aprovisionamiento Automático MikroTik (`/ip/dhcp-server/lease` y `/ppp/secret`) en `fastapi/src/api/v1/subscribers.py`

En [`fastapi/src/api/v1/subscribers.py`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/subscribers.py):
1. Crear los helpers modulares (Grado A Radon `CC <= 4`):
   - `_normalize_mac_address(raw_mac: Optional[str]) -> Optional[str]`: normaliza cualquier formato (`aabb.ccdd.eeff`, `AA-BB-CC-DD-EE-FF`, `aabbccddeeff`) a `AA:BB:CC:DD:EE:FF`.
   - `_collect_router_live_candidates(r: Router, tenant_id: uuid.UUID)`: extrae los leases DHCP (`/ip/dhcp-server/lease`) y sesiones/secretos PPPoE (`/ppp/active`, `/ppp/secret`) de un router.
   - `_provision_subscriber_on_mikrotik(...)`: aprovisiona en el router BNG seleccionado:
     - Si `service_type == CustomerServiceTypeEnum.DHCP` y hay `assigned_ipv4` + `onu_mac_address`: busca en `/ip/dhcp-server/lease` por `mac-address` o `address`; si existe con `dynamic == "true"`, invoca `/ip/dhcp-server/lease/make-static` y luego `PATCH /ip/dhcp-server/lease/{id}`; si existe estático, hace `PATCH /ip/dhcp-server/lease/{id}`; y si no existe, ejecuta `POST /ip/dhcp-server/lease` con `{"address": clean_ip, "mac-address": norm_mac, "comment": f"FTTH: {endpoint_identifier}"}`.
     - Si `service_type == CustomerServiceTypeEnum.PPPOE` y hay `endpoint_identifier`: busca en `/ppp/secret` por `name`; si existe, ejecuta `PATCH /ppp/secret/{id}` actualizando `remote-address`, `caller-id` (`onu_mac_address`) y `password` (si se envió); si no existe, ejecuta `POST /ppp/secret` con `{"name": endpoint_identifier, "password": pppoe_password or endpoint_identifier, "service": "pppoe", "remote-address": clean_ip, "caller-id": norm_mac, "comment": f"FTTH: {endpoint_identifier}"}`.
2. Actualizar `get_subscriber_live_pairing_candidates` para aceptar `bng_router_id: Optional[uuid.UUID] = Query(default=None)`, resolver el nodo físico de la Caja NAP (`access_router_id` / `access_router_name`) y, cuando el nodo físico (`r3`) sea un Bridge L2 sin leases/PPPoE o sin la MAC del cliente, auto-descubrir el router cabecera BNG (`r111`) entre los routers activos del tenant.
3. Actualizar `update_subscriber_device` (`PATCH /api/v1/subscriber-devices/{device_id}`) para aceptar `bng_router_id` / `router_id`, actualizar `device.router_id` al BNG seleccionado y ejecutar `_provision_subscriber_on_mikrotik` cuando `payload.provision_on_router` sea `True`.

#### `Target` en `fastapi/src/api/v1/subscribers.py`:
```python
@subscribers_router.get("/{device_id}/live-candidates", response_model=SubscriberLiveCandidatesResponse)
async def get_subscriber_live_pairing_candidates(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.NOC_MONITOR,
            SystemRoleEnum.FIELD_TECH,
        )
    ),
) -> SubscriberLiveCandidatesResponse:
    """Consulta en vivo en el router MikroTik del abonado los Leases DHCP activos, Sesiones/Secretos PPPoE
    y direcciones IPAM disponibles para emparejar una ONU recién registrada en 1 clic.
    """
    tenant_id = get_tenant_id(claims)
    stmt_dev = select(SubscriberDevice).where(
        SubscriberDevice.id == device_id,
        SubscriberDevice.tenant_id == tenant_id,
    )
    dev = (await db.execute(stmt_dev)).scalar_one_or_none()
    if not dev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo de abonado no encontrado")

    stmt_r = (
        select(Router)
        .options(selectinload(Router.vault))
        .where(Router.id == dev.router_id, Router.tenant_id == tenant_id)
    )
    r = (await db.execute(stmt_r)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router asignador no encontrado")

    dhcp_candidates: list[SubscriberLiveCandidateDhcpLease] = []
    pppoe_candidates: list[SubscriberLiveCandidatePppoe] = []
    seen_pppoe_names: set[str] = set()

    client = _get_router_client(r, tenant_id)
    try:
        async with client:
            raw_leases = await client.get("/ip/dhcp-server/lease")
            if isinstance(raw_leases, list):
                for item in raw_leases:
                    if not isinstance(item, dict):
                        continue
                    addr = str(item.get("address") or item.get("active-address") or "").strip()
                    if not addr:
                        continue
                    dhcp_candidates.append(
                        SubscriberLiveCandidateDhcpLease(
                            address=addr,
                            mac_address=str(item.get("mac-address") or item.get("active-mac-address") or "").strip() or None,
                            host_name=str(item.get("host-name") or "").strip() or None,
                            server=str(item.get("server") or "").strip() or None,
                            status=str(item.get("status") or "bound").strip(),
                            comment=str(item.get("comment") or "").strip() or None,
                        )
                    )

            raw_ppp_active = await client.get("/ppp/active")
            if isinstance(raw_ppp_active, list):
                for item in raw_ppp_active:
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("name") or "").strip()
                    if not name:
                        continue
                    seen_pppoe_names.add(name)
                    pppoe_candidates.append(
                        SubscriberLiveCandidatePppoe(
                            name=name,
                            address=str(item.get("address") or "").strip() or None,
                            caller_id=str(item.get("caller-id") or "").strip() or None,
                            service=str(item.get("service") or "pppoe").strip(),
                            uptime=str(item.get("uptime") or "").strip() or None,
                            source="active",
                        )
                    )

            raw_ppp_secrets = await client.get("/ppp/secret")
            if isinstance(raw_ppp_secrets, list):
                for item in raw_ppp_secrets:
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("name") or "").strip()
                    if not name or name in seen_pppoe_names:
                        continue
                    pppoe_candidates.append(
                        SubscriberLiveCandidatePppoe(
                            name=name,
                            address=str(item.get("remote-address") or "").strip() or None,
                            caller_id=str(item.get("caller-id") or "").strip() or None,
                            service=str(item.get("service") or "pppoe").strip(),
                            uptime=None,
                            source="secret",
                        )
                    )
    except Exception as e:
        logger.warning(f"Sondeo de candidatos en vivo en router {r.display_name} retornó aviso: {e}")

    stmt_ips = (
        select(IPAMAddress)
        .where(IPAMAddress.tenant_id == tenant_id)
        .order_by(IPAMAddress.created_at.desc())
        .limit(100)
    )
    ipam_rows = list((await db.execute(stmt_ips)).scalars().all())

    return SubscriberLiveCandidatesResponse(
        device_id=dev.id,
        router_id=r.id,
        router_name=r.display_name,
        dhcp_leases=dhcp_candidates,
        pppoe_sessions=pppoe_candidates,
        ipam_addresses=[IPAMAddressResponse.model_validate(ip) for ip in ipam_rows],
    )
```

*(Nota: si Spec 76 aún no se ha aplicado en `subscribers.py`, el bloque `stmt_r` tendrá `stmt_r = select(Router).where(Router.id == dev.router_id, Router.tenant_id == tenant_id)` — reemplazar toda la función `get_subscriber_live_pairing_candidates` e incluir los helpers debajo).*

#### `Replacement` en `fastapi/src/api/v1/subscribers.py`:
```python
def _normalize_mac_address(raw_mac: Optional[str]) -> Optional[str]:
    """Normaliza una dirección MAC (AA-BB-CC-DD-EE-FF, aabb.ccdd.eeff, aabbccddeeff) a AA:BB:CC:DD:EE:FF."""
    if not raw_mac:
        return None
    hex_only = "".join(ch for ch in raw_mac.strip().upper() if ch in "0123456789ABCDEF")
    if len(hex_only) == 12:
        return ":".join(hex_only[i : i + 2] for i in range(0, 12, 2))
    return raw_mac.strip().upper()


async def _collect_router_live_candidates(
    r: Router,
    tenant_id: uuid.UUID,
) -> tuple[list[SubscriberLiveCandidateDhcpLease], list[SubscriberLiveCandidatePppoe]]:
    """Extrae en vivo los Leases DHCP y Sesiones/Secretos PPPoE de un router MikroTik."""
    dhcp_candidates: list[SubscriberLiveCandidateDhcpLease] = []
    pppoe_candidates: list[SubscriberLiveCandidatePppoe] = []
    seen_pppoe_names: set[str] = set()

    client = _get_router_client(r, tenant_id)
    try:
        async with client:
            raw_leases = await client.get("/ip/dhcp-server/lease")
            if isinstance(raw_leases, list):
                for item in raw_leases:
                    if not isinstance(item, dict):
                        continue
                    addr = str(item.get("address") or item.get("active-address") or "").strip()
                    if not addr:
                        continue
                    dhcp_candidates.append(
                        SubscriberLiveCandidateDhcpLease(
                            address=addr,
                            mac_address=_normalize_mac_address(
                                str(item.get("mac-address") or item.get("active-mac-address") or "").strip() or None
                            ),
                            host_name=str(item.get("host-name") or "").strip() or None,
                            server=str(item.get("server") or "").strip() or None,
                            status=str(item.get("status") or "bound").strip(),
                            comment=str(item.get("comment") or "").strip() or None,
                        )
                    )

            raw_ppp_active = await client.get("/ppp/active")
            if isinstance(raw_ppp_active, list):
                for item in raw_ppp_active:
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("name") or "").strip()
                    if not name:
                        continue
                    seen_pppoe_names.add(name)
                    pppoe_candidates.append(
                        SubscriberLiveCandidatePppoe(
                            name=name,
                            address=str(item.get("address") or "").strip() or None,
                            caller_id=_normalize_mac_address(str(item.get("caller-id") or "").strip() or None),
                            service=str(item.get("service") or "pppoe").strip(),
                            uptime=str(item.get("uptime") or "").strip() or None,
                            source="active",
                        )
                    )

            raw_ppp_secrets = await client.get("/ppp/secret")
            if isinstance(raw_ppp_secrets, list):
                for item in raw_ppp_secrets:
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("name") or "").strip()
                    if not name or name in seen_pppoe_names:
                        continue
                    pppoe_candidates.append(
                        SubscriberLiveCandidatePppoe(
                            name=name,
                            address=str(item.get("remote-address") or "").strip() or None,
                            caller_id=_normalize_mac_address(str(item.get("caller-id") or "").strip() or None),
                            service=str(item.get("service") or "pppoe").strip(),
                            uptime=None,
                            source="secret",
                        )
                    )
    except Exception as e:
        logger.warning(f"Sondeo de candidatos en vivo en router {r.display_name} retornó aviso: {e}")

    return dhcp_candidates, pppoe_candidates


def _find_mac_match_in_candidates(
    target_mac: Optional[str],
    dhcp_leases: list[SubscriberLiveCandidateDhcpLease],
    pppoe_sessions: list[SubscriberLiveCandidatePppoe],
) -> Optional[str]:
    """Busca si la MAC WAN del abonado ya tiene IP en los leases DHCP o sesiones PPPoE."""
    norm_target = _normalize_mac_address(target_mac)
    if not norm_target:
        return None
    for lease in dhcp_leases:
        if _normalize_mac_address(lease.mac_address) == norm_target and lease.address:
            return lease.address
    for ppp in pppoe_sessions:
        if _normalize_mac_address(ppp.caller_id) == norm_target and ppp.address:
            return ppp.address
    return None


async def _provision_subscriber_on_mikrotik(
    r: Router,
    tenant_id: uuid.UUID,
    service_type: CustomerServiceTypeEnum,
    endpoint_identifier: str,
    assigned_ipv4: Optional[str],
    onu_mac_address: Optional[str],
    pppoe_password: Optional[str] = None,
) -> None:
    """Aprovisiona en el router cabecera MikroTik BNG la reserva estática DHCP o el secreto PPPoE."""
    clean_ip = (assigned_ipv4 or "").strip().split("/")[0].strip()
    norm_mac = _normalize_mac_address(onu_mac_address)
    comment_tag = f"FTTH: {endpoint_identifier}"
    client = _get_router_client(r, tenant_id)

    try:
        async with client:
            if service_type == CustomerServiceTypeEnum.DHCP and clean_ip and norm_mac:
                leases = await client.get("/ip/dhcp-server/lease")
                existing_lease = None
                if isinstance(leases, list):
                    for item in leases:
                        if not isinstance(item, dict):
                            continue
                        item_mac = _normalize_mac_address(
                            str(item.get("mac-address") or item.get("active-mac-address") or "")
                        )
                        item_addr = str(item.get("address") or "").strip()
                        if item_mac == norm_mac or item_addr == clean_ip:
                            existing_lease = item
                            break

                if existing_lease and existing_lease.get(".id"):
                    lease_id = str(existing_lease[".id"])
                    if str(existing_lease.get("dynamic", "false")).lower() == "true":
                        await client.post("/ip/dhcp-server/lease/make-static", {".id": lease_id})
                    await client.patch(
                        f"/ip/dhcp-server/lease/{lease_id}",
                        {"address": clean_ip, "mac-address": norm_mac, "comment": comment_tag},
                    )
                else:
                    await client.post(
                        "/ip/dhcp-server/lease",
                        {"address": clean_ip, "mac-address": norm_mac, "comment": comment_tag},
                    )

            elif service_type == CustomerServiceTypeEnum.PPPOE and endpoint_identifier:
                secrets = await client.get("/ppp/secret")
                existing_secret = None
                if isinstance(secrets, list):
                    for item in secrets:
                        if isinstance(item, dict) and str(item.get("name") or "").strip() == endpoint_identifier:
                            existing_secret = item
                            break

                secret_payload: dict[str, Any] = {
                    "name": endpoint_identifier,
                    "service": "pppoe",
                    "comment": comment_tag,
                }
                if clean_ip:
                    secret_payload["remote-address"] = clean_ip
                if norm_mac:
                    secret_payload["caller-id"] = norm_mac
                if pppoe_password:
                    secret_payload["password"] = pppoe_password

                if existing_secret and existing_secret.get(".id"):
                    await client.patch(f"/ppp/secret/{existing_secret['.id']}", secret_payload)
                else:
                    if "password" not in secret_payload:
                        secret_payload["password"] = endpoint_identifier
                    await client.post("/ppp/secret", secret_payload)
    except Exception as exc:
        logger.warning(f"Aprovisionamiento MikroTik en {r.display_name} para {endpoint_identifier} omitido/aviso: {exc}")


@subscribers_router.get("/{device_id}/live-candidates", response_model=SubscriberLiveCandidatesResponse)
async def get_subscriber_live_pairing_candidates(
    device_id: uuid.UUID,
    bng_router_id: Optional[uuid.UUID] = Query(default=None),
    db: AsyncSession = Depends(get_tenant_db_session),
    claims: dict[str, Any] = Depends(
        require_roles(
            SystemRoleEnum.SUPERADMIN_GLOBAL,
            SystemRoleEnum.TENANT_ADMIN,
            SystemRoleEnum.NOC_MONITOR,
            SystemRoleEnum.FIELD_TECH,
        )
    ),
) -> SubscriberLiveCandidatesResponse:
    """Consulta en vivo los Leases DHCP activos, Sesiones/Secretos PPPoE y direcciones IPAM.
    Soporta arquitecturas desacopladas donde la Caja NAP cuelga de un nodo L2 Bridge (ej. r3)
    mientras el servidor DHCP / BRAS PPPoE vive en un router cabecera BNG (ej. r111).
    """
    tenant_id = get_tenant_id(claims)
    stmt_dev = select(SubscriberDevice).where(
        SubscriberDevice.id == device_id,
        SubscriberDevice.tenant_id == tenant_id,
    )
    dev = (await db.execute(stmt_dev)).scalar_one_or_none()
    if not dev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispositivo de abonado no encontrado")

    # Identificar el nodo físico de acceso (de la Caja NAP si existe, o dev.router_id)
    access_router_id = dev.router_id
    if dev.optical_box_id:
        stmt_box = select(OpticalBox).where(OpticalBox.id == dev.optical_box_id, OpticalBox.tenant_id == tenant_id)
        box_obj = (await db.execute(stmt_box)).scalar_one_or_none()
        if box_obj:
            access_router_id = box_obj.router_id

    stmt_access = select(Router).where(Router.id == access_router_id, Router.tenant_id == tenant_id)
    access_router = (await db.execute(stmt_access)).scalar_one_or_none()

    target_router_id = bng_router_id or dev.router_id
    stmt_r = (
        select(Router)
        .options(selectinload(Router.vault))
        .where(Router.id == target_router_id, Router.tenant_id == tenant_id)
    )
    r = (await db.execute(stmt_r)).scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router asignador no encontrado")

    dhcp_candidates, pppoe_candidates = await _collect_router_live_candidates(r, tenant_id)
    matched_ip = _find_mac_match_in_candidates(dev.onu_mac_address, dhcp_candidates, pppoe_candidates)
    auto_switched_bng = False

    # Si no se forzó bng_router_id y el router actual (ej. r3 en modo Bridge L2) no tiene leases/PPPoE
    # o no tiene la MAC del abonado, buscar automáticamente en los demás routers del tenant (ej. r111)
    if bng_router_id is None and (not matched_ip and len(dhcp_candidates) == 0 and len(pppoe_candidates) == 0):
        stmt_others = (
            select(Router)
            .options(selectinload(Router.vault))
            .where(Router.tenant_id == tenant_id, Router.id != r.id)
            .order_by(Router.created_at.asc())
        )
        other_routers = list((await db.execute(stmt_others)).scalars().all())
        fallback_bng: Optional[tuple[Router, list[SubscriberLiveCandidateDhcpLease], list[SubscriberLiveCandidatePppoe]]] = None

        for candidate_r in other_routers:
            cand_dhcp, cand_pppoe = await _collect_router_live_candidates(candidate_r, tenant_id)
            cand_match = _find_mac_match_in_candidates(dev.onu_mac_address, cand_dhcp, cand_pppoe)
            if cand_match:
                r = candidate_r
                dhcp_candidates = cand_dhcp
                pppoe_candidates = cand_pppoe
                matched_ip = cand_match
                auto_switched_bng = True
                break
            if fallback_bng is None and (len(cand_dhcp) > 0 or len(cand_pppoe) > 0):
                fallback_bng = (candidate_r, cand_dhcp, cand_pppoe)

        if not auto_switched_bng and fallback_bng is not None:
            r, dhcp_candidates, pppoe_candidates = fallback_bng
            matched_ip = _find_mac_match_in_candidates(dev.onu_mac_address, dhcp_candidates, pppoe_candidates)
            auto_switched_bng = True

    stmt_ips = (
        select(IPAMAddress)
        .where(IPAMAddress.tenant_id == tenant_id)
        .order_by(IPAMAddress.created_at.desc())
        .limit(100)
    )
    ipam_rows = list((await db.execute(stmt_ips)).scalars().all())

    return SubscriberLiveCandidatesResponse(
        device_id=dev.id,
        router_id=r.id,
        router_name=r.display_name,
        access_router_id=access_router.id if access_router else r.id,
        access_router_name=access_router.display_name if access_router else r.display_name,
        auto_switched_bng=auto_switched_bng,
        matched_mac_address=_normalize_mac_address(dev.onu_mac_address),
        matched_ipv4=matched_ip,
        dhcp_leases=dhcp_candidates,
        pppoe_sessions=pppoe_candidates,
        ipam_addresses=[IPAMAddressResponse.model_validate(ip) for ip in ipam_rows],
    )
```

Y en `update_subscriber_device` (`fastapi/src/api/v1/subscribers.py`, líneas 1075–1115), actualizar la lógica para permitir reasignar el `bng_router_id` (`device.router_id`), normalizar `onu_mac_address` y aprovisionar en MikroTik:

#### `Target` en `fastapi/src/api/v1/subscribers.py` (`update_subscriber_device`):
```python
    update_dict = payload.model_dump(exclude_unset=True)
    if "onu_serial_number" in update_dict and "device_serial" not in update_dict:
        update_dict["device_serial"] = update_dict.pop("onu_serial_number")
    if "pppoe_username" in update_dict and "endpoint_identifier" not in update_dict and update_dict["pppoe_username"]:
        update_dict["endpoint_identifier"] = update_dict.pop("pppoe_username")

    raw_assigned_ipv4 = update_dict.pop("assigned_ipv4", None)
    if raw_assigned_ipv4:
        resolved_ip_id = await _resolve_or_create_subscriber_ipv4(
            db=db,
            tenant_id=tenant_id,
            router_id=device.router_id,
            raw_ipv4=raw_assigned_ipv4,
            mac_address=update_dict.get("onu_mac_address") or device.onu_mac_address,
            description=f"Abonado FTTH {update_dict.get('endpoint_identifier') or device.endpoint_identifier}",
        )
        if resolved_ip_id:
            device.ipv4_address_id = resolved_ip_id
```

#### `Replacement` en `fastapi/src/api/v1/subscribers.py` (`update_subscriber_device`):
```python
    update_dict = payload.model_dump(exclude_unset=True)
    provision_on_router = bool(update_dict.pop("provision_on_router", True))
    pppoe_password = update_dict.pop("pppoe_password", None)
    bng_router_id = update_dict.pop("bng_router_id", None) or update_dict.pop("router_id", None)

    if bng_router_id:
        stmt_bng = select(Router).where(Router.id == bng_router_id, Router.tenant_id == tenant_id)
        if (await db.execute(stmt_bng)).scalar_one_or_none():
            device.router_id = bng_router_id

    if "onu_mac_address" in update_dict and update_dict["onu_mac_address"]:
        update_dict["onu_mac_address"] = _normalize_mac_address(update_dict["onu_mac_address"])

    if "onu_serial_number" in update_dict and "device_serial" not in update_dict:
        update_dict["device_serial"] = update_dict.pop("onu_serial_number")
    if "pppoe_username" in update_dict and "endpoint_identifier" not in update_dict and update_dict["pppoe_username"]:
        update_dict["endpoint_identifier"] = update_dict.pop("pppoe_username")

    raw_assigned_ipv4 = update_dict.pop("assigned_ipv4", None)
    if raw_assigned_ipv4:
        resolved_ip_id = await _resolve_or_create_subscriber_ipv4(
            db=db,
            tenant_id=tenant_id,
            router_id=device.router_id,
            raw_ipv4=raw_assigned_ipv4,
            mac_address=update_dict.get("onu_mac_address") or device.onu_mac_address,
            description=f"Abonado FTTH {update_dict.get('endpoint_identifier') or device.endpoint_identifier}",
        )
        if resolved_ip_id:
            device.ipv4_address_id = resolved_ip_id

    if provision_on_router and (raw_assigned_ipv4 or update_dict.get("onu_mac_address") or pppoe_password):
        stmt_target_r = (
            select(Router)
            .options(selectinload(Router.vault))
            .where(Router.id == device.router_id, Router.tenant_id == tenant_id)
        )
        target_r = (await db.execute(stmt_target_r)).scalar_one_or_none()
        if target_r:
            eff_service_type = update_dict.get("service_type") or device.service_type
            eff_ep_id = str(update_dict.get("endpoint_identifier") or device.endpoint_identifier)
            eff_mac = update_dict.get("onu_mac_address") or device.onu_mac_address
            await _provision_subscriber_on_mikrotik(
                r=target_r,
                tenant_id=tenant_id,
                service_type=eff_service_type,
                endpoint_identifier=eff_ep_id,
                assigned_ipv4=raw_assigned_ipv4 or device.assigned_ipv4,
                onu_mac_address=eff_mac,
                pppoe_password=pppoe_password,
            )
```

Además, en `_discover_and_pair_live_ip_from_router` (`fastapi/src/api/v1/subscribers.py`, líneas 1200–1216), añadir el respaldo de búsqueda en los demás routers del tenant (ej. `r111`) cuando el nodo inicial (`r3` Bridge L2) no tenga el lease DHCP o la sesión PPPoE de la ONU, de modo que incluso si el Técnico de Campo pulsa **`🚀 Ejecutar Test Ping (1-Click)`** en `/field-ops` antes de que el NOC abra IPAM, RoSGrid descubra el lease en `r111`, actualice `dev.router_id = candidate_r.id` y ejecute el Ping desde `r111`:

#### `Target` en `fastapi/src/api/v1/subscribers.py` (`_discover_and_pair_live_ip_from_router`):
```python
    except Exception as e:
        logger.warning(f"Auto-descubrimiento en vivo para abonado {dev.endpoint_identifier} falló: {e}")

    if discovered_ip:
        ip_id = await _resolve_or_create_subscriber_ipv4(
            db=db,
            tenant_id=tenant_id,
            router_id=r.id,
            raw_ipv4=discovered_ip,
            mac_address=discovered_mac,
            description=f"Auto-emparejado en vivo ({dev.endpoint_identifier})",
        )
        if ip_id:
            dev.ipv4_address_id = ip_id
            if discovered_mac and not dev.onu_mac_address:
                dev.onu_mac_address = discovered_mac
            await db.commit()
    return discovered_ip
```

#### `Replacement` en `fastapi/src/api/v1/subscribers.py` (`_discover_and_pair_live_ip_from_router`):
```python
    except Exception as e:
        logger.warning(f"Auto-descubrimiento en vivo para abonado {dev.endpoint_identifier} falló: {e}")

    effective_router_id = r.id
    if not discovered_ip and mac_upper:
        stmt_bngs = (
            select(Router)
            .options(selectinload(Router.vault))
            .where(Router.tenant_id == tenant_id, Router.id != r.id)
            .order_by(Router.created_at.asc())
        )
        for cand_r in list((await db.execute(stmt_bngs)).scalars().all()):
            cand_dhcp, cand_pppoe = await _collect_router_live_candidates(cand_r, tenant_id)
            cand_ip = _find_mac_match_in_candidates(mac_upper, cand_dhcp, cand_pppoe)
            if cand_ip:
                discovered_ip = cand_ip
                effective_router_id = cand_r.id
                dev.router_id = cand_r.id
                break

    if discovered_ip:
        ip_id = await _resolve_or_create_subscriber_ipv4(
            db=db,
            tenant_id=tenant_id,
            router_id=effective_router_id,
            raw_ipv4=discovered_ip,
            mac_address=discovered_mac,
            description=f"Auto-emparejado en vivo ({dev.endpoint_identifier})",
        )
        if ip_id:
            dev.ipv4_address_id = ip_id
            if discovered_mac and not dev.onu_mac_address:
                dev.onu_mac_address = discovered_mac
            await db.commit()
    return discovered_ip
```

---

### Paso 3: Actualizar Tipos TypeScript y Store Pinia (`vue3/src/types/index.ts` y `vue3/src/stores/useIpamStore.ts`)

1. En [`vue3/src/types/index.ts`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/types/index.ts) (líneas 567–575):

#### `Target` en `vue3/src/types/index.ts`:
```typescript
export interface SubscriberLiveCandidatesResponse {
  device_id: string;
  router_id: string;
  router_name: string;
  dhcp_leases: SubscriberLiveCandidateDhcpLease[];
  pppoe_sessions: SubscriberLiveCandidatePppoe[];
  ipam_addresses: IPAMAddress[];
}
```

#### `Replacement` en `vue3/src/types/index.ts`:
```typescript
export interface SubscriberLiveCandidatesResponse {
  device_id: string;
  router_id: string;
  router_name: string;
  access_router_id?: string | null;
  access_router_name?: string | null;
  auto_switched_bng?: boolean;
  matched_mac_address?: string | null;
  matched_ipv4?: string | null;
  dhcp_leases: SubscriberLiveCandidateDhcpLease[];
  pppoe_sessions: SubscriberLiveCandidatePppoe[];
  ipam_addresses: IPAMAddress[];
}
```

2. En [`vue3/src/stores/useIpamStore.ts`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/stores/useIpamStore.ts) (líneas 158–190), permitir pasar `bngRouterId` opcional a `fetchSubscriberLiveCandidates` y `bng_router_id`, `pppoe_password` y `provision_on_router` a `pairSubscriberNetwork`:

#### `Target` en `vue3/src/stores/useIpamStore.ts`:
```typescript
  async function fetchSubscriberLiveCandidates(
    deviceId: string,
  ): Promise<import('@/types').SubscriberLiveCandidatesResponse> {
    const { http } = await import('@/api/httpClient');
    const res = await http.get<import('@/types').SubscriberLiveCandidatesResponse>(
      `/api/v1/subscriber-devices/${deviceId}/live-candidates`,
    );
    return res.data;
  }

  async function pairSubscriberNetwork(
    deviceId: string,
    payload: {
      service_type: string;
      endpoint_identifier?: string;
      pppoe_username?: string;
      onu_mac_address?: string;
      onu_mode?: string;
      assigned_ipv4?: string;
      ipv4_address_id?: string | null;
    },
  ): Promise<CustomerService> {
```

#### `Replacement` en `vue3/src/stores/useIpamStore.ts`:
```typescript
  async function fetchSubscriberLiveCandidates(
    deviceId: string,
    bngRouterId?: string,
  ): Promise<import('@/types').SubscriberLiveCandidatesResponse> {
    const { http } = await import('@/api/httpClient');
    const query = bngRouterId ? `?bng_router_id=${encodeURIComponent(bngRouterId)}` : '';
    const res = await http.get<import('@/types').SubscriberLiveCandidatesResponse>(
      `/api/v1/subscriber-devices/${deviceId}/live-candidates${query}`,
    );
    return res.data;
  }

  async function pairSubscriberNetwork(
    deviceId: string,
    payload: {
      bng_router_id?: string;
      provision_on_router?: boolean;
      service_type: string;
      endpoint_identifier?: string;
      pppoe_username?: string;
      pppoe_password?: string;
      onu_mac_address?: string;
      onu_mode?: string;
      assigned_ipv4?: string;
      ipv4_address_id?: string | null;
    },
  ): Promise<CustomerService> {
```

---

### Paso 4: Simplificar el Alta del Técnico de Campo (`/field-ops`) Centrada en MAC WAN en `vue3/src/components/field/FieldTechMobileView.vue`

En [`vue3/src/components/field/FieldTechMobileView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/field/FieldTechMobileView.vue):
1. Añadir `handleNormalizeMac()` para normalizar en 1 clic cualquier formato de MAC al estándar `AA:BB:CC:DD:EE:FF`.
2. En `handleRegisterCustomer()` (líneas 250–283), validar `onu_mac_address` como campo principal requerido (con respaldo de `device_serial` para retrocompatibilidad con tests existentes si solo llenan `device_serial`), normalizando la MAC antes de enviarla y dejando la configuración L3 al NOC en IPAM.
3. En el template de la Pestaña 2 (`activeTab === 'customer'`, líneas 802–879), colocar **`MAC WAN de la ONU (`#cust-onu-mac`) *`** como campo primario junto al puerto NAP, dejando el Serial GPON (`#cust-onu-serial`) como opcional y retirando los campos L3 de red (`#cust-service-proto`, `#cust-onu-mode`, `#cust-assigned-ipv4`).

#### `Target 1` en `vue3/src/components/field/FieldTechMobileView.vue` (líneas 155–165 y 250–283):
```typescript
      customerForm.value.device_serial = raw.replace(/\s+/g, '');
    }
    showMessage(`Serial GPON normalizado: ${customerForm.value.device_serial}`, 'success');
  }
```

#### `Replacement 1` en `vue3/src/components/field/FieldTechMobileView.vue`:
```typescript
      customerForm.value.device_serial = raw.replace(/\s+/g, '');
    }
    showMessage(`Serial GPON normalizado: ${customerForm.value.device_serial}`, 'success');
  }

  function formatNormalizedMac(raw: string): string {
    const hex = raw.trim().toUpperCase().replace(/[^0-9A-F]/g, '');
    if (hex.length === 12) {
      return hex.match(/.{1,2}/g)?.join(':') || raw.trim().toUpperCase();
    }
    return raw.trim().toUpperCase();
  }

  function handleNormalizeMac() {
    if (!customerForm.value.onu_mac_address.trim()) return;
    customerForm.value.onu_mac_address = formatNormalizedMac(customerForm.value.onu_mac_address);
    showMessage(`MAC WAN normalizada: ${customerForm.value.onu_mac_address}`, 'success');
  }
```

#### `Target 2` en `vue3/src/components/field/FieldTechMobileView.vue` (líneas 249–283):
```typescript
  // Registrar Nuevo Cliente FTTH
  async function handleRegisterCustomer() {
    if (!customerForm.value.endpoint_identifier.trim()) {
      showMessage('Ingrese el identificador de servicio del abonado', 'error');
      return;
    }
    if (!customerForm.value.device_serial.trim()) {
      showMessage('Ingrese o escanee el serial de la ONU', 'error');
      return;
    }
    if (!customerForm.value.optical_box_id) {
      showMessage('Seleccione una Caja NAP de conexión', 'error');
      return;
    }

    const box = selectedNapBox.value;
    const routerId = box ? box.router_id : napForm.value.router_id;

    try {
      const dev = await fieldStore.registerSubscriberDevice({
        router_id: routerId,
        endpoint_identifier: customerForm.value.endpoint_identifier.trim(),
        service_type: customerForm.value.service_type,
        assigned_ipv4: customerForm.value.assigned_ipv4.trim() || undefined,
        device_serial: customerForm.value.device_serial.trim().toUpperCase(),
        onu_mac_address: customerForm.value.onu_mac_address.trim() || undefined,
        onu_mode: customerForm.value.onu_mode === 'BRIDGE' ? 'BRIDGE' : 'ROUTER',
        optical_box_id: customerForm.value.optical_box_id,
        optical_box_port: Number(customerForm.value.optical_box_port),
        rx_optical_power_dbm: Number(customerForm.value.rx_optical_power_dbm),
        drop_cable_meters: Number(customerForm.value.drop_cable_meters),
        latitude: Number(customerForm.value.latitude),
        longitude: Number(customerForm.value.longitude),
      });
```

#### `Replacement 2` en `vue3/src/components/field/FieldTechMobileView.vue`:
```typescript
  // Registrar Nuevo Cliente FTTH (Enfoque Planta Física + MAC WAN; el NOC aprovisiona L3 en IPAM)
  async function handleRegisterCustomer() {
    if (!customerForm.value.endpoint_identifier.trim()) {
      showMessage('Ingrese el identificador de servicio del abonado', 'error');
      return;
    }
    const normalizedMac = customerForm.value.onu_mac_address.trim()
      ? formatNormalizedMac(customerForm.value.onu_mac_address)
      : '';
    const rawSerial = customerForm.value.device_serial.trim().toUpperCase();
    if (!normalizedMac && !rawSerial) {
      showMessage('Ingrese la dirección MAC WAN de la ONU (ej. AA:BB:CC:11:22:33)', 'error');
      return;
    }
    if (!customerForm.value.optical_box_id) {
      showMessage('Seleccione una Caja NAP de conexión', 'error');
      return;
    }

    const box = selectedNapBox.value;
    const routerId = box ? box.router_id : napForm.value.router_id;
    const effectiveSerial =
      rawSerial || `MAC-${normalizedMac.replace(/[^0-9A-F]/g, '').slice(-8) || 'ONU'}`;

    try {
      const dev = await fieldStore.registerSubscriberDevice({
        router_id: routerId,
        endpoint_identifier: customerForm.value.endpoint_identifier.trim(),
        service_type: customerForm.value.service_type || 'DHCP',
        assigned_ipv4: customerForm.value.assigned_ipv4.trim() || undefined,
        device_serial: effectiveSerial,
        onu_mac_address: normalizedMac || undefined,
        onu_mode: customerForm.value.onu_mode === 'BRIDGE' ? 'BRIDGE' : 'ROUTER',
        optical_box_id: customerForm.value.optical_box_id,
        optical_box_port: Number(customerForm.value.optical_box_port),
        rx_optical_power_dbm: Number(customerForm.value.rx_optical_power_dbm),
        drop_cable_meters: Number(customerForm.value.drop_cable_meters),
        latitude: Number(customerForm.value.latitude),
        longitude: Number(customerForm.value.longitude),
      });
```

#### `Target 3` en `vue3/src/components/field/FieldTechMobileView.vue` (líneas 802–879):
```html
                  <div class="form-group flex-1">
                    <label for="cust-onu-serial">{{ t('field_tech.serial_onu_label') }} *</label>
                    <div class="input-with-btn">
                      <input
                        id="cust-onu-serial"
                        v-model="customerForm.device_serial"
                        type="text"
                        class="rg-input font-mono flex-1"
                        placeholder="Ej: HWTC1234ABCD"
                        required
                      />
                      <button
                        type="button"
                        class="btn-touch-sm btn-touch--cyan"
                        title="Normalizar prefijos GPON"
                        @click="handleNormalizeSerial"
                      >
                        🔤
                      </button>
                    </div>
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group flex-1">
                    <label for="cust-service-proto">Protocolo de Acceso WAN *</label>
                    <select id="cust-service-proto" v-model="customerForm.service_type" class="rg-input">
                      <option value="DHCP">DHCP (Asignación Dinámica / Option 82)</option>
                      <option value="PPPOE">PPPoE (Túnel BRAS Autenticado)</option>
                      <option value="STATIC_IP">IP Estática (Pool IPAM)</option>
                    </select>
                  </div>

                  <div class="form-group flex-1">
                    <label for="cust-onu-mode">{{ t('field_tech.onu_mode') }}</label>
                    <select id="cust-onu-mode" v-model="customerForm.onu_mode" class="rg-input">
                      <option value="ROUTER">{{ t('field_tech.onu_mode_router') }}</option>
                      <option value="BRIDGE">{{ t('field_tech.onu_mode_bridge') }}</option>
                    </select>
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group flex-1">
                    <label for="cust-onu-model">{{ t('field_tech.onu_model') }}</label>
                    <select id="cust-onu-model" v-model="customerForm.model" class="rg-input">
                      <option value="HG8310M Bridge">Huawei HG8310M (Bridge 1GE)</option>
                      <option value="F601 Bridge">ZTE F601 (Bridge 1GE)</option>
                      <option value="F670L WiFi-6">ZTE F670L (Router Dual-Band AX)</option>
                      <option value="EG8145V5 WiFi">Huawei EG8145V5 (Router AC)</option>
                    </select>
                  </div>

                  <div class="form-group flex-1">
                    <label for="cust-onu-mac">MAC WAN / ONU (Opcional — o emparejar en IPAM)</label>
                    <input
                      id="cust-onu-mac"
                      v-model="customerForm.onu_mac_address"
                      type="text"
                      class="rg-input font-mono"
                      placeholder="Ej: AA:BB:CC:11:22:33"
                    />
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group flex-1">
                    <label for="cust-assigned-ipv4">IPv4 Asignada (Opcional — si ya conoce la IP o Lease)</label>
                    <input
                      id="cust-assigned-ipv4"
                      v-model="customerForm.assigned_ipv4"
                      type="text"
                      class="rg-input font-mono"
                      placeholder="Ej: 10.250.3.55 (Dejar vacío para emparejar luego en IPAM)"
                    />
                  </div>
                </div>
```

#### `Replacement 3` en `vue3/src/components/field/FieldTechMobileView.vue`:
```html
                  <div class="form-group flex-1">
                    <label for="cust-onu-mac">MAC WAN de la ONU (Para Reserva DHCP / PPPoE en NOC) *</label>
                    <div class="input-with-btn">
                      <input
                        id="cust-onu-mac"
                        v-model="customerForm.onu_mac_address"
                        type="text"
                        class="rg-input font-mono flex-1"
                        placeholder="Ej: AA:BB:CC:11:22:33"
                        required
                      />
                      <button
                        type="button"
                        class="btn-touch-sm btn-touch--cyan"
                        title="Normalizar formato MAC (AA:BB:CC:DD:EE:FF)"
                        @click="handleNormalizeMac"
                      >
                        🔤
                      </button>
                    </div>
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group flex-1">
                    <label for="cust-onu-model">{{ t('field_tech.onu_model') }}</label>
                    <select id="cust-onu-model" v-model="customerForm.model" class="rg-input">
                      <option value="HG8310M Bridge">Huawei HG8310M (Bridge 1GE)</option>
                      <option value="F601 Bridge">ZTE F601 (Bridge 1GE)</option>
                      <option value="F670L WiFi-6">ZTE F670L (Router Dual-Band AX)</option>
                      <option value="EG8145V5 WiFi">Huawei EG8145V5 (Router AC)</option>
                    </select>
                  </div>

                  <div class="form-group flex-1">
                    <label for="cust-onu-serial">{{ t('field_tech.serial_onu_label') }} (Opcional — Inventario)</label>
                    <div class="input-with-btn">
                      <input
                        id="cust-onu-serial"
                        v-model="customerForm.device_serial"
                        type="text"
                        class="rg-input font-mono flex-1"
                        placeholder="Ej: HWTC1234ABCD (Opcional)"
                      />
                      <button
                        type="button"
                        class="btn-touch-sm btn-touch--cyan"
                        title="Normalizar prefijos GPON"
                        @click="handleNormalizeSerial"
                      >
                        🔤
                      </button>
                    </div>
                  </div>
                </div>
```

---

### Paso 5: Potenciar el Modal `#modal-pair-subscriber` en `vue3/src/views/IpamManagementView.vue` (Selector de Router Cabecera BNG `r111`, Auto-Match por MAC y Aprovisionamiento DHCP/PPPoE)

En [`vue3/src/views/IpamManagementView.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/IpamManagementView.vue):
1. En `pairForm` (líneas 107–190), añadir `bng_router_id`, `pppoe_password` y `provision_on_router: true`.
2. Cuando `openPairSubscriberModal` recibe `liveCandidates`, actualizar `pairForm.value.bng_router_id = liveCandidates.value.router_id` y, si `liveCandidates.value.matched_ipv4` existe y el abonado aún no tenía IP asignada, autocompletar `pairForm.value.assigned_ipv4 = liveCandidates.value.matched_ipv4` y `selectedDhcpLeaseIp.value = liveCandidates.value.matched_ipv4`.
3. Añadir `handleChangeBngRouter()` para que si el operador NOC cambia manualmente el `Router Cabecera BNG / Servidor DHCP-PPPoE` en el modal, recargue en vivo los leases DHCP y sesiones PPPoE de ese router cabecera.
4. En el template de `#modal-pair-subscriber` (líneas 877–1025), agregar:
   - El indicador de arquitectura desacoplada: `Nodo Físico NAP: r3 • Cabecera BNG/DHCP: r111 (Auto-detectado)`.
   - El selector `#pair-bng-router-select` (`Router Cabecera BNG / Servidor DHCP-PPPoE`).
   - El campo `#pair-pppoe-password` (`Contraseña PPPoE en MikroTik`) cuando `pairForm.service_type === 'PPPOE'`.
   - El interruptor `#chk-provision-mikrotik` (`⚡ Aprovisionar reserva DHCP / secreto PPPoE automáticamente en el MikroTik BNG`).

#### `Target 1` en `vue3/src/views/IpamManagementView.vue` (líneas 107–190):
```typescript
  const pairForm = ref({
    service_type: 'DHCP' as 'DHCP' | 'PPPOE' | 'STATIC',
    onu_mode: 'ROUTER' as 'ROUTER' | 'BRIDGE',
    pppoe_username: '',
    onu_mac_address: '',
    assigned_ipv4: '',
  });

  async function openPairSubscriberModal(sub: CustomerService) {
    selectedSubForPair.value = sub;
    pairErrorMsg.value = '';
    pairSuccessMsg.value = '';
    selectedDhcpLeaseIp.value = '';
    selectedPppoeSessionName.value = '';
    pairForm.value = {
      service_type: (sub.service_type as 'DHCP' | 'PPPOE' | 'STATIC') || 'DHCP',
      onu_mode: (sub.onu_mode === 'BRIDGE' ? 'BRIDGE' : 'ROUTER'),
      pppoe_username: sub.pppoe_username || sub.endpoint_identifier || '',
      onu_mac_address: sub.onu_mac_address || '',
      assigned_ipv4: sub.assigned_ipv4 || '',
    };
    pairModalOpen.value = true;
    isLoadingCandidates.value = true;
    try {
      liveCandidates.value = await ipamStore.fetchSubscriberLiveCandidates(sub.id);
    } catch (err: unknown) {
      pairErrorMsg.value = getErrorMessage(err, 'No se pudieron consultar sesiones en vivo del router.');
    } finally {
      isLoadingCandidates.value = false;
    }
  }

  function handleSelectDhcpCandidate(address: string) {
    selectedDhcpLeaseIp.value = address;
    const found = liveCandidates.value?.dhcp_leases.find((l) => l.address === address);
    if (found) {
      pairForm.value.assigned_ipv4 = found.address;
      if (found.mac_address) {
        pairForm.value.onu_mac_address = found.mac_address;
      }
    }
  }

  function handleSelectPppoeCandidate(name: string) {
    selectedPppoeSessionName.value = name;
    const found = liveCandidates.value?.pppoe_sessions.find((p) => p.name === name);
    if (found) {
      pairForm.value.pppoe_username = found.name;
      if (found.address) {
        pairForm.value.assigned_ipv4 = found.address;
      }
      if (found.caller_id) {
        pairForm.value.onu_mac_address = found.caller_id;
      }
    }
  }

  async function handleSavePairSubscriber() {
    if (!selectedSubForPair.value) return;
    isSavingPair.value = true;
    pairErrorMsg.value = '';
    pairSuccessMsg.value = '';
    try {
      await ipamStore.pairSubscriberNetwork(selectedSubForPair.value.id, {
        service_type: pairForm.value.service_type,
        onu_mode: pairForm.value.onu_mode,
        endpoint_identifier:
          pairForm.value.service_type === 'PPPOE' && pairForm.value.pppoe_username.trim()
            ? pairForm.value.pppoe_username.trim()
            : selectedSubForPair.value.endpoint_identifier || selectedSubForPair.value.customer_name,
        onu_mac_address: pairForm.value.onu_mac_address.trim() || undefined,
        assigned_ipv4: pairForm.value.assigned_ipv4.trim() || undefined,
      });
      pairSuccessMsg.value = 'Abonado emparejado exitosamente. Diagnóstico Ping listo.';
      await ipamStore.fetchCustomerServices();
      setTimeout(() => {
        pairModalOpen.value = false;
      }, 900);
    } catch (err: unknown) {
      pairErrorMsg.value = getErrorMessage(err, 'Error al emparejar red del abonado.');
    } finally {
      isSavingPair.value = false;
    }
  }
```

#### `Replacement 1` en `vue3/src/views/IpamManagementView.vue`:
```typescript
  const pairForm = ref({
    bng_router_id: '',
    provision_on_router: true,
    service_type: 'DHCP' as 'DHCP' | 'PPPOE' | 'STATIC',
    onu_mode: 'ROUTER' as 'ROUTER' | 'BRIDGE',
    pppoe_username: '',
    pppoe_password: '',
    onu_mac_address: '',
    assigned_ipv4: '',
  });

  async function loadLiveCandidatesForPair(subId: string, bngRouterId?: string) {
    isLoadingCandidates.value = true;
    pairErrorMsg.value = '';
    try {
      const candidates = await ipamStore.fetchSubscriberLiveCandidates(subId, bngRouterId);
      liveCandidates.value = candidates;
      if (candidates.router_id) {
        pairForm.value.bng_router_id = candidates.router_id;
      }
      if (candidates.matched_ipv4 && !pairForm.value.assigned_ipv4) {
        pairForm.value.assigned_ipv4 = candidates.matched_ipv4;
        selectedDhcpLeaseIp.value = candidates.matched_ipv4;
      }
    } catch (err: unknown) {
      pairErrorMsg.value = getErrorMessage(err, 'No se pudieron consultar sesiones en vivo del router.');
    } finally {
      isLoadingCandidates.value = false;
    }
  }

  async function openPairSubscriberModal(sub: CustomerService) {
    selectedSubForPair.value = sub;
    pairErrorMsg.value = '';
    pairSuccessMsg.value = '';
    selectedDhcpLeaseIp.value = '';
    selectedPppoeSessionName.value = '';
    pairForm.value = {
      bng_router_id: sub.router_id || '',
      provision_on_router: true,
      service_type: (sub.service_type as 'DHCP' | 'PPPOE' | 'STATIC') || 'DHCP',
      onu_mode: (sub.onu_mode === 'BRIDGE' ? 'BRIDGE' : 'ROUTER'),
      pppoe_username: sub.pppoe_username || sub.endpoint_identifier || '',
      pppoe_password: '',
      onu_mac_address: sub.onu_mac_address || '',
      assigned_ipv4: sub.assigned_ipv4 || '',
    };
    pairModalOpen.value = true;
    await loadLiveCandidatesForPair(sub.id);
  }

  async function handleChangeBngRouter() {
    if (!selectedSubForPair.value || !pairForm.value.bng_router_id) return;
    await loadLiveCandidatesForPair(selectedSubForPair.value.id, pairForm.value.bng_router_id);
  }

  function handleSelectDhcpCandidate(address: string) {
    selectedDhcpLeaseIp.value = address;
    const found = liveCandidates.value?.dhcp_leases.find((l) => l.address === address);
    if (found) {
      pairForm.value.assigned_ipv4 = found.address;
      if (found.mac_address) {
        pairForm.value.onu_mac_address = found.mac_address;
      }
    }
  }

  function handleSelectPppoeCandidate(name: string) {
    selectedPppoeSessionName.value = name;
    const found = liveCandidates.value?.pppoe_sessions.find((p) => p.name === name);
    if (found) {
      pairForm.value.pppoe_username = found.name;
      if (found.address) {
        pairForm.value.assigned_ipv4 = found.address;
      }
      if (found.caller_id) {
        pairForm.value.onu_mac_address = found.caller_id;
      }
    }
  }

  async function handleSavePairSubscriber() {
    if (!selectedSubForPair.value) return;
    isSavingPair.value = true;
    pairErrorMsg.value = '';
    pairSuccessMsg.value = '';
    try {
      await ipamStore.pairSubscriberNetwork(selectedSubForPair.value.id, {
        bng_router_id: pairForm.value.bng_router_id || undefined,
        provision_on_router: pairForm.value.provision_on_router,
        service_type: pairForm.value.service_type,
        onu_mode: pairForm.value.onu_mode,
        endpoint_identifier:
          pairForm.value.service_type === 'PPPOE' && pairForm.value.pppoe_username.trim()
            ? pairForm.value.pppoe_username.trim()
            : selectedSubForPair.value.endpoint_identifier || selectedSubForPair.value.customer_name,
        pppoe_password:
          pairForm.value.service_type === 'PPPOE' && pairForm.value.pppoe_password.trim()
            ? pairForm.value.pppoe_password.trim()
            : undefined,
        onu_mac_address: pairForm.value.onu_mac_address.trim() || undefined,
        assigned_ipv4: pairForm.value.assigned_ipv4.trim() || undefined,
      });
      pairSuccessMsg.value = pairForm.value.provision_on_router
        ? 'Abonado emparejado y aprovisionado en MikroTik exitosamente. Diagnóstico Ping listo.'
        : 'Abonado emparejado en IPAM exitosamente.';
      await ipamStore.fetchCustomerServices();
      setTimeout(() => {
        pairModalOpen.value = false;
      }, 900);
    } catch (err: unknown) {
      pairErrorMsg.value = getErrorMessage(err, 'Error al emparejar red del abonado.');
    } finally {
      isSavingPair.value = false;
    }
  }
```

#### `Target 2` en `vue3/src/views/IpamManagementView.vue` (líneas 878–1010):
```html
          <p class="sub-target-info">
            ONU Serial:
            <strong class="font-mono text-cyan">
              {{ selectedSubForPair?.onu_serial_number || selectedSubForPair?.device_serial || 'S/N' }}
            </strong>
            • Caja NAP:
            <strong class="font-mono">{{ selectedSubForPair?.optical_box || 'S/N' }}</strong>
            <span v-if="liveCandidates?.router_name">
              • Router: <strong>{{ liveCandidates.router_name }}</strong>
            </span>
          </p>

          <div v-if="pairSuccessMsg" class="banner banner--success mb-3">{{ pairSuccessMsg }}</div>
          <div v-if="pairErrorMsg" class="banner banner--error mb-3">{{ pairErrorMsg }}</div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label for="pair-proto-select">Protocolo de Servicio del ISP *</label>
              <select id="pair-proto-select" v-model="pairForm.service_type" class="rg-input">
                <option value="DHCP">DHCP (Asignación por Lease DHCP / Option 82)</option>
                <option value="PPPOE">PPPoE (Sesión / Secreto PPPoE en BRAS)</option>
                <option value="STATIC">IP Estática (Asignación Manual / Pool IPAM)</option>
              </select>
            </div>
            <div class="form-group w-30">
              <label for="pair-onu-mode">Modo ONU</label>
              <select id="pair-onu-mode" v-model="pairForm.onu_mode" class="rg-input">
                <option value="ROUTER">ROUTER (NAT)</option>
                <option value="BRIDGE">BRIDGE</option>
              </select>
            </div>
          </div>

          <!-- Selector en vivo para ISPs con DHCP -->
          <div v-if="pairForm.service_type === 'DHCP'" class="form-group mb-3">
            <label for="pair-dhcp-lease-select">
              🔍 Leases DHCP Activos en el Router ({{ liveCandidates?.dhcp_leases.length || 0 }} detectados)
            </label>
            <select
              id="pair-dhcp-lease-select"
              :value="selectedDhcpLeaseIp"
              class="rg-input font-mono"
              @change="handleSelectDhcpCandidate(($event.target as HTMLSelectElement).value)"
            >
              <option value="">-- Seleccione un Lease DHCP activo o ingrese IP abajo --</option>
              <option
                v-for="lease in liveCandidates?.dhcp_leases || []"
                :key="`${lease.address}-${lease.mac_address}`"
                :value="lease.address"
              >
                {{ lease.address }} — MAC: {{ lease.mac_address || 'S/M' }} — {{ lease.host_name || lease.comment || lease.status || 'bound' }}
              </option>
            </select>
          </div>

          <!-- Selector en vivo para ISPs con PPPoE -->
          <div v-if="pairForm.service_type === 'PPPOE'" class="form-group mb-3">
            <label for="pair-pppoe-session-select">
              🔍 Sesiones / Secretos PPPoE en el Router ({{ liveCandidates?.pppoe_sessions.length || 0 }} detectados)
            </label>
            <select
              id="pair-pppoe-session-select"
              :value="selectedPppoeSessionName"
              class="rg-input font-mono"
              @change="handleSelectPppoeCandidate(($event.target as HTMLSelectElement).value)"
            >
              <option value="">-- Seleccione una Sesión/Secreto PPPoE o ingrese abajo --</option>
              <option
                v-for="ppp in liveCandidates?.pppoe_sessions || []"
                :key="`${ppp.source}-${ppp.name}`"
                :value="ppp.name"
              >
                [{{ ppp.source === 'active' ? 'ACTIVA' : 'SECRET' }}] {{ ppp.name }} — IP: {{ ppp.address || 'Dinámica' }} — Caller: {{ ppp.caller_id || '—' }}
              </option>
            </select>
          </div>

          <!-- Selector de Pool IPAM para IP Estática -->
          <div v-if="pairForm.service_type === 'STATIC'" class="form-group mb-3">
            <label for="pair-ipam-address-select">
              🔍 Direcciones IPv4 Registradas en Pool IPAM ({{ liveCandidates?.ipam_addresses.length || 0 }})
            </label>
            <select
              id="pair-ipam-address-select"
              v-model="pairForm.assigned_ipv4"
              class="rg-input font-mono"
            >
              <option value="">-- Seleccione del Pool IPAM o escriba la IP abajo --</option>
              <option
                v-for="ipItem in liveCandidates?.ipam_addresses || []"
                :key="ipItem.id"
                :value="ipItem.address.split('/')[0]"
              >
                {{ ipItem.address }} ({{ ipItem.status }}) — {{ ipItem.description || 'IPAM' }}
              </option>
            </select>
          </div>

          <div class="form-row">
            <div v-if="pairForm.service_type === 'PPPOE'" class="form-group flex-1">
              <label for="pair-pppoe-user">Usuario PPPoE</label>
              <input
                id="pair-pppoe-user"
                v-model="pairForm.pppoe_username"
                class="rg-input font-mono"
                placeholder="Ej: cliente_ftth_01"
              />
            </div>
            <div class="form-group flex-1">
              <label for="pair-assigned-ipv4">Dirección IPv4 Emparejada (Para Ping y Diagnóstico) *</label>
              <input
                id="pair-assigned-ipv4"
                v-model="pairForm.assigned_ipv4"
                class="rg-input font-mono"
                placeholder="Ej: 10.250.3.55"
                required
              />
            </div>
            <div class="form-group flex-1">
              <label for="pair-onu-mac">MAC WAN / ONU</label>
              <input
                id="pair-onu-mac"
                v-model="pairForm.onu_mac_address"
                class="rg-input font-mono"
                placeholder="AA:BB:CC:11:22:33"
              />
            </div>
          </div>
```

#### `Replacement 2` en `vue3/src/views/IpamManagementView.vue`:
```html
          <p class="sub-target-info">
            MAC WAN ONU:
            <strong class="font-mono text-cyan">
              {{ selectedSubForPair?.onu_mac_address || pairForm.onu_mac_address || 'S/M' }}
            </strong>
            • Caja NAP:
            <strong class="font-mono">{{ selectedSubForPair?.optical_box || 'S/N' }}</strong>
            <span v-if="liveCandidates?.access_router_name">
              • Nodo Físico L2: <strong>{{ liveCandidates.access_router_name }}</strong>
            </span>
            <span v-if="liveCandidates?.router_name">
              • Cabecera BNG/DHCP:
              <strong class="text-green">{{ liveCandidates.router_name }}</strong>
              <span v-if="liveCandidates.auto_switched_bng" class="badge-type">Auto-detectado</span>
            </span>
          </p>

          <div v-if="pairSuccessMsg" class="banner banner--success mb-3">{{ pairSuccessMsg }}</div>
          <div v-if="pairErrorMsg" class="banner banner--error mb-3">{{ pairErrorMsg }}</div>

          <!-- Selector de Router Cabecera BNG / Servidor DHCP-PPPoE (Soporte Bridge L2 r3 -> BNG r111) -->
          <div class="form-group mb-3">
            <label for="pair-bng-router-select">
              🏢 Router Cabecera BNG / Servidor DHCP-PPPoE (Donde vive el Lease DHCP o Secreto PPPoE)
            </label>
            <select
              id="pair-bng-router-select"
              v-model="pairForm.bng_router_id"
              class="rg-input"
              @change="handleChangeBngRouter"
            >
              <option v-for="r in inventoryStore.routers" :key="r.id" :value="r.id">
                {{ r.display_name }} ({{ r.ip_address }})
              </option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label for="pair-proto-select">Protocolo de Servicio del ISP *</label>
              <select id="pair-proto-select" v-model="pairForm.service_type" class="rg-input">
                <option value="DHCP">DHCP (Reserva Estática por MAC en Servidor DHCP)</option>
                <option value="PPPOE">PPPoE (Secreto PPPoE en BRAS + Caller-ID MAC)</option>
                <option value="STATIC">IP Estática (Asignación Manual / Pool IPAM)</option>
              </select>
            </div>
            <div class="form-group w-30">
              <label for="pair-onu-mode">Modo ONU</label>
              <select id="pair-onu-mode" v-model="pairForm.onu_mode" class="rg-input">
                <option value="ROUTER">ROUTER (NAT)</option>
                <option value="BRIDGE">BRIDGE</option>
              </select>
            </div>
          </div>

          <!-- Selector en vivo para ISPs con DHCP -->
          <div v-if="pairForm.service_type === 'DHCP'" class="form-group mb-3">
            <label for="pair-dhcp-lease-select">
              🔍 Leases DHCP Activos en {{ liveCandidates?.router_name || 'Router BNG' }} ({{ liveCandidates?.dhcp_leases.length || 0 }} detectados)
            </label>
            <select
              id="pair-dhcp-lease-select"
              :value="selectedDhcpLeaseIp"
              class="rg-input font-mono"
              @change="handleSelectDhcpCandidate(($event.target as HTMLSelectElement).value)"
            >
              <option value="">-- Seleccione un Lease DHCP activo o elija/escriba IP abajo para crear reserva --</option>
              <option
                v-for="lease in liveCandidates?.dhcp_leases || []"
                :key="`${lease.address}-${lease.mac_address}`"
                :value="lease.address"
              >
                {{ lease.address }} — MAC: {{ lease.mac_address || 'S/M' }} — {{ lease.host_name || lease.comment || lease.status || 'bound' }}
              </option>
            </select>
          </div>

          <!-- Selector en vivo para ISPs con PPPoE -->
          <div v-if="pairForm.service_type === 'PPPOE'" class="form-group mb-3">
            <label for="pair-pppoe-session-select">
              🔍 Sesiones / Secretos PPPoE en {{ liveCandidates?.router_name || 'Router BNG' }} ({{ liveCandidates?.pppoe_sessions.length || 0 }} detectados)
            </label>
            <select
              id="pair-pppoe-session-select"
              :value="selectedPppoeSessionName"
              class="rg-input font-mono"
              @change="handleSelectPppoeCandidate(($event.target as HTMLSelectElement).value)"
            >
              <option value="">-- Seleccione una Sesión/Secreto PPPoE existente o cree uno nuevo abajo --</option>
              <option
                v-for="ppp in liveCandidates?.pppoe_sessions || []"
                :key="`${ppp.source}-${ppp.name}`"
                :value="ppp.name"
              >
                [{{ ppp.source === 'active' ? 'ACTIVA' : 'SECRET' }}] {{ ppp.name }} — IP: {{ ppp.address || 'Dinámica' }} — Caller: {{ ppp.caller_id || '—' }}
              </option>
            </select>
          </div>

          <!-- Selector de Pool IPAM (Disponible para DHCP con reserva nueva, PPPoE con IP fija o IP Estática) -->
          <div v-if="liveCandidates?.ipam_addresses?.length" class="form-group mb-3">
            <label for="pair-ipam-address-select">
              🔍 Seleccionar IPv4 del Pool IPAM ({{ liveCandidates.ipam_addresses.length }} registradas)
            </label>
            <select
              id="pair-ipam-address-select"
              v-model="pairForm.assigned_ipv4"
              class="rg-input font-mono"
            >
              <option value="">-- Seleccione una IP del Pool IPAM o escríbala manualmente abajo --</option>
              <option
                v-for="ipItem in liveCandidates.ipam_addresses"
                :key="ipItem.id"
                :value="ipItem.address.split('/')[0]"
              >
                {{ ipItem.address }} ({{ ipItem.status }}) — {{ ipItem.description || 'IPAM' }}
              </option>
            </select>
          </div>

          <div v-if="pairForm.service_type === 'PPPOE'" class="form-row">
            <div class="form-group flex-1">
              <label for="pair-pppoe-user">Usuario PPPoE (Pre-configurado en ONU) *</label>
              <input
                id="pair-pppoe-user"
                v-model="pairForm.pppoe_username"
                class="rg-input font-mono"
                placeholder="Ej: cliente_ftth_01"
                required
              />
            </div>
            <div class="form-group flex-1">
              <label for="pair-pppoe-password">Contraseña PPPoE (Para crear/actualizar `/ppp/secret`)</label>
              <input
                id="pair-pppoe-password"
                v-model="pairForm.pppoe_password"
                type="password"
                class="rg-input font-mono"
                placeholder="Dejar vacío si el secret ya existe"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group flex-1">
              <label for="pair-assigned-ipv4">Dirección IPv4 Asignada / Reservada *</label>
              <input
                id="pair-assigned-ipv4"
                v-model="pairForm.assigned_ipv4"
                class="rg-input font-mono"
                placeholder="Ej: 10.250.3.55"
                required
              />
            </div>
            <div class="form-group flex-1">
              <label for="pair-onu-mac">MAC WAN de la ONU (Reserva DHCP / Caller-ID PPPoE) *</label>
              <input
                id="pair-onu-mac"
                v-model="pairForm.onu_mac_address"
                class="rg-input font-mono"
                placeholder="AA:BB:CC:11:22:33"
                required
              />
            </div>
          </div>

          <div class="form-group mt-2 mb-2">
            <label class="checkbox-inline" for="chk-provision-mikrotik">
              <input
                id="chk-provision-mikrotik"
                v-model="pairForm.provision_on_router"
                type="checkbox"
              />
              <span>
                ⚡ Aprovisionar automáticamente en MikroTik (Crear Reserva Estática DHCP o `/ppp/secret` con `caller-id` MAC)
              </span>
            </label>
          </div>
```

---

## 3. Aseguramiento de Calidad Level-11X (Regla Cero en Docker Efímero)

1. **Pruebas Unitarias Backend (`fastapi/tests/api/test_ftth_subscriber_pairing_and_ping.unit.py`):**
   - Verificar que `GET /api/v1/subscriber-devices/{id}/live-candidates` cuando la Caja NAP está en `r3` (0 leases DHCP porque es Bridge L2) auto-descubre el servidor DHCP en `r111` (`auto_switched_bng == True`, `access_router_name == "r3"`, `router_name == "r111"`) y hace match automático de `matched_ipv4` por `onu_mac_address`.
   - Verificar que `PATCH /api/v1/subscriber-devices/{id}` con `provision_on_router=True`:
     - En modo `DHCP`: crea o convierte a estático el lease en `/ip/dhcp-server/lease` con `address` y `mac-address`.
     - En modo `PPPOE`: crea o actualiza `/ppp/secret` con `name`, `password`, `remote-address` y `caller-id` igual a la MAC normalizada.
2. **Pruebas Unitarias Frontend (`vue3/src/views/IpamSubscriberPairing.unit.ts` y `vue3/src/components/field/FieldTechMobileView.unit.ts`):**
   - Certificar el alta en `FieldTechMobileView.vue` ingresando únicamente `endpoint_identifier`, `optical_box_id` y `onu_mac_address`.
   - Certificar en `IpamManagementView.vue` el selector `#pair-bng-router-select`, los campos PPPoE (`#pair-pppoe-user`, `#pair-pppoe-password`) y el checkbox `#chk-provision-mikrotik`.
3. **Comandos de Verificación en Contenedores Efímeros (`Rule Zero`) y Reconstrucción Local:**
   ```bash
   docker compose -f fastapi/docker-compose.qa.yml run --rm --T backend-qa pytest tests/api/test_ftth_subscriber_pairing_and_ping.unit.py
   docker compose -f vue3/docker-compose.qa.yml run --rm -T frontend-qa npx vitest run src/views/IpamSubscriberPairing.unit.ts
   ```
