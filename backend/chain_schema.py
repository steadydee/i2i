"""
Pydantic models that define the only valid shape for a processor chain row.

• One ChainDef contains ≥1 ChainStep.
• Each ChainStep must have id, class_path, and (optional) init_kwargs.
• Legacy key alias "params" is accepted but normalised to init_kwargs.
"""

from __future__ import annotations
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Literal, Optional

class ChainStep(BaseModel):
    id:          str
    class_path:  str
    init_kwargs: Dict[str, object] = Field(default_factory=dict)

    # accept legacy "params" alias
    @validator("init_kwargs", pre=True, always=True)
    def _params_alias(cls, v, values):
        if v == {} and "params" in values:
            return values["params"] or {}
        return v

class ChainDef(BaseModel):
    type:  Literal["chain"]
    steps: List[ChainStep]

    @validator("steps")
    def _non_empty(cls, v):
        if not v:
            raise ValueError("chain must have at least one step")
        return v
