# `path_manager` — 中心化路徑管理

消滅專案裡散落各處的 `../../data/...`、`os.path.join(Path(__file__).resolve().parent, ...)`、`os.path.join(os.getcwd(), ...)` 等。透過 `SingletonPathManager` 把所有常見路徑統一登記在一個地方；任何模組、任何使用者只需用 **tag** 查詢，不再自己計算。

## 安裝

無額外依賴，包含於核心套件：

```bash
pip install isd-py-framework-sdk
```

## 設計重點

| 功能 | 說明 |
|------|------|
| **Tag 登記制** | 每條路徑打上 `description`，三個月後也知道它的用途 |
| **環境感知** | 自動偵測 dev / PyInstaller；路徑 API 一致，底層自動切換 |
| **Waterfall** | 依序嘗試多個錨點，回傳第一個存在（或可寫）的路徑 |
| **衝突策略** | 寫入前自動偵測衝突，套用 suffix / timestamp 策略 |
| **可繼承接口** | 繼承 `IPathManager` 建立子專案專屬管理者 |

## `PathMode` — 路徑模式

| 值 | 語意 |
|----|------|
| `ABSOLUTE` | 完整 OS 絕對路徑 |
| `PROJ_RELATIVE` | 相對於 `proj_root` |
| `PROJ_ABSOLUTE` | 以 `proj_root` 為基底的絕對路徑 |
| `EXE_RELATIVE` | 相對於 exe 所在目錄 |
| `EXE_ABSOLUTE` | 以 exe 目錄為基底的絕對路徑 |
| `EXE_INNER` | PyInstaller 打包內部（`sys._MEIPASS`） |
| `SYSTEM_TEMP` | 系統暫存目錄 |
| `CWD` | 呼叫時的當前工作目錄 |
| `USER_HOME` / `USER_CONFIG` / `USER_DATA` / `USER_CACHE` | 跨平台 user 目錄 |
| `SCRIPT_DIR` | 入口腳本所在目錄 |
| `VIRTUAL_ENV` | venv 根目錄 |
| `PACKAGE_RESOURCE` | 套件內部資源 |

## `Waterfall` — fallback 鏈

```python
from isd_py_framework_sdk.path_manager import Waterfall, PathMode

# 自訂 waterfall：EXE 內部 → exe 旁邊 → 專案根目錄
wf = Waterfall(PathMode.EXE_INNER, PathMode.EXE_ABSOLUTE, PathMode.PROJ_ABSOLUTE)
path = pm.get("config", wf)
```

**Active presets — 各具不同功能的正規 preset（每個步驟都不重複）**

