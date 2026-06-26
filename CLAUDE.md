# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 專案概覽

**ISD Python Framework SDK** (`isd-py-framework-sdk`) 是一套底層基礎框架套件，提供所有 ISD 系列模組共用的設計模式與工具。版本 `0.9.0`，Python ≥ 3.11。

- pip 安裝名：`isd-py-framework-sdk`
- Python import 名：`isd_py_framework_sdk`
- 版本號格式：`BigChanges.VersionCode.HotfixOrUpdate`（定義在 `src/isd_py_framework_sdk/_version.py`）

---

## 開發環境建置

```powershell
# 建立並啟動虛擬環境
python -m venv .venv
.venv\Scripts\Activate.ps1

# 以可編輯模式安裝核心套件
pip install -e .

# 安裝所有 extras（包含測試工具）
pip install -e ".[all]"
```

---

## 建置與發布

```powershell
# 在 venv 啟動後執行（腳本會互動確認）
.\builder__whl.ps1

# 手動建置
.venv\Scripts\python.exe -m build
# 輸出到 dist/
```

版本號在發布前必須手動修改 `src/isd_py_framework_sdk/_version.py`。

---

## 測試

```powershell
# 執行全部測試（pytest）
.venv\Scripts\python.exe -m pytest -v tests/

# 執行單一測試檔
.venv\Scripts\python.exe -m pytest -v tests/base/singleton_test.py
.venv\Scripts\python.exe -m pytest -v tests/events/event_test.py
.venv\Scripts\python.exe -m pytest -v tests/helpers/assertions_test.py
.venv\Scripts\python.exe -m pytest -v tests/helpers/decorators_test.py
.venv\Scripts\python.exe -m pytest -v tests/helpers/exceptions_test.py
.venv\Scripts\python.exe -m pytest -v tests/path/test_path_manager.py
.venv\Scripts\python.exe -m pytest -v tests/interop/test_interop.py
.venv\Scripts\python.exe -m pytest -v tests/cipher_kit/test_cipher_kit.py
.venv\Scripts\python.exe -m pytest -v tests/credential_vault/test_credential_vault.py

# file_compare 測試（script 式，直接執行；先產生樣本）
.venv\Scripts\python.exe tests/test_file/generate_samples.py
.venv\Scripts\python.exe tests/test_file/test_csv.py   # 其餘 test_json/jsonl/txt/xml/yaml/toml/ini/excel 同理

# monitoring 整合測試（非 pytest，直接執行）
.venv\Scripts\python.exe examples/monitoring/different_usecase.py

# logger 整合測試（非 pytest，需手動執行）
.venv\Scripts\python.exe tests/logger/test__msg_logger.py
.venv\Scripts\python.exe tests/logger/combined_logger.py
```

`test_runner.bat` 列出所有單元測試的逐一執行指令，可作為參考。

### 測試慣例（重要，否則會誤判「沒測到」）

本專案沒有 pytest 設定檔，沿用預設 `python_files = test_*.py`，因此測試分兩類：

- **真 pytest（檔名 `test_*.py`、函式 `test_*`）**：`path` / `excel_painter` / `cipher_kit` / `credential_vault` / `interop`。可用 `pytest -q tests/<dir>`。
- **script 式自我驗證（`*_test.py` 或 `__main__` 腳本）**：`base` / `events` / `helpers` / `test_file`。pytest **目錄掃描不會收集它們**（會顯示「no tests ran」）；請用 `python <file>` 直接執行，靠內部 `assert` / 自製 harness 驗證。
- **整包 `tests/` 一起跑會在 capture teardown 崩潰**（某模組 import 時關閉 stdout）——請**分目錄／分檔**跑。
- Windows cp950 主控台：script 式測試會印 `✔`/`✘`，**重導 stdout 時**請先 `set PYTHONIOENCODING=utf-8`（PowerShell：`$env:PYTHONIOENCODING="utf-8"`），否則 `UnicodeEncodeError`（非邏輯失敗）。
- `unified_io` 目前**無自動化測試**（見其 `agent.md`）；驗證 Excel `styled`/`preserve` 走 `excel_painter` 橋接時，請手動 round-trip。

---

## 套件結構與架構

