"""The retrieval query must always include the mandatory user_id + status=active
filter -- never omitted, never overridable by caller-supplied content
(research.md §3, FR-006/SC-007).
"""

import pytest

from src.services import retrieval_service
from src.services.retrieval_service import list_passages as real_list_passages
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


class _FakeResults:
    def __init__(self, docs: list[dict]) -> None:
        self._docs = docs

    async def _make_iter(self):
        for doc in self._docs:
            yield doc

    def __aiter__(self):
        return self._make_iter()


class _DocsReturningSearchClient:
    def __init__(self, docs: list[dict]) -> None:
        self.last_call: dict | None = None
        self._docs = docs

    async def search(self, **kwargs):
        self.last_call = kwargs
        return _FakeResults(self._docs)


@pytest.mark.asyncio
async def test_list_passages_applies_document_and_user_and_active_status_filter(monkeypatch):
    fake_client = _DocsReturningSearchClient([])
    monkeypatch.setattr(retrieval_service, "_search_client", lambda: fake_client)

    await real_list_passages(user_id="user-123", document_id="doc-1")

    assert (
        fake_client.last_call["filter"]
        == "document_id eq 'doc-1' and user_id eq 'user-123' and status eq 'active'"
    )


@pytest.mark.asyncio
async def test_list_passages_does_not_rely_on_a_server_side_orderby(monkeypatch):
    # Regression guard: chunk_index isn't marked `sortable` in the index
    # schema, and Azure AI Search can't add that to an already-provisioned
    # index without a rebuild -- a server-side $orderby 400s for every
    # existing deployment. Sorting must happen client-side instead.
    fake_client = _DocsReturningSearchClient([])
    monkeypatch.setattr(retrieval_service, "_search_client", lambda: fake_client)

    await real_list_passages(user_id="user-123", document_id="doc-1")

    assert "order_by" not in fake_client.last_call


@pytest.mark.asyncio
async def test_list_passages_sorts_by_chunk_index_regardless_of_search_result_order(monkeypatch):
    docs = [
        {
            "id": "doc-1_2",
            "document_id": "doc-1",
            "location_label": "Section 3 of 3",
            "content": "third chunk",
            "chunk_index": 2,
        },
        {
            "id": "doc-1_0",
            "document_id": "doc-1",
            "location_label": "Section 1 of 3",
            "content": "first chunk",
            "chunk_index": 0,
        },
        {
            "id": "doc-1_1",
            "document_id": "doc-1",
            "location_label": "Section 2 of 3",
            "content": "second chunk",
            "chunk_index": 1,
        },
    ]
    fake_client = _DocsReturningSearchClient(docs)
    monkeypatch.setattr(retrieval_service, "_search_client", lambda: fake_client)

    passages = await real_list_passages(user_id="user-123", document_id="doc-1")

    assert [p.content for p in passages] == ["first chunk", "second chunk", "third chunk"]