| Waterfall preset | 步驟（→ 優先順序） | 說明 |
|---|---|---|
| `DEV_STANDARD` | PROJ_ABSOLUTE → CWD | **讀取**。先看專案根目錄，找不到才退回 CWD。沒有 exe / user 資料夾感知，**不適合打包環境**；開發機日常讀取首選。 |
| `DEV_WITH_USER_CONFIG` | USER_CONFIG → PROJ_ABSOLUTE → CWD | **讀取**。`~/.config/<app>` 可蓋過版控中的專案預設值；最終退路是 CWD。適合**不應版控**的本機設定（API key、DB DSN），讓個人本機設定覆蓋 repo 裡的預設值。 |
| `PROD_READ` | PROJ_ABSOLUTE → EXE_ABSOLUTE → USER_CONFIG | **讀取**。安裝/部署目錄最優先，找不到再看 exe 旁邊的目錄，最後讀取使用者 AppData。允許系統管理員在 exe 旁放置**覆蓋設定**。部署後讀取靜態資源或設定檔的標準選擇。 |
| `PROD_WRITE` | EXE_ABSOLUTE → USER_DATA → SYSTEM_TEMP | **寫入**（需搭配 `ResolveIntent.WRITE`）。優先寫到 exe 旁邊；若安裝目錄唯讀（如 `Program Files`）則退到 AppData；兜底 TEMP 確保**永遠可以寫入**。部署後輸出 log 或報表的標準選擇。 |
| `EXE_PREFER_BUNDLED` | EXE_INNER (MEIPASS) → EXE_ABSOLUTE → PROJ_ABSOLUTE | **讀取**（PyInstaller — **唯讀資源模式**）。MEIPASS 內嵌資料永遠勝出；外部放同名檔案**也無法覆蓋**。適合 icon、字型、schema 等**不應被使用者替換**的靜態資源。 |
| `EXE_OVERRIDE` | EXE_ABSOLUTE → USER_CONFIG → EXE_INNER (MEIPASS) | **讀取**（PyInstaller — **可客製化設定模式**）。exe 旁邊或 AppData 的外部檔案可蓋過 `.exe` 內嵌的預設值；讓部署後**現場替換設定，不需重新編譯**。與 `EXE_PREFER_BUNDLED` 互補。 |
| `ETL_INPUT` | PROJ_ABSOLUTE → CWD → SYSTEM_TEMP | **讀取**。先找專案根 `data/inputs/`，退回 CWD，最後找 TEMP staging 區。**CI/CD 環境**中暫存於 TEMP 的輸入資料也能被找到，管線不因路徑問題中止。 |
| `ETL_OUTPUT` | PROJ_ABSOLUTE → USER_DATA → SYSTEM_TEMP | **寫入**（需搭配 `ResolveIntent.WRITE`）。先寫到 `data/outputs/`，退到 AppData，兜底 TEMP。**管線永遠能寫出結果**，不因輸出目錄不可寫而中止。 |
| `UNIVERSAL` | EXE_INNER → EXE_ABSOLUTE → PROJ_ABSOLUTE → CWD → USER_DATA → SYSTEM_TEMP | **讀取**。依序嘗試六個定位點；不論**開發機、部署環境、PyInstaller** 哪種情境都能找到路徑。適合函式庫程式碼或執行環境不確定的場景，以相容性換取明確性。 |

**Retired aliases — 步驟與上表重複，保留以維持向下相容，新程式碼請勿使用**

| alias | 等同 |
|---|---|
| `CI_ARTIFACT` | `ETL_INPUT` |
| `EXE_WRITE_SAFE` | `PROD_WRITE` |

> 以 `from isd_py_framework_sdk.path_manager import PRESETS` 可取得所有 active preset 的 `dict[str, Waterfall]`，方便程式迭代比對。

## 快速試用

```python
from isd_py_framework_sdk.path_manager import (
    SingletonPathManager, PathMode, Waterfall,
    IncrementSuffixStrategy,
)

pm = SingletonPathManager()

# 設定專案根目錄（只需在入口點呼叫一次）
pm.set_proj_root(__file__, levels_up=1)   # 從此 __file__ 往上 1 層

# 登記路徑（附說明，方便未來查閱）
pm.register("data_in",   "data/inputs",    description="原始資料輸入目錄")
pm.register("data_out",  "data/outputs",   description="輸出結果目錄")
pm.register("error_log", "logs/error.log", description="執行期錯誤日誌")
pm.register(
    "bundled_db",
    "assets/ref.db",
    anchor=PathMode.EXE_INNER,            # PyInstaller 打包內嵌
    description="打包內嵌參考資料庫",
)

# 從任何模組取得路徑（同一 singleton）
pm = SingletonPathManager()

path = pm.get("data_in")                          # → 絕對 Path
rel  = pm.get("data_in",  PathMode.PROJ_RELATIVE) # → 相對 Path
path = pm.get("config",   Waterfall.UNIVERSAL)    # → 第一個存在的 Path

pm.exists("data_in")                              # → bool（不拋例外）
pm.list_tags()                                    # → {tag: description}
print(pm.info())                                  # 格式化診斷字串
```

