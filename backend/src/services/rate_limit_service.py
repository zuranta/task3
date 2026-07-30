"""Per-user rolling-24h rate limiting (FR-012, research.md §8).

Checked and incremented atomically within the same transaction as the
upload/question request it guards, so it can't be bypassed by a caller
racing two requests.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import RateLimitExceededError
from src.models.db import RateLimitCounter, RateLimitCounterType

_WINDOW = timedelta(hours=24)


async def check_and_increment(
    db: AsyncSession, *, user_id: str, counter_type: RateLimitCounterType, limit: int
) -> None:
    now = datetime.now(UTC)
    result = await db.execute(
        select(RateLimitCounter).where(
            RateLimitCounter.user_id == user_id, RateLimitCounter.counter_type == counter_type
        )
    )
    counter = result.scalar_one_or_none()

    if counter is None:
        counter = RateLimitCounter(
            user_id=user_id, counter_type=counter_type, window_start=now, count=0
        )
        db.add(counter)
    else:
        # SQLite drops tzinfo on round-trip even for DateTime(timezone=True)
        # columns; treat a naive value read back from storage as UTC.
        window_start = counter.window_start
        if window_start.tzinfo is None:
            window_start = window_start.replace(tzinfo=UTC)
        if now - window_start >= _WINDOW:
            counter.window_start = now
            counter.count = 0

    if counter.count >= limit:
        reset_at = counter.window_start + _WINDOW
        raise RateLimitExceededError(
            f"Rate limit of {limit} {counter_type.value}s per day exceeded. "
            f"Resets at {reset_at.isoformat()}."
        )

    counter.count += 1
    await db.commit()