```
src/isd_py_framework_sdk/
├── _version.py                   版本號（動態 setuptools 來源）
├── _optional.py                  optional 依賴管線（require / have / notify_substitution）— 管「第三方套件」
├── interop/                      跨模組橋接層（require_feature / has_feature）— 管「子套件之間」
├── __init__.py                   全部公開 API 的 flat 匯出點（PEP 562 lazy 載入）
├── cli.py                        CLI 入口（isd-py-framework-sdk -V）
│
├── base/                         核心設計模式
├── events/                       事件系統（observe / pub-sub）
├── message_logger/               結構化 logger（adapter fan-out 架構）
├── monitoring/                   迴圈計時器 & 進度顯示
├── file_compare/                 多格式檔案比對（unittest 輔助）
├── path_manager/                 集中式路徑管理（singleton registry）
├── unified_io/                   統一 IO 介面（IReader/IWriter adapter）
├── excel_painter/                Excel 樣式工具（fluent ExcelPainter + 格式快照）
├── cipher_kit/                   加密工具（seal/unseal + 可組合 cipher / KDF / 金鑰來源）
├── credential_vault/             祕密載入（env/yaml/json/SYS_ENV + 透明解密）
├── helpers/
│   ├── assertions/               型別、值域、集合斷言
│   ├── decorators/               10 個面向的裝飾器集合
│   └── exceptions/               10 個面向的自訂例外集合
└── window_design_helper/         Tkinter 視窗開發輔助工具
```

### 短路徑別名（Convenience shims）

根層有幾個 flat 模組只做 re-export，讓呼叫端不用記深層路徑。這些是向下相容的薄包裝，**本體在子套件中**：

| 薄包裝 | 實體位置 |
|---|---|
| `interface.py` | `→ base/`, `window_design_helper/` |
| `events_bus.py` | `→ events/` |
| `msg_logger.py` | `→ message_logger/` |
| `assertions.py` | `→ helpers/assertions/` |
| `decorators.py` | `→ helpers/decorators/` |
| `exceptions.py` | `→ helpers/exceptions/` |

新功能優先加到子套件；短路徑別名僅作向下相容保留，不在此擴充。

---

## 核心設計哲學

### Singleton 模式
`SingletonMetaclass`（`base/Singleton.py`）是所有 Singleton 的基石。只要 `metaclass=SingletonMetaclass`，類別首次建立後自動呼叫 `_initialize_manager()`（若存在），之後重複 `__call__` 回傳同一實例。`SingletonSystemLogger` 與 `SingletonPathManager` 均以此實作。

### Adapter/Fan-out 架構（message_logger）
`LoggerBase`（`message_logger/base/LoggerBase.py`）負責格式化與廣播；各 `LoggerAdapterBase` 子類持有各自的 `level_filter`，自行決定是否輸出。logger 對 adapter 種類完全不知情。`message_logger` 為 self-contained（不 import 其他 feature 子套件，只依賴 `base` 與核心 `_optional`）。

### 頂層 lazy 載入（PEP 562）
`__init__.py` 不在 import 時 eager 拉入任何子套件——它只定義 `_FLAT_EXPORTS`（名稱 → 來源模組）與 `__getattr__`/`__dir__`，於「第一次存取」某個名稱時才 import 其來源模組並快取。因此：

- `import isd_py_framework_sdk` 幾乎零成本，且**永遠不需要任何 optional 依賴**；
- flat API（`from isd_py_framework_sdk import retry`）與子套件屬性（`isd.cipher_kit`）皆照舊可用；
- `from ... import *` 走 `__all__`，不會把 heavy 子套件拉進來；
- 子套件 / 短路徑別名（`interface`、`events_bus`…）也可 lazy 以屬性取用。

新增公開名稱時：加到對應模組底下的 `_FLAT_EXPORTS`，並（為了 IDE 自動完成）加到檔案末端的 `TYPE_CHECKING` 區塊。

### Optional 依賴與通知（`_optional.py`）
核心承諾「預設安裝零 heavy 依賴」。所有 heavy 後端都**延後載入**，並透過 `_optional` 提供一致的使用者體驗：

- `require(module, *, extra=, feature=)` — lazy import，缺套件時拋 `MissingOptionalDependencyError`（`ImportError` 子類），訊息直接給出 `pip install isd-py-framework-sdk[<extra>]`。
- `have(module)` — capability 探測（如 `cipher_kit.have_argon2()`）。
- `notify_substitution(msg, once=True)` — 後端被「替換」時（如 argon2id → scrypt）發一次性 `DependencySubstitutionWarning`（numpy/pandas 風格）。

API 演進（改名 / 移除 / 實驗性）的對外通知，沿用 `helpers/decorators/lifecycle.py` 既有裝飾器：`deprecated` / `removed_in` / `since` / `experimental` / `battered`。這是「我們換掉了什麼」的官方通知機制，不要另造一套。

### 跨模組橋接（`interop/`）— `_optional` 的對內版
子套件原則上**解耦**，但有少數合理的跨模組呼叫（`credential_vault`→`cipher_kit`、`unified_io`→`excel_painter`、`monitoring`→`message_logger` 純型別）。這些呼叫統一收進 `interop`，避免散落腐爛、避免只裝部分 extra 的人壞掉。分工：

