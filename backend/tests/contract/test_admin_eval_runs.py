"""POST /admin/eval/comparison-runs and GET .../{id} (FR-024, FR-025, FR-026)."""

import pytest

from src.services import eval_service


def _fake_run_experiment(had_failures: bool):
    def _run(*, version_a_label, version_b_label, eval_user_id="eval-harness"):
        return {
            "version_a_label": version_a_label,
            "version_b_label": version_b_label,
            "langsmith_experiment_id_a": "exp-a-123",
            "langsmith_experiment_id_b": "exp-b-456",
            "aggregate_score_a": {"correctness": 0.9, "relevance": 0.8, "groundedness": 1.0},
            "aggregate_score_b": {"correctness": 0.5, "relevance": 0.6, "groundedness": 0.7},
            "winner": "a",
            "had_failures": had_failures,
        }

    return _run


@pytest.mark.asyncio
async def test_admin_can_start_and_view_a_comparison_run(client, register_admin, monkeypatch):
    monkeypatch.setattr(eval_service, "run_experiment", _fake_run_experiment(False))
    headers, _ = await register_admin("evaladmin3")

    start_response = await client.post(
        "/api/v1/admin/eval/comparison-runs",
        headers=headers,
        json={"version_a_label": "prompt-v1", "version_b_label": "prompt-v2"},
    )
    assert start_response.status_code == 202
    body = start_response.json()
    assert body["status"] == "completed"
    assert body["winner"] == "a"
    assert body["aggregate_score_a"]["correctness"] == 0.9

    get_response = await client.get(
        f"/api/v1/admin/eval/comparison-runs/{body['id']}", headers=headers
    )
    assert get_response.status_code == 200
    assert get_response.json() == body


@pytest.mark.asyncio
async def test_comparison_run_is_partial_when_a_version_has_failures(
    client, register_admin, monkeypatch
):
    monkeypatch.setattr(eval_service, "run_experiment", _fake_run_experiment(True))
    headers, _ = await register_admin("evaladmin4")

    response = await client.post(
        "/api/v1/admin/eval/comparison-runs",
        headers=headers,
        json={"version_a_label": "v1", "version_b_label": "v2"},
    )

    assert response.status_code == 202
    assert response.json()["status"] == "partial"


@pytest.mark.asyncio
async def test_get_nonexistent_comparison_run_returns_404(client, register_admin):
    headers, _ = await register_admin("evaladmin5")

    response = await client.get(
        "/api/v1/admin/eval/comparison-runs/does-not-exist", headers=headers
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_comparison_runs(client, register_admin, monkeypatch):
    monkeypatch.setattr(eval_service, "run_experiment", _fake_run_experiment(False))
    headers, _ = await register_admin("evaladmin6")

    await client.post(
        "/api/v1/admin/eval/comparison-runs",
        headers=headers,
        json={"version_a_label": "v1", "version_b_label": "v2"},
    )

    response = await client.get("/api/v1/admin/eval/comparison-runs", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