需要除錯時可改用 `get_with_trace()`，它不會 raise，並回傳每個 waterfall 步驟的 ✓/✗：

```python
path, trace = pm.get_with_trace("my_config", Waterfall.UNIVERSAL)
print(trace)
```

## Waterfall — PyInstaller 打包情境

```python
# 讀取：先嘗試 exe 內部 MEIPASS，再往外找 → 內嵌資源優先
path = pm.get("config_file", Waterfall.EXE_PREFER_BUNDLED)

# 覆蓋模式：先找 exe 旁邊目錄，再找 USER_CONFIG，最後才用內嵌 → 方便使用者替換預設設定
path = pm.get("config_file", Waterfall.EXE_OVERRIDE)

# 寫入：先嘗試 exe 旁邊，退回 USER_DATA，最後用系統暫存
write_path = pm.get("result_xlsx", Waterfall.PROD_WRITE)
```

## 環境切換（anchor remap）

一般情況下，從開發機搬到 PyInstaller 打包環境後，每個 `register()` 的 anchor 都得從 `PROJ_ABSOLUTE` 改成 `EXE_INNER`。`remap_anchor()` 讓你在**不修改任何 `register()` 呼叫**的情況下完成切換。

### 寫在哪裡？

`remap_anchor()` 必須寫在 **`main.py` 的模組頂端**（`import` 之後、第一個 `pm.get()` 之前），**不是**寫在 `if __name__ == "__main__":` 裡面。

> `if __name__ == "__main__":` 的作用是阻止這段程式碼在被 `import` 時執行；而 remap 必須在任何模組呼叫 `pm.get()` 之前生效——包含模組頂層的初始化程式碼。因為 `pm` 是 singleton，在 `main.py` 頂端設定一次就全域有效。

```python
# main.py  ← 整個應用程式的唯一入口點
import sys

from isd_py_framework_sdk.path_manager import SingletonPathManager, PathMode

# ① 取得 singleton，設定專案根與 app 名稱
pm = SingletonPathManager()
pm.set_proj_root(__file__, levels_up=1)   # main.py 在 src/ 下，往上一層是專案根
pm.set_app_name("MyApp")

# ② 如果在 PyInstaller 打包的 .exe 裡，把 PROJ_ABSOLUTE 重導到 MEIPASS
#    這一行是「開發 ↔ 打包」切換的唯一改動點
if getattr(sys, 'frozen', False):
    pm.remap_anchor(PathMode.PROJ_ABSOLUTE, PathMode.EXE_INNER)

# ③ 其他所有模組的 register() 完全不需要動，照開發時的寫法即可
#    （這些呼叫通常散落在各個模組的頂端，不一定在 main.py 裡）
pm.register("icon",    "assets/icon.png",        PathMode.PROJ_ABSOLUTE)
pm.register("schema",  "config/schema.json",     PathMode.PROJ_ABSOLUTE)
pm.register("report",  "outputs/report.xlsx",    PathMode.PROJ_ABSOLUTE)

# ── 之後任何地方呼叫 pm.get() ──────────────────────────────────────────
icon_path = pm.get("icon")
# 開發機（非 frozen）：<proj_root>/assets/icon.png
# 打包後（frozen）：   sys._MEIPASS/assets/icon.png


def main():
    # 應用程式主邏輯
    ...


if __name__ == "__main__":
    main()
```

### 確保開發到打包都能正常運作

`remap_anchor()` 解決的是**路徑解析**的問題。整個流程能 work 的前提還有：

1. **PyInstaller 要知道哪些檔案要打包進去** — 路徑管理器負責找路徑，但它無法替你告訴 PyInstaller「這個 `assets/` 資料夾要放進 MEIPASS」。你仍需要在 `.spec` 或命令列加：
   ```
   --add-data "assets;assets"      # Windows
   --add-data "assets:assets"      # macOS / Linux
   ```
