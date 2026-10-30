# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para WebFig Capa 2: Motor Dinámico Universal de RouterOS v7."""

import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
# CATÁLOGO DE ACCIONES RPC CONTEXTUALES (HITO 27.16.2)
# ============================================================================


class Layer2RpcParamItem(StrictBaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=120)
    type: str = Field(default="string", min_length=1, max_length=40)
    required: bool = False
    default_value: str | None = None
    enum_options: list[str] = Field(default_factory=list)


class Layer2RpcActionDescriptor(StrictBaseModel):
    action: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1, max_length=300)
    ros_endpoint: str = Field(..., min_length=1, max_length=180)
    scope: Literal["menu", "row"] = "row"
    requires_safemode: bool = False
    requires_maker_checker: bool = False
    id_param_key: str = "numbers"
    parameters_schema: list[Layer2RpcParamItem] = Field(default_factory=list)


# ============================================================================
# RECURSOS, INTROSPECCIÓN Y COLECCIONES DINÁMICAS (HITO 27.16.3 & 27.16.4)
# ============================================================================


class ColumnSchemaItem(StrictBaseModel):
    key: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=120)
    type: str = Field(..., min_length=1, max_length=40)
    sortable: bool = False
    editable: bool = True
    required: bool = False
    default_value: str | None = None
    enum_options: list[str] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=400)


class DynamicLayer2CollectionResponse(StrictBaseModel):
    ros_path: str
    is_singleton: bool
    supports_safe_mode: bool
    columns_schema: list[ColumnSchemaItem] = Field(default_factory=list)
    items: list[dict[str, Any]] = Field(default_factory=list)
    form_data: dict[str, Any] | None = None
    available_rpc_actions: list[Layer2RpcActionDescriptor] = Field(default_factory=list)
    schema_source: str = "inferred"
    is_server_filtered: bool = False
    payload_reduction_pct: float = 0.0


class Layer2InspectResponse(StrictBaseModel):
    ros_path: str
    ros_version: str
    schema_source: str
    columns_schema: list[ColumnSchemaItem] = Field(default_factory=list)
    available_rpc_actions: list[Layer2RpcActionDescriptor] = Field(default_factory=list)
    completions: list[str] = Field(default_factory=list)


class DynamicLayer2WriteRequest(StrictBaseModel):
    attributes: dict[str, Any] = Field(default_factory=dict)
    enable_safemode: bool = True

    @model_validator(mode="before")
    @classmethod
    def _wrap_flat_attributes(cls, data: Any) -> Any:
        if isinstance(data, dict) and "attributes" not in data:
            enable_sm = bool(data.get("enable_safemode", True))
            attrs = {
                k: v
                for k, v in data.items()
                if k not in ("enable_safemode", ".id", "id")
            }
            return {"attributes": attrs, "enable_safemode": enable_sm}
        return data


class DynamicLayer2CommandRequest(StrictBaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)
    action: str | None = Field(default=None, max_length=80)
    item_id: str | None = Field(default=None, max_length=80)
    enable_safemode: bool = False


# ============================================================================
# FILTRADO SERVER-SIDE (.query) Y PROYECCIÓN (.proplist) (HITO 27.16.4)
# ============================================================================


class Layer2QueryFilterItem(StrictBaseModel):
    field: str = Field(..., min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_.-]+$")
    operator: Literal["=", "!=", "<", ">"] = "="
    value: str = Field(..., max_length=200)


class DynamicLayer2QueryRequest(StrictBaseModel):
    proplist: list[str] = Field(default_factory=list, max_length=60)
    filters: list[Layer2QueryFilterItem] = Field(default_factory=list, max_length=15)


# ============================================================================
# OPERACIONES POR LOTE (BULK) Y EXPORTACIÓN .RSC CON DIFF (HITO 27.16.5 & 27.16.6)
# ============================================================================


class DynamicLayer2BulkRequest(StrictBaseModel):
    action: Literal["enable", "disable", "comment", "remove"]
    item_ids: list[str] = Field(..., min_length=1, max_length=100)
    comment: str | None = Field(default=None, max_length=255)
    enable_safemode: bool = True


class DynamicLayer2BulkResponse(StrictBaseModel):
    ros_path: str
    action: str
    total_requested: int
    succeeded_count: int
    failed_count: int
    safemode_applied: bool
    results: list[dict[str, Any]] = Field(default_factory=list)


class DynamicLayer2ExportRequest(StrictBaseModel):
    mode: Literal["compact", "terse", "verbose"] = "compact"
    compare_with_latest_backup: bool = True


class DynamicLayer2ExportResponse(StrictBaseModel):
    ros_path: str
    cli_header: str
    live_rsc_text: str
    backup_rsc_text: str
    unified_diff: str
    has_drift: bool
    latest_backup_timestamp: str | None = None
