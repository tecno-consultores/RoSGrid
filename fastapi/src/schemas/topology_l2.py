# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TopologyNode(BaseModel):
    id: uuid.UUID
    display_name: str
    ros_identity: str | None = None
    model_name: str | None = None
    board_name: str | None = None
    ros_version: str | None = None
    status: str = Field("ONLINE", description="ONLINE, OFFLINE o DEGRADED")
    ip_address: str
    is_pse: bool = Field(False, description="True si suministra energía PoE a otros equipos")


class TopologyEdge(BaseModel):
    id: str
    source_router_id: uuid.UUID
    source_interface: str
    target_router_id: uuid.UUID
    target_interface: str
    link_speed: str | None = None
    protocol: str = Field("MNDP", description="MNDP, LLDP o CDP")
    is_poe_delivering: bool = Field(False, description="True si este enlace entrega energía PoE al equipo destino")
    poe_power_watts: float | None = None


class L2TopologyResponse(BaseModel):
    nodes: list[TopologyNode]
    edges: list[TopologyEdge]
    total_nodes: int
    total_edges: int
    timestamp: datetime
