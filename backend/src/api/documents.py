"""Upload, list, delete documents (FR-008 through FR-010, FR-012)."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.core.security import get_current_user
from src.models.db import User
from src.models.schemas import DocumentOut
from src.services import document_service

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def _to_schema(document) -> DocumentOut:
    return DocumentOut(
        id=document.id,
        original_filename=document.original_filename,
        format=document.format.value,
        status=document.status.value,
        failure_reason=document.failure_reason,
        uploaded_at=document.uploaded_at,
    )


@router.post("", response_model=DocumentOut, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: Annotated[UploadFile, File()],
) -> DocumentOut:
    content = await file.read()
    document = await document_service.upload_document(
        db, user_id=user.id, filename=file.filename or "", content=content
    )
    return _to_schema(document)


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DocumentOut]:
    documents = await document_service.list_documents(db, user_id=user.id)
    return [_to_schema(d) for d in documents]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await document_service.delete_document(db, user_id=user.id, document_id=document_id)
