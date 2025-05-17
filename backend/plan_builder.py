from __future__ import annotations
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import backend.processors as processors

_llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an AI workflow planner. "
        "Given a user goal and a palette of runnable types, produce a JSON list "
        "of steps. Each step: {{\"type\": <runnable_type>, \"label\": <human label>}} "
        "Respond ONLY with JSON."
    ),
    ("user", "Goal: {goal}\n\nAvailable runnables: {palette}")
])

def generate_plan(goal: str) -> List[Dict[str, str]]:
    palette = ", ".join(sorted(processors.REG.keys()))
    resp = _llm.invoke(_prompt.format(goal=goal, palette=palette))
    try:
        return eval(resp.content)   # ← quick-and-dirty JSON parse
    except Exception:
        return []
