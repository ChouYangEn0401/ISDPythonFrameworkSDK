"""Exception hierarchy for :mod:`cipher_kit`.

All errors derive from :class:`CipherKitError` so callers can catch the whole
family with a single ``except``.
"""
from __future__ import annotations

__all__ = [
    "CipherKitError",
    "InvalidTokenError",
    "DecryptionError",
    "MissingDependencyError",
    "MissingKeyError",
]


class CipherKitError(Exception):
    """Base class for every error raised by :mod:`cipher_kit`."""


class InvalidTokenError(CipherKitError):
    """The supplied value is not a well-formed ``CK1`` token."""


class DecryptionError(CipherKitError):
    """Authenticated decryption failed (wrong key/passphrase or tampered token)."""


class MissingDependencyError(CipherKitError):
    """An optional backend (argon2-cffi / keyring) is required but not installed."""


class MissingKeyError(CipherKitError):
    """No key material was provided where one is required."""
