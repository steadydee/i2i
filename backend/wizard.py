"""
Helpers for the 3-step Workflow Wizard (minimal but working).

* wizard_create_draft()      – Step 1: upload template, extract {{fields}}, insert draft
* wizard_update_fields.*     – Step 2: load / render / save field list
* wizard_publish()           – Step 3: draft → processor_chains + task_manifest

Designed to unblock dev quickly; you can harden parsing, validation,
and governance metadata later.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Tuple, Any

import streamlit as st

from backend.supabase import _SB

BUCKET = "templates"
TENANT_DEFAULT = "default"

# ── low-level helpers ---------------------------------------------------------


def _upload_template(file) -> str:
    """Save uploaded file to Supabase Storage and row in `templates`."""
    data = file.getvalue()  # read bytes once
    ext = Path(file.name).suffix.lower().lstrip(".")
    template_id = uuid.uuid4().hex
    path = f"{TENANT_DEFAULT}/{template_id}.{ext}"

    _SB.storage.from_(BUCKET).upload(path, data, {"content-type": file.type})
    _SB.table("templates").insert(
        {
            "template_id": template_id,
            "tenant_id": TENANT_DEFAULT,
            "path": path,
            "filename": file.name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()
    return template_id, data


def _extract_placeholders(raw: bytes) -> List[str]:
    """Very naive {{placeholder}} extractor (good for txt/md/html)."""
    text = raw.decode("utf-8", errors="ignore")
    return re.findall(r"{{\\s*([a-zA-Z0-9_]+)\\s*}}", text)


def _field_spec(name: str) -> Dict[str, Any]:
    return {
        "name": name,
        "label": name.replace("_", " ").title(),
        "widget": "text_input",
    }


# ── Step 1 – create draft ------------------------------------------------------


def wizard_create_draft(
    goal: str, template_file, tenant: str
) -> Tuple[bool, str]:
    """Returns (True, draft_id) on success; (False, err) on failure."""
    goal = goal.strip()
    if not goal:
        return False, "Goal is required."

    template_id = None
    required_fields: List[Dict[str, Any]] = []

    if template_file:
        template_id, raw = _upload_template(template_file)
        required_fields = [_field_spec(n) for n in _extract_placeholders(raw)]

    draft_id = str(uuid.uuid4())
    _SB.table("wizard_drafts").insert(
        {
            "draft_id": draft_id,
            "tenant_id": tenant,
            "goal": goal,
            "template_id": template_id,
            "required_fields": json.dumps(required_fields),
            "step": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()

    return True, draft_id


# ── Step 2 – field editor ------------------------------------------------------


class _FieldEditor:
    """Namespace so app can call wizard_update_fields.load/render/save."""

    # --- load draft row --------------------------------------------------------
    @staticmethod
    def load(draft_id: str):
        res = (
            _SB.table("wizard_drafts")
            .select("draft_id, required_fields, template_id, goal")
            .eq("draft_id", draft_id)
            .single()
            .execute()
            .data
        )
        if not res:
            return None
        res["required_fields"] = json.loads(res["required_fields"])
        return type("Draft", (), res)  # simple obj with attrs

    # --- render grid (very simple placeholder) --------------------------------
    @staticmethod
    def render_edit_grid(fields: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        st.caption("Field list (editing UI coming soon):")
        st.code(json.dumps(fields, indent=2), language="json")
        return fields  # unchanged for now

    # --- save back -------------------------------------------------------------
    @staticmethod
    def save(draft_id: str, fields: List[Dict[str, Any]]):
        _SB.table("wizard_drafts").update(
            {"required_fields": json.dumps(fields)}
        ).eq("draft_id", draft_id).execute()


wizard_update_fields = _FieldEditor  # re-export


# ── Step 3 – publish -----------------------------------------------------------


def wizard_publish(draft) -> Tuple[bool, str]:
    """
    Turn *draft* (object from load) into live task.
    Returns (True, task_id) or (False, error_msg).
    """
    try:
        chain_id = f"doc_chain_{uuid.uuid4().hex[:6]}"
        task_id = f"task_{uuid.uuid4().hex[:4]}"

        # Minimal runnable chain (single node that merges template + fields)
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

        # Insert processor_chains row
        _SB.table("processor_chains").insert(
            {
                "chain_id": chain_id,
                "tenant_id": TENANT_DEFAULT,
                "chain_json": json.dumps(chain_json),
                "enabled": True,
                "version": "1.0",
            }
        ).execute()

        # Insert task_manifest row
        _SB.table("task_manifest").insert(
            {
                "task": task_id,
                "tenant_id": TENANT_DEFAULT,
                "title": draft.goal[:60],
                "phrase_examples": json.dumps([draft.goal]),
                "required_fields": json.dumps(draft.required_fields),
                "processor_chain_id": chain_id,
                "output_type": "download_link",
                "enabled": True,
            }
        ).execute()

        # Mark draft as published
        _SB.table("wizard_drafts").update(
            {"published_at": datetime.now(timezone.utc).isoformat()}
        ).eq("draft_id", draft.draft_id).execute()

        return True, task_id
    except Exception as e:  # pragma: no cover
        return False, str(e)


# ── public re-exports ----------------------------------------------------------

__all__ = [
    "wizard_create_draft",
    "wizard_update_fields",
    "wizard_publish",
]
