from __future__ import annotations
from typing import Dict, List, Literal, Any
from pydantic import BaseModel, Field, validator

# ─────────── linear-chain schema (existing) ───────────
class ChainStep(BaseModel):
    id:          str
    class_path:  str
    init_kwargs: Dict[str, Any] = Field(default_factory=dict)

    @validator("init_kwargs", pre=True, always=True)
    def _alias_params(cls, v, values):
        if v == {} and "params" in values:
            return values["params"] or {}
        return v

class ChainDef(BaseModel):
    type:  Literal["chain"]
    steps: List[ChainStep]

    @validator("steps")
    def _non_empty(cls, v):
        if not v:
            raise ValueError("chain must define at least one step")
        return v

# ─────────── new json_graph schema ───────────
class GraphNode(BaseModel):
    type:   str
    params: Dict[str, Any] = Field(default_factory=dict)
    next:   List[str]      = Field(default_factory=list)
    end:    bool           = False

class GraphDef(BaseModel):
    type:       Literal["json_graph"]
    version:    str | int
    entry:      str
    risk_level: str
    cost_guard: Dict[str, Any]
    nodes:      Dict[str, GraphNode]
