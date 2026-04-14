"""
unitest_structure._shared
─────────────────────────
Shared colour constants and helpers for all file-comparison modules.
"""
from typing import Any, Dict, List, Optional, Set, Tuple


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

    # ── type mismatch ──
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
        if len(actual) != len(expected):
            errors.append((path, "長度不同", len(actual), len(expected)))
        for i in range(min(len(actual), len(expected))):
            deep_compare(actual[i], expected[i], f"{path}[{i}]", errors, exclude_paths, include_paths)

    # ── scalar ──
    else:
        if actual != expected:
            errors.append((path, "值不同", repr(actual), repr(expected)))

    return errors


# ── output helpers ───────────────────────────────────────────────────────
def print_compare_header(fmt: str, target: str, bench: str):
    print(f"\n🚀 {CYAN}開始 {fmt} 對照測試...{RESET}")
    print(f"   待測檔: {target}")
    print(f"   標準檔: {bench}\n")


def print_test_result(label: str, errors: list, *, max_display: int = 10) -> bool:
    """Print coloured pass / fail summary.  Returns ``True`` on pass."""
    if not errors:
        print(f"  {GREEN}✓ PASS{RESET} {label}")
        return True

    print(f"  {RED}✗ FAILED ({len(errors)} 個錯誤){RESET} {label}")
    for err in errors[:max_display]:
        if isinstance(err, tuple) and len(err) == 4:
            path, desc, actual, expected = err
            print(f"    - [{path}] {desc}: {colorize_diff(actual, expected)}")
        else:
            print(f"    - {err}")
    if len(errors) > max_display:
        print(f"    ... 以及其餘 {len(errors) - max_display} 個錯誤")
    return False
