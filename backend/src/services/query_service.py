"""Ask-question orchestration (FR-011, FR-013-FR-017).

Flow: rate-limit check -> retrieval -> generation -> zero-citation
groundedness guard -> persistence. Every read/write is scoped by the
authenticated user_id (research.md §7); a retrieval or generation failure is
persisted as a `failed` Query and re-raised so the API layer maps it to a
non-leaking 502 (FR-021).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.config import get_settings
from src.core.errors import AppError, NotFoundError
from src.models import schemas
from src.models.db import (
    Answer,
    Citation,
    Document,
    DocumentStatus,
    GroundednessStatus,
    Query,
    QueryStatus,
    RateLimitCounterType,
)
from src.services import generation_service, rate_limit_service, retrieval_service


async def ask_question(db: AsyncSession, *, user_id: str, question_text: str) -> Query:
    settings = get_settings()
    await rate_limit_service.check_and_increment(
        db,
        user_id=user_id,
        counter_type=RateLimitCounterType.question,
        limit=settings.question_rate_limit_per_day,
    )

    query = Query(user_id=user_id, question_text=question_text, status=QueryStatus.failed)
    db.add(query)
    await db.flush()

    try:
        question_vector = (await generation_service.embed([question_text]))[0]
        passages = await retrieval_service.search(
            user_id=user_id, question=question_text, question_vector=question_vector
        )
        generated, usage = await generation_service.generate_answer(
            question=question_text, passages=passages
        )
    except AppError:
        await db.commit()  # persists the `failed` status set above
        raise

    # Zero-citation groundedness guard (/speckit-analyze finding U2): an
    # "answered" result with no citations is downgraded rather than persisted
    # as grounded (FR-015).
    if generated.status == "answered" and not generated.citations:
        generated = generated.model_copy(
            update={"status": "no_answer_found", "answer_text": None, "citations": []}
        )

    query.status = (
        QueryStatus.answered if generated.status == "answered" else QueryStatus.no_answer_found
    )
    groundedness = (
        GroundednessStatus.grounded
        if generated.status == "answered"
        else GroundednessStatus.no_answer_found
    )

    answer = Answer(
        query_id=query.id,
        answer_text=generated.answer_text,
        groundedness_status=groundedness,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
        context_window_utilization=usage.context_window_utilization,
    )
    db.add(answer)
    await db.flush()

    passages_by_id = {p.id: p for p in passages}
    for cited in generated.citations:
        passage = passages_by_id.get(cited.passage_id)
        if passage is None:
            continue
        db.add(
            Citation(
                answer_id=answer.id,
                document_id=passage.document_id,
                location_label=passage.location_label,
            )
        )

    await db.commit()
    await db.refresh(query)
    return query


async def build_query_record(db: AsyncSession, query: Query) -> schemas.QueryRecord:
    """Assembles the API response shape for a Query, exactly as originally answered (FR-020)."""
    result = await db.execute(
        select(Answer).options(selectinload(Answer.citations)).where(Answer.query_id == query.id)
    )
    answer = result.scalar_one_or_none()

    if answer is None:
        return schemas.QueryRecord(
            id=query.id,
            question=query.question_text,
            status=query.status.value,
            created_at=query.created_at,
        )

    document_ids = {c.document_id for c in answer.citations}
    documents_result = await db.execute(select(Document).where(Document.id.in_(document_ids)))
    documents_by_id = {d.id: d for d in documents_result.scalars().all()}

    citations = [
        schemas.Citation(
            document_id=c.document_id,
            document_filename=documents_by_id[c.document_id].original_filename,
            location_label=c.location_label,
            source_removed=documents_by_id[c.document_id].status == DocumentStatus.deleted,
        )
        for c in answer.citations
    ]

    answer_schema = schemas.Answer(
        status=query.status.value,
        answer_text=answer.answer_text,
        citations=citations,
        metadata=schemas.ResponseMetadata(
            prompt_tokens=answer.prompt_tokens,
            completion_tokens=answer.completion_tokens,
            total_tokens=answer.total_tokens,
            context_window_utilization=answer.context_window_utilization,
        ),
    )

    return schemas.QueryRecord(
        id=query.id,
        question=query.question_text,
        status=query.status.value,
        answer=answer_schema,
        created_at=query.created_at,
    )


async def list_queries(
    db: AsyncSession, *, user_id: str, limit: int = 20, offset: int = 0
) -> list[Query]:
    """Caller's own past queries, most-recent-first (FR-019). An empty list for
    an account with no history is a normal result, not an error."""
    result = await db.execute(
        select(Query)
        .where(Query.user_id == user_id)
        .order_by(Query.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_query(db: AsyncSession, *, user_id: str, query_id: str) -> Query:
    """One of the caller's own past queries, exactly as originally answered (FR-020)."""
    result = await db.execute(select(Query).where(Query.id == query_id, Query.user_id == user_id))
    query = result.scalar_one_or_none()
    if query is None:
        raise NotFoundError("Query not found.")
    return query
