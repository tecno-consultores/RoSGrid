# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para la Consola BGP Looking Glass Interno (Hito 18.2)."""

import uuid
from typing import Any

from pydantic import BaseModel, Field


class BgpLookingGlassRouteItem(BaseModel):
    """Información normalizada de una ruta BGP en RouterOS v7."""

    prefix: str
    gateway: str
    immediate_gw: str | None = None
    as_path: str = ""
    communities: list[str] = Field(default_factory=list)
    scope: int | None = None
    active: bool = True
    protocol: str = "bgp"
    uptime: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class BgpLookingGlassRouteResponse(BaseModel):
    """Respuesta de consulta de prefijos en la tabla de ruteo BGP."""

    router_id: uuid.UUID
    prefix: str
    total_routes: int
    routes: list[BgpLookingGlassRouteItem] = Field(default_factory=list)


class BgpLookingGlassAdvertisedItem(BaseModel):
    """Prefijo anunciado a un peer BGP específico."""

    peer: str
    prefix: str
    nexthop: str
    as_path: str | None = None
    origin: str | None = None
    communities: list[str] = Field(default_factory=list)


class BgpLookingGlassAdvertisedResponse(BaseModel):
    """Respuesta de anuncios exportados hacia un peer BGP."""

    router_id: uuid.UUID
    peer: str
    total_advertised: int
    advertisements: list[BgpLookingGlassAdvertisedItem] = Field(default_factory=list)
