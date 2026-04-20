"""TXT 比對測試 — 使用 compare_txt_files()"""
from hyper_framework.file_compare import compare_txt_files


class TestTXT:
    """純文字檔案比對"""

    def test_pass(self, cfg, run):
        """完全相同的 TXT → PASS"""
        result = run(compare_txt_files, cfg("pass", "txt", checks=["content", "line_count"]))
        assert result.passed

    def test_fail(self, cfg, run):
        """第 2 行不同 → FAIL"""
        result = run(compare_txt_files, cfg("fail", "txt", checks=["content"]))
        assert not result.passed

    def test_fail_line_count_ok(self, cfg, run):
        """行數相同 → line_count check PASS"""
        result = run(compare_txt_files, cfg("fail", "txt", checks=["line_count"]))
        assert result.passed

    def test_mask_exclude_row(self, cfg, run):
        """排除第 2 行 → PASS"""
        result = run(compare_txt_files,
            cfg("fail", "txt", checks=["content"], mask={"exclude_rows": [2]})
        )
        assert result.passed
