"""
Streamlit front-end for the i2i Assistant
"""

from __future__ import annotations
from typing import Dict, Any
import streamlit as st

from backend.graph import run_workflow, reload_graph

# ─── page config ────────────────────────────────────────────────────────
st.set_page_config(page_title="i2i Assistant", page_icon="🧠", layout="wide")
st.title("🧠  i2i Assistant")

with st.sidebar:
    st.header("Admin")
    if st.button("🔄 Reload processor registry"):
        reload_graph()
        st.success("Processor chains reloaded.")
    st.markdown(
        "<small>• Enter a plain-language request.<br>"
        "• If more info is needed, a form appears.<br>"
        "• Download links / answers render below.</small>",
        unsafe_allow_html=True,
    )

# ─── session init ───────────────────────────────────────────────────────
def _init():
    st.session_state.setdefault("phase", "prompt")          # prompt | form | result
    st.session_state.setdefault("prompt", "")
    st.session_state.setdefault("cached_prompt", "")
    st.session_state.setdefault("form_fields", [])
    st.session_state.setdefault("event", None)

_init()

# ─── prompt phase ───────────────────────────────────────────────────────
if st.session_state.phase == "prompt":
    st.subheader("Describe the task")
    st.text_input("e.g. Draft an SOW for Acme Corp", key="prompt")

    if st.button("▶︎ Run"):
        st.session_state.event = run_workflow(st.session_state.prompt, None)
        st.session_state.cached_prompt = st.session_state.prompt
        if st.session_state.event.get("type") == "form" or st.session_state.event.get("ui_event") == "form":
            st.session_state.form_fields = st.session_state.event["fields"]
            st.session_state.phase = "form"
        else:
            st.session_state.phase = "result"
        st.rerun()

# ─── form phase ─────────────────────────────────────────────────────────
elif st.session_state.phase == "form":
    st.subheader("Additional information required")

    with st.form("dynamic_form"):
        inputs: Dict[str, Any] = {}
        for spec in st.session_state.form_fields:
            name   = spec["name"]
            label  = spec.get("label", name.replace("_", " ").title())
            widget = spec.get("widget", "text_input")
            kwargs = spec.get("widget_kwargs", {})
            inputs[name] = getattr(st, widget)(label, **kwargs)
        submitted = st.form_submit_button("Submit")

    if submitted:
        st.session_state.event = run_workflow(st.session_state.cached_prompt, inputs)
        st.session_state.phase = "result"
        st.rerun()

# ─── result phase ───────────────────────────────────────────────────────
elif st.session_state.phase == "result":
    event = st.session_state.get("event", {})

    # accept either style: {'type': …} or {'ui_event': …}
    etype = event.get("type") or event.get("ui_event")

    if etype == "text":
        st.markdown(event.get("content", "*(empty)*"))

    elif etype == "download_link":
        if "file_bytes" in event:
            st.success("Document ready:")
            st.download_button(
                label="⬇️ Download",
                data=event["file_bytes"],
                file_name=event.get("file_name", "document.docx"),
            )
        elif "url" in event:
            st.success("Document ready:")
            st.link_button("⬇️ Download", url=event["url"])
        else:
            st.error("download_link event missing 'url' or 'file_bytes'")

    else:
        st.warning(f"Unhandled UI event: {event}")

    if st.button("↩︎ New request"):
        st.session_state.phase = "prompt"
        st.session_state.prompt = ""
        st.session_state.event = None
        st.rerun()
