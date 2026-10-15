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


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_evaluate_role_permission__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_evaluate_role_permission__mutmut)
def evaluate_role_permission(role: SystemRoleEnum, action: str) -> str:
    return POLICY_MATRIX.get(role, {}).get(action, DENY)


def x_evaluate_role_permission__mutmut_orig(role: SystemRoleEnum, action: str) -> str:
    return POLICY_MATRIX.get(role, {}).get(action, DENY)


def x_evaluate_role_permission__mutmut_1(role: SystemRoleEnum, action: str) -> str:
    return POLICY_MATRIX.get(role, {}).get(None, DENY)


def x_evaluate_role_permission__mutmut_2(role: SystemRoleEnum, action: str) -> str:
    return POLICY_MATRIX.get(role, {}).get(action, None)


def x_evaluate_role_permission__mutmut_3(role: SystemRoleEnum, action: str) -> str:
    return POLICY_MATRIX.get(role, {}).get(DENY)


def x_evaluate_role_permission__mutmut_4(role: SystemRoleEnum, action: str) -> str:
    return POLICY_MATRIX.get(role, {}).get(action, )


def x_evaluate_role_permission__mutmut_5(role: SystemRoleEnum, action: str) -> str:
    return POLICY_MATRIX.get(None, {}).get(action, DENY)


def x_evaluate_role_permission__mutmut_6(role: SystemRoleEnum, action: str) -> str:
    return POLICY_MATRIX.get(role, None).get(action, DENY)


def x_evaluate_role_permission__mutmut_7(role: SystemRoleEnum, action: str) -> str:
    return POLICY_MATRIX.get({}).get(action, DENY)


def x_evaluate_role_permission__mutmut_8(role: SystemRoleEnum, action: str) -> str:
    return POLICY_MATRIX.get(role, ).get(action, DENY)

mutants_x_evaluate_role_permission__mutmut['_mutmut_orig'] = x_evaluate_role_permission__mutmut_orig # type: ignore # mutmut generated
mutants_x_evaluate_role_permission__mutmut['x_evaluate_role_permission__mutmut_1'] = x_evaluate_role_permission__mutmut_1 # type: ignore # mutmut generated
mutants_x_evaluate_role_permission__mutmut['x_evaluate_role_permission__mutmut_2'] = x_evaluate_role_permission__mutmut_2 # type: ignore # mutmut generated
mutants_x_evaluate_role_permission__mutmut['x_evaluate_role_permission__mutmut_3'] = x_evaluate_role_permission__mutmut_3 # type: ignore # mutmut generated
mutants_x_evaluate_role_permission__mutmut['x_evaluate_role_permission__mutmut_4'] = x_evaluate_role_permission__mutmut_4 # type: ignore # mutmut generated
mutants_x_evaluate_role_permission__mutmut['x_evaluate_role_permission__mutmut_5'] = x_evaluate_role_permission__mutmut_5 # type: ignore # mutmut generated
mutants_x_evaluate_role_permission__mutmut['x_evaluate_role_permission__mutmut_6'] = x_evaluate_role_permission__mutmut_6 # type: ignore # mutmut generated
mutants_x_evaluate_role_permission__mutmut['x_evaluate_role_permission__mutmut_7'] = x_evaluate_role_permission__mutmut_7 # type: ignore # mutmut generated
mutants_x_evaluate_role_permission__mutmut['x_evaluate_role_permission__mutmut_8'] = x_evaluate_role_permission__mutmut_8 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_verify_router_access__mutmut)
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


