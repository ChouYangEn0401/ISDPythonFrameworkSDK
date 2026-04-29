"""
unified_io.adapters.csv_adapter
================================
CSV read / write adapter backed by pandas.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ._interface import IIOAdapter


class CsvIOAdapter(IIOAdapter):
    """Read / write CSV files via ``pandas.read_csv`` / ``DataFrame.to_csv``."""

    def read(self, source: str | Path, **kwargs) -> pd.DataFrame:
        """
        Parameters
        ----------
        source
            Path to the CSV file.
        **kwargs
            Forwarded to :func:`pandas.read_csv` (e.g. ``encoding``,
            ``sep``, ``dtype``).
        """
        return pd.read_csv(source, **kwargs)

    def write(self, df: pd.DataFrame, destination: str | Path, **kwargs) -> None:
        """
        Parameters
        ----------
        destination
            Output CSV path.
        **kwargs
            Forwarded to :meth:`pandas.DataFrame.to_csv`.
            ``index`` defaults to ``False``.
        """
        kwargs.setdefault("index", False)
        df.to_csv(destination, **kwargs)
