"""
Quick smoke-test for helpers/assertions
Run: python src/isd_py_framework_sdk/helpers/assertions/_test.py
"""

import sys
import traceback

sys.path.insert(0, "src")

from isd_py_framework_sdk.assertions import (
    # type
    assert__is_str,
    assert__is_int,
    assert__is_float,
    assert__is_number,
    assert__is_bool,
    assert__is_dict,
    assert__is_list,
    assert__is_tuple,
    assert__is_set,
    assert__is_callable,
    assert__is_none,
    assert__is_not_none,
    assert__is_instance,
    assert__is_subclass,
    assert__is_list_of_str,
    assert__is_list_of_int,
    assert__is_list_of_float,
    assert__is_list_of_number,
    assert__is_list_of_list_of_str,
    assert__is_list_of_tuple_of_str,
    assert__is_dict_of_str_to_str,
    # value
    assert__is_positive,
    assert__is_non_negative,
    assert__is_not_empty,
    assert__in_range,
    assert__is_one_of,
    assert__matches_pattern,
    # collection
    assert__has_length,
    assert__min_length,
    assert__max_length,
    assert__all_keys_exist,
    assert__is_unique,
    assert__no_none_values,
    assert__contains_in_list,
    assert__contains_in_str,
    assert__contains_in_dataclass,
    assert__contains_in_object,
)

PASS = 0
FAIL = 0


def ok(label: str):
    global PASS
    PASS += 1
    print(f"  ✔  {label}")


def fail(label: str, exc: Exception):
    global FAIL
    FAIL += 1
    print(f"  ✘  {label}  →  {type(exc).__name__}: {exc}")


def expect_pass(label: str, fn):
    try:
        fn()
        ok(label)
    except Exception as e:
        fail(label, e)


def expect_fail(label: str, fn, exc_type=Exception):
    try:
        fn()
        fail(label, Exception("no exception raised"))
    except exc_type:
        ok(label)
    except Exception as e:
        fail(label, e)


# ──────────────────────────────────────────────────────────────────────────────
print("\n── Type Assertions ──────────────────────────────────────────────────────")

expect_pass("is_str: 'hello'",              lambda: assert__is_str("hello"))
expect_fail("is_str: 123 → TypeError",      lambda: assert__is_str(123), TypeError)

expect_pass("is_int: 42",                   lambda: assert__is_int(42))
expect_fail("is_int: True → TypeError",     lambda: assert__is_int(True), TypeError)
expect_fail("is_int: 3.14 → TypeError",     lambda: assert__is_int(3.14), TypeError)

expect_pass("is_float: 3.14",               lambda: assert__is_float(3.14))
expect_fail("is_float: 1 → TypeError",      lambda: assert__is_float(1), TypeError)

expect_pass("is_number: 5",                 lambda: assert__is_number(5))
expect_pass("is_number: 5.0",               lambda: assert__is_number(5.0))
expect_fail("is_number: True → TypeError",  lambda: assert__is_number(True), TypeError)

expect_pass("is_bool: True",                lambda: assert__is_bool(True))
expect_fail("is_bool: 1 → TypeError",       lambda: assert__is_bool(1), TypeError)

expect_pass("is_dict: {}",                  lambda: assert__is_dict({}))
expect_pass("is_list: []",                  lambda: assert__is_list([]))
expect_pass("is_tuple: ()",                 lambda: assert__is_tuple(()))
expect_pass("is_set: set()",               lambda: assert__is_set(set()))

expect_pass("is_callable: print",           lambda: assert__is_callable(print))
expect_fail("is_callable: 42 → TypeError",  lambda: assert__is_callable(42), TypeError)

expect_pass("is_none: None",                lambda: assert__is_none(None))
expect_fail("is_none: 0 → TypeError",       lambda: assert__is_none(0), TypeError)

expect_pass("is_not_none: 0",               lambda: assert__is_not_none(0))
expect_fail("is_not_none: None → TypeError",lambda: assert__is_not_none(None), TypeError)

expect_pass("is_instance: 1 int",           lambda: assert__is_instance(1, int))
expect_fail("is_instance: '1' int",         lambda: assert__is_instance("1", int), TypeError)

expect_pass("is_subclass: bool→int",        lambda: assert__is_subclass(bool, int))
expect_fail("is_subclass: str→int",         lambda: assert__is_subclass(str, int), TypeError)

expect_pass("list_of_str: ['a','b']",       lambda: assert__is_list_of_str(["a", "b"]))
expect_fail("list_of_str: [1] → TypeError", lambda: assert__is_list_of_str([1]), TypeError)

expect_pass("list_of_int: [1,2]",           lambda: assert__is_list_of_int([1, 2]))
expect_pass("list_of_float: [1.0]",         lambda: assert__is_list_of_float([1.0]))
expect_pass("list_of_number: [1,2.0]",      lambda: assert__is_list_of_number([1, 2.0]))

expect_pass("list_of_list_of_str: [['a']]", lambda: assert__is_list_of_list_of_str([["a"]]))
expect_pass("list_of_tuple_of_str: [('a',)]",lambda: assert__is_list_of_tuple_of_str([("a",)]))
expect_pass("dict_str_to_str: {'a':'b'}",   lambda: assert__is_dict_of_str_to_str({"a": "b"}))

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Value Assertions ─────────────────────────────────────────────────────")

