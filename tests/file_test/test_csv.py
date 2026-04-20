"""CSV 比對測試 — 使用 compare_csv_files()"""
from hyper_framework.file_compare.csv_unittest_module import compare_csv_files


class TestCSV:
    """CSV 檔案比對"""

    def test_pass(self, cfg, run):
        """完全相同的 CSV → PASS"""
        result = run(compare_csv_files,
            cfg("pass", "csv", checks=["content", "row_count", "column_count", "header"])
        )
        assert result.passed

    def test_fail_content(self, cfg, run):
        """Row3 age / Row4 city 有差異 → FAIL"""
        result = run(compare_csv_files, cfg("fail", "csv", checks=["content"]))
        assert not result.passed

    def test_fail_header_still_ok(self, cfg, run):
        """即使內容不同，標題行一樣 → header check PASS"""
        result = run(compare_csv_files, cfg("fail", "csv", checks=["header"]))
        assert result.passed

    def test_mask_exclude_rows(self, cfg, run):
        """排除差異行 3, 4 → PASS"""
        result = run(compare_csv_files,
            cfg("fail", "csv", checks=["content"], mask={"exclude_rows": [3, 4]})
        )
        assert result.passed

    def test_mask_include_rows(self, cfg, run):
        """只比對無差異行 1, 2 → PASS"""
        result = run(compare_csv_files,
            cfg("fail", "csv", checks=["content"], mask={"include_rows": [1, 2]})
        )
        assert result.passed

    def test_mask_exclude_cols(self, cfg, run):
        """排除差異欄 1(age), 2(city) → PASS"""
        result = run(compare_csv_files,
            cfg("fail", "csv", checks=["content"], mask={"exclude_cols": [1, 2]})
        )
        assert result.passed
