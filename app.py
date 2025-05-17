import streamlit as st
from backend.wizard import (
    wizard_find_similar,
    wizard_start_plan_chat,
    wizard_chat_continue,
)

st.set_page_config(page_title="i2i Assistant", page_icon="🧠", layout="wide")
ss = st.session_state

# ---------------- simple router ----------------
def go(page: str) -> None:
    ss.page = page
if "page" not in ss:
    ss.page = "dashboard"

# ------------------------------------------------------------------ #
# DASHBOARD                                                          #
# ------------------------------------------------------------------ #
if ss.page == "dashboard":
    st.title("🧠 i2i Assistant")

    with st.form("search"):
        q = st.text_input("Describe the task")
        if st.form_submit_button("Run") and q.strip():
            st.write("Running existing task …")         # placeholder

    st.button("Create New Workflow (Wizard)",
              on_click=lambda: go("wizard_intro"))

# ------------------------------------------------------------------ #
# WIZARD · splash (choose task vs workflow)                          #
# ------------------------------------------------------------------ #
if ss.page == "wizard_intro":
    st.header("✨ Workflow Wizard – welcome")
    st.button("Create a Task", on_click=lambda: go("wizard_goal"))
    st.button("Create a Workflow (soon)", disabled=True)
    st.button("← Dashboard", on_click=lambda: go("dashboard"))

# ------------------------------------------------------------------ #
# WIZARD · step 1 – describe goal                                    #
# ------------------------------------------------------------------ #
if ss.page == "wizard_goal":
    st.header("🧙 What would you like to do?")

    goal = st.text_area(
        "Describe the task in 2 – 3 sentences, including inputs, processing, and expected output.",
        key="wiz_goal_input",
        height=130,
    )

    if st.button("Next", disabled=not goal.strip()):
        ss.wiz_goal = goal.strip()
        ss.sim_tasks = wizard_find_similar(ss.wiz_goal)
        go("wizard_similar")
        st.rerun()                       # single rerun after nav

    st.button("← Back", on_click=lambda: go("wizard_intro"))
    st.button("← Dashboard", on_click=lambda: go("dashboard"))

# ------------------------------------------------------------------ #
# WIZARD · similar-tasks hit-list                                    #
# ------------------------------------------------------------------ #
if ss.page == "wizard_similar":
    st.header("🧙 Similar tasks found")

    if not ss.sim_tasks:
        st.info("No close matches – let’s design a new task.")
        if st.button("Continue"):
            go("wizard_plan")
            st.rerun()
    else:
        for t in ss.sim_tasks:
            st.subheader(t["task"])
            st.caption(", ".join(t["phrase_examples"]))
            col1, col2 = st.columns(2)
            col1.button("Run this task", key=f"run_{t['task']}")
            col2.button("Ignore", key=f"ign_{t['task']}")

    st.button("← Back", on_click=lambda: go("wizard_goal"))
    st.button("← Dashboard", on_click=lambda: go("dashboard"))

# ------------------------------------------------------------------ #
# WIZARD · planning chat with GPT                                    #
# ------------------------------------------------------------------ #
if ss.page == "wizard_plan":
    if "wizard_chat" not in ss:
        ss.wizard_chat = wizard_start_plan_chat(ss.wiz_goal)

    st.header("🧙 Preparing to build your task")

    # history (skip system prompt)
    for msg in ss.wizard_chat[1:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_msg = st.chat_input("Type your reply…")
    if user_msg:
        ss.wizard_chat.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.write(user_msg)

        with st.spinner("Thinking…"):
            assistant_text = wizard_chat_continue(ss.wizard_chat)
        ss.wizard_chat.append({"role": "assistant", "content": assistant_text})

        with st.chat_message("assistant"):
            st.write(assistant_text)

        st.rerun()                      # refresh for next turn

    st.button("← Back", on_click=lambda: go("wizard_goal"))
    st.button("← Dashboard", on_click=lambda: go("dashboard"))
