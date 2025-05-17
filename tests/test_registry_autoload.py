"""
Confirms that REG still contains the two built-ins even after auto-load.
No DB mutation needed: we just call reload_registry() and inspect keys.
"""
from backend.processors import REG, reload_registry

def test_builtin_chains_still_registered():
    reload_registry()
    assert "doc_draft_chain" in REG
    assert "policy_qna_chain" in REG
