"""
backend.supabase
----------------
Supabase DB and embedding helpers.

Exposes:
- _SB: sync supabase client
- _embed: embedding function (calls edge function)
- fetch_manifest: finds best task manifest for an input prompt
"""
from dotenv import load_dotenv
load_dotenv()

import os
import requests
from supabase import create_client, Client
from typing import Any, Dict, Tuple

_SB_URL = os.environ.get("SUPABASE_URL")
_SB_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
_SB: Client = create_client(_SB_URL, _SB_KEY)

def _embed(text: str) -> list:
    """
    Calls the /embed edge function for text embedding.
    """
    base_url = os.environ.get("SUPABASE_URL")
    if not base_url:
        raise RuntimeError("SUPABASE_URL environment variable not set.")
    embed_url = f"{base_url}/functions/v1/embed"
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set.")

    resp = requests.post(
        embed_url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('SUPABASE_KEY') or os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_ANON_KEY')}",
            "x-openai-key": openai_api_key
        },
        json={"text": text}
    )
    resp.raise_for_status()
    return resp.json()["embedding"]

def fetch_manifest(prompt: str, min_similarity: float = 0.30, tenant: str = "default") -> Tuple[str, Dict[str, Any]]:
    """
    Embeds the input prompt and finds the closest matching task manifest row
    by calling the 'match_task_manifest_vec' RPC. Returns (task_id, manifest dict).
    Aborts if cosine distance is above the min_similarity threshold.
    """
    vec = _embed(prompt)
    rpc_result = _SB.rpc(
        "match_task_manifest_vec",
        {
            "q_vec": vec,
            "tenant": tenant,
            "min_similarity": min_similarity
        }
    ).execute()

    if not rpc_result.data or not rpc_result.data[0]:
        return "", {}

    row = rpc_result.data[0]
    task_id = row.get("task_id") or row.get("id") or row.get("task") or ""
    return task_id, row
