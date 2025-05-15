"""
backend.vector_search
────────────────────────────────────────────────────────
Similarity-search helper for Supabase / pgvector.
"""

from __future__ import annotations

import json
from typing import List, Dict, Any

from backend.supabase import _SB, _embed


class SupaRetriever:
    """
    Retrieve top-k chunks from any table that stores (embedding, content, metadata).

    Parameters
    ----------
    table_name : str
        PostgreSQL table to search (default “vector_chunks”).
    k : int
        Number of chunks to return.
    tenant : str
        Tenant filter.
    doc_id : str | None
        Optional doc_id filter.
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

    # LangChain-style
    def get_relevant_documents(self, query: str) -> List[Dict[str, Any]]:
        vec = _embed(query)

        # Always use the PL/pgSQL wrapper — avoids “materialize mode” error
        fn_name = "match_vectors"

        res = (
            _SB.rpc(
                fn_name,
                {
                    "table_name": self.table_name,   # ignored by wrapper but harmless
                    "q_vec": json.dumps(vec),
                    "k": self.k,
                    "tenant": self.tenant,
                    "doc_id": self.doc_id,
                },
            )
            .execute()
            .data
        )

        return [
            {"page_content": r["content"], "metadata": r["metadata"]}
            for r in res
        ]
