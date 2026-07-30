"""Ask a question over the caller's own documents (FR-011, FR-013-FR-017), and
browse/replay the caller's own query history (FR-019, FR-020)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import Query as QueryParam
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


@router.get("", response_model=list[QueryRecord])
async def list_queries(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, QueryParam(ge=1, le=100)] = 20,
    offset: Annotated[int, QueryParam(ge=0)] = 0,
) -> list[QueryRecord]:
    queries = await query_service.list_queries(db, user_id=user.id, limit=limit, offset=offset)
    return [await query_service.build_query_record(db, q) for q in queries]


@router.get("/{query_id}", response_model=QueryRecord)
async def get_query(
    query_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QueryRecord:
    query = await query_service.get_query(db, user_id=user.id, query_id=query_id)
    return await query_service.build_query_record(db, query)
