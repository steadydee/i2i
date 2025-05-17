from __future__ import annotations
import importlib, inspect, logging, sys
from typing import Any, Dict, Mapping

log = logging.getLogger(__name__)

class JSONGraphExecutor:
    """Execute a json_graph spec (GraphDef model or plain dict)."""

    def __init__(self, spec: Mapping[str, Any] | Any):
        # Accept either a pydantic GraphDef or raw dict
        self.nodes = spec.nodes if hasattr(spec, "nodes") else spec["nodes"]
        self.entry = spec.entry if hasattr(spec, "entry") else spec["entry"]

    # ------------------------------------------------------------------
    def run(
        self,
        context: Dict[str, Any] | None = None,
        state:   Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        ctx   = context or {}
        data  = state   or {}
        cur   = self.entry
        seen  = set()

        while cur:
            if cur in seen:
                raise RuntimeError(f"cycle detected at node '{cur}'")
            seen.add(cur)

            meta = self.nodes[cur]
            m_get = meta.get if isinstance(meta, dict) else lambda k: getattr(meta, k)

            runobj = self._resolve(m_get("type"), m_get("params") or {})

            sig = inspect.signature(runobj.run)
            data[cur] = (
                runobj.run(data) if len(sig.parameters) == 1
                else runobj.run(ctx, data)
            )

            nxt = m_get("next") or []
            cur = nxt[0] if nxt else None

        return data

    # ------------------------------------------------------------------
    def _resolve(self, dotted: str, params: Dict[str, Any]):
        mod_path, _, attr = dotted.rpartition(".")

        # Shorthand: backend.helpers.<Class>
        if not mod_path:
            try:
                mod = importlib.import_module("backend.helpers")
                if hasattr(mod, attr):
                    return getattr(mod, attr)(**params)
            except ModuleNotFoundError:
                pass
            raise ValueError(f"Invalid runnable path '{dotted}'")

        if mod_path == "__main__":
            mod = sys.modules["__main__"]
            if hasattr(mod, attr):
                return getattr(mod, attr)(**params)
            for frame in inspect.stack():
                if attr in frame.frame.f_locals:
                    return frame.frame.f_locals[attr](**params)
            raise AttributeError(f"'{mod_path}' has no attribute '{attr}'")

        mod = importlib.import_module(mod_path)
        cls = getattr(mod, attr)
        return cls(**params)
