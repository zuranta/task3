"""Correctness evaluator (FR-022): LLM-as-judge comparing the generated
answer against the dataset item's expected answer."""

from eval.evaluators._llm_judge import judge

_SYSTEM_PROMPT = (
    "You judge whether a candidate answer is factually correct given a reference "
    "answer to the same question. Minor wording differences are fine as long as the "
    "substance matches. Respond with exactly one word: 'yes' or 'no'."
)


def correctness_evaluator(run, example) -> dict:
    outputs = run.outputs or {}
    answer_text = outputs.get("answer_text") or ""

    if run.error or not answer_text:
        return {
            "key": "correctness",
            "score": 0.0,
            "comment": "No answer was produced for this question.",
        }

    question = example.inputs.get("question", "")
    expected_answer = example.outputs.get("expected_answer", "")

    verdict = judge(
        _SYSTEM_PROMPT,
        f"Question: {question}\nReference answer: {expected_answer}\n"
        f"Candidate answer: {answer_text}",
    )
    score = 1.0 if verdict.strip().lower().startswith("yes") else 0.0
    return {"key": "correctness", "score": score, "comment": verdict}
