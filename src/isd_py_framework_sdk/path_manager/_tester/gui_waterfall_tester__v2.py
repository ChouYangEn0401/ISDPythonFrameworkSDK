"""PathManager Waterfall Tester — interactive GUI debugger for path resolution.

Tabs
----
⚙ Config  : Configure proj_root / app_name; inspect live pm.info() snapshot.
🏷 Tags    : Full CRUD for registered tags — add / edit / delete / overwrite.
🔍 Test    : Run one waterfall against a registered tag OR an ad-hoc path.
📊 Batch  : Run every preset against a single tag and compare results.

Run
---
    python -m isd_py_framework_sdk.path_manager.gui_waterfall_tester
"""

from __future__ import annotations

import os
import zipfile
from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox

from isd_py_framework_sdk.path_manager import (
    SingletonPathManager,
    PathMode,
    Waterfall,
    ResolveIntent,
)

# ── Colour palette (Catppuccin Mocha) ────────────────────────────────────────
_BG     = "#1E1E2E"
_PANEL  = "#2A2A3E"
_ENTRY  = "#313244"
_BORDER = "#45475A"
_FG     = "#CDD6F4"
_DIM    = "#6C7086"
_ACCENT = "#89B4FA"
_GREEN  = "#A6E3A1"
_RED    = "#F38BA8"
_YELLOW = "#F9E2AF"
_GREY   = "#585B70"

_FONT  = ("Segoe UI", 10)
_BOLD  = ("Segoe UI", 10, "bold")
_SMALL = ("Segoe UI", 9)
_TITLE = ("Segoe UI", 14, "bold")
_MONO  = ("Consolas", 10)

# ── Pre-built waterfall index ─────────────────────────────────────────────────
PRESETS: dict[str, Waterfall] = dict(sorted(
    {n: getattr(Waterfall, n) for n in dir(Waterfall)
     if n.isupper() and isinstance(getattr(Waterfall, n), Waterfall)}.items()
))

WF_TIPS: dict[str, str] = {
    "DEV_STANDARD":
        "PROJ_ABSOLUTE → CWD\n"
        "Standard dev-machine reading — project root first, then current working dir.",
    "DEV_WITH_USER_CONFIG":
        "USER_CONFIG → PROJ_ABSOLUTE → CWD\n"
        "Dev tools that honour ~/.config overrides first (personal API keys, credentials).",
    "PROD_READ":
        "PROJ_ABSOLUTE → EXE_ABSOLUTE → USER_CONFIG\n"
        "Deployed app reading config, assets, or reference data.",
    "PROD_WRITE":
        "EXE_ABSOLUTE → USER_DATA → SYSTEM_TEMP\n"
        "Deployed app writing logs, outputs, or cached results.",
    "EXE_PREFER_BUNDLED":
        "EXE_INNER → EXE_ABSOLUTE → PROJ_ABSOLUTE\n"
        "PyInstaller: prefer data bundled inside the exe (MEIPASS), then beside it.",
    "EXE_WRITE_SAFE":
        "EXE_ABSOLUTE → USER_DATA → SYSTEM_TEMP\n"
        "PyInstaller writing output — never tries to write into the frozen bundle.",
    "ETL_INPUT":
        "PROJ_ABSOLUTE → CWD → SYSTEM_TEMP\n"
        "ETL pipeline: find source data in project, then cwd, then staging temp dir.",
    "ETL_OUTPUT":
        "PROJ_ABSOLUTE → USER_DATA → SYSTEM_TEMP\n"
        "ETL pipeline: write results to project output, then user data, last resort temp.",
    "CI_ARTIFACT":
        "PROJ_ABSOLUTE → CWD → SYSTEM_TEMP\n"
        "CI pipeline artefacts: workspace root → cwd → temp artefact dir.",
    "UNIVERSAL":
        "EXE_INNER → EXE_ABSOLUTE → PROJ_ABSOLUTE → CWD → USER_DATA → SYSTEM_TEMP\n"
        "Maximum compatibility — tries every location in a sensible order.",
}

PM_TIPS: dict[str, str] = {
    "ABSOLUTE":         "Stored path is a complete OS absolute path — used as-is without any base.",
    "PROJ_RELATIVE":    "Relative to project root.  Requires set_proj_root() to be called first.",
    "PROJ_ABSOLUTE":    "Absolute path formed as  proj_root / stored_path.",
    "EXE_RELATIVE":     "Relative to the directory containing the running .exe or script.",
    "EXE_ABSOLUTE":     "Absolute path under the exe / running-script directory.",
    "EXE_INNER":        "sys._MEIPASS / stored_path — only valid inside a PyInstaller bundle.\n"
                        "Raises RuntimeError when not frozen.",
    "SYSTEM_TEMP":      "tempfile.gettempdir() — system temporary folder.",
    "USER_HOME":        "Path.home() — the current user's home directory.",
    "USER_CONFIG":      "~/.config/<app>  |  %APPDATA%  |  ~/Library/Preferences",
    "USER_DATA":        "~/.local/share/<app>  |  %APPDATA%",
    "USER_CACHE":       "~/.cache/<app>  |  %LOCALAPPDATA%\\Cache  |  ~/Library/Caches",
    "CWD":              "Current working directory at the exact moment of the call.",
    "SCRIPT_DIR":       "Parent directory of the running script (__file__).",
    "VIRTUAL_ENV":      "Active venv root — $VIRTUAL_ENV or sys.prefix.",
    "PACKAGE_RESOURCE": "Package resource directory resolved via importlib.resources.",
}

