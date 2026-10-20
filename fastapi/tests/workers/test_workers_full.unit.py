# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Suite Completa de Pruebas Unitarias para los Workers en Segundo Plano (Hito 10)."""

import asyncio
import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.crypto import encrypt_aes_gcm
from src.mikrotik.client import MikrotikRestClient
from src.models.inventory import MaintenanceWindow, Router, RouterAdminStateEnum, RouterCredentialsVault
from src.models.operations import AlertChannelTypeEnum, NotificationChannel, RouterBackup
from src.workers.alert_dispatcher_worker import (
    _decrypt_config,
    _dispatch_smtp_sync,
    _dispatch_telegram,
    _dispatch_to_channel,
    _dispatch_webhook,
    _process_alert_payload,
    alert_dispatcher_worker_loop,
    is_safe_webhook_url,
)
from src.workers.health_monitor_worker import (
    _check_router_in_maintenance,
    _evaluate_single_router,
    _ping_router_resource,
    _publish_alert_and_event,
    health_monitor_worker_loop,
    run_health_monitor_cycle,
)
from src.workers.nightly_backup_worker import (
    _backup_single_router,
    _purge_expired_backups,
    nightly_backup_worker_loop,
    run_nightly_backup_cycle,
)
from src.workers.runner import _setup_signal_handlers, main, main_workers_runner
from src.workers.vault_rotation_worker import (
    _generate_safe_password,
    _rotate_single_vault,
    run_vault_rotation_cycle,
    vault_rotation_worker_loop,
)


class MockScalars:
    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def all(self) -> list[Any]:
        return self._items

    def scalar_one_or_none(self) -> Any:
        return self._items[0] if self._items else None


class MockDbResult:
    def __init__(self, items: list[Any] | None = None, single: Any = None) -> None:
        self._items = items if items is not None else ([single] if single is not None else [])
        self._single = single if single is not None else (items[0] if items else None)

    def scalars(self) -> MockScalars:
        return MockScalars(self._items)

    def scalar_one_or_none(self) -> Any:
        return self._single

    def scalar(self) -> Any:
        return self._single


def _build_test_router() -> tuple[Router, RouterCredentialsVault]:
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()
    r = Router(
        id=r_id,
        tenant_id=t_id,
        display_name="Core-Worker-01",
        api_base_url="https://10.0.0.1:443",
        api_port=443,
        admin_state=RouterAdminStateEnum.PRODUCTION,
        ros_version="7.16",
    )
    aad = f"{t_id}:{r_id}".encode()
    ct, iv, tag = encrypt_aes_gcm(b"secret_pass", aad)
    v = RouterCredentialsVault(
        router_id=r_id,
        tenant_id=t_id,
        api_username="admin",
        current_password_ciphertext=ct,
        current_password_iv=iv,
        current_password_tag=tag,
        auto_rotate_enabled=True,
        rotation_interval_days=30,
        next_rotation_due_at=datetime.now(UTC) - timedelta(days=1),
    )
    r.vault = v
    v.router = r
    return r, v


# ============================================================================
# HEALTH MONITOR WORKER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_health_monitor_maintenance_check() -> None:
    session = AsyncMock()
    t_id = uuid.uuid4()
    r_id = uuid.uuid4()

    # Case 1: In maintenance
    mw = MaintenanceWindow(id=uuid.uuid4(), tenant_id=t_id, router_id=r_id)
    session.execute.return_value = MockDbResult([mw])
    assert await _check_router_in_maintenance(session, t_id, r_id) is True

    # Case 2: Not in maintenance
    session.execute.return_value = MockDbResult([])
    assert await _check_router_in_maintenance(session, t_id, r_id) is False


@pytest.mark.asyncio
async def test_health_monitor_ping_resource() -> None:
    client = AsyncMock(spec=MikrotikRestClient)

    # Success case
    client.get.return_value = {"cpu-load": 15, "total-memory": 1000, "free-memory": 600}
    reachable, cpu, free_pct = await _ping_router_resource(client)
    assert reachable is True
    assert cpu == 15
    assert free_pct == 60

    # Failure case
    client.get.side_effect = TimeoutError("Connection timed out")
    reachable, cpu, free_pct = await _ping_router_resource(client)
    assert reachable is False
    assert cpu == 0
    assert free_pct == 0


