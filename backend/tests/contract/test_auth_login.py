import pytest


async def _register(client, email="alice@example.com", username="alice", password="correcthorse"):
    return await client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )


@pytest.mark.asyncio
async def test_login_with_email_succeeds(client):
    await _register(client)

    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "alice@example.com", "password": "correcthorse"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


@pytest.mark.asyncio
async def test_login_with_username_succeeds(client):
    await _register(client)

    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "alice", "password": "correcthorse"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_generic_401(client):
    await _register(client)

    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "alice", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_with_unrecognized_identifier_returns_same_generic_401(client):
    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "nobody-registered", "password": "whatever"},
    )

    assert response.status_code == 401
    assert "credentials" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_failure_messages_are_identical_regardless_of_which_field_was_wrong(client):
    await _register(client)

    wrong_password = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "alice", "password": "wrong-password"},
    )
    unknown_identifier = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "nobody-registered", "password": "whatever"},
    )

    assert wrong_password.json()["detail"] == unknown_identifier.json()["detail"]
