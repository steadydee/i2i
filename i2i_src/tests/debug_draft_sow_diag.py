"""
Diagnostic: prints the list of missing fields Gather keeps requesting.
Run it with:  python tests/debug_draft_sow_diag.py
"""
from pydantic import BaseModel
from backend.graph import run_workflow

def _d(x):            # unwrap WorkflowState → dict
    return x.model_dump() if isinstance(x, BaseModel) else x

prompt = "I need a SOW for Acme"
state  = _d(run_workflow(prompt))
round_ = 0

while state.get("ui_event") == "form" and round_ < 5:
    round_ += 1
    missing = [f["name"] for f in state["fields"]]
    print(f"ROUND {round_} – Gather still wants: {missing}")

    # feed the missing fields
    answers = {n: "test" for n in missing}

    # build next state: preserve manifest etc., merge cumulative answers
    next_state = state.copy()
    next_state.pop("ui_event", None)
    next_state.pop("fields", None)
    next_state["user_inputs"] = {
        **next_state.get("user_inputs", {}),
        **answers,
    }

    state = _d(run_workflow(prompt, next_state))

print("\nFINAL STATE:", state)
