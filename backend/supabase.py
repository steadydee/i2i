"""
backend/supabase.py
Supabase helpers
────────────────────────────────────────────────────────
• Loads SUPABASE_URL / SUPABASE_KEY from .env (python-dotenv).
• Embeds the user prompt via the `/embed` Edge Function
  using the anon key for authorization.
• Calls `match_task_manifest_vec` with that vector and
  returns the best task-manifest row.
"""

from __future__ import annotations

# auto-populate os.environ from .env  →  pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()

import os
import json
import requests
from typing import Tuple, Dict, Any, List
from supabase import create_client, Client

# ─── configuration ───────────────────────────────────
_SUPABASE_URL: str | None = os.getenv("SUPABASE_URL")
_SUPABASE_KEY: str | None = os.getenv("SUPABASE_KEY")
if not _SUPABASE_URL or not _SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_KEY missing from environment/.env")

_SB: Client = create_client(_SUPABASE_URL, _SUPABASE_KEY)

# Edge Function that returns { "embedding": [ … ] }
_EMBED_URL = f"{_SUPABASE_URL}/functions/v1/embed"

_HTTP_TIMEOUT = 10  # seconds


# ─── helpers ──────────────────────────────────────────
def _embed(text: str) -> List[float]:
    """Call the Edge Function and return the 1536-dim vector."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_SUPABASE_KEY}",   # anon key auth
    }
    resp = requests.post(
        _EMBED_URL,
        headers=headers,
        json={"text": text},
        timeout=_HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def fetch_manifest(prompt: str) -> Tuple[str, Dict[str, Any]]:
    """
    1. Embed the prompt via Edge Function.
    2. Send the vector to match_task_manifest_vec().
    3. Return (task, manifest_row_json).
    """
    vec = _embed(prompt)

    # PostgREST expects the vector param as a JSON array string
    res = _SB.rpc("match_task_manifest_vec", {"q_vec": json.dumps(vec)}).execute()
    if not res.data:
        raise RuntimeError("No manifest matched that prompt.")

    row: Dict[str, Any] = res.data
    return row["task"], row
