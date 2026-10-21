# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.v1.cve import get_fleet_cves_summary, get_router_cves, sync_cve_database
from src.api.v1.syslog import get_router_syslog, get_syslog_provisioning_template
from src.models.core import Tenant, TenantStatusEnum
from src.models.inventory import Router
from src.schemas.cve import CveSyncResponse, FleetCveSummary, RouterCveEvaluation
from src.services.cve_matcher import (
    _check_single_clause,
    compare_ros_versions,
    evaluate_fleet_cves,
    evaluate_router_cves,
    is_version_affected,
    load_cve_catalog,
    parse_ros_version,
    sync_cve_catalog,
)
from src.workers.syslog_collector import (
    SyslogUdpProtocol,
    get_router_syslog_events,
    parse_syslog_message,
    push_event_to_ringbuffer,
)


def test_parse_semver_valid():
    assert parse_ros_version("7.16.2") == (7, 16, 2)
    assert parse_ros_version("v7.15") == (7, 15, 0)
    assert parse_ros_version("7.13rc2") == (7, 13, 0)
    assert parse_ros_version("invalid") is None
    assert parse_ros_version(None) is None


def test_compare_semver():
    v1 = (7, 12, 0)
    v2 = (7, 13, 0)
    assert compare_ros_versions(v1, "<", v2) is True
    assert compare_ros_versions(v1, "<=", v2) is True
    assert compare_ros_versions(v2, ">", v1) is True
    assert compare_ros_versions(v1, ">=", v2) is False
    assert compare_ros_versions(v1, "==", (7, 12, 0)) is True
    assert compare_ros_versions(v1, "!=", v2) is False


def test_is_version_affected():
    expr = ">=7.0.0,<7.16.0"
    assert is_version_affected("7.15.3", expr) is True
    assert is_version_affected("7.16.0", expr) is False
    assert is_version_affected("7.16.2", expr) is False
    assert is_version_affected("6.49", expr) is False
    assert is_version_affected(None, expr) is False
    assert _check_single_clause((7, 15, 0), "invalid_clause") is False
    assert _check_single_clause((7, 15, 0), ">=invalid_version") is False


def test_cve_catalog_loading():
    catalog = load_cve_catalog()
    assert len(catalog) >= 5
    cve_ids = [item.cve_id for item in catalog]
    assert "CVE-2023-32154" in cve_ids
    assert "CVE-2024-38355" in cve_ids


@pytest.fixture
def sample_tenant() -> Tenant:
    return Tenant(
        id=uuid.uuid4(),
        name="Corp Net",
        slug="corp-net",
        status=TenantStatusEnum.ACTIVE,
        cve_scanner_enabled=True,
        syslog_collector_enabled=True,
        l2_topology_enabled=True,
    )


@pytest.fixture
def sample_claims(sample_tenant: Tenant) -> dict[str, str]:
    return {
        "sub": str(uuid.uuid4()),
        "tid": str(sample_tenant.id),
        "rol": "TENANT_ADMIN",
    }


def test_evaluate_router_cves():
    res = evaluate_router_cves(uuid.uuid4(), "Core-Router", "7.8")
    assert isinstance(res, RouterCveEvaluation)
    assert res.total_vulnerabilities > 0
    assert any(c.cve_id == "CVE-2023-32154" for c in res.vulnerabilities)

    # Version segura reciente
    res_clean = evaluate_router_cves(uuid.uuid4(), "Edge-Router", "7.19")
    assert res_clean.total_vulnerabilities == 0


def test_evaluate_fleet_cves():
    fleet = [
        {"id": uuid.uuid4(), "display_name": "R1", "ros_version": "7.10"},
        {"id": uuid.uuid4(), "display_name": "R2", "ros_version": "7.18"},
    ]
    summary = evaluate_fleet_cves(fleet)
    assert isinstance(summary, FleetCveSummary)
    assert summary.total_evaluated_routers == 2
    assert summary.vulnerable_routers_count == 1


def test_parse_syslog_bsd_message():
    raw_info = "<14>Feb 20 10:00:00 MikroTik system,info User admin logged in"
    event_info = parse_syslog_message(raw_info)
    assert event_info.severity == "info"
    assert event_info.is_critical is False
    assert "User admin logged in" in event_info.message

    raw_crit = "<11>Feb 20 10:01:00 MikroTik interface,warning ether1 link down"
    event_crit = parse_syslog_message(raw_crit)
    assert event_crit.severity == "error"
    assert event_crit.is_critical is True


