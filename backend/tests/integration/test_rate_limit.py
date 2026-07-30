"""Per-user upload and question rate limits (FR-012): 429 with limit/reset info."""

import re

import pytest

from src.core.config import get_settings


@pytest.mark.asyncio
async def test_upload_rate_limit_error_includes_limit_and_reset_time(
    client, register_user, monkeypatch
):
    monkeypatch.setattr(get_settings(), "upload_rate_limit_per_day", 1)
    headers, _ = await register_user("ratelimit1")

    await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("a.txt", b"first upload content", "text/plain")},
    )
    response = await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("b.txt", b"second upload content", "text/plain")},
    )

    assert response.status_code == 429
    detail = response.json()["detail"]
    assert "1" in detail
    assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", detail)


@pytest.mark.asyncio
async def test_question_rate_limit_error_includes_limit_and_reset_time(
    client, register_user, monkeypatch
):
    monkeypatch.setattr(get_settings(), "question_rate_limit_per_day", 1)
    headers, _ = await register_user("ratelimit2")

    await client.post("/api/v1/queries", headers=headers, json={"question": "first?"})
    response = await client.post("/api/v1/queries", headers=headers, json={"question": "second?"})

    assert response.status_code == 429
    detail = response.json()["detail"]
    assert "1" in detail
    assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", detail)


@pytest.mark.asyncio
async def test_upload_and_question_rate_limits_are_independent_per_user(
    client, register_user, monkeypatch
):
    monkeypatch.setattr(get_settings(), "upload_rate_limit_per_day", 1)
    headers, _ = await register_user("ratelimit3")

    await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("a.txt", b"content", "text/plain")},
    )
    over_upload_limit = await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("b.txt", b"content", "text/plain")},
    )
    assert over_upload_limit.status_code == 429

    # Question rate limit is a separate counter -- still allowed.
    question_response = await client.post(
        "/api/v1/queries", headers=headers, json={"question": "still allowed?"}
    )
    assert question_response.status_code == 200
