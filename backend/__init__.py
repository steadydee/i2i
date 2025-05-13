# backend/__init__.py
"""
Package marker + explicit export of DocxRender so
`backend.tools.docx_render.DocxRender` can be imported elsewhere.
"""
from backend.tools.docx_render import DocxRender  # noqa: F401
from backend.tools.supabase_retriever import SupabaseRetriever  # noqa: F401
