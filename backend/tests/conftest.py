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


class _FakeSecrets:
    # >= 32 bytes, matching the length the real Bicep-generated secret guarantees.
    jwt_signing_secret = "test-jwt-signing-secret-0123456789abcdef"
    langsmith_api_key = "test-langsmith-api-key"


@pytest.fixture(autouse=True)
def _fake_secrets(monkeypatch):
    """Never hit real Key Vault / Azure in tests."""
    monkeypatch.setattr(security_module, "get_secrets", lambda: _FakeSecrets())


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
