# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para el motor Safe Mode (Dead Man's Switch)."""

from unittest.mock import AsyncMock

import pytest

from src.mikrotik.safemode import (
    SafeModeRollbackTriggeredError,
    build_rollback_command,
    build_scheduler_payload,
    execute_with_safemode,
    generate_safemode_job_name,
    inject_deadmans_switch,
    remove_deadmans_switch,
    verify_connectivity,
)


def test_generate_safemode_job_name() -> None:
    name1 = generate_safemode_job_name()
    assert name1.startswith("rosgrid-safemode-")
    name2 = generate_safemode_job_name("custom-op")
    assert name2 == "rosgrid-safemode-custom-op"


def test_build_rollback_command() -> None:
    # Set/patch
    cmd_set = build_rollback_command(
        menu_path="/ip/firewall/filter",
        action="set",
        item_id="*1",
        before_state={".id": "*1", "disabled": True, "comment": "blocked"},
    )
    assert "/ip/firewall/filter/set [find .id=*1]" in cmd_set
    assert "disabled=yes" in cmd_set
    assert 'comment="blocked"' in cmd_set

    # Create/put with item_id
    cmd_create_id = build_rollback_command(
        menu_path="/interface/vlan",
        action="create",
        item_id="*2",
    )
    assert cmd_create_id == "/interface/vlan/remove [find .id=*2]"

    # Create/put with comment in before_state
    cmd_create_comment = build_rollback_command(
        menu_path="/interface/vlan",
        action="create",
        before_state={"comment": "my-vlan"},
    )
    assert cmd_create_comment == '/interface/vlan/remove [find comment="my-vlan"]'

    # Create/put without item_id or comment
    cmd_create_none = build_rollback_command(
        menu_path="/interface/vlan",
        action="create",
    )
    assert cmd_create_none == "/interface/vlan/remove [find]"

    # Delete
    cmd_delete = build_rollback_command(
        menu_path="/ip/address",
        action="delete",
        item_id="*3",
    )
    assert cmd_delete == "/ip/address/set [find .id=*3] disabled=no"

    # Unknown
    assert build_rollback_command("/menu", "unknown") == ":nothing"


def test_build_scheduler_payload() -> None:
    payload = build_scheduler_payload(
        job_name="rosgrid-safemode-test",
        rollback_cli="/ip/address/remove [find .id=*1]",
        interval_seconds=60,
    )
    assert payload["name"] == "rosgrid-safemode-test"
    assert payload["interval"] == "00:01:00"
    assert "on-event" in payload
    assert "/ip/address/remove" in payload["on-event"]
    assert "rosgrid-safemode-test" in payload["on-event"]


@pytest.mark.asyncio
async def test_inject_deadmans_switch() -> None:
    client = AsyncMock()
    job_name = await inject_deadmans_switch(
        client=client,
        rollback_cli="/ip/address/remove [find]",
        interval_seconds=30,
        job_name="my-job",
    )
    assert job_name == "my-job"
    client.put.assert_awaited_once()
    args, kwargs = client.put.await_args
    assert args[0] == "/system/scheduler"
    assert kwargs["json_data"]["name"] == "my-job"


@pytest.mark.asyncio
async def test_verify_connectivity_success_and_failure() -> None:
    client = AsyncMock()
    # Success on first attempt
    client.get.return_value = {"name": "Router01"}
    assert await verify_connectivity(client, max_retries=2, retry_delay=0.01) is True

    # Failure all attempts
    client.get.side_effect = Exception("Connection lost")
    assert await verify_connectivity(client, max_retries=2, retry_delay=0.01) is False


@pytest.mark.asyncio
async def test_remove_deadmans_switch() -> None:
    client = AsyncMock()
    client.get.return_value = [{".id": "*sched1", "name": "my-job"}]
    assert await remove_deadmans_switch(client, "my-job") is True
    client.delete.assert_awaited_once_with("/system/scheduler/*sched1")

    # Not found case
    client.get.return_value = []
    assert await remove_deadmans_switch(client, "not-found") is False


@pytest.mark.asyncio
async def test_execute_with_safemode_success() -> None:
    client = AsyncMock()
    client.get.side_effect = [
        {"name": "AliveRouter"},  # verify_connectivity
        [{".id": "*sched1", "name": "rosgrid-safemode-1"}],  # remove_deadmans_switch
    ]
    client.put.return_value = {".id": "*sched1"}

    async def sample_mutation() -> str:
        return "MUTATION_DONE"

    result = await execute_with_safemode(
        client=client,
        rollback_cli="/interface/set ether1 disabled=no",
        operation_fn=sample_mutation,
        job_name="rosgrid-safemode-1",
    )
    assert result == "MUTATION_DONE"
    client.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_with_safemode_loss_of_connectivity() -> None:
    client = AsyncMock()
    # verify_connectivity fails
    client.get.side_effect = Exception("Network down")

    async def suicidal_mutation() -> None:
        pass

    with pytest.raises(SafeModeRollbackTriggeredError) as exc_info:
        await execute_with_safemode(
            client=client,
            rollback_cli="/interface/set ether1 disabled=no",
            operation_fn=suicidal_mutation,
            interval_seconds=60,
            job_name="rosgrid-safemode-loss",
        )
    assert "rosgrid-safemode-loss" in str(exc_info.value)