- **`_optional`**：管「**第三方套件**」裝了沒（`cryptography` / `openpyxl`…）。
- **`interop`**：管「**子套件之間**」誰用誰、缺了給什麼訊息——**建在 `_optional` 之上**，不重造。

關鍵語意：`import isd_py_framework_sdk.cipher_kit` 這個動作**永遠成功**（子套件同包、延遲載入），真正可能缺的是它的重依賴（`cryptography`）。所以 `interop.require_feature(name)` 先用 `_optional.require()` 確認該 feature 的代表性重依賴可用（缺則丟標準 `MissingOptionalDependencyError`，附 `pip install ...[<extra>]`），再回傳子套件 module；`has_feature(name)` 為不丟例外的能力探測。

**鐵則**：日後任何新增/修改的跨模組呼叫，都必須走 `interop.require_feature`（在真正用到的函式內 lazy 呼叫），並同步更新 `interop/agent.md` 的橋接表。`interop` 不放進頂層 flat 公開 API，是有文件管理的內部層。

### Extras 分層依賴策略
預設安裝（`pip install isd-py-framework-sdk`）不包含任何 heavy 第三方依賴（`pandas`, `openpyxl`, `pyyaml`, `colorama`…）。每個版本下限只宣告一次（在擁有該依賴的 leaf extra），umbrella 與 `all` 以**自我引用**（`isd-py-framework-sdk[...]`）組合，確保 `all` 永遠是完整超集合、不會漂移。使用者依需要安裝對應 extras：

```
[message_logger]      → colorama
[file_compare.excel]  → openpyxl, pandas
[file_compare.yaml]   → pyyaml
[unified_io]          → pandas
[unified_io.excel]    → pandas, openpyxl
[unified_io.sql]      → pandas, sqlalchemy
[excel_painter]       → openpyxl, wcwidth
[cipher_kit]          → cryptography
[cipher_kit.argon2]   → cryptography, argon2-cffi
[cipher_kit.keyring]  → cryptography, keyring
[credential_vault]    → python-dotenv
[credential_vault.yaml] → python-dotenv, pyyaml
[dev]                 → pytest, black
[all]                 → 全部
```

`file_compare/__init__.py` 使用 lazy import 延遲載入，確保不需要的 backend 不會在 import 時就失敗。`cipher_kit` 與 `credential_vault` 同樣採延遲載入：`import cipher_kit` 本身不需要 `cryptography`，重依賴只在實際 `seal`/`unseal` 時才載入；`credential_vault` 讀純文字值時完全不碰 `cryptography`，只有真的要解 `CK1` token 才 lazy import `cipher_kit`。

`message_logger` 的 `colorama` 為 **required-but-deferred**：`adapters.py` / `LoggerBase.py` 頂層不再 import colorama，只有在建構彩色 terminal adapter 時才 lazy import（缺套件時拋 `MissingOptionalDependencyError`）。`unified_io` 的 Excel 路徑（styled / `preserve` 寫入）會橋接到 `excel_painter`，因此 `[unified_io.excel]` extra 透過自我引用一併帶入 `excel_painter`（openpyxl + wcwidth）。

### 環境變數控制
| 變數 | 作用 |
|---|---|
| `RUN_MODE` | Logger 全域等級過濾：`DEBUG`（預設）/ `DISPLAY`（INFO+）/ `RUN`（ERROR+）|
| `EVENT_MANAGER_DEBUGGER` | 設為 `1` 時，`SingletonEventManager` 印出詳細事件類型解析資訊 |
| `VIRTUAL_ENV` | `PathMode.VIRTUAL_ENV` 與 build 腳本用來偵測 venv |

---

## 各子套件快速導覽

每個子套件的 `agent.md` 有更深入的分析。以下是主要 import 路徑與進入點：

