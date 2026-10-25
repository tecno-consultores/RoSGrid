# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para gestión de políticas CIS personalizables y Onboarding de Tenant Feature Flags."""

import json
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request

from src.api.v1.compliance import (
    auto_harden_router,
    get_cis_policies,
    run_cis_audit,
    update_cis_policies,
)
from src.api.v1.tenants import (
    complete_tenant_onboarding,
    get_tenant_features,
    update_tenant_features,
)
from src.models.inventory import Router, RouterNetworkRoleEnum
from src.schemas.enterprise import (
    CisAutoHardenRequest,
    CisPoliciesConfigRequest,
    CisPolicyRule,
)
from src.schemas.tenants import UpdateTenantFeaturesRequest


class MockDbResult:
    """Mock síncrono para resultados de SQLAlchemy."""

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
        "username": "admin_test",
        "rol": "TENANT_ADMIN",
    }


@pytest.fixture
def mock_request() -> MagicMock:
    req = MagicMock(spec=Request)
    req.client.host = "192.168.10.50"
    req.headers = {"user-agent": "RoSGrid-PyTest/1.0"}
    return req


@pytest.mark.asyncio
async def test_get_and_update_cis_policies(
    sample_tenant_id: uuid.UUID, sample_claims: dict[str, Any], mock_request: MagicMock
) -> None:
    """Certifica consulta y actualización de directivas CIS por tenant con registro WORM."""
    db = AsyncMock()
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # Inicializa con default

    with (
        patch("src.api.v1.compliance.get_redis_client", return_value=mock_redis),
        patch("src.api.v1.compliance.write_audit_log", AsyncMock()) as mock_audit,
    ):
        # 1. GET inicial: perfil CORPORATE
        policies = await get_cis_policies(claims=sample_claims)
        assert policies.tenant_id == sample_tenant_id
        assert policies.profile == "CORPORATE"
        assert len(policies.rules) >= 10

        # 2. PUT: actualizar a perfil ISP personalizando directivas
        custom_rules = [
            CisPolicyRule(
                code="CIS-1.1",
                title="Deshabilitar servicios inseguros",
                category="CONTROL_PLANE",
                weight=15,
                severity="HIGH",
                enabled=True,
                remediation_cmd="/ip service set telnet,ftp,www,api disabled=yes",
                profile_target="ALL",
            ),
            CisPolicyRule(
                code="CIS-2.1",
                title="BGP Prefix Limits & MD5",
                category="ROUTING_BGP",
                weight=10,
                severity="HIGH",
                enabled=True,
                remediation_cmd="/routing bgp connection set [find] tcp-md5-key=yes",
                profile_target="ISP",
            ),
            CisPolicyRule(
                code="CIS-2.2",
                title="Selective FastTrack QoS",
                category="PERFORMANCE",
                weight=10,
                severity="MEDIUM",
                enabled=True,
                remediation_cmd="/ip firewall filter add action=fasttrack-connection packet-mark=!qos-shaped",
                profile_target="ISP",
            ),
        ]
        update_req = CisPoliciesConfigRequest(profile="ISP", rules=custom_rules)
        res = await update_cis_policies(
            payload=update_req,
            request=mock_request,
            db=db,
            claims=sample_claims,
        )

        assert res.profile == "ISP"
        assert len(res.rules) == 3
        mock_redis.set.assert_called_once()
        mock_audit.assert_called_once()


