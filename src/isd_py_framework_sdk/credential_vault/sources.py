"""Config *sources* — uniform read access to where values live.

Each source answers one question: "do you have a value for this key?".  A
missing key is reported with the sentinel :data:`MISSING` (distinct from a key
that genuinely holds ``None``/empty).

Implemented sources:

* :class:`OsEnvSource`  — ``os.environ`` (stdlib, always available).
* :class:`DotEnvSource` — a ``.env`` file (needs ``python-dotenv``; auto-discovers).
* :class:`YamlSource`   — a YAML file (needs ``pyyaml``; supports nested keys).
* :class:`JsonSource`   — a JSON file (stdlib; supports nested keys).
* :class:`ChainSource`  — a waterfall: the first source with the key wins.

Nested access: :class:`YamlSource` and :class:`JsonSource` accept dotted keys,
so ``vault.get("database.password")`` reads ``{"database": {"password": ...}}``.
"""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from .discovery import find_config_file

__all__ = [
    "MISSING",
    "ConfigSource",
    "OsEnvSource",
    "DotEnvSource",
    "YamlSource",
    "JsonSource",
    "ChainSource",
]


class _Missing:
    """Sentinel singleton for 'no value present'."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return "<MISSING>"

    def __bool__(self) -> bool:
        return False


MISSING = _Missing()


def _nested_get(data: dict, key: str):
    """Look up *key* in *data*, supporting dotted paths for nested mappings."""
    if key in data:
        return data[key]
    if "." in key:
        current = data
        for part in key.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return MISSING
        return current
    return MISSING


class ConfigSource(ABC):
    """Abstract read-only key→value source."""

    @abstractmethod
    def get(self, key: str):
        """Return the value for *key*, or :data:`MISSING`."""

    def as_dict(self) -> dict:
        """Best-effort full snapshot (used for debugging / listing keys)."""
        return {}


class OsEnvSource(ConfigSource):
    """Read from the process environment (``os.environ``)."""

    def get(self, key: str):
        return os.environ.get(key, MISSING)

    def as_dict(self) -> dict:
        return dict(os.environ)


class DotEnvSource(ConfigSource):
    """Read from a ``.env`` file.

    With ``path=None`` the file is auto-discovered (walking up from
    ``search_from`` / cwd, and next to the exe when frozen).  Values are cached
    after first load.
    """

    def __init__(
        self,
        path: Optional[str | Path] = None,
        *,
        search_from: Optional[str | Path] = None,
        required: bool = False,
    ):
        self.path = path
        self.search_from = search_from
        self.required = required
        self._cache: Optional[dict] = None

    def _resolve_path(self) -> Optional[Path]:
        if self.path is not None:
            p = Path(self.path).expanduser()
            if not p.exists():
                if self.required:
                    raise FileNotFoundError(f".env file not found: {p}")
                return None
            return p
        return find_config_file(".env", search_from=self.search_from)

    def _load(self) -> dict:
        if self._cache is not None:
            return self._cache
        path = self._resolve_path()
        if path is None:
            if self.required:
                raise FileNotFoundError("No .env file found.")
            self._cache = {}
            return self._cache
        try:
            from dotenv import dotenv_values
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise ImportError(
                "DotEnvSource requires 'python-dotenv'. Install with: "
                "pip install isd-py-framework-sdk[credential_vault]"
            ) from exc
        self._cache = {k: v for k, v in dotenv_values(path).items() if v is not None}
        return self._cache

    def get(self, key: str):
        return self._load().get(key, MISSING)

    def as_dict(self) -> dict:
        return dict(self._load())


class YamlSource(ConfigSource):
    """Read from a YAML file (supports nested/dotted keys)."""

    def __init__(self, path: str | Path, *, required: bool = True):
        self.path = path
        self.required = required
        self._cache: Optional[dict] = None

    def _load(self) -> dict:
        if self._cache is not None:
            return self._cache
        p = Path(self.path).expanduser()
        if not p.exists():
            if self.required:
                raise FileNotFoundError(f"YAML config not found: {p}")
            self._cache = {}
            return self._cache
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise ImportError(
                "YamlSource requires 'pyyaml'. Install with: "
                "pip install isd-py-framework-sdk[credential_vault.yaml]"
            ) from exc
        self._cache = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        return self._cache

    def get(self, key: str):
        return _nested_get(self._load(), key)

    def as_dict(self) -> dict:
        return dict(self._load())


class JsonSource(ConfigSource):
    """Read from a JSON file (supports nested/dotted keys)."""

    def __init__(self, path: str | Path, *, required: bool = True):
        self.path = path
        self.required = required
        self._cache: Optional[dict] = None

    def _load(self) -> dict:
        if self._cache is not None:
            return self._cache
        p = Path(self.path).expanduser()
        if not p.exists():
            if self.required:
                raise FileNotFoundError(f"JSON config not found: {p}")
            self._cache = {}
            return self._cache
        self._cache = json.loads(p.read_text(encoding="utf-8")) or {}
        return self._cache

    def get(self, key: str):
        return _nested_get(self._load(), key)

    def as_dict(self) -> dict:
        return dict(self._load())


class ChainSource(ConfigSource):
    """A waterfall of sources — the first one that has the key wins."""

    def __init__(self, sources):
        self.sources = list(sources)

    def get(self, key: str):
        for source in self.sources:
            value = source.get(key)
            if value is not MISSING and value is not None:
                return value
        return MISSING

    def as_dict(self) -> dict:
        merged: dict = {}
        for source in reversed(self.sources):  # earlier sources override later
            merged.update(source.as_dict())
        return merged
