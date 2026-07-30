"""Deleting a cited document retains its citation in history (marked
source_removed=true) but makes the document no longer retrievable (FR-010).

GET /queries/{id} (history replay) is User Story 3, not yet implemented, so
this test inspects the persisted record directly via query_service.
"""

import pytest
from sqlalchemy import select

from src.models.db import Query as QueryRow
from src.services import query_service


@pytest.mark.asyncio
async def test_delete_cited_document_retains_citation_but_blocks_retrieval(
    client, register_user, db_session
):
    headers, user_id = await register_user("deleter1")

    upload = await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("policy.txt", b"Refunds are processed within thirty days.", "text/plain")},
    )
    document_id = upload.json()["id"]

    ask = await client.post(
        "/api/v1/queries", headers=headers, json={"question": "How long do refunds take?"}
    )
    assert ask.json()["status"] == "answered"

    delete_response = await client.delete(f"/api/v1/documents/{document_id}", headers=headers)
    assert delete_response.status_code == 204

    result = await db_session.execute(
        select(QueryRow).where(QueryRow.user_id == user_id).order_by(QueryRow.created_at.desc())
    )
    query = result.scalars().first()
    record = await query_service.build_query_record(db_session, query)

    assert record.answer is not None
    assert len(record.answer.citations) > 0
    assert record.answer.citations[0].source_removed is True

    ask_again = await client.post(
        "/api/v1/queries", headers=headers, json={"question": "How long do refunds take?"}
    )
    assert ask_again.json()["status"] == "no_answer_found"
