from pydantic import BaseModel
from backend.graph import run_workflow


def _d(x):          # unwrap Pydantic model → dict
    return x.model_dump() if isinstance(x, BaseModel) else x


def test_draft_sow():
    prompt = "I need a SOW for Acme"
    state  = _d(run_workflow(prompt))        # initial call

    answers = {}                             # accumulate answers here

    # loop at most 5 times to avoid infinite hang
    for _ in range(5):
        if state["ui_event"] != "form":
            break

        # merge new fields into the growing answers dict
        for f in state["fields"]:
            answers[f["name"]] = "test"

        # replay SAME prompt with cumulative answers
        state = _d(run_workflow(prompt, {"user_inputs": answers}))

    # final assertions
    assert state["ui_event"] == "download_link"
    assert state["url"].startswith("https://")
