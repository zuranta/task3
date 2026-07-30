"""SQLAlchemy ORM models.

Populated incrementally per user story: User here (Foundational); Document,
Query, Answer, Citation, RateLimitCounter in User Story 2; ComparisonRun in
User Story 4.
"""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.db import Base


class UserRole(enum.StrEnum):
    user = "user"
    admin = "admin"


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False), default=UserRole.user, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# --- User Story 2: Ask Grounded, Cited Questions ----------------------------------


class DocumentFormat(enum.StrEnum):
    pdf = "pdf"
    docx = "docx"
    txt = "txt"
    md = "md"


class DocumentStatus(enum.StrEnum):
    processing = "processing"
    ready = "ready"
    failed = "failed"
    deleted = "deleted"


class QueryStatus(enum.StrEnum):
    answered = "answered"
    no_answer_found = "no_answer_found"
    failed = "failed"


class GroundednessStatus(enum.StrEnum):
    grounded = "grounded"
    no_answer_found = "no_answer_found"


class RateLimitCounterType(enum.StrEnum):
    upload = "upload"
    question = "question"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[DocumentFormat] = mapped_column(Enum(DocumentFormat, native_enum=False))
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False), default=DocumentStatus.processing
    )
    failure_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Query(Base):
    __tablename__ = "queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[QueryStatus] = mapped_column(Enum(QueryStatus, native_enum=False))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    answer: Mapped["Answer | None"] = relationship(back_populates="query", uselist=False)


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    query_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("queries.id"), nullable=False, unique=True
    )
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    groundedness_status: Mapped[GroundednessStatus] = mapped_column(
        Enum(GroundednessStatus, native_enum=False)
    )
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    context_window_utilization: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    query: Mapped["Query"] = relationship(back_populates="answer")
    citations: Mapped[list["Citation"]] = relationship(back_populates="answer")


class Citation(Base):
    __tablename__ = "citations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    answer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("answers.id"), nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id"), nullable=False)
    location_label: Mapped[str] = mapped_column(String(255), nullable=False)

    answer: Mapped["Answer"] = relationship(back_populates="citations")
    document: Mapped["Document"] = relationship()


class RateLimitCounter(Base):
    __tablename__ = "rate_limit_counters"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    counter_type: Mapped[RateLimitCounterType] = mapped_column(
        Enum(RateLimitCounterType, native_enum=False), primary_key=True
    )
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    count: Mapped[int] = mapped_column(Integer, default=0)
