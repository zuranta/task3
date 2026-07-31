"""The model can list the same passage_id more than once in its structured
citations output (e.g. it drew on one passage for more than one part of the
answer). Persisting one Citation row per list entry would then show the same
document/location twice to the user -- ask_question must persist each cited
passage at most once.
"""

import pytest

from src.models.db import Document, DocumentFormat, DocumentStatus, User
from src.models.schemas import GeneratedAnswer
from src.services import generation_service, query_service, retrieval_service
from src.services.generation_service import UsageInfo
from src.services.retrieval_service import Passage


async def _make_user(db_session, username: str) -> User:
    user = User(email=f"{username}@example.com", username=username, password_hash="x")
    db_session.add(user)
    await db_session.flush()
    return user


async def _make_document(db_session, user_id: str, document_id: str) -> Document:
    document = Document(
        id=document_id,
        user_id=user_id,
        original_filename="handbook.txt",
        format=DocumentFormat.txt,
        status=DocumentStatus.ready,
    )
    db_session.add(document)
    await db_session.flush()
    return document


@pytest.mark.asyncio
async def test_a_passage_cited_twice_by_the_model_persists_only_one_citation(
    db_session, monkeypatch
):
    async def fake_embed(texts):
        return [[0.1] * 8 for _ in texts]

    monkeypatch.setattr(generation_service, "embed", fake_embed)

    async def fake_search(**kwargs):
        return [
            Passage(
                id="doc1_0", document_id="doc1", location_label="Section 1 of 1", content="fact"
            )
        ]

    monkeypatch.setattr(retrieval_service, "search", fake_search)

    async def duplicate_citing_generate_answer(*, question, passages):
        return (
            GeneratedAnswer(
                status="answered",
                answer_text="A real answer, twice-grounded in the same passage.",
                citations=[
                    {"passage_id": "doc1_0", "location_label": "Section 1 of 1"},
                    {"passage_id": "doc1_0", "location_label": "Section 1 of 1"},
                ],
            ),
            UsageInfo(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
                context_window_utilization=0.01,
            ),
        )

    monkeypatch.setattr(generation_service, "generate_answer", duplicate_citing_generate_answer)

    user = await _make_user(db_session, "dedup1")
    await _make_document(db_session, user.id, "doc1")
    query = await query_service.ask_question(
        db_session, user_id=user.id, question_text="What is the fact?"
    )

    record = await query_service.build_query_record(db_session, query)
    assert record.answer.status == "answered"
    assert len(record.answer.citations) == 1
    assert record.answer.citations[0].document_id == "doc1"
    assert record.answer.citations[0].location_label == "Section 1 of 1"
