# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para Cajas NAP de distribución óptica y operaciones bimodales (DHCP Sync y Ping 1-Click)."""

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient

from src.api.v1.auth import create_jwt_access_token
from src.db.session import get_tenant_db_session
from src.main import app
from src.models.core import SystemRoleEnum, Tenant
from src.models.inventory import Router, RouterAdminStateEnum, RouterNetworkRoleEnum
from src.models.ipam import OpticalBox, SubscriberDevice
from tests.conftest import FakeAsyncRedis


class MockOpticalBoxesDbScalars:
    def __init__(self, items: list[Any]):
        self._items = items

    def all(self) -> list[Any]:
        return self._items


class MockOpticalBoxesDbResult:
    def __init__(
        self,
        item: Any = None,
        items: list[Any] | None = None,
        scalar_val: Any = None,
        rows: list[Any] | None = None,
    ):
        self._item = item
        self._items = items or ([item] if item is not None else [])
        self._scalar_val = scalar_val
        self._rows = rows or []

    def all(self) -> list[Any]:
        return self._rows

    def scalar_one_or_none(self) -> Any:
        return self._item

    def scalar_one(self) -> Any:
        if self._item is None:
            raise ValueError("No item found")
        return self._item

    def scalar(self) -> Any:
        return self._scalar_val if self._scalar_val is not None else (self._item if self._item is not None else 0)

    def scalars(self) -> MockOpticalBoxesDbScalars:
        return MockOpticalBoxesDbScalars(self._items)


