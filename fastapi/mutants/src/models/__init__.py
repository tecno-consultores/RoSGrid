# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from src.models.base import Base
from src.models.core import SystemRoleEnum, Tenant, TenantStatusEnum, User, UserRouterPermission
from src.models.inventory import (
    MaintenanceWindow,
    Router,
    RouterAdminStateEnum,
    RouterCredentialsVault,
    RouterNetworkRoleEnum,
    RouterTag,
    SSLTrustStatusEnum,
)
from src.models.operations import (
    AlertChannelTypeEnum,
    ApprovalRequest,
    ApprovalStatusEnum,
    AuditLog,
    BulkJob,
    BulkJobItem,
    BulkJobStatusEnum,
    ConfigTemplate,
    CriticalActionTypeEnum,
    NotificationChannel,
    RouterBackup,
)

__all__ = [
    "AlertChannelTypeEnum",
    "ApprovalRequest",
    "ApprovalStatusEnum",
    "AuditLog",
    "Base",
    "BulkJob",
    "BulkJobItem",
    "BulkJobStatusEnum",
    "ConfigTemplate",
    "CriticalActionTypeEnum",
    "MaintenanceWindow",
    "NotificationChannel",
    "Router",
    "RouterAdminStateEnum",
    "RouterBackup",
    "RouterCredentialsVault",
    "RouterNetworkRoleEnum",
    "RouterTag",
    "SSLTrustStatusEnum",
    "SystemRoleEnum",
    "Tenant",
    "TenantStatusEnum",
    "User",
    "UserRouterPermission",
]


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
