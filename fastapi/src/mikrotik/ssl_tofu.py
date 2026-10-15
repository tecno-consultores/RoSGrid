# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Módulo de verificación criptográfica SSL TOFU (Trust On First Use) para RouterOS v7+."""

import asyncio
import enum
import hashlib
import ssl
from typing import Any


class SSLTrustStatus(str, enum.Enum):
    """Estados del ciclo de vida de confianza SSL de un router."""

    PENDING_TOFU = "PENDING_TOFU"
    TRUSTED_PINNED = "TRUSTED_PINNED"
    FINGERPRINT_MISMATCH = "FINGERPRINT_MISMATCH"


class MikrotikSSLError(Exception):
    """Excepción base para errores de conexión o verificación SSL con MikroTik."""


class MikrotikSSLFingerprintMismatchError(MikrotikSSLError):
    """Lanzada cuando la huella SHA-256 observada difiere de la huella fijada (Pinned)."""

    def __init__(self, observed_fp: str, expected_fp: str):
        self.observed_fp = observed_fp
        self.expected_fp = expected_fp
        super().__init__(
            f"Huella SSL SHA-256 no coincide (Esperada: {expected_fp}, Observada: {observed_fp}). "
            "Posible ataque Man-in-the-Middle o renovación no autorizada."
        )


def create_tofu_ssl_context() -> ssl.SSLContext:
    """Crea un contexto SSL cliente para inspeccionar certificados autofirmados."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def compute_der_sha256_fingerprint(der_bytes: bytes) -> str:
    """Calcula la huella digital SHA-256 en minúsculas a partir del formato binario DER."""
    return hashlib.sha256(der_bytes).hexdigest().lower()


async def extract_peer_ssl_fingerprint(host: str, port: int, timeout: float = 5.0) -> str:
    """Se conecta al router MikroTik e inspecciona el certificado DER para obtener su huella SHA-256."""
    ssl_ctx = create_tofu_ssl_context()
    try:
        connect_coro = asyncio.open_connection(host=host, port=port, ssl=ssl_ctx)
        _reader, writer = await asyncio.wait_for(connect_coro, timeout=timeout)
    except TimeoutError as exc:
        raise MikrotikSSLError(f"Tiempo de espera agotado al conectar a {host}:{port}") from exc
    except Exception as exc:
        raise MikrotikSSLError(f"Fallo al establecer handshake TLS con {host}:{port}: {exc}") from exc

    try:
        ssl_obj: Any = writer.get_extra_info("ssl_object")
        if ssl_obj is None:
            raise MikrotikSSLError(f"No se pudo extraer ssl_object en la conexión a {host}:{port}")
        der_cert: bytes | None = ssl_obj.getpeercert(binary_form=True)
        if not der_cert:
            raise MikrotikSSLError(f"El router {host}:{port} no entregó un certificado X.509 binario")
        return compute_der_sha256_fingerprint(der_cert)
    finally:
        writer.close()
        await writer.wait_closed()


def evaluate_ssl_fingerprint(
    observed_fp: str,
    pinned_fp: str | None,
    trust_status: str,
) -> tuple[str, str, bool]:
    """Evalúa la huella observada contra el estado en DB.

    Retorna: (fingerprint_final, nuevo_trust_status, fue_primer_pinning)
    Lanza: MikrotikSSLFingerprintMismatchError si hay discrepancia.
    """
    obs_clean = observed_fp.strip().lower()
    is_pending = trust_status == SSLTrustStatus.PENDING_TOFU.value or not pinned_fp
    if is_pending:
        return obs_clean, SSLTrustStatus.TRUSTED_PINNED.value, True

    exp_clean = pinned_fp.strip().lower() if pinned_fp else ""
    if obs_clean == exp_clean:
        return obs_clean, SSLTrustStatus.TRUSTED_PINNED.value, False

    raise MikrotikSSLFingerprintMismatchError(observed_fp=obs_clean, expected_fp=exp_clean)
