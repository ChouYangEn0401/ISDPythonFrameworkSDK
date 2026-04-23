# path_manager — Development Plan & Progress

> 最後更新：2026-04-22（v2 — 加入 intent, trace, USER_* modes）

---

## 背景 & 動機

### 問題的根源
在中大型 Python 專案裡，「路徑」是最不起眼卻最容易積累技術債的部分。每當有新成員加入，或者三個月後你回頭看自己的 code，你幾乎必然會看到：

```python
# 常見的亂象
os.path.join(Path(__file__).resolve().parent, "..", "..", "data", "inputs")
pd.read_excel(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../result.xlsx"))
```

這些路徑寫法導致幾個問題：
1. **不一致**：不同模組對同一個實體位置有不同的相對路徑表達
2. **缺乏說明**：沒有人知道這個路徑是幹什麼用的，也沒有人知道是誰建的
3. **部署脆弱**：開發環境、打包部署（PyInstaller）、CI 三個環境下路徑語意完全不同
4. **多進程混亂**：subprocess / multiprocessing 啟動後，各自算出的路徑可能不一致
5. **輸出檔無管理**：log、result.xlsx、error_output.csv 散落四處，命名無規律，衝突時直接覆蓋

### 這個模組想解決什麼
`SingletonPathManager` 是一個「全域路徑登記處」：

- **一次登記**：在程式入口把所有要用的路徑登記好，附上說明
- **到處查閱**：任何模組只要 `pm.get("tag")` 就能取得一致的路徑，不再自己算
- **環境感知**：底層自動偵測 dev / PyInstaller / venv 等環境，使用者只用 tag
- **waterfall 策略**：一行設定就能表達「先找 exe 內部，找不到就找 exe 旁邊，還找不到再用 tmp」
- **衝突安全**：寫入前先問一聲 `resolve_conflict()`，不再靜默蓋掉舊資料

---

## 模組結構

```
path_manager/
├── dev_plan.md                  ← 此檔（進度追蹤、設計思考）
├── __init__.py                  ← 公開 API 匯出
├── _enums.py                    ← PathMode（所有路徑錨點）
├── _resolver.py                 ← EnvironmentResolver（環境偵測 + 目錄解析）
├── _waterfall.py                ← Waterfall + ResolveIntent + WaterfallTrace
├── _conflict.py                 ← ConflictStrategy + 內建策略
├── _registry.py                 ← PathEntry + PathRegistry（內部 dict）
├── _meta.py                     ← SingletonABCMeta（解決 ABC + singleton 衝突）
├── interface.py                 ← IPathManager（ABC，供繼承）
├── singleton_path_manager.py   ← SingletonPathManager（主實作）
└── InnoRankingDataGeneration.py ← 舊版（legacy，保留作參考）
```

---

## 需求對應

| # | 需求 | 狀態 | 對應元件 |
|---|------|------|----------|
| 1 | 消滅 `../../..` 相對路徑寫法 | ✅ | `set_proj_root(__file__, levels_up=N)` |
| 2 | 所有模組對同一路徑描述一致 | ✅ | `register(tag, ...)` + `get(tag)` |
| 3 | 測試/臨時檔有說明 & 統一管理 | ✅ | `description=` 欄位 + `list_tags()` |
| 4 | log/結果檔出現在可預測位置 | ✅ | `get(tag, PathMode.PROJ_ABSOLUTE)` |
| 5 | PyInstaller 打包後的 waterfall 策略 | ✅ | `get(tag, Waterfall.EXE_PREFER_BUNDLED)` |
| 6 | multitasking（thread / process）支援 | ⏳ | Thread 已支援；process 見保留項目 §6 |
| 7 | 存檔衝突機制（覆蓋 / 遞增 suffix） | ✅ | `resolve_conflict()` + `ConflictStrategy` |
| 8 | interface + simple singleton 供參考繼承 | ✅ | `IPathManager` + `SingletonPathManager` |
| 9 | 衝突時顯示資訊 + 新名稱 + 策略模板 | ✅ | `ConflictStrategy.conflict_info()` |
| 10 | READ vs WRITE 語意區分 | ✅ | `ResolveIntent` + `Waterfall(intent=...)` |
| 11 | 除錯：查看每次 waterfall 嘗試紀錄 | ✅ | `WaterfallTrace` + `get_with_trace()` |
| 12 | User 目錄（config / data / cache / home）| ✅ | `PathMode.USER_*` + `EnvironmentResolver` |
| 13 | 開發工具環境（venv、package resources）| ✅ | `PathMode.VIRTUAL_ENV / PACKAGE_RESOURCE` |

