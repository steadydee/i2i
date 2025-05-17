#!/usr/bin/env python3
# ──────────────────────────────────────────────────────────────────────────────
#  Vector-search utilities (Supabase + pgvector)
# ──────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import openai
from supabase import create_client, Client

# --------------------------------------------------------------------------- #
# 1.  Config & helpers
# --------------------------------------------------------------------------- #
openai.api_key = os.environ["OPENAI_API_KEY"]
_MODEL_EMBED   = "text-embedding-3-small"          # ⇢ same model stored in DB

_SB: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)


def _embed(text: str) -> List[float]:
    """One-liner wrapper for OpenAI’s embedding endpoint."""
    return openai.embeddings.create(
        model=_MODEL_EMBED,
        input=text,
    ).data[0].embedding


# Make the embedder usable elsewhere
embed_text = _embed


# --------------------------------------------------------------------------- #
# 2.  Generic pgvector RPC wrapper
# --------------------------------------------------------------------------- #
def match_vectors(
    *,
    table_name: str,
    q_text: str,
    k: int = 10,
    tenant: str = "default",
    doc_id: str | None = None,
) -> List[Dict[str, Any]]:
    """
    Call the `match_vectors` Postgres function and return
    a list of rows + raw cosine **similarity** (higher = closer).
    """
    q_vec = _embed(q_text)

    params: Dict[str, Any] = {
        "table_name": table_name,
        "q_vec":      q_vec,
        "k":          k,
        "tenant":     tenant,
        "doc_id":     doc_id,
    }

    rows = _SB.rpc("match_vectors", params).execute().data or []

    out: List[Dict[str, Any]] = []
    for r in rows:
        payload = r["payload"]          # original row as JSONB
        sim     = float(r["score"])     # cosine similarity (-1 … +1)
        out.append(payload | {"sim": sim})

    return out


# --------------------------------------------------------------------------- #
# 3.  Bulk task-embedding fetch (used by router)
# --------------------------------------------------------------------------- #
def get_task_embeddings() -> List[Dict[str, Any]]:
    """Return enabled tasks with their stored embeddings."""
    rows = (
        _SB.table("task_manifest")
           .select("task, embedding, metadata")
           .eq("enabled", True)
           .execute()
           .data
    )

    out: List[Dict[str, Any]] = []
    for r in rows:
        if r["embedding"] is None:
            continue

        meta = r.get("metadata") or {}
        if isinstance(meta, str):
            meta = json.loads(meta)

        out.append(
            {
                "task":      r["task"],
                "helper_py": meta.get("helper_py", "default_helper"),
                "embedding": r["embedding"],
            }
        )
    return out


# --------------------------------------------------------------------------- #
# 4.  Public exports
# --------------------------------------------------------------------------- #
__all__ = [
    "embed_text",
    "match_vectors",
    "get_task_embeddings",
]
