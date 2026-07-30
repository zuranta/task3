from io import BytesIO

import pypdf
import pytest

from src.core.config import get_settings
from src.core.errors import BadRequestError
from src.models.db import DocumentFormat, User
from src.services import document_service


def _encrypted_pdf_bytes() -> bytes:
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.encrypt(user_password="secret")
    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_detect_format_rejects_unsupported_extension():
    with pytest.raises(BadRequestError):
        document_service._detect_format("virus.exe")


def test_detect_format_rejects_missing_extension():
    with pytest.raises(BadRequestError):
        document_service._detect_format("no_extension")


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("a.pdf", DocumentFormat.pdf),
        ("a.docx", DocumentFormat.docx),
        ("a.txt", DocumentFormat.txt),
        ("a.md", DocumentFormat.md),
        ("A.PDF", DocumentFormat.pdf),
    ],
)
def test_detect_format_accepts_supported_extensions(filename, expected):
    assert document_service._detect_format(filename) == expected


def test_chunk_document_rejects_empty_text():
    with pytest.raises(BadRequestError):
        document_service.chunk_document(DocumentFormat.txt, b"   \n\n   ")


def test_chunk_document_rejects_corrupted_pdf():
    with pytest.raises(BadRequestError):
        document_service.chunk_document(DocumentFormat.pdf, b"not a real pdf")


def test_chunk_document_rejects_password_protected_pdf():
    with pytest.raises(BadRequestError):
        document_service.chunk_document(DocumentFormat.pdf, _encrypted_pdf_bytes())


def test_chunk_document_rejects_corrupted_docx():
    with pytest.raises(BadRequestError):
        document_service.chunk_document(DocumentFormat.docx, b"not a real docx")


def test_chunk_document_splits_long_text_into_multiple_labeled_chunks():
    text = ("word " * 1000).encode("utf-8")

    chunks, labels = document_service.chunk_document(DocumentFormat.txt, text)

    assert len(chunks) > 1
    assert len(chunks) == len(labels)
    assert labels == [f"Section {i} of {len(chunks)}" for i in range(1, len(chunks) + 1)]


def test_chunk_document_single_chunk_text_is_labeled_section_1_of_1():
    chunks, labels = document_service.chunk_document(DocumentFormat.txt, b"A short document.")

    assert labels == ["Section 1 of 1"]


def test_chunk_document_pdf_combines_page_number_with_section_number(monkeypatch):
    long_page_text = "word " * 1000  # long enough to split into multiple chunks
    monkeypatch.setattr(
        document_service,
        "_extract",
        lambda fmt, content: [("Page 1", long_page_text), ("Page 2", "A short second page.")],
    )

    chunks, labels = document_service.chunk_document(DocumentFormat.pdf, b"unused")

    chunk_size = document_service._CHUNK_SIZE
    page_1_chunks = -(-len(long_page_text) // chunk_size)  # ceil division
    assert labels[:page_1_chunks] == [
        f"Page 1, Section {i} of {page_1_chunks}" for i in range(1, page_1_chunks + 1)
    ]
    assert labels[page_1_chunks:] == ["Page 2, Section 1 of 1"]
    assert len(chunks) == len(labels)


@pytest.mark.asyncio
async def test_upload_document_rejects_empty_content(db_session):
    user = User(email="empty@example.com", username="emptyupload", password_hash="x")
    db_session.add(user)
    await db_session.flush()

    with pytest.raises(BadRequestError):
        await document_service.upload_document(
            db_session, user_id=user.id, filename="a.txt", content=b""
        )


@pytest.mark.asyncio
async def test_upload_document_rejects_oversized_content(db_session, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_size_bytes", 10)
    user = User(email="big@example.com", username="bigupload", password_hash="x")
    db_session.add(user)
    await db_session.flush()

    with pytest.raises(BadRequestError):
        await document_service.upload_document(
            db_session,
            user_id=user.id,
            filename="a.txt",
            content=b"way more than ten bytes of content",
        )
