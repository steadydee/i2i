"""
Front-end for the i2i assistant – compact top-of-page form, no bottom gap.
"""

import textwrap
from typing import Any, Dict

import streamlit as st
from backend.graph import run_workflow

# ─────────────────────────── UI skeleton ────────────────────────────────
st.set_page_config(page_title="🧠 i2i Assistant", page_icon="🧠")
st.markdown("## 🧠 i2i Assistant")
st.caption("Ask a question about the handbook, draft a SOW, etc.")

# ─────────────────────────── prompt form ────────────────────────────────
with st.form(key="prompt_form"):
    prompt = st.text_input("Describe the task", key="prompt")
    submitted = st.form_submit_button("Run")

if not submitted or not prompt.strip():
    st.stop()

# any answers from previous dynamic forms
answers: Dict[str, Any] | None = st.session_state.pop("form_answers", None)

# ─────────────────────────── run graph ──────────────────────────────────
result: Dict[str, Any] = run_workflow(prompt, answers)
evt = result.get("ui_event")

# ─────────────────────────── dispatcher ─────────────────────────────────
if evt == "text":
    st.markdown(result["content"])

elif evt == "download_link":
    if "file_bytes" in result:
        st.download_button("Download",
                           data=result["file_bytes"],
                           file_name=result.get("file_name", "file.bin"))
    else:
        st.markdown(f"[Download]({result['url']})")

elif evt == "form":
    with st.form(key="dynamic_form"):
        out: Dict[str, Any] = {}
        for fld in result["fields"]:
            w = fld["widget"]
            if w == "text_input":
                out[fld["name"]] = st.text_input(fld["label"])
            elif w == "selectbox":
                out[fld["name"]] = st.selectbox(fld["label"], fld["options"])
            elif w == "number_input":
                out[fld["name"]] = st.number_input(fld["label"], step=1)
            else:
                st.warning(f"Unknown widget: {w}")
        if st.form_submit_button("Submit"):
            st.session_state.form_answers = out
            st.rerun()
else:
    st.error(f"Unknown ui_event: {evt}")
    st.stop()

# ─────────────────────────── chunk preview ──────────────────────────────
if "preview" in result:
    st.divider()
    st.subheader("🔍 Retrieved chunks")
    for ch in result["preview"]:
        label = f"{ch['sim']:.3f} · {ch['doc_id']}"
        with st.expander(label):
            st.write(ch["brief"])
            st.markdown("---")
            st.write(ch["full"])
