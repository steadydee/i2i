from backend.helpers import helpers_registry

def run_processor_chain(manifest, state):
    """
    Dispatches to the correct helper based on processor_chain_id in manifest.
    Handles argument mapping for helpers that expect different field names.
    """
    helper_name = manifest["processor_chain_id"]
    helper_func = helpers_registry.get(helper_name)
    if not helper_func:
        raise ValueError(f"No helper registered for: {helper_name}")

    # Argument mapping (can expand as you add more helpers)
    # For policy_qna, map 'prompt' -> 'question'
    if helper_name == "policy_qna_chain" and "prompt" in state:
        state = dict(state)  # avoid mutating caller's state
        state["question"] = state.pop("prompt")
    
    return helper_func(**state)
