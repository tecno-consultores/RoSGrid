# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Suite Completa de Pruebas Unitarias para Endpoints de Operaciones (Approvals, Backups, Bulk & Updates, Audit, Notification Channels)."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

import src.api.v1.approvals as api_approvals
import src.api.v1.audit as api_audit
import src.api.v1.backups as api_backups
import src.api.v1.bulk_and_updates as api_bulk
import src.api.v1.notification_channels as api_channels
from src.core.audit import GENESIS_AUDIT_HASH, compute_audit_record_hash
from src.core.crypto import encrypt_aes_gcm
from src.models.core import SystemRoleEnum
from src.models.inventory import Router
from src.models.operations import (
    AlertChannelTypeEnum,
    ApprovalRequest,
    ApprovalStatusEnum,
    AuditLog,
    BulkJob,
    BulkJobStatusEnum,
    ConfigTemplate,
    CriticalActionTypeEnum,
    NotificationChannel,
    RouterBackup,
)
from src.schemas.approvals import ApproveRequestPayload, RejectRequestPayload
from src.schemas.bulk_and_updates import (
    BulkJobCreateRequest,
    ConfigTemplateCreateRequest,
    RosUpdateExecuteRequest,
    TemplateRenderPreviewRequest,
)
from src.schemas.notifications import (
    NotificationChannelCreateRequest,
    NotificationChannelUpdateRequest,
    NotificationTestRequest,
)


@pytest.fixture
def fake_op_context() -> dict[str, Any]:
    t_id = uuid.uuid4()
    u_id = uuid.uuid4()
    r_id = uuid.uuid4()
    claims = {
        "tid": str(t_id),
        "sub": str(u_id),
        "rol": SystemRoleEnum.TENANT_ADMIN.value,
        "preferred_username": "admin_test",
    }
    router_obj = Router(
        id=r_id,
        tenant_id=t_id,
        display_name="Edge-OP-Test",
        api_base_url="https://10.0.0.1:443",
        ros_version="7.16",
    )
    client = AsyncMock()
    client.get.return_value = {"ret": "ok"}
    client.post.return_value = {"ret": "ok"}
    client.put.return_value = {"ret": "ok"}
    client.patch.return_value = {"ret": "ok"}
    client.delete.return_value = {}
    client.close = AsyncMock()
    db = AsyncMock()

    async def fake_refresh(instance: Any) -> None:
        if getattr(instance, "id", None) is None:
            instance.id = uuid.uuid4()
        if getattr(instance, "created_at", None) is None:
            instance.created_at = datetime.now(UTC)
        if getattr(instance, "updated_at", None) is None:
            instance.updated_at = datetime.now(UTC)

    db.refresh.side_effect = fake_refresh

    return {
        "tenant_id": t_id,
        "user_id": u_id,
        "router_id": r_id,
        "claims": claims,
        "router": router_obj,
        "client": client,
        "db": db,
    }


