""" 
backend/graph.py
LangGraph orchestration with hot-reload support.
"""

from __future__ import annotations

import threading
from typing import Dict, Any, Mapping

from pydantic import BaseModel, Extra
from langgraph.graph import StateGraph
from langgraph.pregel import Pregel
from langchain.schema.runnable import Runnable

# ──────────────────────────── 1 · Shared workflow state ────────────────────────────
class WorkflowState(BaseModel, extra=Extra.allow):
    prompt: str
    answers: Dict[str, Any] | None = None
    manifest: Dict[str, Any] | None = None
    ui_event: Dict[str, Any] | None = None

# ──────────────────────────── 2 · Nodes ────────────────────────────
def intent_node(state: WorkflowState, *_: Any) -> WorkflowState:
    """Look up the task manifest for the user’s prompt."""
    from backend.supabase import fetch_manifest
    _, manifest = fetch_manifest(state.prompt)
    state.manifest = manifest or {
        "processor_chain_id": "policy_qna_chain",
        "required_fields": [],
        "metadata": {},
    }
    return state

def gather_node(state: WorkflowState, *_: Any) -> WorkflowState:
    required = state.manifest.get("required_fields", [])
    if required and not state.answers:
        state.ui_event = {"ui_event": "form", "fields": required}
    return state

def process_node(state: WorkflowState, *_: Any) -> WorkflowState:
    import backend.processors as processors

    chain_id = state.manifest["processor_chain_id"]
    try:
        chain: Runnable = processors.REG[chain_id]
    except KeyError as exc:
        raise RuntimeError(
            f"Chain '{chain_id}' not registered—did you reload the graph?"
        ) from exc

    payload: Mapping[str, Any] = {
        "prompt": state.prompt,
        "inputs": state.answers,
        # pass only the nested metadata dict
        "metadata": state.manifest.get("metadata", {}),
    }
    state.ui_event = chain.invoke(payload)
    return state

def deliver_node(state: WorkflowState, *_: Any) -> WorkflowState:
    return state

# ──────────────────────────── 3 · Graph builder & hot-reload ────────────────────────────
_graph_lock = threading.RLock()
_GRAPH: Pregel | None = None

def build_graph() -> Pregel:
    with _graph_lock:
        sg = StateGraph(WorkflowState)

        sg.add_node("Intent", intent_node)
        sg.add_node("Gather", gather_node)
        sg.add_node("Process", process_node)
        sg.add_node("Deliver", deliver_node)

        sg.set_entry_point("Intent")
        sg.add_edge("Intent", "Gather")
        sg.add_conditional_edges(
            "Gather",
            lambda s: "Process" if s.ui_event is None else "Deliver",
            {"Process": "Process", "Deliver": "Deliver"},
        )
        sg.add_edge("Process", "Deliver")

        return sg.compile()

def reload_graph() -> None:
    global _GRAPH
    _GRAPH = build_graph()

# build once at import
reload_graph()

# ──────────────────────────── 4 · Public helper ────────────────────────────
def run_workflow(prompt: str, answers: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if _GRAPH is None:
        raise RuntimeError("Graph not initialised – call reload_graph() first.")

    init_state = WorkflowState(prompt=prompt, answers=answers)
    result = _GRAPH.invoke(init_state)          # AddableValuesDict
    return result.get("ui_event") or {
        "type": "error",
        "content": "No UI event produced",
    }
