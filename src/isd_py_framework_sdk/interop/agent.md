# agent.md — `interop` 套件

## 職責

集中管理**子套件之間**的所有跨模組呼叫（inter-module interoperability）。

本 SDK 的子套件原則上**解耦**，但有少數真正需要互相呼叫的點（例如 `credential_vault` 需要 `cipher_kit` 來解一個 `CK1` token）。這些跨模組呼叫如果散落各處，很容易「腐爛」：有人新增一條耦合卻忘了它需要哪個 extra，於是只裝部分 extra 的人（`pip install isd-py-framework-sdk[credential_vault]` 但沒裝 `[cipher_kit]`）執行到那條路徑時，拿到的是某個後端深處丟出的 `ModuleNotFoundError`，而不是本專案一致、可操作的安裝指示。

`interop` 把每一條這種橋接統一收進 `require_feature()` 之後，達成三件事：

1. **唯一的真實來源**：誰用誰、需要哪個 extra，全部記在這份文件的橋接表。
2. **一致的錯誤語氣**：每條橋缺依賴時，丟的都是和整個 SDK 一樣的 `MissingOptionalDependencyError`，訊息直接給出 `pip install isd-py-framework-sdk[<extra>]`。
3. **import 永不踩雷**：單純 `import` 任何子套件都不會觸發橋；重依賴只在「真的執行那條跨呼叫」時才被要求。

---

## 與 `_optional` 的分工（重要）

| | `_optional`（既有） | `interop`（本層） |
|---|---|---|
| 管什麼 | **第三方套件**裝了沒（`cryptography` / `openpyxl`…） | **子套件之間**誰用誰、缺了給什麼訊息 |
| 朝向 | 對外（third-party） | 對內（inter-module） |
| 關係 | 基石 | **建在 `_optional` 之上**，不重造 |

`interop` 是 `_optional` 的「對內版」。它不自己發明錯誤格式或探測邏輯——`require_feature` 內部直接呼叫 `_optional.require()`，所以行為與訊息跟既有第三方依賴體系**完全一致**。

---

## 關鍵語意：子套件永遠 import 得到，缺的是它的重依賴

`import isd_py_framework_sdk.cipher_kit` 這個動作**永遠成功**——子套件全都打包在同一個 wheel 裡，而且採延遲載入。真正可能缺席的是子套件的重**第三方後端**（`cipher_kit` 需要 `cryptography`、`excel_painter` 需要 `openpyxl`）。

所以 `require_feature` 不能只是 import 子套件就回傳，它分兩步：

1. 先用 `_optional.require(<probe_module>, extra=..., feature=...)` 確認該子套件的代表性重依賴可用（缺則丟 `MissingOptionalDependencyError`）。
2. 確認後才 `import` 並回傳子套件 module。

登記表（`_bridges.py`）：

```python
FEATURE_EXTRAS = {                 # feature → 讓它完整可用的 extra
    "cipher_kit":    "cipher_kit",      # 需要 cryptography
    "excel_painter": "excel_painter",   # 需要 openpyxl(+wcwidth)
}
FEATURE_PROBES = {                 # feature → 用來探測「裝了沒」的重依賴
    "cipher_kit":    "cryptography",
    "excel_painter": "openpyxl",
}
```

`message_logger` 核心零重依賴，它被 `monitoring` 用到的只是純型別（`LogLevelLiteral`），執行期完全不需要它，因此**不放進登記表**——該耦合已改用 `TYPE_CHECKING`，無 runtime 依賴可言。

---

## 跨模組橋接表（唯一真實來源）

> **鐵則：日後任何新增／修改的跨模組呼叫，都必須先走 `interop.require_feature`，並同步更新本表。** 這正是這層存在的理由——讓未來不會忘記耦合點。

| # | 使用方 → 被用方 | 觸發時機 | 需要的 extra | 程式碼位置 |
|---|---|---|---|---|
| 1 | `credential_vault` → `cipher_kit` | `get()` 讀到 `CK1.` token 且有金鑰材料時，才解密 | `cipher_kit`（`cryptography`） | `credential_vault/vault.py`，`get()` 內 lazy 呼叫 `require_feature("cipher_kit")` |
| 2 | `unified_io` → `excel_painter` | 寫 Excel 走 `styled` / `preserve` 模式時 | `excel_painter`（`openpyxl`+`wcwidth`） | `unified_io/adapters/excel_adapter.py`，`_write_styled` / `_write_preserve` 內 lazy 呼叫 `require_feature("excel_painter")` |
| 3 | `monitoring` → `message_logger` | **無 runtime 觸發**（純型別 `LogLevelLiteral`） | 無（型別參考，不需 extra） | `monitoring/looped_function_timer.py`，`TYPE_CHECKING` 區塊 |

橋 #3 是「純型別」耦合，已改成 `if TYPE_CHECKING:` import，執行期不存在；列在這裡只是為了「橋接帳本」的完整性，它**不經過** `require_feature`（因為沒有重依賴可缺）。

---

## API

```python
from isd_py_framework_sdk.interop import require_feature, has_feature

cipher_kit = require_feature("cipher_kit")   # → 回傳子套件 module；缺 cryptography 則丟 MissingOptionalDependencyError
if has_feature("excel_painter"):             # → True/False，不丟例外
    ...
```

- `require_feature(name)`：取得兄弟子套件 module；若該 feature 的重依賴未裝，丟 `MissingOptionalDependencyError`，訊息含 `pip install isd-py-framework-sdk[<extra>]`。未知的 `name` 丟 `KeyError`。
- `has_feature(name)`：能力探測，不丟例外。
- `FEATURE_EXTRAS` / `FEATURE_PROBES`：登記表，便於工具或測試自省。

---

## 公開性

`interop` **不**放進頂層 flat 公開 API（不在 `src/isd_py_framework_sdk/__init__.py` 的 `_FLAT_EXPORTS` / `__all__`）。它是有文件管理的內部層；進階使用者可 `from isd_py_framework_sdk.interop import require_feature` 取用，但不對一般使用者推播。

---

## 維護指引（新增一條橋時）

1. 在 `_bridges.py` 的 `FEATURE_EXTRAS`、`FEATURE_PROBES`、`_FEATURE_MODULES` 各加一行。
2. 在使用端**以 lazy 方式**（在真正會用到的函式／方法內）呼叫 `require_feature(...)`，不要放模組頂層。
3. 更新本檔的「跨模組橋接表」與 `README.md`。
4. 若是純型別耦合，改用 `TYPE_CHECKING`（搭配 `from __future__ import annotations`）即可，不需進登記表，但仍列入橋接表備查。

---

## 測試

```powershell
.venv\Scripts\python.exe -m pytest -q tests/interop
```
