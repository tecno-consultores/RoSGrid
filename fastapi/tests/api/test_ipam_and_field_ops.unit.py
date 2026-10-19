# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from datetime import UTC, datetime
from decimal import Decimal
import pytest
from httpx import AsyncClient

from src.api.v1.auth import create_jwt_access_token
from src.db.session import get_tenant_db_session
from src.main import app
from src.models.core import SystemRoleEnum
from src.models.ipam import (
    CustomerService,
    CustomerServiceStatusEnum,
    CustomerServiceTypeEnum,
    FiberCutIncident,
    FiberCutStatusEnum,
    FieldInstallationOrder,
    FieldOrderStatusEnum,
    IPAddressStatusEnum,
    IPAMAddress,
    IPAMPrefix,
    IPAMVrf,
    IPFamilyEnum,
    IPPrefixRoleEnum,
    IPPrefixStatusEnum,
    ONUModeEnum,
)
from src.models.inventory import Router, RouterAdminStateEnum, RouterNetworkRoleEnum
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
            return MockResult(self.prefixes)
        elif "ipam_ip_addresses" in stmt_str:
            return MockResult(self.addresses)
        elif "subscriber_devices" in stmt_str or "customer_services" in stmt_str:
            if "count(" in stmt_str:
                if self.customer_services:
                    r_id = self.customer_services[0].router_id
                    return MockResult([(r_id, "gpon-olt1/1/1", "NAP-04", 4)])
                return MockResult([])
            return MockResult(self.customer_services)
        elif "field_installation_orders" in stmt_str:
            return MockResult(self.field_orders)
        elif "fiber_cut_incidents" in stmt_str:
            return MockResult(self.fiber_cuts)
        elif "routers" in stmt_str:
            return MockResult(self.routers)

        return MockResult([])


@pytest.mark.asyncio
async def test_ipam_vrf_and_prefix_lifecycle(async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch):
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
        resp_next = await async_client.get(f"/api/v1/ipam/prefixes/{pfx_id}/next-available", headers=make_headers(token))
        assert resp_next.status_code == 200
        next_data = resp_next.json()
        assert next_data["next_available"] == "100.64.10.1"
        assert next_data["is_subnet"] is False
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_ipam_ipv6_prefix_delegation_slicing(async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch):
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
        resp_next_v6 = await async_client.get(f"/api/v1/ipam/prefixes/{pfx_v6_id}/next-available", headers=make_headers(token))
        assert resp_next_v6.status_code == 200
        next_v6_data = resp_next_v6.json()
        assert next_v6_data["is_subnet"] is True
        assert "/56" in next_v6_data["next_available"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_field_ops_verification_and_fiber_cuts(async_client: AsyncClient, fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch):
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
