"""INI 比對測試 — 使用 compare_ini_files()"""
from hyper_framework.unitest_structure.ini_unittest_module import compare_ini_files


class TestINI:
    """INI 檔案比對"""

    def test_pass(self, cfg, run):
        """完全相同的 INI → PASS"""
        result = run(compare_ini_files, cfg("pass", "ini"))
        assert result.passed

    def test_fail(self, cfg, run):
        """[server] port 不同 → FAIL"""
        result = run(compare_ini_files, cfg("fail", "ini"))
        assert not result.passed

    def test_mask_exclude_section(self, cfg, run):
        """排除 server section → PASS"""
        result = run(compare_ini_files,
            cfg("fail", "ini", mask={"exclude_sections": ["server"]})
        )
        assert result.passed

    def test_mask_exclude_key(self, cfg, run):
        """排除 server.port → PASS"""
        result = run(compare_ini_files,
            cfg("fail", "ini", mask={"exclude_keys": {"server": ["port"]}})
        )
        assert result.passed

    def test_mask_include_section(self, cfg, run):
        """只比對 database section → PASS"""
        result = run(compare_ini_files,
            cfg("fail", "ini", mask={"include_sections": ["database"]})
        )
        assert result.passed
