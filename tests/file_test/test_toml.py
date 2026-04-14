"""TOML 比對測試 — 使用 compare_toml_files()"""
from hyper_framework.unitest_structure.toml_unittest_module import compare_toml_files


class TestTOML:
    """TOML 檔案比對"""

    def test_pass(self, cfg, run):
        """完全相同的 TOML → PASS"""
        result = run(compare_toml_files, cfg("pass", "toml"))
        assert result.passed

    def test_fail(self, cfg, run):
        """$.server.port 不同 → FAIL"""
        result = run(compare_toml_files, cfg("fail", "toml"))
        assert not result.passed

    def test_mask_exclude_path(self, cfg, run):
        """排除 $.server.port → PASS"""
        result = run(compare_toml_files,
            cfg("fail", "toml", mask={"exclude_paths": ["$.server.port"]})
        )
        assert result.passed

    def test_mask_include_path(self, cfg, run):
        """只比對 $.database → PASS"""
        result = run(compare_toml_files,
            cfg("fail", "toml", mask={"include_paths": ["$.database"]})
        )
        assert result.passed
