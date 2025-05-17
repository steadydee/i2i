"""
Minimal confidence test:
• SOW → should produce a form
• Policy Q&A → should produce plain text

Run:  pytest -q
"""

from backend.graph import run_workflow


def _ui_event(prompt: str, answers=None):
    """Helper: run workflow and always return the ui_event dict."""
    evt = run_workflow(prompt, answers or {})
    return evt.get("output", evt)      # legacy helper returns {"output":{…}}


def test_sow_form():
    ui_evt = _ui_event("I need a SOW for Acme")
    assert ui_evt["ui_event"] == "form", f"Expected 'form', got {ui_evt}"


def test_policy_qna():
    ui_evt = _ui_event("do employees get military leave")
    assert ui_evt["ui_event"] == "text", f"Expected 'text', got {ui_evt}"
