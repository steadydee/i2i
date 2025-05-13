# backend/graph.py
from __future__ import annotations
from typing import TypedDict, Any
from langgraph.graph import StateGraph     # pip install langgraph

class WorkflowState(TypedDict, total=False):
    user_input: str
    task: str
    gathered: dict
    result: Any
    response: str

def intent_node(s: WorkflowState) -> WorkflowState:
    s["task"] = "draft_sow" if "sow" in s["user_input"].lower() else "policy_qna"
    return s

def gather_node(s: WorkflowState) -> WorkflowState:
    s["gathered"] = {}
    return s

def process_node(s: WorkflowState) -> WorkflowState:
    if s["task"] == "draft_sow":
        s["result"] = f"(stub) Generated SOW for: {s['user_input']}"
    else:
        s["result"] = f"(stub) Answered policy Q&A for: {s['user_input']}"
    return s

def deliver_node(s: WorkflowState) -> WorkflowState:
    s["response"] = str(s.get("result", "(no result)"))
    return s

# ─── build graph ──────────────────────────────────────────────────────────
builder = StateGraph(WorkflowState)
builder.add_node("Intent", intent_node)
builder.add_node("Gather", gather_node)
builder.add_node("Process", process_node)
builder.add_node("Deliver", deliver_node)
builder.set_entry_point("Intent")
builder.add_edge("Intent", "Gather")
builder.add_edge("Gather", "Process")
builder.add_edge("Process", "Deliver")
builder.set_finish_point("Deliver")
graph = builder.compile()

def run_workflow(text: str) -> str:
    return graph.invoke({"user_input": text})["response"]
