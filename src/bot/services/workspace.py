from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import OAuthToken
from bot.linear import LinearClient
from bot.linear.oauth import refresh_access_token

log = logging.getLogger(__name__)

# Renew this long before the stored expiry, so a request never races the lapse.
REFRESH_MARGIN = timedelta(minutes=10)


class WorkspaceNotConnected(RuntimeError):
    """Raised when no Linear workspace has been authorized yet."""


async def _maybe_refresh(session: AsyncSession, token: OAuthToken) -> None:
    """If the token is expiring and we have a refresh token, renew it in place."""
    if not token.refresh_token or token.expires_at is None:
        return  # long-lived / non-refreshable token — nothing to do
    now = datetime.now(timezone.utc)
    expires_at = token.expires_at
    if expires_at.tzinfo is None:  # stored naive → assume UTC
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at - REFRESH_MARGIN > now:
        return  # still comfortably valid
    try:
        data = await refresh_access_token(token.refresh_token)
    except Exception:  # noqa: BLE001 — keep serving the old token; UI degrades gracefully
        log.warning("Linear token refresh failed", exc_info=True)
        return
    token.access_token = data["access_token"]
    if data.get("refresh_token"):
        token.refresh_token = data["refresh_token"]
    if data.get("expires_in"):
        token.expires_at = now + timedelta(seconds=int(data["expires_in"]))
    await session.commit()
    log.info("Linear access token refreshed (expires_in=%s)", data.get("expires_in"))


async def get_token(session: AsyncSession) -> OAuthToken:
    """MVP assumes a single connected workspace. Prefer the most recently
    refreshed token, and renew it if it's about to expire."""
    token = await session.scalar(
        select(OAuthToken).order_by(OAuthToken.updated_at.desc()).limit(1)
    )
    if token is None:
        raise WorkspaceNotConnected
    await _maybe_refresh(session, token)
    return token


async def get_client(session: AsyncSession) -> LinearClient:
    token = await get_token(session)
    return LinearClient(token.access_token)
