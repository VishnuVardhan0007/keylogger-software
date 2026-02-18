"""Encryption and decryption of keystroke payloads using Fernet (AES) and PBKDF2."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CryptoError(Exception):
    """Raised when key derivation or encryption fails."""


class DecryptionError(CryptoError):
    """Raised when decryption fails (wrong passphrase or corrupted data)."""


@dataclass(frozen=True)
class CryptoParams:
    """Per-database salt and KDF iteration count for key derivation."""

    salt: bytes
    kdf_iters: int


def derive_fernet_key(passphrase: str, salt: bytes, kdf_iters: int) -> bytes:
    if not passphrase:
        raise CryptoError("Passphrase is required.")
    if not salt:
        raise CryptoError("Salt is required.")
    if kdf_iters < 50_000:
        raise CryptoError("kdf_iters too low.")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=kdf_iters,
    )
    key = kdf.derive(passphrase.encode("utf-8"))
    return base64.urlsafe_b64encode(key)


def build_fernet(passphrase: str, salt: bytes, kdf_iters: int) -> Fernet:
    """Build a Fernet instance from passphrase and stored crypto params."""
    return Fernet(derive_fernet_key(passphrase=passphrase, salt=salt, kdf_iters=kdf_iters))


def encrypt_json(fernet: Fernet, payload: dict[str, Any]) -> bytes:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return fernet.encrypt(data)


def decrypt_json(fernet: Fernet, token: bytes) -> dict[str, Any]:
    """Decrypt ciphertext and parse JSON; raises DecryptionError on failure."""
    try:
        data = fernet.decrypt(token)
    except InvalidToken as e:
        raise DecryptionError("Wrong passphrase or corrupted data.") from e
    return json.loads(data.decode("utf-8"))

