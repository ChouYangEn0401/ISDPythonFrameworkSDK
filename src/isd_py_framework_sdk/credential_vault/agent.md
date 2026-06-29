# agent.md — `credential_vault` 套件

## 職責

便利、環境感知地從 `.env` / YAML / JSON / 系統環境變數載入設定與祕密，並對 [`cipher_kit`](../cipher_kit/agent.md) 封好的值做**透明解密**。是把分散的「找 .env、讀 key、解密」邏輯收斂成一個乾淨入口的載入層，並對 PyInstaller 打包環境友善（凍結時會去 exe 旁邊找檔案）。

與 `cipher_kit` 的分工：`cipher_kit` 負責「封」，`credential_vault` 負責「讀 + 透明解」。依賴方向：`credential_vault → cipher_kit`，且**經由 [`interop.require_feature("cipher_kit")`](../interop/agent.md)** 取得（只在真的要解某個 token 時才呼叫；缺 `cryptography` 時丟標準 `MissingOptionalDependencyError`）。

---

## 架構

```
credential_vault/
├── __init__.py     公開 API：CredentialVault / load_secret + 各 source
├── discovery.py    find_config_file()：walk-up + PyInstaller frozen 偵測
├── sources.py      ConfigSource ABC + OsEnv / DotEnv / Yaml / Json / Chain
└── vault.py        CredentialVault（瀑布 + 透明解密）、load_secret()
```

依賴：核心讀 `.env` 需 `python-dotenv`（extra `credential_vault`）；YAML 需 `pyyaml`（extra `credential_vault.yaml`）。JSON 與系統環境變數走 stdlib，零依賴。

---

## 核心 API

### `load_secret`（一次性便利讀取）

```python
from isd_py_framework_sdk.credential_vault import load_secret

db_url  = load_secret("DATABASE_URL")                              # os.environ → .env 瀑布
api_key = load_secret("OPENAI_API_KEY", password="my-passphrase")  # 是 CK1 token → 自動解
```

預設來源順序 `["os_env", ".env"]`（環境變數覆蓋檔案），`.env` 自動往上層尋找。

### `CredentialVault`（多來源瀑布）

```python
from isd_py_framework_sdk.credential_vault import CredentialVault
from isd_py_framework_sdk.cipher_kit import OsKeyring

vault = CredentialVault(["os_env", ".env", "config.yaml", "secrets.json"])

host = vault.get("database.host")                          # YAML/JSON 巢狀鍵（dotted）
pw   = vault.get("DB_PASSWORD", key_source=OsKeyring("my-app", "prod"))  # 透明解密
url  = vault.get("MISSING", default="sqlite://")           # 找不到給 default
```

**來源 spec**：`"os_env"`、路徑（`.env` / `.yaml` / `.yml` / `.json`），或直接給 `ConfigSource` 實例。第一個命中的來源勝出。

### 透明解密的判斷邏輯

`get()` 只有在「啟用 `decrypt`」「值是字串且以 `CK1.` 開頭」「且有提供金鑰（`password` / `key_source` / `private_key` / `prompt_password=True`）」三者皆成立時，才呼叫 `cipher_kit.unseal`。否則原值直接回傳——所以**讀純文字值永遠不會載入 `cryptography`**。

### `prompt_password=`（執行時輸密碼的糖）

`get()` / `load_secret()` 的 `prompt_password=True` 是「執行時輸入密碼、永不存檔」的便利開關：當值是 `CK1` token 且未給其他金鑰材料時，內部經 `interop.require_feature("cipher_kit")` 取得 `PromptSecret()`（底層 `getpass`）當 `key_source`。等價於手動 `key_source=PromptSecret()`，但呼叫端不必認識/ import 它。純文字值**不會**觸發提示；顯式 `password=`/`key_source=` 優先於 `prompt_password`。

### `get_secret`（強制加密）

要求該值必須是 sealed token，若存的是純文字會拋 `ValueError`——用來防止「不小心把祕密用明文存進設定檔」。

```python
vault.get_secret("API_KEY", password="my-passphrase")   # 必須是 CK1 token，否則 raise
```

---

## 典型工作流（搭配 `cipher_kit`）

1. **封一次**，把 token 貼進 `.env`：

   ```python
   from isd_py_framework_sdk.cipher_kit import seal
   print(seal("sk-real-key", password="my-passphrase"))
   # → OPENAI_API_KEY=CK1.eyJ...
   ```

2. **執行時讀回**，passphrase 從**另一條通道**取得（環境變數 / OS keyring / 互動輸入），避免與 token 同檔：

   ```python
   from isd_py_framework_sdk.credential_vault import load_secret
   from isd_py_framework_sdk.cipher_kit import EnvSecret
   key = load_secret("OPENAI_API_KEY", key_source=EnvSecret("APP_MASTER_PASS"))

   # 或：任意檔案 + 任意 tag + 執行時輸密碼（永不存檔）——一行搞定
   key = load_secret("ENC_API_KEY", env_path="chatgpt_local.env", prompt_password=True)
   ```

---

## 對外橋接依賴

| 觸發時機 | 被用到的子套件 | 需要的 extra |
|---|---|---|
| `get()` / `load_secret()` 讀到 `CK1.` token 且帶金鑰材料（含 `prompt_password=True`） | `cipher_kit` | `cipher_kit`（`cryptography`） |

唯一的跨模組呼叫，經 `interop.require_feature("cipher_kit")`（見 [`interop/agent.md`](../interop/agent.md) 橋接表 #1）。讀純文字值完全不碰此橋；只裝 `[credential_vault]`、不裝 `[cipher_kit]` 的人讀純文字毫無問題，只有解 token 時才會拿到 `pip install isd-py-framework-sdk[cipher_kit]` 的提示。

---

## 來源一覽（`sources.py`）

| 來源 | 後端 | 巢狀鍵 | 備註 |
|---|---|---|---|
| `OsEnvSource` | `os.environ` | ✗ | stdlib，永遠可用 |
| `DotEnvSource(path=None)` | python-dotenv | ✗ | `path=None` 自動尋找；有快取 |
| `YamlSource(path)` | pyyaml | ✓（dotted） | `required=False` 可容忍缺檔 |
| `JsonSource(path)` | json (stdlib) | ✓（dotted） | |
| `ChainSource([...])` | — | — | 瀑布，第一個命中勝出 |

---

## 進入點與 Import

```python
from isd_py_framework_sdk.credential_vault import (
    CredentialVault, load_secret,
    ConfigSource, OsEnvSource, DotEnvSource, YamlSource, JsonSource, ChainSource,
    find_config_file, is_frozen,
)
```

---

## 測試

```powershell
.venv\Scripts\python.exe -m pytest -v tests/credential_vault/test_credential_vault.py
```

---

## 常見陷阱

- `get()` 沒給金鑰時，sealed token 會**原樣**回傳（不會自動解）——這是刻意設計，避免無謂載入 `cryptography`。要解密務必帶 `password=` / `key_source=` / `private_key=`。
- `os.environ` 預設排在 `.env` 之前，所以同名環境變數會覆蓋檔案值（部署覆蓋慣例）。
- YAML/JSON 用 dotted key 取巢狀值（`"database.host"`）；`.env` 與 `os_env` 只支援扁平鍵。
- `DotEnvSource` / `YamlSource` / `JsonSource` 會**快取**首次讀取結果；執行中改檔不會反映，需新建實例。
- 安全提醒：把 token 與其 passphrase 放同一個 `.env` 等於沒加密。請用不同來源提供金鑰（見上方工作流）。
