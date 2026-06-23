# agent.md — `cipher_kit` 套件

## 職責

提供一套**乾淨、可組合**的加密工具：把祕密字串「封」成可安全儲存的 token，之後再「解」回來。專注於把現代密碼學最佳實踐包成低認知負擔的 API——簡單路徑只要 `seal(data, password=...)`，進階參數一律走 `**kwargs`。

核心理念：**祕密（ciphertext）與金鑰（passphrase）應分離**。本套件用 `KeySource` 抽象讓金鑰可來自 OS keyring / 環境變數 / 執行時輸入，避免「密文與密碼放同一個檔」的加密劇場。

與 [`credential_vault`](../credential_vault/agent.md) 互補：`cipher_kit` 負責「封」，`credential_vault` 負責「讀 + 透明解」。

---

## 架構

```
cipher_kit/
├── __init__.py        公開 API：seal / unseal / CipherKit + 所有 cipher、key source
├── errors.py          例外階層（CipherKitError 為根）
├── envelope.py        版本化自描述 token 格式（純 stdlib，認得 token 不需 cryptography）
├── kdf.py             金鑰派生：argon2id → scrypt → pbkdf2-sha256
├── key_sources.py     passphrase 來源：Raw / Env / Prompt / KeyFile / OsKeyring
├── ciphers.py         Cipher ABC + Identity / Password / RsaHybrid / Layered
└── rsa_utils.py       generate_rsa_keypair()
```

依賴：核心只需 `cryptography`（extra `cipher_kit`）。`argon2id` 需 `cipher_kit.argon2`；`OsKeyring` 需 `cipher_kit.keyring`。
**`import cipher_kit` 本身不需要 `cryptography`**——重依賴只在實際 seal/unseal 時才載入。

---

## Token 格式（`envelope.py`）

```
CK1.<base64url(header_json)>.<base64url(ciphertext)>
```

`header` 是一個小 JSON，攜帶解密所需的一切（cipher 名、KDF 演算法與參數、salt、nonce）。因為**自描述**，`unseal()` 不需要被告知當初用什麼演算法——它自己讀 header。這也是未來能升級演算法的關鍵：把 `CK1` 前綴升為 `CK2`，解碼器同時支援兩者即可。

---

## 核心 API

### 模組級函式（90% 情境）

```python
from isd_py_framework_sdk.cipher_kit import seal, unseal

token  = seal("sk-my-real-api-key", password="correct horse battery staple")
secret = unseal(token, password="correct horse battery staple")
```

進階參數全部選用，預設值已是安全現代選擇：

```python
seal("data", password="pw",
     aead="chacha20",        # 'aes-256-gcm'(預設) | 'chacha20-poly1305'
     kdf="argon2id",         # None(預設→最強可用) | 'argon2id' | 'scrypt' | 'pbkdf2-sha256'
     time_cost=4)            # 任何 KDF cost 參數直接走 **kwargs
```

### `CipherKit`（可重用物件）

把設定集中一處，重複使用：

```python
from isd_py_framework_sdk.cipher_kit import CipherKit, OsKeyring

kit = CipherKit.password(key_source=OsKeyring("my-app", "prod"))
a, b = kit.seal("secret-a"), kit.seal("secret-b")
assert kit.unseal(a) == "secret-a"
```

工廠：`CipherKit.password(...)`、`CipherKit.rsa(public_key=/private_key=)`、`CipherKit.layered([...])`。

### 非對稱（RSA 混合加密）

```python
from isd_py_framework_sdk.cipher_kit import seal, unseal, generate_rsa_keypair

priv, pub = generate_rsa_keypair()        # 3072-bit（預設）
token  = seal("secret", public_key=pub)    # 任何人有公鑰都能封
secret = unseal(token, private_key=priv)   # 只有私鑰能解
```

RSA 本身只能加密 ~200 bytes；混合加密用隨機資料金鑰以 AEAD 加 payload、再用 RSA-OAEP 只包那把小金鑰，因此 payload 大小不限。

### 多層加密（瘋狂疊層也乾淨）

