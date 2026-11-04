# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

# Especificación 76: Corrección de `MissingGreenlet` (`HTTP 500`) en Emparejamiento IPAM (`Router.vault`) y Simbología Geométrica Cartográfica (`●` Routers, `■` Cajas NAP, `▲` Clientes) con Anti-Solapamiento Orbital en `UnifiedNetworkMap.vue` (Hito 28.19)

> **Estado:** COMPLETADO AL 100% Y CERTIFICADO EN DOCKER EFÍMERO (Gemini 3.8 Flash High)  
> **Hito Asociado:** Hito 28 (Subhito `28.19`)  
> **Motor de Ejecución Asignado:** Gemini 3.8 Flash (High)  
> **Componentes Afectados:**
> - **Backend (`fastapi/`):**
>   - [fastapi/src/api/v1/subscribers.py](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/subscribers.py) — Precarga ansiosa `.options(selectinload(Router.vault))` en `get_subscriber_live_pairing_candidates`, `ping_subscriber_device_live` y consultas de `Router`, acceso defensivo `r.__dict__.get("vault")` en `_get_router_client`, y herencia automática de coordenadas desde la Caja NAP o Router cuando se registra un abonado sin GPS explícito.
> - **Frontend (`vue3/`):**
>   - [vue3/src/components/network/UnifiedNetworkMap.vue](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/network/UnifiedNetworkMap.vue) — Simbología geométrica triádica (**`●` Círculos = Routers**, **`■` Cuadrados = Cajas NAP**, **`▲` Triángulos = Clientes/ONUs** coloreados según estado), definición completa de reglas CSS globales para `.rg-box-marker` y `.rg-sub-marker` (que antes medían `0×0px`), resolución de coordenadas con herencia de Caja/Router y desplazamiento orbital anti-colisión (`~25m`) cuando múltiples entidades comparten el mismo `[lat, lng]`.
>   - [vue3/src/views/SubscribersMapView.vue](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/SubscribersMapView.vue) — Carga garantizada de `fieldStore.fetchOpticalBoxes()` en `onMounted`.
> - **Pruebas Unitarias y BDD Level-11X:**
>   - [fastapi/tests/api/test_ftth_subscriber_pairing_and_ping.unit.py](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/tests/api/test_ftth_subscriber_pairing_and_ping.unit.py) — Certificación de `get_subscriber_live_pairing_candidates` y `ping_subscriber_device_live` con `Router.vault` precargado sin `MissingGreenlet`.
>   - [vue3/src/components/network/UnifiedNetworkMap.unit.ts](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/network/UnifiedNetworkMap.unit.ts) — Verificación de marcadores geométricos (`■` `.box-square` y `▲` `.sub-triangle-svg`) y desplazamiento orbital anti-solapamiento.

---

## 1. Diagnóstico Forense de Causas Raíz

### 1.1 Error `HTTP 500: Internal Server Error` al Abrir el Modal `🔗 Emparejar Red de Abonado FTTH` en `/ipam`

Al abrir el modal `#modal-pair-subscriber` en `/ipam`, el frontend invoca `GET /api/v1/subscriber-devices/{device_id}/live-candidates`. En los logs del contenedor `rosgrid_api_local` se capturó la siguiente excepción:

```text
  File "/app/src/api/v1/subscribers.py", line 945, in get_subscriber_live_pairing_candidates
    client = _get_router_client(r, tenant_id)
  File "/app/src/api/v1/subscribers.py", line 335, in _get_router_client
    if r.vault:
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; can't call await_() here.
```

- **Causa Raíz 1 (`get_subscriber_live_pairing_candidates` y `ping_subscriber_device_live` en `subscribers.py`):**
  En la línea 936 (`get_subscriber_live_pairing_candidates`) y en la línea 1277 (`ping_subscriber_device_live`), la consulta `stmt_r = select(Router).where(Router.id == dev.router_id, Router.tenant_id == tenant_id)` **omitía `.options(selectinload(Router.vault))`**.
- **Causa Raíz 2 (`_get_router_client` en `subscribers.py` línea 335):**
  La función síncrona `_get_router_client(r: Router, tenant_id: uuid.UUID)` ejecutaba `if r.vault:`. En una `AsyncSession` de SQLAlchemy 2.0, acceder a un atributo de relación (`r.vault`) que no fue precargado con `selectinload` intenta disparar un `SELECT` perezoso síncrono fuera de greenlet, lanzando `MissingGreenlet` (`HTTP 500`).

### 1.2 Por Qué los Clientes (`Clientes / ONUs`) No Se Veían en Ningún Mapa

