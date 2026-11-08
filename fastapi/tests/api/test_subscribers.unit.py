# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias aisladas para endpoints de perfiles de ancho de banda y dispositivos de abonados."""

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient

from src.api.v1.auth import create_jwt_access_token
from src.db.session import get_tenant_db_session
from src.main import app
from src.models.core import SystemRoleEnum
from src.models.inventory import Router, RouterAdminStateEnum, RouterNetworkRoleEnum
from src.models.ipam import (
    BandwidthProfile,
    FieldInstallationOrder,
    OpticalBox,
    SubscriberDevice,
)
from tests.conftest import FakeAsyncRedis


async def fake_audit(**kwargs: Any) -> None:
    pass


class MockSubscribersDbScalars:
    def __init__(self, items: list[Any]):
        self._items = items

    def all(self) -> list[Any]:
        return self._items


class MockSubscribersDbResult:
    def __init__(self, item: Any = None, items: list[Any] | None = None, scalar_val: Any = None):
        self._item = item
        self._items = items or ([item] if item is not None else [])
        self._scalar_val = scalar_val

    def scalar_one_or_none(self) -> Any:
        return self._item

    def scalar_one(self) -> Any:
        if self._item is None:
            raise ValueError("No item found")
        return self._item

    def scalar(self) -> Any:
        return self._scalar_val if self._scalar_val is not None else (self._item if self._item is not None else 0)

    def scalars(self) -> MockSubscribersDbScalars:
        return MockSubscribersDbScalars(self._items)


class MockSubscribersDbSession:
    def __init__(self, tenant_id: uuid.UUID):
        self.tenant_id = tenant_id
        self.profiles: list[BandwidthProfile] = []
        self.devices: list[SubscriberDevice] = []
        self.routers: list[Router] = [
            Router(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                display_name="BRAS-Caracas-01",
                api_base_url="https://10.250.3.8:443",
                api_port=443,
                network_role=RouterNetworkRoleEnum.BRAS_PPPOE,
                admin_state=RouterAdminStateEnum.PRODUCTION,
                physical_location="POP Centro",
            )
        ]
        self.optical_boxes: list[OpticalBox] = []
        self.orders: list[FieldInstallationOrder] = []
        self.deleted: list[Any] = []

    def add(self, obj: Any) -> None:
        now = datetime.now(UTC)
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        if getattr(obj, "created_at", None) is None:
            obj.created_at = now
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = now
        if hasattr(obj, "last_reachability_status") and not getattr(obj, "last_reachability_status", None):
            obj.last_reachability_status = "ONLINE"

        if isinstance(obj, BandwidthProfile):
            self.profiles.append(obj)
        elif isinstance(obj, SubscriberDevice):
            self.devices.append(obj)
        elif isinstance(obj, OpticalBox):
            self.optical_boxes.append(obj)
        elif isinstance(obj, FieldInstallationOrder):
            self.orders.append(obj)

    async def commit(self) -> None:
        pass

    async def flush(self) -> None:
        pass

    async def refresh(self, obj: Any) -> None:
        pass

    async def delete(self, obj: Any) -> None:
        self.deleted.append(obj)
        if isinstance(obj, BandwidthProfile) and obj in self.profiles:
            self.profiles.remove(obj)
        elif isinstance(obj, SubscriberDevice) and obj in self.devices:
            self.devices.remove(obj)
        elif isinstance(obj, OpticalBox) and obj in self.optical_boxes:
            self.optical_boxes.remove(obj)

    async def execute(self, stmt: Any, params: dict[str, Any] | None = None) -> MockSubscribersDbResult:
        stmt_str = str(stmt).lower()

        # Count queries (e.g. subscriber count for bandwidth profile)
        if "count(" in stmt_str and "subscriber_devices" in stmt_str:
            return MockSubscribersDbResult(scalar_val=len(self.devices))

        if "from optical_boxes" in stmt_str:
            target_box = None
            try:
                compiled_params = stmt.compile().params
                for val in compiled_params.values():
                    for b in self.optical_boxes:
                        if b.id == val:
                            target_box = b
                            break
            except Exception:
                pass
            if not target_box and self.optical_boxes:
                target_box = self.optical_boxes[0]
            return MockSubscribersDbResult(target_box, self.optical_boxes)

        if "from bandwidth_profiles" in stmt_str:
            item = self.profiles[0] if self.profiles else None
            return MockSubscribersDbResult(item, self.profiles)

        if "from subscriber_devices" in stmt_str:
            try:
                compiled_params = stmt.compile().params
                p_box_id = None
                p_port = None
                has_ep_check = False
                for k, v in compiled_params.items():
                    if "optical_box_id" in k:
                        p_box_id = v
                    elif "optical_box_port" in k:
                        p_port = v
                    elif "endpoint_identifier" in k:
                        has_ep_check = True
                        for d in self.devices:
                            if d.endpoint_identifier == v:
                                return MockSubscribersDbResult(d, [d])
                if has_ep_check:
                    return MockSubscribersDbResult(None, [])

                if p_box_id is not None and p_port is not None:
                    for d in self.devices:
                        if getattr(d, "optical_box_id", None) == p_box_id and getattr(d, "optical_box_port", None) == p_port:
                            return MockSubscribersDbResult(d, [d])
                    return MockSubscribersDbResult(None, [])

                for k, v in compiled_params.items():
                    if isinstance(v, uuid.UUID):
                        for d in self.devices:
                            if d.id == v:
                                return MockSubscribersDbResult(d, [d])
            except Exception:
                pass
            item = self.devices[0] if self.devices else None
            return MockSubscribersDbResult(item, self.devices)

        if "from routers" in stmt_str:
            item = self.routers[0] if self.routers else None
            return MockSubscribersDbResult(item, self.routers)

        if "from field_installation_orders" in stmt_str:
            item = self.orders[0] if self.orders else None
            return MockSubscribersDbResult(item, self.orders)

        return MockSubscribersDbResult(None, [])


