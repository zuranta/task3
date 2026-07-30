"""Unit tests for the correctness/relevance/groundedness evaluator functions
(FR-022). The LLM-as-judge call is mocked so the scoring/parsing logic is
tested without a live Azure OpenAI call -- run with the backend's venv:
`cd backend && .venv/Scripts/python.exe -m pytest ../eval/tests` (from repo
root so the `eval` package resolves; see quickstart.md).
"""

from types import SimpleNamespace

from eval.evaluators import correctness, groundedness, relevance


def _run(outputs: dict | None, error: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(outputs=outputs, error=error)


def _example(question: str, expected_answer: str) -> SimpleNamespace:
    return SimpleNamespace(
        inputs={"question": question}, outputs={"expected_answer": expected_answer}
    )


def test_correctness_scores_1_when_judge_says_yes(monkeypatch):
    monkeypatch.setattr(correctness, "judge", lambda system, user: "Yes, this matches.")

    result = correctness.correctness_evaluator(
        _run({"answer_text": "Paris"}), _example("Capital of France?", "Paris")
    )

    assert result == {"key": "correctness", "score": 1.0, "comment": "Yes, this matches."}


def test_correctness_scores_0_when_judge_says_no(monkeypatch):
    monkeypatch.setattr(correctness, "judge", lambda system, user: "No, incorrect.")

    result = correctness.correctness_evaluator(
        _run({"answer_text": "Berlin"}), _example("Capital of France?", "Paris")
    )

    assert result["score"] == 0.0


def test_correctness_scores_0_when_the_run_failed_to_answer():
    result = correctness.correctness_evaluator(
        _run(None, error="upstream failure"), _example("q?", "a")
    )

    assert result["score"] == 0.0


def test_relevance_scores_1_when_judge_says_yes(monkeypatch):
    monkeypatch.setattr(relevance, "judge", lambda system, user: "yes")

    result = relevance.relevance_evaluator(
        _run({"answer_text": "Paris is the capital of France."}),
        _example("Capital of France?", "Paris"),
    )

    assert result["score"] == 1.0


def test_relevance_scores_0_when_the_run_failed_to_answer():
    result = relevance.relevance_evaluator(_run(None, error="boom"), _example("q?", "a"))

    assert result["score"] == 0.0


def test_groundedness_scores_1_for_an_explicit_no_answer_found():
    result = groundedness.groundedness_evaluator(
        _run({"answer_text": None, "citations": []}), _example("q?", "a")
    )

    assert result["score"] == 1.0
    assert "no answer" in result["comment"].lower()


def test_groundedness_scores_0_for_an_answer_with_zero_citations():
    result = groundedness.groundedness_evaluator(
        _run({"answer_text": "Some answer", "citations": []}), _example("q?", "a")
    )

    assert result["score"] == 0.0


def test_groundedness_uses_the_judge_when_citations_are_present(monkeypatch):
    monkeypatch.setattr(groundedness, "judge", lambda system, user: "yes")

    result = groundedness.groundedness_evaluator(
        _run({"answer_text": "Some answer", "citations": [{"content": "supporting text"}]}),
        _example("q?", "a"),
    )

    assert result["score"] == 1.0