IT_TIPS: dict[str, str] = {
    "READ":  "READ — path must already exist on disk.\nUse for assets, configs, and input data.",
    "WRITE": "WRITE — the nearest existing ancestor of the path must be writable.\n"
             "The file itself need not exist yet; it will be created by the caller.",
}


# ── Tooltip ───────────────────────────────────────────────────────────────────
class _Tip:
    """Hover tooltip attached to any Tk widget."""

    def __init__(self, widget: tk.Widget, text: str, delay: int = 450) -> None:
        self._w = widget
        self._text = text
        self._delay = delay
        self._id: Optional[str] = None
        self._pop: Optional[tk.Toplevel] = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)

    def set(self, text: str) -> None:
        self._text = text

    def _schedule(self, _e: tk.Event) -> None:
        self._hide()
        self._id = self._w.after(self._delay, self._show)

    def _hide(self, _e: Optional[tk.Event] = None) -> None:
        if self._id:
            self._w.after_cancel(self._id)
            self._id = None
        if self._pop:
            self._pop.destroy()
            self._pop = None

    def _show(self) -> None:
        if not self._text:
            return
        x = self._w.winfo_rootx() + 14
        y = self._w.winfo_rooty() + self._w.winfo_height() + 4
        self._pop = pop = tk.Toplevel(self._w)
        pop.wm_overrideredirect(True)
        pop.wm_geometry(f"+{x}+{y}")
        tk.Label(
            pop, text=self._text, justify="left",
            bg="#FFFDD0", fg="#1A1A2E", relief="solid", bd=1,
            font=_SMALL, wraplength=400, padx=8, pady=6,
        ).pack()


# ── Theme setup ───────────────────────────────────────────────────────────────
def _apply_theme(root: tk.Tk) -> None:
    root.configure(bg=_BG)
    s = ttk.Style(root)
    try:
        s.theme_use("clam")
    except Exception:
        pass

    s.configure(".",               background=_BG,    foreground=_FG,     font=_FONT)
    s.configure("TFrame",          background=_BG)
    s.configure("TLabel",          background=_BG,    foreground=_FG,     font=_FONT)
    s.configure("Dim.TLabel",      background=_BG,    foreground=_DIM,    font=_SMALL)
    s.configure("Title.TLabel",    background=_BG,    foreground=_ACCENT, font=_TITLE)
    s.configure("TLabelframe",     background=_BG,    relief="groove",    borderwidth=1,
                bordercolor=_BORDER)
    s.configure("TLabelframe.Label", background=_BG,  foreground=_ACCENT, font=_BOLD)

    s.configure("TButton",         background=_GREY,  foreground=_FG,     padding=(10, 5),
                relief="flat",     font=_FONT,         borderwidth=0)
    s.map("TButton",
          background=[("active", "#6C7086"), ("pressed", "#7F849C")],
          foreground=[("active", "#FFFFFF")])
    s.configure("Accent.TButton",  background=_ACCENT, foreground=_BG,    padding=(10, 5),
                relief="flat",     font=_BOLD)
    s.map("Accent.TButton",
          background=[("active", "#74C7EC"), ("pressed", "#89DCEB")],
          foreground=[("active", _BG)])
    s.configure("Danger.TButton",  background=_RED,    foreground=_BG,    padding=(10, 5),
                relief="flat",     font=_FONT)
    s.map("Danger.TButton",
          background=[("active", "#EBA0AC")],
          foreground=[("active", _BG)])

    s.configure("TEntry",    fieldbackground=_ENTRY, foreground=_FG,
                insertcolor=_FG, bordercolor=_BORDER, relief="flat")
    s.configure("TCombobox", fieldbackground=_ENTRY, foreground=_FG,
                selectbackground=_GREY, selectforeground=_FG)
    s.map("TCombobox",
          fieldbackground=[("readonly", _ENTRY)],
          foreground=[("readonly", _FG)])

    s.configure("TNotebook",     background=_BG,    tabmargins=[0, 4, 0, 0])
    s.configure("TNotebook.Tab", background=_PANEL, foreground=_DIM,
                padding=(18, 8),  font=_FONT)
    s.map("TNotebook.Tab",
          background=[("selected", _BG)],
          foreground=[("selected", _ACCENT)],
          font=[("selected", _BOLD)])

    s.configure("Treeview",         background=_ENTRY, fieldbackground=_ENTRY,
                foreground=_FG,    rowheight=30,       font=_FONT, borderwidth=0)
    s.configure("Treeview.Heading", background=_PANEL, foreground=_ACCENT,
                font=_BOLD,        relief="flat")
    s.map("Treeview",
          background=[("selected", _GREY)],
          foreground=[("selected", "#FFFFFF")])

    s.configure("TScrollbar",  background=_PANEL, troughcolor=_BG,
                arrowcolor=_DIM, bordercolor=_BG, relief="flat")
    s.configure("TRadiobutton", background=_BG, foreground=_FG, font=_FONT)
    s.configure("TCheckbutton", background=_BG, foreground=_FG, font=_FONT)
    s.configure("TSeparator",   background=_BORDER)
    s.configure("TSpinbox",     fieldbackground=_ENTRY, foreground=_FG,
                insertcolor=_FG, arrowcolor=_FG, relief="flat")


