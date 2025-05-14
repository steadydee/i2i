import streamlit as st
from typing import Dict, Any
from backend.graph import run_workflow
from utils.fields import render_fields

st.set_page_config(page_title="i2i demo")

prompt = st.text_input("What do you need?")

# Call the graph as soon as user hits Enter in the text box
if prompt and "event" not in st.session_state:
    st.session_state.event = run_workflow(prompt)

evt: Dict[str, Any] | None = st.session_state.get("event")
if not evt:
    st.stop()

match evt["ui_event"]:
    # ── dynamic form ────────────────────────────────────────────────
    case "form":
        with st.form("dynamic_form", clear_on_submit=True):
            answers = render_fields(evt["fields"])
            if st.form_submit_button("Submit"):
                st.session_state.event = run_workflow(prompt, answers)
                st.rerun()

    # ── download link ──────────────────────────────────────────────
    case "download_link":
        st.success("Document ready:")
        st.markdown(f"[Download]({evt['url']})")

    # ── plain text ────────────────────────────────────────────────
    case "text":
        st.write(evt.get("content", "(no content)"))

    case _:
        st.error(f"Unsupported ui_event: {evt['ui_event']}")
        st.json(evt)
