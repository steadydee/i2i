def render_event():
    event = st.session_state.get('event')
    if not event:
        return

    output = event.get("output", event)
    evt_type = output.get("ui_event")

    if evt_type == "text" or not evt_type:
        st.markdown(output.get("content", str(output)))
        preview = output.get("preview")
        if preview and isinstance(preview, list):
            with st.expander("Show Source Chunks"):
                for i, chunk in enumerate(preview, 1):
                    st.markdown(f"**Chunk {i}:** {chunk.get('brief', '')}")
                    st.code(chunk.get("content", ""))
        return

    if evt_type == "download_link" and output.get("url"):
        st.download_button("Download", output["url"], key="download_sow")
        return

    if evt_type == "form":
        with st.form("dynamic_form"):
            answers = {}
            for field in output.get("fields", []):
                name = field.get("name")
                label = field.get("label", name.replace("_", " ").title())
                widget = field.get("widget", "text_input")
                if widget == "text_input":
                    answers[name] = st.text_input(label)
                elif widget == "selectbox":
                    answers[name] = st.selectbox(label, field.get("options", []))
                # ...add more widgets as needed...
            submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state['user_inputs'] = answers
            st.rerun()
        return

    st.write(output)
