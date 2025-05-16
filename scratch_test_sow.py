#!/usr/bin/env python3
"""
Quick sanity-check: run the graph directly and print
  • the state returned by run_workflow()
  • the raw manifest match from fetch_manifest()
"""

from pprint import pprint
from backend.graph import run_workflow
from backend.supabase import fetch_manifest

PROMPT = "I need a SOW for Acme"

# --- 1. full graph -----------------------------------------------------------
print("\n★ Full graph run_workflow():")
state = run_workflow(PROMPT)
pprint(state)

# --- 2. intent match only ----------------------------------------------------
print("\n★ fetch_manifest() only:")
sim, row = fetch_manifest(PROMPT)      # ← no tenant_id arg
print("similarity:", sim)
print("task matched:", row["task"])
