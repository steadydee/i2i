from backend.intent# --- drop-in replacement for the helper inside backend/processors.py ---------
from __future__ import annotations
from textwrap import shorten
from typing import Dict, List

from langchain_core.documents import Document
from backend.vector_search import SupaRetriever
from backend.intent import TENANT_ID
from backend.state import ui_event_text   # whatever helper you already have

def _policy_qna(question: str) -> Dict:
    """
    RAG over the employee handbook.
    Returns a ui_event:text plus a debug preview list with both
    a one-liner 'brief' and the full chunk text.
    """
    retriever = SupaRetriever(
        k=12,                   # wider net
        tenant=TENANT_ID,
        doc_id="handbook_2024",
    )
    docs: List[Document] = [
        d for d in retriever.get_relevant_documents(question)
        if d.metadata.get("dist", 1) < 0.30           # keep close matches
    ]

    # build preview rows --------------------------------------------------
    preview = []
    for d in docs:
        sim = d.metadata.get("dist", 1)
        preview.append({
            "sim":   sim,
            "doc_id": d.metadata.get("doc_id", ""),
            "brief": shorten(d.page_content.replace("\n", " "), width=80),
            "full":  d.page_content.strip(),
        })

    # Make the final answer (very simple prompt for now) ------------------
    context = "\n\n---\n".join(d.page_content for d in docs) if docs else ""
    answer  = (
        "I couldn’t find that in the handbook."
        if not docs else
        f"**Answer (with context):**\n\n{context}"
    )

    return {
        "ui_event": "text",
        "content":  answer,
        "preview":  preview,        # ← passed through to the UI
    }
