"""
file_compare.html_report
─────────────────────────
Generate a self-contained HTML diff report from a list of CompareResult objects.

Usage::

    from hyper_framework.file_compare.html_report import generate_html_report
    from hyper_framework.file_compare.csv_unittest_module import compare_csv_files

    r1 = compare_csv_files({...})
    r2 = compare_csv_files({...})
    generate_html_report([r1, r2], "report.html")
"""
import re
from datetime import datetime
from typing import List, Optional

from ._shared import CompareResult

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(s: str) -> str:
    return _ANSI_RE.sub("", s)


def _esc(s) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _error_row(err) -> str:
    if isinstance(err, tuple) and len(err) == 4:
        path, desc, actual, expected = err
        return (
            f"<tr>"
            f"<td class='p'>{_esc(path)}</td>"
            f"<td>{_esc(desc)}</td>"
            f"<td class='a'>{_esc(actual)}</td>"
            f"<td class='e'>{_esc(expected)}</td>"
            f"</tr>"
        )
    plain = _strip_ansi(str(err))
    return f"<tr><td colspan='4' class='msg'>{_esc(plain)}</td></tr>"


_CSS = """
:root{--pass:#22c55e;--fail:#ef4444;--bg:#0f172a;--card:#1e293b;
      --border:#334155;--text:#e2e8f0;--muted:#94a3b8;
      --a:#fca5a5;--e:#86efac;--p:#7dd3fc;}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:ui-monospace,monospace;background:var(--bg);color:var(--text);padding:2rem;font-size:14px}
h1{font-size:1.3rem;margin-bottom:.2rem}
.meta{color:var(--muted);font-size:.75rem;margin-bottom:1.5rem}
.bar{display:flex;gap:2rem;padding:1rem 1.5rem;background:var(--card);
     border-radius:.5rem;border:1px solid var(--border);margin-bottom:2rem}
.bar .n{font-size:1.6rem;font-weight:700}
.bar label{font-size:.7rem;color:var(--muted)}
.pc{color:var(--pass)}.fc{color:var(--fail)}
details{background:var(--card);border:1px solid var(--border);
        border-radius:.5rem;margin-bottom:.6rem;overflow:hidden}
details.fail{border-left:3px solid var(--fail)}
details.pass{border-left:3px solid var(--pass)}
summary{display:flex;align-items:center;gap:.75rem;padding:.7rem 1rem;
        cursor:pointer;user-select:none;list-style:none}
summary::-webkit-details-marker{display:none}
summary:hover{background:rgba(255,255,255,.03)}
.icon{font-size:1rem}.fail .icon{color:var(--fail)}.pass .icon{color:var(--pass)}
.lbl{flex:1;font-weight:600}
.cnt{font-size:.78rem;color:var(--muted)}.fail .cnt{color:var(--fail)}.pass .cnt{color:var(--pass)}
.body{padding:0 1rem .8rem}
.ok{color:var(--pass);font-size:.82rem;padding:.4rem 0}
table{width:100%;border-collapse:collapse;font-size:.78rem;margin-top:.5rem}
th{text-align:left;padding:.35rem .6rem;background:rgba(255,255,255,.04);
   color:var(--muted);border-bottom:1px solid var(--border)}
td{padding:.3rem .6rem;border-bottom:1px solid rgba(255,255,255,.04);
   vertical-align:top;word-break:break-all}
tr:last-child td{border-bottom:none}
.p{color:var(--p)}.a{color:var(--a)}.e{color:var(--e)}
.msg{color:var(--text)}
"""

_CARD = """\
<details class="{cls}" {open_attr}>
  <summary>
    <span class="icon">{icon}</span>
    <span class="lbl">{label}</span>
    <span class="cnt">{cnt}</span>
  </summary>
  <div class="body">{body}</div>
</details>"""


def generate_html_report(
    results: List[CompareResult],
    output_path: str,
    title: str = "File Comparison Report",
) -> str:
    """Write a self-contained HTML report and return ``output_path``.

    Args:
        results:     List of :class:`CompareResult` from any comparison function.
        output_path: Destination ``.html`` file path.
        title:       Browser tab / heading title.
    """
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cards = []
    for r in results:
        cls = "pass" if r.passed else "fail"
        icon = "✓" if r.passed else "✗"
        cnt = "PASS" if r.passed else f"{len(r.errors)} errors"
        open_attr = "" if r.passed else "open"

        if not r.errors:
            body = '<p class="ok">No differences found.</p>'
        else:
            rows = "\n".join(_error_row(e) for e in r.errors)
            body = (
                "<table>"
                "<thead><tr>"
                "<th>路徑 / 位置</th><th>描述</th>"
                "<th>實際值</th><th>預期值</th>"
                "</tr></thead>"
                f"<tbody>{rows}</tbody>"
                "</table>"
            )

        cards.append(
            _CARD.format(
                cls=cls,
                open_attr=open_attr,
                icon=icon,
                label=_esc(r.label),
                cnt=cnt,
                body=body,
            )
        )

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(title)}</title>
<style>{_CSS}</style>
</head>
<body>
<h1>📊 {_esc(title)}</h1>
<p class="meta">Generated: {ts} &nbsp;|&nbsp; {len(results)} tests</p>
<div class="bar">
  <div><span class="n pc">{passed}</span><label>PASSED</label></div>
  <div><span class="n fc">{failed}</span><label>FAILED</label></div>
</div>
{"".join(cards)}
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n[Done] HTML 報告已儲存至: {output_path}")
    return output_path
