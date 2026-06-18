# agent.md — `path_manager` 套件

## 職責

提供集中式、環境感知的路徑管理。解決大型 Python 專案中路徑分散、相對路徑脆弱、跨部署環境（開發 / PyInstaller 打包 / CI）路徑語意不一致的問題。

核心概念：**在程式入口一次性 `register(tag, path)`，之後任何模組都能 `get(tag)` 取得一致的路徑。**

---

## 架構

```
path_manager/
├── __init__.py                    公開 API 匯出
├── interface.py                   IPathManager（ABC，供繼承建立專案專用 manager）
├── singleton_path_manager.py      SingletonPathManager（主實作，thread-safe singleton）
├── _enums.py                      PathMode（所有路徑錨點 enum）
├── _waterfall.py                  Waterfall, ResolveIntent, WaterfallTrace, Attempt, PRESETS
├── _conflict.py                   ConflictStrategy + 四個內建策略
├── _registry.py                   PathEntry + PathRegistry（內部 dict 結構）
├── _resolver.py                   EnvironmentResolver（靜態環境偵測）
├── _meta.py                       SingletonABCMeta（解決 ABC + singleton metaclass 衝突）
├── dev_plan.md                    設計文件與進度追蹤（開發內部文件）
├── InnoRankingDataGeneration.py   舊版 legacy（保留作參考，非公開 API）
└── _tester/                       內部 GUI 測試工具（非公開 API）
```

---

## 核心元件

### `SingletonPathManager`

實作 `IPathManager` ABC，以 `SingletonABCMeta` 確保 thread-safe singleton 與 ABC 可以共存。

```python
from isd_py_framework_sdk.path_manager import SingletonPathManager, PathMode, Waterfall

pm = SingletonPathManager()

# 啟動時設定一次
pm.set_proj_root(__file__, levels_up=1)       # 從 main.py 往上 1 層為 proj root
pm.register("data_in", "data/inputs",  description="Raw CSV inputs")
pm.register("data_out", "data/outputs", description="Generated outputs")
pm.register("error_log", "logs/error.log")

# 在任何模組中取用
pm = SingletonPathManager()                    # 同一實例
path = pm.get("data_in")                       # → absolute Path
rel  = pm.get("data_in", PathMode.PROJ_RELATIVE)  # → 相對路徑
```

---

### `PathMode`（路徑錨點 enum）

控制 `register()` 時路徑的基準點（anchor），以及 `get()` 時的回傳格式：

| 分組 | 枚舉成員 | 說明 |
|---|---|---|
| Passthrough | `ABSOLUTE` | 完整絕對路徑 |
| Project scope | `PROJ_RELATIVE`, `PROJ_ABSOLUTE` | 以 `set_proj_root()` 設定的根為基準 |
| Exe/Deployment | `EXE_RELATIVE`, `EXE_ABSOLUTE`, `EXE_INNER` | PyInstaller 打包環境 |
| System | `SYSTEM_TEMP` | `tempfile.gettempdir()` |
| User | `USER_HOME`, `USER_CONFIG`, `USER_DATA`, `USER_CACHE` | 跨平台 user 目錄 |
| Runtime | `CWD`, `SCRIPT_DIR` | 當前工作目錄 / 入口腳本目錄 |
| Dev tooling | `VIRTUAL_ENV`, `PACKAGE_RESOURCE` | venv 根 / 套件內部資源 |

---

### `Waterfall`（有序回退鏈）

一條有順序的 `PathMode` 序列；`get(tag, waterfall)` 依序嘗試每個 mode，回傳第一個滿足驗證條件的路徑（READ: 路徑存在；WRITE: 最近祖先可寫）。

```python
path = pm.get("config", Waterfall.DEV_STANDARD)   # PROJ → CWD
path = pm.get("output", Waterfall.PROD_WRITE, intent=ResolveIntent.WRITE)

# 自訂 waterfall
wf = Waterfall(PathMode.EXE_INNER, PathMode.EXE_ABSOLUTE, PathMode.PROJ_ABSOLUTE)
path = pm.get("my_config", wf)

# 取得 trace（不 raise，供除錯）
path, trace = pm.get_with_trace("my_config", wf)
print(trace)   # 印出每步驟的 ✓/✗
```

**內建預設 Waterfall（`PRESETS`，共 9 個 active preset，定義在 `_waterfall.py`）：**

| 常數 | 步驟順序 | 適用情境 |
|---|---|---|
| `DEV_STANDARD` | PROJ → CWD | 開發環境讀取 |
| `DEV_WITH_USER_CONFIG` | USER_CFG → PROJ → CWD | 開發 + 本機覆蓋設定 |
| `PROD_READ` | PROJ → EXE → USER_CFG | 生產環境讀取 |
| `PROD_WRITE` | EXE → USER_DATA → TEMP | 生產環境寫入（避免 Program Files 唯讀）|
| `EXE_PREFER_BUNDLED` | EXE_INNER(MEIPASS) → EXE → PROJ | PyInstaller 唯讀資源（icon/字型/schema），MEIPASS 永遠勝出，外部檔案無法覆蓋 |
| `EXE_OVERRIDE` | EXE → USER_CFG → EXE_INNER(MEIPASS) | PyInstaller 可客製化設定，外部檔案可覆蓋內嵌預設值 |
| `ETL_INPUT` | PROJ → CWD → TEMP | 找輸入資料；CI/CD 暫存於 TEMP 的輸入也能找到 |
| `ETL_OUTPUT` | PROJ → USER_DATA → TEMP | 寫輸出；管線永遠能寫出結果 |
| `UNIVERSAL` | EXE_INNER → EXE → PROJ → CWD → USER_DATA → TEMP | 全部 6 個錨點依序兜底 |