```python
from isd_py_framework_sdk.cipher_kit import CipherKit, PasswordCipher, RsaHybridCipher

onion = CipherKit.layered([
    PasswordCipher(password="inner"),       # 內層
    RsaHybridCipher(public_key=pub),        # 外層
])
token = onion.seal("top secret")
# 解密：用相同 recipe（含對應金鑰）重建 LayeredCipher
back = CipherKit.layered([
    PasswordCipher(password="inner"),
    RsaHybridCipher(private_key=priv),
])
assert back.unseal(token) == "top secret"
```

`seal` 依序套層、`unseal` 反序剝層。每層各自產生自描述 token，所以可自由混搭演算法與金鑰。

---

## 金鑰來源（`key_sources.py`）

| 類別 | 來源 | 何時用 |
|---|---|---|
| `RawSecret(value)` | 記憶體字面值 | 測試 / 快速腳本 |
| `EnvSecret(var)` | OS 環境變數 | CI/部署系統注入，不落地 |
| `PromptSecret(prompt)` | 執行時 `getpass` 輸入 | 互動式，永不儲存 |
| `KeyFileSource(path)` | repo 外、權限受限的檔案 | 伺服器部署 |
| `OsKeyring(service, user)` | OS 安全儲存（Windows 認證管理員 / macOS Keychain） | 最推薦，金鑰不落地 |

```python
OsKeyring("my-app", "prod").store("super-secret-passphrase")   # 存一次
kit = CipherKit.password(key_source=OsKeyring("my-app", "prod"))
```

---

## 密碼學選擇（學習筆記）

- **KDF**（passphrase → key）：絕不單純 `sha256(password)`。用 KDF 故意變慢 + 隨機 salt。
  - `argon2id`：記憶體硬化，抗 GPU/ASIC，目前最強（需 `argon2-cffi`）。
  - `scrypt`：也記憶體硬化，內建於 `cryptography`，沒裝 argon2 時的自動 fallback。
  - `pbkdf2-sha256`：僅迭代硬化，相容性最好。
- **AEAD**（authenticated encryption）：加密 + 完整性一步到位。token 被竄改一個 byte → `unseal` 直接拋 `DecryptionError`，不會回傳垃圾。
  - `aes-256-gcm`：現代 CPU 多有硬體加速。
  - `chacha20-poly1305`：純軟體快、constant-time、無 timing 側通道。
- **隨機 salt + 隨機 nonce 每次都重生**：所以同樣明文＋密碼每次得到**不同** token（修正舊版固定 IV 的確定性加密問題）。

---

## 進入點與 Import

```python
from isd_py_framework_sdk.cipher_kit import (
    seal, unseal, CipherKit,
    Cipher, IdentityCipher, PasswordCipher, RsaHybridCipher, LayeredCipher,
    KeySource, RawSecret, EnvSecret, PromptSecret, KeyFileSource, OsKeyring,
    generate_rsa_keypair, is_token, decode_token, default_kdf, have_argon2,
    CipherKitError, InvalidTokenError, DecryptionError,
    MissingDependencyError, MissingKeyError,
)
```

---

## 測試

```powershell
.venv\Scripts\python.exe -m pytest -v tests/cipher_kit/test_cipher_kit.py
```

---

## 常見陷阱

- **金鑰遺失＝資料遺失**：本套件沒有後門；passphrase / 私鑰弄丟就解不回來。
- 同一個 token 每次 `seal` 都不同是**正常**（隨機 salt/nonce），不要拿 token 字串做相等比較或快取鍵。
- `LayeredCipher` 的 token **不能**用模組級 `unseal()` 自動解（各層金鑰不同），必須用相同 recipe 重建 `LayeredCipher`。
- 顯式指定 `kdf="argon2id"` 但沒裝 `argon2-cffi` → `MissingDependencyError`；留預設 `None` 則自動降級 scrypt。
- RSA 私鑰目前以未加密 PEM 處理；私鑰本身請存進 `OsKeyring` 或權限受限檔案。