# ============================================================================
# APPROVALS UNIT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_approvals_helpers_and_list(fake_op_context: dict[str, Any]) -> None:
    ctx = fake_op_context
    claims = ctx["claims"]
    db = ctx["db"]

    # _filter_approvals_by_role
    dummy_stmt = MagicMock()
    filtered = api_approvals._filter_approvals_by_role(claims, dummy_stmt)
    assert filtered is dummy_stmt

    op_claims = dict(claims)
    op_claims["rol"] = SystemRoleEnum.SUPPORT_L1.value
    filtered_l1 = api_approvals._filter_approvals_by_role(op_claims, dummy_stmt)
    dummy_stmt.where.assert_called_once()
    assert filtered_l1 is not None

    now_utc = datetime.now(UTC)
    # _verify_pending_and_not_expired
    app = ApprovalRequest(
        id=uuid.uuid4(),
        tenant_id=ctx["tenant_id"],
        action_type=CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE,
        status=ApprovalStatusEnum.REJECTED,
        summary="Test",
        requester_justification="Test",
        ros_rest_method="PUT",
        ros_rest_path="/ip/firewall/filter",
        request_payload={"chain": "input"},
        requested_by=ctx["user_id"],
        created_at=now_utc,
        expires_at=now_utc + timedelta(hours=1),
    )
    with pytest.raises(HTTPException) as exc_info:
        api_approvals._verify_pending_and_not_expired(app)
    assert exc_info.value.status_code == 400

    app.status = ApprovalStatusEnum.PENDING
    app.expires_at = now_utc - timedelta(hours=1)
    with pytest.raises(HTTPException):
        api_approvals._verify_pending_and_not_expired(app)
    assert app.status == ApprovalStatusEnum.EXPIRED

    # list_approvals
    app.expires_at = now_utc + timedelta(hours=1)
    app.status = ApprovalStatusEnum.PENDING
    mock_count_res = MagicMock()
    mock_count_res.scalar.return_value = 1
    mock_list_res = MagicMock()
    mock_list_res.scalars.return_value.all.return_value = [app]
    db.execute.side_effect = [mock_count_res, mock_list_res]

    res = await api_approvals.list_approvals(
        status_filter=ApprovalStatusEnum.PENDING, limit=10, offset=0, claims=claims, db=db
    )
    assert res.total == 1
    assert len(res.items) == 1

    # Test _execute_deferred_operation for PATCH, DELETE, POST, and unsupported
    async def fake_mut(client: Any, menu: Any, action: Any, coro_fn: Any, **kwargs: Any) -> Any:
        return await coro_fn()

    client_mock = AsyncMock()
    app_put = ApprovalRequest(
        ros_rest_method="PUT",
        ros_rest_path="/ip/address",
        request_payload={"address": "1.1.1.1/32"},
    )
    with patch("src.api.v1.approvals.execute_safe_mutation", side_effect=fake_mut):
        await api_approvals._execute_deferred_operation(client_mock, app_put)
        client_mock.put.assert_called_once()

    app_patch = ApprovalRequest(
        ros_rest_method="PATCH",
        ros_rest_path="/ip/dns",
        request_payload={"servers": "1.1.1.1"},
    )
    with patch("src.api.v1.approvals.execute_safe_mutation", side_effect=fake_mut):
        await api_approvals._execute_deferred_operation(client_mock, app_patch)
        client_mock.patch.assert_called_once()

    app_del = ApprovalRequest(
        ros_rest_method="DELETE",
        ros_rest_path="/ip/address/*1",
        request_payload={},
    )
    with patch("src.api.v1.approvals.execute_safe_mutation", side_effect=fake_mut):
        await api_approvals._execute_deferred_operation(client_mock, app_del)
        client_mock.delete.assert_called_once()

    app_post = ApprovalRequest(
        ros_rest_method="POST",
        ros_rest_path="/system/reboot",
        request_payload={},
    )
    with patch("src.api.v1.approvals.execute_safe_mutation", side_effect=fake_mut):
        await api_approvals._execute_deferred_operation(client_mock, app_post)
        client_mock.post.assert_called_once()

    app_invalid = ApprovalRequest(
        ros_rest_method="HEAD",
        ros_rest_path="/test",
        request_payload={},
    )
    with patch("src.api.v1.approvals.execute_safe_mutation", side_effect=fake_mut):
        with pytest.raises(ValueError):
            await api_approvals._execute_deferred_operation(client_mock, app_invalid)


