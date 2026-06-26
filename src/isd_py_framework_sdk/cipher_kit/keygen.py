"""Generate raw symmetric keys for the *raw-key* ciphers.

The passphrase-based ciphers stretch a human password with a KDF, so they need
no separate key material.  The raw-key ciphers (:class:`RawKeyCipher`,
:class:`Aes256SivCipher`, :class:`AesGcmSivCipher`) and :class:`FernetCipher`
instead take an *already-strong* key — these helpers mint one with a
cryptographically secure RNG.

Keep generated keys somewhere genuinely separate from the ciphertext (an OS
keyring, a KMS, a permission-restricted file) — see :mod:`.key_sources` for the
*passphrase* equivalent of that principle.
"""
from __future__ import annotations

import os

__all__ = ["generate_fernet_key", "generate_aead_key", "generate_aes_siv_key"]


def generate_fernet_key() -> bytes:
    """Return a fresh **Fernet** key (a 32-byte key, url-safe base64-encoded).

    Feed it straight to :class:`FernetCipher` or ``CipherKit.fernet(...)``.
    (Imports ``cryptography`` lazily, so merely importing this module is free.)
    """
    from cryptography.fernet import Fernet

    return Fernet.generate_key()


def generate_aead_key(bits: int = 256) -> bytes:
    """Return a fresh raw AEAD key of *bits* bits (default 256 → 32 bytes).

    Suitable for :class:`RawKeyCipher` (requires 32 bytes / 256 bits) and
    :class:`AesGcmSivCipher` (accepts 16 or 32 bytes).
    """
    if bits not in (128, 256):
        raise ValueError("generate_aead_key supports bits=128 or bits=256.")
    return os.urandom(bits // 8)


def generate_aes_siv_key() -> bytes:
    """Return a fresh **64-byte** key for AES-256-SIV (:class:`Aes256SivCipher`).

    AES-SIV uses a double-length key; 64 bytes selects the AES-256 variant.
    """
    return os.urandom(64)
