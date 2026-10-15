# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para Backups, Diffs, Maker-Checker, Actualizaciones Masivas, Auditoría y Notificaciones."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from src.api.v1.approvals import (
    _execute_approval_lifecycle,
    _verify_pending_and_not_expired,
)
from src.api.v1.audit import (
    _build_export_csv,
    _verify_single_audit_record,
)
from src.api.v1.backups import (
    _build_side_by_side_hunks,
    _compute_diff_stats,
    _decrypt_backup_rsc,
    _extract_raw_rsc_text,
    clean_rsc_export_comments,
)
from src.api.v1.bulk_and_updates import (
    _perform_pre_upgrade_backup,
    _render_template_steps,
    _resolve_target_router_ids,
)
from src.api.v1.notification_channels import (
    _decrypt_channel_config,
    _encrypt_channel_config,
)
from src.core.crypto import encrypt_aes_gcm
from src.models.core import SystemRoleEnum
from src.models.inventory import Router
from src.models.operations import (
    ApprovalRequest,
    ApprovalStatusEnum,
    RouterBackup,
)

# ============================================================================
# BACKUPS & DIFFS TESTS
# ============================================================================


def test_clean_rsc_export_comments() -> None:
    raw = """# oct/15/2026 12:00:00 by RouterOS 7.16.1
# software id = 1234
/interface ethernet
set ether1 comment="WAN"
"""
    cleaned = clean_rsc_export_comments(raw)
    assert "# oct/15/2026" not in cleaned
    assert 'set ether1 comment="WAN"' in cleaned


def test_extract_raw_rsc_text() -> None:
    assert _extract_raw_rsc_text("plain text") == "plain text"
    assert _extract_raw_rsc_text(["line 1", "line 2"]) == "line 1\nline 2"
    assert _extract_raw_rsc_text({"ret": "config text"}) == "config text"


def test_compute_diff_stats_and_hunks() -> None:
    base = ["/interface ethernet", "set ether1 comment=WAN", "set ether2 comment=LAN"]
    target = ["/interface ethernet", "set ether1 comment=WAN_NEW", "set ether3 comment=DMZ"]

    added, removed, diff_gen = _compute_diff_stats(base, target)
    assert added >= 1
    assert removed >= 1

    hunks = _build_side_by_side_hunks(diff_gen)
    types = [h.change_type for h in hunks]
    assert "ADDED" in types or "REMOVED" in types


def test_decrypt_backup_rsc() -> None:
    tenant_id = uuid.uuid4()
    router_id = uuid.uuid4()
    aad = f"{tenant_id}:{router_id}".encode()
    ct, iv, tag = encrypt_aes_gcm(b"/system identity set name=MyRouter", aad)

    b = RouterBackup(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        router_id=router_id,
        rsc_ciphertext=ct,
        rsc_iv=iv,
        rsc_tag=tag,
    )
    decrypted = _decrypt_backup_rsc(b, tenant_id)
    assert decrypted == "/system identity set name=MyRouter"


# ============================================================================
# MAKER-CHECKER TESTS
# ============================================================================


def test_verify_pending_and_not_expired() -> None:
    now = datetime.now(UTC)
    valid_req = ApprovalRequest(
        status=ApprovalStatusEnum.PENDING,
        expires_at=now + timedelta(hours=1),
    )
    _verify_pending_and_not_expired(valid_req)

    # Not pending
    already_approved = ApprovalRequest(
        status=ApprovalStatusEnum.APPROVED_AND_EXECUTED,
        expires_at=now + timedelta(hours=1),
    )
    with pytest.raises(HTTPException) as exc1:
        _verify_pending_and_not_expired(already_approved)
    assert exc1.value.status_code == 409

    # Expired
    expired_req = ApprovalRequest(
        status=ApprovalStatusEnum.PENDING,
        expires_at=now - timedelta(seconds=10),
    )
    with pytest.raises(HTTPException) as exc2:
        _verify_pending_and_not_expired(expired_req)
    assert exc2.value.status_code == 410
    assert expired_req.status == ApprovalStatusEnum.EXPIRED


