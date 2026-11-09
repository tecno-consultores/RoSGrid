# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.api.deps import get_current_user_claims
from src.api.v1.mcp import _extract_client_ip, _is_trusted_proxy_peer
from src.core.audit import GENESIS_AUDIT_HASH, write_audit_log
from src.core.config import Settings
from src.db.session import _reapply_rls_context_after_begin
from src.redis_layer.idempotency import check_idempotency_state
from src.schemas.inventory import _verify_host_ssrf
from src.services.network_events import is_safe_outbound_service_url
from src.workers.alert_dispatcher_worker import is_safe_webhook_url


def test_production_secrets_fail_fast_validation() -> None:
    """Valida que Settings falle al arrancar en producción si usa secretos por defecto o débiles."""
    with pytest.raises(ValueError, match="ROSGRID_MASTER_VAULT_KEY"):
        Settings(
            ROSGRID_ENV="production",
            ROSGRID_MASTER_VAULT_KEY="MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=",
            ROSGRID_JWT_SECRET_KEY="a" * 40,
            ROSGRID_CSRF_HMAC_SECRET="b" * 40,
        )

    with pytest.raises(ValueError, match="ROSGRID_JWT_SECRET_KEY"):
        Settings(
            ROSGRID_ENV="production",
            ROSGRID_MASTER_VAULT_KEY="1a2b3c4d" * 8,
            ROSGRID_JWT_SECRET_KEY="qa_jwt_secret_key_for_ephemeral_testing_only",
            ROSGRID_CSRF_HMAC_SECRET="b" * 40,
        )

    with pytest.raises(ValueError, match="ROSGRID_CSRF_HMAC_SECRET"):
        Settings(
            ROSGRID_ENV="production",
            ROSGRID_MASTER_VAULT_KEY="1a2b3c4d" * 8,
            ROSGRID_JWT_SECRET_KEY="a" * 40,
            ROSGRID_CSRF_HMAC_SECRET="short",
        )

    valid = Settings(
        ROSGRID_ENV="production",
        ROSGRID_MASTER_VAULT_KEY="1a2b3c4d" * 8,
        ROSGRID_JWT_SECRET_KEY="a" * 40,
        ROSGRID_CSRF_HMAC_SECRET="b" * 40,
    )
    assert valid.ROSGRID_ENV == "production"


def test_rls_after_begin_listener_reapplies_tenant_and_superadmin_context() -> None:
    """Verifica que el listener after_begin reaplique el contexto RLS en transacciones subsecuentes."""
    mock_session = MagicMock()
    mock_session.info = {
        "rls_initialized": True,
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "is_superadmin": "true",
    }
    mock_conn = MagicMock()
    _reapply_rls_context_after_begin(mock_session, MagicMock(), mock_conn)
    assert mock_conn.execute.call_count == 1


@pytest.mark.asyncio
async def test_service_account_mcp_only_scope_blocked_outside_mcp() -> None:
    """Verifica que un token SERVICE_ACCOUNT o mcp_only sea rechazado fuera de /api/v1/mcp."""
    import jwt

    from src.core.config import settings

    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "tid": str(uuid.uuid4()),
            "tslug": "acme",
            "sid": "mcp-sid-1",
            "rol": "SERVICE_ACCOUNT",
            "scope": "mcp_only",
        },
        settings.ROSGRID_JWT_SECRET_KEY,
        algorithm="HS256",
    )
    mock_req = MagicMock()
    mock_req.cookies = {}
    mock_req.headers = {"Authorization": f"Bearer {token}"}
    mock_req.url.path = "/api/v1/routers"

    with pytest.raises(HTTPException) as exc:
        await get_current_user_claims(mock_req)
    assert exc.value.status_code == 403

    mock_req.url.path = "/api/v1/mcp"
    fake_redis = MagicMock()
    fake_redis.exists = AsyncMock(return_value=1)
    with (
        patch("src.api.deps.get_redis_client", return_value=fake_redis),
        patch("src.api.deps.cancel_session_closing", new=AsyncMock()),
    ):
        claims = await get_current_user_claims(mock_req)
    assert claims["rol"] == "SERVICE_ACCOUNT"


def test_trusted_proxy_peer_and_ssrf_helpers() -> None:
    """Verifica validación de proxy confiable y bloqueos SSRF de dominios wildcard y DNS."""
    assert _is_trusted_proxy_peer("127.0.0.1") is True
    assert _is_trusted_proxy_peer("8.8.8.8") is False

    req = MagicMock()
    req.client.host = "8.8.8.8"
    req.headers = {"X-Forwarded-For": "10.0.0.1"}
    assert _extract_client_ip(req) == "8.8.8.8"

    with pytest.raises(ValueError, match="infraestructura interna"):
        _verify_host_ssrf("127.0.0.1.nip.io")
    with pytest.raises(ValueError, match="infraestructura interna"):
        _verify_host_ssrf("rosgrid_keydb")

    with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 0))]):
        with pytest.raises(ValueError, match="loopback"):
            _verify_host_ssrf("evil.example.com", resolve_dns=True)

    assert is_safe_webhook_url("https://127.0.0.1.nip.io/hook") is False
    assert is_safe_outbound_service_url("https://rosgrid_postgres/hook") is False
    assert is_safe_outbound_service_url("https://169.254.169.254/latest") is False


@pytest.mark.asyncio
async def test_idempotency_check_detects_in_flight_lock_and_audit_chain_in_tx() -> None:
    """Verifica que check_idempotency_state detecte lock en vuelo y write_audit_log encadene en transacción."""
    redis = AsyncMock()
    redis.hgetall = AsyncMock(return_value={})
    redis.setnx = AsyncMock(return_value=False)
    resp, should_proceed = await check_idempotency_state(redis, "rg:t1:idemp:k1", "reqhash-1")
    assert should_proceed is False
    assert resp is not None and resp.status_code == 409

    session = MagicMock()
    res_mock = MagicMock()
    res_mock.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=res_mock)
    session.get = AsyncMock(return_value=None)

    tid = uuid.uuid4()
    entry1 = await write_audit_log(
        session=session,
        tenant_id=tid,
        actor_username="admin",
        actor_role="TENANT_ADMIN",
        actor_ip="127.0.0.1",
        event_category="TEST",
        event_action="ACT_1",
    )
    entry2 = await write_audit_log(
        session=session,
        tenant_id=tid,
        actor_username="admin",
        actor_role="TENANT_ADMIN",
        actor_ip="127.0.0.1",
        event_category="TEST",
        event_action="ACT_2",
    )
    assert entry1.prev_record_hash == GENESIS_AUDIT_HASH
    assert entry2.prev_record_hash == entry1.record_sha256_hash
    session.add.assert_called()
    assert session.execute.call_args is not None