@pytest.mark.asyncio
async def test_syslog_ringbuffer_push_and_query():
    tid = uuid.uuid4()
    rid = uuid.uuid4()
    ev1 = parse_syslog_message("<11>Feb 20 10:01:00 MikroTik interface,warning ether1 link down")
    ev2 = parse_syslog_message("<14>Feb 20 10:02:00 MikroTik system,info ping reply")

    await push_event_to_ringbuffer(tid, rid, ev1)
    await push_event_to_ringbuffer(tid, rid, ev2)

    events = await get_router_syslog_events(tid, rid, limit=10)
    assert len(events) >= 2
    assert any(e.is_critical for e in events)


@pytest.mark.asyncio
async def test_cve_api_endpoints(sample_tenant, sample_claims):
    db = AsyncMock()
    db.get.return_value = sample_tenant
    mock_res = MagicMock()
    mock_res.all.return_value = [
        (uuid.uuid4(), "R1", "7.10"),
        (uuid.uuid4(), "R2", "7.19"),
    ]
    db.execute.return_value = mock_res

    res = await get_fleet_cves_summary(claims=sample_claims, db=db)
    assert res.total_evaluated_routers == 2

    fake_sync = CveSyncResponse(
        success=True,
        source_url="https://feed.local",
        total_cves=6,
        updated_at=datetime.now(timezone.utc),
        message="Synced",
    )
    with patch("src.api.v1.cve.sync_cve_catalog", AsyncMock(return_value=fake_sync)):
        sync_res = await sync_cve_database(claims=sample_claims, db=db)
        assert sync_res.total_cves == 6


@pytest.mark.asyncio
async def test_syslog_api_template_endpoint(sample_tenant, sample_claims):
    db = AsyncMock()
    db.get.return_value = sample_tenant
    res = await get_syslog_provisioning_template(claims=sample_claims, db=db)
    assert "/system logging action" in res.template_content
    assert res.default_port == 5514


@pytest.mark.asyncio
async def test_syslog_api_template_tenant_not_found(sample_claims):
    db = AsyncMock()
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        await get_syslog_provisioning_template(claims=sample_claims, db=db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_syslog_api_template_feature_disabled(sample_tenant, sample_claims):
    sample_tenant.syslog_collector_enabled = False
    db = AsyncMock()
    db.get.return_value = sample_tenant
    with pytest.raises(HTTPException) as exc:
        await get_syslog_provisioning_template(claims=sample_claims, db=db)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_router_syslog_endpoint(sample_tenant, sample_claims):
    db = AsyncMock()
    db.get.return_value = sample_tenant
    router_id = uuid.uuid4()
    mock_router = Router(id=router_id, tenant_id=sample_tenant.id, display_name="R-Test", is_reachable=True)
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_router
    db.execute.return_value = mock_res

    with patch("src.api.v1.syslog.get_router_syslog_events", AsyncMock(return_value=[])):
        res = await get_router_syslog(router_id=router_id, limit=20, claims=sample_claims, db=db)
        assert res.router_id == router_id
        assert res.total_in_buffer == 0


@pytest.mark.asyncio
async def test_get_router_syslog_router_not_found(sample_tenant, sample_claims):
    db = AsyncMock()
    db.get.return_value = sample_tenant
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_res

    with pytest.raises(HTTPException) as exc:
        await get_router_syslog(router_id=uuid.uuid4(), limit=20, claims=sample_claims, db=db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_router_syslog_tenant_not_found(sample_claims):
    db = AsyncMock()
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        await get_router_syslog(router_id=uuid.uuid4(), limit=20, claims=sample_claims, db=db)
    assert exc.value.status_code == 404


def test_parse_syslog_local_facility():
    # pri 134: facility = 134 >> 3 = 16 (local0), severity = 134 & 7 = 6 (info)
    msg = "<134>Feb 20 10:00:00 MikroTik system,info local facility test"
    event = parse_syslog_message(msg)
    assert event.facility == "local16"
    assert event.severity == "info"


@pytest.mark.asyncio
async def test_push_event_to_ringbuffer_handles_redis_error():
    ev = parse_syslog_message("<11> critical down")
    with patch("src.workers.syslog_collector.get_redis_client", side_effect=Exception("Redis down")):
        # Should not raise exception
        await push_event_to_ringbuffer(uuid.uuid4(), uuid.uuid4(), ev)


@pytest.mark.asyncio
async def test_get_router_syslog_events_handles_redis_error():
    with patch("src.workers.syslog_collector.get_redis_client", side_effect=Exception("Redis down")):
        events = await get_router_syslog_events(uuid.uuid4(), uuid.uuid4())
        assert events == []


def test_syslog_udp_protocol():
    tid = uuid.uuid4()
    rid = uuid.uuid4()
    ip_map = {"192.168.1.1": (tid, rid)}
    proto = SyslogUdpProtocol(ip_map)

    # Unknown IP dropped
    proto.datagram_received(b"<14>test", ("10.0.0.99", 5514))

    # Known IP processed
    with patch("src.workers.syslog_collector.push_event_to_ringbuffer", AsyncMock()):
        proto.datagram_received(b"<14>test known", ("192.168.1.1", 5514))

    # Error handling during decode / parse
    with patch("src.workers.syslog_collector.parse_syslog_message", side_effect=Exception("parse error")):
        proto.datagram_received(b"broken", ("192.168.1.1", 5514))


def test_cve_catalog_loading_missing_and_corrupt(tmp_path):
    with patch("src.services.cve_matcher._CATALOG_PATH", tmp_path / "nonexistent.json"):
        cat = load_cve_catalog(force_reload=True)
        assert cat == []

    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("not json content", encoding="utf-8")
    with patch("src.services.cve_matcher._CATALOG_PATH", corrupt_file):
        cat_corrupt = load_cve_catalog(force_reload=True)
        assert cat_corrupt == []


@pytest.mark.asyncio
async def test_sync_cve_catalog(tmp_path):
    # Successful mock response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "cve_id": "CVE-2026-9999",
            "title": "Mock Vulnerability",
            "cvss_score": 8.0,
            "severity": "HIGH",
            "affected_versions_expr": ">=7.0.0,<7.20.0",
            "fixed_in_version": "7.20.0",
            "description_es": "Descripción de prueba",
            "remediation": "Actualizar RouterOS",
            "published_date": "2026-01-01",
        }
    ]

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    mock_catalog_file = tmp_path / "mock_catalog.json"
    with (
        patch("httpx.AsyncClient", return_value=mock_client),
        patch("src.services.cve_matcher._CATALOG_PATH", mock_catalog_file),
    ):
        res = await sync_cve_catalog("https://example.com/cve-feed")
        assert res.success is True
        assert res.total_cves == 1

    # Failure fallback to local catalog
    mock_fail_client = AsyncMock()
    mock_fail_client.get.side_effect = Exception("Network timeout")
    mock_fail_client.__aenter__.return_value = mock_fail_client
    mock_fail_client.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=mock_fail_client):
        res_fail = await sync_cve_catalog("https://invalid.local")
        assert res_fail.success is False
        assert res_fail.total_cves >= 0


