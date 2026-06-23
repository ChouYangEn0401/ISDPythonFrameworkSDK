"""
examples/excel_painter/generate_templates.py
============================================
Generate a gallery of professional Excel outputs using the excel_painter API.

Run (from repo root, with src importable)::

    $env:PYTHONPATH="src"; .venv\\Scripts\\python.exe examples/excel_painter/generate_templates.py

Outputs land in ``examples/excel_painter/output/``.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from isd_py_framework_sdk.excel_painter import (
    ExcelPainter,
    TableStyle,
    STATUS_GREEN,
    STATUS_AMBER,
    STATUS_RED,
    STATUS_GREY,
    status_report,
    summary_statistics_report,
    multi_sheet_report,
    diff_highlight_report,
)

OUT = Path(__file__).parent / "output"
OUT.mkdir(parents=True, exist_ok=True)


# ── 1) Status report (operations result + summary sheet) ─────────────────────

def gen_status_report() -> Path:
    df = pd.DataFrame({
        "ISI_ID": ["000845123", "000845127", "000845130", "000845144", "000845150", "000845161"],
        "Name": ["Chen, Shih-Yu", "王昭勝", "Lee, Min-Hung", "Hsieh, Wan-Chen", "高嘉宏", "De Iorio, A."],
        "二級單位": ["化學系", "化學系", "元件材料學程", "—", "附設醫院內科部", "—"],
        "回填狀態": ["✅ 已回填", "✅ 已回填", "⚠️ 需人工判定（多個候選）",
                     "❌ 無法分辨二級", "✅ 已回填", "❌ 作者絲毫無歷史資料"],
        "判定方式": ["演算法比中＋AI確認", "演算法比中＋AI確認", "AI歷史回填", "—", "演算法比中＋AI確認", "—"],
        "AI說明": [
            "地址含 Dept Chem，化學系為正式聘任系所，網路查證確認。",
            "王昭勝教授化學系主頁確認；地址雙掛牌但化學系為正式聘任。",
            "地址同時對應兩個學位學程，需人工裁定何者為主聘。",
            "地址僅 Acad Sinica Inst Biomed Sci，無法確定具體 NTU 系所。",
            "高嘉宏教授為 NTUH 消化科（內科部），查詢確認對應附設醫院內科部。",
            "義大利那不勒斯大學訪問學者，校長報表查無歷史資料。",
        ],
    })
    p = OUT / "01_status_report.xlsx"
    return status_report(
        df, p,
        status_column="回填狀態",
        title="NA 清單回填結果（2026 校長報表）",
        widths={"ISI_ID": 14, "Name": 22, "二級單位": 18, "回填狀態": 24, "判定方式": 22, "AI說明": 70},
        wrap_cols=["AI說明"], left_cols=["AI說明", "二級單位"], text_cols=["ISI_ID"],
    )


# ── 2) Numeric statistics with heat-map + totals row ─────────────────────────

def gen_statistics() -> Path:
    df = pd.DataFrame({
        "系所": ["化學系", "物理系", "醫學系", "電機系", "資工系", "地理系"],
        "2021": [142, 98, 305, 221, 176, 33],
        "2022": [155, 110, 322, 240, 205, 41],
        "2023": [168, 121, 318, 268, 233, 38],
        "2024": [171, 130, 341, 290, 261, 45],
    })
    df["總數"] = df[["2021", "2022", "2023", "2024"]].sum(axis=1)
    p = OUT / "02_statistics_heatmap.xlsx"
    return summary_statistics_report(
        df, p,
        numeric_cols=["2021", "2022", "2023", "2024", "總數"],
        label_col="系所",
        title="各系所歷年論文發表統計",
        widths={"系所": 16},
    )


# ── 3) Multi-sheet workbook with overview index ──────────────────────────────

def gen_multi_sheet() -> Path:
    resolved = pd.DataFrame({
        "ISI_ID": ["000845123", "000845127", "000845130"],
        "Name": ["Chen, Shih-Yu", "王昭勝", "Lee, Min-Hung"],
        "OrgSerial": ["TWU000001120100", "TWU000001090300", "TWU000001150700"],
        "Score": [0.962, 0.915, 0.871],
    })
    unresolved = pd.DataFrame({
        "ISI_ID": ["000845144", "000845161"],
        "Name": ["Hsieh, Wan-Chen", "De Iorio, A."],
        "Address": ["Acad Sinica, Inst Biomed Sci, Taipei", "Univ Naples Federico II, Naples, Italy"],
    })
    summary = pd.DataFrame({
        "指標": ["目標作者", "已解決", "待人工", "未解決"],
        "數值": [73, 58, 9, 6],
    })
    p = OUT / "03_multi_sheet.xlsx"
    return multi_sheet_report(
        {"已解決": resolved, "未解決": unresolved, "統計": summary}, p,
        per_sheet={
            "已解決": {"widths": {"OrgSerial": 22, "Name": 20}, "text_cols": ["ISI_ID"]},
            "未解決": {"widths": {"Address": 50, "Name": 20}, "wrap_cols": ["Address"], "text_cols": ["ISI_ID"]},
        },
    )


# ── 4) Word-diff highlight report ────────────────────────────────────────────

def gen_diff_highlight() -> Path:
    df = pd.DataFrame({
        "原始地址": [
            "Dept Chem National Taiwan Univ Taipei",
            "Inst Astron Astrophys National Taiwan Univ",
            "Coll Med Dept Internal Med NTUH Taipei",
        ],
        "比中的單位地址": [
            "Department Chemistry Taiwan University",
            "Institute Astronomy Astrophysics Taiwan",
            "College Medicine Internal Medicine Hospital",
        ],
    })
    p = OUT / "04_diff_highlight.xlsx"
    return diff_highlight_report(
        df, p,
        column_pairs=[("原始地址", "比中的單位地址")],
        method="common_words",
        title="地址比對：共同詞高亮",
        widths={"原始地址": 46, "比中的單位地址": 46},
        wrap_cols=["原始地址", "比中的單位地址"],
    )


# ── 5) Hand-built fluent example (shows the raw chaining API) ─────────────────

def _fluent_custom_explicit(df, p):
    painter = ExcelPainter.new("儀表板")
    painter.title_banner("專案進度儀表板", n_cols=len(df.columns))
    painter.write_dataframe(df, start_row=2)
    painter.auto_width()
    painter.style_table(TableStyle(banded=True), header_row=2, widths={"專案": 18, "完成率": 12, "狀態": 14})
    painter.color_scale("完成率", low_color="F8696B", high_color="63BE7B", header_row=2, min_value=0, max_value=100)
    painter.fill_by_value("狀態", {"✅完成": STATUS_GREEN, "⚠️進行中": STATUS_AMBER}, header_row=2)
    return painter.save(p)


if __name__ == "__main__":
    made = [
        gen_status_report(),
        gen_statistics(),
        gen_multi_sheet(),
        gen_diff_highlight(),
        _fluent_custom_explicit(
            pd.DataFrame({
                "專案": ["Org1 清理", "Org2 回填", "校長報表", "ESI 報表", "AI 驗證"],
                "完成率": [100, 79, 92, 64, 88],
                "狀態": ["✅完成", "⚠️進行中", "✅完成", "⚠️進行中", "✅完成"],
            }),
            OUT / "05_fluent_custom.xlsx",
        ),
    ]
    print("Generated:")
    for m in made:
        print(f"  - {m}")