---

## 核心概念

### PathMode — 路徑錨點

| 群組 | 值 | 語意 |
|------|----|------|
| Passthrough | `ABSOLUTE` | 完整 OS 絕對路徑 |
| Project | `PROJ_RELATIVE` | 相對於 `proj_root` |
| Project | `PROJ_ABSOLUTE` | 以 `proj_root` 為基底的絕對路徑 |
| Executable | `EXE_RELATIVE` | 相對於 exe/腳本所在目錄 |
| Executable | `EXE_ABSOLUTE` | 以 exe 目錄為基底的絕對路徑 |
| Executable | `EXE_INNER` | PyInstaller `sys._MEIPASS` 內部 |
| System | `SYSTEM_TEMP` | 系統暫存目錄 |
| User | `USER_HOME` | `Path.home()` |
| User | `USER_CONFIG` | `~/.config/<app>` / `%APPDATA%` |
| User | `USER_DATA` | `~/.local/share/<app>` / `%APPDATA%` |
| User | `USER_CACHE` | `~/.cache/<app>` / `%LOCALAPPDATA%` |
| Runtime | `CWD` | 呼叫時的 `Path.cwd()` |
| Runtime | `SCRIPT_DIR` | `sys.argv[0]` 的父目錄 |
| DevTools | `VIRTUAL_ENV` | 當前 venv 根目錄 |
| DevTools | `PACKAGE_RESOURCE` | `importlib.resources` 套件資源 |

### ResolveIntent

| 值 | 效果 |
|----|------|
| `READ` (預設) | 候選路徑必須**存在**才視為成功 |
| `WRITE` | 候選路徑的**父目錄**存在且可寫就視為成功（檔案本身可以不存在）|

### Waterfall — fallback 鏈

```python
wf = Waterfall(PathMode.EXE_INNER, PathMode.EXE_ABSOLUTE, PathMode.PROJ_ABSOLUTE)
path = pm.get("config", wf)                          # READ intent（預設）
path = pm.get("output", wf, intent=ResolveIntent.WRITE)  # WRITE intent

# 除錯：不拋出例外，回傳 WaterfallTrace
path, trace = pm.get_with_trace("config", wf)
print(trace)   # 顯示每個步驟的結果
```

### 內建 Waterfall 預設

| 常數 | 步驟 | 設計場景 |
|------|------|----------|
| `DEV_STANDARD` | PROJ_ABSOLUTE → CWD | 日常開發讀取 |
| `DEV_WITH_USER_CONFIG` | USER_CONFIG → PROJ_ABSOLUTE → CWD | 允許個人設定覆蓋的開發工具 |
| `PROD_READ` | PROJ_ABSOLUTE → EXE_ABSOLUTE → USER_CONFIG | 部署後讀取設定 / 資產 |
| `PROD_WRITE` | EXE_ABSOLUTE → USER_DATA → SYSTEM_TEMP | 部署後寫入 log / 輸出 |
| `EXE_PREFER_BUNDLED` | EXE_INNER → EXE_ABSOLUTE → PROJ_ABSOLUTE | PyInstaller 優先讀取打包資料 |
| `EXE_WRITE_SAFE` | EXE_ABSOLUTE → USER_DATA → SYSTEM_TEMP | PyInstaller 安全寫入 |
| `ETL_INPUT` | PROJ_ABSOLUTE → CWD → SYSTEM_TEMP | ETL pipeline 找輸入檔 |
| `ETL_OUTPUT` | PROJ_ABSOLUTE → USER_DATA → SYSTEM_TEMP | ETL pipeline 寫輸出，不怕崩潰 |
| `CI_ARTIFACT` | PROJ_ABSOLUTE → CWD → SYSTEM_TEMP | CI 環境 artefact |
| `UNIVERSAL` | EXE_INNER → EXE_ABSOLUTE → PROJ_ABSOLUTE → CWD → USER_DATA → SYSTEM_TEMP | 最高相容性 |

