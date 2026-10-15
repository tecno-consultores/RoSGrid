# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from typing import Any

from src.models.core import SystemRoleEnum
from src.models.operations import CriticalActionTypeEnum
from src.rbac.policy_matrix import ALLOW, DENY, MAKER_CHECKER, POLICY_MATRIX

_GLOBAL_ACCESS_ROLES = {
    SystemRoleEnum.SUPERADMIN_GLOBAL,
    SystemRoleEnum.TENANT_ADMIN,
    SystemRoleEnum.SUPERVISOR,
    SystemRoleEnum.INVENTORY_MANAGER,
    SystemRoleEnum.AUDITOR,
    SystemRoleEnum.NOC_MONITOR,
}


def evaluate_role_permission(role: SystemRoleEnum, action: str) -> str:
    return POLICY_MATRIX.get(role, {}).get(action, DENY)


def verify_router_access(
    user_role: SystemRoleEnum,
    has_all_routers: bool,
    permission: Any | None,
    action: str,
) -> str:
    base_policy = evaluate_role_permission(user_role, action)
    if base_policy == DENY:
        return DENY

    if user_role in _GLOBAL_ACCESS_ROLES or has_all_routers:
        return base_policy

    if permission is None or not getattr(permission, "can_read", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def _check_routing_critical(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("dst-address", ""))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def _check_firewall_or_service(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/rest/ip/firewall/filter", "/rest/ipv6/firewall/filter")):
        return payload.get("chain") == "input"
    return path.startswith("/rest/ip/service")


def _check_interface_or_ip(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get("disabled") in ("true", True)
    return False


def classify_critical_mikrotik_operation(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("/rest/system/reboot", "/rest/system/shutdown", "/rest/system/reset-configuration"):
        return CriticalActionTypeEnum.ROUTER_REBOOT_OR_SHUTDOWN

    if _check_routing_critical(clean_path, data):
        return CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE

    if _check_firewall_or_service(clean_path, data):
        return CriticalActionTypeEnum.FIREWALL_INPUT_OR_SERVICE_PORT_CHANGE

    if _check_interface_or_ip(method, clean_path, data):
        return CriticalActionTypeEnum.WAN_TRUNK_INTERFACE_OR_IP_CHANGE

    if clean_path in ("/rest/system/backup/load", "/rest/import") or clean_path.startswith(
        ("/rest/system/script", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None
