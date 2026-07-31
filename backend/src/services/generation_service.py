"""Azure OpenAI embeddings + Structured Outputs generation (research.md §4).

Authenticated via `DefaultAzureCredential` (Entra ID token, `Cognitive Services
OpenAI User` role) against the existing `aoai-jab4fcusuxtqs` resource -- no API
keys. Chat responses are constrained to the `GeneratedAnswer` Pydantic model
via the SDK's Structured Outputs feature, so a malformed response is a hard
SDK-level error rather than a parsing gamble.
"""

from dataclasses import dataclass
from functools import lru_cache

import openai
from azure.identity.aio import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI

from src.core import telemetry
from src.core.config import get_settings
from src.core.errors import UpstreamServiceError
from src.models.schemas import GeneratedAnswer
from src.services.retrieval_service import Passage

_COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"

_SYSTEM_PROMPT = (
    "You are a document Q&A assistant. Answer strictly using only the numbered "
    "passages provided below, each tagged with a passage id. If the passages do "
    "not contain the answer, set status to 'no_answer_found' and leave answer_text "
    "empty -- never fabricate an answer from outside knowledge. When you do answer, "
    "cite every passage_id you actually relied on."
)


@dataclass(frozen=True)
class UsageInfo:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    context_window_utilization: float


@lru_cache
def _credential() -> DefaultAzureCredential:
    return DefaultAzureCredential()


@lru_cache
def _client() -> AsyncAzureOpenAI:
    settings = get_settings()
    token_provider = get_bearer_token_provider(_credential(), _COGNITIVE_SERVICES_SCOPE)
    return AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        azure_ad_token_provider=token_provider,
        api_version="2024-10-21",
    )


async def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    settings = get_settings()
    try:
        response = await _client().embeddings.create(
            model=settings.azure_openai_embedding_deployment, input=texts
        )
    except openai.OpenAIError as exc:
        raise UpstreamServiceError(
            "The embedding service could not be reached right now. Please try again."
        ) from exc
    return [item.embedding for item in response.data]


def _format_passages(passages: list[Passage]) -> str:
    return "\n\n".join(
        f"[passage_id={p.id} location={p.location_label}]\n{p.content}" for p in passages
    )


async def generate_answer(
    *, question: str, passages: list[Passage]
) -> tuple[GeneratedAnswer, UsageInfo]:
    settings = get_settings()
    try:
        completion = await _client().beta.chat.completions.parse(
            model=settings.azure_openai_deployment,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Passages:\n{_format_passages(passages)}\n\nQuestion: {question}",
                },
            ],
            response_format=GeneratedAnswer,
        )
    except openai.OpenAIError as exc:
        raise UpstreamServiceError(
            "The answer generation service could not be reached right now. Please try again."
        ) from exc

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise UpstreamServiceError(
            "The answer generation service returned an unexpected response. Please try again."
        )

    usage = completion.usage
    total_tokens = usage.total_tokens if usage else 0
    usage_info = UsageInfo(
        prompt_tokens=usage.prompt_tokens if usage else 0,
        completion_tokens=usage.completion_tokens if usage else 0,
        total_tokens=total_tokens,
        context_window_utilization=total_tokens / settings.azure_openai_model_context_window,
    )
    telemetry.record_generation_tokens(total_tokens)
    return parsed, usage_info