| 子套件 | 主要類別/函式 | 推薦 import 路徑 |
|---|---|---|
| `base` | `SingletonMetaclass` | `isd_py_framework_sdk.interface` |
| `events` | `SingletonEventManager`, `IEventBase`, `IParsEventBase`, `MulticastCallback`, `DelayEventBusManager` | `isd_py_framework_sdk.events` |
| `message_logger` | `SingletonSystemLogger`, `get_logger`, `configure_logger`, `*Adapter` | `isd_py_framework_sdk.message_logger` |
| `monitoring` | `LoopedFunctionTimer`, `MultiProcessLoopedFunctionTimer`, `LoopedFunction_timer_decorator` | `isd_py_framework_sdk.monitoring` |
| `file_compare` | `compare_*_files` 系列函式 | `isd_py_framework_sdk.file_compare` |
| `path_manager` | `SingletonPathManager`, `PathMode`, `Waterfall` | `isd_py_framework_sdk.path_manager` |
| `helpers.assertions` | `assert__is_*` 系列 | `isd_py_framework_sdk.assertions` |
| `helpers.decorators` | 10 個面向的裝飾器 | `isd_py_framework_sdk.decorators` |
| `helpers.exceptions` | 10 個面向的例外 | `isd_py_framework_sdk.exceptions` |
| `unified_io` | `DataIO`, `IReader`, `IWriter`, `CsvIOAdapter`, `ExcelIOAdapter`, `JsonIOAdapter`, `SqlIOAdapter`；df 工具：`multiple_sort_dataframe`, `sort_dataframe`, `pick_and_reorder_then_rename_columns`, `dict_to_df` | `isd_py_framework_sdk.unified_io` |
| `excel_painter` | `ExcelPainter`, `save_styled_table`, `TableStyle`, `SheetFormatSnapshot`, `STATUS_*` | `isd_py_framework_sdk.excel_painter` |
| `cipher_kit` | `seal`, `unseal`, `CipherKit`, `PasswordCipher`, `RsaHybridCipher`, `FernetCipher`, `RawKeyCipher`, `Aes256SivCipher`, `AesGcmSivCipher`, `LayeredCipher`, `OsKeyring`, `generate_rsa_keypair`, `generate_fernet_key`, `generate_aead_key`, `generate_aes_siv_key` | `isd_py_framework_sdk.cipher_kit` |
| `credential_vault` | `CredentialVault`, `load_secret`（含 `prompt_password=` 執行時輸密碼）, `OsEnvSource`, `DotEnvSource`, `YamlSource`, `JsonSource` | `isd_py_framework_sdk.credential_vault` |
| `interop`（內部層） | `require_feature`, `has_feature`, `FEATURE_EXTRAS` | `isd_py_framework_sdk.interop` |

---

## 已知注意事項

- `DelayEventBusManager`（延遲事件匯流排）標記為 `==NEW-STRUCTURE-UNDONE==`，屬於未完成功能，設計仍在迭代中。
- `path_manager` 在多進程（`multiprocessing`）下，每個子進程有獨立 singleton；需在子進程中重新設定，或未來透過 `to_dict()`/`from_dict()` 序列化（見 `path_manager/dev_plan.md` §6）。
- `message_logger` 的 Tkinter adapter 只能在主執行緒使用 widget；跨執行緒 logging 需搭配 `widget.after()` + `queue.Queue`。
- `unified_io/.env` 不應版控（`.gitignore` 以 `**/.env` 排除；該檔含真實 MSSQL 憑證，切勿提交）。
- `excel_painter` 的 `mode="preserve"`（經由 `unified_io`）與 `SheetFormatSnapshot` 不保留 `CellRichText`／charts／images／conditional-formatting，只還原 cell style。
- `cipher_kit`：把 sealed token 與其 passphrase 放在同一個檔案（如同一份 `.env`）等於沒加密——務必用 `KeySource`（`OsKeyring` / `EnvSecret` / `PromptSecret`）從**不同來源**取得金鑰。金鑰遺失即資料遺失，無後門。`LayeredCipher` 的 token 不能用模組級 `unseal()` 自動解，需用相同 recipe 重建。
- `cipher_kit` 除 password / RSA 外另有 4 個「自管金鑰」cipher（全用既有 `cryptography`，無新依賴）：`FernetCipher`（`fernet`）、`RawKeyCipher`（`rawkey`，模組級 `seal(secret_key=...)` 的預設路徑）、`Aes256SivCipher`（`aes-siv`）、`AesGcmSivCipher`（`aes-gcm-siv`）。它們吃 raw 金鑰（用 `generate_fernet_key` / `generate_aead_key` / `generate_aes_siv_key` 產生）、不走 KDF；模組級 `unseal(token, secret_key=...)` 依 header 自動派發、可組進 `LayeredCipher`。**`Aes256SivCipher` 是確定性的**（同明文同金鑰→同 token，方便去重/盲索引，代價是洩漏明文相等性）——不要它時用隨機化 cipher。
- `cipher_kit` token 為自描述格式 `CK1.<header>.<body>`；password/RSA/rawkey/aes-gcm-siv 等隨機化 cipher 同一明文每次 `seal` 因隨機 salt/nonce 而不同，勿用 token 字串做相等比較或快取鍵（唯一例外是刻意確定性的 `aes-siv`）。`argon2id` 需 `[cipher_kit.argon2]`，未安裝時預設 KDF 自動降級為 `scrypt`，並發一次性 `DependencySubstitutionWarning` 通知（顯式指定 `argon2id` 但缺套件則拋 cipher_kit 自有的 `MissingDependencyError`）。注意此處有兩個相似但不同的錯誤：`cipher_kit.errors.MissingDependencyError`（`CipherKitError` 子類，cipher_kit 內部用）與核心 `_optional.MissingOptionalDependencyError`（`ImportError` 子類，跨模組共用，如 message_logger 缺 colorama）。
