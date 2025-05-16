"""
JSONGraphExecutor v0.5 – linear-chain executor

• Dynamically inspects each runnable’s .run() method and passes the
  correct number of positional arguments (state  *or*  ctx+state).
• Keeps the call-stack scan so '__main__.A' and similar test helpers resolve.
"""
from __future__ import annotations
import importlib, inspect, logging, sys
from typing import Any, Dict, Mapping

logger = logging.getLogger(__name__)


class JSONGraphExecutor:
    def __init__(self, spec: Mapping[str, Any]):
        if spec.get("type") != "json_graph":
            raise ValueError("spec.type must be 'json_graph'")
        self.nodes = spec["nodes"]
        self.entry = spec.get("entry") or next(iter(self.nodes))

    # ─────────────────────────── run
    def run(self, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        ctx, state, cur, seen = context or {}, {}, self.entry, set()
        while cur:
            if cur in seen:
                raise RuntimeError(f"cycle detected at node '{cur}'")
            seen.add(cur)

            meta   = self.nodes[cur]
            runobj = self._resolve(meta["type"], meta.get("params", {}))

            # ── NEW: inspect signature to decide how many args to pass ──
            sig = inspect.signature(runobj.run)
            if len(sig.parameters) == 1:
                state[cur] = runobj.run(state)
            else:
                state[cur] = runobj.run(ctx, state)

            nxt = meta.get("next") or []
            cur = nxt[0] if nxt else None
        return state

    # ─────────────────────────── resolver
    def _resolve(self, dotted: str, params: Dict[str, Any]):
        """Import runnable class; works for test-local classes too."""
        mod_path, _, attr = dotted.rpartition(".")
        if not mod_path:
            raise ValueError(f"Invalid runnable path '{dotted}'")

        if mod_path == "__main__":
            # 1) global in the test module
            mod = sys.modules["__main__"]
            if hasattr(mod, attr):
                return getattr(mod, attr)(**params)
            # 2) class defined inside a test function (walk call-stack)
            for frame in inspect.stack():
                if attr in frame.frame.f_locals:
                    return frame.frame.f_locals[attr](**params)
            raise AttributeError(f"'{mod_path}' has no attribute '{attr}'")

        mod = importlib.import_module(mod_path)
        cls = getattr(mod, attr)
        return cls(**params)