Al auditar [`UnifiedNetworkMap.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/network/UnifiedNetworkMap.vue) y los registros reales en PostgreSQL (`subscriber_devices`, `optical_boxes`, `routers`), se detectaron **3 fallos simultáneos**:

1. **Ausencia Total de Estilos CSS para `.rg-sub-marker` y `.sub-dot` (`0px × 0px` en el DOM):**
   - En [`UnifiedNetworkMap.vue`](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/network/UnifiedNetworkMap.vue#L478-L487), cada cliente se inyectaba en Leaflet como:
     ```html
     <div class="rg-sub-marker"><span class="sub-dot"></span></div>
     ```
   - Sin embargo, en el bloque `<style>` global al final de `UnifiedNetworkMap.vue` (líneas 1240–1378), **jamás se definieron las clases `.rg-sub-marker`, `.sub-dot` ni `.rg-box-marker`**. Al ser un `<span>` vacío sin `width`, `height` ni `background-color`, el marcador del cliente medía **`0px × 0px` (invisible)**.
2. **Colisión Exacta de Coordenadas (`10.480600, -66.903600`) y Clientes Creados sin GPS:**
   - En la base de datos local, el router (`caps1` / `r111`), la Caja NAP (`123987456`) y el cliente (`qwe123adf`) tienen exactamente la misma coordenada (`10.480600, -66.903600`). Además, cuando un cliente se crea desde `/ipam` sin especificar latitud/longitud, sus coordenadas quedan en `null`.
   - Si el router, la caja NAP y el cliente se dibujan sobre el mismo píxel sin desplazamiento radial (*orbital micro-offset*), los marcadores se tapan unos a otros.
3. **Resolución de `isIspMode` en `UnifiedNetworkMap.vue` (línea 56):**
   - `UnifiedNetworkMap.vue` leía únicamente `Boolean(authStore.tenantFeatures?.isp_module_enabled)` en vez de usar `authStore.isFeatureEnabled('isp_module_enabled') || props.opticalBoxes.length > 0`.

---

## 2. Diseño de la Simbología Geométrica Cartográfica (`●` / `■` / `▲`)

Para maximizar la legibilidad en campo y en el NOC (cumpliendo con **WCAG 2.1 AA** para daltonismo, donde la **forma geométrica** identifica el tipo de elemento y el **color** indica su estado operativo):

| Capa Cartográfica | Forma Geométrica | Símbolo | Colores por Estado Operativo |
| :--- | :--- | :---: | :--- |
| **1. Routers MikroTik** | **Círculo con Pulso** (`.pin-dot`) | `●` | 🟢 `#10B981` Online · 🟠 `#F59E0B` Mantenimiento · 🔴 `#EF4444` Caído |
| **2. Cajas NAP FTTH** | **Cuadrado Táctico** (`16×16px`, `.box-square`) | `■` | 🟢 `#10B981` Libre (`< 80%`) · 🟠 `#F59E0B` Alta Ocupación (`>= 80%`) · 🔴 `#EF4444` Saturada (`100%`) |
| **3. Clientes / ONUs** | **Triángulo Vectorial** (`18×18px`, `.sub-triangle-svg`) | `▲` | 🟢 `#10B981` Online Óptimo · 🟠 `#F59E0B` Degradado / Pendiente · 🔴 `#EF4444` Offline / Suspendido |

---

## 3. Instrucciones Literales de Implementación (Paso a Paso para Gemini 3.8 Flash High)

### Paso 1: Blindar `_get_router_client`, `selectinload(Router.vault)` y Herencia de Coordenadas en `fastapi/src/api/v1/subscribers.py`

1. En [fastapi/src/api/v1/subscribers.py](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/subscribers.py#L333-L342), actualizar `_get_router_client` para inspeccionar `r.__dict__.get("vault")` de forma asíncrona-segura (sin disparar lazy-load):

**Target (`fastapi/src/api/v1/subscribers.py`):**
```python
def _get_router_client(r: Router, tenant_id: uuid.UUID) -> MikrotikRestClient:
    """Obtiene un cliente REST configurado con credenciales descifradas de la bóveda o valores por defecto."""
    if r.vault:
        try:
            return _create_client_from_vault(r, tenant_id)
        except Exception as e:
            logger.warning(f"No se pudieron descifrar credenciales de bóveda para {r.display_name}: {e}")
    host = r.api_base_url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
    return MikrotikRestClient(host=host, port=r.api_port, username="admin", password="")
```

**Replacement (`fastapi/src/api/v1/subscribers.py`):**
```python
def _get_router_client(r: Router, tenant_id: uuid.UUID) -> MikrotikRestClient:
    """Obtiene un cliente REST configurado con credenciales descifradas de la bóveda o valores por defecto."""
    vault_loaded = r.__dict__.get("vault")
    if vault_loaded is not None:
        try:
            return _create_client_from_vault(r, tenant_id)
        except Exception as e:
            logger.warning(f"No se pudieron descifrar credenciales de bóveda para {r.display_name}: {e}")
    host = r.api_base_url.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
    return MikrotikRestClient(host=host, port=r.api_port, username="admin", password="")
```

2. En [fastapi/src/api/v1/subscribers.py](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/subscribers.py#L812-L876) (`create_subscriber_device`), guardar la referencia `router_obj` y heredar sus coordenadas (o las de la Caja NAP) cuando `payload.latitude` o `payload.longitude` sean `None`:

**Target (`fastapi/src/api/v1/subscribers.py`):**
```python
    # Validar que el router pertenezca al tenant
    stmt_r = select(Router).where(Router.id == payload.router_id, Router.tenant_id == tenant_id)
    if not (await db.execute(stmt_r)).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")
```

**Replacement (`fastapi/src/api/v1/subscribers.py`):**
```python
    # Validar que el router pertenezca al tenant
    stmt_r = select(Router).where(Router.id == payload.router_id, Router.tenant_id == tenant_id)
    router_obj = (await db.execute(stmt_r)).scalar_one_or_none()
    if not router_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Router no encontrado")
```

Y unas líneas más abajo en `create_subscriber_device` (líneas 850–876):

**Target (`fastapi/src/api/v1/subscribers.py`):**
```python
    device = SubscriberDevice(
        tenant_id=tenant_id,
        router_id=payload.router_id,
        endpoint_identifier=ep_id,
        service_type=payload.service_type,
        auth_backend=payload.auth_backend,
        bandwidth_profile_id=payload.bandwidth_profile_id,
        ipv4_address_id=resolved_ipv4_id,
        ipv6_delegated_prefix=payload.ipv6_delegated_prefix,
        onu_mode=payload.onu_mode,
        onu_mac_address=payload.onu_mac_address,
        device_serial=serial,
        cpe_wifi_mac_address=payload.cpe_wifi_mac_address,
        pon_port=payload.pon_port,
        optical_box=resolved_box_code,
        optical_box_id=payload.optical_box_id,
        optical_box_port=payload.optical_box_port,
        rx_optical_power_dbm=payload.rx_optical_power_dbm,
        drop_cable_meters=payload.drop_cable_meters,
        is_custom_coordinates=payload.is_custom_coordinates or (payload.latitude is not None and payload.longitude is not None),
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=CustomerServiceStatusEnum.ACTIVE if payload.optical_box_id else CustomerServiceStatusEnum.PENDING_INSTALL,
        last_reachability_status="ONLINE",
    )
```

**Replacement (`fastapi/src/api/v1/subscribers.py`):**
```python
    resolved_lat = payload.latitude if payload.latitude is not None else router_obj.latitude
    resolved_lng = payload.longitude if payload.longitude is not None else router_obj.longitude
    if payload.latitude is None and payload.optical_box_id:
        stmt_box_coords = select(OpticalBox).where(
            OpticalBox.id == payload.optical_box_id,
            OpticalBox.tenant_id == tenant_id,
        )
        box_coords_obj = (await db.execute(stmt_box_coords)).scalar_one_or_none()
        if box_coords_obj and box_coords_obj.latitude is not None and box_coords_obj.longitude is not None:
            resolved_lat = box_coords_obj.latitude
            resolved_lng = box_coords_obj.longitude

    device = SubscriberDevice(
        tenant_id=tenant_id,
        router_id=payload.router_id,
        endpoint_identifier=ep_id,
        service_type=payload.service_type,
        auth_backend=payload.auth_backend,
        bandwidth_profile_id=payload.bandwidth_profile_id,
        ipv4_address_id=resolved_ipv4_id,
        ipv6_delegated_prefix=payload.ipv6_delegated_prefix,
        onu_mode=payload.onu_mode,
        onu_mac_address=payload.onu_mac_address,
        device_serial=serial,
        cpe_wifi_mac_address=payload.cpe_wifi_mac_address,
        pon_port=payload.pon_port,
        optical_box=resolved_box_code,
        optical_box_id=payload.optical_box_id,
        optical_box_port=payload.optical_box_port,
        rx_optical_power_dbm=payload.rx_optical_power_dbm,
        drop_cable_meters=payload.drop_cable_meters,
        is_custom_coordinates=payload.is_custom_coordinates or (payload.latitude is not None and payload.longitude is not None),
        latitude=resolved_lat,
        longitude=resolved_lng,
        status=CustomerServiceStatusEnum.ACTIVE if payload.optical_box_id else CustomerServiceStatusEnum.PENDING_INSTALL,
        last_reachability_status="ONLINE",
    )
```

3. En [fastapi/src/api/v1/subscribers.py](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/fastapi/src/api/v1/subscribers.py#L936-L940) (`get_subscriber_live_pairing_candidates`) y en `ping_subscriber_device_live` (línea 1277), incluir `.options(selectinload(Router.vault))`:

**Target 1 (`fastapi/src/api/v1/subscribers.py` línea 936):**
```python
    stmt_r = select(Router).where(Router.id == dev.router_id, Router.tenant_id == tenant_id)
    r = (await db.execute(stmt_r)).scalar_one_or_none()
```

**Replacement 1 (`fastapi/src/api/v1/subscribers.py`):**
```python
    stmt_r = (
        select(Router)
        .options(selectinload(Router.vault))
        .where(Router.id == dev.router_id, Router.tenant_id == tenant_id)
    )
    r = (await db.execute(stmt_r)).scalar_one_or_none()
```

**Target 2 (`fastapi/src/api/v1/subscribers.py` línea 1277):**
```python
    stmt_r = select(Router).where(Router.id == dev.router_id, Router.tenant_id == tenant_id)
    r = (await db.execute(stmt_r)).scalar_one_or_none()
```

**Replacement 2 (`fastapi/src/api/v1/subscribers.py`):**
```python
    stmt_r = (
        select(Router)
        .options(selectinload(Router.vault))
        .where(Router.id == dev.router_id, Router.tenant_id == tenant_id)
    )
    r = (await db.execute(stmt_r)).scalar_one_or_none()
```

---

### Paso 2: Implementar Marcadores Geométricos (`●` Routers, `■` Cajas NAP, `▲` Clientes), Anti-Solapamiento Orbital y Estilos CSS en `vue3/src/components/network/UnifiedNetworkMap.vue`

1. En [vue3/src/components/network/UnifiedNetworkMap.vue](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/network/UnifiedNetworkMap.vue#L56), actualizar `isIspMode` para que consulte `authStore.isFeatureEnabled('isp_module_enabled')` o detecte cajas ópticas:

**Target (`vue3/src/components/network/UnifiedNetworkMap.vue`):**
```ts
  const isIspMode = computed<boolean>(() => Boolean(authStore.tenantFeatures?.isp_module_enabled));
```

**Replacement (`vue3/src/components/network/UnifiedNetworkMap.vue`):**
```ts
  const isIspMode = computed<boolean>(
    () =>
      authStore.isFeatureEnabled('isp_module_enabled') ||
      Boolean(authStore.tenantFeatures?.isp_module_enabled) ||
      props.opticalBoxes.length > 0,
  );
```

2. En [vue3/src/components/network/UnifiedNetworkMap.vue](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/network/UnifiedNetworkMap.vue#L337-L501), actualizar `getSubscriberColor` y `renderAllLayers()` para:
   - Resolver coordenadas de respaldo en clientes (`s.latitude || box.latitude || router.latitude`).
   - Aplicar un micro-desplazamiento orbital determinista (`~22m` para Cajas NAP y `~32m` en abanico radial para Clientes/ONUs) cuando coincidan en la misma coordenada (`<= 15m`) con un Router o Caja NAP, trazando una línea punteada sutil en `linesLayer`.
   - Renderizar **Cajas NAP como pequeños cuadrados de colores (`■` `.box-square`)** y **Clientes como pequeños triángulos de colores (`▲` `.sub-triangle-svg`)** según su estado:

**Target (`vue3/src/components/network/UnifiedNetworkMap.vue` líneas 337–501):**
```ts
  function getSubscriberColor(sub: SubscriberDeviceItem): string {
    if (sub.last_reachability_status === 'OFFLINE' || sub.status === 'SUSPENDED') {
      return '#EF4444'; // Rojo
    }
    const lat = sub.ping_latency_ms;
    const loss = sub.packet_loss_pct;
    if ((lat !== undefined && lat !== null && lat >= 40) || (loss !== undefined && loss !== null && loss >= 1)) {
      return '#F97316'; // Naranja
    }
    return '#00F0FF'; // Tactical Cyan / Verde
  }

  function renderAllLayers(): void {
    if (!mapInstance || isHeadlessTest.value) return;

    routersLayer?.clearLayers();
    spiderLayer?.clearLayers();
    boxesLayer?.clearLayers();
    subscribersLayer?.clearLayers();
    linesLayer?.clearLayers();

    // 1. Capa de Routers de Red (con soporte para Sitios Compartidos / Co-ubicados)
    if (showRouters.value && routersLayer) {
      const groups = buildLocationGroups(props.routers);

      groups.forEach((grp) => {
        if (grp.routers.length === 1) {
          const r = grp.routers[0];
          const health = getRouterHealth(r);
          const color = health.color;
          const pulseClass = health.pulseClass;

          const icon = L.divIcon({
            className: 'rg-map-pin-container',
            html: `
              <div class="rg-map-pin" style="--pin-color: ${color};" role="button" tabindex="0" title="${escapeHtml(r.display_name)} (${health.label})">
                <div class="pin-pulse ${pulseClass}"></div>
                <div class="pin-dot"></div>
                <span class="pin-router-label">${escapeHtml(r.display_name)}</span>
              </div>
            `,
            iconSize: [24, 24],
            iconAnchor: [12, 12],
          });

          const marker = L.marker([grp.lat, grp.lng], { icon });
          marker.on('click', () => {
            clearSpiderLayer();
            activeRouter.value = r;
            activeLocationGroup.value = null;
            activeBox.value = null;
            activeSubscriber.value = null;
            emit('select-router', r.id);
          });
          routersLayer?.addLayer(marker);
        } else {
          // Múltiples routers co-ubicados (ej. 5 equipos en Guacara)
          const groupHealth = getGroupStatus(grp.routers);
          const count = grp.routers.length;
          const names = grp.routers.map((r) => r.display_name).join(', ');

          const icon = L.divIcon({
            className: 'rg-map-pin-container',
            html: `
              <div class="rg-map-pin rg-map-pin--multi" style="--pin-color: ${groupHealth.color};" role="button" tabindex="0" title="Sitio con ${count} routers: ${escapeHtml(names)}">
                <div class="pin-pulse pin-pulse--multi ${groupHealth.pulseClass}"></div>
                <div class="pin-dot pin-dot--multi">
                  <span class="pin-count-badge">${count}</span>
                </div>
                <span class="pin-router-label pin-router-label--multi">${count} Equipos (${escapeHtml(grp.routers[0].display_name)}+)</span>
              </div>
            `,
            iconSize: [28, 28],
            iconAnchor: [14, 14],
          });

          const marker = L.marker([grp.lat, grp.lng], { icon });
          marker.on('click', () => {
            activeLocationGroup.value = grp;
            activeRouter.value = null;
            activeBox.value = null;
            activeSubscriber.value = null;
            spiderfyGroup(grp);
            if (grp.routers.length > 0) {
              emit('select-router', grp.routers[0].id);
            }
          });
          routersLayer?.addLayer(marker);
        }
      });
    }

    // 2. Capa de Cajas NAP FTTH (Solo en modo ISP)
    if (isIspMode.value && showBoxes.value && boxesLayer) {
      props.opticalBoxes.forEach((b) => {
        const lat = Number(b.latitude);
        const lng = Number(b.longitude);
        if (isNaN(lat) || isNaN(lng) || (lat === 0 && lng === 0)) return;

        const occ = b.occupied_ports_count || 0;
        const cap = b.capacity_ports || 16;
        const isFull = occ >= cap;
        const color = isFull ? '#EF4444' : '#10B981';

        const icon = L.divIcon({
          className: 'rg-box-marker-container',
          html: `
            <div class="rg-box-marker" style="--box-color: ${color};" title="Caja NAP ${escapeHtml(b.box_code)}">
              <span class="box-icon">📦</span>
              <span class="box-badge">${occ}/${cap}</span>
            </div>
          `,
          iconSize: [36, 36],
          iconAnchor: [18, 18],
        });

        const marker = L.marker([lat, lng], { icon });
        marker.on('click', () => {
          activeBox.value = b;
          activeRouter.value = null;
          activeSubscriber.value = null;
          emit('select-box', b.id);
        });
        boxesLayer?.addLayer(marker);
      });
    }

    // 3. Capa de Clientes / Dispositivos
    if (showSubscribers.value && subscribersLayer) {
      props.subscribers.forEach((s) => {
        const lat = Number(s.latitude);
        const lng = Number(s.longitude);
        if (isNaN(lat) || isNaN(lng) || (lat === 0 && lng === 0)) return;

        // Filtrado rápido por estado
        if (statusFilter.value === 'ONLINE' && s.last_reachability_status === 'OFFLINE') return;
        if (statusFilter.value === 'OFFLINE' && s.last_reachability_status !== 'OFFLINE') return;

        const color = getSubscriberColor(s);
        const isDownByRouter = downRouters.value.some((r) => r.id === s.router_id);

        const icon = L.divIcon({
          className: 'rg-sub-marker-container',
          html: `
            <div class="rg-sub-marker ${isDownByRouter ? 'sub-rca-pulse' : ''}" style="--sub-color: ${color};" title="${escapeHtml(s.endpoint_identifier)}">
              <span class="sub-dot"></span>
            </div>
          `,
          iconSize: [20, 20],
          iconAnchor: [10, 10],
        });

        const marker = L.marker([lat, lng], { icon });
        marker.on('click', async () => {
          activeSubscriber.value = s;
          activeRouter.value = null;
          activeBox.value = null;
          emit('select-subscriber', s.id);
          // Consultar lock operativo y causa raíz en vivo
          operationalLock.value = await fieldOpsStore.fetchOperationalStatus(s.id);
        });
        subscribersLayer?.addLayer(marker);
      });
    }
  }
```

**Replacement (`vue3/src/components/network/UnifiedNetworkMap.vue`):**
```ts
  function getSubscriberColor(sub: SubscriberDeviceItem): string {
    if (sub.last_reachability_status === 'OFFLINE' || sub.status === 'SUSPENDED') {
      return '#EF4444'; // Rojo (Caído / Aislado)
    }
    const lat = sub.ping_latency_ms;
    const loss = sub.packet_loss_pct;
    if (
      sub.status === 'PENDING_INSTALL' ||
      (lat !== undefined && lat !== null && lat >= 40) ||
      (loss !== undefined && loss !== null && loss >= 1)
    ) {
      return '#F59E0B'; // Naranja (Degradado / Pendiente)
    }
    return '#10B981'; // Verde Esmeralda (Online Óptimo)
  }

  function resolveSubscriberBaseCoords(s: SubscriberDeviceItem): [number, number] | null {
    const rawLat = Number(s.latitude);
    const rawLng = Number(s.longitude);
    if (!Number.isNaN(rawLat) && !Number.isNaN(rawLng) && !(rawLat === 0 && rawLng === 0)) {
      return [rawLat, rawLng];
    }
    if (s.optical_box_id || s.optical_box) {
      const parentBox = props.opticalBoxes.find(
        (b) => b.id === s.optical_box_id || b.box_code === s.optical_box,
      );
      if (parentBox) {
        const bLat = Number(parentBox.latitude);
        const bLng = Number(parentBox.longitude);
        if (!Number.isNaN(bLat) && !Number.isNaN(bLng) && !(bLat === 0 && bLng === 0)) {
          return [bLat, bLng];
        }
      }
    }
    if (s.router_id) {
      const parentRouter = props.routers.find((r) => r.id === s.router_id);
      if (parentRouter) {
        const rLat = Number(parentRouter.latitude);
        const rLng = Number(parentRouter.longitude);
        if (!Number.isNaN(rLat) && !Number.isNaN(rLng) && !(rLat === 0 && rLng === 0)) {
          return [rLat, rLng];
        }
      }
    }
    return null;
  }

  function renderAllLayers(): void {
    if (!mapInstance || isHeadlessTest.value) return;

    routersLayer?.clearLayers();
    spiderLayer?.clearLayers();
    boxesLayer?.clearLayers();
    subscribersLayer?.clearLayers();
    linesLayer?.clearLayers();

    const groups = buildLocationGroups(props.routers);

    // 1. Capa de Routers de Red (● Círculos de color con soporte para Sitios Co-ubicados)
    if (showRouters.value && routersLayer) {
      groups.forEach((grp) => {
        if (grp.routers.length === 1) {
          const r = grp.routers[0];
          const health = getRouterHealth(r);
          const color = health.color;
          const pulseClass = health.pulseClass;

          const icon = L.divIcon({
            className: 'rg-map-pin-container',
            html: `
              <div class="rg-map-pin" style="--pin-color: ${color};" role="button" tabindex="0" title="${escapeHtml(r.display_name)} (${health.label})">
                <div class="pin-pulse ${pulseClass}"></div>
                <div class="pin-dot"></div>
                <span class="pin-router-label">${escapeHtml(r.display_name)}</span>
              </div>
            `,
            iconSize: [24, 24],
            iconAnchor: [12, 12],
          });

          const marker = L.marker([grp.lat, grp.lng], { icon });
          marker.on('click', () => {
            clearSpiderLayer();
            activeRouter.value = r;
            activeLocationGroup.value = null;
            activeBox.value = null;
            activeSubscriber.value = null;
            emit('select-router', r.id);
          });
          routersLayer?.addLayer(marker);
        } else {
          const groupHealth = getGroupStatus(grp.routers);
          const count = grp.routers.length;
          const names = grp.routers.map((r) => r.display_name).join(', ');

          const icon = L.divIcon({
            className: 'rg-map-pin-container',
            html: `
              <div class="rg-map-pin rg-map-pin--multi" style="--pin-color: ${groupHealth.color};" role="button" tabindex="0" title="Sitio con ${count} routers: ${escapeHtml(names)}">
                <div class="pin-pulse pin-pulse--multi ${groupHealth.pulseClass}"></div>
                <div class="pin-dot pin-dot--multi">
                  <span class="pin-count-badge">${count}</span>
                </div>
                <span class="pin-router-label pin-router-label--multi">${count} Equipos (${escapeHtml(grp.routers[0].display_name)}+)</span>
              </div>
            `,
            iconSize: [28, 28],
            iconAnchor: [14, 14],
          });

          const marker = L.marker([grp.lat, grp.lng], { icon });
          marker.on('click', () => {
            activeLocationGroup.value = grp;
            activeRouter.value = null;
            activeBox.value = null;
            activeSubscriber.value = null;
            spiderfyGroup(grp);
            if (grp.routers.length > 0) {
              emit('select-router', grp.routers[0].id);
            }
          });
          routersLayer?.addLayer(marker);
        }
      });
    }

    // 2. Capa de Cajas NAP FTTH (■ Pequeños cuadrados de colores según ocupación)
    const renderedBoxCoords = new Map<string, [number, number]>();
    if (isIspMode.value && showBoxes.value && boxesLayer) {
      props.opticalBoxes.forEach((b, boxIdx) => {
        const baseLat = Number(b.latitude);
        const baseLng = Number(b.longitude);
        if (Number.isNaN(baseLat) || Number.isNaN(baseLng) || (baseLat === 0 && baseLng === 0)) return;

        let lat = baseLat;
        let lng = baseLng;
        const collidesWithRouter = groups.some((g) => getDistanceMeters(g.lat, g.lng, baseLat, baseLng) <= 18);
        if (collidesWithRouter) {
          const angle = Math.PI / 4 + boxIdx * (Math.PI / 3);
          lat = baseLat + 0.00022 * Math.sin(angle);
          lng = baseLng + 0.00022 * Math.cos(angle);
          try {
            const feederLine = L.polyline([[baseLat, baseLng], [lat, lng]], {
              color: '#10B981',
              weight: 1.5,
              opacity: 0.65,
              dashArray: '4, 4',
            });
            linesLayer?.addLayer(feederLine);
          } catch {
            // Ignorar en entorno JSDOM sin motor vectorial
          }
        }
        renderedBoxCoords.set(b.id, [lat, lng]);

        const occ = b.occupied_ports_count || 0;
        const cap = b.capacity_ports || 16;
        const ratio = cap > 0 ? occ / cap : 0;
        const color = occ >= cap ? '#EF4444' : ratio >= 0.8 ? '#F59E0B' : '#10B981';

        const icon = L.divIcon({
          className: 'rg-box-marker-container',
          html: `
            <div class="rg-box-marker" style="--box-color: ${color};" role="button" tabindex="0" title="Caja NAP ${escapeHtml(b.box_code)} (${occ}/${cap} puertos)">
              <div class="box-square"></div>
              <span class="box-badge">${escapeHtml(b.box_code)} · ${occ}/${cap}</span>
            </div>
          `,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });

        const marker = L.marker([lat, lng], { icon });
        marker.on('click', () => {
          activeBox.value = b;
          activeRouter.value = null;
          activeLocationGroup.value = null;
          activeSubscriber.value = null;
          emit('select-box', b.id);
        });
        boxesLayer?.addLayer(marker);
      });
    }

    // 3. Capa de Clientes / Dispositivos (▲ Pequeños triángulos de colores según estado)
    if (showSubscribers.value && subscribersLayer) {
      const anchorBuckets = new Map<string, number>();

      props.subscribers.forEach((s) => {
        // Filtrado rápido por estado
        if (statusFilter.value === 'ONLINE' && s.last_reachability_status === 'OFFLINE') return;
        if (statusFilter.value === 'OFFLINE' && s.last_reachability_status !== 'OFFLINE') return;

        const baseCoords = resolveSubscriberBaseCoords(s);
        if (!baseCoords) return;

        let [lat, lng] = baseCoords;
        const anchorKey = `${lat.toFixed(4)},${lng.toFixed(4)}`;
        const subIndexAtAnchor = anchorBuckets.get(anchorKey) || 0;
        anchorBuckets.set(anchorKey, subIndexAtAnchor + 1);

        const collidesWithRouterOrBox =
          subIndexAtAnchor > 0 ||
          groups.some((g) => getDistanceMeters(g.lat, g.lng, lat, lng) <= 20) ||
          props.opticalBoxes.some(
            (b) => getDistanceMeters(Number(b.latitude), Number(b.longitude), lat, lng) <= 20,
          );

        const originLat = lat;
        const originLng = lng;
        if (collidesWithRouterOrBox) {
          const angle = -Math.PI / 3 + subIndexAtAnchor * ((2 * Math.PI) / 8);
          const radiusDeg = 0.00032 + Math.floor(subIndexAtAnchor / 8) * 0.00018;
          lat = originLat + radiusDeg * Math.sin(angle);
          lng = originLng + radiusDeg * Math.cos(angle);

          const parentBoxRendered = s.optical_box_id ? renderedBoxCoords.get(s.optical_box_id) : undefined;
          const lineStart: [number, number] = parentBoxRendered || [originLat, originLng];
          try {
            const dropLine = L.polyline([lineStart, [lat, lng]], {
              color: '#38BDF8',
              weight: 1.2,
              opacity: 0.55,
              dashArray: '2, 4',
            });
            linesLayer?.addLayer(dropLine);
          } catch {
            // Ignorar en entorno JSDOM
          }
        }

        const color = getSubscriberColor(s);
        const isDownByRouter = downRouters.value.some((r) => r.id === s.router_id);
        const labelText = s.customer_name || s.endpoint_identifier;

        const icon = L.divIcon({
          className: 'rg-sub-marker-container',
          html: `
            <div class="rg-sub-marker ${isDownByRouter ? 'sub-rca-pulse' : ''}" style="--sub-color: ${color};" role="button" tabindex="0" title="Cliente: ${escapeHtml(labelText)} (${s.last_reachability_status || 'ONLINE'})">
              <svg class="sub-triangle-svg" viewBox="0 0 20 20" width="18" height="18" aria-hidden="true">
                <polygon points="10,2 19,18 1,18" fill="${color}" stroke="#0B0F19" stroke-width="2.2" stroke-linejoin="round" />
              </svg>
              <span class="sub-dot"></span>
              <span class="sub-label">${escapeHtml(labelText)}</span>
            </div>
          `,
          iconSize: [22, 22],
          iconAnchor: [11, 11],
        });

        const marker = L.marker([lat, lng], { icon });
        marker.on('click', async () => {
          activeSubscriber.value = s;
          activeRouter.value = null;
          activeLocationGroup.value = null;
          activeBox.value = null;
          emit('select-subscriber', s.id);
          operationalLock.value = await fieldOpsStore.fetchOperationalStatus(s.id);
        });
        subscribersLayer?.addLayer(marker);
      });
    }
  }
```

3. En la barra de herramientas `<header class="unified-map-toolbar">` de [vue3/src/components/network/UnifiedNetworkMap.vue](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/network/UnifiedNetworkMap.vue#L576-L612), actualizar los iconos de los 3 botones de capa para que muestren la leyenda geométrica (`●` Routers, `■` Cajas NAP, `▲` Clientes):

**Target (`vue3/src/components/network/UnifiedNetworkMap.vue`):**
```vue
        <button
          type="button"
          class="btn-layer-toggle btn-layer-routers"
          :class="{ 'btn-layer-toggle--active': showRouters }"
          :aria-pressed="showRouters ? 'true' : 'false'"
          @click="showRouters = !showRouters"
        >
          <span class="icon">🏢</span>
          <span class="label">{{ t('network_map.layer_routers') }}</span>
          <span class="counter">({{ routers.length }})</span>
        </button>

        <button
          v-if="isIspMode"
          type="button"
          class="btn-layer-toggle btn-layer-boxes"
          :class="{ 'btn-layer-toggle--active': showBoxes }"
          :aria-pressed="showBoxes ? 'true' : 'false'"
          @click="showBoxes = !showBoxes"
        >
          <span class="icon">📦</span>
          <span class="label">{{ t('network_map.layer_boxes') }}</span>
          <span class="counter">({{ opticalBoxes.length }})</span>
        </button>

        <button
          type="button"
          class="btn-layer-toggle btn-layer-subs"
          :class="{ 'btn-layer-toggle--active': showSubscribers }"
          :aria-pressed="showSubscribers ? 'true' : 'false'"
          @click="showSubscribers = !showSubscribers"
        >
          <span class="icon">💻</span>
          <span class="label">{{ t('network_map.layer_subs') }}</span>
          <span class="counter">({{ subscribers.length }})</span>
        </button>
```

**Replacement (`vue3/src/components/network/UnifiedNetworkMap.vue`):**
```vue
        <button
          type="button"
          class="btn-layer-toggle btn-layer-routers"
          :class="{ 'btn-layer-toggle--active': showRouters }"
          :aria-pressed="showRouters ? 'true' : 'false'"
          @click="showRouters = !showRouters"
        >
          <span class="icon shape-legend shape-legend--circle" aria-hidden="true">●</span>
          <span class="label">{{ t('network_map.layer_routers') }}</span>
          <span class="counter">({{ routers.length }})</span>
        </button>

        <button
          v-if="isIspMode"
          type="button"
          class="btn-layer-toggle btn-layer-boxes"
          :class="{ 'btn-layer-toggle--active': showBoxes }"
          :aria-pressed="showBoxes ? 'true' : 'false'"
          @click="showBoxes = !showBoxes"
        >
          <span class="icon shape-legend shape-legend--square" aria-hidden="true">■</span>
          <span class="label">{{ t('network_map.layer_boxes') }}</span>
          <span class="counter">({{ opticalBoxes.length }})</span>
        </button>

        <button
          type="button"
          class="btn-layer-toggle btn-layer-subs"
          :class="{ 'btn-layer-toggle--active': showSubscribers }"
          :aria-pressed="showSubscribers ? 'true' : 'false'"
          @click="showSubscribers = !showSubscribers"
        >
          <span class="icon shape-legend shape-legend--triangle" aria-hidden="true">▲</span>
          <span class="label">{{ t('network_map.layer_subs') }}</span>
          <span class="counter">({{ subscribers.length }})</span>
        </button>
```

4. Al final del bloque `<style>` global de [vue3/src/components/network/UnifiedNetworkMap.vue](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/components/network/UnifiedNetworkMap.vue#L1340-L1378), añadir las reglas CSS de `.rg-box-marker-container`, `.rg-box-marker`, `.box-square`, `.box-badge`, `.rg-sub-marker-container`, `.rg-sub-marker`, `.sub-triangle-svg`, `.sub-label` y `.sub-rca-pulse`:

**Target (`vue3/src/components/network/UnifiedNetworkMap.vue`):**
```css
.pin-router-label--multi {
  border-color: rgba(0, 240, 255, 0.4);
  color: #00F0FF;
}

@keyframes pin-pulsate {
```

**Replacement (`vue3/src/components/network/UnifiedNetworkMap.vue`):**
```css
.pin-router-label--multi {
  border-color: rgba(0, 240, 255, 0.4);
  color: #00F0FF;
}

/* Marcadores Geométricos de Cajas NAP (■ Cuadrados de Colores) */
.rg-box-marker-container {
  background: transparent !important;
  border: none !important;
}

.rg-box-marker {
  width: 24px;
  height: 24px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.box-square {
  width: 15px;
  height: 15px;
  background-color: var(--box-color, #10B981);
  border: 2px solid #0B0F19;
  border-radius: 3px;
  box-shadow: 0 0 10px var(--box-color, #10B981);
  z-index: 2;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.rg-box-marker:hover .box-square {
  transform: scale(1.25);
  box-shadow: 0 0 15px var(--box-color, #10B981);
}

.box-badge {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 3px;
  background: rgba(11, 15, 25, 0.92);
  color: #E2E8F0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 3px;
  white-space: nowrap;
  border: 1px solid var(--box-color, #10B981);
  pointer-events: none;
  z-index: 3;
}

/* Marcadores Geométricos de Clientes / ONUs (▲ Triángulos de Colores) */
.rg-sub-marker-container {
  background: transparent !important;
  border: none !important;
}

.rg-sub-marker {
  width: 22px;
  height: 22px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.sub-triangle-svg {
  filter: drop-shadow(0 0 6px var(--sub-color, #10B981));
  z-index: 2;
  transition: transform 0.2s ease, filter 0.2s ease;
}

.rg-sub-marker:hover .sub-triangle-svg {
  transform: scale(1.28);
  filter: drop-shadow(0 0 12px var(--sub-color, #10B981));
}

.sub-dot {
  display: none;
}

.sub-label {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 2px;
  background: rgba(11, 15, 25, 0.9);
  color: #F8FAFC;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.64rem;
  padding: 1px 4px;
  border-radius: 3px;
  white-space: nowrap;
  border: 1px solid rgba(255, 255, 255, 0.18);
  pointer-events: none;
  z-index: 3;
}

.sub-rca-pulse .sub-triangle-svg {
  animation: pin-pulsate-danger 1.2s infinite ease-out;
}

@keyframes pin-pulsate {
```

---

### Paso 3: Cargar Cajas Ópticas Siempre en `SubscribersMapView.vue`

En [vue3/src/views/SubscribersMapView.vue](file:///home/sinfallas/Dropbox/git/tecno-consultores/RoSGrid/vue3/src/views/SubscribersMapView.vue#L325-L331), cargar `fieldStore.fetchOpticalBoxes()` incondicionalmente en `onMounted` para que las Cajas NAP y sus coordenadas de respaldo estén disponibles incluso antes de que termine de hidratar `tenantFeatures`:

**Target (`vue3/src/views/SubscribersMapView.vue`):**
```ts
  onMounted(async () => {
    await Promise.all([
      loadSubscriberDevices(),
      loadRouters(),
      isIspMode.value ? fieldStore.fetchOpticalBoxes() : Promise.resolve(),
    ]);
  });
```

**Replacement (`vue3/src/views/SubscribersMapView.vue`):**
```ts
  onMounted(async () => {
    await Promise.allSettled([
      loadSubscriberDevices(),
      loadRouters(),
      fieldStore.fetchOpticalBoxes(),
    ]);
  });
```

---

### Paso 4: Ejecución de Pruebas Level-11X y Reconstrucción Local

```bash
# 1. Ejecutar suite unitaria de backend para emparejamiento IPAM y ping
docker compose -f fastapi/docker-compose.qa.yml run --rm api-qa pytest tests/api/test_ftth_subscriber_pairing_and_ping.unit.py -q

# 2. Ejecutar suite unitaria de frontend para UnifiedNetworkMap y SubscribersMapView
docker compose -f vue3/docker-compose.qa.yml run --rm vue-qa sh -c "pnpm run type-check && npx vitest run src/components/network/UnifiedNetworkMap.unit.ts src/views/subscribersMapView.unit.ts"

# 3. Reconstruir imágenes local-test y recrear entorno local
docker build -t sinfallas/rosgrid-backend:local-test ./fastapi
docker build -t sinfallas/rosgrid-frontend:local-test ./vue3
docker compose -f docker-compose.prod.local.yml up -d
```