@pytest.mark.asyncio
async def test_health_monitor_publish_and_evaluate() -> None:
    redis = AsyncMock()
    session = AsyncMock()
    router_obj, _ = _build_test_router()

    # Publish alert and event
    await _publish_alert_and_event(
        redis, router_obj.tenant_id, router_obj.id, router_obj.display_name, "ROUTER_REACHABLE", "ONLINE"
    )
    assert redis.publish.await_count == 2

    # Evaluate single router with transition from OFFLINE to ONLINE
    session.execute.return_value = MockDbResult([])
    redis.hgetall.return_value = {"operational_status": "OFFLINE", "consecutive_failures": "3"}

    fake_client = AsyncMock(spec=MikrotikRestClient)
    fake_client.get.return_value = {"cpu-load": 20, "total-memory": 1000, "free-memory": 700}
    fake_client.close = AsyncMock()

    with (
        patch("src.workers.health_monitor_worker._create_client_from_vault", return_value=fake_client),
        patch("src.workers.health_monitor_worker._publish_alert_and_event", new_callable=AsyncMock) as mock_pub,
    ):
        await _evaluate_single_router(session, redis, router_obj)
        assert router_obj.is_reachable is True
        assert redis.hset.await_count == 1
        assert mock_pub.await_count >= 1


