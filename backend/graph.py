# -*- coding: utf-8 -*-
"""
i2i LangGraph workflow
Intent ─► Gather ─► Process ─► Deliver
• Gather now fetches task metadata from Supabase.
"""

from __future__ import annotations

import os
from typing import TypedDict, Any
from dotenv import load_dotenv   #  ← add
load_dotenv()                    #  ← add; reads .env into os.environ
from langgraph.graph import StateGraph            # pip install langgraph
from supabase import create_client                # pip install supabase

# ─────────────────────────────────────────────────────────────────────────────
# Supabase lazy‑loaded singleton
# ─────────────────────────────────────────────────────────────────────────────
_SB = None


def sb():
    """Return a cached Supabase client."""
    global _SB
    if _SB is None:
        _SB = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"],
        )
    return _SB


# ─────────────────────────────────────────────────────────────────────────────
# LangGraph shared state
# ─────────────────────────────────────────────────────────────────────────────
class WorkflowState(TypedDict, total=False):
    user_input: str          # raw prompt from the UI
    task: str                # canonical task id (e.g. draft_sow)
    gathered: dict           # task‑manifest row fetched in Gather
    result: Any              # output from processor chain
    response: str            # final human‑facing reply


# ─────────────────────────────────────────────────────────────────────────────
# Graph nodes
# ─────────────────────────────────────────────────────────────────────────────
def intent_node(s: WorkflowState) -> WorkflowState:
    """VERY naive router for demo purposes."""
    text = s["user_input"].lower()
    s["task"] = "draft_sow" if "sow" in text else "policy_qna"
    return s


def gather_node(s: WorkflowState) -> WorkflowState:
    """Pull the task_manifest row (and any metadata) from Supabase."""
    row = (
        sb()
        .table("task_manifest")
        .select("*")
        .eq("task", s["task"])
        .single()
        .execute()
        .data
    )
    if not row:
        raise ValueError(f"No task_manifest row found for '{s['task']}'")
    s["gathered"] = row
    return s


def process_node(s: WorkflowState) -> WorkflowState:
    """Call the processor_chain specified in the manifest.
    For now we stub it out so the app still runs."""
    if s["task"] == "draft_sow":
        s["result"] = f"(stub) Generated SOW for: {s['user_input']}"
    else:
        s["result"] = f"(stub) Answered policy Q&A for: {s['user_input']}"
    return s


def deliver_node(s: WorkflowState) -> WorkflowState:
    s["response"] = str(s.get("result", "(no result)"))
    return s


# ─────────────────────────────────────────────────────────────────────────────
# Build and compile the LangGraph
# ─────────────────────────────────────────────────────────────────────────────
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


# Helper for Streamlit
def run_workflow(text: str) -> str:
    final_state = graph.invoke({"user_input": text})
    return final_state["response"]
