"""GET /queries/{queryId}: exact replay of the original answer; 404 for
another user's query (FR-020)."""

import pytest


@pytest.mark.asyncio
async def test_get_query_replays_the_original_answer_exactly(client, register_user):
    headers, _ = await register_user("detail1")
    original = await client.post(
        "/api/v1/queries", headers=headers, json={"question": "What happened?"}
    )
    query_id = original.json()["id"]

    response = await client.get(f"/api/v1/queries/{query_id}", headers=headers)

    assert response.status_code == 200
    assert response.json() == original.json()


@pytest.mark.asyncio
async def test_get_query_for_another_users_query_returns_404(client, register_user):
    headers_a, _ = await register_user("detail2")
    headers_b, _ = await register_user("detail3")
    original = await client.post(
        "/api/v1/queries", headers=headers_a, json={"question": "A's private question?"}
    )
    query_id = original.json()["id"]

    response = await client.get(f"/api/v1/queries/{query_id}", headers=headers_b)

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_nonexistent_query_returns_404(client, register_user):
    headers, _ = await register_user("detail4")

    response = await client.get("/api/v1/queries/does-not-exist", headers=headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_query_without_auth_returns_401(client):
    response = await client.get("/api/v1/queries/some-id")
    assert response.status_code == 401
