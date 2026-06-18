"""
unified_io.data_io
==================
``DataIO`` — single-entry-point façade for all IO operations.

Format is inferred from the file extension when ``format="auto"``
(the default).  You can also instantiate adapters directly for more
control over per-adapter options.

Quick start
-----------
::
    from isd_py_framework_sdk.unified_io import DataIO

    # ── Read ──────────────────────────────────────────────────────────
    df = DataIO.read("data.csv")
    df = DataIO.read("report.xlsx", sheet_name="Results")
    df = DataIO.read("SELECT * FROM users WHERE active=1", engine=engine)

    # ── Write ─────────────────────────────────────────────────────────
    DataIO.write(df, "output.csv")
    DataIO.write(df, "output.xlsx", sheet_name="Summary")

    # Write back to an existing Excel without losing its formatting:
    DataIO.write(df, "report.xlsx", sheet_name="Data", mode="preserve")

    # ── Explicit adapters (more constructor options) ───────────────────
    from isd_py_framework_sdk.unified_io import ExcelIOAdapter
    adapter = ExcelIOAdapter(default_write_mode="preserve")
    adapter.write(df, "report.xlsx", sheet_name="Data")
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from .adapters import CsvIOAdapter, ExcelIOAdapter, JsonIOAdapter, SqlIOAdapter
from .adapters._interface import IIOAdapter

# Extension → adapter class
_EXT_MAP: dict[str, type[IIOAdapter]] = {
    ".csv": CsvIOAdapter,
    ".xlsx": ExcelIOAdapter,
    ".xls": ExcelIOAdapter,
    ".json": JsonIOAdapter,
    ".jsonl": JsonIOAdapter,
}


def _resolve_adapter(format: str, source: str | Path | Any) -> IIOAdapter:
    """Pick and instantiate the right adapter for *source*."""
    if format != "auto":
        fmt = format.lower().lstrip(".")
        for ext, cls in _EXT_MAP.items():
            if ext.lstrip(".") == fmt:
                # JsonIOAdapter for JSONL needs lines=True
                if cls is JsonIOAdapter and fmt == "jsonl":
                    return JsonIOAdapter(lines=True)
                return cls()
        raise ValueError(
            f"Unknown format {format!r}.  "
            f"Supported: {', '.join(e.lstrip('.') for e in _EXT_MAP)}, sql"
        )

    # Auto-detect from extension
    try:
        suffix = Path(str(source)).suffix.lower()
    except Exception:
        suffix = ""

    if suffix == ".jsonl":
        return JsonIOAdapter(lines=True)

    cls = _EXT_MAP.get(suffix)
    if cls is None:
        raise ValueError(
            f"Cannot auto-detect IO format from source {source!r}.  "
            "Pass format='csv'/'xlsx'/'json'/'jsonl'/'sql' explicitly."
        )
    return cls()


class DataIO:
    """
    Single-entry-point façade for reading and writing tabular data.

    All methods are static / class-level — no instantiation needed.
    """

    # ── Generic read / write ──────────────────────────────────────────────

    @staticmethod
    def read(
        source: str | Path | Any,
        *,
        format: str = "auto",
        **kwargs,
    ) -> pd.DataFrame:
        """
        Read data from *source* and return a :class:`pandas.DataFrame`.

        Parameters
        ----------
        source
            File path, SQL query string, or any adapter-specific identifier.
        format
            ``"auto"`` (infer from extension), ``"csv"``, ``"xlsx"``,
            ``"json"``, ``"jsonl"``, or ``"sql"``.
        **kwargs
            Forwarded to the adapter's ``read()`` method.
        """
        if format == "sql" or (format == "auto" and "engine" in kwargs):
            return SqlIOAdapter().read(source, **kwargs)
        adapter = _resolve_adapter(format, source)
        return adapter.read(source, **kwargs)

    @staticmethod
    def write(
        df: pd.DataFrame,
        destination: str | Path,
        *,
        format: str = "auto",
        **kwargs,
    ) -> None:
        """
        Write *df* to *destination*.

        Parameters
        ----------
        destination
            Output file path or table name (SQL).
        format
            ``"auto"`` (infer from extension), ``"csv"``, ``"xlsx"``,
            ``"json"``, ``"jsonl"``, or ``"sql"``.
        **kwargs
            Forwarded to the adapter's ``write()`` method.
            For Excel, ``mode="preserve"`` or ``mode="inplace"`` activates
            format-safe write modes.
        """
        if format == "sql" or (format == "auto" and "engine" in kwargs):
            SqlIOAdapter().write(df, destination, **kwargs)
            return
        adapter = _resolve_adapter(format, destination)
        adapter.write(df, destination, **kwargs)

    # ── Typed convenience methods ─────────────────────────────────────────

    @staticmethod
    def read_csv(source: str | Path, **kwargs) -> pd.DataFrame:
        return CsvIOAdapter().read(source, **kwargs)

    @staticmethod
    def read_excel(
        source: str | Path,
        sheet_name: str | int = 0,
        **kwargs,
    ) -> pd.DataFrame:
        return ExcelIOAdapter().read(source, sheet_name=sheet_name, **kwargs)

    @staticmethod
    def read_json(source: str | Path, **kwargs) -> pd.DataFrame:
        return JsonIOAdapter().read(source, **kwargs)

    @staticmethod
    def read_jsonl(source: str | Path, **kwargs) -> pd.DataFrame:
        return JsonIOAdapter(lines=True).read(source, **kwargs)

    @staticmethod
    def read_sql(query: str, engine: Any, **kwargs) -> pd.DataFrame:
        return SqlIOAdapter(engine).read(query, **kwargs)

    @staticmethod
    def write_csv(df: pd.DataFrame, destination: str | Path, **kwargs) -> None:
        CsvIOAdapter().write(df, destination, **kwargs)

    @staticmethod
    def write_excel(
        df: pd.DataFrame,
        destination: str | Path,
        sheet_name: str = "Sheet1",
        mode: str = "fresh",
        **kwargs,
    ) -> None:
        ExcelIOAdapter().write(df, destination, sheet_name=sheet_name, mode=mode, **kwargs)

    @staticmethod
    def write_json(df: pd.DataFrame, destination: str | Path, **kwargs) -> None:
        JsonIOAdapter().write(df, destination, **kwargs)

    @staticmethod
    def write_jsonl(df: pd.DataFrame, destination: str | Path, **kwargs) -> None:
        JsonIOAdapter(lines=True).write(df, destination, **kwargs)

    @staticmethod
    def write_sql(
        df: pd.DataFrame, table: str, engine: Any, **kwargs
    ) -> None:
        SqlIOAdapter(engine).write(df, table, **kwargs)
