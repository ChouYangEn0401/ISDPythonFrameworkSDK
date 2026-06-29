"""
tests/interop/test_interop.py
=============================

Unit tests for the interop bridge layer.

Test groups
-----------
1.  has_feature / require_feature happy path (backend installed)
2.  unknown feature → KeyError
3.  simulated missing backend → MissingOptionalDependencyError with the exact
    `pip install ...[extra]` message, while merely importing a sub-package that
    *uses* the bridge does NOT raise
4.  credential_vault reads plain text without ever touching the cipher_kit bridge

Run:
    .venv\\Scripts\\python.exe -m pytest -q tests/interop
"""
from __future__ import annotations

import importlib

import pytest

from isd_py_framework_sdk.interop import (
    FEATURE_EXTRAS,
    FEATURE_PROBES,
    MissingOptionalDependencyError,
    has_feature,
    require_feature,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _block_import(monkeypatch, blocked: str) -> None:
    """Make ``import <blocked>`` (and importlib.import_module) fail, as if the
    third-party backend were not installed."""
    real = importlib.import_module

    def fake(name, *args, **kwargs):
        top = name.split(".")[0]
        if top == blocked:
            raise ImportError(f"simulated missing backend: {blocked}")
        return real(name, *args, **kwargs)

    # Both _optional.require and _bridges call importlib.import_module via the
    # shared importlib module object, so patching here covers both.
    monkeypatch.setattr(importlib, "import_module", fake)


# ---------------------------------------------------------------------------
# 1. happy path
# ---------------------------------------------------------------------------

def test_has_feature_true_when_backend_present():
    # cryptography / openpyxl are installed in the dev env ([all]).
    assert has_feature("cipher_kit") is True
    assert has_feature("excel_painter") is True


def test_require_feature_returns_module():
    cipher_kit = require_feature("cipher_kit")
    assert hasattr(cipher_kit, "seal")
    assert hasattr(cipher_kit, "unseal")
    # round-trip proves we got the real sub-package back
    token = cipher_kit.seal("x", password="pw")
    assert cipher_kit.unseal(token, password="pw") == "x"


def test_registry_keys_consistent():
    assert set(FEATURE_EXTRAS) == set(FEATURE_PROBES)


# ---------------------------------------------------------------------------
# 2. unknown feature
# ---------------------------------------------------------------------------

def test_unknown_feature_raises_keyerror():
    with pytest.raises(KeyError):
        require_feature("does_not_exist")
    with pytest.raises(KeyError):
        has_feature("does_not_exist")


# ---------------------------------------------------------------------------
# 3. simulated missing backend
# ---------------------------------------------------------------------------

def test_require_feature_missing_backend_message(monkeypatch):
    _block_import(monkeypatch, "cryptography")
    assert has_feature("cipher_kit") is False
    with pytest.raises(MissingOptionalDependencyError) as exc:
        require_feature("cipher_kit")
    msg = str(exc.value)
    assert "pip install isd-py-framework-sdk[cipher_kit]" in msg


def test_importing_consumer_does_not_trip_bridge(monkeypatch):
    # Even with the backend "missing", importing a sub-package that *uses* the
    # bridge must not raise — the dependency is demanded only on the cross-call.
    _block_import(monkeypatch, "cryptography")
    mod = importlib.import_module("isd_py_framework_sdk.credential_vault")
    assert hasattr(mod, "CredentialVault")


# ---------------------------------------------------------------------------
# 4. plain text never touches cipher_kit
# ---------------------------------------------------------------------------

def test_plain_value_does_not_require_cipher_kit(monkeypatch, tmp_path):
    from isd_py_framework_sdk.credential_vault import CredentialVault

    env = tmp_path / ".env"
    env.write_text("DATABASE_URL=postgres://localhost/app\n", encoding="utf-8")

    _block_import(monkeypatch, "cryptography")  # crypto unavailable
    vault = CredentialVault([str(env)])
    # Reading a plain value must succeed without the bridge being reached.
    assert vault.get("DATABASE_URL") == "postgres://localhost/app"
