"""
backend/graph.py
Phase-1 orchestrator using LangGraph’s StateGraph.
"""

from __future__ import annotations
from typing import Any, TypedDict, Annotated

from langgraph.graph import StateGraph
from langchain_core.runnables import Runnable

from backend.db import sb
from backend.processors import REG


# ────────────────────────────── State schema ──────────────────────────────
class WorkflowState(TypedDict, total=False):
    user_input: str
    form_data: dict
    task: str
    manifest: dict
    user_inputs: dict
    ask_form: bool
    result: Any
    response: dict


# ───────────────────────────────── Nodes ──────────────────────────────────
def intent_node(state: WorkflowState) -> WorkflowState:
    text = state["user_input"].lower()
    rows = (
        sb().table("task_manifest")
        .select("*")
        .eq("enabled", True)
        .execute()
        .data
    )
    for row in rows:
        if any(p in text for p in row["phrase_examples"]):
            state["task"] = row["task"]
            state["manifest"] = row
            return state

    state["task"] = "unknown_task"
    state["manifest"] = {}
    return state


def gather_node(state: WorkflowState) -> WorkflowState:
    if "form_data" in state:
        state["user_inputs"] = {**state.get("user_inputs", {}), **state["form_data"]}
        state.pop("form_data", None)

    manifest = state.get("manifest", {})
    required = {f["name"] for f in manifest.get("required_fields", [])}
    have = set(state.get("user_inputs", {}))

    state["ask_form"] = bool(required - have)
    if state["ask_form"]:
        state["response"] = {
            "ui_event": "form",
            "fields": manifest.get("required_fields", []),
        }
    return state


def process_node(state: WorkflowState) -> WorkflowState:
    if state.get("ask_form"):
        return state

    chain_id = state["manifest"]["processor_chain_id"]
    chain: Runnable = REG[chain_id]

    inputs = {
        **state.get("user_inputs", {}),
        "user_input": state["user_input"],
        "metadata": state["manifest"].get("metadata", {}),
    }

    state["result"] = chain.invoke(inputs)
    return state


def deliver_node(state: WorkflowState) -> WorkflowState:
    if "response" in state:
        return state

    result = state.get("result")

    if isinstance(result, dict) and "url" in result:
        state["response"] = {
            "ui_event": "download_link",
            "url": result["url"],
        }
    else:
        state["response"] = {
            "ui_event": "text",
            "content": str(result),
        }
    return state


# ────────────────────────── Build the StateGraph ──────────────────────────
graph = StateGraph(WorkflowState)

graph.add_node("Intent", intent_node)
graph.add_node("Gather", gather_node)
graph.add_node("Process", process_node)
graph.add_node("Deliver", deliver_node)

graph.set_entry_point("Intent")
graph.add_edge("Intent", "Gather")

# True → Process (need form), False → Deliver (ready)
graph.add_conditional_edges(
    "Gather",
    Annotated[bool, "ask_form"],
    {True: "Process", False: "Deliver"},
)

graph.add_edge("Process", "Deliver")

graph = graph.compile()


# ─────────────────────────── helper for Streamlit ─────────────────────────
def run_workflow(user_text: str, form_data: dict | None = None) -> dict:
    state: WorkflowState = {"user_input": user_text}
    if form_data:
        state["form_data"] = form_data

    final = graph.invoke(state) or {}
    return final.get(
        "response",
        {"ui_event": "text", "content": "⚠️ No response produced."},
    )
