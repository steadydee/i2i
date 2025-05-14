import streamlit as st
from backend.graph import run_workflow
from utils.fields import render_fields          # generic field renderer

st.title("i2i demo")

# ───────────────── session helpers ────────────────────────
state = st.session_state
state.setdefault("prompt", "")
state.setdefault("event", None)    # last workflow response

# ─────────────────── one-button form ──────────────────────
with st.form("main"):
    state.prompt = st.text_input("What do you need?", value=state.prompt)

    extra_data = {}
    valid = True
    evt = state.event
    if evt and evt["ui_event"] == "form":
        extra_data, valid = render_fields(evt["fields"])

    submitted = st.form_submit_button("Submit")

# ─────────────── handle Submit click(s) ───────────────────
if submitted:
    # 1st click – only prompt exists
    if evt is None or evt["ui_event"] != "form":
        state.event = run_workflow(state.prompt)
        st.rerun()

    # 2nd click – prompt + form data
    elif valid:
        state.event = run_workflow(state.prompt, extra_data)
        st.rerun()

# ─────────────────── final output ─────────────────────────
evt = state.event
if evt and evt["ui_event"] == "download_link":
    st.markdown(f"[Download the document]({evt['url']})", unsafe_allow_html=True)
    if st.button("🔄 Start over"):
        state.clear()
        st.rerun()

elif evt and evt["ui_event"] == "text":
    st.write(evt["content"])
    if st.button("🔄 Start over"):
        state.clear()
        st.rerun()
