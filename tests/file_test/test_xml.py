"""XML 比對測試 — 使用 compare_xml_files()"""
from hyper_framework.unitest_structure.xml_unittest_module import compare_xml_files


class TestXML:
    """XML 檔案比對"""

    def test_pass(self, cfg, run):
        """完全相同的 XML → PASS"""
        result = run(compare_xml_files,
            cfg("pass", "xml", checks=["tag", "text", "attrib", "children_count"])
        )
        assert result.passed

    def test_fail(self, cfg, run):
        """第一個 item 文字 Engineer→Manager → FAIL"""
        result = run(compare_xml_files,
            cfg("fail", "xml", checks=["tag", "text", "attrib", "children_count"])
        )
        assert not result.passed

    def test_fail_attrib_only_ok(self, cfg, run):
        """只比對屬性（屬性相同）→ PASS"""
        result = run(compare_xml_files, cfg("fail", "xml", checks=["attrib"]))
        assert result.passed

    def test_mask_exclude_tag(self, cfg, run):
        """排除 item tag → PASS"""
        result = run(compare_xml_files,
            cfg("fail", "xml",
                checks=["tag", "text", "attrib"],
                mask={"exclude_tags": ["item"]})
        )
        assert result.passed