@pytest.fixture
def subscriber_auth(fake_redis: FakeAsyncRedis) -> dict[str, Any]:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    sid = "sess-sub-001"
    sess_key = f"rg:{tid}:sess:{sid}"

    import asyncio

    asyncio.get_event_loop().run_until_complete(
        fake_redis.hset(
            sess_key,
            mapping={
                "session_id": sid,
                "user_id": str(uid),
                "username": "nocoperator",
                "role": SystemRoleEnum.TENANT_ADMIN.value,
            },
        )
    )

    token = create_jwt_access_token(str(uid), str(tid), "tenant-sub", sid, SystemRoleEnum.TENANT_ADMIN.value, True)
    return {
        "headers": {
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": str(uuid.uuid4()),
        },
        "tenant_id": tid,
        "user_id": uid,
        "token": token,
    }


@pytest.mark.asyncio
async def test_bandwidth_profiles_crud_and_scripts(
    async_client: AsyncClient, subscriber_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("src.api.v1.subscribers.write_audit_log", fake_audit)
    tid = subscriber_auth["tenant_id"]
    headers = subscriber_auth["headers"]
    mock_db = MockSubscribersDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    try:
        # 1. Crear perfil de ancho de banda
        create_payload = {
            "name": "Plan-Fibra-100M",
            "rate_down_kbps": 102400,
            "rate_up_kbps": 51200,
            "burst_down_kbps": 122880,
            "burst_up_kbps": 61440,
            "burst_threshold_down_kbps": 81920,
            "burst_threshold_up_kbps": 40960,
            "burst_time_seconds": 16,
            "priority": 4,
            "queue_type": "pcq-download-custom",
        }
        res_post = await async_client.post("/api/v1/bandwidth-profiles", json=create_payload, headers=headers)
        assert res_post.status_code == 201
        p_data = res_post.json()
        assert p_data["name"] == "Plan-Fibra-100M"
        assert p_data["rate_down_kbps"] == 102400
        p_id = p_data["id"]

        # 2. Listar perfiles
        res_list = await async_client.get("/api/v1/bandwidth-profiles", headers=headers)
        assert res_list.status_code == 200
        assert len(res_list.json()) >= 1

        # 3. Obtener perfil por ID
        res_get = await async_client.get(f"/api/v1/bandwidth-profiles/{p_id}", headers=headers)
        assert res_get.status_code == 200
        assert res_get.json()["name"] == "Plan-Fibra-100M"

        # 4. Actualizar perfil (PATCH)
        res_patch = await async_client.patch(
            f"/api/v1/bandwidth-profiles/{p_id}",
            json={"priority": 2, "burst_time_seconds": 24},
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_patch.status_code == 200
        assert res_patch.json()["priority"] == 2

        # 5. Generar script MikroTik
        res_script = await async_client.get(
            f"/api/v1/bandwidth-profiles/{p_id}/mikrotik-script?target_ip=100.64.0.10",
            headers=headers,
        )
        assert res_script.status_code == 200
        script_data = res_script.json()
        assert "queue/simple/add" in script_data["simple_queue_command"]
        assert "queue/tree/add" in script_data["queue_tree_download_command"]

        # 6. Eliminar perfil (DELETE) cuando no está en uso
        # Simular 0 suscriptores asignados
        mock_db.devices.clear()
        res_del = await async_client.delete(
            f"/api/v1/bandwidth-profiles/{p_id}",
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_del.status_code == 204

        # 7. 404 al consultar perfil eliminado
        mock_db.profiles.clear()
        res_nf = await async_client.get(f"/api/v1/bandwidth-profiles/{uuid.uuid4()}", headers=headers)
        assert res_nf.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_subscriber_devices_crud_and_queue_provisioning(
    async_client: AsyncClient, subscriber_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("src.api.v1.subscribers.write_audit_log", fake_audit)
    tid = subscriber_auth["tenant_id"]
    headers = subscriber_auth["headers"]
    mock_db = MockSubscribersDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    try:
        router_id = mock_db.routers[0].id
        profile = BandwidthProfile(
            id=uuid.uuid4(),
            tenant_id=tid,
            name="Plan-50M",
            rate_down_kbps=51200,
            rate_up_kbps=25600,
            burst_down_kbps=61440,
            burst_up_kbps=30720,
            burst_threshold_down_kbps=40960,
            burst_threshold_up_kbps=20480,
            burst_time_seconds=12,
            priority=5,
            queue_type="default",
        )
        mock_db.add(profile)

        # 1. Crear dispositivo de abonado
        create_payload = {
            "router_id": str(router_id),
            "endpoint_identifier": "CLI-CAR-0042",
            "service_type": "PPPOE",
            "auth_backend": "LOCAL_SECRET",
            "bandwidth_profile_id": str(profile.id),
            "onu_mode": "ROUTER",
            "onu_mac_address": "AA:BB:CC:DD:EE:FF",
            "device_serial": "ALCLB1234567",
            "pon_port": "pon-1/1/2",
            "optical_box": "NAP-CENTRO-01",
            "latitude": 10.4806,
            "longitude": -66.9036,
        }
        res_post = await async_client.post("/api/v1/subscriber-devices", json=create_payload, headers=headers)
        assert res_post.status_code == 201
        dev_data = res_post.json()
        assert dev_data["endpoint_identifier"] == "CLI-CAR-0042"
        assert dev_data["device_serial"] == "ALCLB1234567"
        dev_id = dev_data["id"]

        # 2. Listar dispositivos
        res_list = await async_client.get("/api/v1/subscriber-devices", headers=headers)
        assert res_list.status_code == 200
        assert len(res_list.json()) >= 1

        # 3. Obtener dispositivo por ID
        res_get = await async_client.get(f"/api/v1/subscriber-devices/{dev_id}", headers=headers)
        assert res_get.status_code == 200
        assert res_get.json()["endpoint_identifier"] == "CLI-CAR-0042"

        # 4. Actualizar dispositivo (PATCH)
        res_patch = await async_client.patch(
            f"/api/v1/subscriber-devices/{dev_id}",
            json={"onu_mac_address": "11:22:33:44:55:66", "status": "ACTIVE"},
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_patch.status_code == 200
        assert res_patch.json()["onu_mac_address"] == "11:22:33:44:55:66"

        # 5. Generar script de colas MikroTik para el abonado
        res_q = await async_client.get(f"/api/v1/subscriber-devices/{dev_id}/mikrotik-queue-script", headers=headers)
        assert res_q.status_code == 200
        q_data = res_q.json()
        assert q_data["has_profile"] is True
        assert "queue/simple/add" in q_data["command"]
        assert "SUB_CLI-CAR-0042" in q_data["command"]

        # 5b. Generar script cuando el dispositivo no tiene perfil
        mock_db.devices[0].bandwidth_profile_id = None
        res_no_prof = await async_client.get(
            f"/api/v1/subscriber-devices/{dev_id}/mikrotik-queue-script", headers=headers
        )
        assert res_no_prof.status_code == 200
        assert res_no_prof.json()["has_profile"] is False

        # 6. Eliminar dispositivo
        res_del = await async_client.delete(
            f"/api/v1/subscriber-devices/{dev_id}",
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_del.status_code == 204

        # 7. 404 para dispositivo inexistente
        mock_db.devices.clear()
        res_nf = await async_client.get(f"/api/v1/subscriber-devices/{uuid.uuid4()}", headers=headers)
        assert res_nf.status_code == 404

        # 8. 404 al intentar crear abonado con router inexistente
        mock_db.routers.clear()
        res_bad_router = await async_client.post(
            "/api/v1/subscriber-devices",
            json=create_payload,
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_bad_router.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_subscribers_feature_flag_disabled_403(
    async_client: AsyncClient, subscriber_auth: dict[str, Any], fake_redis: FakeAsyncRedis
) -> None:
    tid = subscriber_auth["tenant_id"]
    headers = subscriber_auth["headers"]

    # Inhabilitar el módulo ISP en la caché L2 para este tenant
    await fake_redis.hset(f"rg:{tid}:features", "isp_module_enabled", "0")

    mock_db = MockSubscribersDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    try:
        # bandwidth-profiles requiere exclusivamente el módulo ISP
        res_bp = await async_client.get("/api/v1/bandwidth-profiles", headers=headers)
        assert res_bp.status_code == 403
        assert "FEATURE_MODULE_DISABLED" in res_bp.text or "isp_module_enabled" in res_bp.text

        # subscriber-devices es bimodal: accesible para empresas no-ISP para ver clientes DHCP en el mapa
        res_devs = await async_client.get("/api/v1/subscriber-devices", headers=headers)
        assert res_devs.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_subscriber_device_ftth_registration_and_port_conflict(
    async_client: AsyncClient, subscriber_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("src.api.v1.subscribers.write_audit_log", fake_audit)
    tid = subscriber_auth["tenant_id"]
    headers = subscriber_auth["headers"]
    mock_db = MockSubscribersDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    try:
        router_id = mock_db.routers[0].id
        nap_box = OpticalBox(
            id=uuid.uuid4(),
            tenant_id=tid,
            router_id=router_id,
            box_code="NAP-TEST-01",
            capacity_ports=16,
            splitter_ratio="1:16",
            installation_type="POSTE",
            latitude=10.4850,
            longitude=-66.9050,
        )
        mock_db.add(nap_box)

        # 1. Registro exitoso de cliente FTTH con alias operativos FTTH_GPON y ROUTER_NAT
        payload_1 = {
            "router_id": str(router_id),
            "endpoint_identifier": "CLI-FTTH-001",
            "service_type": "FTTH_GPON",
            "onu_mode": "ROUTER_NAT",
            "optical_box_id": str(nap_box.id),
            "optical_box_port": 3,
            "rx_optical_power_dbm": -19.2,
            "drop_cable_meters": 65,
            "latitude": 10.4855,
            "longitude": -66.9052,
        }
        res_1 = await async_client.post(
            "/api/v1/subscriber-devices",
            json=payload_1,
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_1.status_code == 201
        data_1 = res_1.json()
        assert data_1["service_type"] == "PPPOE"  # Normalizado
        assert data_1["onu_mode"] == "ROUTER"  # Normalizado
        assert data_1["optical_box_port"] == 3
        assert data_1["optical_box"] == "NAP-TEST-01"
        assert float(data_1["rx_optical_power_dbm"]) == -19.2

        # 2. Intento de registrar segundo cliente en el mismo puerto 3 -> HTTP 409 Conflict
        payload_2 = {
            "router_id": str(router_id),
            "endpoint_identifier": "CLI-FTTH-002",
            "service_type": "FTTH_GPON",
            "optical_box_id": str(nap_box.id),
            "optical_box_port": 3,
        }
        res_conflict = await async_client.post(
            "/api/v1/subscriber-devices",
            json=payload_2,
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_conflict.status_code == 409
        assert "ya se encuentra ocupado" in res_conflict.json()["detail"]

        # 3. Intento de registrar cliente en puerto fuera de rango (ej. 99 > 16) -> HTTP 422
        payload_invalid_port = {
            "router_id": str(router_id),
            "endpoint_identifier": "CLI-FTTH-003",
            "optical_box_id": str(nap_box.id),
            "optical_box_port": 99,
        }
        res_invalid = await async_client.post(
            "/api/v1/subscriber-devices",
            json=payload_invalid_port,
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_invalid.status_code == 422
        assert "excede la capacidad de la caja" in res_invalid.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_subscriber_ipv4_pairing_persistence_and_ipam_list_sync(
    async_client: AsyncClient, subscriber_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica la persistencia real de IPv4 asignada tanto en PATCH subscriber-devices como en GET /ipam/customer-services."""
    monkeypatch.setattr("src.api.v1.subscribers.write_audit_log", fake_audit)
    monkeypatch.setattr("src.api.v1.ipam.write_audit_log", fake_audit)

    mock_ip_id = uuid.uuid4()

    async def mock_resolve(*args: Any, **kwargs: Any) -> uuid.UUID:
        return mock_ip_id

    monkeypatch.setattr("src.api.v1.subscribers._resolve_or_create_subscriber_ipv4", mock_resolve)

    tid = subscriber_auth["tenant_id"]
    headers = subscriber_auth["headers"]
    mock_db = MockSubscribersDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    router_id = mock_db.routers[0].id
    now = datetime.now(UTC)
    sub_device = SubscriberDevice(
        id=uuid.uuid4(),
        tenant_id=tid,
        router_id=router_id,
        endpoint_identifier="CLI-PERSIST-001",
        service_type="PPPOE",
        auth_backend="LOCAL_SECRET",
        onu_mode="ROUTER",
        status="ACTIVE",
        last_reachability_status="ONLINE",
        created_at=now,
        updated_at=now,
    )
    mock_db.add(sub_device)

    try:
        # 1. Emparejar abonado con IPv4 mediante PATCH
        patch_res = await async_client.patch(
            f"/api/v1/subscriber-devices/{sub_device.id}",
            json={"assigned_ipv4": "10.250.3.55"},
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert patch_res.status_code == 200
        patch_data = patch_res.json()
        assert patch_data["assigned_ipv4"] == "10.250.3.55"

        # 2. Consultar /api/v1/ipam/customer-services y verificar persistencia
        list_res = await async_client.get(
            "/api/v1/ipam/customer-services",
            headers=headers,
        )
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert len(list_data) >= 1
        matched = next((item for item in list_data if item["id"] == str(sub_device.id)), None)
        assert matched is not None
        assert matched["assigned_ipv4"] == "10.250.3.55"

        # 3. Crear nuevo servicio en /api/v1/ipam/customer-services con assigned_ipv4
        create_res = await async_client.post(
            "/api/v1/ipam/customer-services",
            json={
                "router_id": str(router_id),
                "endpoint_identifier": "CLI-IPAM-NEW-002",
                "service_type": "PPPOE",
                "assigned_ipv4": "10.250.3.56",
            },
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert create_res.status_code == 201
        create_data = create_res.json()
        assert create_data["assigned_ipv4"] == "10.250.3.56"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_field_ops_certify_signature_svg_column_parity_and_defensive_truncation(
    async_client: AsyncClient, subscriber_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Certifica que POST /api/v1/field-ops/certify persista customer_signature_svg con truncamiento defensivo (Spec 94 / Hito 30.17)."""
    audit_calls: list[dict[str, Any]] = []

    async def fake_audit_capture(**kwargs: Any) -> None:
        audit_calls.append(kwargs)

    monkeypatch.setattr("src.api.v1.field_ops.write_audit_log", fake_audit_capture)

    tid = subscriber_auth["tenant_id"]
    headers = subscriber_auth["headers"]
    mock_db = MockSubscribersDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    router_id = mock_db.routers[0].id
    now = datetime.now(UTC)
    sub_dev = SubscriberDevice(
        id=uuid.uuid4(),
        tenant_id=tid,
        router_id=router_id,
        endpoint_identifier="151515",
        service_type="DHCP",
        auth_backend="LOCAL_SECRET",
        onu_mode="ROUTER",
        device_serial="MAC-55447788",
        onu_mac_address="55:44:77:88:99:00",
        status="PENDING_INSTALL",
        last_reachability_status="ONLINE",
        created_at=now,
        updated_at=now,
    )
    mock_db.add(sub_dev)

    try:
        res = await async_client.post(
            "/api/v1/field-ops/certify",
            json={
                "customer_service_id": str(sub_dev.id),
                "onu_scanned_serial": "MAC-55447788",
                "onu_scanned_mac": "55:44:77:88:99:00:EXTRA",
                "tech_latitude": 10.4806,
                "tech_longitude": -66.9036,
                "customer_signature_svg": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA",
                "notes": "Certificación en campo con firma táctil",
            },
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "CERTIFIED"
        assert body["customer_signature_svg"].startswith("data:image/png;base64,")
        assert len(body["onu_scanned_mac"]) <= 17
        assert len(audit_calls) == 1
        assert audit_calls[0]["event_action"] == "FIELD_INSTALLATION_CERTIFIED"
        assert audit_calls[0]["after_state"]["signature_captured"] is True
    finally:
        app.dependency_overrides.clear()
