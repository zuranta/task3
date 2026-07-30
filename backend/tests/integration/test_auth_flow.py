import pytest

from src.core.security import decode_access_token


@pytest.mark.asyncio
async def test_register_then_login_with_email_and_username(client):
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "grace@example.com", "username": "grace", "password": "correcthorse"},
    )
    assert register_response.status_code == 201
    registered_user_id = decode_access_token(register_response.json()["access_token"])["sub"]

    # "Log out" is purely client-side for a stateless JWT -- simulate it by simply
    # discarding the token and authenticating again from scratch.

    login_with_email = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "grace@example.com", "password": "correcthorse"},
    )
    assert login_with_email.status_code == 200
    assert decode_access_token(login_with_email.json()["access_token"])["sub"] == registered_user_id

    login_with_username = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "grace", "password": "correcthorse"},
    )
    assert login_with_username.status_code == 200
    assert (
        decode_access_token(login_with_username.json()["access_token"])["sub"] == registered_user_id
    )


@pytest.mark.asyncio
async def test_login_with_incorrect_password_is_rejected(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "heidi@example.com", "username": "heidi", "password": "correcthorse"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "heidi", "password": "not-the-password"},
    )

    assert response.status_code == 401
