"""
Processor-chain registry
========================
Maps `chain_id` ➜ LangChain Runnable.

Chains implemented so far
-------------------------
• **doc_draft_chain**         – Fill a DOCX template, return download link  
• **generic_function_chain**  – Call any helper via function_runner  
• **policy_qna_chain**        – RAG placeholder (returns stub)

The Process node looks up `PROC_REG[chain_id]` to execute the chain.
"""
from typing import Dict, Any

from langchain_core.runnables import RunnableLambda

from backend.tools.docx_render import DocxRender
from backend.tools.function_runner import run as function_runner


# ---------------------------------------------------------------------
# Central registry
# ---------------------------------------------------------------------
REG: Dict[str, Any] = {}


# ---------------------------------------------------------------------
# 1. doc_draft_chain  – DOCX template generator
# ---------------------------------------------------------------------
def _doc_draft_chain(payload: Dict[str, Any]) -> Dict[str, Any]:
    tpl_id  = payload["metadata"]["template_id"]
    inputs  = payload["inputs"] or {}
    return DocxRender(tpl_id).invoke(inputs)          # → {"ui_event":"download_link", ...}

REG["doc_draft_chain"] = RunnableLambda(_doc_draft_chain)


# ---------------------------------------------------------------------
# 2. generic_function_chain  – dynamic helper runner
# ---------------------------------------------------------------------
def _generic_chain(payload: Dict[str, Any]) -> Dict[str, Any]:
    func_path = payload["metadata"]["function_path"]           # e.g. backend.helpers.echo:repeat
    inputs    = payload["inputs"] or {}
    return function_runner(func_path, **inputs)                # helper must return {"ui_event": ...}

REG["generic_function_chain"] = RunnableLambda(_generic_chain)


# ---------------------------------------------------------------------
# 3. policy_qna_chain  – stub until RAG is wired
# ---------------------------------------------------------------------
def _policy_qna(payload: Dict[str, Any]) -> Dict[str, Any]:
    question = payload.get("prompt", "(no question)")
    return {
        "ui_event": "text",
        "content": f"*Policy-Q&A stub*\n\nYour question:\n{question}\n\n"
                   "(RAG answer goes here.)"
    }

REG["policy_qna_chain"] = RunnableLambda(_policy_qna)
