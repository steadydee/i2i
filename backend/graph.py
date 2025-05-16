import traceback

from backend.supabase import fetch_manifest
from backend.processors import run_processor_chain

# ... Any other imports, e.g., LangGraph, etc ...

def run_workflow(prompt):
    # Original logic, not minimal scaffold
    _, manifest = fetch_manifest(prompt)
    print("DEBUG [Before workflow state]: manifest =", manifest)
    if not manifest:
        print("DEBUG [No manifest found]")  # More helpful error trace
        return {
            "ui_event": "no_match",
            "message": "No repeatable workflow found for that prompt."
        }

    state = {
        "prompt": prompt,
        "manifest": manifest,
        "step": 0,
        # Add any additional keys you use in your app
    }
    print("DEBUG [Workflow state created]:", state)

    # This may call your LangGraph state machine or other wizard logic
    try:
        result = _GRAPH.invoke(state)  # if using LangGraph, otherwise adjust as needed
    except NameError:
        # If _GRAPH is not used, just fall back to process_node
        result = process_node(state)
    except Exception as e:
        print("DEBUG [run_workflow Exception]:", traceback.format_exc())
        state["error"] = str(e)
        return state

    return result

def process_node(state):
    manifest = state['manifest']
    # Insert your actual processing logic here
    output = run_processor_chain(manifest, state)
    print("DEBUG [Process Node Output]:", output)
    state['output'] = output
    return state

# Export for import
__all__ = ["run_workflow"]
