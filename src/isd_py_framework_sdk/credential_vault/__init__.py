"""
isd_py_framework_sdk.credential_vault
=====================================
Convenient, environment-aware loading of configuration and secrets from
``.env`` / YAML / JSON / OS environment variables — with **transparent
decryption** of values sealed by :mod:`isd_py_framework_sdk.cipher_kit`.

Quick start — one-shot read::

    from isd_py_framework_sdk.credential_vault import load_secret

    db_url  = load_secret("DATABASE_URL")                 # plain value from .env / os.environ
    api_key = load_secret("OPENAI_API_KEY", password="my-passphrase")  # auto-unsealed

Multi-source waterfall (first hit wins; os.environ overrides files)::

    from isd_py_framework_sdk.credential_vault import CredentialVault
    from isd_py_framework_sdk.cipher_kit import OsKeyring

    vault = CredentialVault(["os_env", ".env", "config.yaml", "secrets.json"])
    host = vault.get("database.host")                       # nested key from YAML/JSON
    pw   = vault.get("DB_PASSWORD", key_source=OsKeyring("my-app", "prod"))

Typical workflow with :mod:`cipher_kit`:

1. Once, seal the secret and paste the token into ``.env``::

       from isd_py_framework_sdk.cipher_kit import seal
       print(seal("sk-real-key", password="my-passphrase"))   # OPENAI_API_KEY=CK1....

2. At runtime, read it back — supplying the passphrase from a *separate*
   channel (env var, OS keyring, prompt) so it never sits next to the token.

Discovery is PyInstaller-aware: when frozen, files are also looked up next to
the executable.  Reading plain values never imports ``cryptography``; the
crypto import happens only when a sealed token is actually unsealed.
"""
from __future__ import annotations

from .discovery import find_config_file, is_frozen
from .sources import (
    ChainSource,
    ConfigSource,
    DotEnvSource,
    JsonSource,
    OsEnvSource,
    YamlSource,
)
from .vault import CredentialVault, load_secret

__all__ = [
    # façade
    "CredentialVault",
    "load_secret",
    # sources
    "ConfigSource",
    "OsEnvSource",
    "DotEnvSource",
    "YamlSource",
    "JsonSource",
    "ChainSource",
    # discovery
    "find_config_file",
    "is_frozen",
]
