#!/usr/bin/env python3
"""
Smoke-test: vector similarity against task_manifest
Run:  python scripts/smoke_vector.py "I need an email template"
"""

import sys
from backend.vector_search import match_vectors

query = " ".join(sys.argv[1:]) or "I need an email template"
hits  = match_vectors(
    table_name="task_manifest",
    q_text=query,
    k=10,
    tenant="default",
    doc_id=None,
)

print(f"\nQuery: {query!r}")
print("-" * 60)
if not hits:
    print("No matches at all.")
    sys.exit(0)

print(f"{'task':20}  {'dist':>6}   phrase_examples")
for r in hits:
    print(f"{r['task']:<20}  {r['dist']:.3f}   {r['phrase_examples']}")
