from io import BytesIO

import pypdf
import pytest

from src.core.config import get_settings


def _encrypted_pdf_bytes() -> bytes:
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=72, height=72)
    writer.encrypt(user_password="secret")
    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_upload_valid_txt_file_is_accepted(client, register_user):
    headers, _ = await register_user("uploader1")

    response = await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("notes.txt", b"The capital of Freedonia is Fredonia City.", "text/plain")},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["original_filename"] == "notes.txt"
    assert body["format"] == "txt"
    assert body["status"] == "ready"


@pytest.mark.asyncio
async def test_upload_empty_file_returns_400(client, register_user):
    headers, _ = await register_user("uploader2")

    response = await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_upload_corrupted_pdf_returns_400(client, register_user):
    headers, _ = await register_user("uploader3")

    response = await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("broken.pdf", b"this is not a real pdf file", "application/pdf")},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_password_protected_pdf_returns_400(client, register_user):
    headers, _ = await register_user("uploader4")

    response = await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("locked.pdf", _encrypted_pdf_bytes(), "application/pdf")},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_oversized_file_returns_400(client, register_user, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_size_bytes", 10)
    headers, _ = await register_user("uploader5")

    response = await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("big.txt", b"this file is definitely larger than ten bytes", "text/plain")},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_unsupported_format_returns_400(client, register_user):
    headers, _ = await register_user("uploader6")

    response = await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("virus.exe", b"binary content", "application/octet-stream")},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_upload_over_rate_limit_returns_429(client, register_user, monkeypatch):
    monkeypatch.setattr(get_settings(), "upload_rate_limit_per_day", 2)
    headers, _ = await register_user("uploader7")

    for _ in range(2):
        ok = await client.post(
            "/api/v1/documents",
            headers=headers,
            files={"file": ("notes.txt", b"some perfectly fine content here", "text/plain")},
        )
        assert ok.status_code == 202

    over_limit = await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": ("notes.txt", b"some perfectly fine content here", "text/plain")},
    )
    assert over_limit.status_code == 429
    assert "detail" in over_limit.json()


@pytest.mark.asyncio
async def test_upload_without_auth_returns_401(client):
    response = await client.post(
        "/api/v1/documents",
        files={"file": ("notes.txt", b"content", "text/plain")},
    )
    assert response.status_code == 401
