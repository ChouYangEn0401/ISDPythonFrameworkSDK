# ANALYSIS — 舊式弱加密 (`SHA256-CBC`) 遷移到 `cipher_kit` 的 `CK1`

> 這份文件寫給**另一個專案的 session**（`NTUAuthorityControlAnalysis2025` 的 `llm_service`，遷移到 `ntu_easy_llm`）。
> 它解釋：為什麼 **`isd-py-framework-sdk` 端不需要、也刻意不寫**任何遷就舊格式的程式碼；
> 並提供你**在你自己的專案裡**完成「解舊 → 重封」轉換所需的全部資訊。
> 本 SDK 不提供任何相容轉接層。

---

## 1. 事實：兩種格式 byte 不相容

### 舊格式（`llm_service` 的 `ENC_API_KEY`）

刻意弱化、無認證的對稱加密：

| 項目 | 舊做法 |
|---|---|
| 金鑰派生 | `key = SHA256(password)`（單次雜湊，**非 KDF**） |
| IV | `iv = key[:16]`（**固定、可預測**，與金鑰綁定） |
| 加密 | AES-CBC + PKCS7 padding |
| 編碼 | base64 |
| 完整性 | **無**（沒有 MAC / AEAD tag） |

問題：單次 SHA256 讓暴力破解極快；固定 IV 讓相同明文產生相同密文（洩漏資訊、可重放分析）；沒有認證標籤 → 密文被竄改也不會被偵測（可被 padding-oracle / bit-flipping 攻擊）。

### 本 SDK 格式（`cipher_kit` 的 `CK1`）

現代、自描述、有認證：

| 項目 | `cipher_kit` 做法 |
|---|---|
| 格式 | `CK1.<base64url(header_json)>.<base64url(ciphertext)>`（自描述） |
| 金鑰派生 | 真正的 KDF：Argon2id → scrypt → PBKDF2（記憶體/迭代硬化）+ **每 token 隨機 salt** |
| nonce | **每 token 隨機**（12-byte），存在 header |
| 加密 | AEAD：AES-256-GCM 或 ChaCha20-Poly1305 |
| 完整性 | AEAD tag + domain-separation AAD；竄改一個 byte 即 `DecryptionError` |

### 結論：讀不了

兩者的金鑰派生、IV/nonce 規則、容器格式、認證機制**全部不同**。`cipher_kit.unseal()` 依 `CK1.` 前綴與 header 派發；舊密文既沒有 `CK1.` 前綴、header 結構也不存在，**`cipher_kit.unseal()` 根本不會、也不該嘗試解它**（會丟 `InvalidTokenError`）。

---

## 2. 為什麼本 SDK 端不寫任何相容程式碼（拍板決策）

- 舊方案是**刻意弱化**的設計（無 AEAD/KDF、IV 固定可預測）。把它塞進 `cipher_kit` 核心，等於在一個主打「現代、安全、預設正確」的加密模組裡開一個弱化後門，會：
  1. **污染安全保證**：使用者無法再假設「`cipher_kit` 出來的東西都是 AEAD + KDF」。
  2. **擴大攻擊面**：多一條沒有認證的解密路徑，就是多一個 padding-oracle 風險點。
  3. **製造誤用陷阱**：有人會因為「方便」繼續用弱方案封新資料。
- 遷移本來就**只需要做一次**，而且**明文金鑰在執行時本來就拿得到**（你的服務本來就要用它去呼叫 API）。一次性轉換腳本是對的工具，不是長期相容層。

→ 因此本 SDK 端**零改動**。轉換在**你的專案**裡做。

---

## 3. 建議遷移路徑（在你的專案執行）

前提：你手上有舊的 `password`（解舊密文用）與你想要的新 `passphrase`（封新 token 用，可同可不同）。

### 步驟

1. **解舊（在舊專案做，不在本 SDK 做）**
   用舊專案自己的 `crypto_utils.aes_decrypt`（或等價邏輯：`key=SHA256(password)`、`iv=key[:16]`、AES-CBC、去 PKCS7、base64 解碼）把舊 `ENC_API_KEY` 解成**明文 API key**。

