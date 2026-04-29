"""
unified_io.adapters.json_adapter
==================================
JSON / JSONL read / write adapter backed by pandas.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

import pandas as pd

from ._interface import IIOAdapter


class JsonIOAdapter(IIOAdapter):
    """
    Read / write JSON files.

    Parameters
    ----------
    lines : bool
        ``True`` → JSONL (one JSON object per line).
        ``False`` (default) → standard JSON array / object.
    """

    def __init__(self, lines: bool = False) -> None:
        self._lines = lines

    def read(self, source: str | Path, **kwargs) -> pd.DataFrame:
        """
        Parameters
        ----------
        source
            Path to the JSON / JSONL file.
        **kwargs
            Forwarded to :func:`pandas.read_json`.
            ``lines`` is pre-set from the adapter's constructor but can
            be overridden here.
        """
        kwargs.setdefault("lines", self._lines)
        return pd.read_json(source, **kwargs)

    def write(self, df: pd.DataFrame, destination: str | Path, **kwargs) -> None:
        """
        Parameters
        ----------
        destination
            Output JSON / JSONL path.
        **kwargs
            Forwarded to :meth:`pandas.DataFrame.to_json`.
            ``orient`` defaults to ``"records"``.
            ``lines`` is pre-set from the adapter's constructor.
        """
        kwargs.setdefault("orient", "records")
        kwargs.setdefault("lines", self._lines)
        kwargs.setdefault("force_ascii", False)
        df.to_json(destination, **kwargs)
