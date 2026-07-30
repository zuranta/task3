import pytest


async def _upload(client, headers, filename="notes.txt", content=b"some fine document content"):
    response = await client.post(
        "/api/v1/documents",
        headers=headers,
        files={"file": (filename, content, "text/plain")},
    )
    assert response.status_code == 202
    return response.json()


@pytest.mark.asyncio
async def test_list_documents_returns_only_own_documents(client, register_user):
    headers_a, _ = await register_user("manager_a")
    headers_b, _ = await register_user("manager_b")

    await _upload(client, headers_a, "a.txt", b"user A's private content")

    response_a = await client.get("/api/v1/documents", headers=headers_a)
    response_b = await client.get("/api/v1/documents", headers=headers_b)

    assert response_a.status_code == 200
    assert len(response_a.json()) == 1
    assert response_b.status_code == 200
    assert response_b.json() == []


@pytest.mark.asyncio
async def test_delete_own_document_returns_204(client, register_user):
    headers, _ = await register_user("manager_c")
    document = await _upload(client, headers)

    response = await client.delete(f"/api/v1/documents/{document['id']}", headers=headers)

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_other_users_document_returns_404(client, register_user):
    headers_a, _ = await register_user("manager_d")
    headers_b, _ = await register_user("manager_e")
    document = await _upload(client, headers_a)

    response = await client.delete(f"/api/v1/documents/{document['id']}", headers=headers_b)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_document_returns_404(client, register_user):
    headers, _ = await register_user("manager_f")

    response = await client.delete("/api/v1/documents/does-not-exist", headers=headers)

    assert response.status_code == 404
