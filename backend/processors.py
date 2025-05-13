"""
Processor registry
──────────────────────────────────────────────────────────────────────────────
Loads rows from `processor_chains`, builds LangChain runnables, and wires the
retriever step into RetrievalQA without passing duplicate arguments.
"""
from __future__ import annotations

import importlib
import json
from typing import Any, Callable, Dict, List

from langchain_core.runnables import Runnable, RunnableLambda
from backend.db import sb

REG: Dict[str, Runnable] = {}


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
def _resolve_class(path: str):
    module_path, _, attr = path.rpartition(".")
    module = importlib.import_module(module_path)
    return getattr(module, attr)


def _build_general(cls, init_kwargs: dict[str, Any]) -> Runnable:
    if isinstance(cls, type) and issubclass(cls, Runnable):
        obj: Runnable | Callable = cls(**init_kwargs)
    else:
        obj = cls
    if not isinstance(obj, Runnable):
        obj = RunnableLambda(lambda x, _fn=obj: _fn(x))
    return obj


def _compose(runnables: List[Runnable]) -> Runnable:
    chain: Runnable = runnables[0]
    for nxt in runnables[1:]:
        chain = chain | nxt
    return chain


# --------------------------------------------------------------------------- #
# Chain builder                                                               #
# --------------------------------------------------------------------------- #
def _build_chain(spec: dict | str) -> Runnable:
    data = json.loads(spec) if isinstance(spec, str) else spec
    steps_def = [s for s in data["steps"] if "class_path" in s]

    runnables: List[Runnable] = []
    for step in steps_def:
        path = step["class_path"]
        cls = _resolve_class(path)
        init_kwargs = dict(step.get("init_kwargs", {}))
        method = step.get("method")
        m_kwargs = step.get("method_kwargs", {})

        # ---- RetrievalQA wiring ------------------------------------------- #
        if path.endswith(".RetrievalQA"):
            from langchain_openai import ChatOpenAI

            if not runnables:
                raise ValueError("RetrievalQA cannot be the first step")

            retriever = runnables[-1]
            if init_kwargs.get("retriever") == "{{retrieve}}":  # *** patched line
                init_kwargs.pop("retriever")                    # remove duplicate

            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
            runnable = cls.from_chain_type(llm=llm, retriever=retriever, **init_kwargs)
        else:
            runnable = _build_general(cls, init_kwargs)
            if method:
                runnable = getattr(runnable, method)(**m_kwargs)  # type: ignore

        runnables.append(runnable)

    if not runnables:
        raise ValueError("No runnable steps built")

    return _compose(runnables)


# --------------------------------------------------------------------------- #
# Registry loader                                                             #
# --------------------------------------------------------------------------- #
def load_all() -> None:
    rows = (
        sb()
        .table("processor_chains")
        .select("chain_id,chain_json")
        .execute()
        .data
    )
    for row in rows:
        REG[row["chain_id"]] = _build_chain(row["chain_json"])


load_all()