@pytest.mark.asyncio
async def test_execute_approval_lifecycle_success_and_failure() -> None:
    client = AsyncMock()
    now_utc = datetime.now(UTC)

    req = ApprovalRequest(
        id=uuid.uuid4(),
        ros_rest_method="PATCH",
        ros_rest_path="/ip/firewall/filter/*1",
        request_payload={"disabled": True},
        status=ApprovalStatusEnum.PENDING,
    )

    with patch("src.api.v1.approvals._execute_deferred_operation", return_value={"ret": "ok"}):
        action, code = await _execute_approval_lifecycle(client, req, now_utc)
        assert action == "MAKER_CHECKER_APPROVED_AND_EXECUTED"
        assert code == 200
        assert req.status == ApprovalStatusEnum.APPROVED_AND_EXECUTED

    # Failure case
    with patch("src.api.v1.approvals._execute_deferred_operation", side_effect=Exception("MikroTik Error")):
        action_fail, code_fail = await _execute_approval_lifecycle(client, req, now_utc)
        assert action_fail == "MAKER_CHECKER_EXECUTION_FAILED"
        assert code_fail == 500
        assert req.status == ApprovalStatusEnum.APPROVED_EXECUTION_FAILED


# ============================================================================
# BULK & UPDATES TESTS
# ============================================================================


def test_render_template_steps() -> None:
    steps = [{"path": "/interface", "data": {"comment": "{{ comment_val }}"}}]
    rendered = _render_template_steps(steps, {"comment_val": "RenderedComment"})
    assert rendered[0]["data"]["comment"] == "RenderedComment"


@pytest.mark.asyncio
async def test_resolve_target_router_ids() -> None:
    from src.schemas.bulk_and_updates import BulkJobCreateRequest

    db = AsyncMock()
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()

    req = BulkJobCreateRequest(
        title="Test Job",
        description="Test Desc",
        steps=[],
        target_router_ids=[str(r_id)],
    )
    res = await _resolve_target_router_ids(db, t_id, req)
    assert res == [r_id]


@pytest.mark.asyncio
async def test_perform_pre_upgrade_backup() -> None:
    db = AsyncMock()
    client = AsyncMock()
    client.post.return_value = "/interface ethernet set ether1 comment=test"

    r = Router(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        display_name="Router-To-Upgrade",
    )

    b_id = await _perform_pre_upgrade_backup(db, r, client, uuid.uuid4())
    assert b_id is not None
    db.add.assert_called_once()


# ============================================================================
# AUDIT TESTS
# ============================================================================


def test_build_export_csv() -> None:
    from src.models.core import AuditLog

    now = datetime.now(UTC)
    log = AuditLog(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        actor_username="admin",
        actor_role=SystemRoleEnum.TENANT_ADMIN,
        actor_ip="192.168.1.100",
        event_category="INVENTORY",
        event_action="ROUTER_CREATED",
        router_display_name="Core-01",
        status_code=201,
        record_sha256_hash="hash123",
        created_at=now,
    )
    csv_str = _build_export_csv([log])
    assert "ROUTER_CREATED" in csv_str
    assert "Core-01" in csv_str
    assert "hash123" in csv_str


def test_verify_single_audit_hash() -> None:
    from src.core.audit import compute_audit_record_hash
    from src.models.core import AuditLog

    prev_hash = "0" * 64
    payload: dict[str, Any] = {
        "timestamp_utc": "2026-10-15T12:00:00+00:00",
        "actor_user_id": None,
        "actor_username": "admin",
        "event_category": "INVENTORY",
        "event_action": "ROUTER_CREATED",
        "router_id": None,
        "status_code": 201,
        "before_state": None,
        "after_state": {"name": "R1"},
    }
    rec_hash = compute_audit_record_hash(prev_hash, payload)

    log = AuditLog(
        actor_username="admin",
        event_category="INVENTORY",
        event_action="ROUTER_CREATED",
        status_code=201,
        before_state=None,
        after_state={"name": "R1"},
        record_sha256_hash=rec_hash,
    )
    log.prev_record_hash = prev_hash
    with patch("src.api.v1.audit.compute_audit_record_hash", return_value=rec_hash):
        assert _verify_single_audit_record(log, prev_hash) is True
        assert _verify_single_audit_record(log, "different_prev") is False


# ============================================================================
# NOTIFICATION CHANNELS VALIDATION
# ============================================================================


def test_channel_config_encryption_and_decryption() -> None:
    from src.models.operations import NotificationChannel

    tenant_id = uuid.uuid4()
    ch_id = uuid.uuid4()
    config = {"bot_token": "123:ABC", "chat_id": "456"}

    ct, iv, tag = _encrypt_channel_config(tenant_id, ch_id, config)
    ch = NotificationChannel(
        id=ch_id,
        tenant_id=tenant_id,
        config_ciphertext=ct,
        config_iv=iv,
        config_tag=tag,
    )
    decrypted = _decrypt_channel_config(tenant_id, ch)
    assert decrypted == config
