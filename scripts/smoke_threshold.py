#!/usr/bin/env python3
"""
Smoke-test: show raw similarity scores (wizard_task_lookup) and what
wizard_find_similar() keeps after its threshold filter.
"""
import os, sys, openai
from backend.supabase import _SB
from backend.wizard  import wizard_find_similar
import backend.wizard as wz

MODEL  = "text-embedding-3-small"
QUERY  = sys.argv[1] if len(sys.argv) > 1 else "sow"
TOP_K  = 5

openai.api_key = os.environ["OPENAI_API_KEY"]
print("Query:", QUERY)

# ── embed -----------------------------------------------------------------
vec = openai.embeddings.create(model=MODEL, input=QUERY).data[0].embedding

# ── raw RPC call ----------------------------------------------------------
rows = _SB.rpc("wizard_task_lookup",
               {"query_embedding": vec, "top_k": TOP_K}).execute().data
print(f"\nTop-{TOP_K} raw rows (no threshold)")
for r in rows:
    task   = r["task_row"]["task"]
    score  = float(r["score"])
    phrases = ", ".join(r["task_row"].get("phrase_examples", []))
    print(f"  {score:5.3f}  {task:12}  [{phrases}]")

# ── threshold-filtered ----------------------------------------------------
th_default = getattr(wz, "_SIM_THRESHOLD", None)
print(f"\nFiltered by wizard_find_similar()  (threshold {th_default})")
hits = wizard_find_similar(QUERY)
for h in hits:
    print("  ✓", h["task"])
print("Total kept:", len(hits))
