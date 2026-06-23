"""
tests/cipher_kit/test_cipher_kit.py
===================================

Unit tests for cipher_kit.

Test groups
-----------
1.  envelope — token format, is_token, decode/encode round-trip
2.  seal/unseal — password round-trip, wrong-key failure, non-determinism
3.  AEAD + KDF variants — aes-gcm / chacha20 × argon2id / scrypt / pbkdf2
4.  tamper detection — flipped ciphertext / header fails authentication
5.  key sources — RawSecret / EnvSecret / KeyFileSource
6.  RSA hybrid — keypair seal/unseal, large payloads, wrong key
7.  LayeredCipher — multi-layer compose / peel
8.  CipherKit object — password / rsa / layered factories
9.  bytes payloads + as_bytes round-trip

Run:
    python -m pytest -v tests/cipher_kit/test_cipher_kit.py
"""
from __future__ import annotations

import pytest

from isd_py_framework_sdk.cipher_kit import (
    CipherKit,
    DecryptionError,
    EnvSecret,
    IdentityCipher,
    InvalidTokenError,
    KeyFileSource,
    LayeredCipher,
    MissingKeyError,
    PasswordCipher,
    RawSecret,
    RsaHybridCipher,
    decode_token,
    default_kdf,
    generate_rsa_keypair,
    have_argon2,
    is_token,
    seal,
    unseal,
)
from isd_py_framework_sdk.cipher_kit.envelope import PREFIX, encode_token

PW = "correct horse battery staple"


# ---------------------------------------------------------------------------
# 1. envelope
# ---------------------------------------------------------------------------

def test_token_format_and_is_token():
    token = encode_token({"cipher": "identity"}, b"hello")
    assert token.startswith(PREFIX + ".")
    assert token.count(".") == 2
    assert is_token(token)
    header, body = decode_token(token)
    assert header == {"cipher": "identity"}
    assert body == b"hello"


@pytest.mark.parametrize("bad", ["", "not-a-token", "CK1.only-two", "XX1.a.b", 123, None])
def test_is_token_rejects_garbage(bad):
    assert not is_token(bad)


def test_decode_invalid_raises():
    with pytest.raises(InvalidTokenError):
        decode_token("totally.not.valid")


# ---------------------------------------------------------------------------
# 2. seal / unseal basics
# ---------------------------------------------------------------------------

def test_password_round_trip():
    token = seal("sk-my-real-api-key", password=PW)
    assert is_token(token)
    assert unseal(token, password=PW) == "sk-my-real-api-key"


def test_wrong_password_raises():
    token = seal("secret", password=PW)
    with pytest.raises(DecryptionError):
        unseal(token, password="wrong")


def test_non_deterministic():
    # Same plaintext + passphrase must yield different tokens (random salt+nonce).
    a = seal("same", password=PW)
    b = seal("same", password=PW)
    assert a != b
    assert unseal(a, password=PW) == unseal(b, password=PW) == "same"


def test_seal_requires_key_material():
    with pytest.raises(MissingKeyError):
        seal("x")


# ---------------------------------------------------------------------------
# 3. AEAD + KDF variants
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("aead", ["aes-256-gcm", "aes", "chacha20", "chacha20-poly1305"])
def test_aead_variants(aead):
    token = seal("payload", password=PW, aead=aead, kdf="scrypt")
    assert unseal(token, password=PW) == "payload"


@pytest.mark.parametrize("kdf", ["scrypt", "pbkdf2-sha256"])
def test_kdf_variants(kdf):
    token = seal("payload", password=PW, kdf=kdf)
    header, _ = decode_token(token)
    assert header["kdf"]["algorithm"] == kdf
    assert unseal(token, password=PW) == "payload"


@pytest.mark.skipif(not have_argon2(), reason="argon2-cffi not installed")
def test_argon2id_with_custom_cost():
    token = seal("payload", password=PW, kdf="argon2id", time_cost=2)
    header, _ = decode_token(token)
    assert header["kdf"]["algorithm"] == "argon2id"
    assert header["kdf"]["time_cost"] == 2
    assert unseal(token, password=PW) == "payload"


def test_default_kdf_is_strongest_available():
    assert default_kdf() == ("argon2id" if have_argon2() else "scrypt")


# ---------------------------------------------------------------------------
# 4. tamper detection
# ---------------------------------------------------------------------------

def test_tampered_body_fails():
    token = seal("secret", password=PW)
    head, body = token.rsplit(".", 1)
    # Flip the FIRST body char — it always alters decoded byte 0 (unlike the
    # last char, whose low bits are redundant in unpadded base64url).
    flipped = "B" if body[0] != "B" else "C"
    tampered = f"{head}.{flipped}{body[1:]}"
    with pytest.raises(DecryptionError):
        unseal(tampered, password=PW)


