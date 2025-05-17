"""
Dynamic form-field renderer for Streamlit

• Accepts a list of field-spec dicts (task_manifest.required_fields)
• Returns a dict {name: value} for every rendered widget
"""

from typing import List, Dict, Any
import streamlit as st


# ---------- widget helpers --------------------------------------------------
def _number(label: str, **kw):
    return st.number_input(label, **kw)


def _text(label: str, **kw):
    return st.text_input(label, **kw)


def _selectbox(label: str, **kw):
    # task_manifest stores options inside widget_kwargs
    options = kw.pop("options", [])
    return st.selectbox(label, options, **kw)


_WIDGETS = {
    "number_input": _number,
    "text_input":   _text,
    "selectbox":    _selectbox,
}


# ---------- main render function -------------------------------------------
def render_fields(fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Render widgets and return their values keyed by field.name."""
    answers: Dict[str, Any] = {}

    for fld in fields:
        name  = fld["name"]
        label = fld.get("label", name)
        wtype = fld["widget"]
        wargs = fld.get("widget_kwargs", {})

        widget_fn = _WIDGETS.get(wtype)
        if widget_fn is None:
            st.warning(f"Unsupported widget: {wtype}")
            continue

        answers[name] = widget_fn(label, key=name, **wargs)

    return answers
