"""
Wizard helpers
──────────────
  • wizard_find_similar   – vector / keyword search for existing tasks
  • wizard_start_plan_chat – first assistant turn (“Is that correct?”)
  • wizard_create_draft / wizard_update_fields / wizard_publish
"""

from __future__ import annotations

import json, re, uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

from openai import OpenAI                      # ← new 1.x client
from backend.supabase import _SB
from backend.graph      import run_workflow

# ── config ────────────────────────────────────────────────────────────────
EMB_MODEL        = "text-embedding-3-small"
_SIM_THRESHOLD   = 0.50          # vector cut-off (was 0.60)

TENANT           = "default"
BUCKET           = "templates"

_OA = OpenAI()                   # single shared client


# ╔══════════════════════════════════════════════════════════════════════╗
# ║ 1.  FIND SIMILAR TASKS (vector + keyword)                            ║
# ╚══════════════════════════════════════════════════════════════════════╝
def _embed(text: str) -> List[float]:
    return _OA.embeddings.create(model=EMB_MODEL, input=text).data[0].embedding


def wizard_find_similar(
    description: str,
    *,
    top_k: int = 5,
    threshold: float | None = None,
) -> List[dict]:
    """Return ≤ top_k tasks whose cosine-sim ≥ threshold."""
    th = _SIM_THRESHOLD if threshold is None else threshold
    try:
        q_vec = _embed(description)
        res = _SB.rpc(
            "wizard_task_lookup",
            {"query_embedding": q_vec, "top_k": top_k},
        ).execute()

        seen, ranked = set(), []
        for item in res.data or []:
            if float(item["score"]) < th:
                continue
            row = item["task_row"]
            if row["task"] not in seen:
                ranked.append(row)
                seen.add(row["task"])
        return ranked

    except Exception:
        # fall back to legacy keyword router
        hit = run_workflow(description)
        return [hit] if hit.get("ui_event") != "wizard_offer" else []


# ╔══════════════════════════════════════════════════════════════════════╗
# ║ 2.  START PLAN-CHAT                                                  ║
# ╚══════════════════════════════════════════════════════════════════════╝
_CHAT_SYS = (
    "You are the Workflow Wizard planner. Restate the user's goal in one short "
    "paragraph: mention inputs, processing, and output. End with 'Is that correct?'"
)

def wizard_start_plan_chat(goal: str) -> List[dict]:
    resp = _OA.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _CHAT_SYS},
            {"role": "user",   "content": goal},
        ],
        temperature=0.3,
    )
    first = resp.choices[0].message.content.strip()
    return [{"role": "assistant", "content": first}]


# ╔══════════════════════════════════════════════════════════════════════╗
# ║ 3.  DRAFT CRUD                                                       ║
# ╚══════════════════════════════════════════════════════════════════════╝
def _upload_template(file) -> Tuple[str, bytes]:
    raw = file.getvalue()
    ext = file.name.split(".")[-1].lower()
    template_id = uuid.uuid4().hex
    path = f"{TENANT}/{template_id}.{ext}"

    _SB.storage.from_(BUCKET).upload(path, raw, {"content-type": file.type})
    _SB.table("templates").insert(
        dict(template_id=template_id,
             filename=file.name,
             bucket_path=path,
             tenant_id=TENANT),
    ).execute()
    return template_id, raw


def _extract_placeholders(raw: bytes) -> List[str]:
    return re.findall(r"{{\s*([a-zA-Z0-9_]+)\s*}}", raw.decode(errors="ignore"))


def _field(name: str) -> Dict[str, Any]:
    return {
        "name":   name,
        "label":  name.replace("_", " ").title(),
        "widget": "text_input",
    }


def wizard_create_draft(goal: str, template_file) -> Tuple[bool, str]:
    if not goal.strip():
        return False, "Goal required"

    template_id, fields = None, []
    if template_file:
        template_id, raw = _upload_template(template_file)
        fields = [_field(f) for f in _extract_placeholders(raw)]

    draft_id = uuid.uuid4().hex
    _SB.table("wizard_drafts").insert(
        dict(
            draft_id=draft_id,
            tenant_id=TENANT,
            goal=goal.strip(),
            template_id=template_id,
            required_fields=json.dumps(fields),
            step=1,
        )
    ).execute()
    return True, draft_id


class wizard_update_fields:
    """Tiny namespace with load / save helpers."""

    @staticmethod
    def load(draft_id: str):
        row = (
            _SB.table("wizard_drafts")
            .select("*")
            .eq("draft_id", draft_id)
            .single()
            .execute()
            .data
        )
        if not row:
            return None
        row["required_fields"] = json.loads(row["required_fields"] or "[]")
        return type("Draft", (), row)

    @staticmethod
    def save(draft_id: str, fields: List[Dict[str, Any]]):
        _SB.table("wizard_drafts").update(
            {"required_fields": json.dumps(fields)}
        ).eq("draft_id", draft_id).execute()


def wizard_publish(draft) -> Tuple[bool, str]:
    """Insert processor_chains + task_manifest rows, mark draft published."""
    try:
        chain_id = f"doc_chain_{uuid.uuid4().hex[:6]}"
        task_id  = f"draft_{uuid.uuid4().hex[:4]}"

        chain_json = {
            "type": "json_graph",
            "version": "1.0",
            "entry": "doc_runner",
            "risk_level": "low",
            "cost_guard": {},
            "nodes": {
                "doc_runner": {
                    "id": "doc_runner",
                    "class_path": "backend.processors.doc_template.DocTemplateRunner",
                    "init_kwargs": {"template_id": draft.template_id},
                }
            },
        }

        _SB.table("processor_chains").insert(
            dict(chain_id=chain_id,
                 tenant_id=TENANT,
                 chain_json=json.dumps(chain_json),
                 enabled=True)
        ).execute()

        _SB.table("task_manifest").insert(
            dict(task=task_id,
                 tenant_id=TENANT,
                 phrase_examples=json.dumps([draft.goal]),
                 required_fields=json.dumps(draft.required_fields),
                 processor_chain_id=chain_id,
                 output_type="download_link",
                 enabled=True)
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
    "wizard_create_draft",
    "wizard_update_fields",
    "wizard_publish",
]
