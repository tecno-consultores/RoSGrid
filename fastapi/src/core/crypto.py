# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 RoSGrid Contributors

import base64
import os

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerificationError, VerifyMismatchError
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.core.config import settings

# Parámetros recomendados por OWASP para Argon2id
_PASSWORD_HASHER = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    type=Type.ID,
)


def get_master_vault_key() -> bytes:
    key_b64 = settings.ROSGRID_MASTER_VAULT_KEY
    decoded = base64.b64decode(key_b64)
    if len(decoded) != 32:
        raise ValueError("ROSGRID_MASTER_VAULT_KEY debe ser de exactamente 32 bytes (256 bits)")
    return decoded


def encrypt_aes_gcm(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def decrypt_aes_gcm(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("La contraseña no puede estar vacía")
    return _PASSWORD_HASHER.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return False
    try:
        return _PASSWORD_HASHER.verify(hashed, password)
    except (VerifyMismatchError, VerificationError):
        return False
