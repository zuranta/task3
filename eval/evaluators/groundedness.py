"""Groundedness evaluator (FR-022): a citation-coverage check (an answer with
zero citations is never grounded), with an LLM-as-judge fallback verifying
paraphrased claims are actually supported by the cited passages."""

from eval.evaluators._llm_judge import judge

_SYSTEM_PROMPT = (
    "You judge whether every factual claim in a candidate answer is supported by "
    "the provided citations/context, allowing for paraphrasing. Respond with "
    "exactly one word: 'yes' or 'no'."
)


def groundedness_evaluator(run, example) -> dict:
    outputs = run.outputs or {}
    answer_text = outputs.get("answer_text") or ""
    citations = outputs.get("citations") or []

    if run.error:
        return {
            "key": "groundedness",
            "score": 0.0,
            "comment": "No answer was produced for this question.",
        }

    if not answer_text:
        # An explicit no_answer_found claims nothing, so it's trivially grounded.
        return {"key": "groundedness", "score": 1.0, "comment": "No answer claimed."}

    if not citations:
        return {
            "key": "groundedness",
            "score": 0.0,
            "comment": "Answered with zero supporting citations.",
        }

    context = "\n".join(c.get("content", "") for c in citations)
    verdict = judge(
        _SYSTEM_PROMPT, f"Citations/context:\n{context}\n\nCandidate answer: {answer_text}"
    )
    score = 1.0 if verdict.strip().lower().startswith("yes") else 0.0
    return {"key": "groundedness", "score": score, "comment": verdict}