---

## API 速覽

```python
from isd_py_framework_sdk.path_manager import (
    SingletonPathManager, PathMode, Waterfall, ResolveIntent,
    IncrementSuffixStrategy,
)

pm = SingletonPathManager()

# 一次設定（通常在 main.py / app.py）
pm.set_proj_root(__file__, levels_up=2)  # 從本檔往上 2 層
pm.set_app_name("MyApp")                 # 影響 USER_* 目錄名稱

# 路徑登記（附說明）
pm.register("data_in",    "data/inputs",      description="原始資料目錄")
pm.register("data_out",   "data/outputs",     description="輸出結果目錄")
pm.register("error_log",  "logs/error.log",   description="執行期錯誤日誌")
pm.register("bundled_db", "assets/ref.db",    anchor=PathMode.EXE_INNER,
                                               description="打包內嵌資料庫")

# 取得路徑
pm.get("data_in")                                   # 絕對路徑
pm.get("data_in", PathMode.PROJ_RELATIVE)           # 相對路徑
pm.get("config",  Waterfall.UNIVERSAL)              # waterfall READ
pm.get("report",  Waterfall.ETL_OUTPUT,             # waterfall WRITE
       intent=ResolveIntent.WRITE)

# 工具
pm.exists("data_in")                                # bool，不拋例外
pm.list_tags()                                      # {tag: description}
print(pm.info())                                    # 完整診斷字串

# 衝突安全寫入
safe = pm.resolve_conflict("report")               # 自動加 _001 suffix
safe = pm.resolve_conflict("report",
        strategy=IncrementSuffixStrategy())

# 除錯
path, trace = pm.get_with_trace("config", Waterfall.PROD_READ)
print(trace)   # 每個 waterfall 步驟的 ✓/✗ 詳情
```

---

## 進度追蹤

| 檔案 | 狀態 |
|------|------|
| `dev_plan.md` | ✅ |
| `_enums.py` | ✅ (v2 — USER_*, SCRIPT_DIR, VIRTUAL_ENV, PACKAGE_RESOURCE) |
| `_resolver.py` | ✅ (v2 — user dir 解析、venv、script_dir) |
| `_waterfall.py` | ✅ (v2 — ResolveIntent, WaterfallTrace, Attempt, 10 個 presets) |
| `_conflict.py` | ✅ |
| `_registry.py` | ✅ |
| `_meta.py` | ✅ |
| `interface.py` | ✅ (v2 — intent param, get_with_trace) |
| `singleton_path_manager.py` | ✅ (v2 — 全 PathMode 支援, get_with_trace) |
| `__init__.py` | ✅ |
| `tests/path/test_path_manager.py` | ✅ (71 tests, all green) |
| `README.md` | ✅ |

---

## 保留項目（未來版本）

### §6 — 多進程協調
- **Thread**：共享記憶體，singleton 天然適用，目前已支援
- **Process**（`multiprocessing` / `start-process`）：
  - 各 process 有獨立的 singleton 實例
  - 計畫：`pm.to_dict()` 序列化 → 子 process `pm.from_dict()` 還原
  - 進階：`multiprocessing.Manager().dict()` 作跨 process 後端
  - **狀態：待 v0.4**

### §7 — ConflictManager（full orchestration）
- 整合 registry + strategy + 實際寫入呼叫（目前 resolve_conflict 只計算路徑）
- `AppendModeStrategy`
- **狀態：骨架已建，待 v0.4**

