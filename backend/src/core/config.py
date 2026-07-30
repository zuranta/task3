"""Application settings.

Non-secret settings come from environment variables (see .env.example).
The two secrets with no managed-identity equivalent -- the JWT signing key
and the LangSmith API key -- are resolved from Azure Key Vault at startup
via DefaultAzureCredential, never from a plain environment value.
"""

from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    azure_openai_endpoint: str
    azure_openai_deployment: str = "gpt-5.1"
    azure_search_endpoint: str
    azure_search_index_name: str = "rag-documents"
    key_vault_uri: str
    applicationinsights_connection_string: str | None = None

    database_url: str = "sqlite+aiosqlite:///./rag_document_qa.db"

    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60

    upload_rate_limit_per_day: int = 50
    question_rate_limit_per_day: int = 200
    max_upload_size_bytes: int = 10 * 1024 * 1024


class Secrets:
    """Lazily-resolved secrets from Key Vault, cached for the process lifetime."""

    def __init__(self, key_vault_uri: str) -> None:
        self._client = SecretClient(vault_url=key_vault_uri, credential=DefaultAzureCredential())
        self._jwt_signing_secret: str | None = None
        self._langsmith_api_key: str | None = None

    @property
    def jwt_signing_secret(self) -> str:
        if self._jwt_signing_secret is None:
            self._jwt_signing_secret = self._client.get_secret("JwtSigningSecret").value
        return self._jwt_signing_secret

    @property
    def langsmith_api_key(self) -> str:
        if self._langsmith_api_key is None:
            self._langsmith_api_key = self._client.get_secret("LangSmithApiKey").value
        return self._langsmith_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_secrets() -> Secrets:
    return Secrets(get_settings().key_vault_uri)
