"""GET /queries: caller's own history, most-recent-first, empty array (not an
error) for a new account (FR-019)."""

import pytest


@pytest.mark.asyncio
async def test_list_queries_is_empty_array_for_a_new_account(client, register_user):
    headers, _ = await register_user("historian1")

    response = await client.get("/api/v1/queries", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_queries_returns_most_recent_first(client, register_user):
    headers, _ = await register_user("historian2")

    first = await client.post("/api/v1/queries", headers=headers, json={"question": "first?"})
    second = await client.post("/api/v1/queries", headers=headers, json={"question": "second?"})
    third = await client.post("/api/v1/queries", headers=headers, json={"question": "third?"})

    response = await client.get("/api/v1/queries", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert [q["id"] for q in body] == [
        third.json()["id"],
        second.json()["id"],
        first.json()["id"],
    ]


@pytest.mark.asyncio
async def test_list_queries_only_returns_the_calling_users_own_queries(client, register_user):
    headers_a, _ = await register_user("historian3")
    headers_b, _ = await register_user("historian4")

    await client.post("/api/v1/queries", headers=headers_a, json={"question": "A's question?"})

    response_b = await client.get("/api/v1/queries", headers=headers_b)

    assert response_b.status_code == 200
    assert response_b.json() == []


@pytest.mark.asyncio
async def test_list_queries_without_auth_returns_401(client):
    response = await client.get("/api/v1/queries")
    assert response.status_code == 401
