"""
examples/cipher_kit/quickstart.py
=================================
End-to-end demo of cipher_kit + credential_vault: seal a secret, store it in a
.env file, then load it back with transparent decryption — the exact workflow
you'd use in a real project.

Run:
    .venv\\Scripts\\python.exe examples/cipher_kit/quickstart.py

Requires extras: cipher_kit (+ cipher_kit.argon2 for the argon2id demo),
                 credential_vault.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from isd_py_framework_sdk.cipher_kit import (
    CipherKit,
    PasswordCipher,
    RsaHybridCipher,
    generate_rsa_keypair,
    seal,
    unseal,
)
from isd_py_framework_sdk.credential_vault import CredentialVault, load_secret

PASSPHRASE = "correct horse battery staple"


def demo_basic():
    print("\n=== 1) Basic password seal/unseal ===")
    token = seal("sk-my-real-api-key", password=PASSPHRASE)
    print("sealed token :", token[:48], "...")
    print("unsealed      :", unseal(token, password=PASSPHRASE))
    print("note: sealing again gives a DIFFERENT token (random salt/nonce):")
    print("  ", seal("sk-my-real-api-key", password=PASSPHRASE)[:48], "...")


def demo_store_and_load():
    print("\n=== 2) Store in .env, load with transparent decryption ===")
    workdir = Path(tempfile.mkdtemp())
    env_file = workdir / ".env"

    # ---- one-time: seal the secret and write it into .env ----
    token = seal("sk-real-openai-key", password=PASSPHRASE)
    env_file.write_text(
        f"DATABASE_URL=postgres://localhost/app\nOPENAI_API_KEY={token}\n",
        encoding="utf-8",
    )
    print(".env written to:", env_file)

    # ---- at runtime: read it back ----
    vault = CredentialVault(["os_env", str(env_file)])
    print("plain value   :", vault.get("DATABASE_URL"))
    print("decrypted key :", vault.get("OPENAI_API_KEY", password=PASSPHRASE))
    print("via load_secret:", load_secret("OPENAI_API_KEY", env_path=str(env_file), password=PASSPHRASE))


def demo_rsa():
    print("\n=== 3) Asymmetric (RSA hybrid) — seal with public, unseal with private ===")
    priv, pub = generate_rsa_keypair(bits=2048)
    token = seal("any-length-payload " * 50, public_key=pub)
    print("payload recovered:", unseal(token, private_key=priv)[:30], "...")


def demo_layered():
    print("\n=== 4) Multi-layer composition (password inside, RSA outside) ===")
    priv, pub = generate_rsa_keypair(bits=2048)
    sealer = CipherKit.layered([PasswordCipher(password="inner"), RsaHybridCipher(public_key=pub)])
    unsealer = CipherKit.layered([PasswordCipher(password="inner"), RsaHybridCipher(private_key=priv)])
    token = sealer.seal("top-secret")
    print("layered unseal:", unsealer.unseal(token))


if __name__ == "__main__":
    demo_basic()
    demo_store_and_load()
    demo_rsa()
    demo_layered()
    print("\nAll demos completed.")
