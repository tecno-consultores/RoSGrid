# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import pytest

from src.models.core import SystemRoleEnum
from src.rbac.checker import evaluate_role_permission
from src.rbac.policy_matrix import ALLOW, DENY, MAKER_CHECKER, POLICY_MATRIX, READ_ONLY

ALL_ACTIONS = [
    "TENANT_MANAGEMENT",
    "USER_MANAGEMENT",
    "VIEW_ACTIVE_SESSIONS_KILLSWITCH",
    "ROUTER_INVENTORY_CSV",
    "REVEAL_VAULT_KEYS",
    "TRIGGER_PASSWORD_ROTATION",
    "SCHEDULE_MAINTENANCE",
    "VIEW_OSM_MAP_NOC_CHARTS",
    "LIVE_DIAGNOSTICS",
    "L1_OPERATIONS",
    "CONFIG_STANDARD_L1",
    "CRITICAL_NETWORK_ACTIONS",
    "REBOOT_SHUTDOWN",
    "WEBFIG_L2_UNIVERSAL",
    "MANUAL_BACKUP_DIFF_GIT",
    "RESTORE_BACKUP_CUSTOM_SCRIPT",
    "BULK_ACTIONS_UPGRADE_ROS",
    "APPROVE_MAKER_CHECKER",
    "AUDIT_LOGS_QUERY",
]


def test_matrix_contains_all_11_roles() -> None:
    assert len(POLICY_MATRIX) == 11
    for role in SystemRoleEnum:
        assert role in POLICY_MATRIX
        assert len(POLICY_MATRIX[role]) == 19


@pytest.mark.parametrize("action", ALL_ACTIONS)
def test_superadmin_global_has_allow_on_all_actions(action: str) -> None:
    assert evaluate_role_permission(SystemRoleEnum.SUPERADMIN_GLOBAL, action) == ALLOW


def test_tenant_admin_cannot_manage_tenants() -> None:
    assert evaluate_role_permission(SystemRoleEnum.TENANT_ADMIN, "TENANT_MANAGEMENT") == DENY
    assert evaluate_role_permission(SystemRoleEnum.TENANT_ADMIN, "USER_MANAGEMENT") == ALLOW
    assert evaluate_role_permission(SystemRoleEnum.TENANT_ADMIN, "REVEAL_VAULT_KEYS") == ALLOW


def test_supervisor_cannot_reveal_vault_keys() -> None:
    assert evaluate_role_permission(SystemRoleEnum.SUPERVISOR, "REVEAL_VAULT_KEYS") == DENY
    assert evaluate_role_permission(SystemRoleEnum.SUPERVISOR, "USER_MANAGEMENT") == READ_ONLY
    assert evaluate_role_permission(SystemRoleEnum.SUPERVISOR, "APPROVE_MAKER_CHECKER") == ALLOW


def test_support_l2_requires_maker_checker() -> None:
    role = SystemRoleEnum.SUPPORT_L2
    assert evaluate_role_permission(role, "SCHEDULE_MAINTENANCE") == MAKER_CHECKER
    assert evaluate_role_permission(role, "CRITICAL_NETWORK_ACTIONS") == MAKER_CHECKER
    assert evaluate_role_permission(role, "REBOOT_SHUTDOWN") == MAKER_CHECKER
    assert evaluate_role_permission(role, "RESTORE_BACKUP_CUSTOM_SCRIPT") == MAKER_CHECKER
    assert evaluate_role_permission(role, "BULK_ACTIONS_UPGRADE_ROS") == MAKER_CHECKER
    assert evaluate_role_permission(role, "APPROVE_MAKER_CHECKER") == DENY


def test_auditor_permissions() -> None:
    role = SystemRoleEnum.AUDITOR
    assert evaluate_role_permission(role, "AUDIT_LOGS_QUERY") == ALLOW
    assert evaluate_role_permission(role, "USER_MANAGEMENT") == READ_ONLY
    assert evaluate_role_permission(role, "CRITICAL_NETWORK_ACTIONS") == DENY
    assert evaluate_role_permission(role, "APPROVE_MAKER_CHECKER") == DENY


def test_noc_monitor_read_only_charts() -> None:
    role = SystemRoleEnum.NOC_MONITOR
    assert evaluate_role_permission(role, "VIEW_OSM_MAP_NOC_CHARTS") == ALLOW
    assert evaluate_role_permission(role, "LIVE_DIAGNOSTICS") == DENY
    assert evaluate_role_permission(role, "REBOOT_SHUTDOWN") == DENY


def test_unknown_action_defaults_to_deny() -> None:
    assert evaluate_role_permission(SystemRoleEnum.SUPERADMIN_GLOBAL, "NON_EXISTENT_ACTION") == DENY
