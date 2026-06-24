"""
isd_py_framework_sdk.unified_io
==================================
Unified IO module — read / write tabular data from any supported source
through a single adapter-pattern interface.

Public API
----------
Façade (recommended for most use-cases)::

    from isd_py_framework_sdk.unified_io import DataIO

    df = DataIO.read("data.csv")
    df = DataIO.read("report.xlsx", sheet_name="Sales")
    df = DataIO.read_sql("SELECT * FROM orders", engine=engine)

    DataIO.write(df, "output.xlsx", sheet_name="Results")
    DataIO.write(df, "report.xlsx", mode="preserve")  # keep existing format

Explicit adapters (for constructor-level options)::

    from isd_py_framework_sdk.unified_io import (
        CsvIOAdapter,
        ExcelIOAdapter,
        JsonIOAdapter,
        SqlIOAdapter,
    )

    adapter = ExcelIOAdapter(default_write_mode="inplace")
    df = adapter.read("report.xlsx", sheet_name="Data")
    adapter.write(df_updated, "report.xlsx", sheet_name="Data")

Interfaces (for your own adapters)::

    from isd_py_framework_sdk.unified_io import IReader, IWriter, IIOAdapter

DataFrame transform helpers (multi-column sort, select/reorder/rename, dict→df)::

    from isd_py_framework_sdk.unified_io import (
        multiple_sort_dataframe,
        sort_dataframe,
        pick_and_reorder_then_rename_columns,
        dict_to_df,
    )
"""

from .adapters._interface import IIOAdapter, IReader, IWriter
from .adapters import CsvIOAdapter, ExcelIOAdapter, JsonIOAdapter, SqlIOAdapter
from .data_io import DataIO
from .df_tools import (
    multiple_sort_dataframe,
    sort_dataframe,
    pick_and_reorder_then_rename_columns,
    dict_to_df,
)

__all__ = [
    # Interfaces
    "IReader",
    "IWriter",
    "IIOAdapter",
    # Adapters
    "CsvIOAdapter",
    "ExcelIOAdapter",
    "JsonIOAdapter",
    "SqlIOAdapter",
    # Façade
    "DataIO",
    # DataFrame transform helpers
    "multiple_sort_dataframe",
    "sort_dataframe",
    "pick_and_reorder_then_rename_columns",
    "dict_to_df",
]
