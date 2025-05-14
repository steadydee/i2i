"""
LangGraph definition
====================
Intent  →  Gather  →  Process  →  Deliver
The graph is UI-agnostic.  Front-ends call `run_workflow()` and just
render the single `event` dict it returns.
"""
from __future__ import annotations
from typing import Dict, Any, Optional

from pydantic import BaseModel
from langgraph.graph import StateGraph

from backend.intent import detect_intent
from backend.tools.ui_gather import gather_fields
from backend.processors import REG as PROC_REG


# ─────────────────────────── State schema ────────────────────────────
class WorkflowState(BaseModel):
    prompt: str
    manifest: Optional[Dict[str, Any]] = None
    user_inputs: Optional[Dict[str, Any]] = None
    event: Optional[Dict[str, Any]] = None      # ← single ui_event payload


# ─────────────────────────── Node callables ───────────────────────────
def intent_node(state: WorkflowState) -> Dict[str, Any]:
    """Look up the manifest row that best matches the prompt."""
    return {"manifest": detect_intent(state.prompt)}


def process_node(state: WorkflowState) -> Dict[str, Any]:
    """
    If Gather already created an event (the form), skip processing.
    Otherwise invoke the processor chain and store its ui_event.
    """
    if state.event:
        return {}   # nothing to add

    chain_id = state.manifest["processor_chain_id"]
    chain = PROC_REG[chain_id]
    ui_event = chain.invoke(
        {"inputs": state.user_inputs,
         "metadata": state.manifest.get("metadata"),
         "prompt": state.prompt}
    )
    return {"event": ui_event}


def deliver_node(_: WorkflowState) -> Dict[str, Any]:
    """No-op — final event already lives in the state."""
    return {}


# ─────────────────────────── Build the graph ─────────────────────────
g = StateGraph(state_schema=WorkflowState)

g.add_node("Intent",  intent_node)
g.add_node("Gather",  gather_fields)
g.add_node("Process", process_node)
g.add_node("Deliver", deliver_node)

g.add_edge("Intent",  "Gather")
g.add_edge("Gather",  "Process")
g.add_edge("Process", "Deliver")

g.set_entry_point("Intent")
g.set_finish_point("Deliver")

graph = g.compile()


# ─────────────────────────── Public helper ───────────────────────────
def run_workflow(
    prompt: str,
    extra_inputs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    • 1st call with just the prompt → often returns a “form” event.
    • 2nd call with same prompt + form answers → returns next event
      (text, download_link, etc.).
    """
    init = WorkflowState(prompt=prompt, user_inputs=extra_inputs)
    final_state = graph.invoke(init)
    return final_state["event"]
