"""GUI tester for PathManager waterfalls.

Run as a script and use the UI to set a project root, register test tags,
choose a Waterfall preset and ResolveIntent, then inspect the resolved
path, WaterfallTrace, and sample file contents (or metadata).

Designed for manual testing: copy/move the test files (555.png, public_key.txt,
複製.xlsx) into different anchors (project data, exe inner, temp, etc.) and
observe how Waterfall locates them.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox

from isd_py_framework_sdk.path_manager import (
    SingletonPathManager,
    PathMode,
    Waterfall,
    ResolveIntent,
)


def _waterfall_presets() -> dict:
    """Return mapping name -> Waterfall preset available on Waterfall class."""
    presets = {}
    for name in dir(Waterfall):
        if name.isupper():
            val = getattr(Waterfall, name)
            if isinstance(val, Waterfall):
                presets[name] = val
    # Add a custom universal option
    presets["CUSTOM_UNIVERSAL"] = Waterfall.UNIVERSAL
    return presets


class GUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("PathManager Waterfall Tester")

        self.pm = SingletonPathManager()

        frm = ttk.Frame(root, padding=12)
        frm.grid(sticky="nsew")

        # Project root
        ttk.Label(frm, text="Project root (__file__ or dir):").grid(row=0, column=0, sticky="w")
        self.proj_entry = ttk.Entry(frm, width=60)
        self.proj_entry.grid(row=0, column=1, sticky="we")
        ttk.Button(frm, text="Browse...", command=self.browse_proj).grid(row=0, column=2)

        # App name
        ttk.Label(frm, text="App name (for USER_*):").grid(row=1, column=0, sticky="w")
        self.app_entry = ttk.Entry(frm)
        self.app_entry.insert(0, "TesterApp")
        self.app_entry.grid(row=1, column=1, sticky="we")

        # Stored paths for the three test files
        ttk.Label(frm, text="Stored path for PNG:").grid(row=2, column=0, sticky="w")
        self.png_entry = ttk.Entry(frm)
        self.png_entry.insert(0, "555.png")
        self.png_entry.grid(row=2, column=1, sticky="we")
        self.png_anchor = tk.StringVar(value=PathMode.PROJ_ABSOLUTE.name)
        ttk.OptionMenu(frm, self.png_anchor, self.png_anchor.get(), *[m.name for m in PathMode]).grid(row=2, column=2)

        ttk.Label(frm, text="Stored path for TXT:").grid(row=3, column=0, sticky="w")
        self.txt_entry = ttk.Entry(frm)
        self.txt_entry.insert(0, "public_key.txt")
        self.txt_entry.grid(row=3, column=1, sticky="we")
        self.txt_anchor = tk.StringVar(value=PathMode.PROJ_ABSOLUTE.name)
        ttk.OptionMenu(frm, self.txt_anchor, self.txt_anchor.get(), *[m.name for m in PathMode]).grid(row=3, column=2)

        ttk.Label(frm, text="Stored path for XLSX:").grid(row=4, column=0, sticky="w")
        self.xls_entry = ttk.Entry(frm)
        self.xls_entry.insert(0, "複製.xlsx")
        self.xls_entry.grid(row=4, column=1, sticky="we")
        self.xls_anchor = tk.StringVar(value=PathMode.PROJ_ABSOLUTE.name)
        ttk.OptionMenu(frm, self.xls_anchor, self.xls_anchor.get(), *[m.name for m in PathMode]).grid(row=4, column=2)

        # Waterfall selector
        ttk.Label(frm, text="Waterfall preset:").grid(row=5, column=0, sticky="w")
        self.presets = _waterfall_presets()
        self.preset_names = sorted(self.presets)
        self.preset_var = tk.StringVar(value=self.preset_names[0])
        ttk.OptionMenu(frm, self.preset_var, self.preset_names[0], *self.preset_names).grid(row=5, column=1, sticky="we")

        # Intent
        ttk.Label(frm, text="Intent:").grid(row=6, column=0, sticky="w")
        self.intent_var = tk.StringVar(value=ResolveIntent.READ.name)
        ttk.OptionMenu(frm, self.intent_var, ResolveIntent.READ.name, *[i.name for i in ResolveIntent]).grid(row=6, column=1, sticky="we")

        # Controls
        ttk.Button(frm, text="Register tags", command=self.register_tags).grid(row=7, column=0)
        ttk.Button(frm, text="Find PNG", command=lambda: self.find_and_show('png')).grid(row=7, column=1)
        ttk.Button(frm, text="Find TXT", command=lambda: self.find_and_show('txt')).grid(row=7, column=2)
        ttk.Button(frm, text="Find XLSX", command=lambda: self.find_and_show('xls')).grid(row=8, column=1)

        # Output area
        ttk.Label(frm, text="Trace & Result:").grid(row=9, column=0, sticky="w")
        self.output = scrolledtext.ScrolledText(frm, width=100, height=25)
        self.output.grid(row=10, column=0, columnspan=3, sticky="nsew")

        # Configure grid weights
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        frm.columnconfigure(1, weight=1)

    def browse_proj(self):
        d = filedialog.askdirectory(title="Select project root")
        if d:
            self.proj_entry.delete(0, tk.END)
            self.proj_entry.insert(0, d)

    def register_tags(self):
        proj = self.proj_entry.get().strip()
        if not proj:
            messagebox.showerror("Error", "Please set a project root first.")
            return
        try:
            self.pm.set_proj_root(proj)
        except Exception as e:
            messagebox.showerror("Error", f"set_proj_root failed: {e}")
            return
        self.pm.set_app_name(self.app_entry.get().strip() or "TesterApp")

        # Register tags with explicit anchors
        self.pm.register("test_png", self.png_entry.get().strip(), PathMode[self.png_anchor.get()])
        self.pm.register("test_txt", self.txt_entry.get().strip(), PathMode[self.txt_anchor.get()])
        self.pm.register("test_xls", self.xls_entry.get().strip(), PathMode[self.xls_anchor.get()])

        self.output.insert(tk.END, "Registered tags: test_png, test_txt, test_xls\n")
        self.output.see(tk.END)

    def find_and_show(self, typ: str) -> None:
        tag = {"png": "test_png", "txt": "test_txt", "xls": "test_xls"}[typ]
        preset = self.presets[self.preset_var.get()]
        intent = ResolveIntent[self.intent_var.get()]

        self.output.insert(tk.END, f"\n--- Finding {tag} using {self.preset_var.get()} (intent={intent.name}) ---\n")
        self.output.see(tk.END)

        path, trace = self.pm.get_with_trace(tag, preset, intent=intent)

        self.output.insert(tk.END, f"Resolved path: {path}\n")
        self.output.insert(tk.END, str(trace) + "\n")

        if path is None:
            self.output.insert(tk.END, "No path found.\n")
            return

        # Show file content / metadata when possible
        try:
            p = Path(path)
            if not p.exists():
                self.output.insert(tk.END, "Target path does not exist on disk.\n")
                return

            if p.suffix.lower() in (".txt", ".md", ".csv"):
                txt = p.read_text(encoding="utf-8", errors="replace")
                self.output.insert(tk.END, f"--- File content (first 2000 chars) ---\n{txt[:2000]}\n")
            elif p.suffix.lower() in (".png", ".gif"):
                # Try to display the image using Tkinter's PhotoImage
                try:
                    img = tk.PhotoImage(file=str(p))
                    win = tk.Toplevel(self.root)
                    win.title(p.name)
                    lbl = ttk.Label(win, image=img)
                    lbl.image = img
                    lbl.pack()
                    self.output.insert(tk.END, f"Displayed image in new window: {p}\n")
                except Exception as e:
                    self.output.insert(tk.END, f"Cannot display image: {e}\n")
            elif p.suffix.lower() in (".xlsx", ".xlsm", ".xltx"):
                # XLSX is a zip container — list members
                try:
                    with zipfile.ZipFile(p, "r") as z:
                        members = z.namelist()
                    self.output.insert(tk.END, f"XLSX members: {members}\n")
                except Exception as e:
                    self.output.insert(tk.END, f"Cannot inspect xlsx: {e}\n")
            else:
                # Generic: show file size and first bytes
                b = p.read_bytes()
                self.output.insert(tk.END, f"Binary file: {len(b)} bytes, head: {b[:64]!r}\n")

        except Exception as exc:
            self.output.insert(tk.END, f"Error reading file: {exc}\n")


def main():
    root = tk.Tk()
    GUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
