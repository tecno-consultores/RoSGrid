# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para Emparejamiento de Abonados FTTH (DHCP, PPPoE e IP Estática/IPAM),
descubrimiento de candidatos en vivo y resolución automática de IP en Ping (Hito 28.15 - Spec 70).
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient

from src.api.v1.auth import create_jwt_access_token
from src.db.session import get_tenant_db_session
from src.main import app
from src.models.core import SystemRoleEnum
from src.models.inventory import Router, RouterAdminStateEnum, RouterNetworkRoleEnum
from src.models.ipam import (
    AuthBackendEnum,
    CustomerServiceStatusEnum,
    CustomerServiceTypeEnum,
    IPAddressStatusEnum,
    IPAMAddress,
    IPAMPrefix,
    IPAMVrf,
    IPFamilyEnum,
    ONUModeEnum,
    OpticalBox,
    SubscriberDevice,
)
from tests.conftest import FakeAsyncRedis


async def fake_audit(**kwargs: Any) -> None:
    pass


class MockResult:
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

    def scalars(self) -> Any:
        class _Scalars:
            def __init__(self, it: list[Any]):
                self._it = it

            def all(self) -> list[Any]:
                return self._it

        return _Scalars(self._items)


class MockFtthDbSession:
    def __init__(self, tenant_id: uuid.UUID):
        self.tenant_id = tenant_id
        self.routers: list[Router] = [
            Router(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                display_name="BRAS-FTTH-01",
                api_base_url="https://10.250.3.1:443",
                api_port=443,
                network_role=RouterNetworkRoleEnum.BRAS_PPPOE,
                admin_state=RouterAdminStateEnum.PRODUCTION,
                latitude=Decimal("10.480600"),
                longitude=Decimal("-66.903600"),
            )
        ]
        self.optical_boxes: list[OpticalBox] = []
        self.devices: list[SubscriberDevice] = []
        self.vrfs: list[IPAMVrf] = [
            IPAMVrf(
                id=uuid.uuid4(),
                tenant_id=self.tenant_id,
                name="default",
                description="VRF Global de Enrutamiento",
            )
        ]
        self.prefixes: list[IPAMPrefix] = []
        self.addresses: list[IPAMAddress] = []

    def add(self, obj: Any) -> None:
        now = datetime.now(UTC)
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        if getattr(obj, "tenant_id", None) is None:
            obj.tenant_id = self.tenant_id
        if getattr(obj, "created_at", None) is None:
            obj.created_at = now
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = now
        if hasattr(obj, "auth_backend") and getattr(obj, "auth_backend", None) is None:
            obj.auth_backend = AuthBackendEnum.LOCAL_SECRET
        if hasattr(obj, "last_reachability_status") and not getattr(obj, "last_reachability_status", None):
            obj.last_reachability_status = "ONLINE"

        if isinstance(obj, SubscriberDevice):
            self.devices.append(obj)
        elif isinstance(obj, OpticalBox):
            self.optical_boxes.append(obj)
        elif isinstance(obj, IPAMVrf):
            self.vrfs.append(obj)
        elif isinstance(obj, IPAMPrefix):
            self.prefixes.append(obj)
        elif isinstance(obj, IPAMAddress):
            self.addresses.append(obj)

    async def commit(self) -> None:
        pass

    async def flush(self) -> None:
        pass

    async def refresh(self, obj: Any) -> None:
        pass

    async def execute(self, stmt: Any, params: dict[str, Any] | None = None) -> MockResult:
        s = str(stmt).lower()

        # Routers
        if "from routers" in s:
            target_r = self.routers[0] if self.routers else None
            return MockResult(target_r, self.routers)

        # Optical boxes
        if "from optical_boxes" in s:
            target_box = self.optical_boxes[0] if self.optical_boxes else None
            return MockResult(target_box, self.optical_boxes)

        # VRFs
        if "from ipam_vrfs" in s:
            v = self.vrfs[0] if self.vrfs else None
            return MockResult(v, self.vrfs)

        # Prefixes
        if "from ipam_prefixes" in s:
            return MockResult(None, self.prefixes)

        # Addresses
        if "from ipam_ip_addresses" in s:
            if "host(" in s:
                # Búsqueda por host
                try:
                    compiled = stmt.compile().params
                    for val in compiled.values():
                        for a in self.addresses:
                            if str(a.address).split("/")[0] == str(val):
                                return MockResult(a, [a])
                except Exception:
                    pass
                return MockResult(None, [])
            return MockResult(self.addresses[0] if self.addresses else None, self.addresses)

        # Subscriber devices
        if "from subscriber_devices" in s:
            compiled_params = {}
            try:
                compiled_params = stmt.compile().params
            except Exception:
                pass

            dev_id = None
            ep_id = None
            for k, val in compiled_params.items():
                if "id" in k and isinstance(val, uuid.UUID):
                    dev_id = val
                elif "endpoint_identifier" in k:
                    ep_id = val

            if dev_id:
                for d in self.devices:
                    if d.id == dev_id:
                        # Si tiene ipv4_address_id pero no ipv4_address cargado en dict, buscarlo
                        if d.ipv4_address_id and "ipv4_address" not in d.__dict__:
                            for a in self.addresses:
                                if a.id == d.ipv4_address_id:
                                    d.__dict__["ipv4_address"] = a
                                    break
                        return MockResult(d, [d])

            if ep_id:
                for d in self.devices:
                    if d.endpoint_identifier == ep_id:
                        return MockResult(d, [d])
                return MockResult(None, [])

            if self.devices:
                first = self.devices[0]
                if first.ipv4_address_id and "ipv4_address" not in first.__dict__:
                    for a in self.addresses:
                        if a.id == first.ipv4_address_id:
                            first.__dict__["ipv4_address"] = a
                            break
                return MockResult(first, self.devices)

            return MockResult(None, [])

        return MockResult(None, [])


