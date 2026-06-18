"""
excel_painter.convenience
=========================
One-shot functional helpers over :class:`ExcelPainter` for the common
"write a styled report and be done" case — no fluent chain needed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence, Union

from .painter import ColumnRef, ExcelPainter
from .styles import StatusFills, TableStyle


def save_styled_table(
    df,
    path: Union[str, Path],
    *,
    sheet_name: str = "Sheet1",
    style: Optional[TableStyle] = None,
    widths: Optional[dict] = None,
    wrap_cols: Sequence[ColumnRef] = (),
    left_cols: Sequence[ColumnRef] = (),
    text_cols: Sequence[ColumnRef] = (),
    status_column: Optional[ColumnRef] = None,
    status_fills: Optional[StatusFills] = None,
    auto_width: bool = False,
    index: bool = False,
    safe: bool = False,
    open_after: bool = False,
) -> Path:
    """Write *df* to *path* as a fully styled table in a single call.

    This is the consolidation of the project report builders: header band,
    borders, frozen header, autofilter, per-column wrap/align/text-format, an
    optional status-colour column, and optional CJK auto-width.

    Returns the saved path (which may differ from *path* when ``safe=True`` and
    the original was locked).
    """
    painter = ExcelPainter.from_dataframe(df, sheet_name=sheet_name, index=index)
    if auto_width:
        painter.auto_width()
    painter.style_table(
        style,
        widths=widths,
        wrap_cols=wrap_cols,
        left_cols=left_cols,
        text_cols=text_cols,
    )
    if status_column is not None and status_fills:
        painter.fill_by_value(status_column, status_fills)
    return painter.save(path, safe=safe, open_after=open_after)


def style_existing(
    path: Union[str, Path],
    *,
    sheet: Optional[str] = None,
    style: Optional[TableStyle] = None,
    widths: Optional[dict] = None,
    wrap_cols: Sequence[ColumnRef] = (),
    left_cols: Sequence[ColumnRef] = (),
    text_cols: Sequence[ColumnRef] = (),
    status_column: Optional[ColumnRef] = None,
    status_fills: Optional[StatusFills] = None,
    auto_width: bool = False,
    out_path: Optional[Union[str, Path]] = None,
    safe: bool = False,
) -> Path:
    """Open an existing workbook, apply the styled-table look, and save.

    Saves back over the same file unless ``out_path`` is given.
    """
    painter = ExcelPainter.open(path, sheet=sheet)
    if auto_width:
        painter.auto_width()
    painter.style_table(
        style,
        widths=widths,
        wrap_cols=wrap_cols,
        left_cols=left_cols,
        text_cols=text_cols,
    )
    if status_column is not None and status_fills:
        painter.fill_by_value(status_column, status_fills)
    return painter.save(out_path or path, safe=safe)
