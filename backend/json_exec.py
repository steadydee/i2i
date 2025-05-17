"""
Tiny linear executor (v0.5) that runs a ChainDef step-by-step.
The final step’s output is returned as the ui_event dict.
"""
from __future__ import annotations
import importlib
from typing import Dict, Any
from backend.schema import ChainDef


class JSONGraphExecutor:
    def __init__(self, spec: ChainDef):
        self.steps = spec.steps            # already validated by ChainDef

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        state: Dict[str, Any] = {}
        for step in self.steps:
            module, _, cls_name = step.class_path.rpartition(".")
            cls = getattr(importlib.import_module(module), cls_name)
            runnable = cls(**step.init_kwargs)
            state[step.id] = runnable.run(payload | state)
        return state[self.steps[-1].id]    # must be the ui_event
