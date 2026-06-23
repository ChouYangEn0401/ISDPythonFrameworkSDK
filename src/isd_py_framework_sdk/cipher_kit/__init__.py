"""
isd_py_framework_sdk.cipher_kit
===============================
A clean, composable toolkit for **sealing** secrets so they can be safely
stored (in ``.env`` / YAML / JSON / anywhere) and later **unsealed**.

Quick start — the two functions you need 90% of the time::

    from isd_py_framework_sdk.cipher_kit import seal, unseal

    token = seal("sk-my-real-api-key", password="correct horse battery staple")
    # → 'CK1.eyJ...' — paste this anywhere; it is self-describing.

    secret = unseal(token, password="correct horse battery staple")
    # → 'sk-my-real-api-key'

Everything advanced is opt-in via keyword arguments, so the simple path stays
simple::

    seal("data", password="pw", aead="chacha20", kdf="argon2id", time_cost=4)

Keep the passphrase out of the ciphertext's file by sourcing it elsewhere::

    from isd_py_framework_sdk.cipher_kit import CipherKit, OsKeyring

    kit = CipherKit.password(key_source=OsKeyring("my-app", "prod"))
    token = kit.seal("db-password")
    secret = kit.unseal(token)

Public-key (asymmetric) sealing, and arbitrary multi-layer composition::

    from isd_py_framework_sdk.cipher_kit import (
        CipherKit, PasswordCipher, RsaHybridCipher, generate_rsa_keypair,
    )

    priv, pub = generate_rsa_keypair()
    token = seal("secret", public_key=pub)         # anyone with pub can seal
    secret = unseal(token, private_key=priv)        # only priv can unseal

    onion = CipherKit.layered([
        PasswordCipher(password="inner"),
        RsaHybridCipher(public_key=pub),            # outer
    ])
    token = onion.seal("top secret")

Design notes
------------
* Tokens are **self-describing** (see :mod:`.envelope`): ``unseal`` reads the
  cipher/KDF/salt/nonce from the token header, so you never have to remember
  how something was sealed.
* Symmetric encryption is **AEAD** (AES-256-GCM or ChaCha20-Poly1305): tampered
  tokens fail loudly instead of decrypting to garbage.
* Passphrases are stretched with a real **KDF** (Argon2id → scrypt → PBKDF2),
  each with a random per-token salt.
* ``import``-ing this package never requires ``cryptography``; the heavy import
  happens only when you actually seal/unseal.  Argon2id needs the
  ``cipher_kit.argon2`` extra; OS keyring needs the ``cipher_kit.keyring`` extra.
"""
from __future__ import annotations

from .ciphers import (
    Cipher,
    IdentityCipher,
    LayeredCipher,
    PasswordCipher,
    RsaHybridCipher,
)
from .envelope import decode_token, is_token
from .errors import (
    CipherKitError,
    DecryptionError,
    InvalidTokenError,
    MissingDependencyError,
    MissingKeyError,
)
from .kdf import default_kdf, have_argon2
from .key_sources import (
    EnvSecret,
    KeyFileSource,
    KeySource,
    OsKeyring,
    PromptSecret,
    RawSecret,
)
from .rsa_utils import generate_rsa_keypair

__all__ = [
    # façade
    "seal",
    "unseal",
    "CipherKit",
    # ciphers
    "Cipher",
    "IdentityCipher",
    "PasswordCipher",
    "RsaHybridCipher",
    "LayeredCipher",
    # key sources
    "KeySource",
    "RawSecret",
    "EnvSecret",
    "PromptSecret",
    "KeyFileSource",
    "OsKeyring",
    # helpers
    "generate_rsa_keypair",
    "is_token",
    "decode_token",
    "default_kdf",
    "have_argon2",
    # errors
    "CipherKitError",
    "InvalidTokenError",
    "DecryptionError",
    "MissingDependencyError",
    "MissingKeyError",
]


