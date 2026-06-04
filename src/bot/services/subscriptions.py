from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import Subscription


async def is_subscribed(session: AsyncSession, telegram_id: int, issue_id: str) -> bool:
    row = await session.scalar(
        select(Subscription).where(
            Subscription.telegram_id == telegram_id,
            Subscription.linear_issue_id == issue_id,
        )
    )
    return row is not None


async def subscribe(session: AsyncSession, telegram_id: int, issue_id: str) -> bool:
    if await is_subscribed(session, telegram_id, issue_id):
        return False
    session.add(Subscription(telegram_id=telegram_id, linear_issue_id=issue_id))
    await session.commit()
    return True


async def unsubscribe(session: AsyncSession, telegram_id: int, issue_id: str) -> None:
    row = await session.scalar(
        select(Subscription).where(
            Subscription.telegram_id == telegram_id,
            Subscription.linear_issue_id == issue_id,
        )
    )
    if row is not None:
        await session.delete(row)
        await session.commit()


async def subscriber_ids(session: AsyncSession, issue_id: str) -> list[int]:
    return list(
        await session.scalars(
            select(Subscription.telegram_id).where(
                Subscription.linear_issue_id == issue_id
            )
        )
    )


async def subscriptions_of(session: AsyncSession, telegram_id: int) -> list[str]:
    """Linear issue ids a user is subscribed to."""
    return list(
        await session.scalars(
            select(Subscription.linear_issue_id).where(
                Subscription.telegram_id == telegram_id
            )
        )
    )
