import os

os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
os.environ.setdefault("AZURE_SEARCH_ENDPOINT", "https://test.search.windows.net")
os.environ.setdefault("KEY_VAULT_URI", "https://test.vault.azure.net/")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import src.core.security as security_module
from src.core.db import Base, _session_factory, engine
from src.main import app
from src.models.schemas import GeneratedAnswer, GeneratedCitation
from src.services import generation_service, retrieval_service
from src.services.generation_service import UsageInfo
from src.services.retrieval_service import Passage


class _FakeSecrets:
    # >= 32 bytes, matching the length the real Bicep-generated secret guarantees.
    jwt_signing_secret = "test-jwt-signing-secret-0123456789abcdef"  # gitleaks:allow
    langsmith_api_key = "test-langsmith-api-key"  # gitleaks:allow


@pytest.fixture(autouse=True)
def _fake_secrets(monkeypatch):
    """Never hit real Key Vault / Azure in tests."""
    monkeypatch.setattr(security_module, "get_secrets", lambda: _FakeSecrets())


class _FakeSearchIndex:
    """In-memory stand-in for Azure AI Search, keyed exactly like the real index
    (research.md §3): every passage carries document_id/user_id/status, and
    `search` applies the same user_id+status=active filter the real service
    injects server-side, so tests exercise the real isolation invariant.
    """

    def __init__(self) -> None:
        self.passages: dict[str, dict] = {}

    async def ensure_index_exists(self) -> None:
        return None

    async def index_passages(
        self, *, document_id, user_id, chunks, location_labels, embeddings
    ) -> None:
        for i, chunk in enumerate(chunks):
            pid = f"{document_id}_{i}"
            self.passages[pid] = {
                "id": pid,
                "document_id": document_id,
                "user_id": user_id,
                "status": "active",
                "location_label": location_labels[i],
                "content": chunk,
            }

    async def delete_document_passages(self, document_id) -> None:
        for pid in [p for p, v in self.passages.items() if v["document_id"] == document_id]:
            del self.passages[pid]

    async def search(self, *, user_id, question, question_vector) -> list[Passage]:
        question_words = {w.lower() for w in question.split() if len(w) > 3}
        matches = []
        for p in self.passages.values():
            if p["user_id"] != user_id or p["status"] != "active":
                continue
            content_words = {w.lower().strip(".,!?") for w in p["content"].split()}
            if question_words & content_words:
                matches.append(p)
        return [
            Passage(
                id=p["id"],
                document_id=p["document_id"],
                location_label=p["location_label"],
                content=p["content"],
            )
            for p in matches
        ]


@pytest.fixture(autouse=True)
def fake_search_index(monkeypatch):
    """Swaps retrieval_service's Azure calls for the in-memory fake above."""
    fake = _FakeSearchIndex()
    monkeypatch.setattr(retrieval_service, "ensure_index_exists", fake.ensure_index_exists)
    monkeypatch.setattr(retrieval_service, "index_passages", fake.index_passages)
    monkeypatch.setattr(
        retrieval_service, "delete_document_passages", fake.delete_document_passages
    )
    monkeypatch.setattr(retrieval_service, "search", fake.search)
    return fake


@pytest.fixture(autouse=True)
def _fake_embeddings(monkeypatch):
    """Never call Azure OpenAI embeddings in tests -- a fixed-size dummy vector."""

    async def fake_embed(texts):
        return [[0.1] * 8 for _ in texts]

    monkeypatch.setattr(generation_service, "embed", fake_embed)


@pytest.fixture(autouse=True)
def _fake_generation(monkeypatch):
    """Deterministic stand-in for the Azure OpenAI Structured Outputs call:
    answers (citing every retrieved passage) when passages were retrieved,
    otherwise an explicit no_answer_found -- mirrors the real prompt's
    grounding instruction without a live LLM call.
    """

    async def fake_generate_answer(*, question, passages):
        usage = UsageInfo(
            prompt_tokens=100,
            completion_tokens=20,
            total_tokens=120,
            context_window_utilization=120 / 128_000,
        )
        if passages:
            return (
                GeneratedAnswer(
                    status="answered",
                    answer_text=f"Based on {len(passages)} passage(s): {passages[0].content[:200]}",
                    citations=[
                        GeneratedCitation(passage_id=p.id, location_label=p.location_label)
                        for p in passages
                    ],
                ),
                usage,
            )
        return GeneratedAnswer(status="no_answer_found", answer_text=None, citations=[]), usage

    monkeypatch.setattr(generation_service, "generate_answer", fake_generate_answer)


@pytest_asyncio.fixture(autouse=True)
async def _reset_db():
    """Fresh schema for every test, on the shared in-memory SQLite engine."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    async with _session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def register_user(client):
    """Factory fixture: register a distinct user, return (auth_headers, user_id)."""
    from src.core.security import decode_access_token

    async def _register(username: str) -> tuple[dict[str, str], str]:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"{username}@example.com",
                "username": username,
                "password": "correcthorse",
            },
        )
        token = response.json()["access_token"]
        user_id = decode_access_token(token)["sub"]
        return {"Authorization": f"Bearer {token}"}, user_id

    return _register
