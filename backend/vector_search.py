"""
backend.vector_search
────────────────────────────────────────────────────────
Similarity-search helper that hides Supabase quirks.

• For the standard `vector_chunks` table we call the JSON wrapper
  `search_vector_chunks` (avoids “materialize mode required”).
• For any other table we fall back to the generic `match_vectors`.
"""

from __future__ import annotations

import json
from typing import List

from langchain_core.documents import Document

from backend.supabase import _SB, _embed


class SupaRetriever:
    """
    Parameters
    ----------
    table_name : str   Table that stores (embedding, content, metadata)
    k          : int   Number of chunks to return
    tenant     : str   Tenant filter
    doc_id     : str   Optional doc-ID filter
    """

    def __init__(
        self,
        table_name: str = "vector_chunks",
        *,
        k: int = 4,
        tenant: str = "default",
        doc_id: str | None = None,
    ) -> None:
        self.table_name = table_name
        self.k = k
        self.tenant = tenant
        self.doc_id = doc_id

    # ------------------------------------------------------------------ #
    # LangChain-style interface
    # ------------------------------------------------------------------ #
    def get_relevant_documents(self, query: str) -> List[Document]:
        q_vec = json.dumps(_embed(query))

        if self.table_name == "vector_chunks":
            fn_name = "search_vector_chunks"
            params = {
                "q_vec": q_vec,
                "k": self.k,
                "tenant": self.tenant,
            }
            if self.doc_id is not None:
                params["p_doc_id"] = self.doc_id
        else:
            fn_name = "match_vectors"
            params = {
                "table_name": self.table_name,
                "q_vec": q_vec,
                "k": self.k,
                "tenant": self.tenant,
                "doc_id": self.doc_id,
            }

        rows = _SB.rpc(fn_name, params).execute().data

        docs: List[Document] = []
        for r in rows:
            raw_meta = r.get("metadata") or {}
            meta = json.loads(raw_meta) if isinstance(raw_meta, str) else raw_meta
            if "dist" in r:
                meta["dist"] = r["dist"]
            if "doc_id" in r:
                meta["doc_id"] = r["doc_id"]
            docs.append(Document(page_content=r["content"], metadata=meta))

        return docs
