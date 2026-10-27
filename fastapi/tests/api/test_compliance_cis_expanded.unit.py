# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para la expansión de CIS Benchmark (28 Directivas, Enlaces Oficiales) y Catálogo de Plantillas Masivas Avanzadas (Hito 27.11)."""

import uuid
from datetime import date
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request

from src.api.v1.bulk_and_updates import _DEFAULT_STARTER_TEMPLATES
from src.api.v1.compliance import (
    CIS_CATALOG_BASE,
    _build_default_cis_rules,
    get_cis_catalog,
    run_cis_audit,
)
from src.models.inventory import Router
from src.schemas.enterprise import (
    CisPolicyRule,
)


class MockDbResult:
    """Mock para resultados de SQLAlchemy en AsyncSession."""

    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def scalar_one_or_none(self) -> Any:
        return self._items[0] if self._items else None

    def scalars(self) -> "MockDbResult":
        return self

    def all(self) -> list[Any]:
        return self._items


@pytest.fixture
def sample_tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_claims(sample_tenant_id: uuid.UUID) -> dict[str, Any]:
    return {
        "sub": str(uuid.uuid4()),
        "tid": str(sample_tenant_id),
        "username": "noc_operator",
        "rol": "TENANT_ADMIN",
    }


@pytest.fixture
def mock_request() -> MagicMock:
    req = MagicMock(spec=Request)
    req.client.host = "10.250.0.10"
    req.headers = {"user-agent": "RoSGrid-11X-TestRunner"}
    return req


def test_cis_catalog_completeness_and_official_links() -> None:
    """Certifica que el catálogo base CIS contenga exactamente 28 directivas con referencias y enlaces canónicos."""
    assert len(CIS_CATALOG_BASE) == 28, f"Se esperaban 28 directivas CIS, encontradas: {len(CIS_CATALOG_BASE)}"

    expected_codes = {
        "CIS-1.1", "CIS-1.2", "CIS-1.3", "CIS-1.4", "CIS-1.5", "CIS-1.6",
        "CIS-1.7", "CIS-1.8", "CIS-1.9", "CIS-1.10", "CIS-2.1", "CIS-2.2",
        "CIS-ISP-1", "CIS-ISP-2", "CIS-ISP-3", "CIS-ISP-4",
        "CIS-ISP-5", "CIS-ISP-6", "CIS-ISP-7", "CIS-ISP-8",
        "CIS-CORP-1", "CIS-CORP-2", "CIS-CORP-3", "CIS-CORP-4",
        "CIS-CORP-5", "CIS-CORP-6", "CIS-CORP-7", "CIS-CORP-8",
    }
    actual_codes = {item["code"] for item in CIS_CATALOG_BASE}
    assert actual_codes == expected_codes, f"Discrepancia en códigos de directivas: {actual_codes ^ expected_codes}"

    for d in CIS_CATALOG_BASE:
        code = d["code"]
        assert d.get("title"), f"Directiva {code} carece de título"
        assert d.get("category"), f"Directiva {code} carece de categoría"
        assert d.get("weight", 0) > 0, f"Directiva {code} tiene peso inválido"
        assert d.get("severity") in ("CRITICAL", "HIGH", "MEDIUM", "LOW"), f"Severidad inválida en {code}"
        assert d.get("remediation_cmd"), f"Directiva {code} carece de comando de remediación"
        assert d.get("standard_ref"), f"Directiva {code} carece de standard_ref normativo"
        assert d.get("standard_url", "").startswith("http"), f"Directiva {code} carece de standard_url HTTP válida"
        assert "manual.mikrotik.com" in d.get("reference_url", ""), f"Directiva {code} no apunta al manual oficial de MikroTik"
        assert d.get("rationale"), f"Directiva {code} carece de rationale de riesgo"


@pytest.mark.asyncio
async def test_get_cis_catalog_endpoint() -> None:
    """Certifica que el endpoint GET /compliance/cis-catalog exponga las 28 directivas completas."""
    catalog = await get_cis_catalog()
    assert len(catalog) == 28
    assert all(isinstance(r, CisPolicyRule) for r in catalog)
    assert all(r.enabled is True for r in catalog)


