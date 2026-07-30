import pytest

from src.core.config import get_settings


@pytest.mark.asyncio
async def test_ask_question_with_matching_document_returns_answered_with_citations(
    client, register_user
):
    headers, _ = await register_user("asker1")
    await client.post(
        "/api/v1/documents",
        headers=headers,
        files={
            "file": (
                "facts.txt",
                b"The mitochondria is the powerhouse of the cell.",
                "text/plain",
            )
        },
    )

    response = await client.post(
        "/api/v1/queries", headers=headers, json={"question": "What is the powerhouse of the cell?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    assert body["answer"]["status"] == "answered"
    assert len(body["answer"]["citations"]) > 0
    assert body["answer"]["metadata"]["total_tokens"] > 0


@pytest.mark.asyncio
async def test_ask_question_with_no_matching_content_returns_no_answer_found(client, register_user):
    headers, _ = await register_user("asker2")

    response = await client.post(
        "/api/v1/queries", headers=headers, json={"question": "What is the meaning of life?"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_answer_found"
    assert body["answer"]["status"] == "no_answer_found"
    assert body["answer"]["citations"] == []


@pytest.mark.asyncio
async def test_ask_empty_question_returns_422(client, register_user):
    headers, _ = await register_user("asker3")

    response = await client.post("/api/v1/queries", headers=headers, json={"question": ""})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ask_over_rate_limit_returns_429(client, register_user, monkeypatch):
    monkeypatch.setattr(get_settings(), "question_rate_limit_per_day", 2)
    headers, _ = await register_user("asker4")

    for _ in range(2):
        ok = await client.post("/api/v1/queries", headers=headers, json={"question": "anything?"})
        assert ok.status_code == 200

    over_limit = await client.post(
        "/api/v1/queries", headers=headers, json={"question": "anything?"}
    )
    assert over_limit.status_code == 429
    assert "detail" in over_limit.json()


@pytest.mark.asyncio
async def test_ask_without_auth_returns_401(client):
    response = await client.post("/api/v1/queries", json={"question": "anything?"})
    assert response.status_code == 401
