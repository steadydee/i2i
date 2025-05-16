from pprint import pprint
from backend.graph import run_workflow

def test_prompt(prompt):
    print(f"\n--- Testing prompt: '{prompt}' ---")
    event = run_workflow(prompt)
    print("Event returned:")
    pprint(event)

if __name__ == "__main__":
    # SOW task prompt
    test_prompt("I need a SOW for Acme")

    # Policy Q&A prompt
    test_prompt("is there a military leave policy?")
