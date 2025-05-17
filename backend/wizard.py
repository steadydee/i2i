"""
Wizard helpers
──────────────
• wizard_find_similar
• wizard_start_plan_chat / wizard_chat_continue
• wizard_create_draft / wizard_update_fields / wizard_publish
"""
from __future__ import annotations

import json, uuid, re
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

import openai
from pydantic import BaseModel

from backend.supabase     import _SB
from backend.vector_search import match_vectors, embed_text


# ──────────────────────────────────────────────────────────────────────
# 1.  Similar-task lookup (safe JSON wrapper)                           #
# ──────────────────────────────────────────────────────────────────────
SIM_THRESHOLD = 0.50

def wizard_find_similar(goal: str, k: int = 3) -> List[dict]:
    rows = match_vectors(
        table_name="task_manifest",
        q_text=goal,
        k=k,
        tenant="default",
    )
    return [r for r in rows if r.get("dist", 1) <= (1 - SIM_THRESHOLD)]


# ──────────────────────────────────────────────────────────────────────
# 2.  LLM plan-builder chat                                             #
# ──────────────────────────────────────────────────────────────────────
_SYS = ("You are the Workflow Wizard planner. Restate the user's goal in one "
        "paragraph (inputs, processing, output) and finish with 'Is that correct?'")

_OA = openai.OpenAI()

def wizard_start_plan_chat(goal: str) -> List[dict]:
    msgs = [
        {"role": "system", "content": _SYS},
        {"role": "user",   "content": goal},
    ]
    first = _OA.chat.completions.create(
        model="gpt-4o-mini",
        messages=msgs,
        temperature=0.3,
        max_tokens=160,
    ).choices[0].message.content.strip()
    msgs.append({"role": "assistant", "content": first})
    return msgs


def wizard_chat_continue(history: List[dict]) -> str:
    return _OA.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,
        temperature=0.3,
        max_tokens=180,
    ).choices[0].message.content.strip()


# ──────────────────────────────────────────────────────────────────────
# 3.  Minimal Pydantic draft model (no external import needed)          #
# ──────────────────────────────────────────────────────────────────────
class WizardDraft(BaseModel):
    draft_id: str
    goal: str
    template_id: str | None = None
    required_fields: list[dict]
    step: int = 1


# ──────────────────────────────────────────────────────────────────────
# 4.  Draft CRUD                                                        #
# ──────────────────────────────────────────────────────────────────────
def wizard_create_draft(goal: str) -> WizardDraft:
    row = (
        _SB.table("wizard_drafts")
        .insert(
            {
                "goal": goal,
                "required_fields": json.dumps([]),
                "step": 1,
                "tenant_id": "default",
            }
        )
        .execute()
        .data[0]
    )
    return WizardDraft.model_validate(row)


def wizard_update_fields(draft_id: str, fields: list[dict]) -> None:
    _SB.table("wizard_drafts").update(
        {"required_fields": json.dumps(fields), "step": 2}
    ).eq("draft_id", draft_id).execute()


# ──────────────────────────────────────────────────────────────────────
# 5.  Publish workflow                                                  #
# ──────────────────────────────────────────────────────────────────────
def wizard_publish(draft: WizardDraft) -> Tuple[bool, str]:
    try:
        chain_id = f"doc_chain_{draft.draft_id[:6]}"
        task_id  = f"task_{draft.draft_id[:4]}"

        chain_json = {
            "type": "json_graph",
            "version": "1.0",
            "entry": "doc_runner",
            "risk_level": "low",
            "cost_guard": {},
            "nodes": {
                "doc_runner": {
                    "id": "doc_runner",
                    "class_path": "backend.processors.DocTemplateRunner",
                    "init_kwargs": {"template_id": draft.template_id},
                }
            },
        }

        _SB.table("processor_chains").insert(
            {
                "chain_id": chain_id,
                "chain_json": json.dumps(chain_json),
                "tenant_id": "default",
                "enabled": True,
            }
        ).execute()

        _SB.table("task_manifest").insert(
            {
                "task": task_id,
                "phrase_examples": json.dumps([draft.goal]),
                "required_fields": json.dumps(draft.required_fields),
                "processor_chain_id": chain_id,
                "output_type": "download_link",
                "enabled": True,
                "tenant_id": "default",
            }
        ).execute()

        _SB.table("wizard_drafts").update(
            {"published_at": datetime.now(timezone.utc).isoformat()}
        ).eq("draft_id", draft.draft_id).execute()

        return True, task_id
    except Exception as e:
        return False, f"publish error: {e}"


__all__ = [
    "wizard_find_similar",
    "wizard_start_plan_chat",
    "wizard_chat_continue",
    "wizard_create_draft",
    "wizard_update_fields",
    "wizard_publish",
]
