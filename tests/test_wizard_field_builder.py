from backend.wizard import wizard_step_2

def test_sow_template_fields_present():
    sel = {"type":"template","value":{"template_id":"sow_v1"}}
    evt = wizard_step_2(sel)
    assert evt["step"] == 2
    assert len(evt["required_fields"]) >= 3
