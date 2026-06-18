# ISD Python Framework

```
最底層的基礎架構套件，提供給所有 ISD 系列模組共用的底層設計模式與工具。
基於此套件開發的底層模組套件，將成為後續各專案的基石。
```

## 套件資訊

| 項目 | 值 |
|---|---|
| pip 安裝名 | `isd-py-framework-sdk` |
| Python import 名 | `isd_py_framework_sdk` |
| 版本 | `0.6.3` |
| Python 需求 | `>= 3.11` |

---

## 安裝

```bash
# 安裝核心（預設，不含任何 heavy 第三方依賴）
pip install isd-py-framework-sdk

# 可編輯（開發）模式安裝核心
pip install -e .

# 安裝所有 extras（包含測試工具與全部後端）
pip install isd-py-framework-sdk[all]
```

本套件以 `isd_py_framework_sdk` 為核心框架；預設安裝只包含核心邏輯，不含 `pandas`、`openpyxl`、`pyyaml`、`colorama` 等 heavy 第三方依賴。各子模組依需要安裝對應 extras（例如 `message_logger`、`file_compare.excel`、`file_compare.yaml`、`unified_io.sql`），完整 extras 清單與安裝範例請見各模組自己的 README（連結見下方「模組文件」）。

---

## 模組結構

```
isd_py_framework_sdk/
├── base/                      # 核心設計模式
├── events/                    # 事件系統
├── message_logger/            # 系統日誌
├── monitoring/                 # 迴圈計時器與進度條
├── file_compare/              # 多格式檔案比對工具
├── path_manager/              # 中心化路徑管理
├── unified_io/                # 統一資料 IO 介面（開發中）
├── window_design_helper/      # Tkinter 視窗開發輔助工具
├── helpers/                   # 工具集
│   ├── assertions/            # 斷言（型別 / 值域 / 集合）
│   ├── decorators/             # 裝飾器（10 個面向）
│   └── exceptions/             # 自訂例外（10 個面向）
├── interface.py                # 短路徑別名：SingletonMetaclass, IScalableWindowTester
├── events_bus.py               # 短路徑別名：事件系統（→ events/）
├── msg_logger.py                # 短路徑別名：日誌系統（→ message_logger/）
├── assertions.py                # 短路徑別名：斷言工具（→ helpers/assertions/）
├── decorators.py                # 短路徑別名：裝飾器工具（→ helpers/decorators/）
└── exceptions.py                 # 短路徑別名：自訂例外（→ helpers/exceptions/）
```

---

## Import Namespaces — 建議使用的 module 名稱

請以 `src/` 下的真實 module 名稱為主要匯入路徑；這讓使用者與套件結構一一對應，更直觀也更容易查找來源程式：

- `isd_py_framework_sdk.interface` — 核心設計模式與 `SingletonMetaclass`
- `isd_py_framework_sdk.events` — 事件系統（`SingletonEventManager`, `IEventBase`, `MulticastCallback`）
- `isd_py_framework_sdk.message_logger` — 系統日誌（`SingletonSystemLogger`, adapters）
- `isd_py_framework_sdk.monitoring` — 迴圈計時器與進度條
- `isd_py_framework_sdk.file_compare` — 多格式檔案比對工具（`compare_*` 函式）
- `isd_py_framework_sdk.path_manager` — 中心化路徑管理（`SingletonPathManager`, `PathMode`, `Waterfall`）
- `isd_py_framework_sdk.helpers.assertions` / `.decorators` / `.exceptions` — 工具集三兄弟
- `isd_py_framework_sdk.unified_io` — 統一資料 IO 介面（開發中，目前不可用）

備註：為了向下相容，套件仍提供便捷短檔（例如 `interface.py`, `events_bus.py`, `msg_logger.py` 等），但文件與範例會以真實 module 名稱為主，避免混淆。

---

## 模組文件

每個模組的詳細使用方式、安裝 extras、完整範例都放在該模組自己的 `README.md` 裡；想了解內部架構與開發細節則看同一目錄下的 `agent.md`。

| 模組 | 使用說明（README） | 開發/架構細節（agent.md） |
|---|---|---|
| `base` | [README](src/isd_py_framework_sdk/base/README.md) | [agent.md](src/isd_py_framework_sdk/base/agent.md) |
| `events` | [README](src/isd_py_framework_sdk/events/README.md) | [agent.md](src/isd_py_framework_sdk/events/agent.md) |
| `message_logger` | [README](src/isd_py_framework_sdk/message_logger/README.md) | [agent.md](src/isd_py_framework_sdk/message_logger/agent.md) |
| `monitoring` | [README](src/isd_py_framework_sdk/monitoring/README.md) | [agent.md](src/isd_py_framework_sdk/monitoring/agent.md) |
| `file_compare` | [README](src/isd_py_framework_sdk/file_compare/README.md) | [agent.md](src/isd_py_framework_sdk/file_compare/agent.md) |
| `path_manager` | [README](src/isd_py_framework_sdk/path_manager/README.md) | [agent.md](src/isd_py_framework_sdk/path_manager/agent.md) |
| `helpers`（assertions/decorators/exceptions） | [README](src/isd_py_framework_sdk/helpers/README.md) | [agent.md](src/isd_py_framework_sdk/helpers/agent.md) |
| `unified_io` ⚠️ 開發中，目前不可用 | [README](src/isd_py_framework_sdk/unified_io/README.md) | [agent.md](src/isd_py_framework_sdk/unified_io/agent.md) |
| `window_design_helper` | [README](src/isd_py_framework_sdk/window_design_helper/README.md) | [agent.md](src/isd_py_framework_sdk/window_design_helper/agent.md) |

整體架構導覽（給 Claude Code / 貢獻者）見根目錄 [CLAUDE.md](CLAUDE.md)。

---

## 版本查詢（CLI）

```bash
isd-py-framework-sdk -V
isd-py-framework-sdk --version
```

---

## 建置 `.whl`

```powershell
.\builder__whl.ps1
```
或
```bat
builder__whl.bat
```

---

## Acknowledgements / 銘謝

本專案的原始碼目前放置在：`https://github.com/ChouYangEn0401/ISDPythonFrameworkSDK`

本專案的底層架構，原先是在國立台灣大學（NTU）實驗室中擔任實驗助理期間開發，而後本人重新進行維護，詳見 `AUTHORS.md`。
