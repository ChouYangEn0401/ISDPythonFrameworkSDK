"""YAML 比對測試 — 使用 compare_yaml_files() (需要 pyyaml)"""
import pytest

pytest.importorskip("yaml")

from hyper_framework.file_compare import compare_yaml_files


class TestYAML:
    """YAML 檔案比對"""

    def test_pass(self, cfg, run):
        """完全相同的 YAML → PASS"""
        result = run(compare_yaml_files, cfg("pass", "yaml"))
        assert result.passed

    def test_fail(self, cfg, run):
        """$.server.port 不同 → FAIL"""
        result = run(compare_yaml_files, cfg("fail", "yaml"))
        assert not result.passed

    def test_mask_exclude_path(self, cfg, run):
        """排除 $.server.port → PASS"""
        result = run(compare_yaml_files,
            cfg("fail", "yaml", mask={"exclude_paths": ["$.server.port"]})
        )
        assert result.passed

    def test_mask_include_path(self, cfg, run):
        """只比對 $.database → PASS"""
        result = run(compare_yaml_files,
            cfg("fail", "yaml", mask={"include_paths": ["$.database"]})
        )
        assert result.passed
