# interop — 子套件之間的橋接層

`interop` 把本 SDK 內「**模組 A 需要呼叫模組 B**」的少數跨模組依賴**集中、命名乾淨地**管理起來，確保**只裝部分 extra 的人 import 不會壞**，而呼叫到缺席的橋時拿到的是清楚的安裝指示。

它是 [`_optional`](../_optional.py) 的「對內版」：

- `_optional` 管「**第三方套件**裝了沒」（`cryptography` / `openpyxl`…）。
- `interop` 管「**子套件之間**誰用誰、缺了給什麼訊息」——並且**建在 `_optional` 之上**。

---

## 為什麼需要這層

子套件原則上解耦，但有少數真正合理的跨呼叫（例如 `credential_vault` 解 `CK1` token 要用 `cipher_kit`）。若散落各處，遲早有人新增耦合卻忘了它需要哪個 extra，於是 partial install 的使用者執行到那條路徑時，看到的是後端深處的 `ModuleNotFoundError`，而非本專案一致、可操作的訊息。

`interop` 讓每條橋都：

- 有**唯一登記處**（見 [`agent.md`](agent.md) 的橋接表）；
- 缺依賴時丟**一致的** `MissingOptionalDependencyError`，附上 `pip install isd-py-framework-sdk[<extra>]`；
- **import 子套件本身永遠成功**，重依賴只在真正執行跨呼叫時才被要求。

---

## 用法

```python
from isd_py_framework_sdk.interop import require_feature, has_feature

# 取得兄弟子套件 module（缺 cryptography 時丟 MissingOptionalDependencyError）
cipher_kit = require_feature("cipher_kit")
token = cipher_kit.seal("secret", password="pw")

# 能力探測（不丟例外）
if has_feature("excel_painter"):
    excel_painter = require_feature("excel_painter")
    ...
```

| 函式 | 行為 |
|---|---|
| `require_feature(name)` | 回傳子套件 module；該 feature 的重依賴未裝 → 丟 `MissingOptionalDependencyError`（含 `pip install ...[extra]`）。未知 `name` → `KeyError`。 |
| `has_feature(name)` | 該 feature 的重依賴是否就緒，回傳 `bool`，不丟例外。 |
| `FEATURE_EXTRAS` | `dict`：feature 名 → 讓它完整可用的 extra 名。 |
| `FEATURE_PROBES` | `dict`：feature 名 → 用來探測「裝了沒」的重依賴 import 名。 |

---

## 目前登記的 feature

| feature | extra | 探測用重依賴 |
|---|---|---|
| `cipher_kit` | `cipher_kit` | `cryptography` |
| `excel_painter` | `excel_painter` | `openpyxl` |

完整的「使用方 → 被用方 / 觸發時機 / 程式碼位置」橋接表見 [`agent.md`](agent.md)。

---

## 給維護者的鐵則

**日後任何新增／修改的跨模組呼叫，都必須先走 `interop.require_feature`，並同步更新 `agent.md` 的橋接表。** 純型別的耦合（只在 annotation 用到、執行期不需要）改用 `TYPE_CHECKING` 即可，不需進登記表，但仍列入橋接表備查。

`interop` 不在頂層 flat 公開 API；它是有文件管理的內部層，進階使用者可直接 import。
