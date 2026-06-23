"""
isd_py_framework_sdk.excel_painter
==================================
Powerful, fluent Excel styling — header bands, conditional/status fills,
CJK-aware auto-width, LCS/Jaccard rich-text highlighting, and format
snapshot/restore.

Requires openpyxl (``pip install isd-py-framework-sdk[excel_painter]``);
``wcwidth`` is optional (a built-in CJK width fallback is used when absent).

Quick start
-----------
Fluent (load once → chain → save once)::

    from isd_py_framework_sdk.excel_painter import ExcelPainter, STATUS_GREEN, STATUS_RED

    (
        ExcelPainter.from_dataframe(df, sheet_name="Results")
        .style_table(widths={"Name": 22, "說明": 80}, wrap_cols=["說明"], text_cols=["ISI_ID"])
        .fill_by_value("狀態", {"✅完成": STATUS_GREEN, "❌失敗": STATUS_RED})
        .auto_width(only_columns=[1])
        .save("out.xlsx", safe=True)
    )

One-shot::

    from isd_py_framework_sdk.excel_painter import save_styled_table, STATUS_GREEN

    save_styled_table(
        df, "out.xlsx",
        widths={"Name": 22}, wrap_cols=["說明"], text_cols=["ISI_ID"],
        status_column="狀態", status_fills={"✅完成": STATUS_GREEN},
    )
"""
from ._format_snapshot import SheetFormatSnapshot
from .painter import ExcelPainter
from .convenience import save_styled_table, style_existing
from .templates import (
    auto_status_fills,
    status_report,
    summary_statistics_report,
    multi_sheet_report,
    diff_highlight_report,
)
from .styles import (
    TableStyle,
    StatusFills,
    blue_table,
    minimal_table,
    fill,
    font,
    box,
    side,
    align,
    STATUS_GREEN,
    STATUS_AMBER,
    STATUS_RED,
    STATUS_GREY,
)
from .width import display_width, auto_resize
from .highlight import (
    char_lcs,
    word_lcs,
    common_words,
    lcs_rich_text,
    common_words_rich_text,
    words_rich_text,
)

__all__ = [
    # Core
    "ExcelPainter",
    "SheetFormatSnapshot",
    # Convenience
    "save_styled_table",
    "style_existing",
    # Templates (functionalised common reports)
    "auto_status_fills",
    "status_report",
    "summary_statistics_report",
    "multi_sheet_report",
    "diff_highlight_report",
    # Styles
    "TableStyle",
    "StatusFills",
    "blue_table",
    "minimal_table",
    "fill",
    "font",
    "box",
    "side",
    "align",
    "STATUS_GREEN",
    "STATUS_AMBER",
    "STATUS_RED",
    "STATUS_GREY",
    # Width
    "display_width",
    "auto_resize",
    # Highlight
    "char_lcs",
    "word_lcs",
    "common_words",
    "lcs_rich_text",
    "common_words_rich_text",
    "words_rich_text",
]