class MockMikrotikClient:
    def __init__(
        self,
        dhcp_leases: list[dict[str, Any]] | None = None,
        ppp_active: list[dict[str, Any]] | None = None,
        ppp_secrets: list[dict[str, Any]] | None = None,
        ping_res: list[dict[str, Any]] | None = None,
    ):
        self.dhcp_leases = dhcp_leases or [
            {
                "address": "10.250.3.55",
                "mac-address": "AA:BB:CC:11:22:33",
                "host-name": "FTTH-CLI-151515",
                "server": "dhcp-wan",
                "status": "bound",
            }
        ]
        self.ppp_active = ppp_active or [
            {
                "name": "cliente_pppoe_15",
                "address": "10.250.3.77",
                "caller-id": "AA:BB:CC:44:55:66",
                "service": "pppoe",
                "uptime": "2d14h",
            }
        ]
        self.ppp_secrets = ppp_secrets or [
            {
                "name": "cliente_secret_99",
                "remote-address": "10.250.3.99",
                "caller-id": "AA:BB:CC:77:88:99",
                "service": "pppoe",
            }
        ]
        self.ping_res = ping_res or [
            {"host": "10.250.3.55", "status": "ok", "time": "2ms", "packet-loss": 0},
            {"host": "10.250.3.55", "status": "ok", "time": "3ms", "packet-loss": 0},
        ]

    async def __aenter__(self) -> "MockMikrotikClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    async def get(self, endpoint: str, params: Any = None) -> Any:
        if "/ip/dhcp-server/lease" in endpoint:
            return self.dhcp_leases
        if "/ppp/active" in endpoint:
            return self.ppp_active
        if "/ppp/secret" in endpoint:
            return self.ppp_secrets
        return []

    async def post(self, endpoint: str, json: Any = None) -> Any:
        if "/ping" in endpoint:
            return self.ping_res
        return []


