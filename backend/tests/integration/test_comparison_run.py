"""End-to-end comparison run: a fixture dataset run through eval_service,
including one version failing to answer one question, and the resulting
ComparisonRun correctly persisted as `partial` (FR-024, FR-025, FR-026).

A live LangSmith comparison run isn't exercised here (no LangSmith
credentials in this environment, mirroring T062's live-Azure caveat) --
`run_experiment` is faked at the boundary `eval_service` calls it through,
so this test instead validates the persistence/orchestration layer end-to-end.
"""

import pytest

from src.models.db import ComparisonRunStatus, User, UserRole
from src.services import eval_service


@pytest.mark.asyncio
async def test_end_to_end_comparison_run_with_a_partial_failure(db_session, monkeypatch):
    def fake_run_experiment(*, version_a_label, version_b_label, eval_user_id="eval-harness"):
        return {
            "version_a_label": version_a_label,
            "version_b_label": version_b_label,
            "langsmith_experiment_id_a": "exp-a",
            "langsmith_experiment_id_b": "exp-b",
            "aggregate_score_a": {"correctness": 1.0, "relevance": 1.0, "groundedness": 1.0},
            "aggregate_score_b": {"correctness": 0.33, "relevance": 0.5, "groundedness": 0.5},
            "winner": "a",
            # version b failed to answer one of the fixture dataset's questions
            "had_failures": True,
        }

    monkeypatch.setattr(eval_service, "run_experiment", fake_run_experiment)

    admin = User(
        email="evaluator@example.com", username="evaluatorx", password_hash="x", role=UserRole.admin
    )
    db_session.add(admin)
    await db_session.flush()

    run = await eval_service.start_comparison_run(
        db_session, user_id=admin.id, version_a_label="baseline", version_b_label="candidate"
    )

    assert run.status == ComparisonRunStatus.partial
    assert run.winner.value == "a"
    assert run.aggregate_score_a["correctness"] == 1.0
    assert run.aggregate_score_b["correctness"] == 0.33
    assert run.created_by == admin.id
    assert run.completed_at is not None


@pytest.mark.asyncio
async def test_end_to_end_comparison_run_without_failures_is_completed(db_session, monkeypatch):
    def fake_run_experiment(*, version_a_label, version_b_label, eval_user_id="eval-harness"):
        return {
            "version_a_label": version_a_label,
            "version_b_label": version_b_label,
            "langsmith_experiment_id_a": "exp-a",
            "langsmith_experiment_id_b": "exp-b",
            "aggregate_score_a": {"correctness": 0.9, "relevance": 0.9, "groundedness": 0.9},
            "aggregate_score_b": {"correctness": 0.9, "relevance": 0.9, "groundedness": 0.9},
            "winner": "tie",
            "had_failures": False,
        }

    monkeypatch.setattr(eval_service, "run_experiment", fake_run_experiment)

    admin = User(
        email="evaluator2@example.com",
        username="evaluatory",
        password_hash="x",
        role=UserRole.admin,
    )
    db_session.add(admin)
    await db_session.flush()

    run = await eval_service.start_comparison_run(
        db_session, user_id=admin.id, version_a_label="baseline", version_b_label="candidate"
    )

    assert run.status == ComparisonRunStatus.completed
    assert run.winner.value == "tie"


@pytest.mark.asyncio
async def test_delete_comparison_runs_removes_them(db_session, monkeypatch):
    def fake_run_experiment(*, version_a_label, version_b_label, eval_user_id="eval-harness"):
        return {
            "version_a_label": version_a_label,
            "version_b_label": version_b_label,
            "langsmith_experiment_id_a": "exp-a",
            "langsmith_experiment_id_b": "exp-b",
            "aggregate_score_a": {"correctness": 1.0, "relevance": 1.0, "groundedness": 1.0},
            "aggregate_score_b": {"correctness": 1.0, "relevance": 1.0, "groundedness": 1.0},
            "winner": "tie",
            "had_failures": False,
        }

    monkeypatch.setattr(eval_service, "run_experiment", fake_run_experiment)

    admin = User(
        email="evaluator3@example.com",
        username="evaluatorz",
        password_hash="x",
        role=UserRole.admin,
    )
    db_session.add(admin)
    await db_session.flush()

    run_to_delete = await eval_service.start_comparison_run(
        db_session, user_id=admin.id, version_a_label="baseline", version_b_label="candidate"
    )
    run_to_keep = await eval_service.start_comparison_run(
        db_session, user_id=admin.id, version_a_label="baseline", version_b_label="candidate"
    )

    await eval_service.delete_comparison_runs(db_session, run_ids=[run_to_delete.id])

    remaining = await eval_service.list_comparison_runs(db_session)
    remaining_ids = {run.id for run in remaining}
    assert run_to_delete.id not in remaining_ids
    assert run_to_keep.id in remaining_ids
