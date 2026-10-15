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


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_get_master_vault_key__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_get_master_vault_key__mutmut)
def get_master_vault_key() -> bytes:
    key_b64 = settings.ROSGRID_MASTER_VAULT_KEY
    decoded = base64.b64decode(key_b64)
    if len(decoded) != 32:
        raise ValueError("ROSGRID_MASTER_VAULT_KEY debe ser de exactamente 32 bytes (256 bits)")
    return decoded


def x_get_master_vault_key__mutmut_orig() -> bytes:
    key_b64 = settings.ROSGRID_MASTER_VAULT_KEY
    decoded = base64.b64decode(key_b64)
    if len(decoded) != 32:
        raise ValueError("ROSGRID_MASTER_VAULT_KEY debe ser de exactamente 32 bytes (256 bits)")
    return decoded


def x_get_master_vault_key__mutmut_1() -> bytes:
    key_b64 = None
    decoded = base64.b64decode(key_b64)
    if len(decoded) != 32:
        raise ValueError("ROSGRID_MASTER_VAULT_KEY debe ser de exactamente 32 bytes (256 bits)")
    return decoded


def x_get_master_vault_key__mutmut_2() -> bytes:
    key_b64 = settings.ROSGRID_MASTER_VAULT_KEY
    decoded = None
    if len(decoded) != 32:
        raise ValueError("ROSGRID_MASTER_VAULT_KEY debe ser de exactamente 32 bytes (256 bits)")
    return decoded


def x_get_master_vault_key__mutmut_3() -> bytes:
    key_b64 = settings.ROSGRID_MASTER_VAULT_KEY
    decoded = base64.b64decode(None)
    if len(decoded) != 32:
        raise ValueError("ROSGRID_MASTER_VAULT_KEY debe ser de exactamente 32 bytes (256 bits)")
    return decoded


def x_get_master_vault_key__mutmut_4() -> bytes:
    key_b64 = settings.ROSGRID_MASTER_VAULT_KEY
    decoded = base64.b64decode(key_b64)
    if len(decoded) == 32:
        raise ValueError("ROSGRID_MASTER_VAULT_KEY debe ser de exactamente 32 bytes (256 bits)")
    return decoded


def x_get_master_vault_key__mutmut_5() -> bytes:
    key_b64 = settings.ROSGRID_MASTER_VAULT_KEY
    decoded = base64.b64decode(key_b64)
    if len(decoded) != 33:
        raise ValueError("ROSGRID_MASTER_VAULT_KEY debe ser de exactamente 32 bytes (256 bits)")
    return decoded


def x_get_master_vault_key__mutmut_6() -> bytes:
    key_b64 = settings.ROSGRID_MASTER_VAULT_KEY
    decoded = base64.b64decode(key_b64)
    if len(decoded) != 32:
        raise ValueError(None)
    return decoded


def x_get_master_vault_key__mutmut_7() -> bytes:
    key_b64 = settings.ROSGRID_MASTER_VAULT_KEY
    decoded = base64.b64decode(key_b64)
    if len(decoded) != 32:
        raise ValueError("XXROSGRID_MASTER_VAULT_KEY debe ser de exactamente 32 bytes (256 bits)XX")
    return decoded


def x_get_master_vault_key__mutmut_8() -> bytes:
    key_b64 = settings.ROSGRID_MASTER_VAULT_KEY
    decoded = base64.b64decode(key_b64)
    if len(decoded) != 32:
        raise ValueError("rosgrid_master_vault_key debe ser de exactamente 32 bytes (256 bits)")
    return decoded


def x_get_master_vault_key__mutmut_9() -> bytes:
    key_b64 = settings.ROSGRID_MASTER_VAULT_KEY
    decoded = base64.b64decode(key_b64)
    if len(decoded) != 32:
        raise ValueError("ROSGRID_MASTER_VAULT_KEY DEBE SER DE EXACTAMENTE 32 BYTES (256 BITS)")
    return decoded

