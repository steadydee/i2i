"""
Intent matcher (Supabase)
-------------------------
Extracts the first row from whatever shape supabase-py returns:

• 2.x  → SingleAPIResponse object (has .data, .count, .status_code)
• 1.x  → tuple: (('data', [...]), ('count', None))

Falls back to echo demo when nothing matches.
"""
from typing import Dict, Any
from backend.db import supabase

_FALLBACK: Dict[str, Any] = {
    "task": "echo_fields",
    "required_fields": [],
    "processor_chain_id": "debug_echo_chain",
    "output_type": "text",
    "metadata": {},
}

def _first_row(res) -> Dict[str, Any] | None:
    """Return the first row regardless of response style."""
    # Newer supabase-py (SingleAPIResponse)
    if hasattr(res, "data"):
        rows = res.data
        return rows[0] if rows else None

    # Older supabase-py (tuple style)
    if isinstance(res, tuple) and len(res) and isinstance(res[0], tuple):
        rows = res[0][1]          # second element of the first tuple
        return rows[0] if rows else None

    return None  # unknown response shape


def detect_intent(user_text: str) -> Dict[str, Any]:
    res = supabase.rpc("match_manifest", {"q": user_text}).execute()
    row = _first_row(res)
    return row or _FALLBACK
