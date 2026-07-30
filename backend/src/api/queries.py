"""Ask a question over the caller's own documents (FR-011, FR-013-FR-017).

GET /queries and GET /queries/{queryId} (history/replay) are User Story 3
(spec.md priority P2) and are added to this router in that phase.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.security import get_current_user
from src.models.db import User
from src.models.schemas import QueryRecord, QueryRequest
from src.services import query_service

router = APIRouter(prefix="/api/v1/queries", tags=["queries"])


@router.post("", response_model=QueryRecord)
async def ask_question(
    body: QueryRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QueryRecord:
    query = await query_service.ask_question(db, user_id=user.id, question_text=body.question)
    return await query_service.build_query_record(db, query)
