import pytest


@pytest.mark.asyncio
async def test_register_success_returns_token(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "username": "alice", "password": "correcthorse"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "bob@example.com", "username": "bob", "password": "correcthorse"},
    )

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "bob@example.com", "username": "someoneelse", "password": "correcthorse"},
    )

    assert response.status_code == 409
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_register_duplicate_username_returns_409(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "carol@example.com", "username": "carol", "password": "correcthorse"},
    )

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "someoneelse@example.com", "username": "carol", "password": "correcthorse"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password_returns_422(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dave@example.com", "username": "dave", "password": "short"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_invalid_email_returns_422(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "username": "erin", "password": "correcthorse"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_fields_returns_422(client):
    response = await client.post("/api/v1/auth/register", json={"email": "frank@example.com"})

    assert response.status_code == 422
