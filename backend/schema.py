"""
backend.schema
==============
Pydantic models that define the **only valid shape** for:

• TaskManifest   – one row in task_manifest
• ProcessorChain – one row in processor_chains
• ChainDef / ChainStep – JSON spec for multi-step chains

Adding a new key?  Put a sensible **default** here first so legacy rows
keep validating.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, validator

# ────────────────────────── helper: form field ──────────────────────────
class RequiredField(BaseModel):
    name:   str
    label:  str
    widget: str = "text_input"
    options: Optional[List[str]] = None   # for selects, radios, etc.
    required: bool = True


# ────────────────────────────── 1. manifest ─────────────────────────────
class TaskManifest(BaseModel):
    # minimal routing info
    task:               str
    phrase_examples:    List[str]          = Field(default_factory=list)

    # execution info
    processor_chain_id: str
    type:  Literal["runnable", "json_graph"] = "runnable"

    # dynamic form
    required_fields: List[RequiredField]    = Field(default_factory=list)

    # misc
    enabled:   bool         = True
    metadata:  Dict[str, Any] = Field(default_factory=dict)
    tenant_id: str           = "default"

    # legacy alias → still accept "output_type" silently
    @validator("processor_chain_id", pre=True)
    def _legacy_chain_alias(cls, v, values):
        return v or values.get("output_type")  # old column name
        

# ─────────────────────────── 2. chain definition ────────────────────────
class ChainStep(BaseModel):
    id:          str
    class_path:  str                   # dotted path to Runnable class
    init_kwargs: Dict[str, Any] = Field(default_factory=dict)

    # accept legacy "params" alias
    @validator("init_kwargs", pre=True, always=True)
    def _alias_params(cls, v, values):
        if v == {} and "params" in values:
            return values["params"] or {}
        return v


class ChainDef(BaseModel):
    """
    JSON spec stored in processor_chains.chain_json  when type='json_graph'
    """
    type:  Literal["chain", "json_graph"] = "chain"
    entry: Optional[str] = None          # if None, use first step
    steps: List[ChainStep]

    # simple linear default if caller forgets entry
    @validator("entry", always=True)
    def _auto_entry(cls, v, values):
        if v is None:
            v = values["steps"][0].id
        return v

    @validator("steps")
    def _must_have_steps(cls, v):
        if not v:
            raise ValueError("chain must define at least one step")
        return v


# ─────────────────────────── 3. processor row ───────────────────────────
class ProcessorChain(BaseModel):
    chain_id: str
    version:  int = 1
    type:     Literal["runnable", "chain"] = "runnable"
    chain_json: Optional[Dict[str, Any]] = None
    enabled:  bool = True
    risk_level: Optional[str] = None
    metadata:  Dict[str, Any] = Field(default_factory=dict)

    # when type='chain', validate chain_json
    @validator("chain_json", always=True)
    def _validate_chain_json(cls, v, values):
        if values.get("type") == "chain":
            # raises if invalid
            ChainDef(**v)
        return v


# convenience export
__all__ = ["TaskManifest", "ProcessorChain", "ChainDef", "ChainStep", "RequiredField"]
