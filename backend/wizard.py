from typing import Dict, Any

def wizard_step_1(goal: str) -> Dict[str, Any]:
    goal_lower = goal.lower()
    suggestions = []
    llm_plan = []

    # Template matching
    if "sow" in goal_lower or "statement of work" in goal_lower:
        suggestions.append({
            "template_id": "sow_v1",
            "label": "Statement of Work (Standard)",
            "description": "Use this for client SOWs, customizable sections"
        })
    if "email" in goal_lower:
        suggestions.append({
            "template_id": "email_blank",
            "label": "Blank Email Template",
            "description": "Create a custom email template from scratch"
        })

    # LLM Planning (for now, basic demo)
    if not suggestions:
        if "contract" in goal_lower:
            llm_plan = [
                {"type": "DocDraftRunnable", "label": "Draft Contract"},
                {"type": "EmailTemplateRunnable", "label": "Email Contract"}
            ]
        else:
            llm_plan = [
                {"type": "DocDraftRunnable", "label": "Draft Document"}
            ]

    # Always allow start from scratch
    suggestions.append({
        "template_id": "blank",
        "label": "Start from Scratch",
        "description": "No template, build your own workflow step by step"
    })

    node_types = [
        {
            "type": "DocDraftRunnable",
            "label": "Document Draft",
            "description": "Generate a DOCX or PDF document"
        },
        {
            "type": "EmailTemplateRunnable",
            "label": "Email Template",
            "description": "Draft a custom email for review or sending"
        }
    ]

    return {
        "ui_event": "wizard_step",
        "step": 1,
        "goal": goal,
        "suggested_templates": suggestions,
        "suggested_node_types": node_types,
        "llm_plan": llm_plan
    }

# ───── Test Harness ─────
if __name__ == "__main__":
    from pprint import pprint
    print("Test: SOW Goal")
    result = wizard_step_1("Draft a Statement of Work for Acme")
    pprint(result)
    print("\nTest: Contract Goal")
    result = wizard_step_1("Draft a contract and email it")
    pprint(result)
    print("\nTest: Unknown Goal")
    result = wizard_step_1("Write a board meeting summary")
    pprint(result)