**Retired aliases（向下相容，新程式碼勿用）：** `CI_ARTIFACT` = `ETL_INPUT`；`EXE_WRITE_SAFE` = `PROD_WRITE`。

完整 preset 設計理由（每個 preset 為何選這個順序）見 [README.md](README.md)。

---

### `remap_anchor()` — 開發/打包環境一鍵切換

`SingletonPathManager.remap_anchor(from_mode, to_mode)`（`singleton_path_manager.py`）讓所有以 `from_mode` 為 anchor 登記的 tag，在底層 `_apply_anchor()` 解析時改用 `to_mode`，**不需要修改任何既有的 `register()` 呼叫**。典型用法：在 `main.py` 模組頂層（非 `if __name__ == "__main__":` 內）依 `sys.frozen` 判斷是否打包，呼叫 `pm.remap_anchor(PathMode.PROJ_ABSOLUTE, PathMode.EXE_INNER)`。

- `remove_anchor_remap(from_mode)` — 移除單一 remap。
- `clear_anchor_remaps()` — 清空全部 remap。
- Waterfall 的每一步都會經過 `_apply_anchor()`，因此 remap 對 Waterfall preset 同樣生效，不需要額外設定。
- `pm.info()` 會列出目前生效的 `Anchor remaps`，是排查「路徑跑錯地方」的第一個檢查點。

其他公開方法：`pm.exists(tag)`（不拋例外的存在檢查）、`pm.list_tags()`（回傳 `{tag: description}`）、`pm.set_app_name(name)`（影響 `USER_*` 系列錨點的子目錄名稱）。完整流程範例見 [README.md](README.md) 的「環境切換（anchor remap）」章節。

---

### ConflictStrategy（衝突處理策略）

在寫入輸出前呼叫，避免靜默覆蓋舊資料：

```python
from isd_py_framework_sdk.path_manager import IncrementSuffixStrategy

strategy = IncrementSuffixStrategy()
safe_path = pm.resolve_conflict("output_excel", strategy)
# 若 output.xlsx 已存在 → output_001.xlsx, output_002.xlsx ...
```

| 策略 | 行為 |
|---|---|
| `OverwriteStrategy` | 靜默覆寫 |
| `SkipIfExistsStrategy` | 已存在則跳過 |
| `TimestampSuffixStrategy` | 附加 `_YYYYMMDD_HHMMSS` |
| `IncrementSuffixStrategy` | 附加 `_001`, `_002`, … |

---

### `EnvironmentResolver`

靜態工具類，提供各 `PathMode` 對應的目錄解析邏輯（`PathMode.USER_CONFIG` → `~/.config` / `%APPDATA%`…）。通常不直接使用，由 `SingletonPathManager` 內部呼叫。

---

## 進入點與 Import

```python
from isd_py_framework_sdk.path_manager import (
    SingletonPathManager,
    IPathManager,
    PathMode,
    Waterfall,
    PRESETS,
    ResolveIntent,
    WaterfallTrace,
    ConflictStrategy,
    OverwriteStrategy,
    SkipIfExistsStrategy,
    TimestampSuffixStrategy,
    IncrementSuffixStrategy,
    PathEntry,
    EnvironmentResolver,
)
```

---

## 測試

```powershell
.venv\Scripts\python.exe -m pytest -v tests/path/test_path_manager.py
```

---

## 多進程注意事項

每個 OS 進程（`multiprocessing` fork/spawn）有獨立的 singleton 實例。若需要在子進程使用相同的路徑配置，必須在每個子進程中重新執行 `pm.set_proj_root()` 和 `pm.register()`，或等待未來實作的 `to_dict()`/`from_dict()` 序列化（見 `dev_plan.md` §6）。

執行緒（`threading`）共享同一進程記憶體，singleton 自然共享，無需額外處理。

---

## 常見陷阱

- `pm.get(tag, PathMode.PROJ_RELATIVE)` 在未呼叫 `set_proj_root()` 之前會拋出錯誤。
- `PathMode.EXE_INNER` 在非 PyInstaller 打包環境下呼叫會 `RuntimeError`。
- `PathMode.VIRTUAL_ENV` 在未啟動 venv 時會 `RuntimeError`（讀取 `VIRTUAL_ENV` 環境變數）。
- Waterfall 所有步驟都失敗時拋出 `FileNotFoundError`，並附上完整的 `WaterfallTrace`——trace 是除錯利器，不要忽略它。
- `InnoRankingDataGeneration.py` 是舊版 legacy 實作，不屬於公開 API，保留作歷史參考。
