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
| 版本 | `0.7.0` |
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

本套件以 `isd_py_framework_sdk` 為核心框架；預設安裝**只包含核心邏輯，不含任何 heavy 第三方依賴**（`pandas`、`openpyxl`、`pyyaml`、`colorama`、`cryptography`…）。`import isd_py_framework_sdk` 採 **lazy 載入**（PEP 562）：本身幾乎不 import 任何東西，各功能與子套件在「第一次存取」時才載入，因此 heavy 後端只有在你真的用到對應功能時才會被拉進來。各子模組依需要安裝對應 extras 即可。

### Extras 一覽（裝你需要的就好）

| Extra | 啟用功能 | 帶入的第三方依賴 |
|---|---|---|
| *(無 extra)* | `base` / `events` / `helpers`（assertions、decorators、exceptions）/ `path_manager` / `monitoring` | 無（純標準庫）|
| `message_logger` | 彩色 terminal, tkinter 日誌輸出 | `colorama` |
| `excel_painter` | Excel 樣式工具 | `openpyxl`、`wcwidth` |
| `file_compare.excel` | Excel 檔案比對 | `openpyxl`、`pandas` |
| `file_compare.yaml` | YAML 檔案比對 | `pyyaml` |
| `file_compare` | 上述所有比對後端 | `openpyxl`、`pandas`、`pyyaml` |
| `unified_io` | CSV / JSON 統一 IO | `pandas` |
| `unified_io.excel` | Excel 讀寫（含樣式，橋接 `excel_painter`）| `pandas`、`openpyxl`、`wcwidth` |
| `unified_io.sql` | SQL 讀寫 | `pandas`、`sqlalchemy` |
| `cipher_kit` | 加密 / 解密（AEAD / KDF / RSA）| `cryptography` |
| `cipher_kit.argon2` | argon2id KDF（建議）| `cryptography`、`argon2-cffi` |
| `cipher_kit.keyring` | OS 安全儲存金鑰來源 | `cryptography`、`keyring` |
| `credential_vault` | `.env` / JSON / 環境變數祕密載入 | `python-dotenv` |
| `credential_vault.yaml` | 加上 YAML 設定來源 | `python-dotenv`、`pyyaml` |
| `dev` | 測試 / 格式化工具 | `pytest`、`black` |
| `all` | 以上全部 | 全部 |

每個 extra 的版本下限只宣告一次；umbrella 與 `all` 透過自我引用組合而成，因此 `all` 永遠是完整的超集合、不會與各 extra 漂移。完整使用範例請見各模組自己的 README（連結見下方「模組文件」）。

> 缺少 optional 依賴時不會在 `import` 當下爆掉；而是在你實際用到該功能時，給你一則明確、可照做的安裝提示（例如缺 `colorama` 時建立彩色 adapter 會提示 `pip install isd-py-framework-sdk[message_logger]`）。

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
├── unified_io/                # 統一資料 IO 介面
├── excel_painter/             # Excel 樣式工具（fluent ExcelPainter + 格式快照）
├── cipher_kit/                # 加密工具（seal/unseal + 可組合 cipher / KDF / 金鑰來源）
├── credential_vault/          # 祕密載入（env/yaml/json/SYS_ENV + 透明解密）
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
- `isd_py_framework_sdk.unified_io` — 統一資料 IO 介面（`DataIO`, `*IOAdapter`）
- `isd_py_framework_sdk.excel_painter` — Excel 樣式工具（`ExcelPainter`, `save_styled_table`）
- `isd_py_framework_sdk.cipher_kit` — 加密工具（`seal`, `unseal`, `CipherKit`, `OsKeyring`）
- `isd_py_framework_sdk.credential_vault` — 祕密載入（`CredentialVault`, `load_secret`）
- `isd_py_framework_sdk.window_design_helper` — Tkinter 視窗開發輔助工具

子套件也可直接以屬性方式 lazy 取用（第一次存取才載入），不必先 `import`：

```python
import isd_py_framework_sdk as isd

isd.SingletonMetaclass        # 來自 base（首次存取才載入）
isd.retry                     # 來自 helpers.decorators
isd.cipher_kit.seal(...)      # cipher_kit 子套件，首次存取才載入
```

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
| `unified_io` | [README](src/isd_py_framework_sdk/unified_io/README.md) | [agent.md](src/isd_py_framework_sdk/unified_io/agent.md) |
| `excel_painter` | [README](src/isd_py_framework_sdk/excel_painter/README.md) | [agent.md](src/isd_py_framework_sdk/excel_painter/agent.md) |
| `cipher_kit` | [README](src/isd_py_framework_sdk/cipher_kit/README.md) | [agent.md](src/isd_py_framework_sdk/cipher_kit/agent.md) |
| `credential_vault` | [README](src/isd_py_framework_sdk/credential_vault/README.md) | [agent.md](src/isd_py_framework_sdk/credential_vault/agent.md) |
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
