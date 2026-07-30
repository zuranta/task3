import pytest

from src.core.errors import ValidationAppError
from src.services.auth_service import hash_password, register_user, verify_password


def test_hash_password_does_not_return_plaintext():
    hashed = hash_password("correcthorse")

    assert hashed != "correcthorse"
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


def test_verify_password_accepts_correct_password():
    hashed = hash_password("correcthorse")

    assert verify_password("correcthorse", hashed) is True


def test_verify_password_rejects_incorrect_password():
    hashed = hash_password("correcthorse")

    assert verify_password("wrong-password", hashed) is False


@pytest.mark.asyncio
async def test_register_user_rejects_password_shorter_than_8_chars(db_session):
    with pytest.raises(ValidationAppError):
        await register_user(db_session, email="ivan@example.com", username="ivan", password="short")