mutants_x_get_master_vault_key__mutmut['_mutmut_orig'] = x_get_master_vault_key__mutmut_orig # type: ignore # mutmut generated
mutants_x_get_master_vault_key__mutmut['x_get_master_vault_key__mutmut_1'] = x_get_master_vault_key__mutmut_1 # type: ignore # mutmut generated
mutants_x_get_master_vault_key__mutmut['x_get_master_vault_key__mutmut_2'] = x_get_master_vault_key__mutmut_2 # type: ignore # mutmut generated
mutants_x_get_master_vault_key__mutmut['x_get_master_vault_key__mutmut_3'] = x_get_master_vault_key__mutmut_3 # type: ignore # mutmut generated
mutants_x_get_master_vault_key__mutmut['x_get_master_vault_key__mutmut_4'] = x_get_master_vault_key__mutmut_4 # type: ignore # mutmut generated
mutants_x_get_master_vault_key__mutmut['x_get_master_vault_key__mutmut_5'] = x_get_master_vault_key__mutmut_5 # type: ignore # mutmut generated
mutants_x_get_master_vault_key__mutmut['x_get_master_vault_key__mutmut_6'] = x_get_master_vault_key__mutmut_6 # type: ignore # mutmut generated
mutants_x_get_master_vault_key__mutmut['x_get_master_vault_key__mutmut_7'] = x_get_master_vault_key__mutmut_7 # type: ignore # mutmut generated
mutants_x_get_master_vault_key__mutmut['x_get_master_vault_key__mutmut_8'] = x_get_master_vault_key__mutmut_8 # type: ignore # mutmut generated
mutants_x_get_master_vault_key__mutmut['x_get_master_vault_key__mutmut_9'] = x_get_master_vault_key__mutmut_9 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_encrypt_aes_gcm__mutmut)
def encrypt_aes_gcm(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_orig(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_1(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = None
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_2(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if (key is not None) and False else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_3(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if (key is not None) or True else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_4(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_5(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = None
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_6(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(None)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_7(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = None
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_8(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(None)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_9(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(13)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_10(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = None
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_11(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(None, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_12(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, None, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_13(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, None)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_14(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_15(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_16(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, )
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_17(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = None
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_18(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:+16]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_19(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-17]
    tag = encrypted_payload[-16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_20(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = None
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_21(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[+16:]
    return ciphertext, iv, tag


def x_encrypt_aes_gcm__mutmut_22(plaintext: bytes, aad: bytes, key: bytes | None = None) -> tuple[bytes, bytes, bytes]:
    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    iv = os.urandom(12)
    # cryptography AESGCM concatena el authentication tag de 16 bytes al final del ciphertext
    encrypted_payload = aesgcm.encrypt(iv, plaintext, aad)
    ciphertext = encrypted_payload[:-16]
    tag = encrypted_payload[-17:]
    return ciphertext, iv, tag

mutants_x_encrypt_aes_gcm__mutmut['_mutmut_orig'] = x_encrypt_aes_gcm__mutmut_orig # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_1'] = x_encrypt_aes_gcm__mutmut_1 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_2'] = x_encrypt_aes_gcm__mutmut_2 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_3'] = x_encrypt_aes_gcm__mutmut_3 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_4'] = x_encrypt_aes_gcm__mutmut_4 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_5'] = x_encrypt_aes_gcm__mutmut_5 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_6'] = x_encrypt_aes_gcm__mutmut_6 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_7'] = x_encrypt_aes_gcm__mutmut_7 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_8'] = x_encrypt_aes_gcm__mutmut_8 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_9'] = x_encrypt_aes_gcm__mutmut_9 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_10'] = x_encrypt_aes_gcm__mutmut_10 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_11'] = x_encrypt_aes_gcm__mutmut_11 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_12'] = x_encrypt_aes_gcm__mutmut_12 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_13'] = x_encrypt_aes_gcm__mutmut_13 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_14'] = x_encrypt_aes_gcm__mutmut_14 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_15'] = x_encrypt_aes_gcm__mutmut_15 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_16'] = x_encrypt_aes_gcm__mutmut_16 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_17'] = x_encrypt_aes_gcm__mutmut_17 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_18'] = x_encrypt_aes_gcm__mutmut_18 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_19'] = x_encrypt_aes_gcm__mutmut_19 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_20'] = x_encrypt_aes_gcm__mutmut_20 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_21'] = x_encrypt_aes_gcm__mutmut_21 # type: ignore # mutmut generated
mutants_x_encrypt_aes_gcm__mutmut['x_encrypt_aes_gcm__mutmut_22'] = x_encrypt_aes_gcm__mutmut_22 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_decrypt_aes_gcm__mutmut)
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


def x_decrypt_aes_gcm__mutmut_orig(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
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


def x_decrypt_aes_gcm__mutmut_1(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) == 12:
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


def x_decrypt_aes_gcm__mutmut_2(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 13:
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


def x_decrypt_aes_gcm__mutmut_3(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError(None)
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_4(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("XXEl IV de AES-GCM debe ser de exactamente 12 bytesXX")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_5(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("el iv de aes-gcm debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_6(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("EL IV DE AES-GCM DEBE SER DE EXACTAMENTE 12 BYTES")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_7(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) == 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_8(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 17:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_9(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError(None)

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_10(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("XXEl Tag de AES-GCM debe ser de exactamente 16 bytesXX")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_11(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("el tag de aes-gcm debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_12(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("EL TAG DE AES-GCM DEBE SER DE EXACTAMENTE 16 BYTES")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_13(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = None
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_14(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if (key is not None) and False else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_15(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if (key is not None) or True else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_16(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_17(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = None
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_18(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(None)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_19(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = None
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_20(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext - tag
    try:
        return aesgcm.decrypt(iv, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_21(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(None, full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_22(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, None, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_23(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, None)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_24(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(full_payload, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_25(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, aad)
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_26(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
    if len(iv) != 12:
        raise ValueError("El IV de AES-GCM debe ser de exactamente 12 bytes")
    if len(tag) != 16:
        raise ValueError("El Tag de AES-GCM debe ser de exactamente 16 bytes")

    active_key = key if key is not None else get_master_vault_key()
    aesgcm = AESGCM(active_key)
    full_payload = ciphertext + tag
    try:
        return aesgcm.decrypt(iv, full_payload, )
    except InvalidTag as exc:
        raise ValueError("Fallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)") from exc


def x_decrypt_aes_gcm__mutmut_27(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
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
        raise ValueError(None) from exc


def x_decrypt_aes_gcm__mutmut_28(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
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
        raise ValueError("XXFallo de autenticación o integridad en descifrado AES-GCM (Tag o AAD inválido)XX") from exc


def x_decrypt_aes_gcm__mutmut_29(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
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
        raise ValueError("fallo de autenticación o integridad en descifrado aes-gcm (tag o aad inválido)") from exc


def x_decrypt_aes_gcm__mutmut_30(ciphertext: bytes, iv: bytes, tag: bytes, aad: bytes, key: bytes | None = None) -> bytes:
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
        raise ValueError("FALLO DE AUTENTICACIÓN O INTEGRIDAD EN DESCIFRADO AES-GCM (TAG O AAD INVÁLIDO)") from exc

mutants_x_decrypt_aes_gcm__mutmut['_mutmut_orig'] = x_decrypt_aes_gcm__mutmut_orig # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_1'] = x_decrypt_aes_gcm__mutmut_1 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_2'] = x_decrypt_aes_gcm__mutmut_2 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_3'] = x_decrypt_aes_gcm__mutmut_3 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_4'] = x_decrypt_aes_gcm__mutmut_4 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_5'] = x_decrypt_aes_gcm__mutmut_5 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_6'] = x_decrypt_aes_gcm__mutmut_6 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_7'] = x_decrypt_aes_gcm__mutmut_7 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_8'] = x_decrypt_aes_gcm__mutmut_8 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_9'] = x_decrypt_aes_gcm__mutmut_9 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_10'] = x_decrypt_aes_gcm__mutmut_10 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_11'] = x_decrypt_aes_gcm__mutmut_11 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_12'] = x_decrypt_aes_gcm__mutmut_12 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_13'] = x_decrypt_aes_gcm__mutmut_13 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_14'] = x_decrypt_aes_gcm__mutmut_14 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_15'] = x_decrypt_aes_gcm__mutmut_15 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_16'] = x_decrypt_aes_gcm__mutmut_16 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_17'] = x_decrypt_aes_gcm__mutmut_17 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_18'] = x_decrypt_aes_gcm__mutmut_18 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_19'] = x_decrypt_aes_gcm__mutmut_19 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_20'] = x_decrypt_aes_gcm__mutmut_20 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_21'] = x_decrypt_aes_gcm__mutmut_21 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_22'] = x_decrypt_aes_gcm__mutmut_22 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_23'] = x_decrypt_aes_gcm__mutmut_23 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_24'] = x_decrypt_aes_gcm__mutmut_24 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_25'] = x_decrypt_aes_gcm__mutmut_25 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_26'] = x_decrypt_aes_gcm__mutmut_26 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_27'] = x_decrypt_aes_gcm__mutmut_27 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_28'] = x_decrypt_aes_gcm__mutmut_28 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_29'] = x_decrypt_aes_gcm__mutmut_29 # type: ignore # mutmut generated
mutants_x_decrypt_aes_gcm__mutmut['x_decrypt_aes_gcm__mutmut_30'] = x_decrypt_aes_gcm__mutmut_30 # type: ignore # mutmut generated
mutants_x_hash_password__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_hash_password__mutmut)
def hash_password(password: str) -> str:
    if not password:
        raise ValueError("La contraseña no puede estar vacía")
    return _PASSWORD_HASHER.hash(password)


def x_hash_password__mutmut_orig(password: str) -> str:
    if not password:
        raise ValueError("La contraseña no puede estar vacía")
    return _PASSWORD_HASHER.hash(password)


def x_hash_password__mutmut_1(password: str) -> str:
    if password:
        raise ValueError("La contraseña no puede estar vacía")
    return _PASSWORD_HASHER.hash(password)


def x_hash_password__mutmut_2(password: str) -> str:
    if not password:
        raise ValueError(None)
    return _PASSWORD_HASHER.hash(password)


def x_hash_password__mutmut_3(password: str) -> str:
    if not password:
        raise ValueError("XXLa contraseña no puede estar vacíaXX")
    return _PASSWORD_HASHER.hash(password)


def x_hash_password__mutmut_4(password: str) -> str:
    if not password:
        raise ValueError("la contraseña no puede estar vacía")
    return _PASSWORD_HASHER.hash(password)


def x_hash_password__mutmut_5(password: str) -> str:
    if not password:
        raise ValueError("LA CONTRASEÑA NO PUEDE ESTAR VACÍA")
    return _PASSWORD_HASHER.hash(password)


def x_hash_password__mutmut_6(password: str) -> str:
    if not password:
        raise ValueError("La contraseña no puede estar vacía")
    return _PASSWORD_HASHER.hash(None)

mutants_x_hash_password__mutmut['_mutmut_orig'] = x_hash_password__mutmut_orig # type: ignore # mutmut generated
mutants_x_hash_password__mutmut['x_hash_password__mutmut_1'] = x_hash_password__mutmut_1 # type: ignore # mutmut generated
mutants_x_hash_password__mutmut['x_hash_password__mutmut_2'] = x_hash_password__mutmut_2 # type: ignore # mutmut generated
mutants_x_hash_password__mutmut['x_hash_password__mutmut_3'] = x_hash_password__mutmut_3 # type: ignore # mutmut generated
mutants_x_hash_password__mutmut['x_hash_password__mutmut_4'] = x_hash_password__mutmut_4 # type: ignore # mutmut generated
mutants_x_hash_password__mutmut['x_hash_password__mutmut_5'] = x_hash_password__mutmut_5 # type: ignore # mutmut generated
mutants_x_hash_password__mutmut['x_hash_password__mutmut_6'] = x_hash_password__mutmut_6 # type: ignore # mutmut generated
mutants_x_verify_password__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_verify_password__mutmut)
def verify_password(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return False
    try:
        return _PASSWORD_HASHER.verify(hashed, password)
    except (VerifyMismatchError, VerificationError):
        return False


def x_verify_password__mutmut_orig(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return False
    try:
        return _PASSWORD_HASHER.verify(hashed, password)
    except (VerifyMismatchError, VerificationError):
        return False


def x_verify_password__mutmut_1(password: str, hashed: str) -> bool:
    if not password and not hashed:
        return False
    try:
        return _PASSWORD_HASHER.verify(hashed, password)
    except (VerifyMismatchError, VerificationError):
        return False


def x_verify_password__mutmut_2(password: str, hashed: str) -> bool:
    if password or not hashed:
        return False
    try:
        return _PASSWORD_HASHER.verify(hashed, password)
    except (VerifyMismatchError, VerificationError):
        return False


def x_verify_password__mutmut_3(password: str, hashed: str) -> bool:
    if not password or hashed:
        return False
    try:
        return _PASSWORD_HASHER.verify(hashed, password)
    except (VerifyMismatchError, VerificationError):
        return False


def x_verify_password__mutmut_4(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return True
    try:
        return _PASSWORD_HASHER.verify(hashed, password)
    except (VerifyMismatchError, VerificationError):
        return False


def x_verify_password__mutmut_5(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return False
    try:
        return _PASSWORD_HASHER.verify(None, password)
    except (VerifyMismatchError, VerificationError):
        return False


def x_verify_password__mutmut_6(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return False
    try:
        return _PASSWORD_HASHER.verify(hashed, None)
    except (VerifyMismatchError, VerificationError):
        return False


def x_verify_password__mutmut_7(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return False
    try:
        return _PASSWORD_HASHER.verify(password)
    except (VerifyMismatchError, VerificationError):
        return False


def x_verify_password__mutmut_8(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return False
    try:
        return _PASSWORD_HASHER.verify(hashed, )
    except (VerifyMismatchError, VerificationError):
        return False


def x_verify_password__mutmut_9(password: str, hashed: str) -> bool:
    if not password or not hashed:
        return False
    try:
        return _PASSWORD_HASHER.verify(hashed, password)
    except (VerifyMismatchError, VerificationError):
        return True

mutants_x_verify_password__mutmut['_mutmut_orig'] = x_verify_password__mutmut_orig # type: ignore # mutmut generated
mutants_x_verify_password__mutmut['x_verify_password__mutmut_1'] = x_verify_password__mutmut_1 # type: ignore # mutmut generated
mutants_x_verify_password__mutmut['x_verify_password__mutmut_2'] = x_verify_password__mutmut_2 # type: ignore # mutmut generated
mutants_x_verify_password__mutmut['x_verify_password__mutmut_3'] = x_verify_password__mutmut_3 # type: ignore # mutmut generated
mutants_x_verify_password__mutmut['x_verify_password__mutmut_4'] = x_verify_password__mutmut_4 # type: ignore # mutmut generated
mutants_x_verify_password__mutmut['x_verify_password__mutmut_5'] = x_verify_password__mutmut_5 # type: ignore # mutmut generated
mutants_x_verify_password__mutmut['x_verify_password__mutmut_6'] = x_verify_password__mutmut_6 # type: ignore # mutmut generated
mutants_x_verify_password__mutmut['x_verify_password__mutmut_7'] = x_verify_password__mutmut_7 # type: ignore # mutmut generated
mutants_x_verify_password__mutmut['x_verify_password__mutmut_8'] = x_verify_password__mutmut_8 # type: ignore # mutmut generated
mutants_x_verify_password__mutmut['x_verify_password__mutmut_9'] = x_verify_password__mutmut_9 # type: ignore # mutmut generated
