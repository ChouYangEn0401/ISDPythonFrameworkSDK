"""
excel_painter._format_snapshot
==============================
Capture a worksheet's visual format and restore it after the cell *values*
have been rewritten.

This is the building block behind ``unified_io``'s Excel ``mode="preserve"``
write: snapshot the sheet → clear/rewrite the data → restore the snapshot, so
a hand-crafted (or previously painted) layout survives a data refresh.

What is preserved
-----------------
* per-cell ``font`` / ``fill`` / ``border`` / ``alignment`` / ``number_format``
  (keyed by ``(row, column)`` so it survives a delete-rows + rewrite)
* column widths / hidden flag
* row heights / hidden flag
* ``freeze_panes``
* merged-cell ranges
* ``auto_filter`` range

What is NOT preserved
---------------------
* ``CellRichText`` — the rewrite replaces values with plain text; only the
  cell *style* is restored, not inline rich-text runs.
* charts / images / data validations / conditional-formatting rules.

Usage
-----
::

    from isd_py_framework_sdk.excel_painter import SheetFormatSnapshot

    snap = SheetFormatSnapshot.capture(ws)
    # ... rewrite ws values ...
    snap.restore(ws)
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SheetFormatSnapshot:
    """An immutable-ish capture of a worksheet's formatting.

    Create with :meth:`capture`; reapply with :meth:`restore`.
    """

    # (row, col) -> {"font", "fill", "border", "alignment", "number_format"}
    cell_styles: dict[tuple[int, int], dict[str, Any]] = field(default_factory=dict)
    # column letter -> {"width", "hidden"}
    col_dims: dict[str, dict[str, Any]] = field(default_factory=dict)
    # row index -> {"height", "hidden"}
    row_dims: dict[int, dict[str, Any]] = field(default_factory=dict)
    freeze_panes: str | None = None
    merged_ranges: list[str] = field(default_factory=list)
    auto_filter_ref: str | None = None

    # ── Capture ────────────────────────────────────────────────────────────

    @classmethod
    def capture(cls, ws) -> "SheetFormatSnapshot":
        """Snapshot *ws*'s current formatting into a new instance."""
        snap = cls()

        for row in ws.iter_rows():
            for cell in row:
                if cell.value is None and not cell.has_style:
                    continue
                snap.cell_styles[(cell.row, cell.column)] = {
                    "font": copy.copy(cell.font),
                    "fill": copy.copy(cell.fill),
                    "border": copy.copy(cell.border),
                    "alignment": copy.copy(cell.alignment),
                    "number_format": cell.number_format,
                }

        for letter, dim in ws.column_dimensions.items():
            entry: dict[str, Any] = {}
            if dim.width is not None:
                entry["width"] = dim.width
            if dim.hidden:
                entry["hidden"] = True
            if entry:
                snap.col_dims[letter] = entry

        for idx, dim in ws.row_dimensions.items():
            entry = {}
            if dim.height is not None:
                entry["height"] = dim.height
            if dim.hidden:
                entry["hidden"] = True
            if entry:
                snap.row_dims[idx] = entry

        snap.freeze_panes = ws.freeze_panes
        snap.merged_ranges = [str(r) for r in ws.merged_cells.ranges]
        try:
            snap.auto_filter_ref = ws.auto_filter.ref
        except Exception:  # noqa: BLE001 — auto_filter API varies by version
            snap.auto_filter_ref = None
        return snap

    # ── Restore ────────────────────────────────────────────────────────────

    def restore(self, ws) -> None:
        """Reapply this snapshot onto *ws* (in place)."""
        for (row, col), style in self.cell_styles.items():
            cell = ws.cell(row=row, column=col)
            cell.font = copy.copy(style["font"])
            cell.fill = copy.copy(style["fill"])
            cell.border = copy.copy(style["border"])
            cell.alignment = copy.copy(style["alignment"])
            cell.number_format = style["number_format"]

        for letter, entry in self.col_dims.items():
            dim = ws.column_dimensions[letter]
            if "width" in entry:
                dim.width = entry["width"]
            if entry.get("hidden"):
                dim.hidden = True

        for idx, entry in self.row_dims.items():
            dim = ws.row_dimensions[idx]
            if "height" in entry:
                dim.height = entry["height"]
            if entry.get("hidden"):
                dim.hidden = True

        if self.freeze_panes:
            ws.freeze_panes = self.freeze_panes

        for rng in self.merged_ranges:
            try:
                ws.merge_cells(rng)
            except Exception:  # noqa: BLE001 — already-merged / invalid range
                pass

        if self.auto_filter_ref:
            ws.auto_filter.ref = self.auto_filter_ref