class MockMikrotikClient:
    async def __aenter__(self) -> "MockMikrotikClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    async def get(self, endpoint: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        if "/ip/dhcp-server/lease" in endpoint:
            return [
                {
                    "address": "192.168.88.50",
                    "mac-address": "BC:24:11:AA:BB:CC",
                    "host-name": "PC-FINANZAS-01",
                    "status": "bound",
                }
            ]
        return []

    async def post(self, endpoint: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        if "/ping" in endpoint:
            return [{"status": "echo reply", "time": "12ms"}]
        return []


class MockOpticalBoxesDbSession:
    def __init__(self, tenant_id: uuid.UUID, is_isp_mode: bool = False):
        self.tenant_id = tenant_id
        self.tenant = Tenant(
            id=self.tenant_id,
            name="Tenant Test",
            slug="tenant-test",
            isp_module_enabled=is_isp_mode,
        )
        self.optical_boxes: list[OpticalBox] = []
        self.devices: list[SubscriberDevice] = []
        self.routers: list[Router] = [
            Router(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                display_name="CCR2004-Edge",
                api_base_url="https://10.0.0.1:443",
                api_port=443,
                network_role=RouterNetworkRoleEnum.DISTRIBUTION_SWITCH,
                admin_state=RouterAdminStateEnum.PRODUCTION,
                physical_location="Sede Central",
                latitude=10.4806,
                longitude=-66.9036,
            )
        ]
        self.deleted: list[Any] = []

    def add(self, obj: Any) -> None:
        now = datetime.now(UTC)
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        if getattr(obj, "created_at", None) is None:
            obj.created_at = now
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = now

        if isinstance(obj, OpticalBox):
            self.optical_boxes.append(obj)
        elif isinstance(obj, SubscriberDevice):
            self.devices.append(obj)

    async def commit(self) -> None:
        pass

    async def flush(self) -> None:
        pass

    async def refresh(self, obj: Any) -> None:
        pass

    async def delete(self, obj: Any) -> None:
        self.deleted.append(obj)

    async def execute(self, stmt: Any) -> MockOpticalBoxesDbResult:
        query_str = str(stmt).lower()
        if "from tenants" in query_str:
            return MockOpticalBoxesDbResult(item=self.tenant)

        if "from optical_boxes" in query_str:
            if "where optical_boxes.id =" in query_str or ("where" in query_str and "id" in query_str):
                return MockOpticalBoxesDbResult(item=self.optical_boxes[0] if self.optical_boxes else None)
            return MockOpticalBoxesDbResult(items=list(self.optical_boxes))

        if "from subscriber_devices" in query_str:
            if "group by" in query_str or ("count(" in query_str and "optical_box_id" in query_str):
                box_counts: dict[uuid.UUID, int] = {}
                for d in self.devices:
                    if getattr(d, "optical_box_id", None):
                        box_counts[d.optical_box_id] = box_counts.get(d.optical_box_id, 0) + 1
                return MockOpticalBoxesDbResult(rows=list(box_counts.items()))
            if "count(" in query_str:
                return MockOpticalBoxesDbResult(scalar_val=len(self.devices))
            stmt_repr = repr(stmt)
            for d in self.devices:
                if str(d.id) in stmt_repr:
                    return MockOpticalBoxesDbResult(item=d, items=[d])
            return MockOpticalBoxesDbResult(item=self.devices[-1] if self.devices else None, items=list(self.devices))

        if "from routers" in query_str:
            stmt_repr = repr(stmt)
            for r in self.routers:
                if str(r.id) in stmt_repr:
                    return MockOpticalBoxesDbResult(item=r, items=[r])
            return MockOpticalBoxesDbResult(items=list(self.routers), item=self.routers[0] if self.routers else None)

        return MockOpticalBoxesDbResult(item=None)


@pytest.fixture
def nap_auth(fake_redis: FakeAsyncRedis) -> dict[str, Any]:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    sid = "sess-nap-001"
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

    token = create_jwt_access_token(str(uid), str(tid), "tenant-nap", sid, SystemRoleEnum.TENANT_ADMIN.value, True)
    return {
        "headers": {
            "Authorization": f"Bearer {token}",
            "Cookie": f"rosgrid_access_token={token}",
            "Idempotency-Key": str(uuid.uuid4()),
        },
        "tenant_id": tid,
        "user_id": uid,
        "token": token,
    }


@pytest.mark.asyncio
async def test_optical_boxes_crud_lifecycle(
    async_client: AsyncClient, nap_auth: dict[str, Any], fake_redis: FakeAsyncRedis
) -> None:
    tid = nap_auth["tenant_id"]
    headers = nap_auth["headers"]

    # Habilitar isp_module_enabled en la caché L2
    await fake_redis.hset(f"rg:{tid}:features", "isp_module_enabled", "1")

    mock_db = MockOpticalBoxesDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    try:
        router = mock_db.routers[0]

        # 1. Crear Caja NAP
        create_payload = {
            "router_id": str(router.id),
            "box_code": "NAP-NORTE-01",
            "brand": "Huawei",
            "model": "FAT-16",
            "capacity_ports": 16,
            "splitter_ratio": "1:16",
            "installation_type": "POSTE",
            "physical_location": "Av. Libertador Poste 12",
            "input_power_dbm": -15.2,
            "latitude": 10.4850,
            "longitude": -66.9050,
        }
        res_post = await async_client.post(
            "/api/v1/optical-boxes",
            json=create_payload,
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_post.status_code == 201
        box_data = res_post.json()
        assert box_data["box_code"] == "NAP-NORTE-01"
        assert box_data["capacity_ports"] == 16
        box_id = box_data["id"]

        # 2. Listar Cajas NAP
        res_list = await async_client.get("/api/v1/optical-boxes", headers=headers)
        assert res_list.status_code == 200
        items = res_list.json()
        assert len(items) == 1
        assert items[0]["box_code"] == "NAP-NORTE-01"

        # 3. Obtener Detalle y Matriz de Puertos
        res_detail = await async_client.get(f"/api/v1/optical-boxes/{box_id}", headers=headers)
        assert res_detail.status_code == 200
        detail_data = res_detail.json()
        assert detail_data["capacity_ports"] == 16
        assert len(detail_data["ports"]) == 16
        assert detail_data["ports"][0]["is_occupied"] is False

        # 4. Actualizar Caja NAP
        res_patch = await async_client.patch(
            f"/api/v1/optical-boxes/{box_id}",
            json={"input_power_dbm": -16.0, "notes": "Atenuación revisada"},
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_patch.status_code == 200
        assert float(res_patch.json()["input_power_dbm"]) == -16.0

        # 5. Eliminar Caja NAP
        res_del = await async_client.delete(
            f"/api/v1/optical-boxes/{box_id}",
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_del.status_code == 204
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_optical_boxes_feature_flag_disabled_403(
    async_client: AsyncClient, nap_auth: dict[str, Any], fake_redis: FakeAsyncRedis
) -> None:
    tid = nap_auth["tenant_id"]
    headers = nap_auth["headers"]

    # Desactivar módulo ISP
    await fake_redis.hset(f"rg:{tid}:features", "isp_module_enabled", "0")

    mock_db = MockOpticalBoxesDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    try:
        res = await async_client.get("/api/v1/optical-boxes", headers=headers)
        assert res.status_code == 403
        assert "FEATURE_MODULE_DISABLED" in res.text or "isp_module_enabled" in res.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_subscriber_sync_dhcp_and_ping_live(
    async_client: AsyncClient, nap_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    tid = nap_auth["tenant_id"]
    headers = nap_auth["headers"]

    mock_db = MockOpticalBoxesDbSession(tid, is_isp_mode=False)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    import src.api.v1.subscribers as subs_module

    monkeypatch.setattr(subs_module, "_get_router_client", lambda r, tid: MockMikrotikClient())

    try:
        # 1. Sincronización DHCP
        res_sync = await async_client.post(
            "/api/v1/subscriber-devices/sync-dhcp",
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_sync.status_code == 200
        sync_data = res_sync.json()
        assert "created_count" in sync_data
        assert sync_data["created_count"] >= 1
        assert "total_subscribers" in sync_data

        # 2. Crear dispositivo simulando lease
        now = datetime.now(UTC)
        dev = SubscriberDevice(
            id=uuid.uuid4(),
            tenant_id=tid,
            router_id=mock_db.routers[0].id,
            endpoint_identifier="PC-LAB-01",
            service_type="DHCP",
            auth_backend="LOCAL_SECRET",
            onu_mode="BRIDGE",
            assigned_ipv4="192.168.88.100",
            status="ACTIVE",
            last_reachability_status="UNKNOWN",
            latitude=10.4806,
            longitude=-66.9036,
            is_custom_coordinates=False,
            created_at=now,
            updated_at=now,
        )
        mock_db.devices.append(dev)

        # 3. Test Ping 1-Click
        res_ping = await async_client.post(
            f"/api/v1/subscriber-devices/{dev.id}/ping",
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_ping.status_code == 200
        ping_data = res_ping.json()
        assert ping_data["device_id"] == str(dev.id)
        assert ping_data["last_reachability_status"] in ["ONLINE", "OFFLINE"]

        # 4. Restablecer coordenadas a las del router
        res_reset = await async_client.patch(
            f"/api/v1/subscriber-devices/{dev.id}",
            json={"reset_to_router_coordinates": True},
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res_reset.status_code == 200
        assert res_reset.json()["is_custom_coordinates"] is False
    finally:
        app.dependency_overrides.clear()
