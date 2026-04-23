"""
tools/scenario_check.py
=======================

PathManager Waterfall 情境實測腳本 / Scenario verification script.

這份腳本示範三個真實工程情境的完整設定方式，
並對三個測試檔案（555.png / public_key.txt / 複製.xlsx）
用每個情境的關聯 waterfall 進行解析，印出完整 WaterfallTrace。

This script demonstrates three real-world engineering scenarios,
registers three test files under appropriate anchors,
then resolves each tag with the matching waterfall(s) and prints
the full WaterfallTrace so you can see which step matched — or why
every step failed.

測試方法 / How to test
----------------------
1. 把三個測試檔案放到目標位置，執行本腳本，觀察 ✓/✗ 如何變化。
   Place the three test files in the "test locations" shown for each
   scenario, re-run the script, and observe the ✓/✗ changes.

2. 在不同情境間移動檔案，確認哪個 waterfall 命中了哪個位置。
   Move files between locations to confirm which waterfall step wins.

Usage / 使用方式
----------------
    # 最簡單：使用 repo 根當作 proj_root
    # Simplest: use repo root as proj_root
    python tools/scenario_check.py

    # 指定 proj_root（任意目錄或 __file__ 路徑）
    # Specify proj_root (any dir or __file__ path)
    python tools/scenario_check.py --proj C:/MyProject

    # 自訂三個測試檔名（預設為 555.png / public_key.txt / 複製.xlsx）
    # Custom test file names (defaults shown)
    python tools/scenario_check.py --png 555.png --txt public_key.txt --xlsx 複製.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ── 確保從 repo 根執行時也能找到 src/ / Ensure src/ importable when run from repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from isd_py_framework_sdk.path_manager import (
    SingletonPathManager,
    PathMode,
    Waterfall,
    PRESETS,
    ResolveIntent,
    WaterfallTrace,
    EnvironmentResolver,
)
from isd_py_framework_sdk.path_manager._meta import SingletonABCMeta

# ── ANSI 色碼 ──────────────────────────────────────────────────────────────
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_GREEN  = "\033[32m"
_RED    = "\033[31m"
_YELLOW = "\033[33m"
_CYAN   = "\033[36m"
_DIM    = "\033[2m"

def _g(s: str) -> str: return f"{_GREEN}{s}{_RESET}"
def _r(s: str) -> str: return f"{_RED}{s}{_RESET}"
def _y(s: str) -> str: return f"{_YELLOW}{s}{_RESET}"
def _c(s: str) -> str: return f"{_CYAN}{s}{_RESET}"
def _h(s: str) -> str: return f"{_BOLD}{_YELLOW}{s}{_RESET}"  # heading


def _fresh_pm() -> SingletonPathManager:
    """每次呼叫返回全新的 PM 實例（清除 singleton），避免跨情境污染。
    Return a fresh PM instance each call by evicting the singleton cache."""
    SingletonABCMeta._instances.pop(SingletonPathManager, None)
    return SingletonPathManager()


def _print_trace(trace: WaterfallTrace) -> None:
    """彩色印出 waterfall trace 的每個步驟。
    Print each waterfall step with colour-coded ✓/✗."""
    for a in trace.attempts:
        mark = _g("  [✓]") if a.ok else _r("  [✗]")
        mode = _c(f"{a.mode.name:<22}")
        path = str(a.path)
        reason = _DIM + f"({a.reason})" + _RESET
        print(f"{mark} {mode}{path}  {reason}")


def _resolve_show(
    pm: SingletonPathManager,
    tag: str,
    wf: Waterfall,
    intent: ResolveIntent = ResolveIntent.READ,
) -> str | None:
    """解析並印出 trace；回傳解析到的路徑字串（或 None）。
    Resolve and print trace; return resolved path string or None."""
    intent_label = _y(intent.name)
    print(f"  Tag={_c(tag)}  Intent={intent_label}  Waterfall={_y(repr(wf))}")
    path, trace = pm.get_with_trace(tag, wf, intent=intent)
    _print_trace(trace)
    if path:
        print(f"  {_g('RESOLVED')} → {_g(str(path))}")
    else:
        print(f"  {_r('FAILED')} — no step passed.")
    print()
    return str(path) if path else None


# ============================================================================
# 情境 1：日常開發 / Scenario 1: Daily development
# ============================================================================

def scenario_dev(proj_root: Path, png: str, txt: str, xlsx: str) -> None:
    """
    情境 1：日常開發（本機 IDE 執行）
    Scenario 1: Daily development (running from IDE or terminal)

    設定方式 / Setup:
    -----------------
    ● set_proj_root(__file__, levels_up=N) — 指向 repo 根目錄
    ● 全部三個測試檔案均以 PROJ_ABSOLUTE 為 anchor 註冊
      （即「它們應該放在 proj_root 下」）

    測試位置 / Test locations:
    --------------------------
    放到這裡會讓 DEV_STANDARD 的第 1 步（PROJ_ABSOLUTE）命中：
      {proj_root}/555.png
      {proj_root}/public_key.txt
      {proj_root}/複製.xlsx

    放到 CWD（當前終端所在目錄）會讓第 2 步命中：
      {cwd}/555.png  …etc.
    """
    print(_h("=" * 70))
    print(_h("  情境 1：日常開發 / Scenario 1: Daily Development"))
    print(_h("=" * 70))
    print(f"  proj_root = {proj_root}")
    print(f"  cwd       = {EnvironmentResolver.cwd()}")
    print()
    print("  測試位置 / Test locations:")
    print(f"    [第1步命中] {proj_root / png}")
    print(f"    [第1步命中] {proj_root / txt}")
    print(f"    [第1步命中] {proj_root / xlsx}")
    print(f"    [第2步命中] {EnvironmentResolver.cwd() / png}  (CWD)")
    print()

    pm = _fresh_pm()
    pm.set_proj_root(str(proj_root))
    pm.set_app_name("DevApp")
    # 開發時，所有檔案預期放在專案根下。Register files expected in project root.
    pm.register("png",  png,  PathMode.PROJ_ABSOLUTE, description="測試圖片 / test image")
    pm.register("txt",  txt,  PathMode.PROJ_ABSOLUTE, description="公鑰文字 / public key text")
    pm.register("xlsx", xlsx, PathMode.PROJ_ABSOLUTE, description="試算表 / spreadsheet")

    for name, wf in [
        ("DEV_STANDARD",         Waterfall.DEV_STANDARD),
        ("DEV_WITH_USER_CONFIG",  Waterfall.DEV_WITH_USER_CONFIG),
    ]:
        print(f"  ── Waterfall: {_y(name)} ─────────────────────────────────────")
        for tag in ["png", "txt", "xlsx"]:
            _resolve_show(pm, tag, wf)


# ============================================================================
# 情境 2：部署後 (Prod) / Scenario 2: Deployed application
# ============================================================================

def scenario_prod(proj_root: Path, png: str, txt: str, xlsx: str) -> None:
    """
    情境 2：安裝部署後（非 PyInstaller，直接執行 .py 或安裝 wheel）
    Scenario 2: Deployed (non-frozen: running an installed .py or wheel)

    設定方式 / Setup:
    -----------------
    ● 靜態資源（png/txt）以 EXE_ABSOLUTE 為 anchor（部署後資源放在 exe 旁）
    ● 輸出（xlsx）以 EXE_ABSOLUTE 為 anchor（輸出放在 exe 旁），
      使用 PROD_WRITE（WRITE intent）決定實際可寫路徑

    測試位置 / Test locations:
    --------------------------
    exe_side = {exe_side}
    把檔案放到 exe_side/ 會讓 PROD_READ 第 2 步（EXE_ABSOLUTE）命中：
      {{exe_side}}/555.png
      {{exe_side}}/public_key.txt

    把設定檔放到 USER_CONFIG 目錄會讓第 3 步命中：
      {{user_config}}/複製.xlsx
    """
    exe_side    = EnvironmentResolver.exe_side_root()
    user_config = EnvironmentResolver.user_config("DevApp")

    print(_h("=" * 70))
    print(_h("  情境 2：部署後應用 / Scenario 2: Deployed Application"))
    print(_h("=" * 70))
    print(f"  proj_root   = {proj_root}")
    print(f"  exe_side    = {exe_side}")
    print(f"  user_config = {user_config}")
    print()
    print("  測試位置 / Test locations:")
    print(f"    [PROD_READ 第2步] {exe_side / png}")
    print(f"    [PROD_READ 第2步] {exe_side / txt}")
    print(f"    [PROD_READ 第3步] {user_config / xlsx}")
    print()

    pm = _fresh_pm()
    pm.set_proj_root(str(proj_root))
    pm.set_app_name("DevApp")
    # 靜態資源放在 exe 旁；使用 PROD_READ waterfall 跨環境尋找
    pm.register("png",  png,  PathMode.EXE_ABSOLUTE, description="靜態圖片 / static image")
    pm.register("txt",  txt,  PathMode.EXE_ABSOLUTE, description="靜態文字 / static text")
    pm.register("xlsx", xlsx, PathMode.PROJ_ABSOLUTE, description="輸出試算表 / output xlsx")

    for name, wf, intent in [
        ("PROD_READ  (READ)",  Waterfall.PROD_READ,  ResolveIntent.READ),
        ("PROD_WRITE (WRITE)", Waterfall.PROD_WRITE, ResolveIntent.WRITE),
    ]:
        print(f"  ── Waterfall: {_y(name)} ──────────────────────────────────────")
        for tag in ["png", "txt", "xlsx"]:
            _resolve_show(pm, tag, wf, intent=intent)


# ============================================================================
# 情境 3：PyInstaller 凍結 exe / Scenario 3: PyInstaller frozen executable
# ============================================================================

def scenario_pyinstaller(proj_root: Path, png: str, txt: str, xlsx: str) -> None:
    """
    情境 3：PyInstaller 打包後的凍結執行檔（需設定 sys.frozen / sys._MEIPASS）
    Scenario 3: PyInstaller frozen executable

    設定方式 / Setup:
    -----------------
    ● 靜態資源（png/txt）以 PROJ_ABSOLUTE 為 anchor（開發時的預設）
    ● 使用 EXE_PREFER_BUNDLED waterfall 讀取（EXE_INNER 最優先）
    ● 使用 EXE_OVERRIDE waterfall 讀取（EXE_ABSOLUTE 最優先，允許外部覆蓋）

    注意 / Note:
    -----------
    在非凍結環境下執行時，EXE_INNER 步驟會出現 RuntimeError（sys._MEIPASS 不存在），
    trace 會顯示 ✗ 並繼續嘗試下一步——這是正常的 fallback 行為。

    When running outside a PyInstaller bundle, EXE_INNER steps will show a
    RuntimeError in the trace and fall through — this is expected waterfall fallback.

    EXE_PREFER_BUNDLED vs EXE_OVERRIDE:
    ------------------------------------
    EXE_PREFER_BUNDLED : EXE_INNER → EXE_ABSOLUTE → PROJ_ABSOLUTE
      → 內嵌資源不可被外部覆蓋（出廠預設唯讀）
      → Bundled data cannot be overridden by external files.

    EXE_OVERRIDE       : EXE_ABSOLUTE → USER_CONFIG → EXE_INNER
      → 把檔案放在 exe 旁就能覆蓋內嵌預設值（熱更新/補丁用途）
      → Place a file beside the exe to override bundled defaults (hot-patch).

    測試位置 / Test locations:
    --------------------------
    EXE_PREFER_BUNDLED:
      [第1步] sys._MEIPASS/555.png  （需實際在 PyInstaller bundle 下執行）
      [第2步] {{exe_side}}/555.png
      [第3步] {{proj_root}}/555.png

    EXE_OVERRIDE（覆蓋模式）:
      [第1步] {{exe_side}}/555.png       ← 外部覆蓋優先
      [第2步] {{user_config}}/555.png    ← 使用者設定次之
      [第3步] sys._MEIPASS/555.png       ← 內嵌預設最後才用
    """
    exe_side    = EnvironmentResolver.exe_side_root()
    user_config = EnvironmentResolver.user_config("DevApp")

    print(_h("=" * 70))
    print(_h("  情境 3：PyInstaller 打包 / Scenario 3: PyInstaller Frozen Exe"))
    print(_h("=" * 70))
    print(f"  is_pyinstaller = {EnvironmentResolver.is_pyinstaller()} "
          f"{_DIM}(true only inside a frozen bundle){_RESET}")
    print(f"  exe_side       = {exe_side}")
    print(f"  user_config    = {user_config}")
    print(f"  proj_root      = {proj_root}")
    print()
    print("  EXE_PREFER_BUNDLED 測試位置 / test locations (bundled wins):")
    print(f"    [第1步] sys._MEIPASS/{png}  (frozen only)")
    print(f"    [第2步] {exe_side / png}")
    print(f"    [第3步] {proj_root / png}")
    print()
    print("  EXE_OVERRIDE 覆蓋模式測試位置 / test locations (external wins):")
    print(f"    [第1步] {exe_side / png}        ← 放這裡可覆蓋內嵌 / place here to override")
    print(f"    [第2步] {user_config / png}  ← 使用者設定 / user config override")
    print(f"    [第3步] sys._MEIPASS/{png}  (frozen only, last resort)")
    print()

    pm = _fresh_pm()
    pm.set_proj_root(str(proj_root))
    pm.set_app_name("DevApp")
    # 開發階段以 PROJ_ABSOLUTE 為 anchor；
    # waterfall 讓同一份 tag 在 frozen 環境下尋找 EXE_INNER/EXE_ABSOLUTE
    pm.register("png",  png,  PathMode.PROJ_ABSOLUTE)
    pm.register("txt",  txt,  PathMode.PROJ_ABSOLUTE)
    pm.register("xlsx", xlsx, PathMode.PROJ_ABSOLUTE)

    for name, wf in [
        ("EXE_PREFER_BUNDLED (唯讀-內嵌優先)",  Waterfall.EXE_PREFER_BUNDLED),
        ("EXE_OVERRIDE       (覆蓋模式-外部優先)", Waterfall.EXE_OVERRIDE),
        ("UNIVERSAL          (最高相容性)",      Waterfall.UNIVERSAL),
    ]:
        print(f"  ── Waterfall: {_y(name)} ─────────────────────────────────────")
        for tag in ["png", "txt", "xlsx"]:
            _resolve_show(pm, tag, wf)


# ============================================================================
# 情境 4：ETL 批次管線 / Scenario 4: ETL pipeline
# ============================================================================

def scenario_etl(proj_root: Path, png: str, txt: str, xlsx: str) -> None:
    """
    情境 4：ETL 批次管線（讀取輸入、寫入輸出）
    Scenario 4: ETL batch pipeline (read inputs, write outputs)

    設定方式 / Setup:
    -----------------
    ● 輸入（png/txt）以 PROJ_ABSOLUTE 為 anchor，使用 ETL_INPUT waterfall 讀取
    ● 輸出（xlsx）以 PROJ_ABSOLUTE 為 anchor，使用 ETL_OUTPUT waterfall 寫入

    測試位置 / Test locations:
    --------------------------
    ETL_INPUT（讀取）:
      [第1步] {proj_root}/{png}           ← 標準輸入位置
      [第2步] {cwd}/{png}                 ← 工作目錄（快速測試）
      [第3步] {system_temp}/{png}         ← staging 暫存區

    ETL_OUTPUT（寫入 WRITE intent）:
      [第1步] {proj_root}/{xlsx}           ← 標準輸出（WRITE 檢查父目錄是否可寫）
      [第2步] {user_data}/{xlsx}
      [第3步] {system_temp}/{xlsx}         ← 兜底（管線永不中止）
    """
    system_temp = EnvironmentResolver.system_temp_root()
    user_data   = EnvironmentResolver.user_data("DevApp")
    cwd         = EnvironmentResolver.cwd()

    print(_h("=" * 70))
    print(_h("  情境 4：ETL 批次管線 / Scenario 4: ETL Pipeline"))
    print(_h("=" * 70))
    print(f"  proj_root   = {proj_root}")
    print(f"  cwd         = {cwd}")
    print(f"  system_temp = {system_temp}")
    print(f"  user_data   = {user_data}")
    print()
    print("  ETL_INPUT 測試位置 / test locations (READ):")
    print(f"    [第1步] {proj_root / png}")
    print(f"    [第1步] {proj_root / txt}")
    print(f"    [第2步] {cwd / png}  (CWD fallback)")
    print()
    print("  ETL_OUTPUT 測試位置 / test locations (WRITE):")
    print(f"    [第1步] {proj_root / xlsx}  (WRITE: parent must be writable)")
    print(f"    [第2步] {user_data / xlsx}")
    print(f"    [第3步] {system_temp / xlsx}")
    print()

    pm = _fresh_pm()
    pm.set_proj_root(str(proj_root))
    pm.set_app_name("ETLTool")
    pm.register("png",  png,  PathMode.PROJ_ABSOLUTE, description="輸入圖片 / input image")
    pm.register("txt",  txt,  PathMode.PROJ_ABSOLUTE, description="輸入文字 / input text")
    pm.register("xlsx", xlsx, PathMode.PROJ_ABSOLUTE, description="輸出報表 / output report")

    print(f"  ── ETL_INPUT (READ) ─────────────────────────────────────────────")
    for tag in ["png", "txt"]:
        _resolve_show(pm, tag, Waterfall.ETL_INPUT, intent=ResolveIntent.READ)

    print(f"  ── ETL_OUTPUT (WRITE) ───────────────────────────────────────────")
    _resolve_show(pm, "xlsx", Waterfall.ETL_OUTPUT, intent=ResolveIntent.WRITE)


# ============================================================================
# 全 preset 比較 / All-preset comparison
# ============================================================================

def scenario_all_presets(proj_root: Path, png: str) -> None:
    """
    針對單一 tag（PNG 圖片）執行全部 9 個 active preset，印出比較摘要。
    Run all 9 active presets against a single tag and print a comparison summary.
    適合快速確認：在目前的環境與檔案位置下，哪些 preset 能命中。
    Quick sanity check: which presets succeed in the current environment.
    """
    print(_h("=" * 70))
    print(_h("  全 Preset 比較 / All-Preset Comparison"))
    print(_h(f"  Tag: png = {repr(png)}"))
    print(_h("=" * 70))

    pm = _fresh_pm()
    pm.set_proj_root(str(proj_root))
    pm.set_app_name("DevApp")
    pm.register("png", png, PathMode.PROJ_ABSOLUTE)

    for name, wf in PRESETS.items():
        path, trace = pm.get_with_trace("png", wf)
        ok_mark = _g("✓ OK  ") if path else _r("✗ MISS")
        result  = _g(str(path)) if path else _DIM + "—" + _RESET
        print(f"  {ok_mark}  {name:<25} → {result}")
    print()


# ============================================================================
# CLI entry-point
# ============================================================================

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="PathManager Waterfall 情境實測 / Scenario verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--proj", default=None,
        help=(
            "專案根目錄（預設為 repo 根 = tools/../）。\n"
            "Project root directory (default: repo root = tools/../)."
        ),
    )
    p.add_argument("--png", default="555.png",      help="PNG 檔名 / PNG filename")
    p.add_argument("--txt", default="public_key.txt", help="TXT 檔名 / TXT filename")
    p.add_argument("--xlsx", default="複製.xlsx",     help="XLSX 檔名 / XLSX filename")
    p.add_argument(
        "--scenario", choices=["1", "2", "3", "4", "all", "compare"],
        default="all",
        help=(
            "執行指定情境（預設全部）。\n"
            "  1=dev, 2=prod, 3=pyinstaller, 4=etl, all=全部, compare=全preset比較\n"
            "Run specific scenario (default=all)."
        ),
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    # 解析 proj_root / Resolve proj_root
    if args.proj:
        proj_root = Path(args.proj).resolve()
        if proj_root.is_file():
            proj_root = proj_root.parent
    else:
        # 預設為 repo 根（tools/ 的上一層）/ Default: repo root (parent of tools/)
        proj_root = Path(__file__).resolve().parent.parent

    print()
    print(_h("  PathManager Waterfall Scenario Check"))
    print(_h(f"  proj_root = {proj_root}"))
    print(_h(f"  files     = {args.png}, {args.txt}, {args.xlsx}"))
    print()

    run_all = args.scenario == "all"

    if run_all or args.scenario == "1":
        scenario_dev(proj_root, args.png, args.txt, args.xlsx)

    if run_all or args.scenario == "2":
        scenario_prod(proj_root, args.png, args.txt, args.xlsx)

    if run_all or args.scenario == "3":
        scenario_pyinstaller(proj_root, args.png, args.txt, args.xlsx)

    if run_all or args.scenario == "4":
        scenario_etl(proj_root, args.png, args.txt, args.xlsx)

    if run_all or args.scenario == "compare":
        scenario_all_presets(proj_root, args.png)


if __name__ == "__main__":
    main()
