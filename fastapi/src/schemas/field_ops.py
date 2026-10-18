# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.models.ipam import FiberCutStatusEnum, FieldOrderStatusEnum


class FieldOrderCreate(BaseModel):
    customer_service_id: uuid.UUID
    assigned_tech_id: Optional[uuid.UUID] = None
    notes: Optional[str] = None


class FieldOrderUpdate(BaseModel):
    assigned_tech_id: Optional[uuid.UUID] = None
    status: Optional[FieldOrderStatusEnum] = None
    onu_scanned_serial: Optional[str] = None
    onu_scanned_mac: Optional[str] = None
    detected_mode: Optional[str] = None
    notes: Optional[str] = None


class FieldOrderResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_service_id: uuid.UUID
    assigned_tech_id: Optional[uuid.UUID]
    status: FieldOrderStatusEnum
    onu_scanned_serial: Optional[str]
    onu_scanned_mac: Optional[str]
    detected_mode: Optional[str]
    ping_avg_ms: Optional[Decimal]
    ping_loss_pct: Optional[Decimal]
    traffic_rx_kbps: Optional[Decimal]
    traffic_tx_kbps: Optional[Decimal]
    tech_latitude: Optional[Decimal]
    tech_longitude: Optional[Decimal]
    customer_signature_svg: Optional[str]
    notes: Optional[str]
    certified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FieldVerifySubscriberRequest(BaseModel):
    customer_service_id: uuid.UUID
    onu_scanned_serial: Optional[str] = None
    onu_scanned_mac: Optional[str] = None


class FieldVerifySubscriberResponse(BaseModel):
    customer_service_id: uuid.UUID
    session_active: bool
    connection_type: str = "PPPOE"
    uptime_seconds: int = 0
    assigned_ipv4: Optional[str] = None
    assigned_ipv6_prefix: Optional[str] = None
    detected_mac: Optional[str] = None
    detected_mode: str = "UNKNOWN"
    ping_success: bool = False
    ping_avg_ms: Optional[Decimal] = None
    ping_loss_pct: Decimal = Decimal("0.00")
    traffic_rx_kbps: Decimal = Decimal("0.00")
    traffic_tx_kbps: Decimal = Decimal("0.00")
    status_summary: str = "Verificación completada"


class FieldCertifyOrderRequest(BaseModel):
    order_id: uuid.UUID
    onu_scanned_serial: str = Field(..., min_length=4)
    onu_scanned_mac: Optional[str] = None
    tech_latitude: Optional[Decimal] = None
    tech_longitude: Optional[Decimal] = None
    customer_signature_svg: Optional[str] = None
    notes: Optional[str] = None


class FiberCutIncidentResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    router_id: uuid.UUID
    pon_port: str
    optical_box: Optional[str]
    affected_onus_count: int
    status: FiberCutStatusEnum
    incident_summary: str
    detected_at: datetime
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
