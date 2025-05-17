"""
backend/graph.py
LangGraph orchestration with hot-reload support.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, Mapping, Optional

from langchain.schema.runnable import Runnable
from langgraph.graph   import StateGraph
from langgraph.pregel  import Pregel
from pydantic          import BaseModel, Extra

# ─────────────────────────── 1 · Shared workflow state ───────────────────────────
class WorkflowState(BaseModel, extra=Extra.allow):
    prompt:   str
    answers:  Dict[str, Any] | None = None
    manifest: Dict[str, Any] | None = None
    ui_event: Dict[str, Any] | None = None


# ─────────────────────────── 2 · Nodes ───────────────────────────────────────────
def intent_node(state: WorkflowState, *_: Any) -> WorkflowState:
    """Semantic intent matching → task manifest."""
    from backend.supabase import fetch_manifest
    _, manifest = fetch_manifest(state.prompt)
    state.manifest = manifest or {
        "processor_chain_id": "policy_qna_chain",
        "required_fields":    [],
        "metadata":           {},
    }
    return state


def gather_node(state: WorkflowState, *_: Any) -> WorkflowState:
    """Emit a form event if required fields are missing."""
    required = state.manifest.get("required_fields", [])
    answers  = state.answers or {}
    missing  = [f for f in required if answers.get(f["name"]) in ("", None)]
    if missing:
        state.ui_event = {"ui_event": "form", "fields": missing}
    return state


def process_node(state: WorkflowState, *_: Any) -> WorkflowState:
    import backend.processors as processors
    registry = processors.RUNNABLE_REG

    chain_id = state.manifest["processor_chain_id"]
    try:
        chain: Runnable = registry[chain_id]
    except KeyError as exc:
        raise RuntimeError(f"Chain '{chain_id}' not registered.") from exc

    payload: Mapping[str, Any] = {
        "prompt":   state.prompt,
        "inputs":   state.answers or {},
        "metadata": state.manifest.get("metadata", {}),
    }
    state.ui_event = chain.invoke(payload)
    return state


def deliver_node(state: WorkflowState, *_: Any) -> WorkflowState:
    return state


# ─────────────────────────── 3 · Graph builder / hot-reload ──────────────────────
_graph_lock = threading.RLock()
_GRAPH: Optional[Pregel] = None


def build_graph() -> Pregel:
    with _graph_lock:
        sg = StateGraph(WorkflowState)

        sg.add_node("Intent",  intent_node)
        sg.add_node("Gather",  gather_node)
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


# ─────────────────────────── 4 · Public helper ───────────────────────────────────
def run_workflow(prompt: str, answers: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Execute the LangGraph workflow.
    Returns {"output": <ui_event dict>} for the Streamlit front-end.
    """
    if _GRAPH is None:
        raise RuntimeError("Graph not initialised – call reload_graph() first.")

    init_state = WorkflowState(prompt=prompt, answers=answers or {})
    result_dict = _GRAPH.invoke(init_state)     # AddableValuesDict

    ui_event = result_dict.get("ui_event")
    if not ui_event:
        return {"output": {"ui_event": "error", "content": "No UI event produced."}}

    return {"output": ui_event}
