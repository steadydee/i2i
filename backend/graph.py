# -*- coding: utf-8 -*-
"""
i2i LangGraph workflow
──────────────────────────────────────────────────────────────────────────────
User text  ─► Intent  ─► Gather (Supabase) ─► Process (processor_chain) ─► Deliver
"""
from __future__ import annotations
from typing import TypedDict, Any

from langgraph.graph import StateGraph

from backend.db import sb            # ← shared Supabase client
from backend.processors import REG   # ← registry of LangChain runnables


# ────────────────────────────────────────────────────────────────────────────
# LangGraph state
# ────────────────────────────────────────────────────────────────────────────
class WorkflowState(TypedDict, total=False):
    user_input: str                # raw prompt from Streamlit
    task: str                      # canonical task id (draft_sow / policy_qna)
    gathered: dict                 # task-manifest row pulled in Gather
    result: Any                    # output from processor chain
    response: str                  # human-facing reply for the UI


# ────────────────────────────────────────────────────────────────────────────
# Nodes
# ────────────────────────────────────────────────────────────────────────────
def intent_node(state: WorkflowState) -> WorkflowState:
    """Naïve keyword router; swap in classifier later."""
    txt = state["user_input"].lower()
    state["task"] = "draft_sow" if "sow" in txt else "policy_qna"
    return state


def gather_node(state: WorkflowState) -> WorkflowState:
    """Fetch task-manifest row from Supabase."""
    resp = (
        sb()
        .table("task_manifest")
        .select("*")
        .eq("task", state["task"])
        .limit(1)
        .execute()
    )
    row = resp.data[0] if resp.data else None
    if row is None:
        raise ValueError(f"No task_manifest row found for task='{state['task']}'")
    state["gathered"] = row
    return state


def process_node(state: WorkflowState) -> WorkflowState:
    """Run the registered processor chain for this task."""
    chain_id = state["gathered"]["processor_chain_id"]
    chain = REG.get(chain_id)
    if chain is None:
        raise ValueError(f"No processor registered for '{chain_id}'")

    inputs = {
        "user_input": state["user_input"],
        "metadata":   state["gathered"].get("metadata", {}),
    }
    state["result"] = chain.invoke(inputs)
    return state


def deliver_node(state: WorkflowState) -> WorkflowState:
    """Return whatever Process produced as a UI-friendly string."""
    state["response"] = str(state.get("result", "(no result)"))
    return state


# ────────────────────────────────────────────────────────────────────────────
# Build & compile the graph
# ────────────────────────────────────────────────────────────────────────────
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


# Convenience helper for Streamlit
def run_workflow(prompt: str) -> str:
    """Run the entire graph and return the UI string."""
    final_state = graph.invoke({"user_input": prompt})
    return final_state["response"]
