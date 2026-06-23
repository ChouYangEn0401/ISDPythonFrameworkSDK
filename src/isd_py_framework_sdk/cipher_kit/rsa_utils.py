"""Helpers for generating RSA key material for :class:`RsaHybridCipher`."""
from __future__ import annotations

__all__ = ["generate_rsa_keypair"]


def generate_rsa_keypair(bits: int = 3072) -> tuple[str, str]:
    """Generate a fresh RSA key pair.

    Returns ``(private_pem, public_pem)`` as PEM strings.  Keep the private PEM
    secret (ideally in an OS keyring or a permission-restricted file); the
    public PEM can be distributed freely to anyone who needs to *seal* secrets
    for you.

    ``bits=3072`` (~128-bit security) is a sound default; use ``4096`` for a
    longer safety margin at the cost of slower operations.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = (
        key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )
    return private_pem, public_pem
