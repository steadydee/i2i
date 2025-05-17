import streamlit as st
from backend.graph import run_workflow
from backend.wizard import (
    wizard_find_similar,
    wizard_start_plan_chat,
)

# ── session-helpers ─────────────────────────────────────────────────────────
def _ss(key, default=None):
    return st.session_state.get(key, default)

def _go_home():
    st.session_state["mode"] = "home"          # Streamlit auto-reruns

def _go_wizard():
    st.session_state.update(mode="wizard", wizard_step="describe")

# ────────────────────────────────────────────────────────────────────────────
# 0.  DASHBOARD  vs  WIZARD router
# ────────────────────────────────────────────────────────────────────────────
if _ss("mode") != "wizard":
    # ------------- HOME DASHBOARD ------------------------------------------
    st.title("🧠 i2i Assistant")

    query = st.text_input("Describe the task")
    if st.button("Run", disabled=not query.strip()):
        st.write(run_workflow(query))   # placeholder

    st.divider()
    st.button("🪄  Create New Workflow (Wizard)", on_click=_go_wizard)
    st.stop()

# ======================== WIZARD ===========================================
step = _ss("wizard_step", "describe")

# ── step: describe goal ----------------------------------------------------
if step == "describe":
    st.header("🧙 What would you like to do?")
    goal = st.text_area(
        "Describe the task in 2–3 sentences, including inputs, processing, and expected output."
    )
    if st.button("Next", disabled=not goal.strip()):
        sims = wizard_find_similar(goal.strip())
        st.session_state["wizard_goal"] = goal.strip()
        if sims:
            st.session_state.update(wizard_step="similar", wizard_similar=sims)
        else:
            st.session_state.update(
                wizard_step="chat_plan",
                wizard_chat=wizard_start_plan_chat(goal.strip()),
            )
        st.rerun()                         # rerun needed here

    st.button("← Dashboard", on_click=_go_home)
    st.stop()

# ── step: similar tasks ----------------------------------------------------
if step == "similar":
    st.header("🧙 Similar tasks found")
    for row in _ss("wizard_similar", []):
        st.subheader(row.get("title") or row["task"])
        st.caption(", ".join(row.get("phrase_examples", [])))

        col_run, col_ignore = st.columns(2)
        if col_run.button("Run this task", key=f"run_{row['task']}"):
            st.success("🚀 (Integration placeholder)")

        if col_ignore.button("Ignore", key=f"ign_{row['task']}"):
            st.session_state.update(
                wizard_step="chat_plan",
                wizard_chat=wizard_start_plan_chat(_ss("wizard_goal")),
            )
            st.rerun()                     # rerun after state change

    st.button("← Dashboard", on_click=_go_home)
    st.stop()

# ── step: chat-planner intro ----------------------------------------------
if step == "chat_plan":
    st.header("🧙 Preparing to build your task")

    chat = _ss("wizard_chat", [])
    for turn in chat:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])

    reply = st.text_input("Your reply (type “yes” or corrections)…")
    if st.button("Continue", disabled=not reply.strip()):
        chat.append({"role": "user", "content": reply.strip()})
        st.session_state["wizard_chat"] = chat
        st.success("✅ Reply captured (multi-turn loop coming soon)")

    col_back, col_dash = st.columns(2)
    if col_back.button("← Back"):
        st.session_state["wizard_step"] = "describe"
        st.rerun()
    if col_dash.button("← Dashboard", on_click=_go_home):
        pass
    st.stop()