@pytest.mark.asyncio
async def test_approvals_approve_and_reject(fake_op_context: dict[str, Any]) -> None:
    ctx = fake_op_context
    claims = ctx["claims"]
    db = ctx["db"]
    fake_req = MagicMock()
    fake_req.client.host = "127.0.0.1"

    now_utc = datetime.now(UTC)
    app = ApprovalRequest(
        id=uuid.uuid4(),
        tenant_id=ctx["tenant_id"],
        router_id=ctx["router_id"],
        action_type=CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE,
        status=ApprovalStatusEnum.PENDING,
        summary="Test rule",
        requester_justification="Required",
        ros_rest_method="PUT",
        ros_rest_path="ip/firewall/filter",
        request_payload={"chain": "input"},
        requested_by=uuid.uuid4(),  # Different from checker
        created_at=now_utc,
        expires_at=now_utc + timedelta(hours=1),
    )
    db.get.return_value = app

    with (
        patch("src.api.v1.approvals.get_router_and_client", return_value=(ctx["router"], ctx["client"])),
        patch("src.api.v1.approvals.execute_safe_mutation", return_value={"ret": "*1"}),
        patch("src.api.v1.approvals.write_audit_log", new_callable=AsyncMock),
    ):
        approve_payload = ApproveRequestPayload(review_comment="Approved for maintenance")
        app_res = await api_approvals.approve_request(app.id, approve_payload, fake_req, claims=claims, db=db)
        assert app_res.status == ApprovalStatusEnum.APPROVED_AND_EXECUTED.value

        # Test SoD violation (checker == requester)
        app.status = ApprovalStatusEnum.PENDING
        app.requested_by = ctx["user_id"]
        with pytest.raises(HTTPException) as exc_info:
            await api_approvals.approve_request(app.id, approve_payload, fake_req, claims=claims, db=db)
        assert exc_info.value.status_code == 403

        # Test reject_request
        app.requested_by = uuid.uuid4()
        reject_payload = RejectRequestPayload(review_comment="Not justified")
        rej_res = await api_approvals.reject_request(app.id, reject_payload, fake_req, claims=claims, db=db)
        assert rej_res.status == ApprovalStatusEnum.REJECTED.value

        # Approve not found -> 404
        db.get.return_value = None
        with pytest.raises(HTTPException) as exc_nf:
            await api_approvals.approve_request(uuid.uuid4(), approve_payload, fake_req, claims=claims, db=db)
        assert exc_nf.value.status_code == 404

        # Reject not found -> 404
        with pytest.raises(HTTPException) as exc_rnf:
            await api_approvals.reject_request(uuid.uuid4(), reject_payload, fake_req, claims=claims, db=db)
        assert exc_rnf.value.status_code == 404

        # Reject when not pending -> 400
        app.status = ApprovalStatusEnum.REJECTED
        db.get.return_value = app
        with pytest.raises(HTTPException) as exc_np:
            await api_approvals.reject_request(app.id, reject_payload, fake_req, claims=claims, db=db)
        assert exc_np.value.status_code == 400


