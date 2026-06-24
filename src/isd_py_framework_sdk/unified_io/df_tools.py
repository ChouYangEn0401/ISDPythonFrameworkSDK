"""
DataFrame transform helpers.

Small, dependency-light pandas utilities for the common shaping steps that show
up around tabular IO: multi-column sorting (with custom category order), column
selection / reordering / renaming in one call, and smart ``dict`` → DataFrame
conversion.

Ported (unchanged in behaviour) from the retired ``BetterPyExcelHelper`` — these
were the only pieces of that legacy module not superseded by ``excel_painter``.
They live here because they operate purely on :class:`pandas.DataFrame`, which is
already ``unified_io``'s core dependency.
"""
from __future__ import annotations

from typing import Any, List, Literal

import pandas as pd

__all__ = [
    "multiple_sort_dataframe",
    "sort_dataframe",
    "pick_and_reorder_then_rename_columns",
    "dict_to_df",
]


def multiple_sort_dataframe(
    df: pd.DataFrame,
    sort_by_cols: List[str],
    sorting_orders: List[Literal["a->z", "z->a", "custom"]] | None = None,
    custom_orders: List[List[Any]] | None = None,
) -> pd.DataFrame:
    """
    Sort a DataFrame by several columns, each with its own order.

    Args:
        df: the DataFrame to sort.
        sort_by_cols: column names to sort by (in priority order).
        sorting_orders: per-column order — ``"a->z"`` (ascending, default),
            ``"z->a"`` (descending), or ``"custom"`` (use ``custom_orders``).
        custom_orders: for any ``"custom"`` column, the explicit category order;
            required when that column's order is ``"custom"``.

    Returns:
        The sorted DataFrame (the original is returned unchanged on a mismatch).
    """
    if len(sort_by_cols) != len(sorting_orders):
        print("錯誤：排序欄位數量與排序順序不匹配。返回原始 DataFrame。")
        return df

    for col in sort_by_cols:
        if col not in df.columns:
            print(f"警告：DataFrame 中沒有 '{col}' 欄位，無法進行排序。返回原始 DataFrame。")
            return df

    ascending = []
    for i, order in enumerate(sorting_orders):
        if order == "a->z":
            ascending.append(True)
        elif order == "z->a":
            ascending.append(False)
        elif order == "custom":
            if custom_orders is None or custom_orders[i] is None:
                print("錯誤：當 sorting_order 為 'custom' 時，必須提供 custom_order。返回原始 DataFrame。")
                return df
            else:
                unique_values = df[sort_by_cols[i]].unique().tolist()
                if set(unique_values) - set(custom_orders[i]):
                    print(f"警告：custom_order 並未包含排序欄位 '{sort_by_cols[i]}' 的所有唯一值，排序結果可能不完整。")
                categorical_series = pd.Categorical(df[sort_by_cols[i]], categories=custom_orders[i], ordered=True)
                df[sort_by_cols[i]] = categorical_series
                ascending.append(True)
        else:
            print(f"錯誤：未知的 sorting_order: '{order}'。請使用 'a->z', 'z->a' 或 'custom'。返回原始 DataFrame。")
            return df

    return df.sort_values(by=sort_by_cols, ascending=ascending)


def sort_dataframe(
    df: pd.DataFrame,
    sort_by_col: str,
    sorting_order: Literal["a->z", "z->a", "custom"] = "a->z",
    custom_order: List[str] | None = None,
) -> pd.DataFrame:
    """Single-column convenience wrapper over :func:`multiple_sort_dataframe`."""
    return multiple_sort_dataframe(df, [sort_by_col], [sorting_order], [custom_order])


def pick_and_reorder_then_rename_columns(
    df: pd.DataFrame,
    select_columns: list,
    rename_columns: dict | None = None,
) -> pd.DataFrame:
    """
    Select, reorder, then rename columns in one step.

    Args:
        df: the DataFrame to process.
        select_columns: columns to keep — the list order becomes the final order.
        rename_columns: optional ``{old: new}`` rename map applied after selection.

    Returns:
        A new DataFrame with the chosen columns (missing names are ignored).
    """
    processed_df = df.copy()

    existing_select_columns = [col for col in select_columns if col in processed_df.columns]
    processed_df = processed_df[existing_select_columns]

    if rename_columns:
        columns_to_rename = {old: new for old, new in rename_columns.items() if old in processed_df.columns}
        processed_df = processed_df.rename(columns=columns_to_rename)

    return processed_df


def dict_to_df(data: dict) -> pd.DataFrame:
    """
    Convert a ``dict`` to a DataFrame, auto-detecting its shape.

    Supports three shapes:

    1. ``{"col": [v1, v2], ...}``           → columns of values (normal).
    2. ``{"row": {"col": v, ...}, ...}``    → ``from_dict(orient="index")``.
    3. ``{"col": v, ...}`` (scalar values)  → a single row.
    """
    if not isinstance(data, dict):
        raise ValueError("輸入必須是 dict")

    # shape 2: every value is a dict → rows keyed by the outer keys
    if all(isinstance(v, dict) for v in data.values()):
        return pd.DataFrame.from_dict(data, orient="index")

    # shape 3: every value is a scalar → one row
    elif all(not isinstance(v, (list, dict)) for v in data.values()):
        return pd.DataFrame([data])

    # shape 1: normal column → list mapping
    else:
        return pd.DataFrame(data)
