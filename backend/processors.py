"""
backend.processors
──────────────────
Central processor-chain registry.

Maps a `chain_id` → LangChain Runnable that the *Process* node executes.

Chains implemented
------------------
• doc_draft_chain         – Fill a DOCX template, return download link  
• generic_function_chain  – Call any helper via function_runner  
• policy_qna_chain        – Employee-handbook Q&A via RAG (+chunk preview)
"""
from __future__ import annotations

from textwrap import shorten
from typing import Any, Dict, List

from langchain_core.runnables import RunnableLambda
from langchain_core.prompts   import ChatPromptTemplate
from langchain_openai         import ChatOpenAI

from backend.tools.docx_render    import DocxRender
from backend.tools.function_runner import run as function_runner
from backend.vector_search        import SupaRetriever

# ───────────────────────── registry container ───────────────────────────
REG: Dict[str, Any] = {}

# ───────────────────────── 1. DOCX draft chain ──────────────────────────
def _doc_draft_chain(payload: Dict[str, Any]) -> Dict[str, Any]:
    tpl_id  = payload["metadata"]["template_id"]
    inputs  = payload.get("inputs") or {}
    return DocxRender(tpl_id).invoke(inputs)          # → {"ui_event":"download_link", ...}

REG["doc_draft_chain"] = RunnableLambda(_doc_draft_chain)

# ───────────────────────── 2. generic helper chain ──────────────────────
def _generic_chain(payload: Dict[str, Any]) -> Dict[str, Any]:
    func_path = payload["metadata"]["function_path"]          # e.g. backend.helpers.echo:repeat
    inputs    = payload.get("inputs") or {}
    return function_runner(func_path, **inputs)               # helper must return {"ui_event": …}

REG["generic_function_chain"] = RunnableLambda(_generic_chain)

# ───────────────────────── 3. policy-Q&A chain ──────────────────────────
_LLM = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

_POLICY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are the Exfil Security Employee-Handbook assistant. "
     "Answer the user question **only** from the provided excerpts. "
     "If the answer is not present, say you don’t have that information."),
    ("user", "{question}\n\nContext:\n{context}"),
])

def _policy_qna(payload: Dict[str, Any]) -> Dict[str, Any]:
    # —— inputs ——————————————————————————
    question: str = (
        payload.get("prompt")
        or payload.get("inputs", {}).get("question")
        or "(no question)"
    )
    meta   = payload.get("metadata") or {}
    doc_id = meta.get("doc_id", "handbook_2024")

    # —— retrieve chunks ——————————————————
    retriever = SupaRetriever("vector_chunks", doc_id=doc_id, k=6)
    docs      = retriever.get_relevant_documents(question)      # langchain Documents

    context = "\n\n---\n".join(d.page_content for d in docs) if docs else ""

    # —— LLM answer ————————————————————
    answer = _LLM.invoke(
        _POLICY_PROMPT.format(question=question, context=context)
    ).content

    # —— chunk preview for the UI ————
    preview: List[Dict] = []
    for d in docs:
        dist = d.metadata.get("dist")
        sim  = round(1 - dist, 3) if isinstance(dist, (float, int)) else None
        preview.append({
            "sim": sim,
            "doc_id": d.metadata.get("doc_id", ""),
            "content": shorten(d.page_content.replace("\n", " "), width=80),
        })

    return {
        "ui_event": "text",
        "content":  answer,
        "debug": {
            "source_doc_id": doc_id,
            "chunks": len(docs),
            "preview": preview,
        },
    }

REG["policy_qna_chain"] = RunnableLambda(_policy_qna)

# ───────────────────────── registry aliases (keep all callers happy) ────
RUNNABLE_REG = REG          # new canonical name
REGISTRY     = REG          # back-compat for newer code
# older code already imports REG
