from __future__ import annotations
import re
from typing import List

def suggest_phrases(title: str, min_count: int = 3) -> List[str]:
    """
    Heuristic + GPT fallback:
    • returns ≥ min_count phrases
    • title e.g. 'Invoice Generator' → ['invoice generator', 'invoice', 'create invoice']
    """
    title = title.lower().strip()
    words = re.findall(r"\w+", title)
    if not words:
        return []

    phrases = {title}
    if len(words) == 1:
        root = words[0]
        phrases.update({f"create {root}", f"generate {root}"})
    else:
        phrases.add(" ".join(words[-2:]))          # last two
        phrases.add(f"{words[0]} {words[-1]}")     # first + last

    # if still short, ask GPT once
    if len(phrases) < min_count:
        try:
            import openai, json
            system = "Suggest 3–5 short user phrases that would ask for this workflow."
            user   = f"Title: {title}"
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                temperature=0,
                messages=[{"role":"system","content":system},
                          {"role":"user","content":user}],
            )
            extra = json.loads(resp.choices[0].message.content)
            phrases.update(extra)
        except Exception:
            pass

    return list(phrases)[: max(min_count, len(phrases))]
