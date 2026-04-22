# path_manager — Development Plan & Progress

> 最後更新：2026-04-22

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