@pytest.mark.asyncio
async def test_get_router_cves_endpoint(sample_tenant, sample_claims):
    db = AsyncMock()
    db.get.return_value = sample_tenant
    r_id = uuid.uuid4()
    mock_r = Router(id=r_id, tenant_id=sample_tenant.id, display_name="R1", ros_version="7.10")
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = mock_r
    db.execute.return_value = mock_res

    res = await get_router_cves(router_id=r_id, claims=sample_claims, db=db)
    assert res.router_id == r_id
    assert res.total_vulnerabilities > 0


@pytest.mark.asyncio
async def test_get_router_cves_not_found(sample_tenant, sample_claims):
    db = AsyncMock()
    db.get.return_value = sample_tenant
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_res

    with pytest.raises(HTTPException) as exc:
        await get_router_cves(router_id=uuid.uuid4(), claims=sample_claims, db=db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_cve_endpoints_tenant_not_found_and_disabled(sample_tenant, sample_claims):
    db = AsyncMock()
    db.get.return_value = None

    with pytest.raises(HTTPException) as exc:
        await get_fleet_cves_summary(claims=sample_claims, db=db)
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        await sync_cve_database(claims=sample_claims, db=db)
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        await get_router_cves(router_id=uuid.uuid4(), claims=sample_claims, db=db)
    assert exc.value.status_code == 404

    # Feature disabled
    sample_tenant.cve_scanner_enabled = False
    db.get.return_value = sample_tenant

    with pytest.raises(HTTPException) as exc:
        await get_fleet_cves_summary(claims=sample_claims, db=db)
    assert exc.value.status_code == 403

    with pytest.raises(HTTPException) as exc:
        await sync_cve_database(claims=sample_claims, db=db)
    assert exc.value.status_code == 403

    with pytest.raises(HTTPException) as exc:
        await get_router_cves(router_id=uuid.uuid4(), claims=sample_claims, db=db)
    assert exc.value.status_code == 403
