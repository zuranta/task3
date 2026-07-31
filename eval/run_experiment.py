"""Runs two named system versions through LangSmith's evaluate() against the
benchmark dataset, producing per-question and aggregate correctness/
relevance/groundedness scores and a declared winner (FR-024, FR-025). A
dataset question a version fails to answer is recorded as a failure for that
version (LangSmith's `run.error`), never silently omitted (FR-026).
"""

import argparse

from langsmith.evaluation import evaluate

from eval.dataset_sync import _DATASET_NAME, ensure_dataset
from eval.evaluators.correctness import correctness_evaluator
from eval.evaluators.groundedness import groundedness_evaluator
from eval.evaluators.relevance import relevance_evaluator
from eval.targets import make_target

_EVALUATORS = [correctness_evaluator, relevance_evaluator, groundedness_evaluator]


def _summarize(results) -> tuple[dict, bool]:
    """Averages each evaluator's score across all examples; also reports
    whether any example's target run errored (a recorded failure, FR-026)."""
    totals: dict[str, list[float]] = {}
    had_failures = False
    for row in results:
        if row["run"].error:
            had_failures = True
        for evaluation in row["evaluation_results"].get("results", []):
            totals.setdefault(evaluation.key, []).append(evaluation.score or 0.0)
    aggregate = {key: sum(scores) / len(scores) for key, scores in totals.items() if scores}
    return aggregate, had_failures


def _pick_winner(aggregate_a: dict, aggregate_b: dict) -> str:
    score_a = sum(aggregate_a.values())
    score_b = sum(aggregate_b.values())
    if score_a > score_b:
        return "a"
    if score_b > score_a:
        return "b"
    return "tie"


def run_experiment(
    *, version_a_label: str, version_b_label: str, eval_user_id: str = "eval-harness"
) -> dict:
    ensure_dataset()

    results_a = evaluate(
        make_target(version_a_label, eval_user_id),
        data=_DATASET_NAME,
        evaluators=_EVALUATORS,
        experiment_prefix=f"version-{version_a_label}",
    )
    aggregate_a, failures_a = _summarize(results_a)

    results_b = evaluate(
        make_target(version_b_label, eval_user_id),
        data=_DATASET_NAME,
        evaluators=_EVALUATORS,
        experiment_prefix=f"version-{version_b_label}",
    )
    aggregate_b, failures_b = _summarize(results_b)

    return {
        "version_a_label": version_a_label,
        "version_b_label": version_b_label,
        "langsmith_experiment_id_a": results_a.experiment_name,
        "langsmith_experiment_id_b": results_b.experiment_name,
        "aggregate_score_a": aggregate_a,
        "aggregate_score_b": aggregate_b,
        "winner": _pick_winner(aggregate_a, aggregate_b),
        "had_failures": failures_a or failures_b,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare two named system versions.")
    parser.add_argument("--version-a", required=True, dest="version_a")
    parser.add_argument("--version-b", required=True, dest="version_b")
    args = parser.parse_args()

    result = run_experiment(version_a_label=args.version_a, version_b_label=args.version_b)
    print(result)
