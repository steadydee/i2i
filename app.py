#!/usr/bin/env python3
"""
i2i App: Dynamic Dashboard + Workflow Wizard
• Thin, data-driven UI
• DEBUG logging around every external call & state change
"""
from __future__ import annotations

import logging
import os
import streamlit as st

from backend.graph   import run_workflow
from backend.wizard  import wizard_step_1

# ───── logger ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "DEBUG"),
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
log = logging.getLogger("i2i.app")

st.set_page_config(page_title="🧠  i2i Assistant", layout="centered")

# ───── helpers ───────────────────────────────────────────────────────────
def set_view(view: str) -> None:
    log.debug("🔀 view -> %s", view)
    st.session_state["view"] = view

# ───── session defaults ─────────────────────────────────────────────────
st.session_state.setdefault("view",        "dashboard")
st.session_state.setdefault("wizard_step", 1)

# ───── dashboard view ───────────────────────────────────────────────────
def render_dashboard() -> None:
    st.title("🧠  i2i Assistant")
    st.caption("Describe a task or launch the workflow wizard.")

    with st.form("prompt_form"):
        prompt    = st.text_input("Describe the task", value=st.session_state.get("prompt", ""))
        submitted = st.form_submit_button("Run")

    if submitted and prompt.strip():
        prompt = prompt.strip()
        st.session_state["prompt"] = prompt

        log.debug("➡️  run_workflow(%s)", prompt)
        result = run_workflow(prompt)
        log.debug("⬅️  run_workflow result: %s", result)

        if not result or result.get("ui_event") == "not_found":
            st.warning("No matching task found.")
            if st.button("Create as Workflow (Wizard)", key="wizard_btn"):
                st.session_state["wizard_goal"] = prompt
                set_view("wizard")
            st.stop()

        st.session_state["event"] = result
        st.rerun()

    st.button("Create New Workflow (Wizard)", on_click=lambda: set_view("wizard"))

    # show last event
    event = st.session_state.get("event")
    if not event:
        return

    output   = event.get("output", event)      # fallback for legacy shape
    ui_event = output.get("ui_event")
    log.debug("🎨 render ui_event=%s", ui_event)

    if ui_event == "text":
        st.markdown(output.get("content", ""))
    elif ui_event == "download_link":
        url = output.get("url")
        st.markdown(f"[Download document]({url})" if url else "*No download link returned*")
    elif ui_event == "form":
        st.error("Form event reached dashboard unexpectedly.")
    else:
        st.json(event)

# ───── wizard view (unchanged) ───────────────────────────────────────────
def render_wizard() -> None:
    st.title("Workflow Wizard")
    step = st.session_state.get("wizard_step", 1)
    log.debug("🧙 wizard step=%s", step)

    if step == 1:
        st.caption("Step 1 · Describe your goal")

        with st.form("wizard_goal_form"):
            goal      = st.text_input("Goal", value=st.session_state.get("wizard_goal", ""))
            submitted = st.form_submit_button("Next")

        if submitted and goal.strip():
            goal = goal.strip()
            st.session_state["wizard_goal"] = goal

            log.debug("➡️  wizard_step_1(%s)", goal)
            wiz_evt = wizard_step_1(goal)
            log.debug("⬅️  wizard_step_1 result: %s", wiz_evt)

            st.session_state["wizard_event"]     = wiz_evt
            st.session_state["wizard_selection"] = None
            st.rerun()

        wiz_evt = st.session_state.get("wizard_event")
        if wiz_evt and wiz_evt.get("step") == 1:
            st.subheader("Suggestions")

            # templates
            for idx, t in enumerate(wiz_evt.get("suggested_templates", [])):
                if st.button(f"Use “{t['label']}”", key=f"tpl_{idx}"):
                    log.debug("✔ template picked: %s", t)
                    st.session_state["wizard_selection"] = {"type":"template","value":t}
                    st.session_state["wizard_step"] = 2
                    st.rerun()
                st.write(f"- **{t['label']}** — {t['description']}")

            # llm-plan
            llm_plan = wiz_evt.get("llm_plan")
            if llm_plan:
                if st.button("Use LLM-recommended plan", key="llm_btn"):
                    log.debug("✔ llm-plan picked")
                    st.session_state["wizard_selection"] = {"type":"llm_plan","value":llm_plan}
                    st.session_state["wizard_step"] = 2
                    st.rerun()
                for i, step_desc in enumerate(llm_plan, 1):
                    st.write(f"{i}. {step_desc.get('label', step_desc.get('type',''))}")

        st.button("Back to Dashboard", on_click=lambda: set_view("dashboard"))

    elif step == 2:
        st.caption("Step 2 · Field builder (coming soon)")
        sel = st.session_state.get("wizard_selection")
        if sel:
            st.info(f"Selected **{sel['type']}** – {sel['value'].get('label', sel['value'])}")
        st.button("Back to Dashboard", on_click=lambda: set_view("dashboard"))

    else:
        st.error("Unknown wizard step!")
        log.error("wizard at unexpected step=%s", step)

# ───── router ────────────────────────────────────────────────────────────
view = st.session_state["view"]
log.debug("📟 current view: %s", view)

if view == "dashboard":
    render_dashboard()
elif view == "wizard":
    render_wizard()
else:
    st.error(f"Unknown view “{view}”")
    log.error("session in unknown view=%s", view)

st.caption(f"v0.1 · TENANT: {os.getenv('TENANT_ID','default')}")
