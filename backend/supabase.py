"""
backend/supabase.py
────────────────────────────────────────────────────────
• Embeds a prompt via the `/embed` Edge Function.
• Calls `match_task_manifest_vec` to find the best task.
• Pulls the full manifest row so downstream code has all fields.
"""

from __future__ import annotations

import json
import os
from typing import Tuple, Dict, Any, List

from dotenv import load_dotenv
from supabase import create_client, Client
import requests

# ── config ──────────────────────────────────────────────────────────────────
load_dotenv()

_SB_URL  = os.getenv("SUPABASE_URL")
_SB_KEY  = os.getenv("SUPABASE_KEY")
if not _SB_URL or not _SB_KEY:
    raise RuntimeError("SUPABASE_URL / SUPABASE_KEY missing")

_SB: Client = create_client(_SB_URL, _SB_KEY)

_EMBED_URL    = f"{_SB_URL}/functions/v1/embed"
_HTTP_TIMEOUT = 10

TENANT_ID = os.getenv("TENANT_ID", "default")
MIN_SIM   = 0.25          # chosen from last test (top score ≈ 0.28)

# ── helpers ─────────────────────────────────────────────────────────────────
def _embed(text: str) -> List[float]:
    resp = requests.post(
        _EMBED_URL,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {_SB_KEY}",
        },
        json={"text": text},
        timeout=_HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def fetch_manifest(prompt: str) -> Tuple[str, Dict[str, Any]]:
    """Return (task_name, full manifest row) for a user prompt."""
    vec = _embed(prompt)

    # 1. vector search → gives task + distance
    hit = (
        _SB.rpc(
            "match_task_manifest_vec",
            {
                "q_vec":          json.dumps(vec),
                "tenant":         TENANT_ID,
                "k":              1,
                "min_similarity": MIN_SIM,
            },
        )
        .execute()
        .data
    )

    if not hit:
        raise RuntimeError("No task matched the prompt with sufficient similarity.")

    task_name: str = hit[0]["task"]
    distance:  float = hit[0]["dist"]

    # 2. pull the full manifest row expected by the workflow
    manifest = (
        _SB.table("task_manifest")
           .select("*")
           .eq("task", task_name)
           .single()
           .execute()
           .data
    )

    if not manifest:
        raise RuntimeError(f"Manifest row for task={task_name!r} disappeared.")

    manifest["dist"] = distance          # keep similarity handy
    return task_name, manifest
