from __future__ import annotations
import streamlit as st
from typing import Any, Dict

from backend.graph import run_workflow
from backend.wizard import (
    wizard_create_draft,
    wizard_update_fields,
    wizard_publish,
)

TENANT = "default"


# ── helpers --------------------------------------------------------------------

def _rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()


def _ss(key: str, default=None):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def _intent_search(q: str) -> Dict[str, Any]:
    return run_workflow(q, tenant=TENANT)


# ── router: dashboard vs wizard ------------------------------------------------

step = _ss("wizard_step", None)

# ---------- Dashboard ----------------------------------------------------------
if step is None:
    st.title("🧠  i2i Assistant")

    with st.form("intent"):
        q = st.text_input("Describe the task", key="dash_q")
        if st.form_submit_button("Run") and q.strip():
            payload = _intent_search(q.strip())
            if payload["ui_event"] == "wizard_offer":
                st.session_state.update(
                    wizard_step="intro",
                    wizard_goal="",
                    wizard_desc=payload["goal"],
                    wizard_draft=None,
                )
                _rerun()
            else:
                st.divider()
                st.write("**↘ Render task UI here – unchanged**")
                st.json(payload, expanded=False)

    if st.button("Create New Workflow (Wizard)", type="primary"):
        st.session_state.update(
            wizard_step="intro",
            wizard_goal="",
            wizard_desc="",
            wizard_draft=None,
        )
        _rerun()

    st.markdown("### v0.8 · TENANT: default")
    st.stop()

# ---------- Wizard screens -----------------------------------------------------

# Welcome
if step == "intro":
    st.header("✨ Workflow Wizard – welcome")
    desc_prefill = _ss("wizard_desc", "")
    if desc_prefill:
        st.info(f"Nothing matched **“{desc_prefill}”**. Let’s build it!")
    st.markdown("#### Choose what you’d like to build:")
    c1, c2 = st.columns(2, gap="large")
    if c1.button("Create a Task", use_container_width=True):
        st.session_state["wizard_step"] = "describe"
        _rerun()
    c2.button("Create a Workflow (soon)", disabled=True, use_container_width=True)
    st.stop()

# Describe
if step == "describe":
    st.header("Describe your task")
    st.markdown(
        "*Please explain in 2–3 sentences and include:*  \n"
        "• the **inputs** you will provide  \n"
        "• the **processing** that will be done  \n"
        "• the **expected output**  \n\n"
        "*Example:*  \n"
        "_“I’d like to create an email template with fields I can fill in. "
        "The system will merge the fields and send the email for me.”_"
    )
    desc = st.text_area(
        "What would you like to automate?",
        value=_ss("wizard_desc", ""),
        height=120,
    )
    col1, col2 = st.columns(2)
    if col1.button("Next", disabled=not desc.strip(), type="primary"):
        st.session_state.update(
            wizard_step="template",
            wizard_desc=desc.strip(),
            wizard_goal=desc.strip(),
        )
        _rerun()
    if col2.button("Cancel"):
        st.session_state["wizard_step"] = "intro"
        _rerun()
    st.stop()

# Template + Goal
if step == "template":
    st.header("Provide template & goal")
    goal = st.text_input("Goal", value=_ss("wizard_goal", ""))
    tpl = st.file_uploader(
        "Upload template",
        type=["docx", "pptx", "html", "txt", "md", "htm"],
    )
    c1, c2 = st.columns(2)
    if c1.button("Next", type="primary"):
        ok, res = wizard_create_draft(goal, tpl, TENANT)
        if ok:
            st.session_state.update(
                wizard_step="fields",
                wizard_draft=res,
                wizard_goal=goal,
            )
            _rerun()
        else:
            st.error(res)
    if c2.button("← Back"):
        st.session_state["wizard_step"] = "describe"
        _rerun()
    st.stop()

# Fields
if step == "fields":
    draft = wizard_update_fields.load(_ss("wizard_draft"))
    if not draft:
        st.error("Draft missing – restart wizard."); st.stop()

    st.header("Define required fields")
    fields = wizard_update_fields.render_edit_grid(draft.required_fields)
    c1, c2 = st.columns(2)
    if c1.button("Save & Continue", type="primary"):
        wizard_update_fields.save(draft.draft_id, fields)
        st.session_state["wizard_step"] = "publish"
        _rerun()
    if c2.button("← Back"):
        st.session_state["wizard_step"] = "template"
        _rerun()
    st.stop()

# Publish
if step == "publish":
    draft = wizard_update_fields.load(_ss("wizard_draft"))
    if not draft:
        st.error("Draft missing – restart wizard."); st.stop()

    st.header("Publish your new task")
    if st.button("Publish workflow", type="primary"):
        ok, msg = wizard_publish(draft)
        if ok:
            st.success(f"Published! New task id: **{msg}**")
            st.session_state["wizard_step"] = "done"
            _rerun()
        else:
            st.error(f"Publish failed: {msg}")

    if st.button("← Back"):
        st.session_state["wizard_step"] = "fields"
        _rerun()
    st.stop()

# Done
st.header("Wizard finished ✅")
if st.button("Create another task"):
    st.session_state.update(
        wizard_step="intro",
        wizard_goal="",
        wizard_desc="",
        wizard_draft=None,
    )
    _rerun()
if st.button("← Dashboard"):
    st.session_state["wizard_step"] = None
    _rerun()
