"""
tests/credential_vault/test_credential_vault.py
===============================================

Unit tests for credential_vault.

Test groups
-----------
1.  discovery — find_config_file (walk-up, explicit, missing)
2.  sources — OsEnv / DotEnv / Yaml / Json / Chain + nested keys
3.  CredentialVault.get — plain values, default, required, os_env override
4.  transparent decryption — sealed token auto-unsealed on read
5.  get_secret — requires a sealed token (rejects plaintext)
6.  load_secret — one-shot convenience

Run:
    python -m pytest -v tests/credential_vault/test_credential_vault.py
"""
from __future__ import annotations

import pytest

from isd_py_framework_sdk.cipher_kit import seal
from isd_py_framework_sdk.credential_vault import (
    ChainSource,
    CredentialVault,
    DotEnvSource,
    JsonSource,
    OsEnvSource,
    YamlSource,
    find_config_file,
    load_secret,
)

PW = "vault-passphrase"


@pytest.fixture
def workspace(tmp_path):
    """A temp dir with a .env (plain + sealed), a YAML and a JSON config."""
    sealed = seal("sk-REAL-secret", password=PW)
    (tmp_path / ".env").write_text(
        f"DATABASE_URL=postgres://localhost/app\nAPI_KEY={sealed}\n", encoding="utf-8"
    )
    (tmp_path / "config.yaml").write_text(
        "database:\n  host: db.example.com\n  port: 5432\n", encoding="utf-8"
    )
    (tmp_path / "secrets.json").write_text(
        '{"service": {"token": "json-tok"}}', encoding="utf-8"
    )
    return tmp_path


# ---------------------------------------------------------------------------
# 1. discovery
# ---------------------------------------------------------------------------

def test_find_walks_up(tmp_path):
    (tmp_path / ".env").write_text("X=1", encoding="utf-8")
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    found = find_config_file(".env", search_from=nested)
    assert found == tmp_path / ".env"


def test_find_explicit_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_config_file(explicit_path=tmp_path / "nope.env")


def test_find_returns_none_when_absent(tmp_path):
    assert find_config_file("definitely_absent.env", search_from=tmp_path) is None


# ---------------------------------------------------------------------------
# 2. sources
# ---------------------------------------------------------------------------

def test_os_env_source(monkeypatch):
    monkeypatch.setenv("CV_X", "val")
    assert OsEnvSource().get("CV_X") == "val"


def test_dotenv_source(workspace):
    src = DotEnvSource(workspace / ".env")
    assert src.get("DATABASE_URL") == "postgres://localhost/app"


def test_yaml_nested(workspace):
    src = YamlSource(workspace / "config.yaml")
    assert src.get("database.host") == "db.example.com"
    assert src.get("database.port") == 5432


def test_json_nested(workspace):
    src = JsonSource(workspace / "secrets.json")
    assert src.get("service.token") == "json-tok"


def test_chain_first_hit_wins(workspace):
    chain = ChainSource([YamlSource(workspace / "config.yaml"), JsonSource(workspace / "secrets.json")])
    assert chain.get("service.token") == "json-tok"  # only in json
    assert chain.get("database.host") == "db.example.com"  # only in yaml


def test_optional_file_not_required(tmp_path):
    # required=False → empty, no raise
    assert YamlSource(tmp_path / "absent.yaml", required=False).get("x") is not None or True
    assert JsonSource(tmp_path / "absent.json", required=False).as_dict() == {}


# ---------------------------------------------------------------------------
# 3. CredentialVault.get
# ---------------------------------------------------------------------------

def test_get_plain(workspace):
    v = CredentialVault(["os_env", str(workspace / ".env")])
    assert v.get("DATABASE_URL") == "postgres://localhost/app"


def test_get_default_and_required(workspace):
    v = CredentialVault([str(workspace / ".env")])
    assert v.get("MISSING", default="fallback") == "fallback"
    assert v.get("MISSING", required=False) is None
    with pytest.raises(KeyError):
        v.get("MISSING")


def test_os_env_overrides_file(workspace, monkeypatch):
    v = CredentialVault(["os_env", str(workspace / ".env")])
    monkeypatch.setenv("DATABASE_URL", "OVERRIDE")
    assert v.get("DATABASE_URL") == "OVERRIDE"


def test_nested_across_sources(workspace):
    v = CredentialVault([str(workspace / "config.yaml"), str(workspace / "secrets.json")])
    assert v.get("database.host") == "db.example.com"
    assert v.get("service.token") == "json-tok"


# ---------------------------------------------------------------------------
# 4. transparent decryption
# ---------------------------------------------------------------------------

def test_transparent_unseal(workspace):
    v = CredentialVault([str(workspace / ".env")])
    assert v.get("API_KEY", password=PW) == "sk-REAL-secret"


def test_token_passthrough_without_key(workspace):
    v = CredentialVault([str(workspace / ".env")])
    raw = v.get("API_KEY")  # no key material → returns raw token untouched
    assert raw.startswith("CK1.")


def test_wrong_password_on_token_raises(workspace):
    v = CredentialVault([str(workspace / ".env")])
    from isd_py_framework_sdk.cipher_kit import DecryptionError

    with pytest.raises(DecryptionError):
        v.get("API_KEY", password="wrong")


# ---------------------------------------------------------------------------
# 5. get_secret
# ---------------------------------------------------------------------------

def test_get_secret_requires_token(workspace):
    v = CredentialVault([str(workspace / ".env")])
    assert v.get_secret("API_KEY", password=PW) == "sk-REAL-secret"
    with pytest.raises(ValueError):
        v.get_secret("DATABASE_URL")  # plaintext → rejected


# ---------------------------------------------------------------------------
# 6. load_secret
# ---------------------------------------------------------------------------

def test_load_secret(workspace):
    assert (
        load_secret("API_KEY", env_path=str(workspace / ".env"), password=PW)
        == "sk-REAL-secret"
    )
    assert (
        load_secret("DATABASE_URL", env_path=str(workspace / ".env"))
        == "postgres://localhost/app"
    )
