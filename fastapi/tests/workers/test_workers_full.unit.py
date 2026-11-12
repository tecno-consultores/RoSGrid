# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Jesus Palencia <sinfallas@gmail.com> (Creado en Tecno Consultores)

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
    _resolve_smtp_recipients,
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
    fake_client._observed_fingerprint = "aabbcc112233"
    fake_client.ensure_ssl_verified = AsyncMock(return_value="aabbcc112233")

    with (
        patch("src.workers.health_monitor_worker._create_client_from_vault", return_value=fake_client),
        patch("src.workers.health_monitor_worker._publish_alert_and_event", new_callable=AsyncMock) as mock_pub,
    ):
        await _evaluate_single_router(session, redis, router_obj)
        assert router_obj.is_reachable is True
        assert router_obj.ssl_trust_status.value == "TRUSTED_PINNED"
        assert router_obj.ssl_sha256_fingerprint == "aabbcc112233"
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

    # Resolution of SMTP recipients (to_emails, to_addresses, fallback)
    assert _resolve_smtp_recipients({"to_emails": ["a@corp.com", "b@corp.com"]}) == ["a@corp.com", "b@corp.com"]
    assert _resolve_smtp_recipients({"to_emails": "a@corp.com, b@corp.com"}) == ["a@corp.com", "b@corp.com"]
    assert _resolve_smtp_recipients({"to_addresses": ["legacy@corp.com"]}) == ["legacy@corp.com"]
    assert _resolve_smtp_recipients({"from_email": "sender@corp.com"}) == ["sender@corp.com"]
    assert _resolve_smtp_recipients({"smtp_user": "user@corp.com"}) == ["user@corp.com"]
    assert _resolve_smtp_recipients({}) == []

    # SMTP dispatch sync with missing recipients raises ValueError
    with pytest.raises(ValueError, match="No se especificaron destinatarios"):
        _dispatch_smtp_sync({"to_addresses": []}, alert)

    # SMTP dispatch sync with STARTTLS (port 587)
    smtp_conf = {
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "alert@example.com",
        "smtp_password": "pwd",
        "to_emails": ["noc@example.com"],
        "use_tls": True,
    }
    mock_smtp_inst = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp_inst):
        mock_smtp_inst.__enter__.return_value = mock_smtp_inst
        _dispatch_smtp_sync(smtp_conf, alert)
        mock_smtp_inst.send_message.assert_called_once()
        mock_smtp_inst.starttls.assert_called_once()
        mock_smtp_inst.login.assert_called_once_with("alert@example.com", "pwd")

    # SMTP dispatch sync with SSL (port 465) and Gmail App Password with spaces
    smtp_ssl_conf = {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 465,
        "smtp_user": "noc@gmail.com",
        "smtp_password": "abcd efgh ijkl mnop",
        "to_emails": "admin@gmail.com",
    }
    test_alert_custom = {
        **alert,
        "custom_message": "Verificación manual de alerta de canal",
        "channel_name": "Gmail NOC",
    }
    mock_ssl_inst = MagicMock()
    with patch("smtplib.SMTP_SSL", return_value=mock_ssl_inst):
        mock_ssl_inst.__enter__.return_value = mock_ssl_inst
        _dispatch_smtp_sync(smtp_ssl_conf, test_alert_custom)
        mock_ssl_inst.send_message.assert_called_once()
        # Verify app password spaces were stripped
        mock_ssl_inst.login.assert_called_once_with("noc@gmail.com", "abcdefghijklmnop")

    # Webhook with Authorization header
    webhook_auth_conf = {
        "webhook_url": "https://webhook.site/secure",
        "auth_header": "Bearer my_secret_token",
    }
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        await _dispatch_webhook(webhook_auth_conf, alert)
        mock_post.assert_awaited_once()
        assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer my_secret_token"


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
        patch("src.workers.runner.syslog_collector_worker_loop", new_callable=AsyncMock),
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


