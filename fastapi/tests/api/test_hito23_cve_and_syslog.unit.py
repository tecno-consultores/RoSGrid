# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.v1.cve import get_fleet_cves_summary, sync_cve_database
from src.api.v1.syslog import get_syslog_provisioning_template
from src.models.core import Tenant, TenantStatusEnum
from src.schemas.cve import CveSyncResponse, FleetCveSummary, RouterCveEvaluation
from src.services.cve_matcher import (
    compare_ros_versions,
    evaluate_fleet_cves,
    evaluate_router_cves,
    is_version_affected,
    load_cve_catalog,
    parse_ros_version,
)
from src.workers.syslog_collector import (
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
    assert compare_ros_versions(v1, ">=", v2) is False
    assert compare_ros_versions(v1, "==", (7, 12, 0)) is True


def test_is_version_affected():
    expr = ">=7.0.0,<7.16.0"
    assert is_version_affected("7.15.3", expr) is True
    assert is_version_affected("7.16.0", expr) is False
    assert is_version_affected("7.16.2", expr) is False
    assert is_version_affected("6.49", expr) is False
    assert is_version_affected(None, expr) is False


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
