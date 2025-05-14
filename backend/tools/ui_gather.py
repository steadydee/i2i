"""
Generic GatherFields runnable
-----------------------------
• If answers are missing  → inject {"event": {...}} and STOP further processing
• If answers complete     → inject {"user_inputs": {...}} for Process to use
"""
from typing import Any, Dict, List
from pydantic import BaseModel


def _to_dict(state: Any) -> Dict[str, Any]:
    return state.model_dump() if isinstance(state, BaseModel) else state


def gather_fields(state: Any) -> Dict[str, Any]:
    data = _to_dict(state)

    manifest  = data["manifest"]
    required  = manifest.get("required_fields", [])
    given     = data.get("user_inputs", {}) or {}

    missing: List[dict] = [f for f in required if f["name"] not in given]

    if missing:
        # Wrap the form details in a single event dict
        return {
            "event": {
                "ui_event": "form",
                "fields":   missing,
            }
        }

    # Everything supplied – hand answers over
    return {"user_inputs": given}
