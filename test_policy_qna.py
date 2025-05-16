from backend.helpers import policy_qna

if __name__ == "__main__":
    question = "How much paid time off do employees get?"
    result = policy_qna.run(question=question)
    print(result)
