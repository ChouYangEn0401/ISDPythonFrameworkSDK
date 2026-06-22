"""
examples/excel_painter/io_integration.py
========================================
How unified_io and excel_painter connect.

* ``DataIO.write(..., style=...)`` — the IO layer produces a *styled* workbook by
  bridging into excel_painter (presentation), instead of a raw ``to_excel`` dump.
* ``DataIO.write(..., mode="preserve")`` — refresh the data of an existing
  workbook while keeping its formatting, via excel_painter's
  ``SheetFormatSnapshot``.

Run (from repo root, with src importable)::

    $env:PYTHONPATH="src"; .venv\\Scripts\\python.exe examples/excel_painter/io_integration.py

Outputs land in ``examples/excel_painter/output/``.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from isd_py_framework_sdk.unified_io import DataIO
from isd_py_framework_sdk.excel_painter import STATUS_AMBER, STATUS_GREEN, STATUS_RED

OUT = Path(__file__).parent / "output"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    df = pd.DataFrame({
        "ISI_ID": ["000845123", "000845144", "000845161"],
        "Name": ["王昭勝", "Hsieh, Wan-Chen", "De Iorio, A."],
        "回填狀態": ["✅ 已回填", "⚠️ 需人工判定", "❌ 無法分辨二級"],
        "說明": ["化學系正式聘任，AI 查證確認。", "雙掛牌，需人工裁定主聘。", "校長報表查無歷史資料。"],
    })

    # ── 1) IO layer → styled output (one call, formatted by excel_painter) ──────
    styled = OUT / "06_io_styled.xlsx"
    DataIO.write(
        df, styled,
        style=True,                       # route through excel_painter
        widths={"Name": 20, "說明": 50, "回填狀態": 22},
        wrap_cols=["說明"],
        text_cols=["ISI_ID"],
        status_column="回填狀態",
        status_fills={
            "✅ 已回填": STATUS_GREEN,
            "⚠️ 需人工判定": STATUS_AMBER,
            "❌ 無法分辨二級": STATUS_RED,
        },
        auto_width=True,
    )
    print(f"styled write  -> {styled}")

    # ── 2) Refresh values, keep the formatting (preserve via snapshot) ──────────
    df_updated = df.copy()
    df_updated["回填狀態"] = ["✅ 已回填", "✅ 已回填", "❌ 無法分辨二級"]
    DataIO.write(df_updated, styled, mode="preserve")
    print(f"preserve write -> {styled}  (formatting kept, values refreshed)")

    # round-trip read back through the same IO facade
    back = DataIO.read(styled)
    print(f"read back     -> {back.shape[0]} rows, columns={list(back.columns)}")


if __name__ == "__main__":
    main()
