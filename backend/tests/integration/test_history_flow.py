"""Ask a question -> it appears in GET /queries -> GET /queries/{id} returns
the identical structured answer and citations (FR-019, FR-020)."""

import pytest


@pytest.mark.asyncio
async def test_ask_then_appears_in_history_and_replays_identically(client, register_user):
    headers, _ = await register_user("historyflow1")

    await client.post(
        "/api/v1/documents",
        headers=headers,
        files={
            "file": (
                "facts.txt",
                b"The Wanderer-3 robot has a nine hour battery life.",
                "text/plain",
            )
        },
    )
    ask_response = await client.post(
        "/api/v1/queries",
        headers=headers,
        json={"question": "What is the battery life of the Wanderer-3?"},
    )
    assert ask_response.status_code == 200
    original = ask_response.json()
    assert original["status"] == "answered"
    assert len(original["answer"]["citations"]) > 0

    history_response = await client.get("/api/v1/queries", headers=headers)
    assert history_response.status_code == 200
    history_ids = [q["id"] for q in history_response.json()]
    assert original["id"] in history_ids

    detail_response = await client.get(f"/api/v1/queries/{original['id']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json() == original
