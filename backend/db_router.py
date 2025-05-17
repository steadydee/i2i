"""
backend.db_router
Pure data-access helper.  Fetches task embeddings, prompts, processor chains,
and tool rows from Supabase/Postgres.  Contains **no business logic**.

Environment
-----------
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY   (or SUPABASE_ANON_KEY for local dev)
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

import numpy as np
from supabase import Client, create_client


# ────────────────────────────────────────────────────────────────────────────
# 1.  Supabase client (singleton)
# ────────────────────────────────────────────────────────────────────────────
def _make_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_ANON_KEY")
    )
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / KEY env vars must be set")
    # ⚠️  old supabase-py versions accept only (url, key)
    return create_client(url, key)


_sb: Client | None = None


def sb() -> Client:
    global _sb                           # pylint: disable=global-statement
    if _sb is None:
        _sb = _make_client()
    return _sb


# ────────────────────────────────────────────────────────────────────────────
# 2.  Row helpers
# ────────────────────────────────────────────────────────────────────────────
def _rows(table: str, **eq) -> List[Dict[str, Any]]:
    q = sb().table(table).select("*")
    for col, val in eq.items():
        q = q.eq(col, val)
    return q.execute().data or []


def _to_vec(raw) -> np.ndarray:
    """Coerce JSON or numeric[] into float32 ndarray."""
    if isinstance(raw, (list, tuple)):
        arr = raw
    elif isinstance(raw, str):
        if raw.startswith("{") and raw.endswith("}"):
            arr = raw.strip("{}").split(",")
        else:
            arr = json.loads(raw)
    else:
        raise TypeError(f"Cannot coerce {type(raw)} to vector")
    return np.asarray(arr, dtype=np.float32)


# ────────────────────────────────────────────────────────────────────────────
# 3.  Public API
# ────────────────────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def task_index(enabled_only: bool = True) -> List[Dict[str, Any]]:
    """
    Return task rows for routing.
    Assumes a view `task_index_view` with columns:
      task_id, helper_py, embedding, enabled
    """
    rows = _rows("task_index_view")
    out: List[Dict[str, Any]] = []
    for r in rows:
        if enabled_only and not r["enabled"]:
            continue
        out.append(
            {
                "task_id":   r["task_id"],
                "helper_py": r["helper_py"],
                "embedding": _to_vec(r["embedding"]),
            }
        )
    return out


def processor_chain(chain_id: str) -> Optional[Dict[str, Any]]:
    rows = _rows("processor_chains", chain_id=chain_id)
    return rows[0] if rows else None


def prompt(name: str, version: Optional[int] = None) -> Optional[str]:
    sel = sb().table("prompts").select("name,version,text").eq("name", name)
    if version is not None:
        sel = sel.eq("version", version)
    sel = sel.order("version", desc=True).limit(1)
    rows = sel.execute().data or []
    return rows[0]["text"] if rows else None


def tool(tool_id: str) -> Optional[Dict[str, Any]]:
    rows = _rows("tools", tool_id=tool_id)
    return rows[0] if rows else None


# ────────────────────────────────────────────────────────────────────────────
# 4.  Smoke test (python -m backend.db_router tasks)
# ────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":  # pragma: no cover
    import sys
    import pprint

    if len(sys.argv) > 1 and sys.argv[1] == "tasks":
        for t in task_index()[:5]:
            print(t["task_id"], t["helper_py"], t["embedding"].shape)
    else:
        pprint.pp(processor_chain("policy_qna_chain"))
