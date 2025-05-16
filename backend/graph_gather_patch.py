# ─────────────────────────────────────────────────────────────────────────────
# NEW Gather node – wraps the form inside a proper `ui_event` envelope
# ─────────────────────────────────────────────────────────────────────────────
def gather_node(state: AddableValuesDict) -> AddableValuesDict:
    state = _avd(state)
    mf    = state.manifest

    # Which required fields are still missing?
    need = [f for f in mf["required_fields"] if f not in state.get("answers", {})]

    if need:
        return state + AddableValuesDict(
            ui_event={
                "ui_event": "form",
                "fields": [
                    {
                        "name":   n,
                        "widget": "text_input",
                        "label":  n.replace("_", " ").title(),
                    }
                    for n in need
                ],
            }
        )

    # Nothing missing → go straight to Process
    return state