expect_pass("is_positive: 1",               lambda: assert__is_positive(1))
expect_pass("is_positive: 0.001",           lambda: assert__is_positive(0.001))
expect_fail("is_positive: 0 → ValueError",  lambda: assert__is_positive(0), ValueError)
expect_fail("is_positive: -1 → ValueError", lambda: assert__is_positive(-1), ValueError)

expect_pass("is_non_negative: 0",           lambda: assert__is_non_negative(0))
expect_fail("is_non_negative: -1 →ValueError",lambda: assert__is_non_negative(-1), ValueError)

expect_pass("is_not_empty: 'abc'",          lambda: assert__is_not_empty("abc"))
expect_pass("is_not_empty: [1]",            lambda: assert__is_not_empty([1]))
expect_fail("is_not_empty: '' → ValueError",lambda: assert__is_not_empty(""), ValueError)
expect_fail("is_not_empty: [] → ValueError",lambda: assert__is_not_empty([]), ValueError)
expect_fail("is_not_empty: None → ValueError",lambda: assert__is_not_empty(None), ValueError)

expect_pass("in_range: 5 [1,10]",           lambda: assert__in_range(5, 1, 10))
expect_pass("in_range: 1 [1,10] inclusive", lambda: assert__in_range(1, 1, 10))
expect_fail("in_range: 0 [1,10] → ValueError",lambda: assert__in_range(0, 1, 10), ValueError)
expect_fail("in_range: 1 excl → ValueError",lambda: assert__in_range(1, 1, 10, inclusive=False), ValueError)

expect_pass("is_one_of: 'a' in list",       lambda: assert__is_one_of("a", ["a", "b"]))
expect_fail("is_one_of: 'c' not in list",   lambda: assert__is_one_of("c", ["a", "b"]), ValueError)

expect_pass("matches_pattern: 'abc-123'",   lambda: assert__matches_pattern("abc-123", r"[a-z]+-\d+"))
expect_fail("matches_pattern: 'ABC-123'",   lambda: assert__matches_pattern("ABC-123", r"[a-z]+-\d+"), ValueError)

# ──────────────────────────────────────────────────────────────────────────────
print("\n── Collection Assertions ────────────────────────────────────────────────")

expect_pass("has_length: [1,2] len=2",      lambda: assert__has_length([1, 2], 2))
expect_fail("has_length: [1] len=2 →ValueError",lambda: assert__has_length([1], 2), ValueError)

expect_pass("min_length: [1,2] min=1",      lambda: assert__min_length([1, 2], 1))
expect_fail("min_length: [] min=1 →ValueError",lambda: assert__min_length([], 1), ValueError)

expect_pass("max_length: [1] max=3",        lambda: assert__max_length([1], 3))
expect_fail("max_length: [1,2,3,4] max=2",  lambda: assert__max_length([1, 2, 3, 4], 2), ValueError)

expect_pass("all_keys_exist: a,b in dict",  lambda: assert__all_keys_exist({"a": 1, "b": 2}, ["a", "b"]))
expect_fail("all_keys_exist: c missing",    lambda: assert__all_keys_exist({"a": 1}, ["a", "c"]), KeyError)

expect_pass("is_unique: [1,2,3]",           lambda: assert__is_unique([1, 2, 3]))
expect_fail("is_unique: [1,1,2] →ValueError",lambda: assert__is_unique([1, 1, 2]), ValueError)

expect_pass("no_none_values: [1,2]",        lambda: assert__no_none_values([1, 2]))
expect_fail("no_none_values: [1,None]",     lambda: assert__no_none_values([1, None]), ValueError)
expect_pass("no_none_values dict: {a:1}",   lambda: assert__no_none_values({"a": 1}))
expect_fail("no_none_values dict: {a:None}",lambda: assert__no_none_values({"a": None}), ValueError)

expect_pass("contains_in_list: 2 in [1,2]", lambda: assert__contains_in_list([1, 2], 2))
expect_fail("contains_in_list: 5 missing",  lambda: assert__contains_in_list([1, 2], 5), ValueError)

expect_pass("contains_in_str: 'bc' in 'abc'",lambda: assert__contains_in_str("abc", "bc"))
expect_fail("contains_in_str: 'xyz' missing",lambda: assert__contains_in_str("abc", "xyz"), ValueError)


from dataclasses import dataclass

@dataclass
class _DC:
    name: str
    value: int

expect_pass("contains_in_dataclass: has attr 'name'", lambda: assert__contains_in_dataclass(_DC("x", 1), "name"))
expect_fail("contains_in_dataclass: no attr 'missing'",lambda: assert__contains_in_dataclass(_DC("x", 1), "missing"), AttributeError)


class _Obj:
    foo = 42

expect_pass("contains_in_object: has attr 'foo'", lambda: assert__contains_in_object(_Obj(), "foo"))
expect_fail("contains_in_object: no attr 'bar'",  lambda: assert__contains_in_object(_Obj(), "bar"), AttributeError)

# ──────────────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  結果：{PASS} PASS  /  {FAIL} FAIL")
if FAIL:
    print("  ⚠  有測試失敗，請檢查上方輸出。")
else:
    print("  🎉 全部通過！")
print('='*60)
