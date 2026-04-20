"""JSONL 比對測試 — 使用 compare_jsonl_files()"""
from hyper_framework.file_compare import compare_jsonl_files


class TestJSONL:
    """JSONL (JSON Lines) 檔案比對"""

    def test_pass(self, cfg, run):
        """完全相同的 JSONL → PASS"""
        result = run(compare_jsonl_files, cfg("pass", "jsonl"))
        assert result.passed

    def test_fail(self, cfg, run):
        """第 2 行 age 不同 → FAIL"""
        result = run(compare_jsonl_files, cfg("fail", "jsonl"))
        assert not result.passed

    def test_mask_exclude_row(self, cfg, run):
        """排除第 2 行 → PASS"""
        result = run(compare_jsonl_files,
            cfg("fail", "jsonl", mask={"exclude_rows": [2]})
        )
        assert result.passed

    def test_mask_include_rows(self, cfg, run):
        """只比對第 1, 3 行 → PASS"""
        result = run(compare_jsonl_files,
            cfg("fail", "jsonl", mask={"include_rows": [1, 3]})
        )
        assert result.passed
