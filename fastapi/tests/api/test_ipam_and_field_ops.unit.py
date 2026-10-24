# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from src.api.v1.auth import create_jwt_access_token
from src.db.session import get_tenant_db_session
from src.main import app
from src.models.core import SystemRoleEnum
from src.models.inventory import Router, RouterAdminStateEnum, RouterNetworkRoleEnum
from src.models.ipam import (
    CustomerService,
    CustomerServiceStatusEnum,
    CustomerServiceTypeEnum,
    FiberCutIncident,
    FieldInstallationOrder,
    IPAMAddress,
    IPAMPrefix,
    IPAMVrf,
    ONUModeEnum,
)
from tests.conftest import FakeAsyncRedis


async def fake_audit(**kwargs):
    pass


def make_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": str(uuid.uuid4()),
    }


class MockIpamDbSession:
    def __init__(self, tenant_id: str):
        self.tenant_id = uuid.UUID(tenant_id)
        self.vrfs = []
        self.prefixes = []
        self.addresses = []
        self.customer_services = []
        self.field_orders = []
        self.fiber_cuts = []
        self.routers = [
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

    def add(self, obj):
        now = datetime.now(UTC)
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        if getattr(obj, "created_at", None) is None:
            obj.created_at = now
        if getattr(obj, "updated_at", None) is None:
            obj.updated_at = now
        if hasattr(obj, "detected_at") and getattr(obj, "detected_at", None) is None:
            obj.detected_at = now

        if isinstance(obj, IPAMVrf):
            self.vrfs.append(obj)
        elif isinstance(obj, IPAMPrefix):
            self.prefixes.append(obj)
        elif isinstance(obj, IPAMAddress):
            self.addresses.append(obj)
        elif isinstance(obj, CustomerService):
            self.customer_services.append(obj)
        elif isinstance(obj, FieldInstallationOrder):
            self.field_orders.append(obj)
        elif isinstance(obj, FiberCutIncident):
            self.fiber_cuts.append(obj)

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

    async def execute(self, stmt, params=None):
        stmt_str = str(stmt).lower()

        class MockResult:
            def __init__(self, items):
                self._items = items

            def scalar_one_or_none(self):
                return self._items[0] if self._items else None

            def scalar(self):
                return self._items[0] if self._items else None

            def scalars(self):
                items = self._items

                class MockScalars:
                    def all(self):
                        return items

                return MockScalars()

            def all(self):
                return self._items

        if "ipam_vrfs" in stmt_str:
            return MockResult(self.vrfs)
        elif "ipam_prefixes" in stmt_str:
            if "ipam_prefixes.prefix" in stmt_str:
                try:
                    p_dict = stmt.compile().params
                    target_pfx = next((v for k, v in p_dict.items() if "prefix" in k), None)
                    if target_pfx:
                        matched = [p for p in self.prefixes if getattr(p, "prefix", None) == target_pfx]
                        return MockResult(matched)
                except Exception:
                    pass
            return MockResult(self.prefixes)
        elif "ipam_ip_addresses" in stmt_str:
            if "ipam_ip_addresses.address" in stmt_str:
                try:
                    p_dict = stmt.compile().params
                    target_addr = next((v for k, v in p_dict.items() if "address" in k), None)
                    if target_addr:
                        matched = [a for a in self.addresses if getattr(a, "address", None) == target_addr]
                        return MockResult(matched)
                except Exception:
                    pass
            return MockResult(self.addresses)
        elif "subscriber_devices" in stmt_str or "customer_services" in stmt_str:
            if "count(" in stmt_str:
                if "group by" in stmt_str:
                    if self.customer_services:
                        r_id = self.customer_services[0].router_id
                        return MockResult([(r_id, "gpon-olt1/1/1", "NAP-04", 4)])
                    return MockResult([])
                return MockResult([len(self.customer_services)])
            if "endpoint_identifier" in stmt_str:
                try:
                    p_dict = stmt.compile().params
                    target_ep = next((v for k, v in p_dict.items() if "endpoint" in k), None)
                    if target_ep:
                        matched = [s for s in self.customer_services if getattr(s, "endpoint_identifier", None) == target_ep]
                        return MockResult(matched)
                except Exception:
                    pass
            return MockResult(self.customer_services)
        elif "field_installation_orders" in stmt_str:
            return MockResult(self.field_orders)
        elif "fiber_cut_incidents" in stmt_str:
            return MockResult(self.fiber_cuts)
        elif "routers" in stmt_str:
            return MockResult(self.routers)

        return MockResult([])


@pytest.mark.asyncio
async def test_ipam_vrf_and_prefix_lifecycle(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("src.api.v1.ipam.write_audit_log", fake_audit)

    tenant_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    session_id = "sess-ipam-001"
    sess_key = f"rg:{tenant_id}:sess:{session_id}"

    await fake_redis.hset(
        sess_key,
        mapping={
            "session_id": session_id,
            "user_id": user_id,
            "username": "admin",
            "role": SystemRoleEnum.TENANT_ADMIN.value,
        },
    )

    token = create_jwt_access_token(
        user_id, tenant_id, "test_tenant", session_id, SystemRoleEnum.TENANT_ADMIN.value, True
    )

    mock_db = MockIpamDbSession(tenant_id)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    try:
        # 1. Crear VRF
        resp_vrf = await async_client.post(
            "/api/v1/ipam/vrfs",
            headers=make_headers(token),
            json={"name": "vrf-clientes", "description": "VRF de Clientes de Fibra"},
        )
        assert resp_vrf.status_code == 201
        vrf_data = resp_vrf.json()
        assert vrf_data["name"] == "vrf-clientes"
        vrf_id = vrf_data["id"]

        # 2. Listar VRFs
        resp_list_vrfs = await async_client.get("/api/v1/ipam/vrfs", headers=make_headers(token))
        assert resp_list_vrfs.status_code == 200
        assert len(resp_list_vrfs.json()) == 1

        # 3. Crear Prefijo IPv4
        resp_pfx = await async_client.post(
            "/api/v1/ipam/prefixes",
            headers=make_headers(token),
            json={
                "vrf_id": vrf_id,
                "prefix": "100.64.10.0/24",
                "ip_family": "IPv4",
                "role": "CGNAT",
                "is_pool": True,
            },
        )
        assert resp_pfx.status_code == 201
        pfx_data = resp_pfx.json()
        assert pfx_data["prefix"] == "100.64.10.0/24"
        pfx_id = pfx_data["id"]

        # 4. Validar error ante CIDR inválido
        resp_bad = await async_client.post(
            "/api/v1/ipam/prefixes",
            headers=make_headers(token),
            json={
                "vrf_id": vrf_id,
                "prefix": "999.999.0.0/24",
                "ip_family": "IPv4",
            },
        )
        assert resp_bad.status_code == 422

        # 5. Calcular Siguiente IP Libre (Next Available)
        resp_next = await async_client.get(
            f"/api/v1/ipam/prefixes/{pfx_id}/next-available", headers=make_headers(token)
        )
        assert resp_next.status_code == 200
        next_data = resp_next.json()
        assert next_data["next_available"] == "100.64.10.1"
        assert next_data["is_subnet"] is False

        # 6. Listar Prefijos con filtros
        resp_filter = await async_client.get(
            f"/api/v1/ipam/prefixes?vrf_id={vrf_id}&ip_family=IPv4&role=CGNAT",
            headers=make_headers(token),
        )
        assert resp_filter.status_code == 200

        # 7. Asignar IP en el prefijo
        resp_addr = await async_client.post(
            "/api/v1/ipam/addresses",
            headers=make_headers(token),
            json={
                "prefix_id": str(pfx_id),
                "address": "100.64.10.5",
                "ip_family": "IPv4",
                "status": "ALLOCATED",
                "description": "Gateway CGNAT",
            },
        )
        assert resp_addr.status_code == 201

        # 8. Listar IPs del prefijo
        resp_list_addr = await async_client.get(
            f"/api/v1/ipam/addresses?prefix_id={pfx_id}",
            headers=make_headers(token),
        )
        assert resp_list_addr.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ipam_ipv6_prefix_delegation_slicing(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("src.api.v1.ipam.write_audit_log", fake_audit)

    tenant_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    session_id = "sess-ipam-002"
    sess_key = f"rg:{tenant_id}:sess:{session_id}"

    await fake_redis.hset(
        sess_key,
        mapping={
            "session_id": session_id,
            "user_id": user_id,
            "username": "admin",
            "role": SystemRoleEnum.TENANT_ADMIN.value,
        },
    )

    token = create_jwt_access_token(
        user_id, tenant_id, "test_tenant", session_id, SystemRoleEnum.TENANT_ADMIN.value, True
    )

    mock_db = MockIpamDbSession(tenant_id)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    try:
        vrf = IPAMVrf(tenant_id=uuid.UUID(tenant_id), name="default")
        mock_db.add(vrf)

        # Crear bloque IPv6 /48 para delegación residencial /56
        resp_pfx_v6 = await async_client.post(
            "/api/v1/ipam/prefixes",
            headers=make_headers(token),
            json={
                "vrf_id": str(vrf.id),
                "prefix": "2803:cafe:b001::/48",
                "ip_family": "IPv6",
                "role": "CUSTOMER_RESIDENTIAL",
                "default_child_prefix_len": 56,
            },
        )
        assert resp_pfx_v6.status_code == 201
        pfx_v6_id = resp_pfx_v6.json()["id"]

        # Pedir siguiente subred /56 disponible
        resp_next_v6 = await async_client.get(
            f"/api/v1/ipam/prefixes/{pfx_v6_id}/next-available", headers=make_headers(token)
        )
        assert resp_next_v6.status_code == 200
        next_v6_data = resp_next_v6.json()
        assert next_v6_data["is_subnet"] is True
        assert "/56" in next_v6_data["next_available"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_field_ops_verification_and_fiber_cuts(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("src.api.v1.field_ops.write_audit_log", fake_audit)

    tenant_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    session_id = "sess-field-001"
    sess_key = f"rg:{tenant_id}:sess:{session_id}"

    await fake_redis.hset(
        sess_key,
        mapping={
            "session_id": session_id,
            "user_id": user_id,
            "username": "tecnico_carlos",
            "role": SystemRoleEnum.FIELD_TECH.value,
        },
    )

    token = create_jwt_access_token(
        user_id, tenant_id, "test_tenant", session_id, SystemRoleEnum.FIELD_TECH.value, True
    )

    mock_db = MockIpamDbSession(tenant_id)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    try:
        router_id = mock_db.routers[0].id
        svc = CustomerService(
            tenant_id=uuid.UUID(tenant_id),
            router_id=router_id,
            endpoint_identifier="avila_corp",
            device_serial="SN-12345678",
            service_type=CustomerServiceTypeEnum.PPPOE,
            onu_mode=ONUModeEnum.ROUTER,
            onu_mac_address="48:8F:5A:11:22:33",
            pon_port="gpon-olt1/1/1",
            optical_box="NAP-04",
            last_reachability_status="OFFLINE",
            status=CustomerServiceStatusEnum.ACTIVE,
        )
        mock_db.add(svc)

        # 1. Verificación 1-Click desde Campo
        resp_verify = await async_client.post(
            f"/api/v1/field-ops/verify/{svc.id}",
            headers=make_headers(token),
            json={"customer_service_id": str(svc.id), "onu_scanned_mac": "48:8F:5A:11:22:33"},
        )
        assert resp_verify.status_code == 200
        ver_data = resp_verify.json()
        assert ver_data["session_active"] is True
        assert ver_data["ping_success"] is True

        # 2. Motor de Correlación de Cortes de Fibra
        session_id_sup = "sess-field-002"
        sess_key_sup = f"rg:{tenant_id}:sess:{session_id_sup}"
        await fake_redis.hset(
            sess_key_sup,
            mapping={
                "session_id": session_id_sup,
                "user_id": user_id,
                "username": "supervisor",
                "role": SystemRoleEnum.SUPERVISOR.value,
            },
        )
        token_sup = create_jwt_access_token(
            user_id, tenant_id, "test_tenant", session_id_sup, SystemRoleEnum.SUPERVISOR.value, True
        )

        resp_cuts = await async_client.post(
            "/api/v1/field-ops/detect-fiber-cuts?threshold_onus=3",
            headers=make_headers(token_sup),
        )
        assert resp_cuts.status_code == 200
        cuts_data = resp_cuts.json()
        assert len(cuts_data) == 1
        assert "POSIBLE CORTE DE FIBRA ÓPTICA" in cuts_data[0]["incident_summary"]
        assert cuts_data[0]["affected_onus_count"] == 4
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ipam_customer_services_and_sync_mikrotik(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("src.api.v1.ipam.write_audit_log", fake_audit)

    tenant_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    session_id = "sess-ipam-003"
    sess_key = f"rg:{tenant_id}:sess:{session_id}"

    await fake_redis.hset(
        sess_key,
        mapping={
            "session_id": session_id,
            "user_id": user_id,
            "username": "admin",
            "role": SystemRoleEnum.TENANT_ADMIN.value,
        },
    )

    token = create_jwt_access_token(
        user_id, tenant_id, "test_tenant", session_id, SystemRoleEnum.TENANT_ADMIN.value, True
    )

    mock_db = MockIpamDbSession(tenant_id)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    try:
        router_id = mock_db.routers[0].id
        # 1. Crear servicio de cliente (CustomerService)
        resp_cs = await async_client.post(
            "/api/v1/ipam/customer-services",
            headers=make_headers(token),
            json={
                "router_id": str(router_id),
                "endpoint_identifier": "PPPOE-SUB-01",
                "service_type": "PPPOE",
                "auth_backend": "LOCAL_SECRET",
                "onu_mode": "ROUTER",
                "onu_mac_address": "AA:BB:CC:DD:EE:01",
                "device_serial": "ONU-TEST-001",
            },
        )
        assert resp_cs.status_code == 201
        cs_data = resp_cs.json()
        assert cs_data["endpoint_identifier"] == "PPPOE-SUB-01"

        # 2. Listar servicios de cliente
        resp_list = await async_client.get(
            "/api/v1/ipam/customer-services",
            headers=make_headers(token),
        )
        assert resp_list.status_code == 200
        assert len(resp_list.json()) >= 1

        # 3. Sincronizar desde MikroTik con Mock
        mock_client = AsyncMock()
        mock_client.get.return_value = [{"address": "172.16.10.1/24", "interface": "ether2"}]
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None

        with patch("src.api.v1.ipam.MikrotikRestClient", return_value=mock_client):
            resp_sync = await async_client.post(
                f"/api/v1/ipam/sync-mikrotik/{router_id}",
                headers=make_headers(token),
            )
            assert resp_sync.status_code == 200
            assert resp_sync.json()["status"] == "success"

        # 4. Sincronizar pools DHCP y leases desde MikroTik con mock completo
        async def mock_get(endpoint: str):
            if endpoint == "/ip/address":
                return [
                    {"address": "192.168.10.254/24", "interface": "bridge-anillo", "comment": "pc"},
                    {"address": "10.250.3.8/24", "interface": "ether1"},
                ]
            elif endpoint == "/ip/pool":
                return [
                    {"name": "pool-pcs", "ranges": "192.168.10.2-192.168.10.254", "total": "253", "used": "7"}
                ]
            elif endpoint == "/ip/dhcp-server":
                return [
                    {"name": "dhcp-anillo", "interface": "bridge-anillo", "address-pool": "pool-pcs"}
                ]
            elif endpoint == "/ip/dhcp-server/network":
                return [
                    {"address": "192.168.10.0/24", "gateway": "192.168.10.254", "dns-server": "192.168.10.254"}
                ]
            elif endpoint == "/ip/dhcp-server/lease":
                return [
                    {
                        "address": "192.168.10.253",
                        "mac-address": "00:50:79:66:68:0A",
                        "server": "dhcp-anillo",
                        "host-name": "VPCS",
                        "dynamic": "true",
                    }
                ]
            return []

        mock_client2 = AsyncMock()
        mock_client2.get.side_effect = mock_get
        mock_client2.__aenter__.return_value = mock_client2
        mock_client2.__aexit__.return_value = None

        with patch("src.api.v1.ipam.MikrotikRestClient", return_value=mock_client2):
            resp_sync2 = await async_client.post(
                f"/api/v1/ipam/sync-mikrotik/{router_id}",
                headers=make_headers(token),
            )
            assert resp_sync2.status_code == 200
            assert resp_sync2.json()["status"] == "success"

            # Test sync-all endpoint
            resp_sync_all = await async_client.post("/api/v1/ipam/sync-all", headers=make_headers(token))
            assert resp_sync_all.status_code == 200

            # Verificar que el prefijo del pool fue creado con is_pool=True
            resp_pfxs = await async_client.get("/api/v1/ipam/prefixes", headers=make_headers(token))
            assert resp_pfxs.status_code == 200
            pfx_items = resp_pfxs.json()
            pool_pfx = next((p for p in pfx_items if p["prefix"] == "192.168.10.0/24"), None)
            assert pool_pfx is not None
            assert pool_pfx["is_pool"] is True
            assert float(pool_pfx["utilization_pct"]) > 0

            # Verificar que la IP del lease DHCP está registrada
            resp_addrs = await async_client.get(
                f"/api/v1/ipam/addresses?prefix_id={pool_pfx['id']}",
                headers=make_headers(token),
            )
            assert resp_addrs.status_code == 200
            addrs = resp_addrs.json()
            lease_addr = next((a for a in addrs if "192.168.10.253" in a["address"]), None)
            assert lease_addr is not None
            assert lease_addr["status"] == "DHCP_DYNAMIC"
            assert lease_addr["mac_address"] == "00:50:79:66:68:0A"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_field_ops_orders_and_certification(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("src.api.v1.field_ops.write_audit_log", fake_audit)

    tenant_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())
    session_admin = "sess-admin-001"
    await fake_redis.hset(
        f"rg:{tenant_id}:sess:{session_admin}",
        mapping={
            "session_id": session_admin,
            "user_id": admin_id,
            "username": "supervisor_admin",
            "role": SystemRoleEnum.TENANT_ADMIN.value,
        },
    )
    token_admin = create_jwt_access_token(
        admin_id, tenant_id, "test_tenant", session_admin, SystemRoleEnum.TENANT_ADMIN.value, True
    )

    tech_id = str(uuid.uuid4())
    session_tech = "sess-field-003"
    await fake_redis.hset(
        f"rg:{tenant_id}:sess:{session_tech}",
        mapping={
            "session_id": session_tech,
            "user_id": tech_id,
            "username": "tech_field",
            "role": SystemRoleEnum.FIELD_TECH.value,
        },
    )
    token_tech = create_jwt_access_token(
        tech_id, tenant_id, "test_tenant", session_tech, SystemRoleEnum.FIELD_TECH.value, True
    )

    mock_db = MockIpamDbSession(tenant_id)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    try:
        router_id = mock_db.routers[0].id
        svc = CustomerService(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            router_id=router_id,
            endpoint_identifier="SUB-ORDER-01",
            device_serial="SN-ORDER-99",
            service_type=CustomerServiceTypeEnum.PPPOE,
            onu_mode=ONUModeEnum.ROUTER,
            status=CustomerServiceStatusEnum.PENDING_INSTALL,
            last_reachability_status="ONLINE",
        )
        mock_db.add(svc)

        # 1. Crear orden de instalación de campo (Supervisor / Admin)
        resp_order = await async_client.post(
            "/api/v1/field-ops/orders",
            headers=make_headers(token_admin),
            json={
                "customer_service_id": str(svc.id),
                "notes": "Instalación en NAP 02 puerto 4",
            },
        )
        assert resp_order.status_code == 201
        order_data = resp_order.json()
        order_id = order_data["id"]

        # 2. Listar órdenes
        resp_list = await async_client.get(
            "/api/v1/field-ops/orders",
            headers=make_headers(token_tech),
        )
        assert resp_list.status_code == 200
        assert len(resp_list.json()) >= 1

        # 3. Certificar orden de instalación (Técnico de campo)
        resp_cert = await async_client.post(
            "/api/v1/field-ops/certify",
            headers=make_headers(token_tech),
            json={
                "order_id": order_id,
                "onu_scanned_serial": "SN-ORDER-99-OK",
                "onu_scanned_mac": "AA:BB:CC:11:22:33",
                "tech_latitude": 10.4850,
                "tech_longitude": -66.9050,
                "notes": "Certificación exitosa con niveles ópticos adecuados",
            },
        )
        assert resp_cert.status_code == 200
        assert resp_cert.json()["status"] == "CERTIFIED"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_simulate_subscribers_from_dhcp(
    async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr("src.api.v1.subscribers.write_audit_log", fake_audit)

    tenant_id = str(uuid.uuid4())
    admin_id = str(uuid.uuid4())
    session_admin = "sess-admin-sim-001"
    await fake_redis.hset(
        f"rg:{tenant_id}:sess:{session_admin}",
        mapping={
            "session_id": session_admin,
            "user_id": admin_id,
            "username": "noc_operator",
            "role": SystemRoleEnum.TENANT_ADMIN.value,
        },
    )
    token_admin = create_jwt_access_token(
        admin_id, tenant_id, "test_tenant", session_admin, SystemRoleEnum.TENANT_ADMIN.value, True
    )

    mock_db = MockIpamDbSession(tenant_id)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    try:
        # 1. Simular clientes a partir de las IPs/DHCP del tenant
        resp_sim = await async_client.post(
            "/api/v1/subscriber-devices/simulate-from-dhcp?reset_existing=false",
            headers=make_headers(token_admin),
        )
        assert resp_sim.status_code == 200
        sim_data = resp_sim.json()
        assert "created_count" in sim_data
        assert "total_subscribers" in sim_data
        assert sim_data["created_count"] >= 1
        assert "clientes de laboratorio" in sim_data["message"]

        # 2. Verificar que se puedan listar los clientes para el mapa
        resp_list = await async_client.get(
            "/api/v1/subscriber-devices",
            headers=make_headers(token_admin),
        )
        assert resp_list.status_code == 200
        devices = resp_list.json()
        assert len(devices) >= 1
        dev0 = devices[0]
        assert "latitude" in dev0
        assert "longitude" in dev0
        assert "optical_box" in dev0
        assert "last_reachability_status" in dev0
    finally:
        app.dependency_overrides.clear()

