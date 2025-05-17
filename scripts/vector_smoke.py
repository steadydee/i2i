#!/usr/bin/env python3
import os, openai, json, sys
from backend.supabase import _SB

openai.api_key = os.environ["OPENAI_API_KEY"]
MODEL  = "text-embedding-3-small"
QUERY  = "create an SOW for Acme"

# embed the query
vec = openai.embeddings.create(model=MODEL, input=QUERY).data[0].embedding
print("vector length:", len(vec))  # should be 1536

# call the RPC directly
rows = _SB.rpc("wizard_task_lookup",
               {"query_embedding": vec, "top_k": 5}).execute().data
hits = [r["task_row"]["task"] for r in rows]
print("hits:", hits)
