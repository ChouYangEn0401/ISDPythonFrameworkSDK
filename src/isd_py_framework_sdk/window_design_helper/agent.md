# agent.md — `window_design_helper` 套件

## 職責

提供 Tkinter 視窗開發的輔助工具，協助開發者在設計階段快速確認視窗/元件的實際渲染尺寸，以便設定正確的 `minsize`、`geometry` 等參數。

---

## 架構

```
window_design_helper/
└── IScalableWindowTester.py    IScalableWindowTester + WidgetResizeLogger
```

此套件**沒有 `__init__.py`**，也**不在根 `__init__.py` 匯出**。在 `interface.py`（根層短路徑別名）有 re-export。

---

## 元件說明

### `IScalableWindowTester`

Mixin 類別，搭配 `tk.Toplevel` 或 `tk.Tk`，在每次 `<Configure>` 事件（視窗大小改變）時自動印出當前的 `height` 和 `width`。

**設計用途：** 開發階段暫時 mix in 此類別，觀察視窗實際渲染後的尺寸，確認後設定 `minsize` 或 `geometry`，再移除此 mixin。

```python
from isd_py_framework_sdk.interface import IScalableWindowTester
import tkinter as tk

class MyWindow(tk.Toplevel, IScalableWindowTester):
    def __init__(self, master):
        tk.Toplevel.__init__(self, master)
        IScalableWindowTester.__init__(self)
        # 觀察輸出後，決定合適的 minsize

# 輸出範例：
# [Resize] height=647, width=684
```

### `WidgetResizeLogger`

功能類似，但針對單一 widget（非頂層視窗）使用，記錄 widget 大小變化。

---

## Import

```python
# 透過 interface 短路徑
from isd_py_framework_sdk.interface import IScalableWindowTester

# 直接引用
from isd_py_framework_sdk.window_design_helper.IScalableWindowTester import IScalableWindowTester
```

---

## 注意事項

- 此工具**只用於開發階段**，生產程式碼移除此 mixin 後不影響任何功能。
- `<Configure>` 事件在視窗縮放、移動時都會觸發，輸出量可能很多。
- 無外部依賴，使用標準庫 `tkinter`。
