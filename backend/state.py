"""
backend.state
=============
Defines the Pydantic model that carries data between graph nodes.
Add new top‑level fields here whenever nodes need to share extra data.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class WorkflowState(BaseModel):
    """
    Shared state object merged and passed along the LangGraph.

    • `manifest`    – the task_manifest row selected by the Intent node
    • `event`       – ui_event dict emitted by Gather or Process
    • `user_inputs` – answers collected by Gather (may be empty)
    """
    manifest: Optional[Dict[str, Any]] = None
    event: Optional[Dict[str, Any]] = None
    user_inputs: Optional[Dict[str, Any]] = None

    # allow nodes/helpers to stash ad‑hoc keys without failing validation
    model_config = ConfigDict(extra="allow")
