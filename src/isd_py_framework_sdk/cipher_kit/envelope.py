"""Versioned, self-describing token format.

A sealed secret is encoded as a single dotted ASCII string::

    CK1.<base64url(header_json)>.<base64url(ciphertext)>

The header is a small JSON object that carries *everything* needed to decrypt
the body (cipher name, KDF algorithm + parameters, salt, nonce, …).  Because
the format is self-describing, :func:`cipher_kit.unseal` never needs to be told
which algorithm produced a token — it reads it from the header.  This is also
what lets the algorithm evolve over time without breaking old tokens: bump the
``CK1`` prefix to ``CK2`` and teach the decoder both.

This module is intentionally dependency-free (stdlib only) so that merely
*recognising* a token (:func:`is_token`) never drags in ``cryptography``.
"""
from __future__ import annotations

import base64
import json

from .errors import InvalidTokenError

__all__ = ["PREFIX", "encode_token", "decode_token", "is_token", "b64e", "b64d"]

PREFIX = "CK1"


# --- inner-field codec (standard base64, used inside the JSON header) --------

def b64e(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64d(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


# --- token codec (url-safe base64, no padding, for the dotted segments) ------

def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64u_d(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def encode_token(header: dict, ciphertext: bytes) -> str:
    """Serialise *header* + *ciphertext* into a ``CK1.<h>.<c>`` token string."""
    h = _b64u(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    c = _b64u(ciphertext)
    return f"{PREFIX}.{h}.{c}"


def decode_token(token: str) -> tuple[dict, bytes]:
    """Parse a token back into ``(header, ciphertext)``.

    Raises :class:`InvalidTokenError` if *token* is not a well-formed ``CK1``
    string.
    """
    if not isinstance(token, str):
        raise InvalidTokenError("Token must be a str.")
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != PREFIX:
        raise InvalidTokenError(
            f"Not a cipher_kit token (expected '{PREFIX}.<header>.<body>')."
        )
    try:
        header = json.loads(_b64u_d(parts[1]).decode("utf-8"))
        ciphertext = _b64u_d(parts[2])
    except Exception as exc:  # noqa: BLE001 — any malformed input → one clear error
        raise InvalidTokenError(f"Corrupted token: {exc}") from exc
    return header, ciphertext


def is_token(value: object) -> bool:
    """Cheap, dependency-free check: does *value* look like a ``CK1`` token?"""
    return (
        isinstance(value, str)
        and value.startswith(PREFIX + ".")
        and value.count(".") == 2
    )
