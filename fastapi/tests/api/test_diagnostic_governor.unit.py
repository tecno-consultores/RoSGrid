# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para el Gobernador Anti-Saturación de Diagnósticos (KeyDB + RouterOS v7)."""

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
from src.models.ipam import SubscriberDevice
from src.services.diagnostic_governor import DiagnosticGovernor
from tests.conftest import FakeAsyncRedis


class MockGovernorDbResult:
    def __init__(self, item: Any = None, items: list[Any] | None = None):
        self._item = item
        self._items = items or ([item] if item is not None else [])

    def scalar_one_or_none(self) -> Any:
        return self._item

    def scalar(self) -> Any:
        return self._item if self._item is not None else 0

    def scalars(self) -> Any:
        class S:
            def __init__(self, it: list[Any]):
                self._it = it

            def all(self) -> list[Any]:
                return self._it

        return S(self._items)


class MockGovernorDbSession:
    def __init__(self, tenant_id: uuid.UUID):
        self.tenant_id = tenant_id
        self.tenant = Tenant(
            id=self.tenant_id,
            name="Governor Tenant",
            slug="governor-tenant",
            isp_module_enabled=True,
        )
        self.router = Router(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            display_name="CCR2004-Edge",
            api_base_url="https://10.0.0.1:443",
            api_port=443,
            network_role=RouterNetworkRoleEnum.DISTRIBUTION_SWITCH,
            admin_state=RouterAdminStateEnum.PRODUCTION,
            physical_location="POP Central",
            latitude=10.4806,
            longitude=-66.9036,
        )
        now = datetime.now(UTC)
        self.device = SubscriberDevice(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            router_id=self.router.id,
            endpoint_identifier="PC-FINANZAS (192.168.88.50)",
            service_type="DHCP",
            auth_backend="LOCAL_SECRET",
            onu_mode="BRIDGE",
            assigned_ipv4="192.168.88.50",
            status="ACTIVE",
            last_reachability_status="UNKNOWN",
            latitude=10.4806,
            longitude=-66.9036,
            is_custom_coordinates=False,
            created_at=now,
            updated_at=now,
        )

    async def commit(self) -> None:
        pass

    async def flush(self) -> None:
        pass

    async def execute(self, stmt: Any) -> MockGovernorDbResult:
        s = str(stmt).lower()
        if "from tenants" in s:
            return MockGovernorDbResult(self.tenant)
        if "from subscriber_devices" in s:
            return MockGovernorDbResult(self.device)
        if "from routers" in s:
            return MockGovernorDbResult(self.router)
        return MockGovernorDbResult(None)


class MockPingClient:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.call_count = 0

    async def __aenter__(self) -> "MockPingClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    async def post(self, endpoint: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError("MikroTik RouterOS API timeout (simulado)")
        return [{"status": "echo reply", "time": "8.5ms"}]