# ---------------------------------------------------------------------------
# 5. key sources
# ---------------------------------------------------------------------------

def test_raw_secret_empty_raises():
    with pytest.raises(MissingKeyError):
        RawSecret("").get_secret()


def test_env_secret(monkeypatch):
    monkeypatch.setenv("CK_TEST_PASS", PW)
    token = seal("v", key_source=EnvSecret("CK_TEST_PASS"))
    assert unseal(token, key_source=EnvSecret("CK_TEST_PASS")) == "v"


def test_env_secret_missing(monkeypatch):
    monkeypatch.delenv("CK_TEST_PASS_MISSING", raising=False)
    with pytest.raises(MissingKeyError):
        EnvSecret("CK_TEST_PASS_MISSING").get_secret()


def test_key_file_source(tmp_path):
    keyfile = tmp_path / "secret.key"
    keyfile.write_text("  " + PW + "  \n", encoding="utf-8")  # whitespace is stripped
    token = seal("v", key_source=KeyFileSource(keyfile))
    assert unseal(token, key_source=KeyFileSource(keyfile)) == "v"


# ---------------------------------------------------------------------------
# 6. RSA hybrid
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rsa_keys():
    return generate_rsa_keypair(bits=2048)  # smaller = faster for tests


def test_rsa_hybrid_round_trip(rsa_keys):
    priv, pub = rsa_keys
    token = seal("secret", public_key=pub)
    assert unseal(token, private_key=priv) == "secret"


def test_rsa_hybrid_large_payload(rsa_keys):
    # RSA alone caps at ~200 bytes; hybrid handles any size.
    priv, pub = rsa_keys
    big = "A" * 100_000
    token = seal(big, public_key=pub)
    assert unseal(token, private_key=priv) == big


def test_rsa_wrong_key_raises(rsa_keys):
    _priv, pub = rsa_keys
    other_priv, _ = generate_rsa_keypair(bits=2048)
    token = seal("secret", public_key=pub)
    with pytest.raises(DecryptionError):
        unseal(token, private_key=other_priv)


# ---------------------------------------------------------------------------
# 7. LayeredCipher
# ---------------------------------------------------------------------------

def test_layered_password_then_rsa(rsa_keys):
    priv, pub = rsa_keys
    sealer = LayeredCipher([PasswordCipher(password="inner"), RsaHybridCipher(public_key=pub)])
    token = sealer.seal(b"top-secret")
    unsealer = LayeredCipher([PasswordCipher(password="inner"), RsaHybridCipher(private_key=priv)])
    assert unsealer.unseal(token) == b"top-secret"


def test_layered_three_passwords():
    layers = [PasswordCipher(password=p) for p in ("a", "b", "c")]
    sealer = LayeredCipher(layers)
    token = sealer.seal(b"deep")
    assert LayeredCipher([PasswordCipher(password=p) for p in ("a", "b", "c")]).unseal(token) == b"deep"


def test_layered_wrong_inner_fails():
    sealer = LayeredCipher([PasswordCipher(password="a"), PasswordCipher(password="b")])
    token = sealer.seal(b"x")
    bad = LayeredCipher([PasswordCipher(password="WRONG"), PasswordCipher(password="b")])
    with pytest.raises(DecryptionError):
        bad.unseal(token)


# ---------------------------------------------------------------------------
# 8. CipherKit object
# ---------------------------------------------------------------------------

def test_cipherkit_password_reuse():
    kit = CipherKit.password(password=PW, aead="chacha20")
    a, b = kit.seal("a"), kit.seal("b")
    assert kit.unseal(a) == "a" and kit.unseal(b) == "b"


def test_cipherkit_rsa(rsa_keys):
    priv, pub = rsa_keys
    enc = CipherKit.rsa(public_key=pub)
    dec = CipherKit.rsa(private_key=priv)
    assert dec.unseal(enc.seal("hi")) == "hi"


def test_cipherkit_layered_accepts_cipherkit(rsa_keys):
    priv, pub = rsa_keys
    enc = CipherKit.layered([CipherKit.password(password="x"), RsaHybridCipher(public_key=pub)])
    dec = CipherKit.layered([CipherKit.password(password="x"), RsaHybridCipher(private_key=priv)])
    assert dec.unseal(enc.seal("y")) == "y"


# ---------------------------------------------------------------------------
# 9. bytes payloads
# ---------------------------------------------------------------------------

def test_bytes_round_trip():
    blob = bytes(range(256))
    token = seal(blob, password=PW)
    assert unseal(token, password=PW, as_bytes=True) == blob


def test_identity_cipher_passthrough():
    token = IdentityCipher().seal(b"plain")
    assert IdentityCipher().unseal(token) == b"plain"
    # module-level unseal recognises identity tokens
    assert unseal(token, as_bytes=True) == b"plain"
