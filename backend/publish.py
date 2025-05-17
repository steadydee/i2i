from __future__ import annotations
import os, uuid
from typing import Dict, Any
from supabase import create_client

url, key   = os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
TENANT     = os.getenv("TENANT_ID", "default")
_SB        = create_client(url, key) if url and key else None

def _uid() -> str:
    return uuid.uuid4().hex

def publish_draft(draft_id: str) -> str:
    if _SB is None:
        raise RuntimeError("SUPABASE creds missing")

    draft = (_SB.table("wizard_drafts")
               .select("*").eq("draft_id", draft_id)
               .single().execute().data)
    if not draft:
        raise ValueError("Draft not found")

    chain_id = f"doc_chain_{_uid()[:6]}"
    task_id  = draft.get("task_name") or f"task_{_uid()[:4]}"

    chain_json: Dict[str, Any] = {
        "type":    "json_graph",
        "version": "1.0",
        "entry":   "doc",
        "nodes": {
            "doc": {
                "type":   "backend.tools.docx_render.DocDraftRunnable",
                "params": {"template_id": draft["template_id"]},
                "end":    True
            }
        }
    }

    _SB.table("processor_chains").insert({
        "chain_id":   chain_id,
        "chain_json": chain_json,
        "type":       "chain",
        "enabled":    True,
        "tenant_id":  TENANT
    }).execute()

    _SB.table("task_manifest").insert({
        "task":               task_id,
        "phrase_examples":    draft.get("phrase_examples") or [draft["goal"]],
        "required_fields":    draft["required_fields"],
        "processor_chain_id": chain_id,
        "output_type":        "text",
        "enabled":            True,
        "tenant_id":          TENANT
    }).execute()

    # mark draft finished (no published_at column)
    _SB.table("wizard_drafts").update({"step": 99}).eq("draft_id", draft_id).execute()

    return task_id
