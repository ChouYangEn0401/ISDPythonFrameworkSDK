"""JSON 比對測試 — 使用 compare_json_files()"""
from hyper_framework.unitest_structure.json_unittest_module import compare_json_files


class TestJSON:
    """JSON 檔案比對"""

    def test_pass(self, cfg, run):
        """完全相同的 JSON → PASS"""
        result = run(compare_json_files, cfg("pass", "json"))
        assert result.passed

    def test_fail(self, cfg, run):
        """$.users[0].age 不同 → FAIL"""
        result = run(compare_json_files, cfg("fail", "json"))
        assert not result.passed

    def test_mask_exclude_path(self, cfg, run):
        """排除 $.users[0].age → PASS"""
        result = run(compare_json_files,
            cfg("fail", "json", mask={"exclude_paths": ["$.users[0].age"]})
        )
        assert result.passed

    def test_mask_include_path(self, cfg, run):
        """只比對 $.count（無差異）→ PASS"""
        result = run(compare_json_files,
            cfg("fail", "json", mask={"include_paths": ["$.count"]})
        )
        assert result.passed
