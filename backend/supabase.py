"""
backend/supabase.py
────────────────────────────────────────────────────────
• Loads SUPABASE_URL / SUPABASE_KEY from .env (python-dotenv).
• Embeds a prompt via the `/embed` Edge Function.
• Calls `match_task_manifest_vec` to fetch the best-matching task
  manifest row for the current tenant.
"""

from __future__ import annotations

import json
import os
from typing import Tuple, Dict, Any, List

from dotenv import load_dotenv            # pip install python-dotenv
from supabase import create_client, Client
import requests

# ── configuration ───────────────────────────────────────────────────────────
load_dotenv()                             # populate os.environ

_SUPABASE_URL = os.getenv("SUPABASE_URL")
_SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not _SUPABASE_URL or not _SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL / SUPABASE_KEY missing in environment")

_SB: Client = create_client(_SUPABASE_URL, _SUPABASE_KEY)

_EMBED_URL    = f"{_SUPABASE_URL}/functions/v1/embed"
_HTTP_TIMEOUT = 10                        # seconds

TENANT_ID: str = os.getenv("TENANT_ID", "default")
MIN_SIM:  float = 0.25                    # threshold (top score ≈ 0.283)

# ── helpers ─────────────────────────────────────────────────────────────────
def _embed(text: str) -> List[float]:
    """Return a 1 536-dim embedding for *text* via the Edge Function."""
    resp = requests.post(
        _EMBED_URL,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {_SUPABASE_KEY}",
        },
        json={"text": text},
        timeout=_HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def fetch_manifest(prompt: str) -> Tuple[str, Dict[str, Any]]:
    """
    Resolve *prompt* → (task_name, manifest_row).

    1. Embed the prompt.
    2. Ask `match_task_manifest_vec` for the single nearest task whose
       similarity ≥ MIN_SIM for the current tenant.
    """
    vec = _embed(prompt)

    res = _SB.rpc(
        "match_task_manifest_vec",
        {
            "q_vec":          json.dumps(vec),   # pgvector via JSON-array text
            "tenant":         TENANT_ID,
            "k":              1,                 # top hit only
            "min_similarity": MIN_SIM,
        },
    ).execute()

    if not res.data:
        raise RuntimeError("No task matched the prompt with sufficient similarity.")

    row: Dict[str, Any] = res.data[0]
    return row["task"], row
