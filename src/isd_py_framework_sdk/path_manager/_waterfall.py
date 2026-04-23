"""
Waterfall — 有序回退鏈，用於跨環境路徑解析。
Waterfall — ordered fallback chain for cross-environment path resolution.

A ``Waterfall`` is a sequence of ``PathMode`` steps.  During resolution the
manager attempts each step in order and returns the first path that satisfies
a **validation check** ("first found wins").
一個 ``Waterfall`` 是一連串有序的 ``PathMode`` 步驟，依序嘗試每個步驟，
回傳第一個滿足驗證條件的路徑（誰先讀到就不往下走）。

By default / 預設驗證規則:

- ``ResolveIntent.READ``  → 路徑必須存在於磁碟 / the path must exist on disk
- ``ResolveIntent.WRITE`` → 路徑最近的已存在祖先目錄必須可寫入
  / the nearest existing ancestor of the path must be writable

If you need custom validation, pass a ``check`` callable to the constructor.
若需要自訂驗證邏輯，可將 ``check`` callable 傳入建構子。

If no step passes, a ``FileNotFoundError`` is raised that includes a
``WaterfallTrace`` listing every attempt — making debugging easy.
若所有步驟皆失敗，拋出 ``FileNotFoundError``，並附上完整的 ``WaterfallTrace``
供除錯用。

Usage / 使用範例
----------------
::

    from isd_py_framework_sdk.path_manager import Waterfall, PathMode, ResolveIntent

    # 自訂 waterfall / Custom waterfall
    wf = Waterfall(PathMode.EXE_INNER, PathMode.EXE_ABSOLUTE, PathMode.PROJ_ABSOLUTE)

    # 標準讀取（失敗時 raise）/ Standard read (raises on failure)
    path = pm.get("my_config", wf)

    # 寫入意圖 / Write intent
    path = pm.get("output_excel", Waterfall.ETL_OUTPUT, intent=ResolveIntent.WRITE)

    # 取得 trace（不 raise）/ Inspect trace without raising
    path, trace = pm.get_with_trace("my_config", wf)
    print(trace)  # 印出每步驟的 ✓/✗

Active Presets / 啟用中的預設值
--------------------------------
+---------------------+-----------------------------------+-----------------------------------------------+
| Constant            | Steps (→ priority order)          | Behaviour & use-case                          |
+=====================+===================================+===============================================+
| DEV_STANDARD        | PROJ → CWD                        | READ. 先看專案根，找不到才退回 CWD。             |
|                     |                                   | 無 exe/user 資料夾感知，不適合打包環境。          |
+---------------------+-----------------------------------+-----------------------------------------------+
| DEV_WITH_USER_CONFIG| USER_CFG → PROJ → CWD             | READ. ~/.config/ 可覆蓋版控預設值，             |
|                     |                                   | 適合本機 API key / DB DSN 不應版控的場景。       |
+---------------------+-----------------------------------+-----------------------------------------------+
| PROD_READ           | PROJ → EXE → USER_CFG             | READ. 安裝目錄優先，再找 exe 旁還有 AppData。    |
|                     |                                   | 允許系統管理員在 exe 旁放置覆蓋設定檔。           |
+---------------------+-----------------------------------+-----------------------------------------------+
| PROD_WRITE          | EXE → USER_DATA → TEMP            | WRITE. exe 旁優先；如果 exe 目錄唯讀            |
|                     |                                   | （如 Program Files）則退到 AppData，最後兜底 TEMP.|
+---------------------+-----------------------------------+-----------------------------------------------+
| EXE_PREFER_BUNDLED  | MEIPASS → EXE → PROJ              | READ / PyInstaller「唯讀資源」模式。             |
|                     |                                   | MEIPASS 永遠勝出，外部同名檔案無法覆蓋。          |
+---------------------+-----------------------------------+-----------------------------------------------+
| EXE_OVERRIDE        | EXE → USER_CFG → MEIPASS          | READ / PyInstaller「可客製化」模式。             |
|                     |                                   | exe 旁外部檔可覆蓋 MEIPASS 預設值，              |
|                     |                                   | 部署後現場替換設定不需重新編譯。                  |
+---------------------+-----------------------------------+-----------------------------------------------+
| ETL_INPUT           | PROJ → CWD → TEMP                 | READ. 找輸入資料；CI/CD TEMP staging 也返回。    |
+---------------------+-----------------------------------+-----------------------------------------------+
| ETL_OUTPUT          | PROJ → USER_DATA → TEMP           | WRITE. 先寫專案 outputs/，退回 AppData，        |
|                     |                                   | 兜底 TEMP 確保管線不因輸出目錄不可寫而中止。       |
+---------------------+-----------------------------------+-----------------------------------------------+
| UNIVERSAL           | 全部六個定位點（按順序）             | READ. 全環境通用；適合函式庫程式碼或              |
|                     |                                   | 執行環境不確定的場景。                           |
+---------------------+-----------------------------------+-----------------------------------------------+

Retired aliases (identical steps, kept for back-compat) / 退役別名（步驟與上表重複，保留以維持相容性）:
  CI_ARTIFACT  = ETL_INPUT   (PROJ → CWD → TEMP)
  EXE_WRITE_SAFE = PROD_WRITE  (EXE → USER_DATA → TEMP)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Optional

from ._enums import PathMode


# ------------------------------------------------------------------ #
#  Intent                                                             #
# ------------------------------------------------------------------ #

class ResolveIntent(Enum):
    """
    Whether we intend to **read** from or **write** to the resolved path.

    This affects the default validation check applied to each candidate:

    ``READ``
        The path must exist on disk.
    ``WRITE``
        The path's parent directory must exist (the file itself need not
        exist yet, and will be created by the caller).
    """

    READ  = auto()
    WRITE = auto()


# ------------------------------------------------------------------ #
#  Validation helpers                                                 #
# ------------------------------------------------------------------ #

def _check_exists(p: Path) -> bool:
    """Default READ check: path must exist."""
    return p.exists()


def _check_writable_location(p: Path) -> bool:
    """
    WRITE check: the path is writable, or an ancestor directory exists and
    is writable (meaning all intermediate directories can be created).

    Walks up the path hierarchy to the nearest existing ancestor rather than
    only checking the immediate parent.  This allows ``outputs/result.csv``
    to pass even when ``outputs/`` has not been created yet, as long as the
    project root (or temp dir) itself is writable.
    """
    if p.exists():
        return os.access(p, os.W_OK)
    candidate = p.parent
    while not candidate.exists():
        parent = candidate.parent
        if parent == candidate:  # reached filesystem root without match
            return False
        candidate = parent
    return os.access(candidate, os.W_OK)


def _default_check(intent: ResolveIntent) -> Callable[[Path], bool]:
    if intent is ResolveIntent.READ:
        return _check_exists
    return _check_writable_location


# ------------------------------------------------------------------ #
#  Trace                                                              #
# ------------------------------------------------------------------ #

@dataclass
class Attempt:
    """
    Records one step in a ``Waterfall`` resolution attempt.

    Attributes
    ----------
    mode : PathMode
        The step that was tried.
    path : Path
        The candidate path that was evaluated (``Path("<error>")`` on exception).
    ok : bool
        Whether this step passed the validation check.
    reason : str
        Human-readable explanation (``"accepted"``, ``"check failed"``,
        or an exception message).
    """

    mode:   PathMode
    path:   Path
    ok:     bool
    reason: str

    def __str__(self) -> str:
        status = "✓" if self.ok else "✗"
        return f"  [{status}] {self.mode.name:<20} {self.path}  ({self.reason})"


class WaterfallTrace:
    """Collection of ``Attempt`` records from a single waterfall resolution."""

    def __init__(self, waterfall: "Waterfall", attempts: list[Attempt]) -> None:
        self._waterfall = waterfall
        self._attempts  = attempts

    @property
    def attempts(self) -> list[Attempt]:
        return list(self._attempts)

    @property
    def succeeded(self) -> bool:
        return any(a.ok for a in self._attempts)

    def __str__(self) -> str:
        lines = [f"WaterfallTrace for {self._waterfall}:"]
        lines.extend(str(a) for a in self._attempts)
        return "\n".join(lines)

    def __repr__(self) -> str:
        return str(self)


# ------------------------------------------------------------------ #
#  Waterfall                                                          #
# ------------------------------------------------------------------ #

class Waterfall:
    """
    Ordered sequence of ``PathMode`` steps for fallback path resolution.

    Parameters
    ----------
    *steps : PathMode
        One or more ``PathMode`` values tried in order.
    check : callable, optional
        A custom ``(Path) -> bool`` predicate.  When provided it
        overrides the default intent-based check for every step.
    """

    def __init__(
        self,
        *steps: PathMode,
        check: Optional[Callable[[Path], bool]] = None,
    ) -> None:
        if not steps:
            raise ValueError("A Waterfall must contain at least one PathMode step.")
        self._steps: tuple[PathMode, ...] = steps
        self._check: Optional[Callable[[Path], bool]] = check

    # ------------------------------------------------------------------ #
    #  Public interface                                                    #
    # ------------------------------------------------------------------ #

    @property
    def steps(self) -> tuple[PathMode, ...]:
        """The ordered resolution steps (immutable)."""
        return self._steps

    def resolve(
        self,
        resolver: Callable[[PathMode], Path],
        *,
        intent: ResolveIntent = ResolveIntent.READ,
        with_trace: bool = False,
    ) -> "Path | tuple[Optional[Path], WaterfallTrace]":
        """
        Attempt each step using *resolver* and return the first passing path.

        Parameters
        ----------
        resolver :
            A callable ``(PathMode) -> Path`` supplied by the path manager.
            Keeping it external means ``Waterfall`` stays decoupled from
            the manager's internal state.
        intent :
            ``READ`` (default) or ``WRITE`` — controls the default check.
            Ignored when a custom ``check`` was passed to the constructor.
        with_trace :
            If ``True``, always return ``(path_or_None, WaterfallTrace)``
            instead of raising on failure.  The caller must handle
            ``path is None`` when all steps failed.

        Returns
        -------
        Path
            When *with_trace* is ``False`` and a step passes.
        (Path | None, WaterfallTrace)
            When *with_trace* is ``True``.

        Raises
        ------
        FileNotFoundError
            When *with_trace* is ``False`` and every step fails.
        """
        check = self._check or _default_check(intent)
        attempts: list[Attempt] = []

        for mode in self._steps:
            try:
                p = resolver(mode)
                ok = check(p)
                attempts.append(Attempt(mode, p, ok, "accepted" if ok else "check failed"))
                if ok:
                    if with_trace:
                        return p, WaterfallTrace(self, attempts)
                    return p
            except Exception as exc:
                attempts.append(Attempt(mode, Path("<error>"), False, str(exc)))

        trace = WaterfallTrace(self, attempts)
        if with_trace:
            return None, trace

        raise FileNotFoundError(
            f"Waterfall exhausted — no valid path found.\n{trace}"
        )

    # ------------------------------------------------------------------ #
    #  Dunder helpers                                                      #
    # ------------------------------------------------------------------ #

    def __repr__(self) -> str:
        chain = " → ".join(s.name for s in self._steps)
        return f"Waterfall({chain})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Waterfall):
            return self._steps == other._steps
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._steps)

    # ------------------------------------------------------------------ #
    #  Pre-built preset annotations  (instances assigned after class)    #
    #  預設 preset 的型別宣告（實例在 class body 後賦值）                 #
    # ------------------------------------------------------------------ #

    # ── Developer workstation（開發機）────────────────────────────────

    #: 日常開發讀取：優先專案根目錄，找不到則退回 CWD。
    #: Daily dev reading: project root first, fall back to cwd.
    DEV_STANDARD: "Waterfall"

    #: 帶個人設定覆蓋的開發模式：USER_CONFIG 優先（例如個人 API key），
    #: 再到專案根，再到 CWD。
    #: Dev with personal overrides: USER_CONFIG first (e.g. local API keys),
    #: then project root, then cwd.
    DEV_WITH_USER_CONFIG: "Waterfall"

    # ── Production / deployed app（部署後應用）────────────────────────

    #: 已部署程式讀取資源 / 設定：專案根 → exe 旁 → USER_CONFIG。
    #: Deployed app reading assets or config: proj root → exe-side → user config.
    PROD_READ: "Waterfall"

    #: 已部署程式寫入紀錄 / 輸出：exe 旁（若可寫）→ USER_DATA → SYSTEM_TEMP。
    #: Deployed app writing logs or outputs: exe-side → user data dir → system temp.
    PROD_WRITE: "Waterfall"

    # ── PyInstaller / frozen executable（打包執行檔）─────────────────

    #: 【唯讀-內嵌優先】凍結 exe 讀取：EXE_INNER（MEIPASS）優先 → exe 旁 → 專案根。
    #: 用於出廠預設資源：外部檔案**無法**覆蓋內嵌資料。
    #:
    #: [Read, bundled wins] Frozen exe reading: EXE_INNER (sys._MEIPASS) first
    #: → beside exe → project root.
    #: Use for factory defaults that must not be overridden by external files.
    EXE_PREFER_BUNDLED: "Waterfall"

    #: 【覆蓋模式 / Override mode】凍結 exe 讀取：exe 旁 → USER_CONFIG → EXE_INNER。
    #: 允許使用者把檔案放在 exe 旁（或 USER_CONFIG）來覆蓋內嵌的預設資源，
    #: 如果外部都找不到才回退到 MEIPASS 內的版本。
    #:
    #: [Read, external overrides bundled] Frozen exe reading: beside exe first
    #: → user config → EXE_INNER (MEIPASS) as last resort.
    #: Allows patching a deployed app by placing a file next to the exe
    #: without recompiling — the external file wins.
    EXE_OVERRIDE: "Waterfall"

    # ── ETL pipelines（批次管線）──────────────────────────────────────

    #: ETL 輸入：在專案根找原始資料，退回 CWD，最後退到 SYSTEM_TEMP（staging 區）。
    #: ETL input: find source data under project root, then cwd, then staging temp.
    ETL_INPUT: "Waterfall"

    #: ETL 輸出（WRITE intent）：優先寫到專案根 outputs；若不可用則 USER_DATA；
    #: 最後退到 SYSTEM_TEMP 確保管線不會因為找不到輸出目錄而中止。
    #: ETL output (WRITE intent): write to project root first, then user data dir,
    #: last resort system temp so the pipeline never crashes silently.
    ETL_OUTPUT: "Waterfall"

    # ── Maximum compatibility（最高相容性）────────────────────────────

    #: 依序嘗試全部六個定位點，適合要在開發、部署、凍結三種環境下都能運作的函式庫程式碼。
    #: Try all six anchors in a sensible order — good for library code that must
    #: work in dev, deployed, and frozen environments without extra configuration.
    UNIVERSAL: "Waterfall"

    # ── Retired aliases（退役別名）────────────────────────────────────
    # 以下兩個 preset 步驟與上方重複，保留以維持向下相容性，不建議新程式碼使用。
    # The following two presets are identical to existing ones above.
    # Kept for back-compat only — do not use in new code.

    #: [alias] CI pipeline artefacts — identical steps to ETL_INPUT.
    #: [別名] CI 管線產出物 — 步驟與 ETL_INPUT 完全相同。
    CI_ARTIFACT: "Waterfall"

    #: [alias] PyInstaller write-safe — identical steps to PROD_WRITE.
    #: [別名] PyInstaller 安全寫出 — 步驟與 PROD_WRITE 完全相同。
    EXE_WRITE_SAFE: "Waterfall"


# ------------------------------------------------------------------ #
#  Pre-built instances（預設實例賦值）                                 #
# ------------------------------------------------------------------ #

# ── Developer workstation / 開發機 ────────────────────────────────────────
#   最常見的開發情境：先找專案根，找不到退回當前工作目錄。
#   Most common dev scenario: try project root first, fall back to cwd.

Waterfall.DEV_STANDARD = Waterfall(
    PathMode.PROJ_ABSOLUTE,   # 1. 專案根 / project root
    PathMode.CWD,             # 2. 當前工作目錄 / current working directory
)

#   帶個人覆蓋的開發模式：允許 ~/.config/<app> 裡的設定覆蓋專案預設值，
#   適合存放個人 API key、本機資料庫 DSN 等不應版控的資訊。
#   Dev with personal override: USER_CONFIG can shadow project defaults.
#   Useful for local API keys, DB credentials that must not be committed.

Waterfall.DEV_WITH_USER_CONFIG = Waterfall(
    PathMode.USER_CONFIG,     # 1. 使用者設定目錄（可覆蓋）/ user config (can override)
    PathMode.PROJ_ABSOLUTE,   # 2. 專案根預設值 / project root default
    PathMode.CWD,             # 3. 工作目錄退路 / cwd fallback
)

# ── Production / deployed app / 部署後 ────────────────────────────────────
#   讀取：專案根 → exe 旁 → USER_CONFIG（三層覆蓋鏈）
#   Reading: project root → beside exe → user config (3-tier chain)

Waterfall.PROD_READ = Waterfall(
    PathMode.PROJ_ABSOLUTE,   # 1. 專案根 / project root
    PathMode.EXE_ABSOLUTE,    # 2. exe 旁（部署後常見位置）/ beside .exe
    PathMode.USER_CONFIG,     # 3. 使用者設定（最後機會）/ user config last chance
)

#   寫入：exe 旁（若可寫）→ 使用者資料目錄 → 系統 TEMP。
#   Writing: beside exe (if writable) → user data dir → system temp.

Waterfall.PROD_WRITE = Waterfall(
    PathMode.EXE_ABSOLUTE,    # 1. exe 旁（最理想，日誌/輸出放這）/ beside exe (ideal)
    PathMode.USER_DATA,       # 2. 使用者資料目錄 / user data directory
    PathMode.SYSTEM_TEMP,     # 3. 系統暫存（兜底）/ system temp (last resort)
)

# ── PyInstaller / frozen executable / 打包執行檔 ─────────────────────────
#
#   兩個 exe 相關 preset 設計上是互補的：
#   The two exe presets are intentionally complementary:
#
#   EXE_PREFER_BUNDLED : MEIPASS 優先 → 內嵌資源不可被外部檔案覆蓋。
#                        MEIPASS wins  → bundled data cannot be overridden externally.
#
#   EXE_OVERRIDE       : exe旁 優先 → 外部檔案可覆蓋內嵌預設資源。
#                        Beside-exe wins → external file can override bundled default.
#
#   選哪個取決於你是否希望讓使用者能在不重新編譯的情況下替換內嵌資源。
#   Choose based on whether users should be able to patch assets without recompiling.

Waterfall.EXE_PREFER_BUNDLED = Waterfall(
    PathMode.EXE_INNER,       # 1. MEIPASS（內嵌資源，不可被覆蓋）/ bundled, cannot override
    PathMode.EXE_ABSOLUTE,    # 2. exe 旁 / beside exe
    PathMode.PROJ_ABSOLUTE,   # 3. 專案根（開發時退路）/ project root (dev fallback)
)

Waterfall.EXE_OVERRIDE = Waterfall(
    PathMode.EXE_ABSOLUTE,    # 1. exe 旁（外部覆蓋優先）/ beside exe (external override wins)
    PathMode.USER_CONFIG,     # 2. 使用者設定（次要覆蓋）/ user config (secondary override)
    PathMode.EXE_INNER,       # 3. MEIPASS（內嵌預設值，最後退路）/ bundled default, last resort
)

# ── ETL pipelines / 批次管線 ──────────────────────────────────────────────

Waterfall.ETL_INPUT = Waterfall(
    PathMode.PROJ_ABSOLUTE,   # 1. 專案根（標準輸入位置）/ project root (standard input location)
    PathMode.CWD,             # 2. 工作目錄（暫時測試用）/ cwd (for quick tests)
    PathMode.SYSTEM_TEMP,     # 3. TEMP（staging 暫存區）/ system temp (staging area)
)

Waterfall.ETL_OUTPUT = Waterfall(
    PathMode.PROJ_ABSOLUTE,   # 1. 專案根 outputs/ / project root outputs/
    PathMode.USER_DATA,       # 2. 使用者資料目錄（備用）/ user data dir (fallback)
    PathMode.SYSTEM_TEMP,     # 3. 系統 TEMP（兜底，管線不中止）/ temp (pipeline never crashes)
)

# ── Maximum compatibility / 最高相容性 ────────────────────────────────────
#   依序嘗試所有六個定位點，適合跨環境的函式庫程式碼。
#   Tries all six anchors in a sensible order — for cross-environment library code.

Waterfall.UNIVERSAL = Waterfall(
    PathMode.EXE_INNER,       # 1. MEIPASS（只有 PyInstaller 環境有效）/ MEIPASS (PyInstaller only)
    PathMode.EXE_ABSOLUTE,    # 2. exe 旁 / beside exe
    PathMode.PROJ_ABSOLUTE,   # 3. 專案根 / project root
    PathMode.CWD,             # 4. 工作目錄 / cwd
    PathMode.USER_DATA,       # 5. 使用者資料目錄 / user data dir
    PathMode.SYSTEM_TEMP,     # 6. 系統 TEMP（兜底）/ system temp (last resort)
)

# ── Retired aliases / 退役別名 ────────────────────────────────────────────
#   步驟與對應的 active preset 完全相同，僅保留以維持向下相容性。
#   Steps are identical to the corresponding active preset; kept for back-compat only.
#   新程式碼請改用 ETL_INPUT / PROD_WRITE。
#   New code should use ETL_INPUT / PROD_WRITE directly.

Waterfall.CI_ARTIFACT  = Waterfall.ETL_INPUT    # alias: PROJ_ABSOLUTE → CWD → SYSTEM_TEMP
Waterfall.EXE_WRITE_SAFE = Waterfall.PROD_WRITE  # alias: EXE_ABSOLUTE → USER_DATA → SYSTEM_TEMP


# ------------------------------------------------------------------ #
#  PRESETS  ─  dict of ACTIVE (non-alias) presets                    #
#  僅包含功能各異的正規 preset；alias 請直接用 Waterfall.<alias>       #
# ------------------------------------------------------------------ #
#  用途 / Usage:
#    from isd_py_framework_sdk.path_manager import PRESETS
#    for name, wf in PRESETS.items():
#        path, trace = pm.get_with_trace("my_tag", wf)

PRESETS: dict[str, "Waterfall"] = {
    "DEV_STANDARD":         Waterfall.DEV_STANDARD,
    "DEV_WITH_USER_CONFIG": Waterfall.DEV_WITH_USER_CONFIG,
    "PROD_READ":            Waterfall.PROD_READ,
    "PROD_WRITE":           Waterfall.PROD_WRITE,
    "EXE_PREFER_BUNDLED":   Waterfall.EXE_PREFER_BUNDLED,
    "EXE_OVERRIDE":         Waterfall.EXE_OVERRIDE,
    "ETL_INPUT":            Waterfall.ETL_INPUT,
    "ETL_OUTPUT":           Waterfall.ETL_OUTPUT,
    "UNIVERSAL":            Waterfall.UNIVERSAL,
}

