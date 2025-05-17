from __future__ import annotations
import logging, os
from typing import Dict, Any

from pydantic import ValidationError
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from supabase import create_client

from backend.schema        import ChainDef, GraphDef
from backend.json_executor import JSONGraphExecutor
from backend.tools.docx_render      import DocxRender
from backend.tools.function_runner  import run as function_runner
from backend.vector_search          import SupaRetriever

log = logging.getLogger(__name__)

REG: Dict[str, Any] = {}

# ────────────────────────── built-in chains ────────────────────────────
def _doc_chain(payload: Dict[str, Any]) -> Dict[str, Any]:
    tpl_id = payload["metadata"]["template_id"]
    return DocxRender(tpl_id).invoke(payload.get("inputs") or {})
REG["doc_draft_chain"] = RunnableLambda(_doc_chain)

def _generic_chain(payload: Dict[str, Any]) -> Dict[str, Any]:
    fp = payload["metadata"]["function_path"]
    return function_runner(fp, **(payload.get("inputs") or {}))
REG["generic_function_chain"] = RunnableLambda(_generic_chain)

_LLM = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
def _policy_qna(payload: Dict[str, Any]) -> Dict[str, Any]:
    q = payload.get("prompt") or "(no question)"
    retr = SupaRetriever("vector_chunks", doc_id="handbook_2024", k=6)
    ctx  = "\n\n".join(d.page_content for d in retr.get_relevant_documents(q))
    ans  = _LLM.invoke(f"Answer strictly from context.\n\nQuestion: {q}\n\nContext:\n{ctx}").content
    return {"ui_event":"text","content":ans}
REG["policy_qna_chain"] = RunnableLambda(_policy_qna)

# ───────────────────── dynamic loader from Supabase ─────────────────────
def _load_external_chains() -> None:
    url = os.getenv("SUPABASE_URL"); key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        log.warning("SUPABASE creds not set; external chains skipped")
        return
    sb   = create_client(url, key)
    rows = (sb.table("processor_chains")
              .select("*")
              .eq("enabled", True)
              .eq("type", "chain")
              .execute()
              .data or [])
    for row in rows:
        cid, cj = row["chain_id"], row["chain_json"]
        if cid in REG:
            continue
        try:
            if cj.get("type") == "json_graph":
                spec = GraphDef(**cj)
                REG[cid] = JSONGraphExecutor(spec)
            else:
                spec = ChainDef(**cj)
                REG[cid] = RunnableLambda(
                    lambda payload, s=spec: function_runner(
                        s.steps[0].class_path, **(payload.get("inputs") or {}))
                )
            log.info("Loaded chain %s", cid)
        except ValidationError as e:
            log.error("Skipping chain %s: %s", cid, e)

_load_external_chains()

# ───────────────────── back-compat shim (legacy callers) ─────────────────
from backend.graph import reload_graph as _reload_graph
def reload_registry() -> None:        # legacy alias
    _reload_graph()
