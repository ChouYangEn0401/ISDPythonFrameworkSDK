"""
hyper_framework.helpers.assertions — All assertion utilities.
"""


# ── Type assertions ───────────────────────────────────────────────────────
from .type_assertions import (
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
    
    assert__is_dict_of_str_to_str,

    assert__is_list_of_list_of_str,
    assert__is_list_of_tuple_of_str,
)

# ── Value assertions ─────────────────────────────────────────────────────
from .value_assertions import (
    assert__is_positive,
    assert__is_non_negative,
    assert__is_not_empty,
    assert__in_range,
    assert__is_one_of,
    assert__matches_pattern,
)

# ── Collection assertions ────────────────────────────────────────────────
from .collection_assertions import (
    assert__has_length,
    assert__min_length,
    assert__max_length,
    assert__all_keys_exist,
    assert__is_unique,
    assert__no_none_values,
    # contains helpers
    assert__contains_in_list,
    assert__contains_in_str,
    assert__contains_in_dataclass,
    assert__contains_in_object,
)

__all__ = [
    # legacy
    "assert__is_str",
    "assert__is_list_of_str",
    "assert__is_list_of_list_of_str",
    "assert__is_list_of_tuple_of_str",
    # type
    "assert__is_int",
    "assert__is_float",
    "assert__is_number",
    "assert__is_bool",
    "assert__is_dict",
    "assert__is_list",
    "assert__is_tuple",
    "assert__is_set",
    "assert__is_callable",
    "assert__is_none",
    "assert__is_not_none",
    "assert__is_instance",
    "assert__is_subclass",
    "assert__is_list_of_int",
    "assert__is_list_of_float",
    "assert__is_list_of_number",
    "assert__is_dict_of_str_to_str",
    # value
    "assert__is_positive",
    "assert__is_non_negative",
    "assert__is_not_empty",
    "assert__in_range",
    "assert__is_one_of",
    "assert__matches_pattern",
    # collection
    "assert__has_length",
    "assert__min_length",
    "assert__max_length",
    "assert__all_keys_exist",
    "assert__is_unique",
    "assert__no_none_values",
    # contains
    "assert__contains_in_list",
    "assert__contains_in_str",
    "assert__contains_in_dataclass",
    "assert__contains_in_object",
]
