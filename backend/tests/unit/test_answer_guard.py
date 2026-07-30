"""An Answer cannot be persisted with groundedness_status=grounded and zero
citations (FR-015, /speckit-analyze finding U2): a hallucinated "answered"
result with no supporting passages must be rejected/downgraded.
"""

import pytest

from src.models.db import GroundednessStatus, QueryStatus, User
from src.models.schemas import GeneratedAnswer
from src.services import generation_service, query_service
from src.services.generation_service import UsageInfo


async def _make_user(db_session, username: str) -> User:
    user = User(email=f"{username}@example.com", username=username, password_hash="x")
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_answered_with_zero_citations_is_downgraded_to_no_answer_found(
    db_session, monkeypatch
):
    async def hallucinating_generate_answer(*, question, passages):
        return (
            GeneratedAnswer(
                status="answered",
                answer_text="This is a fabricated answer.",
                citations=[],
            ),
            UsageInfo(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
                context_window_utilization=0.01,
            ),
        )

    monkeypatch.setattr(generation_service, "generate_answer", hallucinating_generate_answer)

    user = await _make_user(db_session, "guarded1")
    query = await query_service.ask_question(
        db_session, user_id=user.id, question_text="Anything at all?"
    )

    assert query.status == QueryStatus.no_answer_found

    record = await query_service.build_query_record(db_session, query)
    assert record.answer.status == "no_answer_found"
    assert record.answer.answer_text is None
    assert record.answer.citations == []


@pytest.mark.asyncio
async def test_answered_with_citations_is_persisted_as_grounded(db_session, monkeypatch):
    async def fake_embed(texts):
        return [[0.1] * 8 for _ in texts]

    monkeypatch.setattr(generation_service, "embed", fake_embed)

    from src.services import retrieval_service
    from src.services.retrieval_service import Passage

    async def fake_search(**kwargs):
        return [Passage(id="doc1_0", document_id="doc1", location_label="Page 1", content="fact")]

    monkeypatch.setattr(retrieval_service, "search", fake_search)

    async def grounded_generate_answer(*, question, passages):
        return (
            GeneratedAnswer(
                status="answered",
                answer_text="A real answer.",
                citations=[{"passage_id": "doc1_0", "location_label": "Page 1"}],
            ),
            UsageInfo(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
                context_window_utilization=0.01,
            ),
        )

    monkeypatch.setattr(generation_service, "generate_answer", grounded_generate_answer)

    user = await _make_user(db_session, "guarded2")
    query = await query_service.ask_question(
        db_session, user_id=user.id, question_text="What is the fact?"
    )

    assert query.status == QueryStatus.answered

    from sqlalchemy import select

    from src.models.db import Answer

    result = await db_session.execute(select(Answer).where(Answer.query_id == query.id))
    answer = result.scalar_one()
    assert answer.groundedness_status == GroundednessStatus.grounded