### §8 — 子專案 / MultiManager 拓撲
- 多個繼承 `IPathManager` 的 class，由上層 orchestrator 統一協調
- 跨子專案路徑互查
- **狀態：待 v0.5**


---

## 背景 & 動機

大型專案中，路徑管理是最常見的「看起來簡單、實際又亂」的問題：

- 每個模組自己算相對路徑（`../../data`）、(`os.path.join(Path(__file__).resolve().parent, ...)`)、(`os.path.join(os.getcwd(), ...)`) 等，彼此不一致
- PyInstaller 打包後路徑語意完全改變（`sys._MEIPASS`）
- 測試檔、log 檔、結果檔沒有統一規範，三個月後沒人知道是誰的，也沒人知道在幹嘛
- mvp 或者實驗部屬中，會需要大量測試文件時，一個禮拜以後就會被雜亂無章的序列名稱搞混，全不也都缺乏註釋與管理
- 多進程啟動時，各自對同一路徑有不同理解

本模組的目標：**提供一個中心化、環境感知的路徑管理接口**，讓所有模組透過「tag」查詢路徑，不再自己算。

---

## 模組結構（目標）

```
path_manager/
├── dev_plan.md                  ← 此檔（進度追蹤、想法陳述）
├── __init__.py                  ← 公開 API 匯出
├── _enums.py                    ← PathMode enum
├── _resolver.py                 ← EnvironmentResolver（環境偵測 + anchor 計算）
├── _waterfall.py                ← Waterfall（fallback 鏈）
├── _conflict.py                 ← ConflictStrategy + 內建策略（§7 保留）
├── _registry.py                 ← PathEntry + PathRegistry（內部 registry）
├── interface.py                 ← IPathManager（ABC）
├── singleton_path_manager.py   ← SingletonPathManager（主實作）
└── InnoRankingDataGeneration.py ← 舊版（保留，legacy）
```

---

## 需求對應

| # | 需求 | 狀態 | 對應元件 |
|---|------|------|----------|
| 1 | 消滅 `../../..` 的相對路徑寫法 | ✅ | `set_proj_root().__file__, levels_up=N)` |
| 2 | 所有模組對同一路徑描述一致 | ✅ | `register(tag, ...)` + `get(tag)` |
| 3 | 測試/臨時檔有說明 & 統一管理 | ✅ | `description=` 欄位 + `list_tags()` |
| 4 | log/結果檔出現在可預測位置 | ✅ | `get(tag, PathMode.PROJ_ABSOLUTE)` |
| 5 | PyInstaller 打包後的 waterfall 策略 | ✅ | `get(tag, Waterfall(...))` |
| 6 | multitasking（thread / process）支援 | ⏳ | 見下方「多進程說明」 |
| 7 | 存檔衝突機制（覆蓋 / 遞增 suffix） | ⏸ | `_conflict.py` 已骨架，`resolve_conflict()` 保留 |
| 8 | interface + simple singleton 供參考繼承 | ✅ | `IPathManager` + `SingletonPathManager` |
| 9 | 衝突時顯示資訊 + 新名稱 + 策略模板 | ✅ | `ConflictStrategy.conflict_info()` |

---

## 核心概念

### PathMode（路徑模式）

| 值 | 語意 |
|----|------|
| `ABSOLUTE` | 完整 OS 絕對路徑 |
| `PROJ_RELATIVE` | 相對於 `proj_root` |
| `PROJ_ABSOLUTE` | 以 `proj_root` 為基底的絕對路徑 |
| `EXE_RELATIVE` | 相對於 exe 所在目錄 |
| `EXE_ABSOLUTE` | 以 exe 目錄為基底的絕對路徑 |
| `EXE_INNER` | PyInstaller 打包內部（`sys._MEIPASS`） |
| `SYSTEM_TEMP` | 系統暫存目錄 |
| `CWD` | 呼叫時的 `os.getcwd()` |

