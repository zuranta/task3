"""Every document_service/query_service read and write requires and applies the
authenticated user_id (research.md §7, mirrors test_retrieval_service.py's
pattern for the SQLite-backed side of FR-006/SC-007).

list_queries/get_query don't exist yet (User Story 3); this covers the US2
surface: document list/delete, and that ask_question's persisted Query/Answer/
Citation rows are correctly scoped to the calling user.
"""

import pytest
from sqlalchemy import select

from src.core.errors import NotFoundError
from src.models.db import Query as QueryRow
from src.models.db import User
from src.services import document_service, query_service


async def _make_user(db_session, username: str) -> User:
    user = User(email=f"{username}@example.com", username=username, password_hash="x")
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_list_documents_only_returns_the_calling_users_documents(db_session):
    user_a = await _make_user(db_session, "isoa1")
    user_b = await _make_user(db_session, "isob1")

    await document_service.upload_document(
        db_session, user_id=user_a.id, filename="a.txt", content=b"user A's document content"
    )

    docs_for_a = await document_service.list_documents(db_session, user_id=user_a.id)
    docs_for_b = await document_service.list_documents(db_session, user_id=user_b.id)

    assert len(docs_for_a) == 1
    assert docs_for_b == []


@pytest.mark.asyncio
async def test_delete_document_rejects_a_non_owning_user(db_session):
    user_a = await _make_user(db_session, "isoa2")
    user_b = await _make_user(db_session, "isob2")

    document = await document_service.upload_document(
        db_session, user_id=user_a.id, filename="a.txt", content=b"user A's document content"
    )

    with pytest.raises(NotFoundError):
        await document_service.delete_document(
            db_session, user_id=user_b.id, document_id=document.id
        )


@pytest.mark.asyncio
async def test_ask_question_persists_query_scoped_to_the_calling_user(db_session):
    user_a = await _make_user(db_session, "isoa3")
    user_b = await _make_user(db_session, "isob3")

    query = await query_service.ask_question(
        db_session, user_id=user_a.id, question_text="Whose data is this?"
    )

    assert query.user_id == user_a.id

    result = await db_session.execute(select(QueryRow).where(QueryRow.user_id == user_b.id))
    assert result.scalars().all() == []