# ============================================================================
# BACKUPS UNIT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_backups_helpers_and_diff(fake_op_context: dict[str, Any]) -> None:
    ctx = fake_op_context
    claims = ctx["claims"]
    db = AsyncMock()

    # RSC comments cleaning
    raw_rsc = "# oct/15/2026 by RouterOS\n/ip address\nadd address=10.0.0.1/24\n"
    cleaned = api_backups.clean_rsc_export_comments(raw_rsc)
    assert "#" not in cleaned
    assert "/ip address" in cleaned

    assert api_backups._extract_raw_rsc_text("string_res") == "string_res"
    assert api_backups._extract_raw_rsc_text(["line1", "line2"]) == "line1\nline2"
    assert api_backups._extract_raw_rsc_text({"ret": "ok"}) == "ok"

    added, removed, diff_lines = api_backups._compute_diff_stats(["a", "b"], ["a", "c"])
    assert added == 1
    assert removed == 1
    hunks = api_backups._build_side_by_side_hunks(diff_lines)
    assert len(hunks) >= 1

    # list_backups
    b_id = uuid.uuid4()
    aad = f"{ctx['tenant_id']}:{ctx['router_id']}".encode()
    ct, iv, tag = encrypt_aes_gcm(cleaned.encode("utf-8"), aad)
    backup_obj = RouterBackup(
        id=b_id,
        tenant_id=ctx["tenant_id"],
        router_id=ctx["router_id"],
        backup_type="MANUAL_OPERATOR",
        ros_version_at_backup="7.16",
        rsc_sha256_hash="hash123",
        rsc_size_bytes=len(cleaned),
        rsc_ciphertext=ct,
        rsc_iv=iv,
        rsc_tag=tag,
        diff_lines_added=0,
        diff_lines_removed=0,
        created_at=datetime.now(UTC),
        last_verified_identical_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    mock_list = MagicMock()
    mock_list.scalars.return_value.all.return_value = [backup_obj]
    db.execute.return_value = mock_list

    b_list = await api_backups.list_backups(ctx["router_id"], claims=claims, db=db)
    assert len(b_list.items) == 1

    # get_backup_diff against LIVE
    db.get.return_value = backup_obj
    with patch("src.api.v1.backups.get_router_and_client", return_value=(ctx["router"], ctx["client"])):
        ctx["client"].post.return_value = "/ip address\nadd address=10.0.0.2/24"
        diff_res = await api_backups.get_backup_diff(
            ctx["router_id"], base_backup_id=b_id, target_backup_id="LIVE", claims=claims, db=db
        )
        assert diff_res.target_backup_id == "LIVE"
        assert diff_res.lines_added >= 1

    # Target backup by UUID
    target_b_id = uuid.uuid4()
    target_backup_obj = RouterBackup(
        id=target_b_id,
        tenant_id=ctx["tenant_id"],
        router_id=ctx["router_id"],
        backup_type="MANUAL_OPERATOR",
        ros_version_at_backup="7.16",
        rsc_sha256_hash="hash456",
        rsc_size_bytes=len(cleaned),
        rsc_ciphertext=ct,
        rsc_iv=iv,
        rsc_tag=tag,
        diff_lines_added=0,
        diff_lines_removed=0,
        created_at=datetime.now(UTC),
        last_verified_identical_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    db.get.side_effect = [backup_obj, target_backup_obj]
    diff_res_uuid = await api_backups.get_backup_diff(
        ctx["router_id"], base_backup_id=b_id, target_backup_id=str(target_b_id), claims=claims, db=db
    )
    assert diff_res_uuid.target_backup_id == str(target_b_id)

    # Invalid UUID
    db.get.side_effect = None
    db.get.return_value = backup_obj
    with pytest.raises(HTTPException) as exc_diff:
        await api_backups.get_backup_diff(
            ctx["router_id"], base_backup_id=b_id, target_backup_id="not-a-valid-uuid", claims=claims, db=db
        )
    assert exc_diff.value.status_code == 400

    # Base backup not found -> 404
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc_b404:
        await api_backups.get_backup_diff(
            ctx["router_id"], base_backup_id=uuid.uuid4(), target_backup_id="LIVE", claims=claims, db=db
        )
    assert exc_b404.value.status_code == 404

    # Target backup UUID not found -> 404
    db.get.side_effect = [backup_obj, None]
    with pytest.raises(HTTPException) as exc_t404:
        await api_backups.get_backup_diff(
            ctx["router_id"], base_backup_id=b_id, target_backup_id=str(uuid.uuid4()), claims=claims, db=db
        )
    assert exc_t404.value.status_code == 404


@pytest.mark.asyncio
async def test_backups_trigger_deduplication(fake_op_context: dict[str, Any]) -> None:
    ctx = fake_op_context
    claims = ctx["claims"]
    db = AsyncMock()
    fake_req = MagicMock()
    fake_req.client.host = "127.0.0.1"

    ctx["client"].post.return_value = "/ip address\nadd address=10.0.0.1/24"

    # 1. First trigger creates new backup
    mock_latest = MagicMock()
    mock_latest.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_latest

    with (
        patch("src.api.v1.backups.get_router_and_client", return_value=(ctx["router"], ctx["client"])),
        patch("src.api.v1.backups.write_audit_log", new_callable=AsyncMock),
    ):
        res_create = await api_backups.trigger_backup(ctx["router_id"], fake_req, claims=claims, db=db)
        assert res_create.status == "CREATED"

        # 2. Second trigger with identical content deduplicates
        existing_backup = RouterBackup(
            id=uuid.uuid4(),
            tenant_id=ctx["tenant_id"],
            router_id=ctx["router_id"],
            rsc_sha256_hash=res_create.rsc_sha256_hash,
            created_at=datetime.now(UTC),
        )
        mock_latest_dup = MagicMock()
        mock_latest_dup.scalar_one_or_none.return_value = existing_backup
        db.execute.return_value = mock_latest_dup

        res_dedup = await api_backups.trigger_backup(ctx["router_id"], fake_req, claims=claims, db=db)
        assert res_dedup.status == "IDENTICAL_SKIPPED_DEDUPLICATED"


# ============================================================================
# BULK OPERATIONS & UPDATES UNIT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_templates_and_jobs(fake_op_context: dict[str, Any]) -> None:
    ctx = fake_op_context
    claims = ctx["claims"]
    db = ctx["db"]

    # Template steps rendering
    steps = [{"method": "PUT", "path": "/ip/address", "data": {"address": "{{ ip_addr }}"}}]
    rendered = api_bulk._render_template_steps(steps, {"ip_addr": "10.10.10.1/24"})
    assert rendered[0]["data"]["address"] == "10.10.10.1/24"

    # Template CRUD
    t_id = uuid.uuid4()
    now_utc = datetime.now(UTC)
    tmpl = ConfigTemplate(
        id=t_id,
        tenant_id=ctx["tenant_id"],
        name="Base DNS",
        category="NETWORK",
        description="Base template",
        variables_schema=[{"name": "dns", "type": "string"}],
        rest_steps_template=[{"method": "PATCH", "path": "/ip/dns", "data": {"servers": "{{ dns }}"}}],
        requires_safemode=True,
        created_by=ctx["user_id"],
        created_at=now_utc,
        updated_at=now_utc,
    )
    mock_t_list = MagicMock()
    mock_t_list.scalars.return_value.all.return_value = [tmpl]
    mock_t_list.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_t_list

    t_list = await api_bulk.list_templates(claims=claims, db=db)
    assert len(t_list) == 1

    # Test presets endpoint
    presets = await api_bulk.list_template_presets(claims=claims)
    assert len(presets) >= 4
    ntp_preset = next(p for p in presets if p["name"] == "CLIENTE_NTP")
    assert ntp_preset["category"] == "SYSTEM"
    assert ntp_preset["description"] == "Activa el cliente NTP"
    assert len(ntp_preset["variables_schema"]) == 4
    assert len(ntp_preset["rest_steps_template"]) == 5
    assert ntp_preset["rest_steps_template"][0]["endpoint"] == "system/ntp/client"
    assert ntp_preset["rest_steps_template"][1]["endpoint"] == "system/ntp/client/servers"

    syslog_preset = next(p for p in presets if p["name"] == "SYSLOG_CENTRALIZADO_ROSGRID")
    assert syslog_preset["category"] == "SECURITY"
    assert "Syslog remoto" in syslog_preset["description"]
    assert len(syslog_preset["variables_schema"]) == 2
    assert syslog_preset["variables_schema"][0]["key"] == "rosgrid_server_ip"
    assert syslog_preset["variables_schema"][1]["key"] == "rosgrid_syslog_port"
    assert len(syslog_preset["rest_steps_template"]) == 7
    assert syslog_preset["rest_steps_template"][0]["endpoint"] == "system/logging/action"
    assert syslog_preset["rest_steps_template"][0]["method"] == "PUT"
    assert syslog_preset["rest_steps_template"][1]["endpoint"] == "system/logging"
    assert syslog_preset["rest_steps_template"][1]["method"] == "PUT"
    assert syslog_preset["requires_safemode"] is True

    # Test seed_default_templates
    seed_res = await api_bulk.seed_default_templates(claims=claims, db=db)
    assert len(seed_res) >= 1

    create_payload = ConfigTemplateCreateRequest(
        name="New Template",
        category="SECURITY",
        description="Security template",
        variables_schema=[],
        rest_steps_template=[{"method": "PUT", "path": "/ip/service"}],
        requires_safemode=False,
    )
    fake_req = MagicMock()
    fake_req.client.host = "127.0.0.1"
    fake_req.headers.get.return_value = "Pytest-Client"
    c_res = await api_bulk.create_template(create_payload, fake_req, claims=claims, db=db)
    assert c_res.name == "New Template"

    # Test update and delete template
    update_payload = api_bulk.ConfigTemplateUpdateRequest(description="Updated description")
    db.get.return_value = tmpl
    u_res = await api_bulk.update_template(t_id, update_payload, fake_req, claims=claims, db=db)
    assert u_res.description == "Updated description"

    await api_bulk.delete_template(t_id, fake_req, claims=claims, db=db)

    db.get.return_value = tmpl
    prev_res = await api_bulk.preview_template(
        t_id, TemplateRenderPreviewRequest(variables={"dns": "1.1.1.1"}), claims=claims, db=db
    )
    assert prev_res.rendered_steps[0]["data"]["servers"] == "1.1.1.1"

    # Bulk Jobs
    job_create = BulkJobCreateRequest(
        title="Deploy DNS",
        job_type="TEMPLATE_ROLLOUT",
        template_id=t_id,
        target_router_ids=[str(ctx["router_id"])],
        execution_parameters={"dns": "8.8.8.8"},
    )
    mock_job = BulkJob(
        id=uuid.uuid4(),
        tenant_id=ctx["tenant_id"],
        job_type="TEMPLATE_ROLLOUT",
        title="Deploy DNS",
        status=BulkJobStatusEnum.QUEUED,
        template_id=t_id,
        execution_parameters={"dns": "8.8.8.8"},
        target_router_ids=[str(ctx["router_id"])],
        total_routers=1,
        succeeded_count=0,
        failed_count=0,
        created_by=ctx["user_id"],
        created_at=datetime.now(UTC),
    )
    db.get.return_value = mock_job
    mock_items = MagicMock()
    mock_items.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_items

    job_detail = await api_bulk.create_bulk_job(job_create, claims=claims, db=db)
    assert job_detail.status == BulkJobStatusEnum.QUEUED.value

    # Test _resolve_target_router_ids by target_role
    req_role = BulkJobCreateRequest(
        title="Role job",
        job_type="TEMPLATE_ROLLOUT",
        template_id=t_id,
        target_role="EDGE_AGGREGATION",
        execution_parameters={},
    )
    mock_r_res = MagicMock()
    mock_r_res.scalars.return_value.all.return_value = [ctx["router_id"]]
    db.execute.return_value = mock_r_res
    r_ids = await api_bulk._resolve_target_router_ids(db, ctx["tenant_id"], req_role)
    assert r_ids == [ctx["router_id"]]

    # by target_tag
    req_tag = BulkJobCreateRequest(
        title="Tag job",
        job_type="TEMPLATE_ROLLOUT",
        template_id=t_id,
        target_tag="datacenter",
        execution_parameters={},
    )
    r_tag_ids = await api_bulk._resolve_target_router_ids(db, ctx["tenant_id"], req_tag)
    assert r_tag_ids == [ctx["router_id"]]

    # missing criteria raises 400
    req_none = BulkJobCreateRequest(
        title="None job",
        job_type="TEMPLATE_ROLLOUT",
        template_id=t_id,
        execution_parameters={},
    )
    with pytest.raises(HTTPException):
        await api_bulk._resolve_target_router_ids(db, ctx["tenant_id"], req_none)

    # L2 role creates job with AWAITING_APPROVAL status
    l2_claims = dict(claims)
    l2_claims["rol"] = SystemRoleEnum.SUPPORT_L2.value
    mock_l2_job = BulkJob(
        id=uuid.uuid4(),
        tenant_id=ctx["tenant_id"],
        job_type="TEMPLATE_ROLLOUT",
        title="Deploy DNS",
        status=BulkJobStatusEnum.AWAITING_APPROVAL,
        template_id=t_id,
        execution_parameters={"dns": "8.8.8.8"},
        target_router_ids=[str(ctx["router_id"])],
        total_routers=1,
        succeeded_count=0,
        failed_count=0,
        created_by=ctx["user_id"],
        created_at=datetime.now(UTC),
    )
    db.get.return_value = mock_l2_job
    mock_items_l2 = MagicMock()
    mock_items_l2.scalars.return_value.all.return_value = []
    db.execute.return_value = mock_items_l2
    job_l2 = await api_bulk.create_bulk_job(job_create, claims=l2_claims, db=db)
    assert job_l2.status == BulkJobStatusEnum.AWAITING_APPROVAL.value

    # preview_template 404
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc_p404:
        await api_bulk.preview_template(uuid.uuid4(), TemplateRenderPreviewRequest(variables={}), claims=claims, db=db)
    assert exc_p404.value.status_code == 404

    # create_bulk_job 400 when no target routers resolved
    with patch("src.api.v1.bulk_and_updates._resolve_target_router_ids", return_value=[]):
        with pytest.raises(HTTPException) as exc_no_r:
            await api_bulk.create_bulk_job(job_create, claims=claims, db=db)
        assert exc_no_r.value.status_code == 400

    # get_bulk_job 404
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc_j404:
        await api_bulk.get_bulk_job(uuid.uuid4(), claims=claims, db=db)
    assert exc_j404.value.status_code == 404

    # Fleet update status and execution
    mock_routers = MagicMock()
    mock_routers.scalars.return_value.all.return_value = [ctx["router"]]
    db.execute.return_value = mock_routers
    fleet_status = await api_bulk.get_fleet_updates_status(claims=claims, db=db)
    assert fleet_status.total_routers == 1

    with (
        patch("src.api.v1.bulk_and_updates.get_router_and_client", return_value=(ctx["router"], ctx["client"])),
        patch("src.api.v1.bulk_and_updates._perform_pre_upgrade_backup", return_value=True),
    ):
        exec_payload = RosUpdateExecuteRequest(router_ids=[ctx["router_id"]], auto_upgrade_firmware=True)
        up_res = await api_bulk.execute_fleet_updates(exec_payload, claims=claims, db=db)
        assert up_res.status == "COMPLETED"

    # Fleet updates: pre-backup fails -> ABORTED_PRE_BACKUP_FAILED
    with (
        patch("src.api.v1.bulk_and_updates.get_router_and_client", return_value=(ctx["router"], ctx["client"])),
        patch("src.api.v1.bulk_and_updates._perform_pre_upgrade_backup", return_value=False),
    ):
        exec_fail = await api_bulk.execute_fleet_updates(exec_payload, claims=claims, db=db)
        assert exec_fail.results[0]["status"] == "ABORTED_PRE_BACKUP_FAILED"

    # Fleet updates: exception -> FAILED
    with patch("src.api.v1.bulk_and_updates.get_router_and_client", side_effect=RuntimeError("MikroTik timeout")):
        exec_err = await api_bulk.execute_fleet_updates(exec_payload, claims=claims, db=db)
        assert exec_err.results[0]["status"] == "FAILED"


# ============================================================================
# AUDIT CONSOLE UNIT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_audit_filters_and_integrity(fake_op_context: dict[str, Any]) -> None:
    ctx = fake_op_context
    claims = ctx["claims"]
    db = AsyncMock()

    # Filter helpers
    stmt = MagicMock()
    stmt.where.return_value = stmt
    api_audit._apply_audit_filters(stmt, ctx["user_id"], ctx["router_id"], "SECURITY", "LOGIN")
    assert stmt.where.call_count == 4

    stmt_date = MagicMock()
    stmt_date.where.return_value = stmt_date
    now = datetime.now(UTC)
    api_audit._apply_date_filters(stmt_date, now, now, 200)
    assert stmt_date.where.call_count == 3

    # WORM chain integrity verification
    payload_rec = {
        "tenant_id": str(ctx["tenant_id"]),
        "actor_user_id": str(ctx["user_id"]),
        "actor_username": "admin",
        "event_category": "AUTH",
        "event_action": "LOGIN",
        "router_id": None,
        "status_code": 200,
        "before_state": None,
        "after_state": None,
    }
    rec_hash = compute_audit_record_hash(GENESIS_AUDIT_HASH, payload_rec)
    rec1 = AuditLog(
        id=uuid.uuid4(),
        tenant_id=ctx["tenant_id"],
        actor_user_id=ctx["user_id"],
        actor_username="admin",
        actor_role=SystemRoleEnum.TENANT_ADMIN,
        actor_ip="127.0.0.1",
        event_category="AUTH",
        event_action="LOGIN",
        status_code=200,
        prev_record_hash=GENESIS_AUDIT_HASH,
        record_sha256_hash=rec_hash,
        created_at=datetime.now(UTC),
    )

    assert api_audit._verify_single_audit_record(rec1, GENESIS_AUDIT_HASH) is True
    assert api_audit._verify_single_audit_record(rec1, "wrong_prev") is False

    # verify_audit_integrity endpoint
    mock_chain = MagicMock()
    mock_chain.scalars.return_value.all.return_value = [rec1]
    db.execute.return_value = mock_chain

    intact_res = await api_audit.verify_audit_integrity(claims=claims, db=db)
    assert intact_res.integrity_status == "VERIFIED_INTACT"
    assert intact_res.verified_records_count == 1

    # list_audit_logs and export_audit_logs
    mock_count = MagicMock()
    mock_count.scalar.return_value = 1
    db.execute.side_effect = [mock_count, mock_chain]
    logs_res = await api_audit.list_audit_logs(limit=10, offset=0, claims=claims, db=db)
    assert logs_res.total == 1

    db.execute.side_effect = None
    db.execute.return_value = mock_chain
    csv_resp = await api_audit.export_audit_logs(export_format="csv", claims=claims, db=db)
    assert csv_resp.headers["Content-Disposition"].endswith('.csv"')
    assert "X-Audit-Digest" in csv_resp.headers

    json_resp = await api_audit.export_audit_logs(export_format="json", claims=claims, db=db)
    assert json_resp.headers["Content-Disposition"].endswith('.json"')


# ============================================================================
# NOTIFICATION CHANNELS UNIT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_notification_channels_crud(fake_op_context: dict[str, Any]) -> None:
    ctx = fake_op_context
    claims = ctx["claims"]
    db = ctx["db"]

    ch_id = uuid.uuid4()
    conf = {"bot_token": "secret_token", "chat_id": "123456"}
    ct, iv, tag = api_channels._encrypt_channel_config(ctx["tenant_id"], ch_id, conf)

    now_utc = datetime.now(UTC)
    channel = NotificationChannel(
        id=ch_id,
        tenant_id=ctx["tenant_id"],
        name="Telegram NOC",
        channel_type=AlertChannelTypeEnum.TELEGRAM_BOT,
        is_enabled=True,
        config_ciphertext=ct,
        config_iv=iv,
        config_tag=tag,
        subscribed_events=["ROUTER_OFFLINE", "CPU_OVERLOAD"],
        created_at=now_utc,
        updated_at=now_utc,
    )

    decrypted = api_channels._decrypt_channel_config(ctx["tenant_id"], channel)
    assert decrypted["bot_token"] == "secret_token"

    mock_ch_list = MagicMock()
    mock_ch_list.scalars.return_value.all.return_value = [channel]
    db.execute.return_value = mock_ch_list

    ch_list = await api_channels.list_channels(claims=claims, db=db)
    assert len(ch_list) == 1

    create_payload = NotificationChannelCreateRequest(
        name="Webhook NOC",
        channel_type="GENERIC_WEBHOOK",
        is_enabled=True,
        config={"webhook_url": "https://hooks.example.com/alerts"},
        subscribed_events=["ALL"],
    )
    new_ch = await api_channels.create_channel(create_payload, claims=claims, db=db)
    assert new_ch.name == "Webhook NOC"

    db.get.return_value = channel
    up_payload = NotificationChannelUpdateRequest(name="Telegram NOC Updated", is_enabled=False)
    up_ch = await api_channels.update_channel(ch_id, up_payload, claims=claims, db=db)
    assert up_ch.name == "Telegram NOC Updated"
    # Update config
    up_cfg_payload = NotificationChannelUpdateRequest(config={"bot_token": "updated_token", "chat_id": "999"})
    up_cfg_ch = await api_channels.update_channel(ch_id, up_cfg_payload, claims=claims, db=db)
    assert up_cfg_ch is not None

    test_res = await api_channels.test_channel(ch_id, NotificationTestRequest(), claims=claims, db=db)
    assert test_res.status == "SUCCESS"

    # test_channel missing config fields
    bad_channel = NotificationChannel(
        id=uuid.uuid4(),
        tenant_id=ctx["tenant_id"],
        name="Bad Telegram",
        channel_type=AlertChannelTypeEnum.TELEGRAM_BOT,
        is_enabled=True,
        config_ciphertext=ct,
        config_iv=iv,
        config_tag=tag,
        subscribed_events=[],
        created_at=now_utc,
        updated_at=now_utc,
    )
    with patch("src.api.v1.notification_channels._decrypt_channel_config", return_value={}):
        db.get.return_value = bad_channel
        fail_res = await api_channels.test_channel(bad_channel.id, NotificationTestRequest(), claims=claims, db=db)
        assert fail_res.status == "FAILED"

        bad_channel.channel_type = AlertChannelTypeEnum.GENERIC_WEBHOOK
        fail_webhook = await api_channels.test_channel(bad_channel.id, NotificationTestRequest(), claims=claims, db=db)
        assert fail_webhook.status == "FAILED"

    db.get.return_value = channel
    await api_channels.delete_channel(ch_id, claims=claims, db=db)
    db.delete.assert_called_once_with(channel)

    # 404 error cases for channel not found
    db.get.return_value = None
    with pytest.raises(HTTPException) as exc_up_404:
        await api_channels.update_channel(uuid.uuid4(), up_payload, claims=claims, db=db)
    assert exc_up_404.value.status_code == 404

    with pytest.raises(HTTPException) as exc_del_404:
        await api_channels.delete_channel(uuid.uuid4(), claims=claims, db=db)
    assert exc_del_404.value.status_code == 404

    with pytest.raises(HTTPException) as exc_tst_404:
        await api_channels.test_channel(uuid.uuid4(), NotificationTestRequest(), claims=claims, db=db)
    assert exc_tst_404.value.status_code == 404
