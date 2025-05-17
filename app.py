#!/usr/bin/env python3
from __future__ import annotations
import os, re, logging, traceback
import streamlit as st

from backend.graph      import run_workflow, reload_graph
from backend.wizard     import wizard_step_1, wizard_step_2
from backend.templates  import upload_template, extract_placeholders
from backend.drafts     import create_draft, update_fields
from backend.publish    import publish_draft

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
                    format="%(asctime)s %(levelname)-8s %(message)s")
log = logging.getLogger("i2i.app")

st.set_page_config(page_title="🧠 i2i Assistant", layout="centered")

# ── session defaults ────────────────────────────────────────────────────
st.session_state.setdefault("view", "dashboard")
st.session_state.setdefault("wizard_step", 1)

# ── helpers ─────────────────────────────────────────────────────────────
def start_new_wizard():
    st.session_state.update(view="wizard", wizard_step=1)
    for k in ("wizard_event","wiz_sel","field_defs","node_params","draft_id"):
        st.session_state.pop(k, None)

def dynamic_form(fields:list[dict]) -> None:
    with st.form("dynamic_form"):
        answers={}
        for f in fields:
            k=f"{f['name']}_input"
            widget=f.get("widget","text_input")
            if widget=="number_input":
                answers[f["name"]] = st.number_input(f["label"], key=k)
            elif widget=="select":
                answers[f["name"]] = st.selectbox(f["label"], ["web","api"], key=k)
            else:
                answers[f["name"]] = st.text_input(f["label"], key=k)
        if st.form_submit_button("Submit"):
            st.session_state["event"] = run_workflow(
                st.session_state.get("prompt",""), answers)
            st.rerun()

def render_field_builder(fields:list[dict]) -> list[dict]:
    edited=[]
    for i,f in enumerate(fields):
        c = st.columns(4)
        f["name"]   = c[0].text_input("name", f["name"], key=f"n{i}")
        f["label"]  = c[1].text_input("label", f["label"], key=f"l{i}")
        f["widget"] = c[2].selectbox(
            "widget", ["text_input","number_input","date_input","select"],
            index=["text_input","number_input","date_input","select"].index(f["widget"]),
            key=f"w{i}"
        )
        if c[3].button("❌", key=f"del{i}"):
            continue
        edited.append(f)
    if st.button("Add field"):
        edited.append({"name":"","label":"","widget":"text_input"})
    return edited

# ── dashboard view ──────────────────────────────────────────────────────
def render_dashboard():
    st.title("🧠  i2i Assistant")
    with st.form("prompt_form"):
        prompt = st.text_input("Describe the task", st.session_state.get("prompt",""))
        if st.form_submit_button("Run") and prompt.strip():
            st.session_state["prompt"] = prompt.strip()
            st.session_state["event"]  = run_workflow(prompt.strip())
            st.rerun()

    st.button("Create New Workflow (Wizard)", on_click=start_new_wizard)

    evt = st.session_state.get("event")
    if not evt:
        return
    out = evt.get("output", evt)
    if out["ui_event"] == "text":
        st.markdown(out["content"])
    elif out["ui_event"] == "download_link":
        st.markdown(f"[Download]({out.get('url')})")
    elif out["ui_event"] == "form":
        dynamic_form(out["fields"])
    else:
        st.json(out)

# ── wizard view ─────────────────────────────────────────────────────────
def render_wizard():
    step = st.session_state.get("wizard_step", 1)

    # Step 1 – goal / template
    if step == 1:
        st.header("Wizard · Step 1 – goal / template")
        goal = st.text_input("Goal", st.session_state.get("wizard_goal",""))
        if st.button("Next") and goal.strip():
            st.session_state.update(
                wizard_goal  = goal.strip(),
                wizard_event = wizard_step_1(goal.strip())
            ); st.rerun()

        uploaded = st.file_uploader("Upload template",
                                    type=["docx","pptx","html","txt","md"])
        if uploaded:
            tenant = os.getenv("TENANT_ID","default")
            data   = uploaded.read()
            tid    = upload_template(data, uploaded.name, tenant)
            names  = extract_placeholders(data, os.path.splitext(uploaded.name)[1].lower())

            def gw(n:str)->str:
                if re.search(r"(amount|total|cost|price)", n): return "number_input"
                if re.search(r"(date|due|deadline)", n):       return "date_input"
                return "text_input"

            fields = [{"name":n,"label":n.replace('_',' ').title(),"widget":gw(n)} for n in names]
            did = create_draft(goal or "Template task", tenant, tid, fields)

            st.session_state.update(
                draft_id   = did,
                wiz_sel    = {"type":"template","value":{"template_id":tid}},
                field_defs = fields,
                wizard_step=2
            )
            st.success(f"Uploaded & detected {len(names)} field(s)")
            st.rerun()

        evt = st.session_state.get("wizard_event")
        if evt:
            st.subheader("Suggestions")
            for i,t in enumerate(evt["suggested_templates"]):
                if st.button(f"Use “{t['label']}”", key=f"tpl{i}"):
                    st.session_state.update(
                        wiz_sel={"type":"template","value":t},
                        wizard_step=2
                    ); st.rerun()
            if evt["llm_plan"] and st.button("Use AI plan"):
                st.session_state.update(
                    wiz_sel={"type":"llm_plan","value":evt["llm_plan"]},
                    wizard_step=2
                ); st.rerun()

    # Step 2 – required fields
    elif step == 2:
        st.header("Wizard · Step 2 – required fields")
        if "field_defs" not in st.session_state:
            st.session_state["field_defs"] = wizard_step_2(
                st.session_state["wiz_sel"])["required_fields"]

        st.session_state["field_defs"] = render_field_builder(
            st.session_state["field_defs"])

        if st.button("Save & Continue"):
            update_fields(st.session_state["draft_id"],
                          st.session_state["field_defs"], step=2)

            sel = st.session_state["wiz_sel"]
            if sel["type"] == "template":
                st.session_state["node_params"] = {"template_id": sel["value"]["template_id"]}
            else:
                st.session_state["node_params"] = {}

            st.session_state["wizard_step"] = 4
            st.success("Fields saved"); st.rerun()

        st.button("← Cancel", on_click=start_new_wizard)

    # Step 3 – publish
    elif step == 4:
        st.header("Wizard · Step 3 – publish")
        if st.button("Publish workflow"):
            try:
                task_id = publish_draft(st.session_state["draft_id"])
                reload_graph()
                st.success(f"Published! New task id: **{task_id}**")
            except Exception as e:
                traceback.print_exc()          # full trace to terminal
                st.error(f"Publish failed: {e}")
        st.button("← Dashboard", on_click=start_new_wizard)

    else:
        st.error("Unknown wizard step")

# ── router ──────────────────────────────────────────────────────────────
if st.session_state["view"] == "wizard":
    render_wizard()
else:
    render_dashboard()

st.caption(f"v0.7 · TENANT: {os.getenv('TENANT_ID','default')}")
