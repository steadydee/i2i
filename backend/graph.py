"""
backend.graph
=============
LangGraph definition (UI-agnostic)

Intent  →  Gather  →  Process  →  Deliver

Front-ends call `run_workflow(prompt, answers)` and simply render the
single `event` dict it returns.

Key tweak (May 14 ‘25)
----------------------
`run_workflow` now accepts either:

    • answers dict               → {"client": "...", ...}
    • full init_state dict       → {"user_inputs": {...}, "manifest": ...}

so tests can pass flat answers without wrapping them in another layer.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

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
    event: Optional[Dict[str, Any]] = None     # single ui_event payload

    model_config = {"extra": "allow"}          # tolerate ad-hoc keys


# ─────────────────────────── Node callables ──────────────────────────
def intent_node(state: WorkflowState) -> Dict[str, Any]:
    """Look up the manifest row that best matches the prompt."""
    return {"manifest": detect_intent(state.prompt)}


def process_node(state: WorkflowState) -> Dict[str, Any]:
    """Invoke the processor chain unless Gather already produced an event."""
    if state.event:
        return {}

    chain_id = state.manifest["processor_chain_id"]
    chain = PROC_REG[chain_id]
    ui_event = chain.invoke(
        {
            "inputs": state.user_inputs,
            "metadata": state.manifest.get("metadata"),
            "prompt": state.prompt,
        }
    )
    return {"event": ui_event}


def deliver_node(_: WorkflowState) -> Dict[str, Any]:
    """No-op – Deliver just surfaces `state.event`."""
    return {}


# ─────────────────────────── Build the graph ─────────────────────────
_g = StateGraph(state_schema=WorkflowState)

_g.add_node("Intent", intent_node)
_g.add_node("Gather", gather_fields)
_g.add_node("Process", process_node)
_g.add_node("Deliver", deliver_node)

_g.add_edge("Intent",  "Gather")
_g.add_edge("Gather",  "Process")
_g.add_edge("Process", "Deliver")

_g.set_entry_point("Intent")
_g.set_finish_point("Deliver")

GRAPH = _g.compile()


# ─────────────────────────── Public helper ───────────────────────────
def run_workflow(
    prompt: str,
    extra_inputs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute the LangGraph and return the *event* dict for the UI.

    Parameters
    ----------
    prompt :
        User’s natural-language request.
    extra_inputs :
        Either:
          • raw answers dict            {"client": "...", ...}
          • full init_state dict        {"user_inputs": {...}, "manifest": ...}

    Returns
    -------
    dict
        The event payload produced by Deliver (form, download_link, text, …).
    """
    extra_inputs = extra_inputs or {}

    # Accept flat answers OR already-nested user_inputs
    if "user_inputs" in extra_inputs:
        init_kwargs = extra_inputs
    else:
        init_kwargs = {"user_inputs": extra_inputs}

    init_state = WorkflowState(prompt=prompt, **init_kwargs)
    final_state = GRAPH.invoke(init_state)
    return final_state["event"]