@pytest.fixture
def gov_auth(fake_redis: FakeAsyncRedis) -> dict[str, Any]:
    tid = uuid.uuid4()
    uid = uuid.uuid4()
    sid = "sess-gov-001"
    import asyncio

    asyncio.get_event_loop().run_until_complete(
        fake_redis.hset(
            f"rg:{tid}:sess:{sid}",
            mapping={
                "session_id": sid,
                "user_id": str(uid),
                "username": "fieldtech_01",
                "role": SystemRoleEnum.FIELD_TECH.value,
            },
        )
    )
    token = create_jwt_access_token(str(uid), str(tid), "gov-tenant", sid, SystemRoleEnum.FIELD_TECH.value, True)
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
async def test_diagnostic_cache_hit_and_anti_thundering_herd(
    async_client: AsyncClient, gov_auth: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    tid = gov_auth["tenant_id"]
    headers = gov_auth["headers"]

    mock_db = MockGovernorDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    mock_client = MockPingClient()
    import src.api.v1.subscribers as subs_module

    monkeypatch.setattr(subs_module, "_get_router_client", lambda r, t: mock_client)

    try:
        # Primer Ping: Se ejecuta contra el router y se almacena en caché
        res1 = await async_client.post(
            f"/api/v1/subscriber-devices/{mock_db.device.id}/ping",
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["is_cached"] is False
        assert mock_client.call_count == 1

        # Segundo Ping inmediato (dentro de los 15s): Debe responder desde la caché de KeyDB
        res2 = await async_client.post(
            f"/api/v1/subscriber-devices/{mock_db.device.id}/ping",
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["is_cached"] is True
        assert data2["cache_ttl_remaining"] > 0
        assert "Caché reciente" in data2["message"]
        # El router NO fue consultado una segunda vez (call_count sigue siendo 1)
        assert mock_client.call_count == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_user_rate_limit_exceeded_429(
    async_client: AsyncClient, gov_auth: dict[str, Any], fake_redis: FakeAsyncRedis
) -> None:
    tid = gov_auth["tenant_id"]
    uid = gov_auth["user_id"]
    headers = gov_auth["headers"]

    mock_db = MockGovernorDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    # Simular que el usuario ya realizó 60 peticiones en el último minuto
    await fake_redis.set(f"rg:{tid}:diag:rate:user:{uid}", DiagnosticGovernor.MAX_PER_MINUTE_PER_USER)

    try:
        res = await async_client.post(
            f"/api/v1/subscriber-devices/{mock_db.device.id}/ping",
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res.status_code == 429
        assert "Límite de solicitudes de diagnóstico excedido" in res.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_router_concurrency_governor_429(
    async_client: AsyncClient, gov_auth: dict[str, Any], fake_redis: FakeAsyncRedis
) -> None:
    tid = gov_auth["tenant_id"]
    headers = gov_auth["headers"]

    mock_db = MockGovernorDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    # Simular que el router ya tiene 3 peticiones en curso (semáforo lleno)
    await fake_redis.set(f"rg:{tid}:diag:inflight:{mock_db.router.id}", DiagnosticGovernor.MAX_CONCURRENT_PER_ROUTER)

    try:
        res = await async_client.post(
            f"/api/v1/subscriber-devices/{mock_db.device.id}/ping",
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res.status_code == 429
        assert "diagnósticos concurrentes" in res.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_router_circuit_breaker_tripped_direct_slot_503(
    fake_redis: FakeAsyncRedis
) -> None:
    tid = uuid.uuid4()
    rid = uuid.uuid4()

    # Simular que el Circuit Breaker del router está ABIERTO
    await fake_redis.set(f"rg:{tid}:diag:cb:{rid}", "OPEN")

    with pytest.raises(Exception) as exc_info:
        async with DiagnosticGovernor.acquire_router_slot(tid, rid):
            pass
    assert "Circuito de diagnóstico abierto" in str(exc_info.value)


@pytest.mark.asyncio
async def test_diagnostic_root_cause_suppression_when_router_down(
    async_client: AsyncClient, gov_auth: dict[str, Any], fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    tid = gov_auth["tenant_id"]
    headers = gov_auth["headers"]

    mock_db = MockGovernorDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    mock_client = MockPingClient()
    import src.api.v1.subscribers as subs_module

    monkeypatch.setattr(subs_module, "_get_router_client", lambda r, t: mock_client)

    # Simular router caído con Circuit Breaker OPEN
    await fake_redis.set(f"rg:{tid}:diag:cb:{mock_db.router.id}", "OPEN")

    try:
        res = await async_client.post(
            f"/api/v1/subscriber-devices/{mock_db.device.id}/ping",
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ROOT_CAUSE_SUPPRESSED"
        assert data["last_reachability_status"] == "OFFLINE"
        assert "Diagnóstico omitido" in data["message"]
        assert data["root_cause_device_name"] == mock_db.router.display_name
        # El router NO fue consultado en absoluto
        assert mock_client.call_count == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_device_operational_lock_and_collision_avoidance(
    async_client: AsyncClient, gov_auth: dict[str, Any], fake_redis: FakeAsyncRedis, monkeypatch: pytest.MonkeyPatch
) -> None:
    tid = gov_auth["tenant_id"]
    headers = gov_auth["headers"]
    uid = gov_auth["user_id"]

    mock_db = MockGovernorDbSession(tid)
    app.dependency_overrides[get_tenant_db_session] = lambda: mock_db

    mock_client = MockPingClient()
    import src.api.v1.subscribers as subs_module

    monkeypatch.setattr(subs_module, "_get_router_client", lambda r, t: mock_client)

    try:
        # 1. Técnico 1 realiza Ping: adquiere el lock operativo
        res1 = await async_client.post(
            f"/api/v1/subscriber-devices/{mock_db.device.id}/ping",
            headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["operational_lock"] is not None
        assert data1["operational_lock"]["technician_id"] == str(uid)

        # 2. Técnico 2 consulta el estado operativo de ese mismo dispositivo
        other_uid = uuid.uuid4()
        other_sid = "sess-other-tech"
        await fake_redis.hset(
            f"rg:{tid}:sess:{other_sid}",
            mapping={
                "session_id": other_sid,
                "user_id": str(other_uid),
                "username": "pedro_field",
                "role": SystemRoleEnum.FIELD_TECH.value,
            },
        )
        other_token = create_jwt_access_token(str(other_uid), str(tid), "gov-tenant", other_sid, SystemRoleEnum.FIELD_TECH.value, True)
        other_headers = {
            "Authorization": f"Bearer {other_token}",
            "Cookie": f"rosgrid_access_token={other_token}",
        }

        res_status = await async_client.get(
            f"/api/v1/subscriber-devices/{mock_db.device.id}/operational-status",
            headers=other_headers,
        )
        assert res_status.status_code == 200
        st_data = res_status.json()
        assert st_data["is_locked"] is True
        assert st_data["is_locked_by_other"] is True
        assert "En atención" in st_data["message"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_router_circuit_breaker_recovery(fake_redis: FakeAsyncRedis) -> None:
    tid = uuid.uuid4()
    rid = uuid.uuid4()

    # 1. Registrar 3 fallas y verificar que se abra el circuito
    await DiagnosticGovernor.record_router_failure(tid, rid)
    await DiagnosticGovernor.record_router_failure(tid, rid)
    await DiagnosticGovernor.record_router_failure(tid, rid)

    cb_state = await fake_redis.get(f"rg:{tid}:diag:cb:{rid}")
    assert cb_state == "OPEN"

    # 2. Registrar éxito y comprobar que el circuito se restablece
    await DiagnosticGovernor.record_router_success(tid, rid)
    cb_after = await fake_redis.get(f"rg:{tid}:diag:cb:{rid}")
    assert cb_after is None

