"""Relevance evaluator (FR-022): LLM-as-judge checking whether the generated
answer actually addresses the original question (independent of whether it
happens to be correct)."""

from eval.evaluators._llm_judge import judge

_SYSTEM_PROMPT = (
    "You judge whether a candidate answer is relevant to the question it claims to "
    "answer -- i.e. it addresses what was actually asked, regardless of whether it "
    "is factually correct. Respond with exactly one word: 'yes' or 'no'."
)


def relevance_evaluator(run, example) -> dict:
    outputs = run.outputs or {}
    answer_text = outputs.get("answer_text") or ""

    if run.error or not answer_text:
        return {
            "key": "relevance",
            "score": 0.0,
            "comment": "No answer was produced for this question.",
        }

    question = example.inputs.get("question", "")

    verdict = judge(_SYSTEM_PROMPT, f"Question: {question}\nCandidate answer: {answer_text}")
    score = 1.0 if verdict.strip().lower().startswith("yes") else 0.0
    return {"key": "relevance", "score": score, "comment": verdict}
