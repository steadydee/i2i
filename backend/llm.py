import os
import openai
from backend.prompts import get_prompt

def call_llm(prompt_name, variables=None, model="gpt-4o", version=None, max_tokens=512, temperature=0.2):
    """
    Universal LLM call helper, updated for openai>=1.0.0
    """
    prompt_text = get_prompt(prompt_name, version)
    if variables:
        for k, v in variables.items():
            prompt_text = prompt_text.replace(f"{{{{ {k} }}}}", v)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt_text}],
        max_tokens=max_tokens,
        temperature=temperature
    )
    return response.choices[0].message.content

# Test Harness
if __name__ == "__main__":
    context = "Paid time off (PTO) is 20 days per year for all employees."
    question = "How much PTO do employees get per year?"
    print(call_llm("policy_qa", {"CONTEXT": context, "QUESTION": question}))