def seal(
    data: str | bytes,
    *,
    password: str | None = None,
    key_source: KeySource | None = None,
    public_key=None,
    aead: str = "aes-256-gcm",
    kdf: str | None = None,
    encoding: str = "utf-8",
    **kdf_params,
) -> str:
    """Seal *data* into a self-describing ``CK1`` token string.

    Provide exactly one kind of key material:

    * ``password=`` or ``key_source=``  → passphrase-based symmetric encryption.
    * ``public_key=``                   → RSA hybrid (asymmetric) encryption.

    Advanced knobs (``aead``, ``kdf``, and KDF cost params like ``time_cost``)
    are optional; the defaults are already a sound modern choice.
    """
    raw = data.encode(encoding) if isinstance(data, str) else data
    if public_key is not None:
        cipher: Cipher = RsaHybridCipher(public_key=public_key, aead=aead)
    elif password is not None or key_source is not None:
        cipher = PasswordCipher(
            password=password, key_source=key_source, aead=aead, kdf=kdf, **kdf_params
        )
    else:
        raise MissingKeyError(
            "seal() needs key material: pass password=, key_source=, or public_key=."
        )
    return cipher.seal(raw)


def unseal(
    token: str,
    *,
    password: str | None = None,
    key_source: KeySource | None = None,
    private_key=None,
    encoding: str = "utf-8",
    as_bytes: bool = False,
) -> str | bytes:
    """Unseal a ``CK1`` *token* back to the original secret.

    The cipher used is read from the token itself; just supply the matching key
    material (``password=``/``key_source=`` for symmetric tokens,
    ``private_key=`` for RSA-hybrid tokens).  Returns ``str`` by default, or
    ``bytes`` when ``as_bytes=True``.
    """
    header, _ = decode_token(token)
    name = header.get("cipher")
    if name == "rsa-hybrid":
        cipher: Cipher = RsaHybridCipher(private_key=private_key)
    elif name == "identity":
        cipher = IdentityCipher()
    elif name in ("aes-256-gcm", "chacha20-poly1305"):
        cipher = PasswordCipher(password=password, key_source=key_source)
    else:
        raise InvalidTokenError(f"Unknown cipher in token: {name!r}")
    raw = cipher.unseal(token)
    return raw if as_bytes else raw.decode(encoding)


class CipherKit:
    """A reusable, pre-configured sealer/unsealer.

    Build one with a factory and reuse it for many secrets so the configuration
    (algorithm, key source, layering) lives in one place::

        kit = CipherKit.password(key_source=OsKeyring("app", "prod"))
        a = kit.seal("secret-a")
        b = kit.seal("secret-b")
        assert kit.unseal(a) == "secret-a"
    """

    def __init__(self, cipher: Cipher):
        self.cipher = cipher

    @classmethod
    def password(
        cls,
        password: str | None = None,
        *,
        key_source: KeySource | None = None,
        aead: str = "aes-256-gcm",
        kdf: str | None = None,
        **kdf_params,
    ) -> "CipherKit":
        return cls(
            PasswordCipher(
                password=password, key_source=key_source, aead=aead, kdf=kdf, **kdf_params
            )
        )

    @classmethod
    def rsa(cls, *, public_key=None, private_key=None, aead: str = "aes-256-gcm") -> "CipherKit":
        return cls(RsaHybridCipher(public_key=public_key, private_key=private_key, aead=aead))

    @classmethod
    def layered(cls, layers) -> "CipherKit":
        """Compose layers (``Cipher`` or ``CipherKit`` instances), inner-first."""
        normalised = [item.cipher if isinstance(item, CipherKit) else item for item in layers]
        return cls(LayeredCipher(normalised))

    def seal(self, data: str | bytes, *, encoding: str = "utf-8") -> str:
        raw = data.encode(encoding) if isinstance(data, str) else data
        return self.cipher.seal(raw)

    def unseal(
        self, token: str, *, encoding: str = "utf-8", as_bytes: bool = False
    ) -> str | bytes:
        raw = self.cipher.unseal(token)
        return raw if as_bytes else raw.decode(encoding)
