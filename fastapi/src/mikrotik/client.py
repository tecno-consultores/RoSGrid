# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Cliente HTTP asíncrono para la REST API de RouterOS v7+ con soporte TOFU y fallback de credenciales."""

import logging
from typing import Any

import httpx

from src.mikrotik.ssl_tofu import (
    SSLTrustStatus,
    create_tofu_ssl_context,
    evaluate_ssl_fingerprint,
    extract_peer_ssl_fingerprint,
)

logger = logging.getLogger(__name__)


class MikrotikClientError(Exception):
    """Excepción base para errores del cliente REST de RouterOS."""


class MikrotikConnectionError(MikrotikClientError):
    """Error de conectividad de red con el router MikroTik."""


class MikrotikTimeoutError(MikrotikClientError):
    """Tiempo de espera agotado al comunicarse con el router MikroTik."""


class MikrotikAuthFailedError(MikrotikClientError):
    """Error de autenticación HTTP Basic (401 Unauthorized) con el router MikroTik."""


class MikrotikApiError(MikrotikClientError):
    """Error devuelto por la REST API de RouterOS (códigos 4xx/5xx)."""

    def __init__(self, status_code: int, message: str, detail: Any = None):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        super().__init__(f"RouterOS REST API Error [{status_code}]: {message}")


class MikrotikRestClient:
    """Cliente HTTP asíncrono optimizado para RouterOS v7.1+ REST API (/rest/*)."""

    def __init__(
        self,
        host: str,
        port: int = 443,
        username: str = "",
        password: str = "",  # nosec B107
        previous_password: str | None = None,
        ssl_pinned_fingerprint: str | None = None,
        timeout: float = 10.0,
        use_ssl: bool = True,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.previous_password = previous_password
        self.ssl_pinned_fingerprint = ssl_pinned_fingerprint
        self.timeout = timeout
        self.use_ssl = use_ssl
        self._ssl_verified = False
        self._observed_fingerprint: str | None = None
        self._client: httpx.AsyncClient | None = None

    def _get_base_url(self) -> str:
        scheme = "https" if self.use_ssl else "http"
        return f"{scheme}://{self.host}:{self.port}/rest"

    def _build_url(self, endpoint: str) -> str:
        clean_endpoint = endpoint.strip("/")
        return f"{self._get_base_url()}/{clean_endpoint}"

    async def ensure_ssl_verified(self) -> str | None:
        """Verifica la huella SHA-256 del certificado TLS contra la huella pinned antes de enviar credenciales."""
        if not self.use_ssl or self._ssl_verified:
            return self._observed_fingerprint

        observed = await extract_peer_ssl_fingerprint(
            host=self.host,
            port=self.port,
            timeout=self.timeout,
        )
        trust_status = (
            SSLTrustStatus.TRUSTED_PINNED.value if self.ssl_pinned_fingerprint else SSLTrustStatus.PENDING_TOFU.value
        )
        fp, _, _ = evaluate_ssl_fingerprint(
            observed_fp=observed,
            pinned_fp=self.ssl_pinned_fingerprint,
            trust_status=trust_status,
        )
        self._observed_fingerprint = fp
        self._ssl_verified = True
        return self._observed_fingerprint

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            ssl_ctx = create_tofu_ssl_context() if self.use_ssl else None
            limits = httpx.Limits(max_keepalive_connections=20, max_connections=100, keepalive_expiry=60.0)
            self._client = httpx.AsyncClient(
                verify=ssl_ctx if ssl_ctx else False,
                timeout=httpx.Timeout(self.timeout),
                limits=limits,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    def _parse_response_body(self, response: httpx.Response) -> Any:
        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except Exception:
            return response.text

    def _handle_error_status(self, response: httpx.Response) -> None:
        body = self._parse_response_body(response)
        error_msg = body.get("detail", body) if isinstance(body, dict) else str(body)
        if response.status_code == 401:
            raise MikrotikAuthFailedError(f"Autenticación fallida con {self.username}@{self.host}")
        raise MikrotikApiError(
            status_code=response.status_code,
            message=str(error_msg),
            detail=body,
        )

    async def _raw_send(
        self,
        method: str,
        url: str,
        password: str,
        params: dict[str, Any] | None = None,
        json_data: Any = None,
    ) -> httpx.Response:
        client = await self._get_client()
        auth = httpx.BasicAuth(username=self.username, password=password)
        try:
            return await client.request(
                method=method,
                url=url,
                auth=auth,
                params=params,
                json=json_data,
            )
        except httpx.TimeoutException as exc:
            raise MikrotikTimeoutError(f"Timeout en {method} {url} tras {self.timeout}s") from exc
        except httpx.NetworkError as exc:
            raise MikrotikConnectionError(f"Error de red al conectar a {self.host}:{self.port}: {exc}") from exc

    async def _execute_with_auth_fallback(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        json_data: Any = None,
    ) -> httpx.Response:
        response = await self._raw_send(
            method=method,
            url=url,
            password=self.password,
            params=params,
            json_data=json_data,
        )
        if response.status_code != 401 or not self.previous_password:
            return response

        logger.warning(
            "HTTP 401 recibido para %s@%s. Intentando fallback con previous_password",
            self.username,
            self.host,
        )
        fallback_res = await self._raw_send(
            method=method,
            url=url,
            password=self.previous_password,
            params=params,
            json_data=json_data,
        )
        return fallback_res

    async def request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: Any = None,
    ) -> Any:
        """Ejecuta una petición HTTP a la REST API garantizando TOFU SSL y manejo de errores."""
        await self.ensure_ssl_verified()
        url = self._build_url(endpoint)
        response = await self._execute_with_auth_fallback(
            method=method,
            url=url,
            params=params,
            json_data=json_data,
        )
        if response.is_error:
            self._handle_error_status(response)
        return self._parse_response_body(response)

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Obtiene un recurso o lista de recursos (GET)."""
        return await self.request("GET", endpoint, params=params)

    async def put(self, endpoint: str, json_data: Any = None) -> Any:
        """Crea un nuevo recurso en RouterOS v7 (PUT)."""
        return await self.request("PUT", endpoint, json_data=json_data)

    async def patch(self, endpoint: str, json_data: Any = None) -> Any:
        """Modifica un recurso existente por su .id (PATCH)."""
        return await self.request("PATCH", endpoint, json_data=json_data)

    async def delete(self, endpoint: str) -> Any:
        """Elimina un recurso existente por su .id (DELETE)."""
        return await self.request("DELETE", endpoint)

    async def post(self, endpoint: str, json_data: Any = None) -> Any:
        """Ejecuta comandos o acciones CLI en RouterOS v7 (POST)."""
        return await self.request("POST", endpoint, json_data=json_data)

    async def close(self) -> None:
        """Cierra el cliente HTTP subyacente y libera recursos."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "MikrotikRestClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()
