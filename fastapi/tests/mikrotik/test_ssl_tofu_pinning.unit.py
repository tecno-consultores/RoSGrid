# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

"""Pruebas unitarias para verificación y anclaje SSL TOFU (Trust On First Use)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mikrotik.ssl_tofu import (
    MikrotikSSLError,
    MikrotikSSLFingerprintMismatchError,
    SSLTrustStatus,
    compute_der_sha256_fingerprint,
    create_tofu_ssl_context,
    evaluate_ssl_fingerprint,
    extract_peer_ssl_fingerprint,
)


def test_compute_der_sha256_fingerprint() -> None:
    sample_cert_der = b"sample_certificate_der_bytes_for_testing"
    fp = compute_der_sha256_fingerprint(sample_cert_der)
    assert len(fp) == 64
    assert fp == compute_der_sha256_fingerprint(sample_cert_der)
    assert fp != compute_der_sha256_fingerprint(b"another_cert_der_bytes")


def test_create_tofu_ssl_context() -> None:
    ctx = create_tofu_ssl_context()
    assert ctx.check_hostname is False
    assert ctx.verify_mode == 0  # CERT_NONE


def test_evaluate_ssl_fingerprint_pending_tofu() -> None:
    obs = "a" * 64
    final_fp, new_status, was_first = evaluate_ssl_fingerprint(
        observed_fp=obs,
        pinned_fp=None,
        trust_status=SSLTrustStatus.PENDING_TOFU.value,
    )
    assert final_fp == obs
    assert new_status == SSLTrustStatus.TRUSTED_PINNED.value
    assert was_first is True


def test_evaluate_ssl_fingerprint_matching_existing() -> None:
    obs = "b" * 64
    final_fp, new_status, was_first = evaluate_ssl_fingerprint(
        observed_fp=obs,
        pinned_fp=obs,
        trust_status=SSLTrustStatus.TRUSTED_PINNED.value,
    )
    assert final_fp == obs
    assert new_status == SSLTrustStatus.TRUSTED_PINNED.value
    assert was_first is False


def test_evaluate_ssl_fingerprint_mismatch() -> None:
    pinned = "c" * 64
    obs = "d" * 64
    with pytest.raises(MikrotikSSLFingerprintMismatchError) as exc_info:
        evaluate_ssl_fingerprint(
            observed_fp=obs,
            pinned_fp=pinned,
            trust_status=SSLTrustStatus.TRUSTED_PINNED.value,
        )
    assert exc_info.value.observed_fp == obs
    assert exc_info.value.expected_fp == pinned


@pytest.mark.asyncio
async def test_extract_peer_ssl_fingerprint_success() -> None:
    mock_ssl_obj = MagicMock()
    mock_ssl_obj.getpeercert.return_value = b"sample_cert_der"

    mock_writer = MagicMock()
    mock_writer.get_extra_info.return_value = mock_ssl_obj
    mock_writer.close = MagicMock()
    mock_writer.wait_closed = AsyncMock()

    mock_reader = MagicMock()

    async def fake_open_connection(*args: object, **kwargs: object) -> tuple[MagicMock, MagicMock]:
        return mock_reader, mock_writer

    with patch("asyncio.open_connection", side_effect=fake_open_connection):
        fp = await extract_peer_ssl_fingerprint("192.168.88.1", 443, timeout=1.0)
        assert fp == compute_der_sha256_fingerprint(b"sample_cert_der")


@pytest.mark.asyncio
async def test_extract_peer_ssl_fingerprint_timeout() -> None:
    async def timeout_conn(*args: object, **kwargs: object) -> tuple[MagicMock, MagicMock]:
        raise TimeoutError("Timed out")

    with patch("asyncio.open_connection", side_effect=timeout_conn):
        with pytest.raises(MikrotikSSLError, match="Tiempo de espera agotado"):
            await extract_peer_ssl_fingerprint("192.168.88.1", 443, timeout=0.1)


@pytest.mark.asyncio
async def test_extract_peer_ssl_fingerprint_missing_cert() -> None:
    mock_ssl_obj = MagicMock()
    mock_ssl_obj.getpeercert.return_value = None

    mock_writer = MagicMock()
    mock_writer.get_extra_info.return_value = mock_ssl_obj
    mock_writer.close = MagicMock()
    mock_writer.wait_closed = AsyncMock()

    async def fake_open_connection(*args: object, **kwargs: object) -> tuple[MagicMock, MagicMock]:
        return MagicMock(), mock_writer

    with patch("asyncio.open_connection", side_effect=fake_open_connection):
        with pytest.raises(MikrotikSSLError, match="no entregó un certificado"):
            await extract_peer_ssl_fingerprint("192.168.88.1", 443, timeout=1.0)
