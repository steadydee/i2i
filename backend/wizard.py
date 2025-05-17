from typing import Dict, Any, List
from backend.plan_builder import generate_plan

# ─── Step 1: goal → suggestions / AI plan ───────────────────────────────
def wizard_step_1(goal: str) -> Dict[str, Any]:
    goal_lower = goal.lower()

    suggestions: List[Dict[str, Any]] = []
    if "sow" in goal_lower:
        suggestions.append({
            "template_id": "sow_v1",
            "label":       "Statement of Work (Standard)",
            "description": "Draft a client SOW with customizable sections"
        })

    llm_plan = generate_plan(goal) if not suggestions else []

    suggestions.append({
        "template_id": "blank",
        "label":       "Start from Scratch",
        "description": "No template; build a workflow step by step"
    })

    node_types = [
        {"type":"DocDraftRunnable", "label":"Document Draft"},
        {"type":"EmailTemplateRunnable", "label":"Email Template"},
    ]

    return {
        "ui_event":            "wizard_step",
        "step":                1,
        "goal":                goal,
        "suggested_templates": suggestions,
        "suggested_node_types":node_types,
        "llm_plan":            llm_plan,
    }

# ─── Step 2: template / plan → required_fields skeleton ────────────────
def wizard_step_2(selection: Dict[str, Any]) -> Dict[str, Any]:
    """
    `selection` comes from the UI after Step 1:
        {"type": "template" | "llm_plan", "value": …}
    Returns a wizard_step event with an initial required_fields list that
    the front-end will let the user edit.
    """
    sel_type = selection["type"]
    val      = selection["value"]

    if sel_type == "template" and val["template_id"] == "sow_v1":
        fields = [
            {"name":"client",           "label":"Client",            "widget":"text_input"},
            {"name":"application_name","label":"Application Name",  "widget":"text_input"},
            {"name":"duration",         "label":"Duration (months)", "widget":"number_input"},
            {"name":"cost",             "label":"Cost (USD)",        "widget":"number_input"},
            {"name":"application_type", "label":"Application Type",  "widget":"text_input"},
        ]
    elif sel_type == "llm_plan":
        # very first cut: start with an empty list; user adds fields manually
        fields = []
    else:   # "blank" template
        fields = []

    return {
        "ui_event":      "wizard_step",
        "step":          2,
        "required_fields": fields,
        "selection":     selection,   # echo for the UI
    }
