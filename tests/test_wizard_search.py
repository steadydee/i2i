import os
from backend.wizard import wizard_find_similar

PHRASE = "create an SOW"

def test_sow_found():
    """
    Smoke-test: the phrase should surface the existing draft_sow task
    via wizard_find_similar().
    """
    hits = wizard_find_similar(PHRASE, top_k=5)
    task_ids = [row["task"] for row in hits]
    assert "draft_sow" in task_ids, f"'draft_sow' not in {task_ids}"
