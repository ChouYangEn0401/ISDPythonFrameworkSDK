"""
excel_painter.width
===================
CJK-aware column-width helpers.

Excel column width is measured roughly in "number of default-font characters".
A wide (full-width / CJK) glyph occupies ~2 of those units, so a naive
``len(text)`` under-sizes columns full of Chinese / Japanese / Korean text.

``display_width`` prefers :mod:`wcwidth` when installed (most accurate); when it
is not, it falls back to a built-in East-Asian-width heuristic via
:mod:`unicodedata`, so this module never hard-requires the extra dependency.
"""
from __future__ import annotations

import unicodedata
from typing import Iterable, Optional

try:  # optional, more accurate
    from wcwidth import wcswidth as _wcswidth
except Exception:  # noqa: BLE001 — wcwidth not installed
    _wcswidth = None


def display_width(text: object) -> int:
    """Return the on-screen width of *text* (full-width glyphs count as 2)."""
    if text is None:
        return 0
    s = str(text)

    if _wcswidth is not None:
        w = _wcswidth(s)
        if w >= 0:  # wcswidth returns -1 on control chars
            return w

    width = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ("W", "F"):
            width += 2
        elif unicodedata.combining(ch):
            width += 0
        else:
            width += 1
    return width


def auto_resize(
    ws,
    *,
    padding: int = 2,
    min_width: float = 4.0,
    max_width: Optional[float] = 80.0,
    only_columns: Optional[Iterable[int]] = None,
) -> None:
    """Auto-fit every column of *ws* to its widest (display-width) cell.

    Parameters
    ----------
    padding
        Extra width added on top of the widest cell.
    min_width / max_width
        Clamp range.  ``max_width=None`` disables the upper clamp.
    only_columns
        1-based column indices to resize; ``None`` resizes all.
    """
    from openpyxl.utils import get_column_letter

    wanted = set(only_columns) if only_columns is not None else None

    for column_cells in ws.columns:
        if not column_cells:
            continue
        col_idx = column_cells[0].column
        if wanted is not None and col_idx not in wanted:
            continue

        widest = 0
        for cell in column_cells:
            if cell.value is not None:
                widest = max(widest, display_width(cell.value))

        width = widest + padding
        if width < min_width:
            width = min_width
        if max_width is not None and width > max_width:
            width = max_width

        ws.column_dimensions[get_column_letter(col_idx)].width = width
