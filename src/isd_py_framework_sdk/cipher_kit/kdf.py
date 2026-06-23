"""Key Derivation Functions (KDF) — turn a human passphrase into a strong key.

A passphrase is *not* a key.  Hashing it once (``sha256(password)``) is fast,
which means an attacker can also try billions of guesses per second.  A KDF
deliberately makes derivation *slow* and (for the modern ones) *memory-hard*,
and mixes in a random ``salt`` so the same passphrase never yields the same key
twice and pre-computed rainbow tables are useless.

Three algorithms, best-first:

* ``argon2id``     — memory-hard, resists GPU/ASIC cracking; the current
                     state of the art (Password Hashing Competition winner).
                     Requires the optional ``argon2-cffi`` backend.
* ``scrypt``       — also memory-hard, ships inside ``cryptography``; the
                     automatic fallback when argon2 is not installed.
* ``pbkdf2-sha256`` — iteration-hard only (not memory-hard), but universally
                     available; kept for interop / constrained environments.

Every derivation returns a ``meta`` dict that fully describes how the key was
produced (algorithm + parameters + salt).  That dict is stored in the token
header so :func:`derive_from_meta` can reproduce the exact same key at
decryption time.
"""
from __future__ import annotations

import os

from .envelope import b64d, b64e
from .errors import CipherKitError, MissingDependencyError

__all__ = ["derive_key", "derive_from_meta", "default_kdf", "have_argon2"]

# Sensible 2024-era defaults.  Override any of them via **kdf_params.
_DEFAULTS: dict[str, dict] = {
    "argon2id": {"time_cost": 3, "memory_cost": 65536, "parallelism": 4},  # 64 MiB
    "scrypt": {"n": 2 ** 15, "r": 8, "p": 1},  # ~32 MiB
    "pbkdf2-sha256": {"iterations": 600_000},
}

_ALIASES = {
    "argon2": "argon2id",
    "argon2id": "argon2id",
    "scrypt": "scrypt",
    "pbkdf2": "pbkdf2-sha256",
    "pbkdf2-sha256": "pbkdf2-sha256",
    "pbkdf2_sha256": "pbkdf2-sha256",
}


def have_argon2() -> bool:
    """Is the optional ``argon2-cffi`` backend importable?"""
    try:
        import argon2  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def default_kdf() -> str:
    """Pick the strongest KDF available: argon2id if installed, else scrypt."""
    return "argon2id" if have_argon2() else "scrypt"


def _normalise(algorithm: str) -> str:
    key = algorithm.lower().replace(" ", "")
    if key not in _ALIASES:
        raise CipherKitError(
            f"Unknown KDF {algorithm!r}. Use 'argon2id', 'scrypt', or 'pbkdf2-sha256'."
        )
    return _ALIASES[key]


def derive_key(
    passphrase: bytes,
    *,
    algorithm: str,
    length: int = 32,
    salt: bytes | None = None,
    params: dict | None = None,
) -> tuple[bytes, dict]:
    """Derive a *length*-byte key from *passphrase*.

    When *salt* is ``None`` a fresh random 16-byte salt is generated (the
    encryption path).  Returns ``(key, meta)`` where *meta* is a
    JSON-serialisable description of the derivation, ready to embed in a token
    header.
    """
    algorithm = _normalise(algorithm)
    if salt is None:
        salt = os.urandom(16)
    p = {**_DEFAULTS[algorithm], **(params or {})}

    if algorithm == "argon2id":
        if not have_argon2():
            raise MissingDependencyError(
                "argon2id requires 'argon2-cffi'. Install with: "
                "pip install isd-py-framework-sdk[cipher_kit.argon2]  "
                "(or pass kdf='scrypt')."
            )
        from argon2.low_level import Type, hash_secret_raw

        key = hash_secret_raw(
            secret=passphrase,
            salt=salt,
            time_cost=p["time_cost"],
            memory_cost=p["memory_cost"],
            parallelism=p["parallelism"],
            hash_len=length,
            type=Type.ID,
        )
    elif algorithm == "scrypt":
        from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

        key = Scrypt(salt=salt, length=length, n=p["n"], r=p["r"], p=p["p"]).derive(passphrase)
    else:  # pbkdf2-sha256
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        key = PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=length, salt=salt, iterations=p["iterations"]
        ).derive(passphrase)

    meta = {"algorithm": algorithm, "salt": b64e(salt), "length": length, **p}
    return key, meta


def derive_from_meta(passphrase: bytes, meta: dict) -> bytes:
    """Reproduce a key from a *meta* dict previously emitted by :func:`derive_key`."""
    algorithm = meta["algorithm"]
    salt = b64d(meta["salt"])
    length = meta.get("length", 32)
    params = {k: v for k, v in meta.items() if k not in ("algorithm", "salt", "length")}
    key, _ = derive_key(passphrase, algorithm=algorithm, length=length, salt=salt, params=params)
    return key
