# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para conmutación rápida de tenants por Super Administrador Global (Hito 25)."""

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from src.api.v1.auth import switch_tenant
from src.models.core import SystemRoleEnum, Tenant, TenantStatusEnum, User
from src.schemas.auth import SwitchTenantRequest


class MockDbResult:
    """Mock síncrono para resultados de SQLAlchemy."""

    def __init__(self, item: Any = None) -> None:
        self._item = item

    def scalar_one_or_none(self) -> Any:
        return self._item


@pytest.fixture
def superadmin_user() -> User:
    u = User(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        username="superadmin",
        email="superadmin@rosgrid.local",
        full_name="SuperAdmin Global",
        role=SystemRoleEnum.SUPERADMIN_GLOBAL,
        is_active=True,
        is_locked=False,
        has_all_routers_access=True,
    )
    return u


@pytest.fixture
def target_tenant() -> Tenant:
    t = Tenant(
        id=uuid.uuid4(),
        name="ISP Destino",
        slug="isp-destino",
        status=TenantStatusEnum.ACTIVE,
    )
    t.features = {"isp_module_enabled": True, "l2_topology_enabled": True}
    return t


@pytest.fixture
def superadmin_claims(superadmin_user: User) -> dict[str, Any]:
    return {
        "sub": str(superadmin_user.id),
        "tid": str(superadmin_user.tenant_id),
        "tslug": "tenant-origen",
        "sid": "old_session_12345",
        "rol": SystemRoleEnum.SUPERADMIN_GLOBAL.value,
        "all_r": True,
    }


@pytest.fixture
def mock_request() -> Request:
    req = MagicMock(spec=Request)
    req.client = MagicMock(host="127.0.0.1")
    req.headers = {"User-Agent": "Pytest-RoSGrid"}
    req.url = MagicMock(scheme="http")
    return req


@pytest.mark.asyncio
async def test_switch_tenant_forbidden_for_non_superadmin(mock_request: Request) -> None:
    """Verifica que roles diferentes a SUPERADMIN_GLOBAL son rechazados con HTTP 403."""
    claims = {
        "sub": str(uuid.uuid4()),
        "tid": str(uuid.uuid4()),
        "tslug": "tenant-1",
        "sid": "sess_1",
        "rol": SystemRoleEnum.TENANT_ADMIN.value,
    }
    db = AsyncMock()
    body = SwitchTenantRequest(target_tenant_slug="otro-tenant")
    response = Response()

    with pytest.raises(HTTPException) as exc_info:
        await switch_tenant(body=body, request=mock_request, response=response, claims=claims, db=db)

    assert exc_info.value.status_code == 403
    assert "Super Administrador Global" in exc_info.value.detail


@pytest.mark.asyncio
async def test_switch_tenant_not_found(
    mock_request: Request,
    superadmin_claims: dict[str, Any],
) -> None:
    """Verifica que si el tenant destino no existe se devuelve HTTP 404."""
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=None)
    body = SwitchTenantRequest(target_tenant_id=uuid.uuid4())
    response = Response()

    with pytest.raises(HTTPException) as exc_info:
        await switch_tenant(
            body=body,
            request=mock_request,
            response=response,
            claims=superadmin_claims,
            db=db,
        )

    assert exc_info.value.status_code == 404
    assert "no existe" in exc_info.value.detail


@pytest.mark.asyncio
async def test_switch_tenant_inactive(
    mock_request: Request,
    superadmin_claims: dict[str, Any],
    target_tenant: Tenant,
) -> None:
    """Verifica que si el tenant destino está suspendido/inactivo se devuelve HTTP 400."""
    target_tenant.status = TenantStatusEnum.SUSPENDED
    db = AsyncMock()
    db.scalar = AsyncMock(return_value=target_tenant)
    body = SwitchTenantRequest(target_tenant_id=target_tenant.id)
    response = Response()

    with pytest.raises(HTTPException) as exc_info:
        await switch_tenant(
            body=body,
            request=mock_request,
            response=response,
            claims=superadmin_claims,
            db=db,
        )

    assert exc_info.value.status_code == 400
    assert "no se encuentra activo" in exc_info.value.detail


@pytest.mark.asyncio
async def test_switch_tenant_success_by_id(
    mock_request: Request,
    superadmin_claims: dict[str, Any],
    superadmin_user: User,
    target_tenant: Tenant,
) -> None:
    """Verifica la conmutación exitosa por target_tenant_id."""
    db = AsyncMock()
    # Primera llamada a db.scalar devuelve target_tenant, segunda devuelve superadmin_user
    db.scalar = AsyncMock(side_effect=[target_tenant, superadmin_user])
    response = Response()
    body = SwitchTenantRequest(target_tenant_id=target_tenant.id)

    with (
        patch("src.api.v1.auth.kill_session", new_callable=AsyncMock) as mock_kill,
        patch("src.api.v1.auth.create_session", new_callable=AsyncMock) as mock_create_sess,
        patch("src.api.v1.auth.kill_all_user_sessions", new_callable=AsyncMock) as mock_kill_dup,
        patch("src.api.v1.auth.write_audit_log", new_callable=AsyncMock) as mock_audit,
    ):
        mock_kill.return_value = True
        mock_kill_dup.return_value = 0
        mock_create_sess.return_value = ("new_sess_abc", "fam_1", "rt_token_abc")

        res = await switch_tenant(
            body=body,
            request=mock_request,
            response=response,
            claims=superadmin_claims,
            db=db,
        )

        assert res.session_id == "new_sess_abc"
        assert res.user.tenant_id == target_tenant.id
        assert res.user.tenant_slug == "isp-destino"
        assert res.user.tenant_name == "ISP Destino"
        assert res.user.role == SystemRoleEnum.SUPERADMIN_GLOBAL
        assert res.user.features.get("isp_module_enabled") is True

        # Verificar que se revocó la sesión anterior
        mock_kill.assert_awaited_once_with(
            superadmin_claims["tid"],
            superadmin_claims["sid"],
            killed_by="SUPERADMIN_TENANT_SWITCH",
            reason="Conmutación al tenant isp-destino",
        )

        # Verificar auditoría
        assert mock_audit.await_count >= 1


@pytest.mark.asyncio
async def test_switch_tenant_success_by_slug(
    mock_request: Request,
    superadmin_claims: dict[str, Any],
    superadmin_user: User,
    target_tenant: Tenant,
) -> None:
    """Verifica la conmutación exitosa especificando target_tenant_slug."""
    db = AsyncMock()
    db.scalar = AsyncMock(side_effect=[target_tenant, superadmin_user])
    response = Response()
    body = SwitchTenantRequest(target_tenant_slug="isp-destino")

    with (
        patch("src.api.v1.auth.kill_session", new_callable=AsyncMock) as mock_kill,
        patch("src.api.v1.auth.create_session", new_callable=AsyncMock) as mock_create_sess,
        patch("src.api.v1.auth.kill_all_user_sessions", new_callable=AsyncMock) as mock_kill_dup,
        patch("src.api.v1.auth.write_audit_log", new_callable=AsyncMock),
    ):
        mock_kill.return_value = True
        mock_kill_dup.return_value = 0
        mock_create_sess.return_value = ("new_sess_xyz", "fam_2", "rt_token_xyz")

        res = await switch_tenant(
            body=body,
            request=mock_request,
            response=response,
            claims=superadmin_claims,
            db=db,
        )

        assert res.session_id == "new_sess_xyz"
        assert res.user.tenant_slug == "isp-destino"
