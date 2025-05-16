#!/usr/bin/env python3
"""
i2i App: Dynamic Dashboard + Workflow Wizard
• Thin, data-driven, no rigid UI
• Switches views with session state
"""
from __future__ import annotations

import os
import streamlit as st

from backend.graph import run_workflow
from backend.wizard import wizard_step_1

st.set_page_config(page_title="🧠  i2i Assistant", layout="centered")

# ───── Utility: Set View ─────
def set_view(view):
    st.session_state['view'] = view

# ───── Initial State ─────
if 'view' not in st.session_state:
    st.session_state['view'] = 'dashboard'
if 'wizard_step' not in st.session_state:
    st.session_state['wizard_step'] = 1

# ───── Dashboard View ─────
def render_dashboard():
    st.title("🧠  i2i Assistant")
    st.caption("Describe a task or launch the workflow wizard.")

    with st.form("prompt_form"):
        prompt = st.text_input("Describe the task", value=st.session_state.get("prompt", ""))
        submitted = st.form_submit_button("Run")
    if submitted and prompt.strip():
        st.session_state['prompt'] = prompt.strip()
        result = run_workflow(prompt.strip())
        if not result or result.get('ui_event') == 'not_found':
            st.warning("No matching task found.")
            if st.button("Create as Workflow (Wizard)", key="wizard_btn"):
                st.session_state['wizard_goal'] = prompt.strip()
                set_view('wizard')
            st.stop()
        else:
            st.session_state['event'] = result
            st.rerun()

    st.button("Create New Workflow (Wizard)", on_click=lambda: set_view('wizard'))

    # TODO: Recent tasks, Task library, etc.

# ───── Wizard View (Steps 1 & 2) ─────
def render_wizard():
    st.title("Workflow Wizard")
    wizard_step = st.session_state.get('wizard_step', 1)

    if wizard_step == 1:
        st.caption("Step 1: What do you want to automate?")

        if 'wizard_goal' not in st.session_state:
            st.session_state['wizard_goal'] = ""

        with st.form("wizard_goal_form"):
            goal = st.text_input("Describe your goal", value=st.session_state['wizard_goal'])
            submitted = st.form_submit_button("Next")
        if submitted and goal.strip():
            st.session_state['wizard_goal'] = goal.strip()
            # Call backend wizard step 1
            wizard_event = wizard_step_1(goal.strip())
            st.session_state['wizard_event'] = wizard_event
            st.session_state['wizard_selection'] = None
            st.rerun()

        # If user already submitted, show selectable suggestions
        wizard_event = st.session_state.get('wizard_event')
        if wizard_event and wizard_event.get('step') == 1:
            st.subheader("Suggestions:")

            # User selection logic
            selection = st.session_state.get('wizard_selection')
            picked = None

            # Templates
            templates = wizard_event.get("suggested_templates", [])
            if templates:
                st.markdown("**Matching Templates:**")
                for idx, t in enumerate(templates):
                    btn_key = f"template_{idx}"
                    if st.button(f"Use '{t['label']}'", key=btn_key):
                        st.session_state['wizard_selection'] = {"type": "template", "value": t}
                        st.session_state['wizard_step'] = 2
                        st.rerun()
                    st.write(f"- **{t['label']}** — {t['description']}")

            # LLM Plan (if present)
            llm_plan = wizard_event.get("llm_plan", [])
            if llm_plan:
                st.markdown("**LLM-Recommended Plan:**")
                if st.button("Use LLM-Recommended Plan", key="llm_plan_btn"):
                    st.session_state['wizard_selection'] = {"type": "llm_plan", "value": llm_plan}
                    st.session_state['wizard_step'] = 2
                    st.rerun()
                for idx, step in enumerate(llm_plan, 1):
                    label = step.get("label", step.get("type", ""))
                    st.write(f"{idx}. {label}")

        st.button("Back to Dashboard", on_click=lambda: set_view('dashboard'))

    # Step 2 placeholder
    elif wizard_step == 2:
        st.caption("Step 2: Field Builder (Coming Soon)")
        sel = st.session_state.get('wizard_selection')
        if sel:
            st.info(f"You selected: {sel['type']} – {sel['value'].get('label', str(sel['value']))}")
        st.button("Back to Dashboard", on_click=lambda: set_view('dashboard'))

# ───── Router ─────
if st.session_state['view'] == 'dashboard':
    render_dashboard()
elif st.session_state['view'] == 'wizard':
    render_wizard()

# Footer
st.caption("v0.1 · TENANT: " + os.getenv("TENANT_ID", "default"))
