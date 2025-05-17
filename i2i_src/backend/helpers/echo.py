"""
backend.helpers.echo
--------------------
Tiny helper for smoke-tests.

It receives one text field (`message`) and returns it verbatim in a
plain-text ui_event. Designed to be invoked via the generic_function_chain.
"""

def repeat(message: str, **_) -> dict:
    """Return the same text that was provided."""
    return {"ui_event": "text", "content": message}
