"""
Processor-chain registry.

• Built-in single-step chains are hard-coded.
• Multi-step chains (type='chain') auto-load from the processor_chains table.
"""
from __future__ import annotations
import importlib, logging, os
from typing import Dict, Any, Mapping

from langchain_core.runnables import RunnableLambda
from langchain_openai          import ChatOpenAI
from langchain_core.prompts    import ChatPromptTemplate
from supabase                  import create_client

from backend.tools.docx_render     import DocxRender
from backend.tools.function_runner import run as function_runner
from backend.vector_search         import SupaRetriever
from backend.schema                import ChainDef
from backend.json_exec             import JSONGraphExecutor

log = logging.getLogger("processors")

# ─── Registry container ────────────────────────────────────────────────
REG: Dict[str, Any] = {}

# ─── Built-in chains ───────────────────────────────────────────────────
def _doc_draft_chain(payload: Dict[str, Any]) -> Dict[str, Any]:
    tpl_id = payload["metadata"]["template_id"]
    inputs = payload.get("inputs") or {}
    return DocxRender(tpl_id).invoke(inputs)

def _generic_chain(payload: Dict[str, Any]) -> Dict[str, Any]:
    func_path = payload["metadata"]["function_path"]      # e.g. backend.helpers.echo:repeat
    mod, _, attr = func_path.partition(":")
    fn = getattr(importlib.import_module(mod), attr)
    return fn(**(payload.get("inputs") or {}))

_llm   = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
_qna_p = ChatPromptTemplate.from_messages([
    ("system", "Answer **only** from the context.\n{context}"),
    ("user",   "{prompt}")
])
def _policy_qna(payload: Mapping[str, Any]) -> Dict[str, Any]:
    question = payload["prompt"]
    docs = SupaRetriever("vector_chunks", doc_id="handbook_2024", k=6)\
           .get_relevant_documents(question)
    context = "\n---\n".join(d.page_content for d in docs)
    answer  = _llm.invoke(_qna_p.format(prompt=question, context=context)).content
    return {"ui_event": "text", "content": answer}

REG.update({
    "doc_draft_chain":        RunnableLambda(_doc_draft_chain),
    "generic_function_chain": RunnableLambda(_generic_chain),
    "policy_qna_chain":       RunnableLambda(_policy_qna),
})

# ─── Auto-load DB chains ───────────────────────────────────────────────
_sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def _load_db_chains() -> Dict[str, Any]:
    rows = (
        _sb.table("processor_chains")
           .select("*")
           .eq("enabled", True)
           .eq("type",   "chain")
           .execute()
           .data
    )
    loaded: Dict[str, Any] = {}
    for row in rows:
        cid = row["chain_id"]
        try:
            spec  = ChainDef(**row["chain_json"])      # validate JSON
            exec_ = JSONGraphExecutor(spec)            # wrap executor
            loaded[cid] = RunnableLambda(exec_.run)
            log.debug("Loaded chain %s (%s steps)", cid, len(spec.steps))
        except Exception as exc:
            log.error("Skipping chain %s: %s", cid, exc)
    return loaded

def reload_registry() -> Dict[str, Any]:
    """Rebuild REG (built-ins plus any DB chains)."""
    global REG
    builtin = {
        k: v for k, v in REG.items()
        if k in ("doc_draft_chain", "generic_function_chain", "policy_qna_chain")
    }
    REG = {**builtin, **_load_db_chains()}
    return REG

# first load
reload_registry()
