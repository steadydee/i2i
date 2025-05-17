from __future__ import annotations
import os, uuid
from typing import List, Dict, Any
from supabase import create_client

_SB = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def create_draft(
    goal: str,
    tenant: str,
    template_id: str | None = None,
    required_fields: List[Dict[str, Any]] | None = None,
) -> str:
    """Insert a new wizard_drafts row and return its draft_id."""
    draft_id = str(uuid.uuid4())
    _SB.table("wizard_drafts").insert({
        "draft_id": draft_id,
        "tenant_id": tenant,
        "goal": goal,
        "template_id": template_id,
        "required_fields": required_fields or [],
        "step": 1,
    }).execute()
    return draft_id

def update_fields(draft_id: str, fields: List[Dict[str, Any]], step: int = 2) -> None:
    """Update required_fields (and optionally step) for an existing draft."""
    _SB.table("wizard_drafts").update({
        "required_fields": fields,
        "step": step,
    }).eq("draft_id", draft_id).execute()
