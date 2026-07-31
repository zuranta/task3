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


@pytest.mark.asyncio
async def test_list_own_document_passages_returns_indexed_content(client, register_user):
    headers, _ = await register_user("manager_g")
    document = await _upload(client, headers, "notes.txt", b"some fine document content")

    response = await client.get(f"/api/v1/documents/{document['id']}/passages", headers=headers)

    assert response.status_code == 200
    passages = response.json()
    assert len(passages) > 0
    assert passages[0]["content"]
    assert passages[0]["location_label"]


@pytest.mark.asyncio
async def test_list_other_users_document_passages_returns_404(client, register_user):
    headers_a, _ = await register_user("manager_h")
    headers_b, _ = await register_user("manager_i")
    document = await _upload(client, headers_a)

    response = await client.get(f"/api/v1/documents/{document['id']}/passages", headers=headers_b)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_deleted_documents_passages_returns_404(client, register_user):
    headers, _ = await register_user("manager_j")
    document = await _upload(client, headers)
    await client.delete(f"/api/v1/documents/{document['id']}", headers=headers)

    response = await client.get(f"/api/v1/documents/{document['id']}/passages", headers=headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_nonexistent_document_passages_returns_404(client, register_user):
    headers, _ = await register_user("manager_k")

    response = await client.get("/api/v1/documents/does-not-exist/passages", headers=headers)

    assert response.status_code == 404