def test_build_default_cis_rules_sovereignty() -> None:
    """Certifica la soberanía del usuario: todas las directivas están disponibles y se pre-activan según perfil."""
    # 1. Perfil ISP
    isp_rules = _build_default_cis_rules("ISP")
    assert len(isp_rules) == 28
    isp_enabled_codes = {r.code for r in isp_rules if r.enabled}
    assert "CIS-ISP-1" in isp_enabled_codes
    assert "CIS-ISP-3" in isp_enabled_codes
    assert "CIS-CORP-1" not in isp_enabled_codes
    assert "CIS-1.10" not in isp_enabled_codes

    # 2. Perfil CORPORATE
    corp_rules = _build_default_cis_rules("CORPORATE")
    assert len(corp_rules) == 28
    corp_enabled_codes = {r.code for r in corp_rules if r.enabled}
    assert "CIS-CORP-1" in corp_enabled_codes
    assert "CIS-CORP-4" in corp_enabled_codes
    assert "CIS-ISP-3" not in corp_enabled_codes

    # 3. Perfil DATACENTER (todas activas)
    dc_rules = _build_default_cis_rules("DATACENTER")
    assert len(dc_rules) == 28
    assert all(r.enabled is True for r in dc_rules)


@pytest.mark.asyncio
async def test_run_cis_audit_score_dynamic_calculation(
    sample_tenant_id: uuid.UUID, sample_claims: dict[str, Any]
) -> None:
    """Certifica el cálculo dinámico del Security Score considerando únicamente directivas habilitadas."""
    router_id = uuid.uuid4()
    mock_router = Router(
        id=router_id,
        tenant_id=sample_tenant_id,
        display_name="Router 1 Core Test",
        api_base_url="https://10.250.3.4",
        api_port=443,
        network_role="CORE",
        serial_number="SN-TEST-CIS-12345",
        physical_location="NOC Principal",
        online_since_date=date(2026, 1, 1),
    )

    db = AsyncMock()
    db.execute.return_value = MockDbResult([mock_router])

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # Default CORPORATE
    mock_redis.smembers.return_value = {b"CIS-1.1", b"CIS-1.2", b"CIS-CORP-1"}

    with (
        patch("src.api.v1.compliance.get_redis_client", return_value=mock_redis),
        patch("src.api.v1.compliance.get_router_and_client", side_effect=Exception("Offline Router Mock")),
    ):
        audit_res = await run_cis_audit(router_id=router_id, db=db, claims=sample_claims)

        assert audit_res.router_id == router_id
        assert audit_res.total_directives > 0
        assert len(audit_res.directives) == 28
        assert 0 <= audit_res.security_score <= 100

        # Verificar directivas deshabilitadas para CORPORATE
        disabled_dirs = [d for d in audit_res.directives if d.enabled is False]
        assert len(disabled_dirs) > 0
        for d in disabled_dirs:
            assert "desactivada" in d.finding.lower()
            assert d.passed is False


def test_starter_templates_catalog_and_syslog() -> None:
    """Certifica la presencia y validez de las 10 nuevas plantillas masivas avanzadas y la plantilla de Syslog."""
    template_names = {t["name"] for t in _DEFAULT_STARTER_TEMPLATES}

    # 1. Verificar plantilla de Syslog centralizado
    assert "SYSLOG_CENTRALIZADO_ROSGRID" in template_names
    syslog_tpl = next(t for t in _DEFAULT_STARTER_TEMPLATES if t["name"] == "SYSLOG_CENTRALIZADO_ROSGRID")
    syslog_cli = syslog_tpl["ros_command_template"]
    assert "topics=system,info" in syslog_cli
    assert "topics=account" in syslog_cli
    assert "topics=firewall,info" in syslog_cli

    # 2. Verificar las 10 nuevas plantillas masivas
    advanced_templates = [
        "ISP_BGP_RPKI_STRICT_VALIDATION",
        "ISP_CGNAT_DETERMINISTIC_OVERLOAD",
        "ISP_IPV6_DUAL_STACK_PD",
        "COPP_CONTROL_PLANE_PROTECTION",
        "BCP38_ANTI_SPOOFING_FILTER",
        "TCP_MSS_CLAMPING_OPTIMIZER",
        "ENTERPRISE_BRIDGE_VLAN_TRUNK_ACCESS",
        "QOS_CAKE_SMART_QUEUE",
        "SDWAN_WIREGUARD_SITE_TO_SITE",
        "NIGHTLY_ENCRYPTED_BACKUP_SFTP",
    ]

    for name in advanced_templates:
        assert name in template_names, f"Falta plantilla masiva avanzada: {name}"
        tpl = next(t for t in _DEFAULT_STARTER_TEMPLATES if t["name"] == name)
        assert tpl.get("category"), f"Plantilla {name} carece de categoría"
        assert tpl.get("description"), f"Plantilla {name} carece de descripción"
        assert tpl.get("variables_schema"), f"Plantilla {name} carece de variables_schema"
        assert tpl.get("rest_steps_template"), f"Plantilla {name} carece de rest_steps_template"
        assert tpl.get("requires_safemode") is True, f"Plantilla {name} debe exigir Safe Mode"
