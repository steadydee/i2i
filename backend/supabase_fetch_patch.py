# -------- PATCH for backend/supabase.py ---------
from __future__ import annotations
import json, os
from typing import Tuple, Dict, Any
from backend.supabase import _SB, _embed   # rest of the module already imports these

TENANT_ID = os.getenv("TENANT_ID", "default")  # coarse tenant flag

def fetch_manifest(prompt: str) -> Tuple[str, Dict[str, Any]]:
    """
    Resolve <prompt> → (task, manifest_row).
    Uses the smarter match_task_manifest_vec(q_vec, tenant, k, min_similarity).
    """
    vec = _embed(prompt)

    res = _SB.rpc(
        "match_task_manifest_vec",
        {
            "q_vec": json.dumps(vec),
            "tenant": TENANT_ID,
            "k": 1,                 # we only need the best row in production
            "min_similarity": 0.65, # raise or lower per tenant later
        },
    ).execute()

    if not res.data:
        raise RuntimeError("No task matched the prompt with sufficient similarity.")

    row: Dict[str, Any] = res.data[0]   # first—and only—row
    return row["task"], row
# -------- END PATCH ---------