@pytest.fixture
def ftth_auth(fake_redis: FakeAsyncRedis) -> dict[str, Any]:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    sid = "sess-ftth-pairing-001"
    sess_key = f"rg:{tid}:sess:{sid}"

    import asyncio

    asyncio.get_event_loop().run_until_complete(
        fake_redis.hset(
            sess_key,
            mapping={
                "session_id": sid,
                "user_id": str(uid),
                "username": "techoperator",
                "role": SystemRoleEnum.TENANT_ADMIN.value,
            },
        )
    )

    token = create_jwt_access_token(str(uid), str(tid), "tenant-ftth", sid, SystemRoleEnum.TENANT_ADMIN.value, True)
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
async def test_subscriber_device_registration_with_assigned_ipv4(
    async_client: AsyncClient, ftth_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("src.api.v1.subscribers.write_audit_log", fake_audit)
    tid = ftth_auth["tenant_id"]
    headers = ftth_auth["headers"]
    mock_db = MockFtthDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    try:
        router_id = mock_db.routers[0].id
        nap_box = OpticalBox(
            id=uuid.uuid4(),
            tenant_id=tid,
            router_id=router_id,
            box_code="NAP-PAIR-01",
            capacity_ports=8,
            splitter_ratio="1:8",
            installation_type="POSTE",
            latitude=10.4850,
            longitude=-66.9050,
        )
        mock_db.add(nap_box)

        # Registrar abonado FTTH con assigned_ipv4 y protocolo DHCP
        payload = {
            "router_id": str(router_id),
            "endpoint_identifier": "CLI-DHCP-151515",
            "service_type": "DHCP",
            "assigned_ipv4": "10.250.3.55",
            "onu_mode": "ROUTER",
            "onu_mac_address": "AA:BB:CC:11:22:33",
            "device_serial": "HWTC12345678",
            "optical_box_id": str(nap_box.id),
            "optical_box_port": 1,
            "rx_optical_power_dbm": -18.5,
            "drop_cable_meters": 45,
        }

        res = await async_client.post(
            "/api/v1/subscriber-devices",
            json=payload,
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["service_type"] == "DHCP"
        assert data["assigned_ipv4"] == "10.250.3.55"
        assert data["onu_mac_address"] == "AA:BB:CC:11:22:33"
        assert len(mock_db.addresses) == 1
        assert str(mock_db.addresses[0].address) == "10.250.3.55"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_subscriber_device_patch_pairing_network(
    async_client: AsyncClient, ftth_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("src.api.v1.subscribers.write_audit_log", fake_audit)
    tid = ftth_auth["tenant_id"]
    headers = ftth_auth["headers"]
    mock_db = MockFtthDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    try:
        router_id = mock_db.routers[0].id
        dev = SubscriberDevice(
            id=uuid.uuid4(),
            tenant_id=tid,
            router_id=router_id,
            endpoint_identifier="CLI-UNPAIRED-01",
            service_type=CustomerServiceTypeEnum.DHCP,
            onu_mode=ONUModeEnum.ROUTER,
            status=CustomerServiceStatusEnum.ACTIVE,
        )
        mock_db.add(dev)

        # Realizar emparejamiento mediante PATCH con nueva IP y MAC
        patch_payload = {
            "service_type": "DHCP",
            "assigned_ipv4": "10.250.3.60",
            "onu_mac_address": "BB:CC:DD:22:33:44",
        }

        res = await async_client.patch(
            f"/api/v1/subscriber-devices/{dev.id}",
            json=patch_payload,
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["assigned_ipv4"] == "10.250.3.60"
        assert data["onu_mac_address"] == "BB:CC:DD:22:33:44"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_subscriber_device_live_candidates(
    async_client: AsyncClient, ftth_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    tid = ftth_auth["tenant_id"]
    headers = ftth_auth["headers"]
    mock_db = MockFtthDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    mock_client = MockMikrotikClient()
    monkeypatch.setattr("src.api.v1.subscribers._get_router_client", lambda r, t: mock_client)

    try:
        router_id = mock_db.routers[0].id
        dev = SubscriberDevice(
            id=uuid.uuid4(),
            tenant_id=tid,
            router_id=router_id,
            endpoint_identifier="CLI-LIVE-01",
            service_type=CustomerServiceTypeEnum.DHCP,
            onu_mode=ONUModeEnum.ROUTER,
            status=CustomerServiceStatusEnum.ACTIVE,
        )
        mock_db.add(dev)

        res = await async_client.get(
            f"/api/v1/subscriber-devices/{dev.id}/live-candidates",
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["router_name"] == "BRAS-FTTH-01"
        assert len(data["dhcp_leases"]) == 1
        assert data["dhcp_leases"][0]["address"] == "10.250.3.55"
        assert len(data["pppoe_sessions"]) == 2  # active + secret
        assert data["pppoe_sessions"][0]["name"] == "cliente_pppoe_15"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_subscriber_device_ping_with_paired_ip(
    async_client: AsyncClient, ftth_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    tid = ftth_auth["tenant_id"]
    headers = ftth_auth["headers"]
    mock_db = MockFtthDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    mock_client = MockMikrotikClient()
    monkeypatch.setattr("src.api.v1.subscribers._get_router_client", lambda r, t: mock_client)

    try:
        router_id = mock_db.routers[0].id
        ip_addr = IPAMAddress(
            id=uuid.uuid4(),
            tenant_id=tid,
            prefix_id=uuid.uuid4(),
            address="10.250.3.55",
            ip_family=IPFamilyEnum.IPv4,
            status=IPAddressStatusEnum.ALLOCATED,
        )
        mock_db.add(ip_addr)

        dev = SubscriberDevice(
            id=uuid.uuid4(),
            tenant_id=tid,
            router_id=router_id,
            endpoint_identifier="CLI-PING-01",
            service_type=CustomerServiceTypeEnum.DHCP,
            onu_mode=ONUModeEnum.ROUTER,
            ipv4_address_id=ip_addr.id,
            status=CustomerServiceStatusEnum.ACTIVE,
        )
        dev.__dict__["ipv4_address"] = ip_addr
        mock_db.add(dev)

        res = await async_client.post(
            f"/api/v1/subscriber-devices/{dev.id}/ping?force=true",
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["assigned_ipv4"] == "10.250.3.55"
        assert data["last_reachability_status"] == "ONLINE"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_subscriber_device_ping_auto_discovery_from_router(
    async_client: AsyncClient, ftth_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    tid = ftth_auth["tenant_id"]
    headers = ftth_auth["headers"]
    mock_db = MockFtthDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    # Router tiene activo cliente_pppoe_15 con IP 10.250.3.77
    mock_client = MockMikrotikClient(
        ppp_active=[
            {
                "name": "cliente_pppoe_auto",
                "address": "10.250.3.77",
                "caller-id": "AA:BB:CC:99:99:99",
                "service": "pppoe",
            }
        ]
    )
    monkeypatch.setattr("src.api.v1.subscribers._get_router_client", lambda r, t: mock_client)

    try:
        router_id = mock_db.routers[0].id
        dev = SubscriberDevice(
            id=uuid.uuid4(),
            tenant_id=tid,
            router_id=router_id,
            endpoint_identifier="cliente_pppoe_auto",
            service_type=CustomerServiceTypeEnum.PPPOE,
            onu_mode=ONUModeEnum.ROUTER,
            status=CustomerServiceStatusEnum.ACTIVE,
        )
        mock_db.add(dev)

        res = await async_client.post(
            f"/api/v1/subscriber-devices/{dev.id}/ping?force=true",
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["assigned_ipv4"] == "10.250.3.77"
        assert data["last_reachability_status"] == "ONLINE"
        # Verificar que la IP quedó persistida automáticamente
        assert len(mock_db.addresses) == 1
        assert str(mock_db.addresses[0].address) == "10.250.3.77"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_subscriber_device_ping_without_ip_fails_gracefully(
    async_client: AsyncClient, ftth_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    tid = ftth_auth["tenant_id"]
    headers = ftth_auth["headers"]
    mock_db = MockFtthDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    mock_client = MockMikrotikClient(dhcp_leases=[], ppp_active=[], ppp_secrets=[])
    monkeypatch.setattr("src.api.v1.subscribers._get_router_client", lambda r, t: mock_client)

    try:
        router_id = mock_db.routers[0].id
        dev = SubscriberDevice(
            id=uuid.uuid4(),
            tenant_id=tid,
            router_id=router_id,
            endpoint_identifier="CLI-NO-IP-01",
            service_type=CustomerServiceTypeEnum.DHCP,
            onu_mode=ONUModeEnum.ROUTER,
            status=CustomerServiceStatusEnum.ACTIVE,
        )
        mock_db.add(dev)

        res = await async_client.post(
            f"/api/v1/subscriber-devices/{dev.id}/ping?force=true",
            headers=headers,
        )
        assert res.status_code == 400
        assert "aún no tiene dirección IPv4" in res.json()["detail"]
        assert "🔗 Emparejar Red" in res.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_get_router_client_vault_defensive_access_no_greenlet_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifica que _get_router_client inspecciona r.__dict__.get('vault') sin provocar
    sqlalchemy.exc.MissingGreenlet ni fallar si la relación no ha sido precargada.
    """
    from src.api.v1.subscribers import _get_router_client

    tid = uuid.uuid4()

    # Caso 1: Router sin atributo 'vault' en __dict__ (simula lazy relationship no precargada)
    r_unloaded = Router(
        id=uuid.uuid4(),
        tenant_id=tid,
        display_name="ROUTER-UNLOADED-VAULT",
        api_base_url="https://10.0.0.1:443",
        api_port=443,
    )
    # Asegurar que 'vault' no esté en __dict__
    r_unloaded.__dict__.pop("vault", None)

    client1 = _get_router_client(r_unloaded, tid)
    assert client1.host == "10.0.0.1"
    assert client1.port == 443

    # Caso 2: Router con 'vault' precargado y válido
    class MockVault:
        encrypted_credentials = "fake-encrypted-token"
        credentials_format = "TOKEN"

    r_loaded = Router(
        id=uuid.uuid4(),
        tenant_id=tid,
        display_name="ROUTER-LOADED-VAULT",
        api_base_url="https://10.0.0.2:443",
        api_port=443,
    )
    r_loaded.__dict__["vault"] = MockVault()

    monkeypatch.setattr(
        "src.api.v1.subscribers._create_client_from_vault",
        lambda r, t: MockMikrotikClient(),
    )
    client2 = _get_router_client(r_loaded, tid)
    assert isinstance(client2, MockMikrotikClient)


@pytest.mark.asyncio
async def test_create_subscriber_inherits_coordinates_from_box_or_router(
    async_client: AsyncClient, ftth_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica que al crear un abonado sin latitud/longitud explícita, hereda
    las coordenadas de la Caja NAP o del Router asignador.
    """
    tid = ftth_auth["tenant_id"]
    headers = ftth_auth["headers"]
    mock_db = MockFtthDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db
    monkeypatch.setattr("src.api.v1.subscribers.write_audit_log", fake_audit)

    router_id = mock_db.routers[0].id

    # Caso 1: Hereda de la Caja NAP cuando se especifica optical_box_id
    box = OpticalBox(
        id=uuid.uuid4(),
        tenant_id=tid,
        router_id=router_id,
        box_code="NAP-TEST-COORD-01",
        capacity_ports=16,
        latitude=Decimal("10.123450"),
        longitude=Decimal("-66.543210"),
    )
    mock_db.add(box)

    payload_with_box = {
        "router_id": str(router_id),
        "endpoint_identifier": "CLI-COORD-BOX-01",
        "service_type": "DHCP",
        "onu_mode": "ROUTER",
        "optical_box_id": str(box.id),
        "optical_box_port": 1,
    }

    try:
        headers1 = {**headers, "Idempotency-Key": str(uuid.uuid4())}
        res1 = await async_client.post("/api/v1/subscriber-devices", json=payload_with_box, headers=headers1)
        assert res1.status_code == 201, f"res1 failed: {res1.status_code} {res1.text}"
        data1 = res1.json()
        assert float(data1["latitude"]) == pytest.approx(10.123450, rel=1e-4)
        assert float(data1["longitude"]) == pytest.approx(-66.543210, rel=1e-4)

        # Caso 2: Hereda del Router cuando NO hay optical_box_id ni coordenadas
        payload_no_box = {
            "router_id": str(router_id),
            "endpoint_identifier": "CLI-COORD-ROUTER-01",
            "service_type": "DHCP",
            "onu_mode": "ROUTER",
        }
        headers2 = {**headers, "Idempotency-Key": str(uuid.uuid4())}
        res2 = await async_client.post("/api/v1/subscriber-devices", json=payload_no_box, headers=headers2)
        assert res2.status_code == 201, f"res2 failed: {res2.status_code} {res2.text}"
        data2 = res2.json()
        assert float(data2["latitude"]) == pytest.approx(10.480600, rel=1e-4)
        assert float(data2["longitude"]) == pytest.approx(-66.903600, rel=1e-4)
    finally:
        app.dependency_overrides.clear()