@pytest.mark.asyncio
async def test_vault_rotation_individual_commits_and_error_truncation() -> None:
    """Verifica que la rotación haga commit individual y que el status de fallo no exceda 32 chars."""
    from src.workers.vault_rotation_worker import _rotate_single_vault

    mock_session = AsyncMock()

    # Router 1: Rotación exitosa
    vault1 = MagicMock()
    vault1.api_username = "admin"
    vault1.rotation_interval_days = 30
    router1 = MagicMock()
    router1.id = uuid.uuid4()
    router1.tenant_id = uuid.uuid4()
    router1.display_name = "Router-OK"

    mock_client1 = AsyncMock()
    with (
        patch("src.workers.vault_rotation_worker._create_client_from_vault", return_value=mock_client1),
        patch("src.workers.vault_rotation_worker.write_audit_log", new_callable=AsyncMock) as mock_audit,
    ):
        await _rotate_single_vault(mock_session, vault1, router1)
        assert vault1.last_rotation_status == "SUCCESS"
        assert mock_session.commit.call_count >= 1
        mock_audit.assert_awaited_once()

    # Router 2: Rotación con error > 100 caracteres
    mock_session.reset_mock()
    vault2 = MagicMock()
    vault2.api_username = "admin"
    router2 = MagicMock()
    router2.id = uuid.uuid4()
    router2.tenant_id = uuid.uuid4()
    router2.display_name = "Router-Fail"

    mock_client2 = AsyncMock()
    mock_client2.patch.side_effect = RuntimeError("X" * 150)
    with patch("src.workers.vault_rotation_worker._create_client_from_vault", return_value=mock_client2):
        await _rotate_single_vault(mock_session, vault2, router2)
        assert vault2.last_rotation_status == "FAILED"
        assert len(vault2.last_rotation_status) <= 32
        mock_session.rollback.assert_awaited()

    # Router 3: Fallos en rollback y commit en bloque except
    mock_session_failing = AsyncMock()
    mock_session_failing.rollback.side_effect = RuntimeError("Rollback failed")
    mock_session_failing.commit.side_effect = RuntimeError("Commit failed")
    vault3 = MagicMock()
    vault3.api_username = "admin"
    router3 = MagicMock()
    router3.display_name = "Router-Rollback-Fail"
    mock_client3 = AsyncMock()
    mock_client3.patch.side_effect = RuntimeError("Original error")
    with patch("src.workers.vault_rotation_worker._create_client_from_vault", return_value=mock_client3):
        await _rotate_single_vault(mock_session_failing, vault3, router3)
        assert vault3.last_rotation_status == "FAILED"

    # run_vault_rotation_cycle con mocks
    mock_vault_entry = MagicMock()
    mock_vault_entry.router = router1
    mock_db_sess = AsyncMock()
    mock_db_sess.execute.return_value = MockDbResult([mock_vault_entry])

    class MockAsyncSessionMaker:
        async def __aenter__(self):
            return mock_db_sess

        async def __aexit__(self, *args):
            pass

    with (
        patch("src.workers.vault_rotation_worker.async_session_maker", return_value=MockAsyncSessionMaker()),
        patch("src.workers.vault_rotation_worker._rotate_single_vault", new_callable=AsyncMock) as mock_rot_single,
    ):
        await run_vault_rotation_cycle()
        mock_rot_single.assert_awaited_once()


