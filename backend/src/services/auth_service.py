"""Registration and login (FR-001 through FR-005)."""

import bcrypt
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, UnauthorizedError, ValidationAppError
from src.models.db import User, UserRole


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


async def register_user(db: AsyncSession, *, email: str, username: str, password: str) -> User:
    if len(password) < 8:
        raise ValidationAppError("Password must be at least 8 characters long.")

    existing = await db.execute(
        select(User).where(or_(User.email == email, User.username == username))
    )
    conflict = existing.scalar_one_or_none()
    if conflict is not None:
        field = "email" if conflict.email == email else "username"
        raise ConflictError(f"An account with that {field} already exists.")

    user = User(
        email=email,
        username=username,
        password_hash=hash_password(password),
        role=UserRole.user,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        # DB-level unique constraint is the ultimate guard against a registration
        # race the pre-check above can't catch (research.md, Authentication &
        # authorization decision).
        await db.rollback()
        raise ConflictError("An account with that email or username already exists.") from None

    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, *, identifier: str, password: str) -> User:
    result = await db.execute(
        select(User).where(or_(User.email == identifier, User.username == identifier))
    )
    user = result.scalar_one_or_none()

    # Single generic message regardless of which part was wrong (FR-004): prevents
    # user enumeration via distinguishable error responses.
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid credentials.")

    return user
