"""
backend.tools.function_runner
-----------------------------
A single entry-point for *any* helper function.

Allows new workflows to be registered by pointing the manifest’s
`metadata.function_path` at a callable written as:

    pkg.module:func_name

The callable will receive **all** fields gathered from the user
as keyword arguments and must return a dict that includes a
`"ui_event"` key (e.g. "text", "markdown", "download_link").
That dict is merged back into the graph state by the Process node.
"""
from __future__ import annotations

import importlib
from typing import Any, Dict


def run(function_path: str, **kwargs: Any) -> Dict[str, Any]:
    """
    Dynamically import and execute a helper.

    Parameters
    ----------
    function_path :
        Import path in the form ``"package.module:function"``.
    **kwargs :
        Arbitrary keyword arguments gathered from the user (or
        supplied by previous nodes). They are forwarded unchanged
        to the helper.

    Returns
    -------
    Dict[str, Any]
        Whatever the helper returns. Must include ``"ui_event"`` so
        the Deliver node knows how to present the result.
    """
    try:
        module_name, func_name = function_path.split(":", 1)
    except ValueError as exc:
        raise ValueError(
            f"function_path must be 'module.sub:func', got '{function_path}'"
        ) from exc

    module = importlib.import_module(module_name)
    try:
        func = getattr(module, func_name)
    except AttributeError as exc:
        raise ImportError(
            f"Could not find function '{func_name}' in module '{module_name}'"
        ) from exc

    if not callable(func):
        raise TypeError(f"Target '{function_path}' is not callable")

    result = func(**kwargs)
    if not isinstance(result, dict) or "ui_event" not in result:
        raise ValueError(
            "Helper must return a dict that includes a 'ui_event' key "
            f"(got {type(result).__name__})"
        )
    return result
