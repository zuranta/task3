"""POST /queries retrieval/generation failure -> 502, non-leaking message
(FR-021, /speckit-analyze finding E1).
"""

import pytest

from src.core.errors import UpstreamServiceError
from src.services import generation_service, retrieval_service


@pytest.mark.asyncio
async def test_ask_question_returns_502_when_retrieval_fails(client, register_user, monkeypatch):
    headers, _ = await register_user("failer1")

    async def broken_search(**kwargs):
        raise UpstreamServiceError("The document search could not be completed right now.")

    monkeypatch.setattr(retrieval_service, "search", broken_search)

    response = await client.post("/api/v1/queries", headers=headers, json={"question": "anything?"})

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "traceback" not in detail.lower()
    assert "exception" not in detail.lower()


@pytest.mark.asyncio
async def test_ask_question_returns_502_when_generation_fails(client, register_user, monkeypatch):
    headers, _ = await register_user("failer2")

    async def broken_generate(**kwargs):
        raise UpstreamServiceError("The answer generation service could not be reached right now.")

    monkeypatch.setattr(generation_service, "generate_answer", broken_generate)

    response = await client.post("/api/v1/queries", headers=headers, json={"question": "anything?"})

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "traceback" not in detail.lower()
    assert "exception" not in detail.lower()