@pytest.mark.asyncio
async def test_run_cis_audit_with_custom_tenant_policy(
    sample_tenant_id: uuid.UUID, sample_claims: dict[str, Any]
) -> None:
    """Verifica que el escaneo CIS pondera únicamente las directivas activas de la política del tenant."""
    db = AsyncMock()
    router_id = uuid.uuid4()
    mock_router = Router(
        id=router_id,
        tenant_id=sample_tenant_id,
        display_name="ISP-Border-CCR2004",
        network_role=RouterNetworkRoleEnum.EDGE_BGP,
        api_base_url="https://10.250.0.1:443",
    )
    db.execute.return_value = MockDbResult([mock_router])

    mock_client = AsyncMock()
    mock_client.get.return_value = []

    mock_redis = AsyncMock()
    # Mockear política en Redis con 2 directivas activas (peso total 25)
    custom_policy_doc = {
        "profile": "ISP",
        "updated_at": "2026-10-24T22:00:00Z",
        "rules": [
            {
                "code": "CIS-1.1",
                "title": "Deshabilitar servicios inseguros",
                "category": "CONTROL_PLANE",
                "weight": 15,
                "severity": "HIGH",
                "enabled": True,
                "remediation_cmd": "/ip service set telnet disabled=yes",
                "profile_target": "ALL",
            },
            {
                "code": "CIS-2.1",
                "title": "Seguridad BGP MD5",
                "category": "ROUTING_BGP",
                "weight": 10,
                "severity": "HIGH",
                "enabled": True,
                "remediation_cmd": "/routing bgp connection set [find] tcp-md5-key=yes",
                "profile_target": "ISP",
            },
            {
                "code": "CIS-1.10",
                "title": "VLAN 99 de gestión",
                "category": "SEGMENTATION",
                "weight": 7,
                "severity": "LOW",
                "enabled": False,  # Deshabilitada para ISP
                "remediation_cmd": "/interface vlan add name=vlan99-mgmt",
                "profile_target": "CORPORATE",
            },
        ],
    }
    mock_redis.get.return_value = json.dumps(custom_policy_doc).encode()
    mock_redis.smembers.return_value = {b"CIS-1.1", b"CIS-2.1"}  # Ambas directivas aplicadas

    with (
        patch("src.api.v1.compliance.get_redis_client", return_value=mock_redis),
        patch("src.api.v1.compliance.get_router_and_client", return_value=(mock_router, mock_client)),
    ):
        audit_res = await run_cis_audit(router_id=router_id, db=db, claims=sample_claims)
        # Solo las 2 habilitadas deben ser evaluadas
        assert audit_res.total_directives == 2
        assert audit_res.passed_directives == 2
        assert audit_res.failed_directives == 0
        assert audit_res.security_score == 100
        assert audit_res.compliance_grade == "A"


@pytest.mark.asyncio
async def test_tenant_onboarding_lifecycle(
    sample_tenant_id: uuid.UUID, sample_claims: dict[str, Any]
) -> None:
    """Verifica persistencia y lectura de onboarding_completed en KeyDB y actualización de flags."""
    db = AsyncMock()
    mock_redis = AsyncMock()
    from src.models.core import Tenant, TenantStatusEnum

    mock_tenant = Tenant(
        id=sample_tenant_id,
        slug="test-isp",
        name="Test ISP Enterprise",
        status=TenantStatusEnum.ACTIVE,
        tax_id="J-12345678-9",
    )
    db.execute.return_value = MockDbResult([mock_tenant])

    # 1. Simular tenant nuevo sin onboarding completado
    mock_redis.get.return_value = None

    with patch("src.api.v1.tenants.get_redis_client", return_value=mock_redis):
        features = await get_tenant_features(tenant_id=sample_tenant_id, db=db, claims=sample_claims)
        assert features.onboarding_completed is False

        # 2. Completar onboarding explícito
        complete_res = await complete_tenant_onboarding(
            tenant_id=sample_tenant_id, db=db, claims=sample_claims
        )
        assert complete_res.onboarding_completed is True
        mock_redis.set.assert_called_with(f"rg:{sample_tenant_id}:onboarding_completed", "true")

        # 3. Actualizar feature flags con onboarding completado
        update_req = UpdateTenantFeaturesRequest(
            isp_module_enabled=True,
            bgp_looking_glass_enabled=True,
            onboarding_completed=True,
        )
        updated = await update_tenant_features(
            tenant_id=sample_tenant_id,
            body=update_req,
            request=mock_request,
            db=db,
            claims=sample_claims,
        )
        assert updated.isp_module_enabled is True
        assert updated.bgp_looking_glass_enabled is True
        assert updated.onboarding_completed is True
