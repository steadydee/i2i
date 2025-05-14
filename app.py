import streamlit as st
from backend.graph import run_workflow

st.set_page_config(page_title="i2i demo")

# ── persistent UI state ─────────────────────────────────────────────
if "pending_fields" not in st.session_state:
    st.session_state.pending_fields = None
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = ""

st.title("i2i demo")

# ── 1️⃣  prompt stage ────────────────────────────────────────────────
if st.session_state.pending_fields is None:
    prompt = st.text_input("What do you need?")
    if st.button("Send") and prompt:
        st.session_state.last_prompt = prompt
        event = run_workflow(prompt)

        if event["ui_event"] == "form":
            st.session_state.pending_fields = event["fields"]
            st.rerun()

        elif event["ui_event"] == "text":
            st.markdown(event["content"])

        elif event["ui_event"] == "download_link":
            st.markdown(f"[Download the document]({event['url']})")

# ── 2️⃣  dynamic form stage ──────────────────────────────────────────
else:
    st.subheader("Please provide a few details:")
    with st.form("dynamic_form"):
        inputs: dict[str, object] = {}
        for fld in st.session_state.pending_fields:
            name   = fld["name"]
            label  = fld.get("label", name.replace("_", " ").title())
            widget = fld["widget"]

            if widget == "text_input":
                inputs[name] = st.text_input(label)

            elif widget == "number_input":
                kwargs = fld.get("widget_kwargs", {})
                inputs[name] = st.number_input(label, **kwargs)

        submitted = st.form_submit_button("Submit")

    if submitted:
        event = run_workflow(
            st.session_state.last_prompt,
            form_data=inputs,
        )

        # ── DEBUG ──────────────────────────────────────────────────
        st.write("DEBUG event:", event)

        st.session_state.pending_fields = None

        if event["ui_event"] == "text":
            st.markdown(event["content"])

        elif event["ui_event"] == "download_link":
            st.markdown(f"[Download the document]({event['url']})")
