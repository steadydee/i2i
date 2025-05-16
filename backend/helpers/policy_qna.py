"""
backend.helpers.policy_qna
--------------------------
Reusable helper for Employee Handbook Q&A using RAG and DB-backed prompt.
Expected fields: question (str), doc_id (optional, default 'handbook_2024')
Returns: dict ({"ui_event": "text", "content": ..., "preview": [...]})
"""
from textwrap import shorten
from backend.vector_search import SupaRetriever
from backend.llm import call_llm

def run(question: str, doc_id: str = "handbook_2024", **kwargs):
    # Retrieve relevant context chunks from vector DB
    retriever = SupaRetriever("vector_chunks", doc_id=doc_id, k=6)
    docs = retriever.get_relevant_documents(question)

    context = "\n\n---\n".join(d.page_content for d in docs) if docs else ""

    # Call universal LLM helper with DB-backed prompt
    answer = call_llm(
        "policy_qa",
        {"CONTEXT": context, "QUESTION": question}
    )

    # Chunk preview for UI
    preview = [
        {
            "doc_id": d.metadata.get("doc_id", ""),
            "sim": float(d.metadata.get("dist", 1)),
            "brief": shorten(d.page_content, width=80, placeholder="…"),
            "content": d.page_content,
        }
        for d in docs
    ]

    return {
        "ui_event": "text",
        "content": answer,
        "preview": preview,
    }
