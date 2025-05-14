"""
backend/processors.py
Central registry (REG) of LangChain runnables used by graph.Process.

* docx_tpl_render   – fills {{brace}} DOCX templates via docxtpl
* policy_qna_chain  – stub HR Q&A (plain-text answer)
"""

from __future__ import annotations
from io import BytesIO
from uuid import uuid4
from typing import Dict

from docxtpl import DocxTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_openai import ChatOpenAI

from backend.db import sb   # existing Supabase client factory

# ───────────────────────────── Global registry ────────────────────────────
REG: Dict[str, Runnable] = {}

# -------------------------------------------------------------------------
# 1. Brace-style DOCX renderer (plain function)
# -------------------------------------------------------------------------
def render_docx_braces(template_id: str, context: dict) -> dict:
    """
    1. Download a {{token}} template from 'templates' bucket
    2. Render with docxtpl
    3. Upload to 'documents' bucket
    4. Return {'url': <signed link>} for download
    """
    client = sb()

    # 1) template bytes
    tpl_bytes = client.storage.from_("templates").download(template_id)

    # 2) merge
    tpl = DocxTemplate(BytesIO(tpl_bytes))
    tpl.render(context)               # {{token}} -> context["token"]
    buf = BytesIO()
    tpl.save(buf)

    # 3) upload result
    out_key = f"{template_id}/{uuid4()}.docx"
    client.storage.from_("documents").upload(out_key, buf.getvalue())

    # 4) signed link (7-day expiry)
    signed = client.storage.from_("documents").create_signed_url(
        path=out_key,
        expires_in=7 * 24 * 3600,
    )["signedURL"]
    return {"url": signed}

# Wrap the plain function in a Runnable so Process can call `.invoke()`
REG["docx_tpl_render"] = RunnableLambda(
    lambda d: render_docx_braces(
        template_id=d["metadata"]["template_id"],
        context={k: v for k, v in d.items() if k not in ("metadata", "user_input")},
    )
)

# -------------------------------------------------------------------------
# 2. Stub policy Q&A chain
# -------------------------------------------------------------------------
_policy_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an HR assistant. Respond briefly and note that the full "
        "policy search feature is not yet implemented."
    ),
    ("human", "{question}")
])

# map input dict -> {"question": user_input}
_input_map: Runnable = RunnableLambda(lambda d: {"question": d["user_input"]})

policy_qna_chain: Runnable = (
    _input_map
    | _policy_prompt
    | ChatOpenAI(model_name="gpt-3.5-turbo")
    | RunnableLambda(lambda m: m.content)     # strip metadata; return plain str
)

REG["policy_qna_chain"] = policy_qna_chain

# -------------------------------------------------------------------------
# 3. (Optional) import & register any existing chains, e.g. doc_draft_chain
# -------------------------------------------------------------------------
# from backend.other_module import doc_draft_chain
# REG["doc_draft_chain"] = doc_draft_chain
