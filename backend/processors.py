"""
backend/processors.py
--------------------------------------------------
• Validates every processor_chain row against ChainDef.
• Accepts both "init_kwargs" (preferred) and legacy "params".
• Interpolates placeholders in init_kwargs once at load time.
• Registers the runnable in REG dict for fast lookup.
"""

from __future__ import annotations

import importlib
import os
import re
from typing import Any, Dict

from langchain_core.runnables import Runnable, RunnableLambda

from backend.db import sb
from backend.chain_schema import ChainDef  # pydantic models

# public registry
REG: Dict[str, Runnable] = {}

# ── helpers ───────────────────────────────────────────────────────────────
_placeholder_rx = re.compile(r"\{([a-zA-Z0-9_.]+)\}")

def _interp(val: str, ctx: dict[str, Any]) -> str:
    """Replace {a.b} or {ENV_VAR} with values from ctx dict."""
    def repl(m):
        cur: Any = ctx
        for key in m.group(1).split("."):
            cur = cur.get(key, "")
        return str(cur)
    return _placeholder_rx.sub(repl, val)

def _resolve(path: str):
    mod, name = path.rsplit(".", 1)
    return getattr(importlib.import_module(mod), name)

# ── build one chain --------------------------------------------------------
def _build_chain(def_json: dict) -> Runnable:
    chain_def = ChainDef.parse_obj(def_json)   # raises on bad JSON

    chain: Runnable = RunnableLambda(lambda x: x)  # start with identity
    for step in chain_def.steps:
        cls = _resolve(step.class_path)

        # kwargs with placeholder interpolation
        ctx = {"env": os.environ}
        init_kwargs = {
            k: (_interp(v, ctx) if isinstance(v, str) else v)
            for k, v in step.init_kwargs.items()
        }

        runnable: Runnable = cls(**init_kwargs)

        # IMPORTANT: use .invoke so result passes through
        chain = chain | RunnableLambda(lambda x, fn=runnable: fn.invoke(x))

    return chain

# ── load all rows at startup ----------------------------------------------
def load_all() -> None:
    rows = (
        sb()
        .table("processor_chains")
        .select("chain_id, chain_json, enabled")
        .execute()
        .data
    )
    for row in rows:
        if not row.get("enabled", True):
            continue
        try:
            REG[row["chain_id"]] = _build_chain(row["chain_json"])
        except Exception as e:
            # disable bad chains so runtime stays healthy
            sb().table("processor_chains").update({"enabled": False}).eq("chain_id", row["chain_id"]).execute()
            print(f"[processors] ⚠️ disabled broken chain {row['chain_id']}: {e}")

load_all()
# ───────────────── policy_qna_chain (temporary stub) ─────────────────
#
# This keeps the graph from crashing until we wire up the real RAG-based
# policy lookup. It simply echoes the question back with a “TODO” note.

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable

_policy_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an HR assistant. "
        "Respond briefly and flag that the full policy search is not yet implemented."
    ),
    ("human", "{question}")
])

policy_qna_chain: Runnable = _policy_prompt | ChatOpenAI(model_name="gpt-3.5-turbo")

# register in the global registry
REG["policy_qna_chain"] = policy_qna_chain
# ───────────────── policy_qna_chain (temporary stub) ─────────────────
#
# Maps the graph’s {"user_input": "..."} into the prompt’s {"question": "..."}.

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable, RunnableLambda

_policy_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an HR assistant. "
        "Respond briefly and flag that the full policy search is not yet implemented."
    ),
    ("human", "{question}")
])

# Map input → {"question": user_input}
_input_mapper: Runnable = RunnableLambda(
    lambda d: {"question": d["user_input"]}
)

policy_qna_chain: Runnable = _input_mapper | _policy_prompt | ChatOpenAI(model_name="gpt-3.5-turbo")

REG["policy_qna_chain"] = policy_qna_chain
from langchain_core.runnables import RunnableLambda

# … existing _input_mapper | _policy_prompt | ChatOpenAI …

policy_qna_chain: Runnable = (
    _input_mapper
    | _policy_prompt
    | ChatOpenAI(model_name="gpt-3.5-turbo")
    | RunnableLambda(lambda m: m.content)   # ← NEW: return plain string
)

REG["policy_qna_chain"] = policy_qna_chain