# ── Helpers ───────────────────────────────────────────────────────────────────
def _make_text(parent: tk.Widget, height: int = 10, **kw) -> scrolledtext.ScrolledText:
    return scrolledtext.ScrolledText(
        parent,
        bg=_ENTRY, fg=_FG, insertbackground=_FG,
        selectbackground=_GREY, selectforeground="#FFF",
        font=_MONO, relief="flat", borderwidth=0, height=height,
        **kw,
    )


def _sep(parent: tk.Widget, row: int, col: int = 0, span: int = 3) -> None:
    ttk.Separator(parent, orient="horizontal").grid(
        row=row, column=col, columnspan=span, sticky="ew", pady=8,
    )


def _tree_with_scroll(
    parent: tk.Widget,
    cols: tuple,
    col_widths: dict,
    col_heads: dict,
    height: int = 18,
) -> ttk.Treeview:
    """Build a Treeview with vertical + horizontal scrollbars inside *parent*."""
    parent.grid_rowconfigure(0, weight=1)
    parent.grid_columnconfigure(0, weight=1)

    tv = ttk.Treeview(parent, columns=cols, show="headings", height=height)
    for c in cols:
        tv.heading(c, text=col_heads.get(c, c))
        tv.column(c, width=col_widths.get(c, 120), minwidth=60)

    vsb = ttk.Scrollbar(parent, orient="vertical",   command=tv.yview)
    hsb = ttk.Scrollbar(parent, orient="horizontal", command=tv.xview)
    tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tv.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    return tv


