from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import OAuthToken
from bot.linear import LinearClient


class WorkspaceNotConnected(RuntimeError):
    """Raised when no Linear workspace has been authorized yet."""


async def get_token(session: AsyncSession) -> OAuthToken:
    """MVP assumes a single connected workspace. Multi-workspace support would
    key this by chat/team binding instead."""
    token = await session.scalar(select(OAuthToken).limit(1))
    if token is None:
        raise WorkspaceNotConnected
    return token


async def get_client(session: AsyncSession) -> LinearClient:
    token = await get_token(session)
    return LinearClient(token.access_token)
