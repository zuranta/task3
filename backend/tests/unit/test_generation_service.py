"""generation_service.py has no dedicated coverage anywhere else -- the
conftest autouse fixtures replace embed()/generate_answer() wholesale for
every other test, so its own error handling, usage computation, and
telemetry wiring were never actually exercised (T096 coverage gap)."""

from types import SimpleNamespace

import openai
import pytest

from src.core import telemetry as telemetry_module
from src.core.errors import UpstreamServiceError
from src.models.schemas import GeneratedAnswer
from src.services import generation_service
from src.services.retrieval_service import Passage

# Captured at collection time, before any test/fixture runs -- conftest's
# autouse fixtures (_fake_embeddings/_fake_generation) monkeypatch these same
# module attributes to fixed stand-ins for every other test in the suite, so
# each test below restores the real implementation for its own duration.
_real_embed = generation_service.embed
_real_generate_answer = generation_service.generate_answer


def _passage(pid="p1") -> Passage:
    return Passage(id=pid, document_id="doc-1", location_label="Section 1 of 1", content="text")


class _FakeEmbeddings:
    def __init__(self, vectors=None, error=None):
        self._vectors = vectors
        self._error = error

    async def create(self, *, model, input):
        if self._error:
            raise self._error
        return SimpleNamespace(data=[SimpleNamespace(embedding=v) for v in self._vectors])


class _FakeCompletions:
    def __init__(self, completion=None, error=None):
        self._completion = completion
        self._error = error

    async def parse(self, *, model, messages, response_format):
        if self._error:
            raise self._error
        return self._completion


def _fake_client(embeddings=None, completion=None, completion_error=None, embed_error=None):
    return SimpleNamespace(
        embeddings=_FakeEmbeddings(vectors=embeddings, error=embed_error),
        beta=SimpleNamespace(
            chat=SimpleNamespace(completions=_FakeCompletions(completion, completion_error))
        ),
    )


def _fake_completion(parsed, prompt_tokens=100, completion_tokens=20, total_tokens=120):
    usage = (
        SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        if total_tokens is not None
        else None
    )
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(parsed=parsed))], usage=usage
    )


@pytest.mark.asyncio
async def test_embed_returns_empty_list_without_calling_the_client(monkeypatch):
    monkeypatch.setattr(generation_service, "embed", _real_embed)
    monkeypatch.setattr(
        generation_service, "_client", lambda: (_ for _ in ()).throw(AssertionError)
    )

    assert await generation_service.embed([]) == []


@pytest.mark.asyncio
async def test_embed_returns_the_vectors_from_the_client(monkeypatch):
    monkeypatch.setattr(generation_service, "embed", _real_embed)
    monkeypatch.setattr(
        generation_service, "_client", lambda: _fake_client(embeddings=[[0.1, 0.2]])
    )

    result = await generation_service.embed(["hello"])

    assert result == [[0.1, 0.2]]


@pytest.mark.asyncio
async def test_embed_wraps_openai_errors_without_leaking_the_original_message(monkeypatch):
    monkeypatch.setattr(generation_service, "embed", _real_embed)
    monkeypatch.setattr(
        generation_service,
        "_client",
        lambda: _fake_client(
            embed_error=openai.OpenAIError("api key rotated, endpoint xyz.internal down")
        ),
    )

    with pytest.raises(UpstreamServiceError) as exc_info:
        await generation_service.embed(["hello"])

    assert "xyz.internal" not in exc_info.value.detail
    assert "api key" not in exc_info.value.detail


@pytest.mark.asyncio
async def test_generate_answer_computes_usage_and_records_tokens_to_telemetry(monkeypatch):
    monkeypatch.setattr(generation_service, "generate_answer", _real_generate_answer)
    parsed = GeneratedAnswer(status="answered", answer_text="42", citations=[])
    monkeypatch.setattr(
        generation_service, "_client", lambda: _fake_client(completion=_fake_completion(parsed))
    )
    recorded = []
    monkeypatch.setattr(telemetry_module, "record_generation_tokens", recorded.append)

    result, usage = await generation_service.generate_answer(
        question="What is it?", passages=[_passage()]
    )

    assert result is parsed
    assert usage.prompt_tokens == 100
    assert usage.completion_tokens == 20
    assert usage.total_tokens == 120
    assert usage.context_window_utilization == pytest.approx(120 / 128_000)
    assert recorded == [120]


@pytest.mark.asyncio
async def test_generate_answer_handles_a_missing_usage_object(monkeypatch):
    monkeypatch.setattr(generation_service, "generate_answer", _real_generate_answer)
    parsed = GeneratedAnswer(status="no_answer_found", answer_text=None, citations=[])
    completion = _fake_completion(parsed, total_tokens=None)
    monkeypatch.setattr(generation_service, "_client", lambda: _fake_client(completion=completion))
    monkeypatch.setattr(telemetry_module, "record_generation_tokens", lambda _: None)

    _, usage = await generation_service.generate_answer(question="?", passages=[])

    assert usage.prompt_tokens == 0
    assert usage.completion_tokens == 0
    assert usage.total_tokens == 0
    assert usage.context_window_utilization == 0.0


@pytest.mark.asyncio
async def test_generate_answer_rejects_an_unparseable_response(monkeypatch):
    monkeypatch.setattr(generation_service, "generate_answer", _real_generate_answer)
    completion = _fake_completion(parsed=None)
    monkeypatch.setattr(generation_service, "_client", lambda: _fake_client(completion=completion))

    with pytest.raises(UpstreamServiceError):
        await generation_service.generate_answer(question="?", passages=[])


@pytest.mark.asyncio
async def test_generate_answer_wraps_openai_errors_without_leaking_the_original_message(
    monkeypatch,
):
    monkeypatch.setattr(generation_service, "generate_answer", _real_generate_answer)
    monkeypatch.setattr(
        generation_service,
        "_client",
        lambda: _fake_client(completion_error=openai.OpenAIError("token sk-secretvalue invalid")),
    )

    with pytest.raises(UpstreamServiceError) as exc_info:
        await generation_service.generate_answer(question="?", passages=[])

    assert "sk-secretvalue" not in exc_info.value.detail