2. **`set_proj_root()` 在 frozen 環境下仍可呼叫**，但因為 `PROJ_ABSOLUTE` 已被 remap 到 `EXE_INNER`，`_proj_root` 的值此時不再被用到，呼叫它不會造成問題。
3. **有些路徑不應該被 remap**（例如輸出報表、log 檔）：將這些寫入路徑的 anchor 改用 `PROD_WRITE` 相關的 PathMode（`EXE_ABSOLUTE` 或 `USER_DATA`），或直接用 `PathMode.ABSOLUTE` 傳入完整絕對路徑，`remap_anchor()` 不影響 `ABSOLUTE` anchor。

### Waterfall 也受 remap 影響

anchor remap 在底層的 `_apply_anchor()` 套用，waterfall 的每一步都經過它，所以 `DEV_STANDARD`（PROJ → CWD）的第一步在 `PROJ_ABSOLUTE → EXE_INNER` remap 生效後，會自動嘗試 `EXE_INNER` 而非 `PROJ_ABSOLUTE`，**不需要另外為 Waterfall 設定 remap**。

### 方法速查

| 方法 | 說明 |
|---|---|
| `pm.remap_anchor(from, to)` | 讓所有以 `from` 為 anchor 的 tag 改用 `to` 解析。重複呼叫會覆蓋前一個設定。 |
| `pm.remove_anchor_remap(from)` | 移除指定 anchor 的 remap，恢復原始行為。不存在時不報錯。 |
| `pm.clear_anchor_remaps()` | 移除全部 remap。 |

> 目前已設定的 remap 會顯示在 `pm.info()` 的 `Anchor remaps` 區段，方便除錯。

## 存檔衝突處理（`ConflictStrategy`）

在寫入輸出前呼叫，避免靜默覆蓋舊資料：

```python
from isd_py_framework_sdk.path_manager import (
    SingletonPathManager, IncrementSuffixStrategy, TimestampSuffixStrategy,
)

pm = SingletonPathManager()
pm.register("report", "outputs/report.xlsx", description="週報")

# 若目標已存在，自動加 _001 / _002 … suffix
safe_path = pm.resolve_conflict("report")
# [CONFLICT] 'outputs/report.xlsx' already exists → redirecting write to 'outputs/report_001.xlsx'

# 或指定策略
safe_path = pm.resolve_conflict("report", strategy=TimestampSuffixStrategy())
# → outputs/report_20260422_153012.xlsx
```

| 策略 | 行為 |
|---|---|
| `OverwriteStrategy` | 靜默覆寫 |
| `SkipIfExistsStrategy` | 已存在則跳過 |
| `TimestampSuffixStrategy` | 附加 `_YYYYMMDD_HHMMSS` |
| `IncrementSuffixStrategy` | 附加 `_001`, `_002`, … |

## 自訂管理者（繼承 `IPathManager`）

```python
from isd_py_framework_sdk.path_manager import IPathManager

class MyProjectPathManager(IPathManager, ...):
    """子專案路徑管理者，與頂層 SingletonPathManager 共用接口。"""
    ...
```

## 多進程注意事項

每個 OS 進程（`multiprocessing` fork/spawn）有獨立的 singleton 實例。若需要在子進程使用相同的路徑配置，必須在每個子進程中重新執行 `pm.set_proj_root()` 和 `pm.register()`，或等待未來實作的 `to_dict()`/`from_dict()` 序列化（詳見 `dev_plan.md` §6 — 套件規劃文件）。執行緒（`threading`）共享同一進程記憶體，singleton 自然共享，無需額外處理。

## 測試

```powershell
.venv\Scripts\python.exe -m pytest -v tests/path/test_path_manager.py
```

---

開發/架構細節（內部模組拆分、`SingletonABCMeta` 設計）請見 [agent.md](agent.md)；套件規劃與未完成項目見 [dev_plan.md](dev_plan.md)。
