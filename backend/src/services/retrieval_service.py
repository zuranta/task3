"""Azure AI Search hybrid (vector + keyword) retrieval (research.md §3).

Every query applies a server-injected `user_id eq ... and status eq 'active'`
filter -- never a client-suppliable one -- so cross-user data isolation
(FR-006/SC-007) is enforced at this layer regardless of what any caller passes
in. Passages are upserted on document ingest and removed on document delete.
"""

from dataclasses import dataclass
from functools import lru_cache

from azure.core.exceptions import HttpResponseError
from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.aio import SearchClient
from azure.search.documents.indexes.aio import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

from src.core.config import get_settings
from src.core.errors import UpstreamServiceError

_EMBEDDING_DIMENSIONS = 1536
_VECTOR_PROFILE_NAME = "rag-hnsw-profile"
_VECTOR_ALGORITHM_NAME = "rag-hnsw"


@dataclass(frozen=True)
class Passage:
    id: str
    document_id: str
    location_label: str
    content: str


def _passage_id(document_id: str, chunk_index: int) -> str:
    return f"{document_id}_{chunk_index}"


@lru_cache
def _credential() -> DefaultAzureCredential:
    return DefaultAzureCredential()


@lru_cache
def _search_client() -> SearchClient:
    settings = get_settings()
    return SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=settings.azure_search_index_name,
        credential=_credential(),
    )


@lru_cache
def _index_client() -> SearchIndexClient:
    settings = get_settings()
    return SearchIndexClient(endpoint=settings.azure_search_endpoint, credential=_credential())


def _index_schema(index_name: str) -> SearchIndex:
    return SearchIndex(
        name=index_name,
        fields=[
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="document_id", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="user_id", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="status", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="chunk_index", type=SearchFieldDataType.Int32),
            SearchableField(name="location_label", type=SearchFieldDataType.String),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=_EMBEDDING_DIMENSIONS,
                vector_search_profile_name=_VECTOR_PROFILE_NAME,
            ),
        ],
        vector_search=VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name=_VECTOR_ALGORITHM_NAME)],
            profiles=[
                VectorSearchProfile(
                    name=_VECTOR_PROFILE_NAME, algorithm_configuration_name=_VECTOR_ALGORITHM_NAME
                )
            ],
        ),
    )


async def ensure_index_exists() -> None:
    settings = get_settings()
    client = _index_client()
    try:
        await client.get_index(settings.azure_search_index_name)
    except HttpResponseError as exc:
        if exc.status_code != 404:
            raise UpstreamServiceError(
                "The document search service is temporarily unavailable."
            ) from exc
        await client.create_index(_index_schema(settings.azure_search_index_name))


async def index_passages(
    *,
    document_id: str,
    user_id: str,
    chunks: list[str],
    location_labels: list[str],
    embeddings: list[list[float]],
) -> None:
    """Upsert one search document per chunk, marked `status=active`."""
    client = _search_client()
    docs = [
        {
            "id": _passage_id(document_id, i),
            "document_id": document_id,
            "user_id": user_id,
            "status": "active",
            "chunk_index": i,
            "location_label": location_labels[i],
            "content": chunk,
            "content_vector": embeddings[i],
        }
        for i, chunk in enumerate(chunks)
    ]
    try:
        await client.upload_documents(docs)
    except HttpResponseError as exc:
        raise UpstreamServiceError(
            "The document could not be indexed for search right now. Please try again."
        ) from exc


async def delete_document_passages(document_id: str) -> None:
    """Remove a document's passages from the index (FR-010): no longer retrievable."""
    client = _search_client()
    try:
        results = await client.search(search_text="*", filter=f"document_id eq '{document_id}'")
        keys = [doc["id"] async for doc in results]
        if keys:
            await client.delete_documents([{"id": key} for key in keys])
    except HttpResponseError as exc:
        raise UpstreamServiceError(
            "The document could not be removed from search right now. Please try again."
        ) from exc


async def list_passages(*, user_id: str, document_id: str) -> list[Passage]:
    """All active passages for one document, in their original chunk order --
    powers the "view the source" affordance (clicking a document to see what
    it was indexed as). Scoped by the same mandatory user_id+status filter as
    `search`, never a client-suppliable one (research.md §3).

    Sorts client-side rather than via Azure AI Search's `$orderby` on
    `chunk_index`: that field isn't marked `sortable` in the index schema
    (nothing needed to sort by it before this feature), and Azure AI Search
    cannot add `sortable` to a field of an already-existing index without
    rebuilding it -- so a server-side orderby would 400 for every
    already-provisioned deployment, not just newly-created ones.
    """
    client = _search_client()
    filter_expr = (
        f"document_id eq '{document_id}' and user_id eq '{user_id}' and status eq 'active'"
    )
    try:
        results = await client.search(search_text="*", filter=filter_expr)
        docs = [doc async for doc in results]
    except HttpResponseError as exc:
        raise UpstreamServiceError(
            "The document's passages could not be retrieved right now. Please try again."
        ) from exc

    docs.sort(key=lambda doc: doc["chunk_index"])
    return [
        Passage(
            id=doc["id"],
            document_id=doc["document_id"],
            location_label=doc["location_label"],
            content=doc["content"],
        )
        for doc in docs
    ]


async def search(*, user_id: str, question: str, question_vector: list[float]) -> list[Passage]:
    """Hybrid vector+keyword search, mandatorily scoped to the caller's own active documents."""
    settings = get_settings()
    client = _search_client()
    try:
        results = await client.search(
            search_text=question,
            vector_queries=[
                VectorizedQuery(
                    vector=question_vector,
                    k_nearest_neighbors=settings.retrieval_top_k,
                    fields="content_vector",
                )
            ],
            filter=f"user_id eq '{user_id}' and status eq 'active'",
            top=settings.retrieval_top_k,
        )
        return [
            Passage(
                id=doc["id"],
                document_id=doc["document_id"],
                location_label=doc["location_label"],
                content=doc["content"],
            )
            async for doc in results
        ]
    except HttpResponseError as exc:
        raise UpstreamServiceError(
            "The document search could not be completed right now. Please try again."
        ) from exc
