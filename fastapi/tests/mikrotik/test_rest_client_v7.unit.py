# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para el cliente REST asíncrono de RouterOS v7."""

from typing import Any
from unittest.mock import patch

import httpx
import pytest

from src.mikrotik.client import (
    MikrotikApiError,
    MikrotikAuthFailedError,
    MikrotikConnectionError,
    MikrotikRestClient,
    MikrotikTimeoutError,
)


@pytest.mark.asyncio
async def test_rest_client_urls() -> None:
    c_ssl = MikrotikRestClient("192.168.88.1", port=443, use_ssl=True)
    assert c_ssl._get_base_url() == "https://192.168.88.1:443/rest"
    assert c_ssl._build_url("/system/resource") == "https://192.168.88.1:443/rest/system/resource"

    c_plain = MikrotikRestClient("192.168.88.1", port=80, use_ssl=False)
    assert c_plain._get_base_url() == "http://192.168.88.1:80/rest"


@pytest.mark.asyncio
async def test_rest_client_crud_methods() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        method = request.method
        path = request.url.path
        if method == "GET" and path == "/rest/system/identity":
            return httpx.Response(200, json={"name": "TestRouter"})
        if method == "PUT" and path == "/rest/interface/bridge":
            return httpx.Response(201, json={".id": "*1", "name": "br0"})
        if method == "PATCH" and path == "/rest/interface/bridge/*1":
            return httpx.Response(200, json={".id": "*1", "comment": "updated"})
        if method == "DELETE" and path == "/rest/interface/bridge/*1":
            return httpx.Response(204)
        if method == "POST" and path == "/rest/system/reboot":
            return httpx.Response(200, json={})
        return httpx.Response(404, json={"detail": "Not Found"})

    transport = httpx.MockTransport(handler)
    mock_http_client = httpx.AsyncClient(transport=transport)

    client = MikrotikRestClient("10.0.0.1", port=80, use_ssl=False)
    client._client = mock_http_client

    async with client:
        # GET
        get_res = await client.get("/system/identity")
        assert get_res == {"name": "TestRouter"}

        # PUT
        put_res = await client.put("/interface/bridge", json_data={"name": "br0"})
        assert put_res[".id"] == "*1"

        # PATCH
        patch_res = await client.patch("/interface/bridge/*1", json_data={"comment": "updated"})
        assert patch_res["comment"] == "updated"

        # DELETE (204 -> None)
        del_res = await client.delete("/interface/bridge/*1")
        assert del_res is None

        # POST
        post_res = await client.post("/system/reboot")
        assert post_res == {}


@pytest.mark.asyncio
async def test_rest_client_auth_fallback() -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        auth_hdr = request.headers.get("Authorization", "")
        calls.append(auth_hdr)
        # First call has current password -> fails 401
        # Second call has previous password -> succeeds 200
        if len(calls) == 1:
            return httpx.Response(401, json={"detail": "Unauthorized"})
        return httpx.Response(200, json={"version": "7.16.1"})

    transport = httpx.MockTransport(handler)
    mock_http_client = httpx.AsyncClient(transport=transport)

    client = MikrotikRestClient(
        host="10.0.0.1",
        username="admin",
        password="new_password",
        previous_password="old_password",
        use_ssl=False,
    )
    client._client = mock_http_client

    res = await client.get("/system/resource")
    assert res == {"version": "7.16.1"}
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_rest_client_auth_failed_without_fallback() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Bad credentials"})

    transport = httpx.MockTransport(handler)
    mock_http_client = httpx.AsyncClient(transport=transport)

    client = MikrotikRestClient(
        host="10.0.0.1",
        username="admin",
        password="wrong_password",
        previous_password=None,
        use_ssl=False,
    )
    client._client = mock_http_client

    with pytest.raises(MikrotikAuthFailedError, match="Autenticación fallida"):
        await client.get("/system/resource")


@pytest.mark.asyncio
async def test_rest_client_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"detail": "Invalid parameter"})

    transport = httpx.MockTransport(handler)
    mock_http_client = httpx.AsyncClient(transport=transport)

    client = MikrotikRestClient("10.0.0.1", use_ssl=False)
    client._client = mock_http_client

    with pytest.raises(MikrotikApiError) as exc_info:
        await client.get("/invalid/path")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_rest_client_timeout_and_network_errors() -> None:
    client = MikrotikRestClient("10.0.0.1", timeout=0.1, use_ssl=False)

    async def raise_timeout(*args: Any, **kwargs: Any) -> Any:
        raise httpx.ReadTimeout("Timeout")

    async def raise_network(*args: Any, **kwargs: Any) -> Any:
        raise httpx.ConnectError("Network down")

    with patch.object(httpx.AsyncClient, "request", side_effect=raise_timeout):
        with pytest.raises(MikrotikTimeoutError):
            await client.get("/system/resource")

    with patch.object(httpx.AsyncClient, "request", side_effect=raise_network):
        with pytest.raises(MikrotikConnectionError):
            await client.get("/system/resource")


@pytest.mark.asyncio
async def test_rest_client_ssl_verification() -> None:
    fake_fp = "f" * 64
    client = MikrotikRestClient("10.0.0.1", port=443, use_ssl=True, ssl_pinned_fingerprint=fake_fp)

    with (
        patch("src.mikrotik.client.extract_peer_ssl_fingerprint", return_value=fake_fp),
        patch("src.mikrotik.client.evaluate_ssl_fingerprint", return_value=(fake_fp, None, True)),
    ):
        fp = await client.ensure_ssl_verified()
        assert fp == fake_fp
        assert client._ssl_verified is True
        # Calling again should immediately return cached
        fp2 = await client.ensure_ssl_verified()
        assert fp2 == fake_fp
