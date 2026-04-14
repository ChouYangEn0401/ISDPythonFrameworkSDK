"""
tests/file_test — conftest
──────────────────────────
自動產生 fixture 檔案，並提供 ``cfg`` fixture 供測試使用。

Fixture 命名慣例
~~~~~~~~~~~~~~~~
  標準檔 (benchmark) : ``[BU] sample.{ext}``
  待測檔 (target)    : ``sample.{ext}``

目錄
~~~~
  ``fixtures/pass/``  — 一對完全相同的檔案（預期 PASS）
  ``fixtures/fail/``  — 一對有已知差異的檔案（預期 FAIL）

差異摘要 (fail 資料夾)
~~~~~~~~~~~~~~~~~~~~~~
  CSV  : Row3 age 25→26 , Row4 city Tainan→Taichung
  JSON : $.users[0].age 30→31
  JSONL: Line2 age 25→26
  TXT  : Line2 文字不同
  YAML : $.server.port 8080→9090
  XML  : 第一個 <item> 文字 Engineer→Manager
  INI  : [server] port 8080→9090
  TOML : $.server.port 8080→9090
  XLSX : Row3 col B (age) 25→26
"""
import os
import json
import pytest

# ── 路徑常數 ──────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(_HERE, "fixtures")
PASS_DIR = os.path.join(FIXTURES, "pass")
FAIL_DIR = os.path.join(FIXTURES, "fail")
SAMPLE = "sample"


def _bench(case: str, ext: str) -> str:
    d = PASS_DIR if case == "pass" else FAIL_DIR
    return os.path.join(d, f"[BU] {SAMPLE}.{ext}")


def _target(case: str, ext: str) -> str:
    d = PASS_DIR if case == "pass" else FAIL_DIR
    return os.path.join(d, f"{SAMPLE}.{ext}")


def _build_config(case: str, ext: str, **kw) -> dict:
    """組合 compare 函式需要的 config dict。"""
    cfg = {"target_path": _target(case, ext), "bench_path": _bench(case, ext)}
    cfg.update(kw)
    return cfg


# ── pytest fixture ───────────────────────────────────────────────────────
@pytest.fixture
def cfg():
    """提供 ``build_config(case, ext, **kw)`` 供測試組裝 config。

    Usage::

        def test_csv_pass(cfg):
            result = compare_csv_files(cfg("pass", "csv", checks=["content"]))
            assert result.passed
    """
    return _build_config


# ── Fixture 資料 ─────────────────────────────────────────────────────────
# CSV — Row3 age 不同 (25→26), Row4 city 不同 (Tainan→Taichung)
_CSV      = "name,age,city\nAlice,30,Taipei\nBob,25,Kaohsiung\nCharlie,35,Tainan\n"
_CSV_DIFF = "name,age,city\nAlice,30,Taipei\nBob,26,Kaohsiung\nCharlie,35,Taichung\n"

