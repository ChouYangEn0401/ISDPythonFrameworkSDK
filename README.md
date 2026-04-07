# ISD Python Framework

```text
最底層的基礎架構套件，提供給所有 ISD 系列模組共用的底層設計模式與工具。
基於此套件開發的底層模組套件，將成為後續各專案的基石。
```

## 套件名稱
| 項目 | 值 |
|---|---|
| pip 安裝名 | `isd-python-framework` |
| Python import 名 | `hyper_framework` |
| 版本 | `0.1.0` |

## 環境需求
```
Python >= 3.11
```

## 安裝

### 一、作為使用者（從 .whl 安裝）
```bash
pip install isd_python_framework-*.whl
```

### 二、共同開發（可編輯模式）
```bash
pip install -e .
```

## 目前提供的功能

### `SingletonMetaclass`
元類，讓任何類別自動實現單例模式。

```python
from hyper_framework import SingletonMetaclass

class MyManager(metaclass=SingletonMetaclass):
    def _initialize_manager(self):
        # 單例首次建立時執行一次
        self.data = []

a = MyManager()
b = MyManager()
print(a)
print(b)
assert a is b  # True
```

可選鉤子：若類別中定義了 `_initialize_manager(self)`，會在單例首次建立後自動呼叫一次。

## 版本查詢（CLI）
```bash
isd-python-framework -V
isd-python-framework --version
```

## 建置 .whl
```powershell
.\builder__whl.ps1
```
或
```bat
builder__whl.bat
```

## Acknowledgements / 銘謝

本專案的底層架構為本人研發成果，原先在國立台灣大學（NTU）實驗室擔任工程師期間開發，感謝台大提供薪資與時間，使我有此研發與學習機會，使得此基礎架構得以產生。

本專案亦是從一個名為 `ACA`（完全由本人開發、約 60k+ 行程式碼）之專案中抽取並整理而來，於此特別註記來源與感謝。

欲詳細聯絡或討論授權、引用方式，請參考 `AUTHORS.md`。

