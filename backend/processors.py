"""
Processor-chain registry
========================

Every entry maps a `chain_id` ➜ LangChain Runnable.

• **doc_draft_chain** → fills a DOCX template via DocxRender and returns
  a signed download link.

• **policy_qna_chain** → stub that will eventually call the RAG layer.

Extend this file whenever you add new processor chains; the graph loads
them dynamically via REG.
"""
from typing import Dict, Any
from langchain_core.runnables import RunnableLambda

from backend.tools.docx_render import DocxRender


# ---------------------------------------------------------------------
# Central registry
# ---------------------------------------------------------------------
REG: Dict[str, Any] = {}


# ---------------------------------------------------------------------
# 1. doc_draft_chain  – SOW generator (template-driven)
# ---------------------------------------------------------------------
def _sow_chain(payload: Dict[str, Any]) -> Dict[str, Any]:
    # metadata.template_id is set in task_manifest
    tpl_id  = payload["metadata"]["template_id"]
    inputs  = payload["inputs"]          # answers captured by Gather
    return DocxRender(tpl_id).invoke(inputs)   # returns {"ui_event":"download_link", ...}

REG["doc_draft_chain"] = RunnableLambda(_sow_chain)


# ---------------------------------------------------------------------
# 2. policy_qna_chain  – placeholder until RAG is wired
# ---------------------------------------------------------------------
def _policy_qna(payload: Dict[str, Any]) -> Dict[str, Any]:
    question = payload.get("prompt", "(no question)")
    return {
        "ui_event": "text",
        "content": f"*Policy-Q&A stub*\n\nYour question:\n{question}\n\n"
                   "(RAG answer goes here.)"
    }

REG["policy_qna_chain"] = RunnableLambda(_policy_qna)
