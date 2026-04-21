"""
file_compare._shared
─────────────────────
Shared colour constants and helpers for all file-comparison modules.
"""
from dataclasses import dataclass, field as _dataclass_field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class CompareResult:
    """Result of a single file-comparison call.

    Behaves as ``bool`` for backward-compatibility::

        if compare_csv_files(cfg):   # still works
            ...
    """
    label: str
    passed: bool
    errors: list = _dataclass_field(default_factory=list)

    def __bool__(self) -> bool:
        return self.passed

    def __repr__(self) -> str:
        status = "PASS" if self.passed else f"FAIL({len(self.errors)} errors)"
        return f"CompareResult({self.label!r}, {status})"


# ── ANSI colour codes ────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
PURPLE = "\033[95m"
BOLD   = "\033[1m"


def colorize_diff(actual: Any, expected: Any) -> str:
    """Color-format a 'got / expected' pair."""
    return (
        f"{YELLOW}得到{RESET} {actual} | "
        f"{CYAN}預期{RESET} {expected}"
    )


# ── row-based mask helper ────────────────────────────────────────────────
def resolve_row_mask(
    total_rows: int,
    mask: Optional[Dict[str, Any]] = None,
) -> Set[int]:
    """
    Return the set of **1-indexed** row numbers that should be checked.

    mask keys (all optional):
      include_rows : list[int]  – only check these rows
      exclude_rows : list[int]  – skip these rows

    If *mask* is ``None`` or empty, all rows ``1 … total_rows`` are included.
    """
    if not mask:
        return set(range(1, total_rows + 1))

    include = mask.get("include_rows")
    exclude = mask.get("exclude_rows")

    rows = set(include) if include is not None else set(range(1, total_rows + 1))
    if exclude:
        rows -= set(exclude)
    return rows


# ── deep-compare for tree structures (JSON / YAML / TOML) ───────────────
def deep_compare(
    actual: Any,
    expected: Any,
    path: str = "$",
    errors: Optional[List[Tuple]] = None,
    exclude_paths: Optional[Set[str]] = None,
    include_paths: Optional[Set[str]] = None,
) -> List[Tuple[str, str, Any, Any]]:
    """Recursively compare two nested structures (dict / list / scalar).

    Returns a list of ``(path, description, actual_repr, expected_repr)``.
    """
    if errors is None:
        errors = []

    # ── path masking ──
    if exclude_paths:
        for ep in exclude_paths:
            if path == ep or path.startswith(ep + ".") or path.startswith(ep + "["):
                return errors

    if include_paths:
        if not any(
            path.startswith(ip) or ip.startswith(path)
            for ip in include_paths
        ):
            return errors

    # ── bool first (bool is a subclass of int; must check before numeric) ──
    if isinstance(actual, bool) or isinstance(expected, bool):
        if type(actual) is not type(expected):
            errors.append((path, "型別不同", type(actual).__name__, type(expected).__name__))
        elif actual != expected:
            errors.append((path, "值不同", repr(actual), repr(expected)))
        return errors

    # ── numeric coercion: int and float are compared by value, not by type ──
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        if actual != expected:
            errors.append((path, "值不同", repr(actual), repr(expected)))
        return errors

    # ── other type mismatches ──
    if type(actual) is not type(expected):
        errors.append((path, "型別不同", type(actual).__name__, type(expected).__name__))
        return errors

    # ── dict ──
    if isinstance(expected, dict):
        for key in sorted(set(list(actual.keys()) + list(expected.keys())), key=str):
            child = f"{path}.{key}"
            if key not in actual:
                errors.append((child, "缺少 key", "（缺失）", repr(expected[key])))
            elif key not in expected:
                errors.append((child, "多餘 key", repr(actual[key]), "（無）"))
            else:
                deep_compare(actual[key], expected[key], child, errors, exclude_paths, include_paths)

    # ── list ──
    elif isinstance(expected, list):
        min_len = min(len(actual), len(expected))
        if len(actual) != len(expected):
            errors.append((path, "長度不同", len(actual), len(expected)))
        for i in range(min_len):
            deep_compare(actual[i], expected[i], f"{path}[{i}]", errors, exclude_paths, include_paths)
        # enumerate extra items in actual (target has more)
        for i in range(min_len, len(actual)):
            errors.append((f"{path}[{i}]", "多餘項目", repr(actual[i]), "（無）"))
        # enumerate missing items (bench has more)
        for i in range(min_len, len(expected)):
            errors.append((f"{path}[{i}]", "缺少項目", "（缺失）", repr(expected[i])))

    # ── scalar ──
    else:
        if actual != expected:
            errors.append((path, "值不同", repr(actual), repr(expected)))

    return errors


# ── output helpers ───────────────────────────────────────────────────────
def print_compare_header(fmt: str, target: str, bench: str):
    print(f"\n{CYAN}[{fmt}] 開始對照測試...{RESET}")
    print(f"   待測檔: {target}")
    print(f"   標準檔: {bench}\n")


def print_test_result(label: str, errors: list, *, max_display: int = 15) -> "CompareResult":
    """Print coloured pass / fail summary and return a :class:`CompareResult`."""
    if not errors:
        print(f"  {GREEN}✓ PASS{RESET} {label}")
        return CompareResult(label=label, passed=True, errors=[])

    print(f"  {RED}✗ FAILED ({len(errors)} 個錯誤){RESET} {label}")
    for err in errors[:max_display]:
        if isinstance(err, tuple) and len(err) == 4:
            path, desc, actual, expected = err
            print(f"    - [{path}] {desc}: {colorize_diff(actual, expected)}")
        else:
            print(f"    - {err}")
    if len(errors) > max_display:
        print(f"    ... 以及其餘 {len(errors) - max_display} 個錯誤")
    return CompareResult(label=label, passed=False, errors=errors)
