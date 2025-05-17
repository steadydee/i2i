"""
backend.graph
=============
LangGraph orchestration with hot-reload support *plus* a
**back-compat shim** that normalises legacy helper output.

If a processor chain still returns:
    • {"event": {...}}
    • {"type": "text", "content": "..."}      ← very old helpers
…the shim maps it to the new contract:
    {"ui_event": "text", ...}
"""

from __future__ import annotations
import threading
from typing import Any, Dict, Mapping

from langchain.schema.runnable import Runnable
from langgraph.graph import StateGraph
from langgraph.pregel import Pregel
from pydantic import BaseModel, Extra

# ─────────────────────────── 1 · shared state ──────────────────────────
class WorkflowState(BaseModel, extra=Extra.allow):
    prompt:   str
    answers:  Dict[str, Any] | None = None
    manifest: Dict[str, Any] | None = None
    ui_event: Dict[str, Any] | None = None


# ─────────────────────────── 2 · nodes ──────────────────────────────────
def intent_node(state: WorkflowState, *_: Any) -> WorkflowState:
    from backend.supabase import fetch_manifest
    _, manifest = fetch_manifest(state.prompt)
    # fallback to policy-Q&A if nothing matches
    state.manifest = manifest or {
        "processor_chain_id": "policy_qna_chain",
        "required_fields":    [],
        "metadata":           {},
    }
    return state


def gather_node(state: WorkflowState, *_: Any) -> WorkflowState:
    required = state.manifest.get("required_fields", [])
    if required and not state.answers:
        state.ui_event = {"ui_event": "form", "fields": required}
    return state


def _shim_legacy(evt: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map 2014-style helper output → modern {"ui_event": ...} dict.
    """
    if not evt:
        return {"ui_event": "error", "content": "Empty helper response"}

    # 1) helpers that still wrap everything in {"event": {...}}
    if "event" in evt and "ui_event" not in evt:
        return evt["event"]

    # 2) very old: {"type":"text","content":"..."}
    if "ui_event" not in evt and "type" in evt:
        evt["ui_event"] = evt.pop("type")

    return evt


def process_node(state: WorkflowState, *_: Any) -> WorkflowState:
    import backend.processors as processors

    chain_id = state.manifest["processor_chain_id"]
    try:
        runnable: Runnable = processors.REG[chain_id]
    except KeyError as exc:
        raise RuntimeError(f"Unregistered chain_id '{chain_id}'") from exc

    payload: Mapping[str, Any] = {
        "prompt":   state.prompt,
        "inputs":   state.answers or {},
        "metadata": state.manifest.get("metadata", {}),
    }
    raw_evt = runnable.invoke(payload)         # helper response
    state.ui_event = _shim_legacy(raw_evt)
    return state


def deliver_node(state: WorkflowState, *_: Any) -> WorkflowState:
    return state


# ─────────────────────────── 3 · graph builder ─────────────────────────
_graph_lock = threading.RLock()
_GRAPH: Pregel | None = None

def build_graph() -> Pregel:
    with _graph_lock:
        sg = StateGraph(WorkflowState)

        sg.add_node("Intent",  intent_node)
        sg.add_node("Gather",  gather_node)
        sg.add_node("Process", process_node)
        sg.add_node("Deliver", deliver_node)

        sg.set_entry_point("Intent")
        sg.add_edge("Intent",  "Gather")
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

# compile once at import
reload_graph()


# ─────────────────────────── 4 · public helper ─────────────────────────
def run_workflow(prompt: str, answers: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if _GRAPH is None:
        raise RuntimeError("Graph not initialised – call reload_graph() first.")
    init_state = WorkflowState(prompt=prompt, answers=answers)
    final: WorkflowState = _GRAPH.invoke(init_state)  # type: ignore
    return {"output": final.ui_event}   # single, predictable envelope
# ─────────────────────────── 4 · public helper (patched) ────────────────
def run_workflow(prompt: str, answers: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Entry-point used by Streamlit + tests.
    Always returns {"output": {ui_event…}} so callers have one envelope shape.
    """
    if _GRAPH is None:
        raise RuntimeError("Graph not initialised – call reload_graph() first.")

    init_state = WorkflowState(prompt=prompt, answers=answers)
    final_state = _GRAPH.invoke(init_state)        # AddableValuesDict

    # AddableValuesDict behaves like a dict
    ui_evt = final_state.get("ui_event")

    # Absolute last-chance fallback
    if ui_evt is None:
        ui_evt = {"ui_event": "error", "content": "No ui_event produced"}

    return {"output": ui_evt}
def reload_graph() -> None:
    import backend.processors as processors
    processors.reload_registry()          # refresh REG from DB
    global _GRAPH
    _GRAPH = build_graph()
