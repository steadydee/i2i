from backend.graph import reload_graph
from backend.processors import REG

def test_reload_graph_refreshes_registry():
    before = set(REG.keys())
    reload_graph()
    after  = set(REG.keys())
    assert before == after            # still contains built-ins
