"""
examples/path_manager/quickstart.py
===================================
Smoke test + end-to-end demo of path_manager's ergonomics layer: bulk
registration, dict-style access, and the simplified waterfall.  Every demo
asserts the result, so running this file doubles as a quick smoke test:

Run:
    .venv\\Scripts\\python.exe examples/path_manager/quickstart.py

No optional dependencies required (path_manager is pure-stdlib).
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from isd_py_framework_sdk.path_manager import (
    SingletonPathManager,
    PathMode,
    Waterfall,
    ResolveIntent,
)
from isd_py_framework_sdk.path_manager._meta import SingletonABCMeta


def _fresh() -> SingletonPathManager:
    """Evict the singleton so this demo starts from a clean registry."""
    SingletonABCMeta._instances.pop(SingletonPathManager, None)
    return SingletonPathManager()


def demo_register_many():
    print("\n=== 1) register_many: one shared anchor, no repeated PathMode ===")
    pm = _fresh()
    proj = Path(tempfile.mkdtemp())
    pm.set_proj_root(str(proj))

    pm.register_many(
        {
            "data_in":   "data/inputs",
            "data_out":  "data/outputs",
            "error_log": "logs/error.log",
        },
        anchor=PathMode.PROJ_ABSOLUTE,
        descriptions={"data_in": "raw input files"},
    )

    assert pm.get("data_in") == (proj / "data/inputs").resolve()
    assert pm.list_tags()["data_in"] == "raw input files"
    assert pm.list_tags()["data_out"] == ""  # omitted description -> empty
    print("registered 3 tags in one call; data_in ->", pm.get("data_in"))

    # A typo in descriptions is caught early.
    try:
        pm.register_many({"a": "x"}, anchor=PathMode.CWD, descriptions={"typo": "!"})
    except KeyError as exc:
        print("typo in descriptions correctly rejected:", exc)


def demo_mapping_sugar():
    print("\n=== 2) Mapping-style sugar: pm[tag], in, len, iter ===")
    pm = _fresh()
    pm.set_proj_root(str(Path(tempfile.mkdtemp())))
    pm.register_many({"a": "data/a", "b": "data/b"}, anchor=PathMode.PROJ_ABSOLUTE)

    assert pm["a"] == pm.get("a")
    assert "a" in pm and "ghost" not in pm
    assert 123 not in pm  # non-string membership is False, never raises
    assert len(pm) == 2
    assert set(pm) == {"a", "b"}
    print('pm["a"] =', pm["a"])
    print('"a" in pm =', "a" in pm, "| len(pm) =", len(pm), "| tags =", sorted(pm))


def demo_simple_waterfall():
    print("\n=== 3) Waterfall without constructing Waterfall(...) ===")
    pm = _fresh()
    proj = Path(tempfile.mkdtemp())
    pm.set_proj_root(str(proj))

    # File only exists under SYSTEM_TEMP, not under the project root.
    pm.register("cfg", "", PathMode.SYSTEM_TEMP)

    # Pass a plain list of modes — coerced to a Waterfall internally.
    via_list = pm.get("cfg", [PathMode.PROJ_ABSOLUTE, PathMode.SYSTEM_TEMP])
    via_obj = pm.get("cfg", Waterfall(PathMode.PROJ_ABSOLUTE, PathMode.SYSTEM_TEMP))
    assert via_list == via_obj
    print("list form == Waterfall(...) form:", via_list)

    # A single PathMode works too.
    assert pm.get("cfg", PathMode.SYSTEM_TEMP).exists()

    # WRITE intent + trace, list form.
    pm.register("report", "outputs/result.xlsx", PathMode.PROJ_ABSOLUTE)
    path, trace = pm.get_with_trace(
        "report",
        [PathMode.PROJ_ABSOLUTE, PathMode.SYSTEM_TEMP],
        intent=ResolveIntent.WRITE,
    )
    assert path is not None and trace.succeeded
    print("WRITE-intent waterfall resolved to:", path)

    # Bad inputs raise a friendly TypeError.
    for bad in ([], ["not_a_mode"]):
        try:
            pm.get("cfg", bad)
        except TypeError as exc:
            print(f"rejected {bad!r}:", exc)


if __name__ == "__main__":
    demo_register_many()
    demo_mapping_sugar()
    demo_simple_waterfall()
    print("\nAll path_manager smoke checks passed.")