2. **重封成 `CK1`（用本 SDK）**
   ```python
   from isd_py_framework_sdk.cipher_kit import seal
   new_token = seal(plain_api_key, password=new_passphrase)   # → 'CK1.…'
   ```
   把 `new_token` 寫回 `.env`（例如 `ENC_API_KEY=CK1....`）。

3. **之後一律走 `credential_vault`（含執行時輸密碼的新糖）**
   ```python
   from isd_py_framework_sdk.credential_vault import load_secret

   # 任意檔案 + 任意 tag + 執行時輸密碼（getpass，永不存檔）
   api_key = load_secret("ENC_API_KEY", env_path="chatgpt_local.env", prompt_password=True)
   ```
   這正是你原本卡關的「從任意 `.env`、用任意 tag、執行時輸入且絕不存檔的密碼解密」——本 SDK 一行就能做到（`prompt_password=True` 等價於 `key_source=PromptSecret()`）。

### 一次性轉換腳本（你自己寫；以下為骨架）

```python
"""one_off__migrate_enc_api_key.py — 在『你的專案』執行一次即可。
舊→新轉換：SHA256-CBC 舊密文 → cipher_kit CK1 token。本 SDK 端不提供此腳本。"""
import getpass

# 1) 解舊（用你舊專案的工具；下面是等價骨架，請改用你既有的 aes_decrypt）
import base64, hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

def legacy_decrypt(b64_ciphertext: str, password: str) -> str:
    key = hashlib.sha256(password.encode()).digest()      # 舊：單次 SHA256
    iv = key[:16]                                          # 舊：固定 IV
    raw = base64.b64decode(b64_ciphertext)
    dec = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    padded = dec.update(raw) + dec.finalize()
    unpadder = PKCS7(128).unpadder()
    return (unpadder.update(padded) + unpadder.finalize()).decode("utf-8")

# 2) 重封成 CK1（用本 SDK）
from isd_py_framework_sdk.cipher_kit import seal

old_b64 = "...貼上舊 ENC_API_KEY..."
old_password = getpass.getpass("舊密碼：")
plain = legacy_decrypt(old_b64, old_password)

new_passphrase = getpass.getpass("新 passphrase：")
new_token = seal(plain, password=new_passphrase)
print("把這行寫回 .env：")
print(f"ENC_API_KEY={new_token}")
```

> 注意：上面 `legacy_decrypt` 只是**等價骨架**，方便你對照；正式轉換請直接呼叫你舊專案既有的 `crypto_utils.aes_decrypt`，避免重抄出錯。

---

## 4. 你需要讀的本 SDK 文件

- `src/isd_py_framework_sdk/cipher_kit/README.md` — `seal`/`unseal`/`CK1`、KDF/AEAD 選項、金鑰與密文分離原則。
- `src/isd_py_framework_sdk/cipher_kit/agent.md` — token 格式與派發機制細節。
- `src/isd_py_framework_sdk/credential_vault/README.md` — `load_secret` / `CredentialVault.get` 的 `prompt_password=` 與 `key_source=PromptSecret()` 用法（「任意檔案 + 任意 tag + 執行時輸密碼」段落）。

安裝（你的專案端）：

```bash
pip install isd-py-framework-sdk[cipher_kit]        # cryptography（seal/unseal）
pip install isd-py-framework-sdk[credential_vault]  # python-dotenv（讀 .env）
# 想用記憶體硬化的 argon2id KDF（建議）：
pip install isd-py-framework-sdk[cipher_kit.argon2]
```

---

## 5. 一句話總結

舊密文與 `CK1` **byte 不相容**，且舊方案刻意弱化不該進核心；既然明文金鑰執行時本來就拿得到，**用一次性腳本「解舊→`cipher_kit.seal` 重封」**，之後改用 `credential_vault.load_secret(..., prompt_password=True)` 即可。本 SDK 端不寫任何相容程式碼。