# ============================================================================
# SESSION LIFECYCLE WORKER TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_session_lifecycle_worker_full() -> None:
    """Verifica el barrido completo de sesiones efímeras con smembers, scan_iter, keys y loop."""
    from src.workers.session_lifecycle_worker import (
        session_lifecycle_worker_loop,
        sweep_all_tenants_closing_sessions,
    )

    t1 = str(uuid.uuid4())
    t2 = str(uuid.uuid4())

    # 1. Caso smembers
    mock_redis = AsyncMock()
    mock_redis.smembers.return_value = {t1.encode(), t2}
    with (
        patch("src.workers.session_lifecycle_worker.get_redis_client", return_value=mock_redis),
        patch(
            "src.workers.session_lifecycle_worker.sweep_expired_closing_sessions", return_value=["s1", "s2"]
        ) as mock_sweep,
    ):
        total = await sweep_all_tenants_closing_sessions()
        assert total == 4
        assert mock_sweep.call_count == 2

    # 2. Caso scan_iter fallback
    mock_redis_scan = AsyncMock()
    del mock_redis_scan.smembers  # Sin smembers

    async def fake_scan_iter(match: str, count: int):
        yield f"rg:{t1}:closing_sessions_zset".encode()
        yield f"rg:{t2}:closing_sessions_zset"

    mock_redis_scan.scan_iter = fake_scan_iter
    with (
        patch("src.workers.session_lifecycle_worker.get_redis_client", return_value=mock_redis_scan),
        patch("src.workers.session_lifecycle_worker.sweep_expired_closing_sessions", return_value=[]),
    ):
        total = await sweep_all_tenants_closing_sessions()
        assert total == 0

    # 3. Caso keys fallback
    mock_redis_keys = AsyncMock()
    del mock_redis_keys.smembers
    del mock_redis_keys.scan_iter
    mock_redis_keys.keys = AsyncMock(return_value=[f"rg:{t1}:closing_sessions_zset".encode()])
    with (
        patch("src.workers.session_lifecycle_worker.get_redis_client", return_value=mock_redis_keys),
        patch("src.workers.session_lifecycle_worker.sweep_expired_closing_sessions", return_value=["s1"]),
    ):
        total = await sweep_all_tenants_closing_sessions()
        assert total == 1

    # 4. Excepción capturada
    mock_redis_err = AsyncMock()
    mock_redis_err.smembers.side_effect = RuntimeError("Redis error")
    with patch("src.workers.session_lifecycle_worker.get_redis_client", return_value=mock_redis_err):
        total = await sweep_all_tenants_closing_sessions()
        assert total == 0

    # 5. Worker loop
    with (
        patch(
            "src.workers.session_lifecycle_worker.sweep_all_tenants_closing_sessions",
            side_effect=[1, RuntimeError("fail"), asyncio.CancelledError],
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        await session_lifecycle_worker_loop()


# ============================================================================
# TELEMETRY BEACON WORKER & RUNNER HEARTBEAT TESTS
# ============================================================================


@pytest.mark.asyncio
async def test_telemetry_beacon_worker_full() -> None:
    """Verifica loop, ticks y sleep interval del worker de telemetría."""
    from src.workers.telemetry_beacon_worker import (
        _beacon_sleep_interval,
        _dispatch_beacon_http,
        _execute_beacon_tick,
        telemetry_beacon_worker_loop,
    )

    # 1. Worker disabled
    with patch("src.workers.telemetry_beacon_worker.settings.ROSGRID_TELEMETRY_BEACON_ENABLED", False):
        await telemetry_beacon_worker_loop()

    # 2. Worker enabled y stop_event
    stop_event = asyncio.Event()
    with (
        patch("src.workers.telemetry_beacon_worker.settings.ROSGRID_TELEMETRY_BEACON_ENABLED", True),
        patch("src.workers.telemetry_beacon_worker.settings.ROSGRID_TELEMETRY_BEACON_INTERVAL_SECONDS", 1),
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch("src.workers.telemetry_beacon_worker._execute_beacon_tick", new_callable=AsyncMock) as mock_tick,
        patch("src.workers.telemetry_beacon_worker._beacon_sleep_interval", return_value=True),
    ):
        await telemetry_beacon_worker_loop(stop_event)
        mock_tick.assert_awaited_once()

    # 3. _execute_beacon_tick con excepción ordinaria y CancelledError
    with patch("src.workers.telemetry_beacon_worker.send_telemetry_heartbeat_once", side_effect=RuntimeError("err")):
        await _execute_beacon_tick()

    with patch("src.workers.telemetry_beacon_worker.send_telemetry_heartbeat_once", side_effect=asyncio.CancelledError):
        with pytest.raises(asyncio.CancelledError):
            await _execute_beacon_tick()

    # 4. _beacon_sleep_interval
    ev = asyncio.Event()
    # Sin stop_event
    with patch("asyncio.sleep", new_callable=AsyncMock):
        assert await _beacon_sleep_interval(None, 1) is False

    # Con stop_event ya activado
    ev.set()
    assert await _beacon_sleep_interval(ev, 1) is True

    # Timeout en wait_for
    ev_to = asyncio.Event()
    with patch("asyncio.wait_for", side_effect=TimeoutError):
        assert await _beacon_sleep_interval(ev_to, 1) is False

    # 5. _dispatch_beacon_http con fallback GET en 403/405
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 405
    mock_get_resp = MagicMock()
    mock_get_resp.status_code = 200

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_post_resp
    mock_client.get.return_value = mock_get_resp

    class MockAsyncClientCtx:
        async def __aenter__(self):
            return mock_client

        async def __aexit__(self, *args):
            pass

    with patch("httpx.AsyncClient", return_value=MockAsyncClientCtx()):
        status = await _dispatch_beacon_http({"key": "val"})
        assert status == 200
        mock_client.post.assert_awaited_once()
        mock_client.get.assert_awaited_once()

    # 6. get_telemetry_beacon_status con fallo en KeyDB y send_telemetry_heartbeat_once sin router_count
    from src.workers.telemetry_beacon_worker import (
        get_telemetry_beacon_status,
        send_telemetry_heartbeat_once,
    )

    mock_redis_err = AsyncMock()
    mock_redis_err.hgetall.side_effect = RuntimeError("KeyDB unreachable")
    with (
        patch("src.workers.telemetry_beacon_worker.get_redis_client", return_value=mock_redis_err),
        patch("src.workers.telemetry_beacon_worker._count_active_routers_safe", return_value=3),
    ):
        status_res = await get_telemetry_beacon_status()
        assert status_res["router_count"] == 3

    with (
        patch("src.workers.telemetry_beacon_worker._count_active_routers_safe", return_value=2),
        patch("src.workers.telemetry_beacon_worker.settings.ROSGRID_TELEMETRY_BEACON_ENABLED", False),
    ):
        once_res = await send_telemetry_heartbeat_once(router_count=None)
        assert once_res["router_count"] == 2


@pytest.mark.asyncio
async def test_runner_worker_heartbeat_loop_monitoring() -> None:
    """Verifica que el heartbeat distinga workers opcionales desactivados de fallos reales."""
    from pathlib import Path

    from src.workers.runner import (
        _has_failed_sibling,
        _is_sibling_worker_failed,
        _worker_heartbeat_loop,
        _write_heartbeat_tick,
    )

    assert _has_failed_sibling(None) is False
    assert _has_failed_sibling([]) is False

    # Worker obligatorio terminado sin excepción -> sigue siendo fallo inesperado
    mock_mandatory_exited = MagicMock()
    mock_mandatory_exited.get_name.return_value = "HealthMonitorWorker"
    mock_mandatory_exited.done.return_value = True
    mock_mandatory_exited.cancelled.return_value = False
    mock_mandatory_exited.exception.return_value = None
    assert _is_sibling_worker_failed(mock_mandatory_exited) is True

    # Worker opcional desactivado por flag (return limpio, exception is None) -> NO es fallo
    mock_optional_disabled = MagicMock()
    mock_optional_disabled.get_name.return_value = "TelemetryBeaconWorker"
    mock_optional_disabled.done.return_value = True
    mock_optional_disabled.cancelled.return_value = False
    mock_optional_disabled.exception.return_value = None
    assert _is_sibling_worker_failed(mock_optional_disabled) is False

    # Worker opcional que crashea con excepción -> SÍ es fallo
    mock_optional_crashed = MagicMock()
    mock_optional_crashed.get_name.return_value = "TelemetryBeaconWorker"
    mock_optional_crashed.done.return_value = True
    mock_optional_crashed.cancelled.return_value = False
    mock_optional_crashed.exception.return_value = RuntimeError("Crash")
    assert _is_sibling_worker_failed(mock_optional_crashed) is True

    # Worker cancelado durante apagado ordenado -> NO es fallo
    mock_cancelled = MagicMock()
    mock_cancelled.done.return_value = True
    mock_cancelled.cancelled.return_value = True
    assert _is_sibling_worker_failed(mock_cancelled) is False

    mock_task_running = MagicMock()
    mock_task_running.get_name.return_value = "healthy_worker"
    mock_task_running.done.return_value = False
    mock_task_running.cancelled.return_value = False

    stop_event = asyncio.Event()
    mock_path = MagicMock(spec=Path)

    async def fake_wait_for_1(fut: Any, timeout: float) -> None:
        fut.close()
        stop_event.set()

    with (
        patch("src.workers.runner.WORKER_HEARTBEAT_PATH", mock_path),
        patch("asyncio.wait_for", side_effect=fake_wait_for_1),
    ):
        # 1. Con tarea obligatoria caída: no debe escribir heartbeat
        await _worker_heartbeat_loop(stop_event, [mock_mandatory_exited, mock_task_running])
        mock_path.write_text.assert_not_called()

    # 2. Con worker opcional desactivado + workers vivos: SÍ escribe heartbeat (incluso tras TimeoutError)
    mock_path.reset_mock()
    stop_event_2 = asyncio.Event()
    calls_2 = 0

    async def fake_wait_for_2(fut: Any, timeout: float) -> None:
        nonlocal calls_2
        fut.close()
        calls_2 += 1
        if calls_2 == 1:
            raise TimeoutError
        stop_event_2.set()

    with (
        patch("src.workers.runner.WORKER_HEARTBEAT_PATH", mock_path),
        patch("asyncio.wait_for", side_effect=fake_wait_for_2),
    ):
        await _worker_heartbeat_loop(stop_event_2, [mock_optional_disabled, mock_task_running])
        assert mock_path.write_text.call_count == 2

    # 3. Resiliencia ante OSError en escritura de disco
    mock_path_err = MagicMock(spec=Path)
    mock_path_err.write_text.side_effect = OSError("Read-only fs")
    with patch("src.workers.runner.WORKER_HEARTBEAT_PATH", mock_path_err):
        _write_heartbeat_tick()


@pytest.mark.asyncio
async def test_main_workers_runner_writes_real_heartbeat_with_production_defaults(
    tmp_path: Any,
) -> None:
    """Prueba Anti-Silo: arranca main_workers_runner con loops opcionales reales desactivados y verifica el archivo de healthcheck."""
    heartbeat_file = tmp_path / "worker_heartbeat"

    async def _blocking_forever_worker(*_args: Any, **_kwargs: Any) -> None:
        await asyncio.Event().wait()

    with (
        patch("src.workers.runner.WORKER_HEARTBEAT_PATH", heartbeat_file),
        patch("src.workers.runner.health_monitor_worker_loop", side_effect=_blocking_forever_worker),
        patch("src.workers.runner.alert_dispatcher_worker_loop", side_effect=_blocking_forever_worker),
        patch("src.workers.runner.nightly_backup_worker_loop", side_effect=_blocking_forever_worker),
        patch("src.workers.runner.vault_rotation_worker_loop", side_effect=_blocking_forever_worker),
        patch("src.workers.runner.syslog_collector_worker_loop", side_effect=_blocking_forever_worker),
        patch("src.workers.runner.subscriber_status_poller_worker_loop", side_effect=_blocking_forever_worker),
        patch("src.workers.runner.session_lifecycle_worker_loop", side_effect=_blocking_forever_worker),
        # Loops opcionales REALES sin AsyncMock bajo defaults de producción (opt-in false):
        patch("src.workers.telemetry_beacon_worker.settings.ROSGRID_TELEMETRY_BEACON_ENABLED", False),
        patch("src.workers.version_check_worker.settings.ROSGRID_VERSION_CHECK_ENABLED", False),
        patch("src.workers.runner.close_redis_client", new_callable=AsyncMock),
    ):
        runner_task = asyncio.create_task(main_workers_runner())
        # Cede múltiples ticks al event loop para que los workers opcionales retornen ANTES/DURANTE el heartbeat
        await asyncio.sleep(0.05)

        assert heartbeat_file.exists(), (
            "El archivo /tmp/worker_heartbeat debe crearse en el arranque con los defaults de producción"
        )
        content = heartbeat_file.read_text(encoding="utf-8").strip()
        assert content.isdigit() and int(content) > 0

        runner_task.cancel()
        try:
            await runner_task
        except asyncio.CancelledError:
            pass
