"""
Smoke-test: draft_sow helper via generic_function_chain.

We call run_workflow() once with a complete user_inputs payload and
expect Deliver to return a download link.
"""
from pydantic import BaseModel
from backend.graph import run_workflow


def _d(obj):
    return obj.model_dump() if isinstance(obj, BaseModel) else obj


def test_draft_sow():
    prompt = "I need a SOW for Acme"

    answers = {
        "client":            "Acme Corp",
        "cost":              100000,
        "duration":          5,
        "application_name":  "Acme Portal",
        "application_type":  "Web",
    }

    state = _d(run_workflow(prompt, {"user_inputs": answers}))

    assert state["ui_event"] == "download_link"
    assert state["url"].startswith("https://")