@pytest.mark.asyncio
async def test_health_monitor_cycle_and_loop() -> None:
    router_obj, _ = _build_test_router()
    fake_session = AsyncMock()
    fake_session.execute.return_value = MockDbResult([router_obj])

    class MockContextManager:
        async def __aenter__(self) -> AsyncMock:
            return fake_session

        async def __aexit__(self, *args: Any) -> None:
            pass

    with (
        patch("src.workers.health_monitor_worker.get_redis_client", return_value=AsyncMock()),
        patch("src.workers.health_monitor_worker.async_session_maker", return_value=MockContextManager()),
        patch("src.workers.health_monitor_worker._evaluate_single_router", new_callable=AsyncMock) as mock_eval,
    ):
        await run_health_monitor_cycle()
        mock_eval.assert_awaited_once()

    # Router evaluation error inside cycle
    with (
        patch("src.workers.health_monitor_worker.get_redis_client", return_value=AsyncMock()),
        patch("src.workers.health_monitor_worker.async_session_maker", return_value=MockContextManager()),
        patch("src.workers.health_monitor_worker._evaluate_single_router", side_effect=RuntimeError("eval fail")),
    ):
        await run_health_monitor_cycle()

    # Loop cancellation and exception handling
    with patch("src.workers.health_monitor_worker.run_health_monitor_cycle", side_effect=asyncio.CancelledError):
        await health_monitor_worker_loop()

    with (
        patch(
            "src.workers.health_monitor_worker.run_health_monitor_cycle",
            side_effect=[RuntimeError("loop fail"), asyncio.CancelledError],
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        await health_monitor_worker_loop()


# ============================================================================
# ALERT DISPATCHER WORKER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_alert_dispatcher_decryption_and_dispatchers() -> None:
    t_id = uuid.uuid4()
    ch_id = uuid.uuid4()
    conf = {"bot_token": "token123", "chat_id": "chat999"}
    aad = f"{t_id}:{ch_id}".encode()
    ct, iv, tag = encrypt_aes_gcm(json.dumps(conf).encode("utf-8"), aad)

    ch = NotificationChannel(
        id=ch_id,
        tenant_id=t_id,
        channel_type=AlertChannelTypeEnum.TELEGRAM_BOT,
        config_ciphertext=ct,
        config_iv=iv,
        config_tag=tag,
        subscribed_events=["ROUTER_DOWN"],
    )

    decrypted = _decrypt_config(t_id, ch)
    assert decrypted["bot_token"] == "token123"

    alert = {
        "event_name": "ROUTER_DOWN",
        "router_display_name": "R1",
        "operational_status": "OFFLINE",
        "timestamp_iso": "2026-10-15T00:00:00Z",
    }

    # Telegram dispatch
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        await _dispatch_telegram(conf, alert)
        mock_post.assert_awaited_once()

    # Webhook dispatch
    webhook_conf = {"webhook_url": "https://webhook.site/test", "secret": "s3cr3t"}
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        await _dispatch_webhook(webhook_conf, alert)
        mock_post.assert_awaited_once()

    # Webhook dispatch with empty url
    await _dispatch_webhook({"webhook_url": ""}, alert)

    # Webhook dispatch blocked by SSRF
    assert is_safe_webhook_url("https://hooks.slack.com/services/T00/B00/X00") is True
    assert is_safe_webhook_url("http://127.0.0.1:8000/internal") is False
    assert is_safe_webhook_url("http://localhost:8000/internal") is False
    assert is_safe_webhook_url("http://169.254.169.254/latest/meta-data") is False
    assert is_safe_webhook_url("http://10.0.0.1/admin") is False
    assert is_safe_webhook_url("ftp://example.com") is False
    assert is_safe_webhook_url("not-a-valid-url") is False
    assert is_safe_webhook_url("http://") is False
    with patch("urllib.parse.urlparse", side_effect=ValueError("bad url")):
        assert is_safe_webhook_url("https://example.com") is False

    webhook_conf_ssrf = {"webhook_url": "http://169.254.169.254/latest/meta-data", "secret": "s3cr3t"}
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        await _dispatch_webhook(webhook_conf_ssrf, alert)
        mock_post.assert_not_called()

    # Telegram dispatch with missing config
    await _dispatch_telegram({"bot_token": ""}, alert)

    # SMTP dispatch sync with missing to_addresses
    _dispatch_smtp_sync({"to_addresses": []}, alert)

    # SMTP dispatch sync
    smtp_conf = {
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "alert@example.com",
        "smtp_password": "pwd",
        "to_addresses": ["noc@example.com"],
        "use_tls": True,
    }
    mock_smtp_inst = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp_inst):
        mock_smtp_inst.__enter__.return_value = mock_smtp_inst
        _dispatch_smtp_sync(smtp_conf, alert)
        mock_smtp_inst.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_alert_dispatcher_channel_selection_and_process() -> None:
    t_id = uuid.uuid4()
    ch_id = uuid.uuid4()
    conf = {"bot_token": "token123", "chat_id": "chat999"}
    aad = f"{t_id}:{ch_id}".encode()
    ct, iv, tag = encrypt_aes_gcm(json.dumps(conf).encode("utf-8"), aad)

    ch = NotificationChannel(
        id=ch_id,
        tenant_id=t_id,
        name="Telegram NOC",
        channel_type=AlertChannelTypeEnum.TELEGRAM_BOT,
        config_ciphertext=ct,
        config_iv=iv,
        config_tag=tag,
        subscribed_events=["ROUTER_DOWN"],
    )

    alert = {"event_name": "ROUTER_DOWN", "router_display_name": "R1"}

    with patch("src.workers.alert_dispatcher_worker._dispatch_telegram", new_callable=AsyncMock) as mock_tel:
        await _dispatch_to_channel(t_id, ch, alert)
        mock_tel.assert_awaited_once()

    # Unsubscribed event
    unsubscribed_alert = {"event_name": "ROUTER_UP", "router_display_name": "R1"}
    await _dispatch_to_channel(t_id, ch, unsubscribed_alert)

    # SMTP channel dispatch
    ch_smtp = NotificationChannel(
        id=ch_id,
        tenant_id=t_id,
        name="SMTP NOC",
        channel_type=AlertChannelTypeEnum.SMTP_EMAIL,
        config_ciphertext=ct,
        config_iv=iv,
        config_tag=tag,
        subscribed_events=["ROUTER_DOWN"],
    )
    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_smtp:
        await _dispatch_to_channel(t_id, ch_smtp, alert)
        mock_smtp.assert_awaited_once()

    # Webhook channel dispatch
    ch_webhook = NotificationChannel(
        id=ch_id,
        tenant_id=t_id,
        name="Webhook NOC",
        channel_type=AlertChannelTypeEnum.GENERIC_WEBHOOK,
        config_ciphertext=ct,
        config_iv=iv,
        config_tag=tag,
        subscribed_events=["ROUTER_DOWN"],
    )
    with patch("src.workers.alert_dispatcher_worker._dispatch_webhook", new_callable=AsyncMock) as mock_wh:
        await _dispatch_to_channel(t_id, ch_webhook, alert)
        mock_wh.assert_awaited_once()

    # Exception handling during dispatch
    with patch("src.workers.alert_dispatcher_worker._dispatch_telegram", side_effect=RuntimeError("telegram error")):
        await _dispatch_to_channel(t_id, ch, alert)

    # Process alert payload with DB lookup
    fake_session = AsyncMock()
    fake_session.execute.return_value = MockDbResult([ch])

    class MockContextManager:
        async def __aenter__(self) -> AsyncMock:
            return fake_session

        async def __aexit__(self, *args: Any) -> None:
            pass

    with (
        patch("src.workers.alert_dispatcher_worker.async_session_maker", return_value=MockContextManager()),
        patch("src.workers.alert_dispatcher_worker._dispatch_to_channel", new_callable=AsyncMock) as mock_disp,
    ):
        await _process_alert_payload(str(t_id), json.dumps(alert))
        mock_disp.assert_awaited_once()

        # Invalid json handling
        await _process_alert_payload("bad-uuid", "invalid-json")


@pytest.mark.asyncio
async def test_alert_dispatcher_worker_loop() -> None:
    mock_pubsub = AsyncMock()
    mock_pubsub.get_message.side_effect = [
        {"channel": b"rg:pubsub:alerts:11111111-1111-1111-1111-111111111111", "data": b'{"event_name": "TEST"}'},
        asyncio.CancelledError(),
    ]
    fake_redis = MagicMock()
    fake_redis.pubsub.return_value = mock_pubsub

    with (
        patch("src.workers.alert_dispatcher_worker.get_redis_client", return_value=fake_redis),
        patch("src.workers.alert_dispatcher_worker._process_alert_payload", new_callable=AsyncMock) as mock_proc,
    ):
        await alert_dispatcher_worker_loop()
        mock_proc.assert_awaited_once()


# ============================================================================
# NIGHTLY BACKUP WORKER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_nightly_backup_purge() -> None:
    session = AsyncMock()
    r_id = uuid.uuid4()
    now = datetime.now(UTC)

    b_expired_old = RouterBackup(id=uuid.uuid4(), router_id=r_id, created_at=now - timedelta(days=40))
    b_expired_latest = RouterBackup(id=uuid.uuid4(), router_id=r_id, created_at=now - timedelta(days=31))

    # First query returns expired backups
    session.execute.side_effect = [
        MockDbResult([b_expired_latest, b_expired_old]),
        MockDbResult(single=b_expired_latest.id),  # latest check for b_expired_latest
    ]

    purged = await _purge_expired_backups(session)
    assert purged == 1
    session.delete.assert_awaited_once_with(b_expired_old)


@pytest.mark.asyncio
async def test_nightly_backup_single_router_and_cycle() -> None:
    session = AsyncMock()
    session.add = MagicMock()
    router_obj, _ = _build_test_router()

    fake_client = AsyncMock(spec=MikrotikRestClient)
    fake_client.post.return_value = "/ip address\nadd address=10.0.0.1/24 interface=ether1\n"
    fake_client.close = AsyncMock()

    # Case 1: First backup (no previous backup)
    session.execute.return_value = MockDbResult([])

    with patch("src.workers.nightly_backup_worker._create_client_from_vault", return_value=fake_client):
        await _backup_single_router(session, router_obj)
        session.add.assert_called_once()

    # Case 1b: Router without vault returns None
    router_no_vault = Router(id=uuid.uuid4(), tenant_id=uuid.uuid4(), display_name="R-NoVault")
    router_no_vault.vault = None
    await _backup_single_router(session, router_no_vault)

    # Case 1c: Deduplication branch (identical hash)
    cleaned_rsc = "/ip address\nadd address=10.0.0.1/24 interface=ether1\n"
    rsc_hash = hashlib.sha256(cleaned_rsc.encode("utf-8")).hexdigest()
    identical_b = MagicMock(rsc_sha256_hash=rsc_hash)
    session_dup = AsyncMock()
    session_dup.execute.return_value = MockDbResult([identical_b], single=identical_b)
    with patch("src.workers.nightly_backup_worker._create_client_from_vault", return_value=fake_client):
        await _backup_single_router(session_dup, router_obj)
        assert identical_b.last_verified_identical_at is not None

    # Case 2: Run cycle
    fake_session = AsyncMock()
    fake_session.execute.return_value = MockDbResult([router_obj])

    class MockContextManager:
        async def __aenter__(self) -> AsyncMock:
            return fake_session

        async def __aexit__(self, *args: Any) -> None:
            pass

    with (
        patch("src.workers.nightly_backup_worker.async_session_maker", return_value=MockContextManager()),
        patch("src.workers.nightly_backup_worker._backup_single_router", new_callable=AsyncMock) as mock_bk,
        patch("src.workers.nightly_backup_worker._purge_expired_backups", new_callable=AsyncMock, return_value=0),
    ):
        await run_nightly_backup_cycle()
        mock_bk.assert_awaited_once()

    # Case 2b: Cycle exception handling
    with (
        patch("src.workers.nightly_backup_worker.async_session_maker", return_value=MockContextManager()),
        patch("src.workers.nightly_backup_worker._backup_single_router", side_effect=RuntimeError("backup fail")),
        patch("src.workers.nightly_backup_worker._purge_expired_backups", new_callable=AsyncMock, return_value=0),
    ):
        await run_nightly_backup_cycle()

    # Case 3: Loop cancellation and exception handling
    with patch("src.workers.nightly_backup_worker.run_nightly_backup_cycle", side_effect=asyncio.CancelledError):
        await nightly_backup_worker_loop()

    with (
        patch(
            "src.workers.nightly_backup_worker.run_nightly_backup_cycle",
            side_effect=[RuntimeError("loop fail"), asyncio.CancelledError],
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        await nightly_backup_worker_loop()


# ============================================================================
# VAULT ROTATION WORKER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_vault_rotation_single_and_cycle() -> None:
    pwd = _generate_safe_password()
    assert len(pwd) == 32

    session = AsyncMock()
    router_obj, vault_obj = _build_test_router()

    fake_client = AsyncMock(spec=MikrotikRestClient)
    fake_client.patch.return_value = {}
    fake_client.close = AsyncMock()

    with (
        patch("src.workers.vault_rotation_worker._create_client_from_vault", return_value=fake_client),
        patch("src.workers.vault_rotation_worker.write_audit_log", new_callable=AsyncMock) as mock_audit,
    ):
        await _rotate_single_vault(session, vault_obj, router_obj)
        assert vault_obj.last_rotation_status == "SUCCESS"
        mock_audit.assert_awaited_once()

    # Exception in rotation
    fake_client.patch.side_effect = RuntimeError("Router connection refused")
    with patch("src.workers.vault_rotation_worker._create_client_from_vault", return_value=fake_client):
        await _rotate_single_vault(session, vault_obj, router_obj)
        assert "FAILED" in vault_obj.last_rotation_status

    # Cycle test
    fake_session = AsyncMock()
    fake_session.execute.return_value = MockDbResult([vault_obj])

    class MockContextManager:
        async def __aenter__(self) -> AsyncMock:
            return fake_session

        async def __aexit__(self, *args: Any) -> None:
            pass

    with (
        patch("src.workers.vault_rotation_worker.async_session_maker", return_value=MockContextManager()),
        patch("src.workers.vault_rotation_worker._rotate_single_vault", new_callable=AsyncMock) as mock_rot,
    ):
        await run_vault_rotation_cycle()
        mock_rot.assert_awaited_once()

    # Loop cancellation and exception handling
    with patch("src.workers.vault_rotation_worker.run_vault_rotation_cycle", side_effect=asyncio.CancelledError):
        await vault_rotation_worker_loop()

    with (
        patch(
            "src.workers.vault_rotation_worker.run_vault_rotation_cycle",
            side_effect=[RuntimeError("cycle err"), asyncio.CancelledError],
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        await vault_rotation_worker_loop()


# ============================================================================
# RUNNER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_workers_runner() -> None:
    stop_event = asyncio.Event()
    _setup_signal_handlers(stop_event)

    # Signal handlers on platforms raising NotImplementedError
    fake_loop = MagicMock()
    fake_loop.add_signal_handler.side_effect = NotImplementedError
    with patch("asyncio.get_running_loop", return_value=fake_loop):
        _setup_signal_handlers(stop_event)

    with (
        patch("src.workers.runner.health_monitor_worker_loop", new_callable=AsyncMock),
        patch("src.workers.runner.alert_dispatcher_worker_loop", new_callable=AsyncMock),
        patch("src.workers.runner.nightly_backup_worker_loop", new_callable=AsyncMock),
        patch("src.workers.runner.vault_rotation_worker_loop", new_callable=AsyncMock),
        patch("src.workers.runner.close_redis_client", new_callable=AsyncMock),
    ):
        # Trigger stop_event immediately
        runner_task = asyncio.create_task(main_workers_runner())
        await asyncio.sleep(0.01)
        runner_task.cancel()
        try:
            await runner_task
        except asyncio.CancelledError:
            pass

    with (
        patch("src.workers.runner.main_workers_runner", new_callable=AsyncMock),
        patch("asyncio.run") as mock_run,
    ):
        main()
        mock_run.assert_called_once()

    # KeyboardInterrupt in main()
    with (
        patch("asyncio.run", side_effect=KeyboardInterrupt),
        patch("sys.exit") as mock_exit,
    ):
        main()
        mock_exit.assert_called_once_with(0)