# JSON — $.users[0].age 不同 (30→31)
_JSON      = {"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}], "count": 2}
_JSON_DIFF = {"users": [{"name": "Alice", "age": 31}, {"name": "Bob", "age": 25}], "count": 2}

# JSONL — 第 2 行 age 不同 (25→26)
_JSONL      = '{"name": "Alice", "age": 30}\n{"name": "Bob", "age": 25}\n{"name": "Charlie", "age": 35}\n'
_JSONL_DIFF = '{"name": "Alice", "age": 30}\n{"name": "Bob", "age": 26}\n{"name": "Charlie", "age": 35}\n'

# TXT — 第 2 行不同
_TXT      = "Hello World\nThis is a test file.\nThird line here.\n"
_TXT_DIFF = "Hello World\nThis has been modified.\nThird line here.\n"

# YAML — $.server.port 不同 (8080→9090)
_YAML      = "server:\n  host: localhost\n  port: 8080\ndatabase:\n  name: testdb\n  host: 127.0.0.1\n"
_YAML_DIFF = "server:\n  host: localhost\n  port: 9090\ndatabase:\n  name: testdb\n  host: 127.0.0.1\n"

# XML — 第一個 <item> 文字不同 (Engineer→Manager)
_XML      = ('<?xml version="1.0" encoding="UTF-8"?>\n<root>\n'
             '  <item name="Alice" age="30">Engineer</item>\n'
             '  <item name="Bob" age="25">Designer</item>\n</root>\n')
_XML_DIFF = ('<?xml version="1.0" encoding="UTF-8"?>\n<root>\n'
             '  <item name="Alice" age="30">Manager</item>\n'
             '  <item name="Bob" age="25">Designer</item>\n</root>\n')

# INI — [server] port 不同 (8080→9090)
_INI      = "[server]\nhost = localhost\nport = 8080\n\n[database]\nname = testdb\nhost = 127.0.0.1\n"
_INI_DIFF = "[server]\nhost = localhost\nport = 9090\n\n[database]\nname = testdb\nhost = 127.0.0.1\n"

# TOML — [server] port 不同 (8080→9090)
_TOML      = '[server]\nhost = "localhost"\nport = 8080\n\n[database]\nname = "testdb"\nhost = "127.0.0.1"\n'
_TOML_DIFF = '[server]\nhost = "localhost"\nport = 9090\n\n[database]\nname = "testdb"\nhost = "127.0.0.1"\n'

# XLSX — Row3 col B (age) 不同 (25→26)
_XLSX_ROWS      = [["name", "age", "city"], ["Alice", 30, "Taipei"], ["Bob", 25, "Kaohsiung"]]
_XLSX_DIFF_ROWS = [["name", "age", "city"], ["Alice", 30, "Taipei"], ["Bob", 26, "Kaohsiung"]]


# ── 寫檔工具 ─────────────────────────────────────────────────────────────
def _w(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)


def _generate_all():
    """產生 pass / fail 所有 fixture 檔案。"""
    text_pairs = [
        ("csv",  _CSV,  _CSV_DIFF),
        ("jsonl", _JSONL, _JSONL_DIFF),
        ("txt",  _TXT,  _TXT_DIFF),
        ("yaml", _YAML, _YAML_DIFF),
        ("xml",  _XML,  _XML_DIFF),
        ("ini",  _INI,  _INI_DIFF),
        ("toml", _TOML, _TOML_DIFF),
    ]
    for ext, base, diff in text_pairs:
        for case, content in [("pass", base), ("fail", diff)]:
            _w(_bench(case, ext), base)
            _w(_target(case, ext), content)

    # JSON (dict → formatted string)
    for case, obj in [("pass", _JSON), ("fail", _JSON_DIFF)]:
        _w(_bench(case, "json"), json.dumps(_JSON, indent=2, ensure_ascii=False))
        _w(_target(case, "json"), json.dumps(obj, indent=2, ensure_ascii=False))

    # XLSX (binary — needs openpyxl)
    try:
        from openpyxl import Workbook
        for case, t_rows in [("pass", _XLSX_ROWS), ("fail", _XLSX_DIFF_ROWS)]:
            for path, rows in [(_bench(case, "xlsx"), _XLSX_ROWS),
                               (_target(case, "xlsx"), t_rows)]:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                wb = Workbook()
                ws = wb.active
                ws.title = "Sheet1"
                for row in rows:
                    ws.append(row)
                wb.save(path)
    except ImportError:
        pass


@pytest.fixture(scope="session", autouse=True)
def _ensure_fixtures():
    """在第一個測試執行前自動產生所有 fixture 檔案。"""
    _generate_all()


# ── 相容新舊 API 的 run fixture ──────────────────────────────────────────
class _FallbackResult:
    """Minimal stand-in when compare functions return bool/None (old API)."""
    __slots__ = ("passed", "errors")

    def __init__(self, passed: bool):
        self.passed = passed
        self.errors = [] if passed else ["(detail not available from old API)"]

    def __bool__(self):
        return self.passed


@pytest.fixture
def run():
    """Wrap a compare function call, normalising its return to ``.passed`` / ``.errors``.

    Works with both the old API (returns ``bool`` / ``None``) and the new
    ``CompareResult`` API.
    """
    def _invoke(compare_fn, config):
        raw = compare_fn(config)
        if raw is None:
            pytest.skip("compare function returned None — requires CompareResult API")
        if hasattr(raw, "passed"):
            return raw
        return _FallbackResult(bool(raw))
    return _invoke
