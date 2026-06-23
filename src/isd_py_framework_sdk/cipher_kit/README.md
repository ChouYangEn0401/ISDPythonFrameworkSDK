# `cipher_kit` — 乾淨好用的加密工具

把祕密字串「封」成可安全儲存的 token，之後再「解」回來。現代密碼學最佳實踐，但 API 維持低認知負擔：簡單路徑只要 `seal(data, password=...)`，神秘參數一律走 `**kwargs`。

與 [`credential_vault`](../credential_vault/README.md) 是一對：`cipher_kit` 負責「封」，`credential_vault` 負責「讀 + 透明解」。

## 最簡：兩個函式

```python
from isd_py_framework_sdk.cipher_kit import seal, unseal

token  = seal("sk-my-real-api-key", password="correct horse battery staple")
# → 'CK1.eyJ...'：自描述字串，貼進 .env / yaml / json / 任何地方

secret = unseal(token, password="correct horse battery staple")
# → 'sk-my-real-api-key'
```

> 同一明文每次 `seal` 都會得到**不同** token（隨機 salt/nonce）——這是正確行為，請勿拿 token 做相等比較或快取鍵。

## 進階參數（全部選用，預設已是安全選擇）

```python
seal("data", password="pw",
     aead="chacha20",     # 'aes-256-gcm'(預設) | 'chacha20-poly1305'
     kdf="argon2id",      # None(預設→最強可用) | 'argon2id' | 'scrypt' | 'pbkdf2-sha256'
     time_cost=4)         # 任何 KDF cost 參數直接傳
```

`unseal` 不需要任何演算法參數——cipher / KDF / salt / nonce 全寫在 token header 裡，自動讀取。

## 金鑰與密文分離（重要！）

把 token 和它的 passphrase 放在**同一個檔案**（例如同一份 `.env`）等於沒加密。請用 `KeySource` 從**不同來源**取得金鑰：

```python
from isd_py_framework_sdk.cipher_kit import CipherKit, OsKeyring, EnvSecret

# 金鑰存在 OS 安全儲存（Windows 認證管理員 / macOS Keychain），不落地在檔案
OsKeyring("my-app", "prod").store("super-secret-passphrase")    # 設定一次
kit = CipherKit.password(key_source=OsKeyring("my-app", "prod"))
token = kit.seal("db-password")
assert kit.unseal(token) == "db-password"

# 或從環境變數（由 CI / 部署系統注入）
kit = CipherKit.password(key_source=EnvSecret("APP_MASTER_PASS"))
```

| KeySource | 來源 | 適用 |
|---|---|---|
| `RawSecret(value)` | 記憶體字面值 | 測試 / 快速腳本 |
| `EnvSecret(var)` | OS 環境變數 | CI / 部署注入 |
| `PromptSecret(prompt)` | 執行時 `getpass` | 互動式，不儲存 |
| `KeyFileSource(path)` | repo 外受限檔案 | 伺服器部署 |
| `OsKeyring(service, user)` | OS 安全儲存 | 最推薦 |

## 非對稱（RSA 混合加密）

公鑰加密、私鑰解密；payload 大小不限（RSA 只用來包一把隨機 AES 金鑰）。

```python
from isd_py_framework_sdk.cipher_kit import seal, unseal, generate_rsa_keypair

priv, pub = generate_rsa_keypair()           # 3072-bit（預設）
token  = seal("secret", public_key=pub)       # 任何人有公鑰都能封
secret = unseal(token, private_key=priv)      # 只有私鑰能解
```

## 多層加密（想疊幾層都行）

```python
from isd_py_framework_sdk.cipher_kit import CipherKit, PasswordCipher, RsaHybridCipher

onion = CipherKit.layered([
    PasswordCipher(password="inner"),         # 內層
    RsaHybridCipher(public_key=pub),          # 外層
])
token = onion.seal("top secret")

# 解密：用相同 recipe（含對應金鑰）重建
back = CipherKit.layered([
    PasswordCipher(password="inner"),
    RsaHybridCipher(private_key=priv),
])
assert back.unseal(token) == "top secret"
```

`seal` 依序套層、`unseal` 反序剝層；每層各自產生自描述 token，可自由混搭演算法與金鑰。

## 安裝

```bash
pip install isd-py-framework-sdk[cipher_kit]            # 核心：cryptography（AES-GCM / ChaCha20 / scrypt / PBKDF2 / RSA）
pip install isd-py-framework-sdk[cipher_kit.argon2]     # + Argon2id KDF（記憶體硬化，推薦）
pip install isd-py-framework-sdk[cipher_kit.keyring]    # + OsKeyring（OS 安全儲存）
```

`import cipher_kit` 本身不需要 `cryptography`；重依賴只在實際 `seal`/`unseal` 時才載入。顯式指定 `kdf="argon2id"` 但未裝 `argon2-cffi` 會拋 `MissingDependencyError`；留預設則自動降級為 `scrypt`。

## 安全須知

- **金鑰遺失＝資料遺失**：沒有後門。
- AEAD（AES-256-GCM / ChaCha20-Poly1305）會驗證完整性：token 被竄改一個 byte，`unseal` 直接拋 `DecryptionError`，不會回傳垃圾。
- `LayeredCipher` 的 token 不能用模組級 `unseal()` 自動解，需用相同 recipe 重建。

完整工作流範例：[examples/cipher_kit/quickstart.py](../../../examples/cipher_kit/quickstart.py)。內部架構與密碼學選擇細節見 [agent.md](agent.md)。
