# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from types import SimpleNamespace

from src.models.core import SystemRoleEnum
from src.models.operations import CriticalActionTypeEnum
from src.rbac.checker import (
    classify_critical_mikrotik_operation,
    verify_router_access,
)
from src.rbac.policy_matrix import ALLOW, DENY, MAKER_CHECKER


def test_verify_router_access_base_deny_prevails() -> None:
    perm = SimpleNamespace(can_read=True, can_write=True, bypass_maker_checker=True)
    res = verify_router_access(SystemRoleEnum.NOC_MONITOR, False, perm, "CRITICAL_NETWORK_ACTIONS")
    assert res == DENY


def test_verify_router_access_global_roles_bypass_specific_checks() -> None:
    res = verify_router_access(SystemRoleEnum.SUPERADMIN_GLOBAL, False, None, "ROUTER_INVENTORY_CSV")
    assert res == ALLOW


def test_verify_router_access_has_all_routers() -> None:
    res = verify_router_access(SystemRoleEnum.SUPPORT_L1, True, None, "L1_OPERATIONS")
    assert res == ALLOW


def test_verify_router_access_missing_or_no_read_permission() -> None:
    assert verify_router_access(SystemRoleEnum.SUPPORT_L1, False, None, "L1_OPERATIONS") == DENY

    no_read_perm = SimpleNamespace(can_read=False, bypass_maker_checker=False)
    assert verify_router_access(SystemRoleEnum.SUPPORT_L1, False, no_read_perm, "L1_OPERATIONS") == DENY


def test_verify_router_access_maker_checker_bypass() -> None:
    perm_standard = SimpleNamespace(can_read=True, bypass_maker_checker=False)
    res1 = verify_router_access(SystemRoleEnum.SUPPORT_L2, False, perm_standard, "REBOOT_SHUTDOWN")
    assert res1 == MAKER_CHECKER

    perm_bypass = SimpleNamespace(can_read=True, bypass_maker_checker=True)
    res2 = verify_router_access(SystemRoleEnum.SUPPORT_L2, False, perm_bypass, "REBOOT_SHUTDOWN")
    assert res2 == ALLOW


def test_classify_critical_operations_reboot_shutdown() -> None:
    for path in ("/rest/system/reboot", "/rest/system/shutdown", "/rest/system/reset-configuration"):
        res = classify_critical_mikrotik_operation("POST", path)
        assert res == CriticalActionTypeEnum.ROUTER_REBOOT_OR_SHUTDOWN


def test_classify_critical_operations_routing() -> None:
    # BGP path
    assert classify_critical_mikrotik_operation("POST", "/rest/routing/bgp/connection") == (
        CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE
    )
    # Default route 0.0.0.0/0
    assert (
        classify_critical_mikrotik_operation(
            "POST", "/rest/ip/route", {"dst-address": "0.0.0.0/0", "gateway": "1.1.1.1"}
        )
        == CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE
    )

    # Non-default route is not critical
    assert (
        classify_critical_mikrotik_operation(
            "POST", "/rest/ip/route", {"dst-address": "10.0.0.0/24", "gateway": "1.1.1.1"}
        )
        is None
    )


def test_classify_critical_operations_firewall_and_service() -> None:
    # Input chain is critical
    assert (
        classify_critical_mikrotik_operation("POST", "/rest/ip/firewall/filter", {"chain": "input", "action": "drop"})
        == CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE
    )

    # Forward chain is not critical under this signature
    assert (
        classify_critical_mikrotik_operation(
            "POST", "/rest/ip/firewall/filter", {"chain": "forward", "action": "accept"}
        )
        is None
    )

    # IP service modification (ssh, www-ssl, api)
    assert (
        classify_critical_mikrotik_operation("PATCH", "/rest/ip/service/www-ssl", {"port": "8443"})
        == CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE
    )


def test_classify_critical_operations_interfaces_and_ips() -> None:
    # Any IP address modification
    assert (
        classify_critical_mikrotik_operation("POST", "/rest/ip/address", {"address": "192.168.10.1/24"})
        == CriticalActionTypeEnum.WAN_TRUNK_INTERFACE_OR_IP_CHANGE
    )

    # Interface delete
    assert (
        classify_critical_mikrotik_operation("DELETE", "/rest/interface/ether1")
        == CriticalActionTypeEnum.WAN_TRUNK_INTERFACE_OR_IP_CHANGE
    )

    # Interface disable
    assert (
        classify_critical_mikrotik_operation("PATCH", "/rest/interface/ether1", {"disabled": "true"})
        == CriticalActionTypeEnum.WAN_TRUNK_INTERFACE_OR_IP_CHANGE
    )

    # Interface normal modification (comment) is not critical
    assert classify_critical_mikrotik_operation("PATCH", "/rest/interface/ether1", {"comment": "WAN link"}) is None


def test_classify_critical_operations_backup_restore_and_users() -> None:
    assert classify_critical_mikrotik_operation("POST", "/rest/system/backup/load") == (
        CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT
    )
    assert classify_critical_mikrotik_operation("POST", "/rest/system/script/run") == (
        CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT
    )
    assert classify_critical_mikrotik_operation("POST", "/rest/user/add") == (
        CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE
    )


def test_classify_non_critical_operation() -> None:
    assert classify_critical_mikrotik_operation("GET", "/rest/system/resource") is None
    assert classify_critical_mikrotik_operation("PATCH", "/rest/system/identity", {"name": "Core-R1"}) is None