# ── Tag add/edit dialog ───────────────────────────────────────────────────────
class _TagDialog(tk.Toplevel):
    """Modal form for registering or editing a tag."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str = "Tag",
        tag: str = "",
        path: str = "",
        anchor: str = "PROJ_ABSOLUTE",
        desc: str = "",
    ) -> None:
        super().__init__(parent)
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.title(title)
        self.configure(bg=_BG)
        self.result: Optional[tuple] = None

        frm = ttk.Frame(self, padding=20)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(1, weight=1)

        # Tag name
        ttk.Label(frm, text="Tag name:").grid(row=0, column=0, sticky="w", pady=5)
        self._tag = ttk.Entry(frm, width=38)
        self._tag.insert(0, tag)
        self._tag.grid(row=0, column=1, columnspan=2, sticky="we", padx=(8, 0), pady=5)
        _Tip(self._tag,
             "Short identifier used throughout the codebase.\n"
             "Must be unique — re-registering an existing tag overwrites it silently.")

        # Stored path + browse
        ttk.Label(frm, text="Stored path:").grid(row=1, column=0, sticky="w", pady=5)
        self._path = ttk.Entry(frm, width=38)
        self._path.insert(0, path)
        self._path.grid(row=1, column=1, sticky="we", padx=(8, 4), pady=5)
        ttk.Button(frm, text="Browse…", command=self._browse).grid(row=1, column=2)
        _Tip(self._path,
             "The path fragment stored in the registry.\n"
             "Typically a filename or relative sub-path like  data/myfile.csv\n"
             "For ABSOLUTE anchor, paste the full OS path.")

        # Anchor
        ttk.Label(frm, text="Anchor:").grid(row=2, column=0, sticky="w", pady=5)
        modes = [m.name for m in PathMode]
        self._anchor_var = tk.StringVar(value=anchor)
        anchor_cb = ttk.Combobox(frm, textvariable=self._anchor_var,
                                 values=modes, state="readonly", width=22)
        anchor_cb.grid(row=2, column=1, columnspan=2, sticky="we", padx=(8, 0), pady=5)
        self._anchor_tip = _Tip(anchor_cb, PM_TIPS.get(anchor, ""))
        anchor_cb.bind("<<ComboboxSelected>>",
                       lambda _e: self._anchor_tip.set(PM_TIPS.get(self._anchor_var.get(), "")))

        # Description
        ttk.Label(frm, text="Description:").grid(row=3, column=0, sticky="w", pady=5)
        self._desc = ttk.Entry(frm, width=38)
        self._desc.insert(0, desc)
        self._desc.grid(row=3, column=1, columnspan=2, sticky="we", padx=(8, 0), pady=5)

        _sep(frm, row=4, span=3)

        btn = ttk.Frame(frm)
        btn.grid(row=5, column=0, columnspan=3, sticky="e")
        ttk.Button(btn, text="Cancel", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(btn, text="  OK  ", style="Accent.TButton", command=self._ok).pack(side="right")

        self._tag.focus_set()
        self.wait_window()

    def _browse(self) -> None:
        p = filedialog.askopenfilename(title="Select file")
        if p:
            self._path.delete(0, tk.END)
            self._path.insert(0, p)

    def _ok(self) -> None:
        tag = self._tag.get().strip()
        if not tag:
            messagebox.showerror("Error", "Tag name cannot be empty.", parent=self)
            return
        self.result = (
            tag,
            self._path.get().strip(),
            self._anchor_var.get(),
            self._desc.get().strip(),
        )
        self.destroy()


# ── Tab 1: Config ─────────────────────────────────────────────────────────────
class _ConfigTab(ttk.Frame):
    def __init__(self, parent: ttk.Notebook, pm: SingletonPathManager) -> None:
        super().__init__(parent, padding=16)
        self._pm = pm

        # ── Project configuration ──────────────────────────────────────────
        cfg = ttk.LabelFrame(self, text="Project Configuration", padding=12)
        cfg.pack(fill="x", pady=(0, 12))
        cfg.columnconfigure(1, weight=1)

        ttk.Label(cfg, text="Project root:").grid(row=0, column=0, sticky="w")
        self._proj = ttk.Entry(cfg)
        self._proj.grid(row=0, column=1, sticky="we", padx=(8, 4))
        _Tip(self._proj,
             "Directory that becomes proj_root.\n"
             "You can paste a __file__ path — the parent directory is used.\n"
             "Required for PROJ_* anchors.")
        ttk.Button(cfg, text="Browse…", command=self._browse_proj).grid(row=0, column=2)
        ttk.Button(cfg, text="Script dir", command=self._use_script_dir).grid(
            row=0, column=3, padx=(4, 0))

        ttk.Label(cfg, text="Levels up:").grid(row=1, column=0, sticky="w", pady=8)
        self._levels = tk.IntVar(value=0)
        sp = ttk.Spinbox(cfg, from_=0, to=10, textvariable=self._levels, width=5)
        sp.grid(row=1, column=1, sticky="w", padx=(8, 0))
        _Tip(sp,
             "Ascend N levels from the selected path.\n"
             "Example: path = src/app/main.py, levels_up=2 → project root (parent of src/).")

        ttk.Label(cfg, text="App name:").grid(row=2, column=0, sticky="w")
        self._app = ttk.Entry(cfg)
        self._app.insert(0, "TesterApp")
        self._app.grid(row=2, column=1, sticky="we", padx=(8, 0))
        _Tip(self._app,
             "Used to build USER_CONFIG / USER_DATA / USER_CACHE directories.\n"
             "Example: 'MyApp' → ~/.config/MyApp  |  %APPDATA%\\MyApp")

        ttk.Button(cfg, text="✔  Apply Config", style="Accent.TButton",
                   command=self._apply).grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(10, 0))

        # ── Environment snapshot ───────────────────────────────────────────
        snap = ttk.LabelFrame(self, text="Environment Snapshot  (pm.info())", padding=10)
        snap.pack(fill="both", expand=True)

        self._info_txt = _make_text(snap, height=20)
        self._info_txt.pack(fill="both", expand=True)
        ttk.Button(snap, text="⟳  Refresh", command=self._refresh).pack(
            anchor="e", pady=(6, 0))

        self._refresh()

    def _browse_proj(self) -> None:
        d = filedialog.askdirectory(title="Select project root")
        if d:
            self._proj.delete(0, tk.END)
            self._proj.insert(0, d)

    def _use_script_dir(self) -> None:
        import __main__
        p = getattr(__main__, "__file__", None)
        if p:
            self._proj.delete(0, tk.END)
            self._proj.insert(0, str(Path(p).resolve().parent))

    def _apply(self) -> None:
        proj = self._proj.get().strip()
        if proj:
            try:
                self._pm.set_proj_root(proj, levels_up=self._levels.get())
            except Exception as exc:
                messagebox.showerror("Error", str(exc))
                return
        app = self._app.get().strip()
        if app:
            self._pm.set_app_name(app)
        self._refresh()

    def _refresh(self) -> None:
        txt = self._pm.info()
        self._info_txt.configure(state="normal")
        self._info_txt.delete("1.0", tk.END)
        self._info_txt.insert(tk.END, txt)
        self._info_txt.configure(state="disabled")


# ── Tab 2: Tags ───────────────────────────────────────────────────────────────
class _TagsTab(ttk.Frame):
    def __init__(self, parent: ttk.Notebook, pm: SingletonPathManager) -> None:
        super().__init__(parent, padding=16)
        self._pm = pm

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=(0, 6))

        ttk.Button(toolbar, text="＋  Add",    style="Accent.TButton",
                   command=self._add).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="✎  Edit",   command=self._edit).pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="✕  Delete", style="Danger.TButton",
                   command=self._delete).pack(side="left", padx=(0, 12))
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(toolbar, text="⟳  Refresh", command=self.refresh).pack(side="left")

        ttk.Label(self,
                  text="Tip: Re-registering an existing tag silently overwrites it — "
                       "use Edit to change the anchor or stored path at any time.",
                  style="Dim.TLabel", wraplength=900,
                  ).pack(anchor="w", pady=(0, 8))

        tv_frame = ttk.Frame(self)
        tv_frame.pack(fill="both", expand=True)

        cols = ("tag", "anchor", "stored_path", "description")
        self._tv = _tree_with_scroll(
            tv_frame, cols,
            col_widths={"tag": 160, "anchor": 145, "stored_path": 380, "description": 240},
            col_heads={"tag": "Tag", "anchor": "Anchor",
                       "stored_path": "Stored path", "description": "Description"},
            height=22,
        )
        self.refresh()

    def refresh(self) -> None:
        self._tv.delete(*self._tv.get_children())
        for tag, entry in self._pm._registry.all_entries().items():
            self._tv.insert("", tk.END, iid=tag, values=(
                tag, entry.anchor.name, str(entry.stored_path), entry.description,
            ))

    def _selected_tag(self) -> Optional[str]:
        sel = self._tv.selection()
        return sel[0] if sel else None

    def _add(self) -> None:
        dlg = _TagDialog(self, title="Add Tag")
        if dlg.result:
            tag, path, anchor, desc = dlg.result
            self._pm.register(tag, path, PathMode[anchor], description=desc)
            self.refresh()

    def _edit(self) -> None:
        tag = self._selected_tag()
        if not tag:
            messagebox.showinfo("Info", "Select a tag row to edit.")
            return
        entry = self._pm._registry.all_entries()[tag]
        dlg = _TagDialog(
            self, title=f"Edit Tag  ·  {tag}",
            tag=tag, path=str(entry.stored_path),
            anchor=entry.anchor.name, desc=entry.description,
        )
        if dlg.result:
            new_tag, path, anchor, desc = dlg.result
            if new_tag != tag:
                self._pm.unregister(tag)
            self._pm.register(new_tag, path, PathMode[anchor], description=desc)
            self.refresh()

    def _delete(self) -> None:
        tag = self._selected_tag()
        if not tag:
            messagebox.showinfo("Info", "Select a tag row to delete.")
            return
        if messagebox.askyesno("Confirm delete", f"Remove tag  '{tag}'?"):
            self._pm.unregister(tag)
            self.refresh()


# ── Tab 3: Single-waterfall test ──────────────────────────────────────────────
class _TestTab(ttk.Frame):
    _ADHOC = "__adhoc__"

    def __init__(
        self,
        parent: ttk.Notebook,
        pm: SingletonPathManager,
        tags_tab: "_TagsTab",
    ) -> None:
        super().__init__(parent, padding=16)
        self._pm = pm
        self._tags_tab = tags_tab

        # ── Source ────────────────────────────────────────────────────────
        src = ttk.LabelFrame(self, text="Source", padding=12)
        src.pack(fill="x", pady=(0, 10))
        src.columnconfigure(2, weight=1)

        self._src_mode = tk.StringVar(value="registered")
        rb_reg = ttk.Radiobutton(src, text="Registered tag",
                                 variable=self._src_mode, value="registered",
                                 command=self._toggle_src)
        rb_reg.grid(row=0, column=0, sticky="w")
        _Tip(rb_reg, "Use a tag already in the registry.\n"
                     "The waterfall combines each step's base dir with the tag's stored_path.")

        rb_adhoc = ttk.Radiobutton(src, text="Ad-hoc  (test a file without registration)",
                                   variable=self._src_mode, value="adhoc",
                                   command=self._toggle_src)
        rb_adhoc.grid(row=0, column=1, columnspan=3, sticky="w", padx=(20, 0))
        _Tip(rb_adhoc, "Temporarily register the path as  __adhoc__  and run immediately.\n"
                       "Lets you test any filename against any waterfall without touching the registry.")

        # Registered branch
        self._reg_frm = ttk.Frame(src)
        self._reg_frm.grid(row=1, column=0, columnspan=4, sticky="we", pady=(8, 0))
        ttk.Label(self._reg_frm, text="Tag:").pack(side="left")
        self._tag_var = tk.StringVar()
        self._tag_cb = ttk.Combobox(self._reg_frm, textvariable=self._tag_var,
                                    state="readonly", width=28)
        self._tag_cb.pack(side="left", padx=(8, 4))
        ttk.Button(self._reg_frm, text="⟳", width=3,
                   command=self._refresh_tags).pack(side="left")

        # Ad-hoc branch
        self._adhoc_frm = ttk.Frame(src)
        self._adhoc_frm.grid(row=2, column=0, columnspan=4, sticky="we", pady=(8, 0))
        ttk.Label(self._adhoc_frm, text="Filename:").pack(side="left")
        self._adhoc_path = ttk.Entry(self._adhoc_frm, width=36)
        self._adhoc_path.pack(side="left", padx=(8, 4))
        _Tip(self._adhoc_path,
             "Filename or relative sub-path to test, e.g.  555.png  or  data/555.png\n"
             "This is combined with each waterfall step's base directory.")
        ttk.Button(self._adhoc_frm, text="Browse…",
                   command=self._browse_adhoc).pack(side="left", padx=(0, 16))
        ttk.Label(self._adhoc_frm, text="Anchor:").pack(side="left")
        self._adhoc_anchor = tk.StringVar(value="PROJ_ABSOLUTE")
        adhoc_cb = ttk.Combobox(self._adhoc_frm, textvariable=self._adhoc_anchor,
                                values=[m.name for m in PathMode],
                                state="readonly", width=18)
        adhoc_cb.pack(side="left", padx=(8, 0))
        self._adhoc_anchor_tip = _Tip(adhoc_cb, PM_TIPS.get("PROJ_ABSOLUTE", ""))
        adhoc_cb.bind("<<ComboboxSelected>>",
                      lambda _e: self._adhoc_anchor_tip.set(
                          PM_TIPS.get(self._adhoc_anchor.get(), "")))

        self._toggle_src()

        # ── Waterfall controls ────────────────────────────────────────────
        wf = ttk.LabelFrame(self, text="Waterfall", padding=12)
        wf.pack(fill="x", pady=(0, 10))
        wf.columnconfigure(1, weight=1)

        ttk.Label(wf, text="Preset:").grid(row=0, column=0, sticky="w")
        preset_names = list(PRESETS.keys())
        self._preset_var = tk.StringVar(value=preset_names[0])
        self._preset_cb = ttk.Combobox(wf, textvariable=self._preset_var,
                                       values=preset_names, state="readonly", width=26)
        self._preset_cb.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self._preset_tip = _Tip(self._preset_cb, WF_TIPS.get(preset_names[0], ""))
        self._preset_cb.bind("<<ComboboxSelected>>",
                             lambda _e: self._preset_tip.set(
                                 WF_TIPS.get(self._preset_var.get(), "")))

        ttk.Label(wf, text="Steps:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._steps_lbl = ttk.Label(wf, text="", style="Dim.TLabel", wraplength=700)
        self._steps_lbl.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(6, 0))
        self._preset_cb.bind("<<ComboboxSelected>>", self._update_steps, add="+")
        self._update_steps()

        ttk.Label(wf, text="Intent:").grid(row=2, column=0, sticky="w", pady=(10, 0))
        intent_frm = ttk.Frame(wf)
        intent_frm.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(10, 0))
        self._intent_var = tk.StringVar(value="READ")
        for name in ("READ", "WRITE"):
            rb = ttk.Radiobutton(intent_frm, text=name,
                                 variable=self._intent_var, value=name)
            rb.pack(side="left", padx=(0, 16))
            _Tip(rb, IT_TIPS[name])

        ttk.Button(self, text="▶  Run", style="Accent.TButton",
                   command=self._run).pack(anchor="w", pady=(0, 10))

        # ── Trace output ──────────────────────────────────────────────────
        trace_frm = ttk.LabelFrame(self, text="Waterfall Trace", padding=8)
        trace_frm.pack(fill="both", expand=True)

        self._trace = _make_text(trace_frm, height=13)
        self._trace.tag_configure("head", foreground=_YELLOW, font=_BOLD)
        self._trace.tag_configure("dim",  foreground=_DIM)
        self._trace.tag_configure("ok",   foreground=_GREEN)
        self._trace.tag_configure("fail", foreground=_RED)
        self._trace.tag_configure("info", foreground=_ACCENT)
        self._trace.tag_configure("path", font=_MONO)
        self._trace.pack(fill="both", expand=True)

        # ── File preview ──────────────────────────────────────────────────
        prev_frm = ttk.LabelFrame(self, text="File Preview", padding=8)
        prev_frm.pack(fill="x", pady=(10, 0))
        self._preview = _make_text(prev_frm, height=7)
        self._preview.pack(fill="both", expand=True)

        self._refresh_tags()

    # ── helpers ───────────────────────────────────────────────────────────────
    def _toggle_src(self) -> None:
        if self._src_mode.get() == "registered":
            self._reg_frm.grid()
            self._adhoc_frm.grid_remove()
        else:
            self._reg_frm.grid_remove()
            self._adhoc_frm.grid()

    def _refresh_tags(self) -> None:
        tags = list(self._pm.list_tags().keys())
        self._tag_cb["values"] = tags
        if tags and not self._tag_var.get():
            self._tag_var.set(tags[0])

    def _browse_adhoc(self) -> None:
        p = filedialog.askopenfilename(title="Select test file")
        if p:
            self._adhoc_path.delete(0, tk.END)
            self._adhoc_path.insert(0, p)

    def _update_steps(self, _e: Optional[tk.Event] = None) -> None:
        wf = PRESETS.get(self._preset_var.get())
        if wf:
            self._steps_lbl.configure(text="  →  ".join(s.name for s in wf.steps))

    def _run(self) -> None:
        if self._src_mode.get() == "registered":
            tag = self._tag_var.get()
            if not tag:
                messagebox.showerror("Error", "No tag selected.")
                return
        else:
            adhoc_path = self._adhoc_path.get().strip()
            if not adhoc_path:
                messagebox.showerror("Error", "Enter a filename for ad-hoc mode.")
                return
            anchor = PathMode[self._adhoc_anchor.get()]
            self._pm.register(self._ADHOC, adhoc_path, anchor,
                               description="ad-hoc test")
            self._tags_tab.refresh()
            tag = self._ADHOC

        wf_name = self._preset_var.get()
        wf      = PRESETS[wf_name]
        intent  = ResolveIntent[self._intent_var.get()]

        resolved, trace = self._pm.get_with_trace(tag, wf, intent=intent)

        # ── Render trace ──────────────────────────────────────────────────
        t = self._trace
        t.configure(state="normal")
        t.delete("1.0", tk.END)

        t.insert(tk.END,
                 f"  Tag: {tag}    Waterfall: {wf_name}    Intent: {intent.name}\n",
                 "head")
        t.insert(tk.END,
                 "  Steps: " + "  →  ".join(s.name for s in wf.steps) + "\n",
                 "dim")
        t.insert(tk.END, "  " + "─" * 76 + "\n", "dim")

        for attempt in trace.attempts:
            mark = "✓" if attempt.ok else "✗"
            tag_style = "ok" if attempt.ok else "fail"
            t.insert(tk.END, f"  [{mark}] ", tag_style)
            t.insert(tk.END, f"{attempt.mode.name:<22}", "info")
            t.insert(tk.END, f"  {attempt.path}", "path")
            t.insert(tk.END, f"  ({attempt.reason})\n", "dim")

        t.insert(tk.END, "  " + "─" * 76 + "\n", "dim")
        if resolved:
            t.insert(tk.END, f"  RESOLVED  →  {resolved}\n", "ok")
        else:
            t.insert(tk.END, "  FAILED  — no step passed the check.\n", "fail")

        t.configure(state="disabled")

        # ── File preview ──────────────────────────────────────────────────
        self._preview.configure(state="normal")
        self._preview.delete("1.0", tk.END)
        if resolved:
            self._show_preview(Path(resolved))
        self._preview.configure(state="disabled")

    def _show_preview(self, p: Path) -> None:
        if not p.exists():
            self._preview.insert(tk.END, "Path was resolved but does not exist on disk.")
            return
        ext = p.suffix.lower()
        if ext in (".txt", ".md", ".csv", ".log", ".ini", ".toml",
                   ".json", ".jsonl", ".yaml", ".yml", ".py", ".xml"):
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
                self._preview.insert(tk.END, txt[:5000])
                if len(txt) > 5000:
                    self._preview.insert(tk.END, "\n… (truncated)")
            except Exception as exc:
                self._preview.insert(tk.END, f"Cannot read text: {exc}")

        elif ext in (".xlsx", ".xlsm", ".xltx"):
            try:
                with zipfile.ZipFile(p) as z:
                    members = z.namelist()
                self._preview.insert(
                    tk.END,
                    f"XLSX zip members ({len(members)}):\n" +
                    "\n".join(f"  {m}" for m in members),
                )
            except Exception as exc:
                self._preview.insert(tk.END, f"Cannot inspect XLSX: {exc}")

        elif ext in (".png", ".gif", ".ppm", ".pgm", ".pbm"):
            try:
                img = tk.PhotoImage(file=str(p))
                win = tk.Toplevel(self)
                win.title(p.name)
                win.configure(bg=_BG)
                lbl = tk.Label(win, image=img, bg=_BG)
                lbl.image = img       # keep reference alive
                lbl.pack(padx=16, pady=16)
                self._preview.insert(
                    tk.END,
                    f"Image displayed in new window.\n"
                    f"Dimensions: {img.width()} × {img.height()} px",
                )
            except Exception as exc:
                self._preview.insert(tk.END, f"Cannot display image: {exc}")

        else:
            try:
                data = p.read_bytes()
                self._preview.insert(
                    tk.END,
                    f"Binary file — {len(data):,} bytes\n"
                    f"First 160 bytes:\n{data[:160]!r}",
                )
            except Exception as exc:
                self._preview.insert(tk.END, f"Cannot read file: {exc}")


# ── Tab 4: Batch preset comparison ────────────────────────────────────────────
class _BatchTab(ttk.Frame):
    def __init__(self, parent: ttk.Notebook, pm: SingletonPathManager) -> None:
        super().__init__(parent, padding=16)
        self._pm = pm

        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", pady=(0, 12))

        ttk.Label(ctrl, text="Tag:").pack(side="left")
        self._tag_var = tk.StringVar()
        self._tag_cb = ttk.Combobox(ctrl, textvariable=self._tag_var,
                                    state="readonly", width=24)
        self._tag_cb.pack(side="left", padx=(8, 4))
        _Tip(self._tag_cb, "Run every waterfall preset in sequence against this registered tag.")
        ttk.Button(ctrl, text="⟳", width=3,
                   command=self._refresh_tags).pack(side="left")

        ttk.Label(ctrl, text="  Intent:").pack(side="left", padx=(16, 0))
        self._intent_var = tk.StringVar(value="READ")
        for name in ("READ", "WRITE"):
            rb = ttk.Radiobutton(ctrl, text=name, variable=self._intent_var, value=name)
            rb.pack(side="left", padx=(6, 0))
            _Tip(rb, IT_TIPS[name])

        ttk.Button(ctrl, text="▶  Run All Presets", style="Accent.TButton",
                   command=self._run).pack(side="left", padx=(20, 0))

        # Results table
        tv_frame = ttk.Frame(self)
        tv_frame.pack(fill="both", expand=True)

        cols = ("preset", "steps", "ok", "path")
        self._tv = _tree_with_scroll(
            tv_frame, cols,
            col_widths={"preset": 190, "steps": 360, "ok": 50, "path": 420},
            col_heads={"preset": "Preset", "steps": "Steps  (→ order)",
                       "ok": "OK?", "path": "Resolved path"},
            height=24,
        )
        self._tv.tag_configure("ok",   foreground=_GREEN)
        self._tv.tag_configure("fail", foreground=_RED)

        self._refresh_tags()

    def _refresh_tags(self) -> None:
        tags = list(self._pm.list_tags().keys())
        self._tag_cb["values"] = tags
        if tags and not self._tag_var.get():
            self._tag_var.set(tags[0])

    def _run(self) -> None:
        tag = self._tag_var.get()
        if not tag:
            messagebox.showerror("Error", "No tag selected.")
            return
        intent = ResolveIntent[self._intent_var.get()]
        self._tv.delete(*self._tv.get_children())

        for name, wf in PRESETS.items():
            steps_str = "  →  ".join(s.name for s in wf.steps)
            resolved, _ = self._pm.get_with_trace(tag, wf, intent=intent)
            ok = resolved is not None
            self._tv.insert("", tk.END, tags=("ok" if ok else "fail",), values=(
                name,
                steps_str,
                "✓" if ok else "✗",
                str(resolved) if resolved else "—",
            ))


# ── Application shell ─────────────────────────────────────────────────────────
class WaterfallTesterApp:
    def __init__(self, root: tk.Tk) -> None:
        _apply_theme(root)
        root.title("PathManager Waterfall Tester")
        root.geometry("1120x840")
        root.minsize(900, 680)

        pm = SingletonPathManager()

        # Header
        hdr = ttk.Frame(root, padding=(18, 12, 18, 0))
        hdr.pack(fill="x")
        ttk.Label(hdr, text="PathManager Waterfall Tester", style="Title.TLabel").pack(side="left")
        ttk.Label(hdr, text="— inspect how each waterfall preset resolves your files",
                  style="Dim.TLabel").pack(side="left", padx=(10, 0))
        ttk.Separator(root, orient="horizontal").pack(fill="x", padx=18, pady=(8, 0))

        # Notebook
        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=18, pady=10)

        config_tab = _ConfigTab(nb, pm)
        tags_tab   = _TagsTab(nb, pm)
        test_tab   = _TestTab(nb, pm, tags_tab)
        batch_tab  = _BatchTab(nb, pm)

        nb.add(config_tab, text="  ⚙  Config  ")
        nb.add(tags_tab,   text="  🏷  Tags  ")
        nb.add(test_tab,   text="  🔍  Test  ")
        nb.add(batch_tab,  text="  📊  Batch  ")

        # Sync dropdowns when switching tabs
        def _on_switch(_e: tk.Event) -> None:
            idx = nb.index(nb.select())
            if idx == 1:
                tags_tab.refresh()
            elif idx == 2:
                test_tab._refresh_tags()
            elif idx == 3:
                batch_tab._refresh_tags()

        nb.bind("<<NotebookTabChanged>>", _on_switch)


def main() -> None:
    root = tk.Tk()
    WaterfallTesterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
