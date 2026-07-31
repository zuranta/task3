"""rate_limit_service's rolling-window reset (FR-012) has no direct coverage
anywhere else -- the integration tests in tests/integration/test_rate_limit.py
only ever exercise a still-open window, never one that's actually expired."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from src.core.errors import RateLimitExceededError
from src.models.db import RateLimitCounter, RateLimitCounterType, User
from src.services import rate_limit_service


async def _make_user(db_session) -> User:
    user = User(email="ratelimitunit@example.com", username="ratelimitunit", password_hash="x")
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_first_request_creates_a_fresh_counter_and_succeeds(db_session):
    user = await _make_user(db_session)

    await rate_limit_service.check_and_increment(
        db_session, user_id=user.id, counter_type=RateLimitCounterType.question, limit=5
    )

    result = await db_session.execute(
        select(RateLimitCounter).where(RateLimitCounter.user_id == user.id)
    )
    counter = result.scalar_one()
    assert counter.count == 1


@pytest.mark.asyncio
async def test_a_request_exactly_at_the_limit_is_rejected(db_session):
    user = await _make_user(db_session)

    for _ in range(3):
        await rate_limit_service.check_and_increment(
            db_session, user_id=user.id, counter_type=RateLimitCounterType.question, limit=3
        )

    with pytest.raises(RateLimitExceededError):
        await rate_limit_service.check_and_increment(
            db_session, user_id=user.id, counter_type=RateLimitCounterType.question, limit=3
        )


@pytest.mark.asyncio
async def test_a_request_after_the_rolling_window_has_elapsed_resets_the_counter(db_session):
    user = await _make_user(db_session)
    stale_counter = RateLimitCounter(
        user_id=user.id,
        counter_type=RateLimitCounterType.question,
        window_start=datetime.now(UTC) - timedelta(hours=25),
        count=999,  # already far over any realistic limit, in the OLD window
    )
    db_session.add(stale_counter)
    await db_session.commit()

    # Should succeed: the 25h-old window has expired, so this starts a new one.
    await rate_limit_service.check_and_increment(
        db_session, user_id=user.id, counter_type=RateLimitCounterType.question, limit=1
    )

    await db_session.refresh(stale_counter)
    assert stale_counter.count == 1


@pytest.mark.asyncio
async def test_a_request_still_within_the_window_does_not_reset_the_counter(db_session):
    user = await _make_user(db_session)
    counter = RateLimitCounter(
        user_id=user.id,
        counter_type=RateLimitCounterType.question,
        window_start=datetime.now(UTC) - timedelta(hours=1),
        count=1,
    )
    db_session.add(counter)
    await db_session.commit()

    with pytest.raises(RateLimitExceededError):
        await rate_limit_service.check_and_increment(
            db_session, user_id=user.id, counter_type=RateLimitCounterType.question, limit=1
        )
