# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

from fastapi import APIRouter

from src.api.v1.approvals import router as approvals_router
from src.api.v1.audit import router as audit_router
from src.api.v1.auth import router as auth_router
from src.api.v1.backups import router as backups_router
from src.api.v1.bgp_looking_glass import router as bgp_looking_glass_router
from src.api.v1.bulk_and_updates import router as bulk_updates_router
from src.api.v1.compliance import router as compliance_router
from src.api.v1.diagnostics_360 import router as diagnostics_360_router
from src.api.v1.field_ops import router as field_ops_router
from src.api.v1.inventory import router as inventory_router
from src.api.v1.ipam import router as ipam_router
from src.api.v1.maintenance import router as maintenance_router
from src.api.v1.mcp import router as mcp_router
from src.api.v1.network_services import router as network_services_router
from src.api.v1.notification_channels import router as notification_channels_router
from src.api.v1.rbac import router as rbac_router
from src.api.v1.sdwan import router as sdwan_router
from src.api.v1.sessions import router as sessions_router
from src.api.v1.sla import router as sla_router
from src.api.v1.subscribers import bandwidth_router, subscribers_router
from src.api.v1.switching import router as switching_router
from src.api.v1.tenants import router as tenants_router
from src.api.v1.traffic_flow import router as traffic_flow_router
from src.api.v1.users import router as users_router
from src.api.v1.vault import router as vault_router
from src.api.v1.webfig_firewall import router as webfig_firewall_router
from src.api.v1.webfig_interfaces import router as webfig_interfaces_router
from src.api.v1.webfig_ip import router as webfig_ip_router
from src.api.v1.webfig_layer2 import router as webfig_layer2_router
from src.api.v1.webfig_ppp import router as webfig_ppp_router
from src.api.v1.webfig_queues import router as webfig_queues_router
from src.api.v1.webfig_routing import router as webfig_routing_router
from src.api.v1.webfig_system_tools import (
    system_router as webfig_system_router,
)
from src.api.v1.webfig_system_tools import (
    tools_router as webfig_tools_router,
)
from src.api.v1.wifi import router as wifi_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(tenants_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(inventory_router)
api_v1_router.include_router(ipam_router)
api_v1_router.include_router(bandwidth_router)
api_v1_router.include_router(subscribers_router)
api_v1_router.include_router(network_services_router)
api_v1_router.include_router(field_ops_router)
api_v1_router.include_router(vault_router)
api_v1_router.include_router(maintenance_router)
api_v1_router.include_router(webfig_interfaces_router)
api_v1_router.include_router(webfig_ip_router)
api_v1_router.include_router(webfig_firewall_router)
api_v1_router.include_router(webfig_routing_router)
api_v1_router.include_router(webfig_ppp_router)
api_v1_router.include_router(webfig_queues_router)
api_v1_router.include_router(webfig_system_router)
api_v1_router.include_router(webfig_tools_router)
api_v1_router.include_router(webfig_layer2_router)
api_v1_router.include_router(approvals_router)
api_v1_router.include_router(backups_router)
api_v1_router.include_router(bulk_updates_router)
api_v1_router.include_router(notification_channels_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(mcp_router)
api_v1_router.include_router(rbac_router)
api_v1_router.include_router(diagnostics_360_router)
api_v1_router.include_router(bgp_looking_glass_router)
api_v1_router.include_router(traffic_flow_router)
api_v1_router.include_router(compliance_router)
api_v1_router.include_router(sdwan_router)
api_v1_router.include_router(switching_router)
api_v1_router.include_router(sla_router)
api_v1_router.include_router(wifi_router)
