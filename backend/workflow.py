"""
Task router that uses vector similarity (task_embeddings) to choose the
appropriate helper.  Drops in until the DB-driven router is ready.
"""

from __future__ import annotations
import importlib
from typing import Dict, Any
import numpy as np
from backend.vector_search import get_task_embeddings          # ⬅️ your util
from supabase import create_client, Client                     # or your wrapper

# --- config ---
SIM_THRESHOLD = 0.55     # change back to whatever you used

# --------------------------------------------------------------------------- #
# 1.  Load task-level embeddings once at import-time                           #
# --------------------------------------------------------------------------- #
rows = get_task_embeddings()         # returns [{task, embedding, helper_py}]
TASK_EMB  = np.stack([r["embedding"] for r in rows])
TASK_META = rows                     # keep task + helper filename handy
TASK_NORM = np.linalg.norm(TASK_EMB, axis=1, keepdims=True)

# --------------------------------------------------------------------------- #
# 2.  Main entry point called by Streamlit                                    #
# --------------------------------------------------------------------------- #
def run(prompt: str, **extra) -> Dict[str, Any]:
    """
    Vector-router → helper.run() → helper result
    """
    emb = embed(prompt)                            # same model you stored with
    sim = (TASK_EMB @ emb) / (TASK_NORM.squeeze() * np.linalg.norm(emb))

    best_idx = int(np.argmax(sim))
    best_sim = float(sim[best_idx])

    if best_sim >= SIM_THRESHOLD:
        helper_mod = importlib.import_module(f"backend.helpers.{TASK_META[best_idx]['helper_py']}")
    else:
        # last-ditch keyword stub until DB router lands
        helper_mod = _fallback_helper(prompt)

    return helper_mod.run(prompt, **extra)

# --------------------------------------------------------------------------- #
# 3.  Tiny helpers                                                            #
# --------------------------------------------------------------------------- #
def embed(text: str) -> np.ndarray:
    # whatever embedding fn you already use for tasks
    from backend.vector_search import embed_text
    return embed_text(text)

def _fallback_helper(prompt: str):
    p = prompt.lower()
    if "sow" in p:
        return importlib.import_module("backend.helpers.draft_sow")
    else:
        return importlib.import_module("backend.helpers.policy_qna")
