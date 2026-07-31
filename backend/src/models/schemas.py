"""Pydantic request/response schemas.

Populated incrementally per user story: the shared Error schema here
(Foundational); auth schemas in User Story 1; document/query/answer/
citation schemas in User Story 2; eval schemas in User Story 4.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class Error(BaseModel):
    """Clear, user-facing, non-leaking error message (FR-021).

    Never contains stack traces, credentials, infrastructure hostnames, or
    raw third-party error payloads.
    """

    detail: str


# --- User Story 1: Register and Log In -------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, description="Either the account's email or username.")
    password: str = Field(min_length=1)


class AuthToken(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


# --- User Story 2: Ask Grounded, Cited Questions ----------------------------------


class DocumentOut(BaseModel):
    id: str
    original_filename: str
    format: Literal["pdf", "docx", "txt", "md"]
    status: Literal["processing", "ready", "failed", "deleted"]
    failure_reason: str | None = None
    uploaded_at: datetime


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)


class Citation(BaseModel):
    document_id: str
    document_filename: str
    location_label: str
    source_removed: bool


class ResponseMetadata(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    context_window_utilization: float


class Answer(BaseModel):
    status: Literal["answered", "no_answer_found"]
    answer_text: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    metadata: ResponseMetadata


class QueryRecord(BaseModel):
    id: str
    question: str
    status: Literal["answered", "no_answer_found", "failed"]
    answer: Answer | None = None
    created_at: datetime


# --- Structured Outputs: the shape Azure OpenAI is constrained to produce ---------


class GeneratedCitation(BaseModel):
    """One passage the model grounded its answer in, by Source Passage id."""

    passage_id: str
    location_label: str


class GeneratedAnswer(BaseModel):
    """Bound directly to Azure OpenAI Structured Outputs (research.md §4).

    `passage_id` values must be drawn from the passages supplied in the prompt;
    `query_service` maps them back to full Citation records (with document
    filename / source_removed) before persistence and response.
    """

    status: Literal["answered", "no_answer_found"]
    answer_text: str | None = None
    citations: list[GeneratedCitation] = Field(default_factory=list)


# --- User Story 4: Compare Two System Versions Against a Benchmark Dataset --------


class DatasetItem(BaseModel):
    id: str | None = None
    question: str = Field(min_length=1)
    expected_answer: str = Field(min_length=1)
    expected_source_reference: str | None = None


class ComparisonRunRequest(BaseModel):
    version_a_label: str = Field(min_length=1)
    version_b_label: str = Field(min_length=1)


class DeleteIdsRequest(BaseModel):
    ids: list[str] = Field(min_length=1)


class AggregateScore(BaseModel):
    correctness: float
    relevance: float
    groundedness: float


class ComparisonRun(BaseModel):
    id: str
    version_a_label: str
    version_b_label: str
    status: Literal["running", "completed", "partial"]
    aggregate_score_a: AggregateScore | None = None
    aggregate_score_b: AggregateScore | None = None
    winner: Literal["a", "b", "tie"] | None = None
    started_at: datetime
    completed_at: datetime | None = None
