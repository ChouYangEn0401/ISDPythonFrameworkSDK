"""
tests/smoke/test_smoke.py
=========================
Cross-cutting **smoke / health-check** for the whole SDK — a fast "is everything
wired up?" checkpoint. It consolidates the ad-hoc verification done during the
0.9.0 API pass into one re-runnable suite covering this release's surface:

* every subpackage + short-path shim imports cleanly;
* the ``interop`` bridge layer (registry, capability probe, and the
  partial-install error message);
* the new ``cipher_kit`` ciphers (Fernet / RawKey / AES-SIV / AES-GCM-SIV)
  round-trip and module-level dispatch;
* the ``credential_vault`` ``prompt_password`` sugar;
* the ``unified_io`` → ``excel_painter`` styled/preserve bridge;
* the ``monitoring`` → ``message_logger`` type-only decoupling.

Run it any time as a regression checkpoint::

    .venv\\Scripts\\python.exe -m pytest -q tests/smoke

Assumes a full ``[all]`` dev install (heavy-backend tests ``importorskip`` their
backend, so missing extras skip rather than fail).  The *partial-install
behaviour itself* is asserted explicitly in
:func:`test_interop_partial_install_message`.
"""
from __future__ import annotations

import importlib

import pytest

# Subpackages + backward-compat short-path shims. All must import with no heavy
# third-party dependency required (the core "zero-heavy-dep import" promise).
SUBPACKAGES = [
    "base", "events", "message_logger", "monitoring", "file_compare",
    "path_manager", "unified_io", "excel_painter", "cipher_kit",
    "credential_vault", "helpers", "window_design_helper", "interop",
    # short-path shims
    "interface", "events_bus", "msg_logger", "assertions", "decorators", "exceptions",
]


# ---------------------------------------------------------------------------
# 1. import health
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackage_imports(name):
    importlib.import_module(f"isd_py_framework_sdk.{name}")


def test_top_level_version_present():
    import isd_py_framework_sdk as isd

    assert isd.__version__  # non-empty string


# ---------------------------------------------------------------------------
# 2. interop bridge layer
# ---------------------------------------------------------------------------

def test_interop_registry_and_probe():
    from isd_py_framework_sdk.interop import (
        FEATURE_EXTRAS,
        FEATURE_PROBES,
        has_feature,
    )

    assert set(FEATURE_EXTRAS) == set(FEATURE_PROBES)
    assert isinstance(has_feature("cipher_kit"), bool)  # never raises
    with pytest.raises(KeyError):
        has_feature("does_not_exist")


def test_interop_partial_install_message(monkeypatch):
    """A missing backend → standard pip-install message; importing a consumer
    sub-package still does not raise (the partial-install guarantee)."""
    from isd_py_framework_sdk.interop import (
        MissingOptionalDependencyError,
        require_feature,
    )

    real = importlib.import_module

    def fake(name, *args, **kwargs):
        if name.split(".")[0] == "cryptography":
            raise ImportError("simulated missing backend")
        return real(name, *args, **kwargs)

    monkeypatch.setattr(importlib, "import_module", fake)

    # consumer import is still fine even with the backend "missing"
    importlib.import_module("isd_py_framework_sdk.credential_vault")

    with pytest.raises(MissingOptionalDependencyError) as exc:
        require_feature("cipher_kit")
    assert "pip install isd-py-framework-sdk[cipher_kit]" in str(exc.value)


# ---------------------------------------------------------------------------
# 3. cipher_kit new ciphers
# ---------------------------------------------------------------------------

def test_cipher_kit_new_ciphers_roundtrip_and_dispatch():
    pytest.importorskip("cryptography")
    from isd_py_framework_sdk.cipher_kit import (
        CipherKit,
        generate_aead_key,
        generate_aes_siv_key,
        generate_fernet_key,
        seal,
        unseal,
    )

    # RawKey via module-level seal(secret_key=)/unseal
    k = generate_aead_key()
    assert unseal(seal("x", secret_key=k), secret_key=k) == "x"

    # Fernet — factory + module-level dispatch
    fk = generate_fernet_key()
    assert unseal(CipherKit.fernet(fk).seal("y"), secret_key=fk) == "y"

    # AES-GCM-SIV
    gk = generate_aead_key()
    assert unseal(CipherKit.aes_gcm_siv(gk).seal("z"), secret_key=gk) == "z"

    # AES-SIV — deterministic
    sk = generate_aes_siv_key()
    a = CipherKit.aes_siv(sk).seal("same")
    assert a == CipherKit.aes_siv(sk).seal("same")
    assert unseal(a, secret_key=sk) == "same"


# ---------------------------------------------------------------------------
# 4. credential_vault prompt_password sugar
# ---------------------------------------------------------------------------

def test_credential_vault_prompt_password(monkeypatch, tmp_path):
    pytest.importorskip("cryptography")
    pytest.importorskip("dotenv")  # python-dotenv
    import getpass

    from isd_py_framework_sdk.cipher_kit import seal
    from isd_py_framework_sdk.credential_vault import CredentialVault

    pw = "smoke-passphrase"
    token = seal("sk-smoke", password=pw)
    (tmp_path / ".env").write_text(f"K={token}\nPLAIN=hello\n", encoding="utf-8")
    vault = CredentialVault([str(tmp_path / ".env")])

    monkeypatch.setattr(getpass, "getpass", lambda *a, **k: pw)
    assert vault.get("K", prompt_password=True) == "sk-smoke"

    # plain value must NOT prompt
    def boom(*a, **k):
        raise AssertionError("getpass must not be called for a plain value")

    monkeypatch.setattr(getpass, "getpass", boom)
    assert vault.get("PLAIN", prompt_password=True) == "hello"


# ---------------------------------------------------------------------------
# 5. unified_io → excel_painter bridge (styled + preserve)
# ---------------------------------------------------------------------------

def test_unified_io_excel_bridge(tmp_path):
    pd = pytest.importorskip("pandas")
    pytest.importorskip("openpyxl")
    from isd_py_framework_sdk.unified_io import DataIO

    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    dest = tmp_path / "out.xlsx"

    DataIO.write(df, str(dest), mode="styled")  # routes through interop bridge
    assert dest.exists()
    assert len(DataIO.read(str(dest))) == 3

    DataIO.write(df, str(dest), mode="preserve")  # also via the bridge
    assert dest.exists()


# ---------------------------------------------------------------------------
# 6. monitoring → message_logger type-only decoupling
# ---------------------------------------------------------------------------

def test_monitoring_type_only_decoupling():
    import isd_py_framework_sdk.monitoring.looped_function_timer as m

    # LogLevelLiteral is referenced only in annotations → must not be a runtime
    # global (TYPE_CHECKING import).
    assert "LogLevelLiteral" not in vars(m)

    from isd_py_framework_sdk.monitoring import LoopedFunctionTimer

    LoopedFunctionTimer(total=3)  # instantiates without message_logger at runtime
