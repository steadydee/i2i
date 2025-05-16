"""
Pytest autouse fixture
──────────────────────
• Stubs out Supabase network calls **before** tests execute.
• Ensures a runnable named 'debug_echo' exists in the registry.
• Works even if backend.graph imported earlier compiled its graph.
"""

import os
import pytest
import backend.supabase as db
from backend.processors import REG as PROCESSORS, reload_registry

# ─────────────────────────────────────────────────────────────────────────────
# 1. Guarantee registry has a runnable we can call
# ─────────────────────────────────────────────────────────────────────────────
reload_registry()

if "debug_echo" not in PROCESSORS:
    class DebugEcho:
        def __init__(self, *_, **__): pass
        def run(self, state): return {"echo": state.get("prompt", "")}
    PROCESSORS["debug_echo"] = DebugEcho

# ─────────────────────────────────────────────────────────────────────────────
# 2. In-memory rows returned by patched helpers
# ─────────────────────────────────────────────────────────────────────────────
_manifest_row = {
    "task": "debug_echo",
    "required_fields": [],
    "processor_chain_id": "debug_echo",
}
_chain_row = {"chain_id": "debug_echo", "chain_json": {}}

# Dummy 1536-dim vector (all zeros) so anything expecting len() still works
_dummy_vec = [0.0] * 1536

# ─────────────────────────────────────────────────────────────────────────────
# 3. Autouse fixture patches Supabase helpers AND embed
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def patch_supabase(monkeypatch):
    # Stub the /embed call first — this protects even old copies
    monkeypatch.setattr(db, "_embed", lambda text: _dummy_vec)

    # Replace helper look-ups in the shared module
    monkeypatch.setattr(
        db, "fetch_manifest",
        lambda prompt, tenant_id="default", k=1: (0.0, _manifest_row),
    )
    monkeypatch.setattr(db, "_fetch_chain", lambda cid: _chain_row)

    # Patch the copies imported into backend.graph at import time
    import backend.graph as g
    monkeypatch.setattr(g, "fetch_manifest",
                        lambda prompt, tenant_id="default": (0.0, _manifest_row),
                        raising=False)

    yield
