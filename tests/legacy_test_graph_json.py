import backend.graph as g

def test_json_graph_linear(monkeypatch):
    # create two stub runnables in memory ------------------------------
    class A:
        def __init__(self, x=1): pass
        def run(self, ctx, st): return {"a": 1}

    class B:
        def __init__(self): pass
        def run(self, ctx, st): return {"b": 2}

    monkeypatch.setitem(
        g.PROCESSORS,
        "dummy_chain",
        A  # not used, but keeps _fetch_chain happy when fallback path hits
    )

    spec = {
        "type": "json_graph",
        "entry": "first",
        "nodes": {
            "first":  {"type": "__main__.A", "params": {}, "next": ["second"]},
            "second": {"type": "__main__.B", "params": {}}
        },
    }

    # Fake _fetch_chain to return our spec instead of a DB row ----------
    monkeypatch.setattr(
        g, "_fetch_chain",
        lambda chain_id: {"chain_id": "x", "chain_json": spec}
    )

    res = g.run_workflow("hello", tenant_id="test")
    assert res["output"] == {"b": 2}
    assert "node_outputs" in res["extra"]
