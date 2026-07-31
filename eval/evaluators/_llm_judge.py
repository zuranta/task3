"""Shared Azure OpenAI client for LLM-as-judge evaluators (research.md §9).

Uses its own lightweight client rather than importing backend/src -- eval/ is
intentionally decoupled from the request-serving path (plan.md's Project
Structure): it's standalone tooling, not a FastAPI dependency, authenticated
via the same DefaultAzureCredential + Cognitive Services OpenAI User role as
the backend, against the same existing Azure OpenAI deployment.
"""

import os
from functools import lru_cache

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

_COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"


@lru_cache
def _client() -> AzureOpenAI:
    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), _COGNITIVE_SERVICES_SCOPE
    )
    return AzureOpenAI(
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        azure_ad_token_provider=token_provider,
        api_version="2024-10-21",
    )


def judge(system_prompt: str, user_prompt: str) -> str:
    """Returns the raw judge response text for a yes/no-style verdict."""
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "chat")
    completion = _client().chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return completion.choices[0].message.content or ""