def x_verify_router_access__mutmut_orig(
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


def x_verify_router_access__mutmut_1(
    user_role: SystemRoleEnum,
    has_all_routers: bool,
    permission: Any | None,
    action: str,
) -> str:
    base_policy = None
    if base_policy == DENY:
        return DENY

    if user_role in _GLOBAL_ACCESS_ROLES or has_all_routers:
        return base_policy

    if permission is None or not getattr(permission, "can_read", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_2(
    user_role: SystemRoleEnum,
    has_all_routers: bool,
    permission: Any | None,
    action: str,
) -> str:
    base_policy = evaluate_role_permission(None, action)
    if base_policy == DENY:
        return DENY

    if user_role in _GLOBAL_ACCESS_ROLES or has_all_routers:
        return base_policy

    if permission is None or not getattr(permission, "can_read", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_3(
    user_role: SystemRoleEnum,
    has_all_routers: bool,
    permission: Any | None,
    action: str,
) -> str:
    base_policy = evaluate_role_permission(user_role, None)
    if base_policy == DENY:
        return DENY

    if user_role in _GLOBAL_ACCESS_ROLES or has_all_routers:
        return base_policy

    if permission is None or not getattr(permission, "can_read", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_4(
    user_role: SystemRoleEnum,
    has_all_routers: bool,
    permission: Any | None,
    action: str,
) -> str:
    base_policy = evaluate_role_permission(action)
    if base_policy == DENY:
        return DENY

    if user_role in _GLOBAL_ACCESS_ROLES or has_all_routers:
        return base_policy

    if permission is None or not getattr(permission, "can_read", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_5(
    user_role: SystemRoleEnum,
    has_all_routers: bool,
    permission: Any | None,
    action: str,
) -> str:
    base_policy = evaluate_role_permission(user_role, )
    if base_policy == DENY:
        return DENY

    if user_role in _GLOBAL_ACCESS_ROLES or has_all_routers:
        return base_policy

    if permission is None or not getattr(permission, "can_read", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_6(
    user_role: SystemRoleEnum,
    has_all_routers: bool,
    permission: Any | None,
    action: str,
) -> str:
    base_policy = evaluate_role_permission(user_role, action)
    if base_policy != DENY:
        return DENY

    if user_role in _GLOBAL_ACCESS_ROLES or has_all_routers:
        return base_policy

    if permission is None or not getattr(permission, "can_read", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_7(
    user_role: SystemRoleEnum,
    has_all_routers: bool,
    permission: Any | None,
    action: str,
) -> str:
    base_policy = evaluate_role_permission(user_role, action)
    if base_policy == DENY:
        return DENY

    if user_role in _GLOBAL_ACCESS_ROLES and has_all_routers:
        return base_policy

    if permission is None or not getattr(permission, "can_read", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_8(
    user_role: SystemRoleEnum,
    has_all_routers: bool,
    permission: Any | None,
    action: str,
) -> str:
    base_policy = evaluate_role_permission(user_role, action)
    if base_policy == DENY:
        return DENY

    if user_role not in _GLOBAL_ACCESS_ROLES or has_all_routers:
        return base_policy

    if permission is None or not getattr(permission, "can_read", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_9(
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

    if permission is None and not getattr(permission, "can_read", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_10(
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

    if permission is not None or not getattr(permission, "can_read", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_11(
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

    if permission is None or getattr(permission, "can_read", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_12(
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

    if permission is None or not getattr(None, "can_read", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_13(
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

    if permission is None or not getattr(permission, None, True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_14(
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

    if permission is None or not getattr(permission, "can_read", None):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_15(
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

    if permission is None or not getattr("can_read", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_16(
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

    if permission is None or not getattr(permission, True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_17(
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

    if permission is None or not getattr(permission, "can_read", ):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_18(
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

    if permission is None or not getattr(permission, "XXcan_readXX", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_19(
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

    if permission is None or not getattr(permission, "CAN_READ", True):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_20(
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

    if permission is None or not getattr(permission, "can_read", False):
        return DENY

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_21(
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

    if base_policy == MAKER_CHECKER or getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_22(
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

    if base_policy != MAKER_CHECKER and getattr(permission, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_23(
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

    if base_policy == MAKER_CHECKER and getattr(None, "bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_24(
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

    if base_policy == MAKER_CHECKER and getattr(permission, None, False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_25(
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

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", None):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_26(
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

    if base_policy == MAKER_CHECKER and getattr("bypass_maker_checker", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_27(
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

    if base_policy == MAKER_CHECKER and getattr(permission, False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_28(
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

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", ):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_29(
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

    if base_policy == MAKER_CHECKER and getattr(permission, "XXbypass_maker_checkerXX", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_30(
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

    if base_policy == MAKER_CHECKER and getattr(permission, "BYPASS_MAKER_CHECKER", False):
        return ALLOW

    return base_policy


def x_verify_router_access__mutmut_31(
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

    if base_policy == MAKER_CHECKER and getattr(permission, "bypass_maker_checker", True):
        return ALLOW

    return base_policy

mutants_x_verify_router_access__mutmut['_mutmut_orig'] = x_verify_router_access__mutmut_orig # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_1'] = x_verify_router_access__mutmut_1 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_2'] = x_verify_router_access__mutmut_2 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_3'] = x_verify_router_access__mutmut_3 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_4'] = x_verify_router_access__mutmut_4 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_5'] = x_verify_router_access__mutmut_5 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_6'] = x_verify_router_access__mutmut_6 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_7'] = x_verify_router_access__mutmut_7 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_8'] = x_verify_router_access__mutmut_8 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_9'] = x_verify_router_access__mutmut_9 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_10'] = x_verify_router_access__mutmut_10 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_11'] = x_verify_router_access__mutmut_11 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_12'] = x_verify_router_access__mutmut_12 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_13'] = x_verify_router_access__mutmut_13 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_14'] = x_verify_router_access__mutmut_14 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_15'] = x_verify_router_access__mutmut_15 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_16'] = x_verify_router_access__mutmut_16 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_17'] = x_verify_router_access__mutmut_17 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_18'] = x_verify_router_access__mutmut_18 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_19'] = x_verify_router_access__mutmut_19 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_20'] = x_verify_router_access__mutmut_20 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_21'] = x_verify_router_access__mutmut_21 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_22'] = x_verify_router_access__mutmut_22 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_23'] = x_verify_router_access__mutmut_23 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_24'] = x_verify_router_access__mutmut_24 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_25'] = x_verify_router_access__mutmut_25 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_26'] = x_verify_router_access__mutmut_26 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_27'] = x_verify_router_access__mutmut_27 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_28'] = x_verify_router_access__mutmut_28 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_29'] = x_verify_router_access__mutmut_29 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_30'] = x_verify_router_access__mutmut_30 # type: ignore # mutmut generated
mutants_x_verify_router_access__mutmut['x_verify_router_access__mutmut_31'] = x_verify_router_access__mutmut_31 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__check_routing_critical__mutmut)
def _check_routing_critical(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("dst-address", ""))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_orig(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("dst-address", ""))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_1(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(None):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("dst-address", ""))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_2(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("XX/rest/routing/XX"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("dst-address", ""))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_3(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/REST/ROUTING/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("dst-address", ""))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_4(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return False
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("dst-address", ""))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_5(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith(None):
        dst = str(payload.get("dst-address", ""))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_6(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("XX/rest/ip/routeXX"):
        dst = str(payload.get("dst-address", ""))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_7(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/REST/IP/ROUTE"):
        dst = str(payload.get("dst-address", ""))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_8(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = None
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_9(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(None)
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_10(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get(None, ""))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_11(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("dst-address", None))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_12(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get(""))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_13(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("dst-address", ))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_14(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("XXdst-addressXX", ""))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_15(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("DST-ADDRESS", ""))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_16(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("dst-address", "XXXX"))
        return dst in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_17(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("dst-address", ""))
        return dst not in ("0.0.0.0/0", "::/0")
    return False


def x__check_routing_critical__mutmut_18(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("dst-address", ""))
        return dst in ("XX0.0.0.0/0XX", "::/0")
    return False


def x__check_routing_critical__mutmut_19(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("dst-address", ""))
        return dst in ("0.0.0.0/0", "XX::/0XX")
    return False


def x__check_routing_critical__mutmut_20(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/routing/"):
        return True
    if path.startswith("/rest/ip/route"):
        dst = str(payload.get("dst-address", ""))
        return dst in ("0.0.0.0/0", "::/0")
    return True

mutants_x__check_routing_critical__mutmut['_mutmut_orig'] = x__check_routing_critical__mutmut_orig # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_1'] = x__check_routing_critical__mutmut_1 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_2'] = x__check_routing_critical__mutmut_2 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_3'] = x__check_routing_critical__mutmut_3 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_4'] = x__check_routing_critical__mutmut_4 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_5'] = x__check_routing_critical__mutmut_5 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_6'] = x__check_routing_critical__mutmut_6 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_7'] = x__check_routing_critical__mutmut_7 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_8'] = x__check_routing_critical__mutmut_8 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_9'] = x__check_routing_critical__mutmut_9 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_10'] = x__check_routing_critical__mutmut_10 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_11'] = x__check_routing_critical__mutmut_11 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_12'] = x__check_routing_critical__mutmut_12 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_13'] = x__check_routing_critical__mutmut_13 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_14'] = x__check_routing_critical__mutmut_14 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_15'] = x__check_routing_critical__mutmut_15 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_16'] = x__check_routing_critical__mutmut_16 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_17'] = x__check_routing_critical__mutmut_17 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_18'] = x__check_routing_critical__mutmut_18 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_19'] = x__check_routing_critical__mutmut_19 # type: ignore # mutmut generated
mutants_x__check_routing_critical__mutmut['x__check_routing_critical__mutmut_20'] = x__check_routing_critical__mutmut_20 # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__check_firewall_or_service__mutmut)
def _check_firewall_or_service(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/rest/ip/firewall/filter", "/rest/ipv6/firewall/filter")):
        return payload.get("chain") == "input"
    return path.startswith("/rest/ip/service")


def x__check_firewall_or_service__mutmut_orig(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/rest/ip/firewall/filter", "/rest/ipv6/firewall/filter")):
        return payload.get("chain") == "input"
    return path.startswith("/rest/ip/service")


def x__check_firewall_or_service__mutmut_1(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(None):
        return payload.get("chain") == "input"
    return path.startswith("/rest/ip/service")


def x__check_firewall_or_service__mutmut_2(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("XX/rest/ip/firewall/filterXX", "/rest/ipv6/firewall/filter")):
        return payload.get("chain") == "input"
    return path.startswith("/rest/ip/service")


def x__check_firewall_or_service__mutmut_3(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/REST/IP/FIREWALL/FILTER", "/rest/ipv6/firewall/filter")):
        return payload.get("chain") == "input"
    return path.startswith("/rest/ip/service")


def x__check_firewall_or_service__mutmut_4(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/rest/ip/firewall/filter", "XX/rest/ipv6/firewall/filterXX")):
        return payload.get("chain") == "input"
    return path.startswith("/rest/ip/service")


def x__check_firewall_or_service__mutmut_5(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/rest/ip/firewall/filter", "/REST/IPV6/FIREWALL/FILTER")):
        return payload.get("chain") == "input"
    return path.startswith("/rest/ip/service")


def x__check_firewall_or_service__mutmut_6(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/rest/ip/firewall/filter", "/rest/ipv6/firewall/filter")):
        return payload.get(None) == "input"
    return path.startswith("/rest/ip/service")


def x__check_firewall_or_service__mutmut_7(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/rest/ip/firewall/filter", "/rest/ipv6/firewall/filter")):
        return payload.get("XXchainXX") == "input"
    return path.startswith("/rest/ip/service")


def x__check_firewall_or_service__mutmut_8(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/rest/ip/firewall/filter", "/rest/ipv6/firewall/filter")):
        return payload.get("CHAIN") == "input"
    return path.startswith("/rest/ip/service")


def x__check_firewall_or_service__mutmut_9(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/rest/ip/firewall/filter", "/rest/ipv6/firewall/filter")):
        return payload.get("chain") != "input"
    return path.startswith("/rest/ip/service")


def x__check_firewall_or_service__mutmut_10(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/rest/ip/firewall/filter", "/rest/ipv6/firewall/filter")):
        return payload.get("chain") == "XXinputXX"
    return path.startswith("/rest/ip/service")


def x__check_firewall_or_service__mutmut_11(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/rest/ip/firewall/filter", "/rest/ipv6/firewall/filter")):
        return payload.get("chain") == "INPUT"
    return path.startswith("/rest/ip/service")


def x__check_firewall_or_service__mutmut_12(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/rest/ip/firewall/filter", "/rest/ipv6/firewall/filter")):
        return payload.get("chain") == "input"
    return path.startswith(None)


def x__check_firewall_or_service__mutmut_13(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/rest/ip/firewall/filter", "/rest/ipv6/firewall/filter")):
        return payload.get("chain") == "input"
    return path.startswith("XX/rest/ip/serviceXX")


def x__check_firewall_or_service__mutmut_14(path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(("/rest/ip/firewall/filter", "/rest/ipv6/firewall/filter")):
        return payload.get("chain") == "input"
    return path.startswith("/REST/IP/SERVICE")

mutants_x__check_firewall_or_service__mutmut['_mutmut_orig'] = x__check_firewall_or_service__mutmut_orig # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut['x__check_firewall_or_service__mutmut_1'] = x__check_firewall_or_service__mutmut_1 # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut['x__check_firewall_or_service__mutmut_2'] = x__check_firewall_or_service__mutmut_2 # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut['x__check_firewall_or_service__mutmut_3'] = x__check_firewall_or_service__mutmut_3 # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut['x__check_firewall_or_service__mutmut_4'] = x__check_firewall_or_service__mutmut_4 # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut['x__check_firewall_or_service__mutmut_5'] = x__check_firewall_or_service__mutmut_5 # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut['x__check_firewall_or_service__mutmut_6'] = x__check_firewall_or_service__mutmut_6 # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut['x__check_firewall_or_service__mutmut_7'] = x__check_firewall_or_service__mutmut_7 # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut['x__check_firewall_or_service__mutmut_8'] = x__check_firewall_or_service__mutmut_8 # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut['x__check_firewall_or_service__mutmut_9'] = x__check_firewall_or_service__mutmut_9 # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut['x__check_firewall_or_service__mutmut_10'] = x__check_firewall_or_service__mutmut_10 # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut['x__check_firewall_or_service__mutmut_11'] = x__check_firewall_or_service__mutmut_11 # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut['x__check_firewall_or_service__mutmut_12'] = x__check_firewall_or_service__mutmut_12 # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut['x__check_firewall_or_service__mutmut_13'] = x__check_firewall_or_service__mutmut_13 # type: ignore # mutmut generated
mutants_x__check_firewall_or_service__mutmut['x__check_firewall_or_service__mutmut_14'] = x__check_firewall_or_service__mutmut_14 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__check_interface_or_ip__mutmut)
def _check_interface_or_ip(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get("disabled") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_orig(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get("disabled") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_1(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith(None):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get("disabled") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_2(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("XX/rest/ip/addressXX"):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get("disabled") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_3(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/REST/IP/ADDRESS"):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get("disabled") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_4(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return False
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get("disabled") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_5(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith(None):
        return method == "DELETE" or payload.get("disabled") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_6(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("XX/rest/interfaceXX"):
        return method == "DELETE" or payload.get("disabled") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_7(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/REST/INTERFACE"):
        return method == "DELETE" or payload.get("disabled") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_8(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" and payload.get("disabled") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_9(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method != "DELETE" or payload.get("disabled") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_10(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method == "XXDELETEXX" or payload.get("disabled") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_11(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method == "delete" or payload.get("disabled") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_12(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get(None) in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_13(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get("XXdisabledXX") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_14(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get("DISABLED") in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_15(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get("disabled") not in ("true", True)
    return False


def x__check_interface_or_ip__mutmut_16(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get("disabled") in ("XXtrueXX", True)
    return False


def x__check_interface_or_ip__mutmut_17(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get("disabled") in ("TRUE", True)
    return False


def x__check_interface_or_ip__mutmut_18(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get("disabled") in ("true", False)
    return False


def x__check_interface_or_ip__mutmut_19(method: str, path: str, payload: dict[str, Any]) -> bool:
    if path.startswith("/rest/ip/address"):
        return True
    if path.startswith("/rest/interface"):
        return method == "DELETE" or payload.get("disabled") in ("true", True)
    return True

mutants_x__check_interface_or_ip__mutmut['_mutmut_orig'] = x__check_interface_or_ip__mutmut_orig # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_1'] = x__check_interface_or_ip__mutmut_1 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_2'] = x__check_interface_or_ip__mutmut_2 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_3'] = x__check_interface_or_ip__mutmut_3 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_4'] = x__check_interface_or_ip__mutmut_4 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_5'] = x__check_interface_or_ip__mutmut_5 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_6'] = x__check_interface_or_ip__mutmut_6 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_7'] = x__check_interface_or_ip__mutmut_7 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_8'] = x__check_interface_or_ip__mutmut_8 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_9'] = x__check_interface_or_ip__mutmut_9 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_10'] = x__check_interface_or_ip__mutmut_10 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_11'] = x__check_interface_or_ip__mutmut_11 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_12'] = x__check_interface_or_ip__mutmut_12 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_13'] = x__check_interface_or_ip__mutmut_13 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_14'] = x__check_interface_or_ip__mutmut_14 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_15'] = x__check_interface_or_ip__mutmut_15 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_16'] = x__check_interface_or_ip__mutmut_16 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_17'] = x__check_interface_or_ip__mutmut_17 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_18'] = x__check_interface_or_ip__mutmut_18 # type: ignore # mutmut generated
mutants_x__check_interface_or_ip__mutmut['x__check_interface_or_ip__mutmut_19'] = x__check_interface_or_ip__mutmut_19 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_classify_critical_mikrotik_operation__mutmut)
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


def x_classify_critical_mikrotik_operation__mutmut_orig(
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


def x_classify_critical_mikrotik_operation__mutmut_1(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = None
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


def x_classify_critical_mikrotik_operation__mutmut_2(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload and {}
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


def x_classify_critical_mikrotik_operation__mutmut_3(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = None

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


def x_classify_critical_mikrotik_operation__mutmut_4(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().upper()

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


def x_classify_critical_mikrotik_operation__mutmut_5(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path not in ("/rest/system/reboot", "/rest/system/shutdown", "/rest/system/reset-configuration"):
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


def x_classify_critical_mikrotik_operation__mutmut_6(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("XX/rest/system/rebootXX", "/rest/system/shutdown", "/rest/system/reset-configuration"):
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


def x_classify_critical_mikrotik_operation__mutmut_7(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("/REST/SYSTEM/REBOOT", "/rest/system/shutdown", "/rest/system/reset-configuration"):
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


def x_classify_critical_mikrotik_operation__mutmut_8(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("/rest/system/reboot", "XX/rest/system/shutdownXX", "/rest/system/reset-configuration"):
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


def x_classify_critical_mikrotik_operation__mutmut_9(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("/rest/system/reboot", "/REST/SYSTEM/SHUTDOWN", "/rest/system/reset-configuration"):
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


def x_classify_critical_mikrotik_operation__mutmut_10(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("/rest/system/reboot", "/rest/system/shutdown", "XX/rest/system/reset-configurationXX"):
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


def x_classify_critical_mikrotik_operation__mutmut_11(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("/rest/system/reboot", "/rest/system/shutdown", "/REST/SYSTEM/RESET-CONFIGURATION"):
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


def x_classify_critical_mikrotik_operation__mutmut_12(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("/rest/system/reboot", "/rest/system/shutdown", "/rest/system/reset-configuration"):
        return CriticalActionTypeEnum.ROUTER_REBOOT_OR_SHUTDOWN

    if _check_routing_critical(None, data):
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


def x_classify_critical_mikrotik_operation__mutmut_13(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("/rest/system/reboot", "/rest/system/shutdown", "/rest/system/reset-configuration"):
        return CriticalActionTypeEnum.ROUTER_REBOOT_OR_SHUTDOWN

    if _check_routing_critical(clean_path, None):
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


def x_classify_critical_mikrotik_operation__mutmut_14(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("/rest/system/reboot", "/rest/system/shutdown", "/rest/system/reset-configuration"):
        return CriticalActionTypeEnum.ROUTER_REBOOT_OR_SHUTDOWN

    if _check_routing_critical(data):
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


def x_classify_critical_mikrotik_operation__mutmut_15(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("/rest/system/reboot", "/rest/system/shutdown", "/rest/system/reset-configuration"):
        return CriticalActionTypeEnum.ROUTER_REBOOT_OR_SHUTDOWN

    if _check_routing_critical(clean_path, ):
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


def x_classify_critical_mikrotik_operation__mutmut_16(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("/rest/system/reboot", "/rest/system/shutdown", "/rest/system/reset-configuration"):
        return CriticalActionTypeEnum.ROUTER_REBOOT_OR_SHUTDOWN

    if _check_routing_critical(clean_path, data):
        return CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE

    if _check_firewall_or_service(None, data):
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


def x_classify_critical_mikrotik_operation__mutmut_17(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("/rest/system/reboot", "/rest/system/shutdown", "/rest/system/reset-configuration"):
        return CriticalActionTypeEnum.ROUTER_REBOOT_OR_SHUTDOWN

    if _check_routing_critical(clean_path, data):
        return CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE

    if _check_firewall_or_service(clean_path, None):
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


def x_classify_critical_mikrotik_operation__mutmut_18(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("/rest/system/reboot", "/rest/system/shutdown", "/rest/system/reset-configuration"):
        return CriticalActionTypeEnum.ROUTER_REBOOT_OR_SHUTDOWN

    if _check_routing_critical(clean_path, data):
        return CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE

    if _check_firewall_or_service(data):
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


def x_classify_critical_mikrotik_operation__mutmut_19(
    method: str, ros_path: str, payload: dict[str, Any] | None = None
) -> CriticalActionTypeEnum | None:
    data = payload or {}
    clean_path = ros_path.strip().lower()

    if clean_path in ("/rest/system/reboot", "/rest/system/shutdown", "/rest/system/reset-configuration"):
        return CriticalActionTypeEnum.ROUTER_REBOOT_OR_SHUTDOWN

    if _check_routing_critical(clean_path, data):
        return CriticalActionTypeEnum.ROUTING_BGP_OSPF_DEFAULT_CHANGE

    if _check_firewall_or_service(clean_path, ):
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


def x_classify_critical_mikrotik_operation__mutmut_20(
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

    if _check_interface_or_ip(None, clean_path, data):
        return CriticalActionTypeEnum.WAN_TRUNK_INTERFACE_OR_IP_CHANGE

    if clean_path in ("/rest/system/backup/load", "/rest/import") or clean_path.startswith(
        ("/rest/system/script", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_21(
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

    if _check_interface_or_ip(method, None, data):
        return CriticalActionTypeEnum.WAN_TRUNK_INTERFACE_OR_IP_CHANGE

    if clean_path in ("/rest/system/backup/load", "/rest/import") or clean_path.startswith(
        ("/rest/system/script", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_22(
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

    if _check_interface_or_ip(method, clean_path, None):
        return CriticalActionTypeEnum.WAN_TRUNK_INTERFACE_OR_IP_CHANGE

    if clean_path in ("/rest/system/backup/load", "/rest/import") or clean_path.startswith(
        ("/rest/system/script", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_23(
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

    if _check_interface_or_ip(clean_path, data):
        return CriticalActionTypeEnum.WAN_TRUNK_INTERFACE_OR_IP_CHANGE

    if clean_path in ("/rest/system/backup/load", "/rest/import") or clean_path.startswith(
        ("/rest/system/script", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_24(
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

    if _check_interface_or_ip(method, data):
        return CriticalActionTypeEnum.WAN_TRUNK_INTERFACE_OR_IP_CHANGE

    if clean_path in ("/rest/system/backup/load", "/rest/import") or clean_path.startswith(
        ("/rest/system/script", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_25(
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

    if _check_interface_or_ip(method, clean_path, ):
        return CriticalActionTypeEnum.WAN_TRUNK_INTERFACE_OR_IP_CHANGE

    if clean_path in ("/rest/system/backup/load", "/rest/import") or clean_path.startswith(
        ("/rest/system/script", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_26(
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

    if clean_path in ("/rest/system/backup/load", "/rest/import") and clean_path.startswith(
        ("/rest/system/script", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_27(
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

    if clean_path not in ("/rest/system/backup/load", "/rest/import") or clean_path.startswith(
        ("/rest/system/script", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_28(
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

    if clean_path in ("XX/rest/system/backup/loadXX", "/rest/import") or clean_path.startswith(
        ("/rest/system/script", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_29(
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

    if clean_path in ("/REST/SYSTEM/BACKUP/LOAD", "/rest/import") or clean_path.startswith(
        ("/rest/system/script", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_30(
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

    if clean_path in ("/rest/system/backup/load", "XX/rest/importXX") or clean_path.startswith(
        ("/rest/system/script", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_31(
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

    if clean_path in ("/rest/system/backup/load", "/REST/IMPORT") or clean_path.startswith(
        ("/rest/system/script", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_32(
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
        None
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_33(
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
        ("XX/rest/system/scriptXX", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_34(
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
        ("/REST/SYSTEM/SCRIPT", "/rest/system/scheduler")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_35(
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
        ("/rest/system/script", "XX/rest/system/schedulerXX")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_36(
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
        ("/rest/system/script", "/REST/SYSTEM/SCHEDULER")
    ):
        return CriticalActionTypeEnum.BACKUP_RESTORE_OR_CUSTOM_SCRIPT

    if clean_path.startswith("/rest/user"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_37(
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

    if clean_path.startswith(None):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_38(
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

    if clean_path.startswith("XX/rest/userXX"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None


def x_classify_critical_mikrotik_operation__mutmut_39(
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

    if clean_path.startswith("/REST/USER"):
        return CriticalActionTypeEnum.ROUTER_INTERNAL_USER_CHANGE

    return None

mutants_x_classify_critical_mikrotik_operation__mutmut['_mutmut_orig'] = x_classify_critical_mikrotik_operation__mutmut_orig # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_1'] = x_classify_critical_mikrotik_operation__mutmut_1 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_2'] = x_classify_critical_mikrotik_operation__mutmut_2 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_3'] = x_classify_critical_mikrotik_operation__mutmut_3 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_4'] = x_classify_critical_mikrotik_operation__mutmut_4 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_5'] = x_classify_critical_mikrotik_operation__mutmut_5 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_6'] = x_classify_critical_mikrotik_operation__mutmut_6 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_7'] = x_classify_critical_mikrotik_operation__mutmut_7 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_8'] = x_classify_critical_mikrotik_operation__mutmut_8 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_9'] = x_classify_critical_mikrotik_operation__mutmut_9 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_10'] = x_classify_critical_mikrotik_operation__mutmut_10 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_11'] = x_classify_critical_mikrotik_operation__mutmut_11 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_12'] = x_classify_critical_mikrotik_operation__mutmut_12 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_13'] = x_classify_critical_mikrotik_operation__mutmut_13 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_14'] = x_classify_critical_mikrotik_operation__mutmut_14 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_15'] = x_classify_critical_mikrotik_operation__mutmut_15 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_16'] = x_classify_critical_mikrotik_operation__mutmut_16 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_17'] = x_classify_critical_mikrotik_operation__mutmut_17 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_18'] = x_classify_critical_mikrotik_operation__mutmut_18 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_19'] = x_classify_critical_mikrotik_operation__mutmut_19 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_20'] = x_classify_critical_mikrotik_operation__mutmut_20 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_21'] = x_classify_critical_mikrotik_operation__mutmut_21 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_22'] = x_classify_critical_mikrotik_operation__mutmut_22 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_23'] = x_classify_critical_mikrotik_operation__mutmut_23 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_24'] = x_classify_critical_mikrotik_operation__mutmut_24 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_25'] = x_classify_critical_mikrotik_operation__mutmut_25 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_26'] = x_classify_critical_mikrotik_operation__mutmut_26 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_27'] = x_classify_critical_mikrotik_operation__mutmut_27 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_28'] = x_classify_critical_mikrotik_operation__mutmut_28 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_29'] = x_classify_critical_mikrotik_operation__mutmut_29 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_30'] = x_classify_critical_mikrotik_operation__mutmut_30 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_31'] = x_classify_critical_mikrotik_operation__mutmut_31 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_32'] = x_classify_critical_mikrotik_operation__mutmut_32 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_33'] = x_classify_critical_mikrotik_operation__mutmut_33 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_34'] = x_classify_critical_mikrotik_operation__mutmut_34 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_35'] = x_classify_critical_mikrotik_operation__mutmut_35 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_36'] = x_classify_critical_mikrotik_operation__mutmut_36 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_37'] = x_classify_critical_mikrotik_operation__mutmut_37 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_38'] = x_classify_critical_mikrotik_operation__mutmut_38 # type: ignore # mutmut generated
mutants_x_classify_critical_mikrotik_operation__mutmut['x_classify_critical_mikrotik_operation__mutmut_39'] = x_classify_critical_mikrotik_operation__mutmut_39 # type: ignore # mutmut generated
