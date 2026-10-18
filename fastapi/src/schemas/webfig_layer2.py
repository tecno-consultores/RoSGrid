# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para WebFig Capa 2: Motor Dinámico Universal de RouterOS v7."""

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    """Modelo base con restricción estricta de atributos adicionales (extra='forbid')."""

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# CATÁLOGO DE MENÚS CAPA 2
# ============================================================================


class CatalogMenuItem(StrictBaseModel):
    label: str = Field(..., min_length=1, max_length=120)
    ros_path: str = Field(..., min_length=1, max_length=160)
    supports_safe_mode: bool = True


class CatalogMenuGroup(StrictBaseModel):
    group: str = Field(..., min_length=1, max_length=120)
    items: list[CatalogMenuItem] = Field(default_factory=list)


class WebfigLayer2CatalogResponse(StrictBaseModel):
    router_id: uuid.UUID
    ros_version: str
    installed_packages: list[str] = Field(default_factory=list)
    menu_tree: list[CatalogMenuGroup] = Field(default_factory=list)


# ============================================================================
# RECURSOS Y COLECCIONES DINÁMICAS
# ============================================================================


class ColumnSchemaItem(StrictBaseModel):
    key: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=120)
    type: str = Field(..., min_length=1, max_length=40)
    sortable: bool = False
    editable: bool = True


class DynamicLayer2CollectionResponse(StrictBaseModel):
    ros_path: str
    is_singleton: bool
    supports_safe_mode: bool
    columns_schema: list[ColumnSchemaItem] = Field(default_factory=list)
    items: list[dict[str, Any]] = Field(default_factory=list)
    form_data: dict[str, Any] | None = None


class DynamicLayer2WriteRequest(StrictBaseModel):
    attributes: dict[str, Any] = Field(default_factory=dict)
    enable_safemode: bool = True


class DynamicLayer2CommandRequest(StrictBaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)
