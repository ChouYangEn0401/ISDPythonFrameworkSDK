"""Where the *passphrase* comes from.

The single biggest security mistake is storing the ciphertext **and** the
passphrase that unlocks it in the same place (e.g. both in ``.env``) — anyone
who reads the file gets both, so the encryption buys you nothing.

A :class:`KeySource` decouples *the secret value* from *where it lives*, so you
can keep the sealed token in a config file but pull the passphrase from a
genuinely separate channel:

* :class:`RawSecret`    — a literal string (handy for tests / quick scripts).
* :class:`EnvSecret`    — an OS environment variable (injected by your CI/deploy
                          system, never written to disk).
* :class:`PromptSecret` — typed in at runtime via ``getpass`` (never stored).
* :class:`KeyFileSource`— a file outside the repo, with restrictive permissions.
* :class:`OsKeyring`    — the OS secure store (Windows Credential Manager /
                          macOS Keychain / Secret Service).  Requires the
                          optional ``keyring`` backend.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .errors import MissingDependencyError, MissingKeyError

__all__ = [
    "KeySource",
    "RawSecret",
    "EnvSecret",
    "PromptSecret",
    "KeyFileSource",
    "OsKeyring",
]


class KeySource(ABC):
    """Abstract provider of a passphrase string."""

    @abstractmethod
    def get_secret(self) -> str:
        """Return the passphrase, or raise :class:`MissingKeyError`."""


class RawSecret(KeySource):
    """A literal passphrase held in memory."""

    def __init__(self, value: str):
        self._value = value

    def get_secret(self) -> str:
        if not self._value:
            raise MissingKeyError("RawSecret was given an empty value.")
        return self._value


class EnvSecret(KeySource):
    """Read the passphrase from an OS environment variable."""

    def __init__(self, var_name: str):
        self.var_name = var_name

    def get_secret(self) -> str:
        import os

        value = os.environ.get(self.var_name)
        if not value:
            raise MissingKeyError(f"Environment variable {self.var_name!r} is not set.")
        return value


class PromptSecret(KeySource):
    """Prompt for the passphrase interactively (never echoed, never stored)."""

    def __init__(self, prompt: str = "Passphrase: ", *, confirm: bool = False):
        self.prompt = prompt
        self.confirm = confirm

    def get_secret(self) -> str:
        import getpass

        value = getpass.getpass(self.prompt)
        if self.confirm and value != getpass.getpass("Confirm passphrase: "):
            raise MissingKeyError("Passphrases did not match.")
        if not value:
            raise MissingKeyError("Empty passphrase entered.")
        return value


class KeyFileSource(KeySource):
    """Read the passphrase from a file (contents are stripped of whitespace)."""

    def __init__(self, path, *, encoding: str = "utf-8"):
        self.path = path
        self.encoding = encoding

    def get_secret(self) -> str:
        from pathlib import Path

        p = Path(self.path).expanduser()
        if not p.exists():
            raise MissingKeyError(f"Key file not found: {p}")
        value = p.read_text(encoding=self.encoding).strip()
        if not value:
            raise MissingKeyError(f"Key file is empty: {p}")
        return value


class OsKeyring(KeySource):
    """Read the passphrase from the OS secure store via the ``keyring`` library.

    Store a secret once (e.g. in a setup script or the shell) and it never
    touches your repo::

        OsKeyring("my-app", "prod").store("super-secret-passphrase")
    """

    def __init__(self, service: str, username: str):
        self.service = service
        self.username = username

    def _keyring(self):
        try:
            import keyring
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise MissingDependencyError(
                "OsKeyring requires 'keyring'. Install with: "
                "pip install isd-py-framework-sdk[cipher_kit.keyring]"
            ) from exc
        return keyring

    def get_secret(self) -> str:
        value = self._keyring().get_password(self.service, self.username)
        if not value:
            raise MissingKeyError(
                f"No secret in the OS keyring for service={self.service!r}, "
                f"username={self.username!r}. Store one first with "
                f"OsKeyring(...).store(secret)."
            )
        return value

    def store(self, secret: str) -> None:
        """Persist *secret* into the OS secure store."""
        self._keyring().set_password(self.service, self.username, secret)

    def delete(self) -> None:
        """Remove the stored secret from the OS secure store."""
        self._keyring().delete_password(self.service, self.username)
