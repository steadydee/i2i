#!/usr/bin/env python3
"""
Streamlit front-end for i2i
───────────────────────────
• Single prompt box (“Describe the task …”)  
• Calls `backend.graph.run_workflow()`  
• Renders the `ui_event` it returns.  
• Shows an optional debug panel with retrieved chunks.
"""
from __future__ import annotations

import os
import streamlit as st

from backend.graph import run_workflow

st.set_page_config(page_title="🧠  i2i Assistant", layout="centered")

# ─────────────────────────  UI: prompt  ────────────────────────────
st.title("🧠  i2i Assistant")

with st.form("ask_form"):
    prompt = st.text_input(
        "Describe the task",
        placeholder="e.g. Draft an SOW for Acme Corp",
        value=st.session_state.get("prompt", ""),
    )
    submitted = st.form_submit_button("Run")

if submitted and prompt.strip():
    st.session_state.prompt = prompt.strip()
    st.session_state.event  = run_workflow(st.session_state.prompt, None)

# ─────────────────────────  UI: render event  ───────────────────────
event = st.session_state.get("event")
if event:
    if event.get("ui_event") == "text":
        st.markdown(event["content"])
    elif event.get("ui_event") == "download_link":
        st.success("Your document is ready:")
        st.markdown(f"[Download]({event['content']})")
    else:
        st.write(event)

    # ── Debug: chunk preview (if present) ──────────────────────────
    dbg = event.get("debug", {})
    if dbg.get("preview"):
        st.divider()
        st.subheader("🔍 Retrieved chunks")
        for ch in dbg["preview"]:
            label = f"{ch['sim']:.3f} · {ch['doc_id']}"
            with st.expander(label):
                st.write(ch["content"])

# ─────────────────────────  footer  ────────────────────────────────
st.caption("v0.1 · TENANT: " + os.getenv("TENANT_ID", "default"))
