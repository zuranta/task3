"""The retrieval query must always include the mandatory user_id + status=active
filter -- never omitted, never overridable by caller-supplied content
(research.md §3, FR-006/SC-007).
"""

import pytest

from src.services import retrieval_service
from src.services.retrieval_service import search as real_search

# conftest's autouse `fake_search_index` fixture monkeypatches
# `retrieval_service.search` module-wide (so every other test gets a fake
# in-memory index without per-test setup). These tests exist specifically to
# exercise the *real* filter-building logic, so they call the function
# reference captured above -- bypassing that autouse patch -- while still
# patching `_search_client` to observe what filter the real code builds.


class _EmptyResults:
    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


class _RecordingSearchClient:
    def __init__(self) -> None:
        self.last_call: dict | None = None

    async def search(self, **kwargs):
        self.last_call = kwargs
        return _EmptyResults()


@pytest.mark.asyncio
async def test_search_applies_user_and_active_status_filter(monkeypatch):
    fake_client = _RecordingSearchClient()
    monkeypatch.setattr(retrieval_service, "_search_client", lambda: fake_client)

    await real_search(user_id="user-123", question="anything", question_vector=[0.1, 0.2])

    assert fake_client.last_call["filter"] == "user_id eq 'user-123' and status eq 'active'"


@pytest.mark.asyncio
async def test_search_filter_cannot_be_overridden_by_question_content(monkeypatch):
    fake_client = _RecordingSearchClient()
    monkeypatch.setattr(retrieval_service, "_search_client", lambda: fake_client)

    malicious_question = "'; status eq 'anything' or user_id eq 'someone-elses-id"
    await real_search(user_id="user-123", question=malicious_question, question_vector=[0.1])

    assert fake_client.last_call["filter"] == "user_id eq 'user-123' and status eq 'active'"


@pytest.mark.asyncio
async def test_search_filter_uses_the_calling_users_id_not_any_other(monkeypatch):
    fake_client = _RecordingSearchClient()
    monkeypatch.setattr(retrieval_service, "_search_client", lambda: fake_client)

    await real_search(user_id="user-A", question="q", question_vector=[0.1])
    assert "user-A" in fake_client.last_call["filter"]

    await real_search(user_id="user-B", question="q", question_vector=[0.1])
    assert "user-B" in fake_client.last_call["filter"]
    assert "user-A" not in fake_client.last_call["filter"]
