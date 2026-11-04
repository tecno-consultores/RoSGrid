# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import pytest

from src.core.crypto import (
    decrypt_aes_gcm,
    encrypt_aes_gcm,
    get_master_vault_key,
    hash_password,
    validate_stig_password_complexity,
    verify_dummy_password,
    verify_password,
)


def test_master_key_derivation() -> None:
    key = get_master_vault_key()
    assert len(key) == 32


def test_master_key_invalid_length(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.core.config.settings.ROSGRID_MASTER_VAULT_KEY", "aW52YWxpZA==")
    with pytest.raises(ValueError, match="exactamente 32 bytes"):
        get_master_vault_key()


def test_aes_gcm_encryption_and_decryption() -> None:
    plaintext = b"SuperSecretRouterOSPassword123!"
    aad = b"tenant-1:router-42"

    ciphertext, iv, tag = encrypt_aes_gcm(plaintext, aad)

    assert len(iv) == 12
    assert len(tag) == 16
    assert ciphertext != plaintext

    decrypted = decrypt_aes_gcm(ciphertext, iv, tag, aad)
    assert decrypted == plaintext


def test_aes_gcm_tampered_ciphertext() -> None:
    plaintext = b"SensitiveData"
    aad = b"tenant-1:router-1"
    ciphertext, iv, tag = encrypt_aes_gcm(plaintext, aad)

    # Corromper un byte del ciphertext
    tampered_ct = bytearray(ciphertext)
    tampered_ct[0] ^= 0xFF

    with pytest.raises(ValueError, match="Fallo de autenticación o integridad"):
        decrypt_aes_gcm(bytes(tampered_ct), iv, tag, aad)


def test_aes_gcm_tampered_aad() -> None:
    plaintext = b"SensitiveData"
    aad = b"tenant-1:router-1"
    wrong_aad = b"tenant-2:router-1"  # Intento de reasignación a otro tenant
    ciphertext, iv, tag = encrypt_aes_gcm(plaintext, aad)

    with pytest.raises(ValueError, match="Fallo de autenticación o integridad"):
        decrypt_aes_gcm(ciphertext, iv, tag, wrong_aad)


def test_aes_gcm_tampered_tag() -> None:
    plaintext = b"SensitiveData"
    aad = b"tenant-1:router-1"
    ciphertext, iv, tag = encrypt_aes_gcm(plaintext, aad)

    tampered_tag = bytearray(tag)
    tampered_tag[0] ^= 0xFF

    with pytest.raises(ValueError, match="Fallo de autenticación o integridad"):
        decrypt_aes_gcm(ciphertext, iv, bytes(tampered_tag), aad)


def test_aes_gcm_invalid_iv_or_tag_length() -> None:
    ciphertext = b"some_cipher"
    aad = b"aad"
    with pytest.raises(ValueError, match="IV de AES-GCM debe ser de exactamente 12 bytes"):
        decrypt_aes_gcm(ciphertext, b"short_iv", b"1234567890123456", aad)

    with pytest.raises(ValueError, match="Tag de AES-GCM debe ser de exactamente 16 bytes"):
        decrypt_aes_gcm(ciphertext, b"123456789012", b"short_tag", aad)


def test_argon2id_hash_and_verify() -> None:
    raw_pwd = "AdminSecurePassword2026!"
    hashed = hash_password(raw_pwd)

    assert hashed.startswith("$argon2id$")
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(raw_pwd, "") is False


def test_argon2id_empty_password_raises() -> None:
    with pytest.raises(ValueError, match="no puede estar vacía"):
        hash_password("")


def test_verify_dummy_password_timing_defense() -> None:
    # Retorna False consistentemente pero ejecuta la computación completa de Argon2id
    assert verify_dummy_password("any_attempted_password") is False
    assert verify_dummy_password("") is False


def test_validate_stig_password_complexity() -> None:
    # 1. Menos de 15 caracteres
    ok, err = validate_stig_password_complexity("Short1!a")
    assert ok is False
    assert "al menos 15 caracteres" in str(err)

    # 2. Sin mayúsculas
    ok, err = validate_stig_password_complexity("passwordlong123!@#")
    assert ok is False
    assert "caracteres especiales" in str(err)

    # 3. Sin números
    ok, err = validate_stig_password_complexity("PasswordLongWithoutDigit!@#")
    assert ok is False
    assert "caracteres especiales" in str(err)

    # 4. Sin caracteres especiales
    ok, err = validate_stig_password_complexity("PasswordLong12345678")
    assert ok is False
    assert "caracteres especiales" in str(err)

    # 5. Cumple plenamente DISA ASD STIG V6R5
    ok, err = validate_stig_password_complexity("StigCompliantPassword2026!#")
    assert ok is True
    assert err is None
