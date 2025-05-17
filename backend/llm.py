import os
import openai

from backend.prompts import get_prompt


def _substitute(template: str, variables: dict[str, str] | None) -> str:
    """
    Replace placeholders like {CONTEXT} with their values using str.format.
    Non‑string values are cast to str so you can pass numbers, etc.
    """
    if not variables:
        return template

    safe_vars = {k: str(v) for k, v in variables.items()}
    try:
        return template.format(**safe_vars)
    except KeyError as err:
        missing = err.args[0]
        raise ValueError(f"Prompt expects placeholder {{{missing}}} which "
                         "was not supplied in `variables`.") from None


def call_llm(
    prompt_name: str,
    variables: dict[str, str] | None = None,
    *,
    model: str = "gpt-4o",
    version: int | None = None,
    max_tokens: int = 512,
    temperature: float = 0.2,
) -> str:
    """
    Universal OpenAI chat‑completion helper.

    • Prompts are fetched from the DB via `get_prompt`.
    • Placeholders use *single braces* (e.g. {CONTEXT}).
    • Values are injected with Python’s `str.format(**variables)`.
    """
    prompt_text = get_prompt(prompt_name, version)
    prompt_text = _substitute(prompt_text, variables)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set.")

    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt_text}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content


# --------------------------------------------------------------------------- #
# Quick smoke test
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    ctx = "Paid time off (PTO) is 20 days per year for all employees."
    q   = "How much PTO do employees get per year?"
    print(call_llm("policy_qa", {"CONTEXT": ctx, "QUESTION": q}))
