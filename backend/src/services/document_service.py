"""Document upload validation, parsing/chunking, and lifecycle (FR-008, FR-009, FR-010).

Every read/write here is scoped by the authenticated user_id (research.md §7):
list/get/delete all filter on Document.user_id at the query level, never
fetch-then-filter-in-Python.
"""

import io

import docx
import pypdf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.core.errors import AppError, BadRequestError, NotFoundError
from src.models.db import Document, DocumentFormat, DocumentStatus, RateLimitCounterType
from src.services import generation_service, rate_limit_service, retrieval_service

_CHUNK_SIZE = 1000

_EXTENSION_TO_FORMAT = {
    "pdf": DocumentFormat.pdf,
    "docx": DocumentFormat.docx,
    "txt": DocumentFormat.txt,
    "md": DocumentFormat.md,
}


def _detect_format(filename: str) -> DocumentFormat:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    fmt = _EXTENSION_TO_FORMAT.get(ext)
    if fmt is None:
        raise BadRequestError("Unsupported file format. Supported formats: pdf, docx, txt, md.")
    return fmt


def _extract_pdf(content: bytes) -> list[tuple[str | None, str]]:
    """Returns a list of (page_label, text), one entry per page."""
    try:
        reader = pypdf.PdfReader(io.BytesIO(content))
    except Exception as exc:
        raise BadRequestError("The file is corrupted and could not be read.") from exc
    if reader.is_encrypted:
        raise BadRequestError("The file is password-protected and could not be read.")
    try:
        return [(f"Page {i + 1}", page.extract_text() or "") for i, page in enumerate(reader.pages)]
    except Exception as exc:
        raise BadRequestError("The file is corrupted and could not be read.") from exc


def _extract_docx(content: bytes) -> list[tuple[str | None, str]]:
    try:
        document = docx.Document(io.BytesIO(content))
    except Exception as exc:
        raise BadRequestError(
            "The file is corrupted or password-protected and could not be read."
        ) from exc
    return [(None, "\n".join(p.text for p in document.paragraphs))]


def _extract_text(content: bytes) -> list[tuple[str | None, str]]:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BadRequestError("The file is corrupted and could not be read.") from exc
    return [(None, text)]


def _extract(fmt: DocumentFormat, content: bytes) -> list[tuple[str | None, str]]:
    if fmt == DocumentFormat.pdf:
        return _extract_pdf(content)
    if fmt == DocumentFormat.docx:
        return _extract_docx(content)
    return _extract_text(content)


def chunk_document(fmt: DocumentFormat, content: bytes) -> tuple[list[str], list[str]]:
    """Returns (chunks, location_labels) -- one location label per chunk, combining
    the page number (pdf only, since other formats have no native page concept)
    with a 1-indexed section number so multiple chunks from the same page/document
    stay distinguishable in citations (e.g. "Page 2, Section 1 of 3")."""
    sections = _extract(fmt, content)
    chunks: list[str] = []
    labels: list[str] = []
    for page_label, text in sections:
        text = text.strip()
        if not text:
            continue
        pieces = [
            piece
            for start in range(0, len(text), _CHUNK_SIZE)
            if (piece := text[start : start + _CHUNK_SIZE].strip())
        ]
        for i, piece in enumerate(pieces, start=1):
            section_label = f"Section {i} of {len(pieces)}"
            label = f"{page_label}, {section_label}" if page_label else section_label
            chunks.append(piece)
            labels.append(label)
    if not chunks:
        raise BadRequestError("The file is empty and contains no extractable text.")
    return chunks, labels


async def upload_document(
    db: AsyncSession, *, user_id: str, filename: str, content: bytes
) -> Document:
    settings = get_settings()
    if not content:
        raise BadRequestError("The file is empty.")
    if len(content) > settings.max_upload_size_bytes:
        max_mb = settings.max_upload_size_bytes // (1024 * 1024)
        raise BadRequestError(f"The file exceeds the maximum upload size of {max_mb} MB.")
    fmt = _detect_format(filename)

    await rate_limit_service.check_and_increment(
        db,
        user_id=user_id,
        counter_type=RateLimitCounterType.upload,
        limit=settings.upload_rate_limit_per_day,
    )

    document = Document(
        user_id=user_id, original_filename=filename, format=fmt, status=DocumentStatus.processing
    )
    db.add(document)
    await db.flush()

    try:
        chunks, labels = chunk_document(fmt, content)
        embeddings = await generation_service.embed(chunks)
        await retrieval_service.ensure_index_exists()
        await retrieval_service.index_passages(
            document_id=document.id,
            user_id=user_id,
            chunks=chunks,
            location_labels=labels,
            embeddings=embeddings,
        )
    except AppError as exc:
        document.status = DocumentStatus.failed
        document.failure_reason = exc.detail
        await db.commit()
        raise

    document.status = DocumentStatus.ready
    await db.commit()
    await db.refresh(document)
    return document


async def list_documents(db: AsyncSession, *, user_id: str) -> list[Document]:
    result = await db.execute(
        select(Document).where(Document.user_id == user_id).order_by(Document.uploaded_at.desc())
    )
    return list(result.scalars().all())


async def delete_document(db: AsyncSession, *, user_id: str, document_id: str) -> None:
    result = await db.execute(
        select(Document).where(Document.id == document_id, Document.user_id == user_id)
    )
    document = result.scalar_one_or_none()
    if document is None or document.status == DocumentStatus.deleted:
        raise NotFoundError("Document not found.")

    await retrieval_service.delete_document_passages(document_id)
    document.status = DocumentStatus.deleted
    await db.commit()
