# `credential_vault` — 便利的祕密 / 設定載入

從 `.env` / YAML / JSON / 系統環境變數載入設定與祕密，並對 [`cipher_kit`](../cipher_kit/README.md) 封好的值做**透明解密**。對 PyInstaller 打包友善（凍結時也會去 exe 旁邊找檔案）。

與 `cipher_kit` 是一對：`cipher_kit` 負責「封」，`credential_vault` 負責「讀 + 透明解」。

## 最簡：一次性讀取

```python
from isd_py_framework_sdk.credential_vault import load_secret

db_url  = load_secret("DATABASE_URL")                              # os.environ → .env 瀑布
api_key = load_secret("OPENAI_API_KEY", password="my-passphrase")  # 是 CK1 token → 自動解
```

預設來源 `["os_env", ".env"]`（環境變數覆蓋檔案），`.env` 自動往上層尋找。

## 多來源瀑布

```python
from isd_py_framework_sdk.credential_vault import CredentialVault
from isd_py_framework_sdk.cipher_kit import OsKeyring

vault = CredentialVault(["os_env", ".env", "config.yaml", "secrets.json"])

host = vault.get("database.host")                          # YAML/JSON 巢狀鍵（dotted）
pw   = vault.get("DB_PASSWORD", key_source=OsKeyring("my-app", "prod"))  # 透明解密
url  = vault.get("MISSING", default="sqlite://")           # 找不到給 default
```

來源 spec 可為 `"os_env"`、路徑（`.env` / `.yaml` / `.yml` / `.json`），或 `ConfigSource` 實例。第一個命中的來源勝出。

| 來源 | 後端 | 巢狀鍵 |
|---|---|---|
| `OsEnvSource` | `os.environ`（stdlib） | ✗ |
| `DotEnvSource` | python-dotenv | ✗ |
| `YamlSource` | pyyaml | ✓（dotted） |
| `JsonSource` | json（stdlib） | ✓（dotted） |
| `ChainSource` | 瀑布組合 | — |

## 典型工作流（搭配 `cipher_kit`）

**1) 封一次**，把 token 貼進 `.env`：

```python
from isd_py_framework_sdk.cipher_kit import seal
print(seal("sk-real-key", password="my-passphrase"))
# 貼進 .env：  OPENAI_API_KEY=CK1.eyJ...
```

**2) 執行時讀回**，passphrase 從**另一條通道**取得（環境變數 / OS keyring / 互動輸入），避免與 token 同檔：

```python
from isd_py_framework_sdk.credential_vault import load_secret
from isd_py_framework_sdk.cipher_kit import EnvSecret

key = load_secret("OPENAI_API_KEY", key_source=EnvSecret("APP_MASTER_PASS"))
```

## ⭐ 任意檔案 + 任意 tag + 執行時輸密碼（永不存檔）

這是本套件的招牌能力：「從**任意 `.env`**、用**任意 key 名**、密碼**執行時才輸入、絕不落地**」地解密。很多下游專案卡在「金鑰管理」，其實這裡一行就能做到。

**最簡：`prompt_password=True`**（不必自己 import 任何東西，缺密碼時 `getpass` 互動輸入）：

```python
from isd_py_framework_sdk.credential_vault import CredentialVault

vault = CredentialVault(["os_env", "chatgpt_local.env"])      # 任意檔案
key   = vault.get("ENC_API_KEY", prompt_password=True)        # 任意 tag + 執行時輸入、永不存檔

# 一次性版本：
from isd_py_framework_sdk.credential_vault import load_secret
key = load_secret("ENC_API_KEY", env_path="chatgpt_local.env", prompt_password=True)
```

**完整版（等價、可自訂提示字串等）**：用 `key_source=PromptSecret()`：

```python
from isd_py_framework_sdk.credential_vault import CredentialVault
from isd_py_framework_sdk.cipher_kit import PromptSecret

vault = CredentialVault(["os_env", "chatgpt_local.env"])
key   = vault.get("ENC_API_KEY", key_source=PromptSecret("API 金鑰密碼："))
```

重點：

- **任意檔案** → `CredentialVault([..., "some_file.env"])` 或 `load_secret(key, env_path=...)`。
- **任意 tag** → 直接給 key 名，沒有寫死 `chatgpt` / `gemini`。
- **執行時密碼、不存檔** → `prompt_password=True`（底層 `getpass`，永不寫入任何檔案）。
- `prompt_password=True` 只有在「值真的是 `CK1` token」時才會跳出輸入提示；**純文字值不會提示、直接回傳**。
- 若同時給了 `password=` / `key_source=`，以顯式金鑰為準，不會跳輸入。

## 透明解密的判斷規則

`get()` 只有在「值是字串且以 `CK1.` 開頭」「且有提供金鑰（`password` / `key_source` / `private_key` / `prompt_password=True`）」時才解密；否則原值直接回傳。**所以讀純文字值永遠不會載入 `cryptography`。**

沒給金鑰時 sealed token 會原樣回傳（不自動解）——要解密務必帶金鑰參數。

## `get_secret`：強制加密

要求該值必須是 sealed token，存的若是純文字會拋 `ValueError`——防止「不小心把祕密用明文存進設定檔」。

```python
vault.get_secret("API_KEY", password="my-passphrase")   # 必須是 CK1 token，否則 raise
```

## 安裝

```bash
pip install isd-py-framework-sdk[credential_vault]         # 核心：python-dotenv（.env 支援）
pip install isd-py-framework-sdk[credential_vault.yaml]    # + pyyaml（YAML 來源）
```

JSON 與系統環境變數走 stdlib，零依賴。透明解密需另裝 `cipher_kit` extra（見其 README）。

## 對外橋接依賴

`credential_vault` 只在**真的要解一個 `CK1` token** 時，才透過 [`interop`](../interop/README.md) 橋接到 `cipher_kit`：

| 觸發時機 | 被用到的子套件 | 需要的 extra |
|---|---|---|
| `get()` / `load_secret()` 讀到 `CK1.` token 且帶金鑰材料（含 `prompt_password=True`） | `cipher_kit` | `cipher_kit`（`cryptography`） |

- **讀純文字值完全不碰 `cipher_kit`／`cryptography`**——只裝 `[credential_vault]` 的人完全沒問題。
- 只有解 token 那一刻才會要求 `cipher_kit`；若沒裝，會丟出標準訊息 `pip install isd-py-framework-sdk[cipher_kit]`（由 `interop.require_feature` 統一處理）。

## 注意事項

- `os.environ` 預設排在 `.env` 之前，同名環境變數會覆蓋檔案值（部署覆蓋慣例）。
- YAML/JSON 用 dotted key 取巢狀值（`"database.host"`）；`.env` 與 `os_env` 只支援扁平鍵。
- 各檔案來源會**快取**首次讀取結果；執行中改檔需新建實例才會反映。
- 安全提醒：token 與其 passphrase 放同一個 `.env` 等於沒加密，請用不同來源提供金鑰。

內部架構細節見 [agent.md](agent.md)。
