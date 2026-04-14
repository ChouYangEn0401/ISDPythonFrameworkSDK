"""Excel 比對測試 — 使用 compare_excel_sheets() (需要 openpyxl)"""
import pytest

pytest.importorskip("openpyxl")

from hyper_framework.unitest_structure.excel_unittest_module import compare_excel_sheets


def _excel_cfg(base_cfg, **sheet_kw):
    """將 cfg() 的輸出轉為 Excel compare_excel_sheets 的 config 格式。"""
    sheet = {"target_sheet": "Sheet1", "bench_sheet": "Sheet1", "checks": ["content"]}
    sheet.update(sheet_kw)
    base_cfg["sheets"] = [sheet]
    return base_cfg


class TestExcel:
    """Excel 檔案比對"""

    def test_pass(self, cfg, run):
        """完全相同的 XLSX → PASS"""
        result = run(compare_excel_sheets, _excel_cfg(cfg("pass", "xlsx")))
        assert result.passed

    def test_fail(self, cfg, run):
        """Row3 age 不同 → FAIL"""
        result = run(compare_excel_sheets, _excel_cfg(cfg("fail", "xlsx")))
        assert not result.passed

    def test_mask_exclude_cell(self, cfg, run):
        """排除 B3 → PASS"""
        result = run(compare_excel_sheets,
            _excel_cfg(cfg("fail", "xlsx"), mask={"exclude_cells": ["B3"]})
        )
        assert result.passed

    def test_mask_exclude_row(self, cfg, run):
        """排除第 3 行 → PASS"""
        result = run(compare_excel_sheets,
            _excel_cfg(cfg("fail", "xlsx"), mask={"exclude_rows": [3]})
        )
        assert result.passed

    def test_mask_include_col(self, cfg, run):
        """只比對 A 欄 (name, 無差異) → PASS"""
        result = run(compare_excel_sheets,
            _excel_cfg(cfg("fail", "xlsx"), mask={"include_cols": ["A"]})
        )
        assert result.passed
