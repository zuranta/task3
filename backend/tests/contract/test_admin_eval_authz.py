"""Every /admin/eval/* route rejects non-admin callers with 403 (FR-007)."""

import pytest


@pytest.mark.asyncio
async def test_non_admin_cannot_add_dataset_item(client, register_user):
    headers, _ = await register_user("regular1")

    response = await client.post(
        "/api/v1/admin/eval/dataset-items",
        headers=headers,
        json={"question": "q?", "expected_answer": "a"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_non_admin_cannot_list_dataset_items(client, register_user):
    headers, _ = await register_user("regular2")

    response = await client.get("/api/v1/admin/eval/dataset-items", headers=headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_non_admin_cannot_start_comparison_run(client, register_user):
    headers, _ = await register_user("regular3")

    response = await client.post(
        "/api/v1/admin/eval/comparison-runs",
        headers=headers,
        json={"version_a_label": "a", "version_b_label": "b"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_non_admin_cannot_list_comparison_runs(client, register_user):
    headers, _ = await register_user("regular4")

    response = await client.get("/api/v1/admin/eval/comparison-runs", headers=headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_non_admin_cannot_get_a_comparison_run(client, register_user):
    headers, _ = await register_user("regular5")

    response = await client.get("/api/v1/admin/eval/comparison-runs/some-id", headers=headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_caller_cannot_access_admin_eval_routes(client):
    response = await client.get("/api/v1/admin/eval/dataset-items")
    assert response.status_code == 401
