"""The cipher strategies — how bytes are actually protected.

Every cipher implements the same tiny contract::

    seal(data: bytes) -> str      # → a self-describing CK1 token
    unseal(token: str) -> bytes   # ← back to the original bytes

so they are interchangeable and, crucially, *composable* via
:class:`LayeredCipher`.

Symmetric ciphers use **AEAD** (Authenticated Encryption with Associated Data):
encryption and integrity in one step.  If a single byte of the token is
altered, decryption raises instead of returning garbage.  Two AEAD algorithms
are offered:

* ``aes-256-gcm``        — hardware-accelerated on virtually all modern CPUs.
* ``chacha20-poly1305``  — fast in pure software, constant-time, no timing
                           side-channels; a great pick when AES-NI is absent.

:class:`RsaHybridCipher` adds asymmetric (public-key) encryption: a fresh random
data key encrypts the payload with AEAD, and only that small data key is wrapped
with RSA-OAEP.  This is *hybrid encryption* — it sidesteps RSA's tiny size limit
so you can seal payloads of any length with a public key and decrypt them with
the matching private key.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod

from .envelope import b64d, b64e, decode_token, encode_token
from .errors import CipherKitError, DecryptionError, MissingKeyError
from .kdf import default_kdf, derive_from_meta, derive_key
from .key_sources import KeySource, RawSecret

__all__ = [
    "Cipher",
    "IdentityCipher",
    "PasswordCipher",
    "RsaHybridCipher",
    "LayeredCipher",
]

# Domain-separation tag bound into every AEAD operation as associated data.
_AAD = b"isd-py-framework-sdk/cipher_kit/CK1"
_NONCE_LEN = 12  # 96-bit nonce — the standard size for both GCM and ChaCha20

_AEAD_ALIASES = {
    "aes": "aes-256-gcm",
    "aes-gcm": "aes-256-gcm",
    "aes256": "aes-256-gcm",
    "aes-256-gcm": "aes-256-gcm",
    "chacha": "chacha20-poly1305",
    "chacha20": "chacha20-poly1305",
    "chacha20-poly1305": "chacha20-poly1305",
}


def _normalise_aead(name: str) -> str:
    key = name.lower().replace("_", "-")
    if key not in _AEAD_ALIASES:
        raise CipherKitError(
            f"Unknown AEAD cipher {name!r}. Use 'aes-256-gcm' or 'chacha20-poly1305'."
        )
    return _AEAD_ALIASES[key]


def _aead(name: str, key: bytes):
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305

    return AESGCM(key) if name == "aes-256-gcm" else ChaCha20Poly1305(key)


class Cipher(ABC):
    """Common interface: ``bytes`` ↔ self-describing ``CK1`` token string."""

    @abstractmethod
    def seal(self, data: bytes) -> str: ...

    @abstractmethod
    def unseal(self, token: str) -> bytes: ...


class IdentityCipher(Cipher):
    """No encryption — a passthrough placeholder for composition / testing."""

    def seal(self, data: bytes) -> str:
        return encode_token({"cipher": "identity"}, data)

    def unseal(self, token: str) -> bytes:
        _, ciphertext = decode_token(token)
        return ciphertext


class PasswordCipher(Cipher):
    """Passphrase-based symmetric encryption: KDF + AEAD.

    Parameters
    ----------
    password:
        Convenience shorthand — wrapped in a :class:`RawSecret`.
    key_source:
        Any :class:`KeySource` (preferred for real deployments — keep the
        passphrase out of the ciphertext's file).
    aead:
        ``"aes-256-gcm"`` (default) or ``"chacha20-poly1305"``.
    kdf:
        ``"argon2id"`` / ``"scrypt"`` / ``"pbkdf2-sha256"``.  ``None`` (default)
        picks the strongest available (argon2id if installed, else scrypt).
    **kdf_params:
        Override KDF cost parameters, e.g. ``time_cost=4`` or ``n=2**16``.
    """

    def __init__(
        self,
        password: str | None = None,
        *,
        key_source: KeySource | None = None,
        aead: str = "aes-256-gcm",
        kdf: str | None = None,
        **kdf_params,
    ):
        if key_source is None and password is not None:
            key_source = RawSecret(password)
        self._key_source = key_source
        self._aead = _normalise_aead(aead)
        self._kdf = kdf
        self._kdf_params = kdf_params

    def _passphrase(self) -> bytes:
        if self._key_source is None:
            raise MissingKeyError("PasswordCipher needs a password= or key_source=.")
        return self._key_source.get_secret().encode("utf-8")

    def seal(self, data: bytes) -> str:
        algorithm = self._kdf or default_kdf()
        key, kdf_meta = derive_key(
            self._passphrase(), algorithm=algorithm, params=self._kdf_params or None
        )
        nonce = os.urandom(_NONCE_LEN)
        ciphertext = _aead(self._aead, key).encrypt(nonce, data, _AAD)
        header = {"cipher": self._aead, "kdf": kdf_meta, "nonce": b64e(nonce)}
        return encode_token(header, ciphertext)

    def unseal(self, token: str) -> bytes:
        header, ciphertext = decode_token(token)
        name = header.get("cipher")
        if name not in ("aes-256-gcm", "chacha20-poly1305"):
            raise CipherKitError(f"PasswordCipher cannot unseal a {name!r} token.")
        key = derive_from_meta(self._passphrase(), header["kdf"])
        nonce = b64d(header["nonce"])
        try:
            return _aead(name, key).decrypt(nonce, ciphertext, _AAD)
        except Exception as exc:  # noqa: BLE001
            raise DecryptionError(
                "Decryption failed — wrong passphrase or tampered token."
            ) from exc


class RsaHybridCipher(Cipher):
    """Hybrid public-key encryption (RSA-OAEP wraps an AEAD data key).

    Provide ``public_key`` to :meth:`seal` and ``private_key`` to
    :meth:`unseal`.  Keys may be PEM ``str``/``bytes`` or already-loaded
    ``cryptography`` key objects.  Generate a pair with
    :func:`cipher_kit.generate_rsa_keypair`.
    """

    def __init__(self, *, public_key=None, private_key=None, aead: str = "aes-256-gcm"):
        self._public = public_key
        self._private = private_key
        self._aead = _normalise_aead(aead)

    @staticmethod
    def _oaep():
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        return padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        )

    def _load_public(self):
        if self._public is None:
            raise MissingKeyError("RsaHybridCipher.seal needs public_key=.")
        if hasattr(self._public, "encrypt"):
            return self._public
        from cryptography.hazmat.primitives.serialization import load_pem_public_key

        pem = self._public
        return load_pem_public_key(pem.encode() if isinstance(pem, str) else pem)

    def _load_private(self):
        if self._private is None:
            raise MissingKeyError("RsaHybridCipher.unseal needs private_key=.")
        if hasattr(self._private, "decrypt"):
            return self._private
        from cryptography.hazmat.primitives.serialization import load_pem_private_key

        pem = self._private
        return load_pem_private_key(pem.encode() if isinstance(pem, str) else pem, password=None)

    def seal(self, data: bytes) -> str:
        public_key = self._load_public()
        data_key = os.urandom(32)
        nonce = os.urandom(_NONCE_LEN)
        ciphertext = _aead(self._aead, data_key).encrypt(nonce, data, _AAD)
        wrapped = public_key.encrypt(data_key, self._oaep())
        header = {
            "cipher": "rsa-hybrid",
            "aead": self._aead,
            "wrapped_key": b64e(wrapped),
            "nonce": b64e(nonce),
        }
        return encode_token(header, ciphertext)

    def unseal(self, token: str) -> bytes:
        header, ciphertext = decode_token(token)
        if header.get("cipher") != "rsa-hybrid":
            raise CipherKitError("Not an rsa-hybrid token.")
        private_key = self._load_private()
        try:
            data_key = private_key.decrypt(b64d(header["wrapped_key"]), self._oaep())
            return _aead(header["aead"], data_key).decrypt(
                b64d(header["nonce"]), ciphertext, _AAD
            )
        except Exception as exc:  # noqa: BLE001
            raise DecryptionError(
                "RSA-hybrid decryption failed — wrong key or tampered token."
            ) from exc


class LayeredCipher(Cipher):
    """Compose ciphers into an onion: seal applies layers in order, unseal peels
    them in reverse.

    Because each layer emits its own self-describing token, the layers can mix
    algorithms and keys freely — e.g. an inner passphrase layer wrapped by an
    outer RSA layer for a "two people must cooperate" scheme::

        kit = CipherKit.layered([
            PasswordCipher(key_source=OsKeyring("app", "prod")),
            RsaHybridCipher(public_key=pub),  # outer
        ])

    To unseal you reconstruct the *same* LayeredCipher (it holds the recipe and
    the necessary keys).
    """

    def __init__(self, layers: list[Cipher]):
        if not layers:
            raise CipherKitError("LayeredCipher needs at least one layer.")
        self.layers = list(layers)

    def seal(self, data: bytes) -> str:
        current = data
        for layer in self.layers:
            current = layer.seal(current).encode("utf-8")
        return current.decode("utf-8")

    def unseal(self, token: str) -> bytes:
        ordered = list(reversed(self.layers))
        result = b""
        current = token
        for index, layer in enumerate(ordered):
            result = layer.unseal(current)
            if index < len(ordered) - 1:
                current = result.decode("utf-8")
        return result