### Waterfall（fallback 鏈）

```
Waterfall(PathMode.EXE_INNER, PathMode.EXE_ABSOLUTE, PathMode.PROJ_ABSOLUTE)
```

- `get(tag, waterfall)` → 依序嘗試，回傳第一個**存在**的路徑
- 若全部都不存在 → 拋出 `FileNotFoundError`（含詳細診斷）

### 內建 Waterfall 預設

| 名稱 | 步驟 | 適合場景 |
|------|------|----------|
| `Waterfall.EXE_PREFER_BUNDLED` | EXE_INNER → EXE_ABSOLUTE → PROJ_ABSOLUTE | 打包後優先讀取 bundle 資料 |
| `Waterfall.DEV_STANDARD` | PROJ_ABSOLUTE → ABSOLUTE → CWD | 開發期間標準讀取 |
| `Waterfall.EXE_WRITE_SAFE` | EXE_ABSOLUTE → SYSTEM_TEMP | 寫入時優先放在 exe 旁，失敗用暫存 |
| `Waterfall.UNIVERSAL` | EXE_INNER → EXE_ABSOLUTE → PROJ_ABSOLUTE → CWD → SYSTEM_TEMP | 通用最大相容 |

---

## API 速覽

```python
from isd_py_framework_sdk.path_manager import SingletonPathManager, PathMode, Waterfall

pm = SingletonPathManager()

# 設定專案根目錄（只需呼叫一次）
pm.set_proj_root(__file__, levels_up=2)  # 從此 __file__ 往上 2 層

# 註冊路徑（帶說明）
pm.register("data_in",   "data/inputs",       description="原始資料輸入目錄")
pm.register("data_out",  "data/outputs",       description="輸出結果目錄")
pm.register("error_log", "logs/error.log",     description="執行期錯誤日誌")
pm.register("bundled_db","assets/ref.db",      anchor=PathMode.EXE_INNER, description="打包內嵌資料庫")

# 依模式取得路徑
pm.get("data_in")                             # → Path（絕對）
pm.get("data_in", PathMode.PROJ_RELATIVE)     # → Path（相對 proj_root）
pm.get("data_in", Waterfall.UNIVERSAL)        # → Path（第一個存在的）

# 輔助工具
pm.exists("data_in")                          # → bool
pm.list_tags()                                # → {tag: description}
pm.info()                                     # → 格式化診斷字串

# 存檔衝突（骨架，§7）
safe_path = pm.resolve_conflict("data_out")   # 若目標已存在則自動加 suffix
```

---

## 進度追蹤

| 檔案 | 狀態 |
|------|------|
| `dev_plan.md` | ✅ |
| `_enums.py` | ✅ |
| `_resolver.py` | ✅ |
| `_waterfall.py` | ✅ |
| `_conflict.py` | ✅ |
| `_registry.py` | ✅ |
| `interface.py` | ✅ |
| `singleton_path_manager.py` | ✅ |
| `__init__.py` (更新) | ✅ |
| `README.md` (更新) | ✅ |

---

## 保留項目（§7 — 未來擴展）

### 多進程協調
- **Thread**：共享記憶體，singleton 天然適用，目前已支援
- **Process**（`multiprocessing` / `start-process`）：各 process 有獨立的 singleton 實例
  - 建議：在主 process 呼叫 `pm.to_dict()` 序列化，子 process 呼叫 `pm.from_dict()` 還原
  - 或：改以 `SharedMemory` / `Manager().dict()` 作跨 process 後端
  - **狀態：保留，待 v0.4 設計**

### 寫入衝突 full orchestration
- `ConflictManager` 整合 registry + strategy + 實際寫入呼叫
- `AppendModeStrategy`
- **狀態：骨架已建，待 v0.4 補全**

### 子專案 / MultiManager 拓撲
- 多個繼承 `IPathManager` 的 class，由上層 orchestrator 統一協調
- 跨子專案路徑互查
- **狀態：待 v0.5 設計**
