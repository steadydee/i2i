from backend.plan_builder import generate_plan

def test_generate_plan_returns_list():
    plan = generate_plan("Draft an NDA and email it")
    assert isinstance(plan, list)
