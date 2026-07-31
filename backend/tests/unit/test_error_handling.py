"""T099 security hardening pass, made concrete as a test: an unexpected
exception anywhere in a request must never reach the client as anything but
the generic, curated Error shape -- no stack trace, no exception message,
no internal identifiers (FR-021)."""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.services import query_service

_SENSITIVE_DETAIL = (
    "Connection to db-prod-internal.internal:5432 failed for user 'app' "
    "password 'Sup3rSecret!' -- Traceback (most recent call last): ..."
)


@pytest.mark.asyncio
async def test_an_unexpected_exception_never_leaks_its_message_to_the_client(
    client, register_user, monkeypatch
):
    async def _raise(*args, **kwargs):
        raise RuntimeError(_SENSITIVE_DETAIL)

    monkeypatch.setattr(query_service, "ask_question", _raise)
    headers, _ = await register_user("leaktest1")

    # Starlette's ServerErrorMiddleware sends the real response but then
    # deliberately re-raises the exception too (so servers can log it) --
    # httpx's ASGITransport re-raises that by default, which would hide the
    # actual response from this test. Disabling it gets the real response.
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as no_raise_client:
        response = await no_raise_client.post(
            "/api/v1/queries", headers=headers, json={"question": "does this leak?"}
        )

    assert response.status_code == 500
    body = response.text
    assert "db-prod-internal" not in body
    assert "Sup3rSecret" not in body
    assert "Traceback" not in body
    assert response.json()["detail"] == "An unexpected error occurred. Please try again."


@pytest.mark.asyncio
async def test_malformed_request_body_returns_a_generic_validation_error(client, register_user):
    headers, _ = await register_user("leaktest2")

    response = await client.post("/api/v1/queries", headers=headers, json={"not_a_question": 1})

    assert response.status_code == 422
    assert response.json()["detail"] == "The request was malformed or missing required fields."
