"""
backend/tools/supabase_retriever.py
A BaseRetriever that queries an existing Supabase pgvector table.
Relies on SUPABASE_URL / SUPABASE_KEY / OPENAI_API_KEY env vars.
"""

from __future__ import annotations
import os
from typing import Any, List

from supabase import create_client, Client
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings


class SupabaseRetriever(BaseRetriever):
    def __init__(
        self,
        table_name: str = "documents",
        top_k: int = 4,
        search_type: str = "similarity",   # "mmr" etc. also allowed
        **_: Any,
    ):
        super().__init__()

        # ---------- build Supabase client ----------
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        sb: Client = create_client(url, key)

        # ---------- build VectorStore ----------
        store = SupabaseVectorStore(
            client=sb,
            embedding=OpenAIEmbeddings(),
            table_name=table_name,
        )
        self._retriever = store.as_retriever(
            search_type=search_type,
            search_kwargs={"k": top_k},
        )

    # -------- BaseRetriever API --------
    def get_relevant_documents(self, query: str) -> List[Document]:
        return self._retriever.get_relevant_documents(query)

    async def aget_relevant_documents(self, query: str) -> List[Document]:
        return await self._retriever.aget_relevant_documents(query)
