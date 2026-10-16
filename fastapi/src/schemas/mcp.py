# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Esquemas Pydantic v2 para el protocolo JSON-RPC 2.0 y servidor MCP Streamable HTTP."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class McpJsonRpcRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jsonrpc: Literal["2.0"] = "2.0"
    id: str | int | None = None
    method: Literal[
        "initialize",
        "notifications/initialized",
        "ping",
        "tools/list",
        "tools/call",
    ]
    params: dict[str, Any] = Field(default_factory=dict)


class McpToolDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    inputSchema: dict[str, Any]


class McpJsonRpcError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: int
    message: str
    data: dict[str, Any] | None = None


class McpJsonRpcResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    jsonrpc: Literal["2.0"] = "2.0"
    id: str | int | None = None
    result: dict[str, Any] | None = None
    error: McpJsonRpcError | None = None
