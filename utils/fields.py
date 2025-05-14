"""
utils/fields.py
Generic field-renderer + simple validators for Streamlit forms.

Usage
-----
from utils.fields import render_fields
data, ok = render_fields(fields)   # `fields` is the manifest JSON list
if ok:
    ...  # every field valid, use `data`
"""

from __future__ import annotations
from typing import TypedDict, Any, Callable, Dict, List, Tuple
import streamlit as st


# ----------------------------------------------------------------------
# 1. Typed schema for one field (mirrors the manifest JSON)
# ----------------------------------------------------------------------
class Field(TypedDict, total=False):
    name: str
    label: str
    widget: str
    widget_kwargs: dict[str, Any]
    validators: list[str]


# ----------------------------------------------------------------------
# 2. Validator registry
#    Each validator gets the widget value and returns (bool, error_msg)
# ----------------------------------------------------------------------
def _non_empty(val: Any) -> Tuple[bool, str | None]:
    if val not in ("", None):
        return True, None
    return False, "Required"

def _positive_int(val: Any) -> Tuple[bool, str | None]:
    if isinstance(val, (int, float)) and val > 0:
        return True, None
    return False, "Must be > 0"

VALIDATORS: Dict[str, Callable[[Any], Tuple[bool, str | None]]] = {
    "non_empty": _non_empty,
    "positive_int": _positive_int,
}


# ----------------------------------------------------------------------
# 3. Main helper
# ----------------------------------------------------------------------
def render_fields(fields: List[Field]) -> Tuple[Dict[str, Any], bool]:
    """
    Draw each field’s widget.
    Returns (data, all_valid)
      • data is {name: value} for rendered fields
      • all_valid is True iff every field passed its validators
    Call inside a Streamlit context (e.g. inside st.form).
    """
    data: Dict[str, Any] = {}
    all_valid = True

    for fld in fields:
        key = fld["name"]
        label = fld.get("label", key)
        widget = fld.get("widget", "text_input")
        kwargs = fld.get("widget_kwargs", {})

        # ----- render widget -----
        if widget == "text_input":
            val = st.text_input(label, key=key, **kwargs)
        elif widget == "number_input":
            val = st.number_input(label, key=key, **kwargs)
        else:
            st.warning(f"Unsupported widget: {widget}")
            val = None

        data[key] = val

        # ----- validate -----
        for vname in fld.get("validators", ["non_empty"]):
            ok, err = VALIDATORS[vname](val)
            if not ok:
                all_valid = False
                st.caption(f":red[{err}]")
                break  # stop at first error

    return data, all_valid
