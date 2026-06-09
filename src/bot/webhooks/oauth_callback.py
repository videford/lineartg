from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from aiohttp import web

from bot.db import OAuthToken
from bot.db.session import session_factory
from bot.linear import LinearClient
from bot.linear.oauth import exchange_code
from bot.services.projects import sync_projects

log = logging.getLogger(__name__)


async def oauth_callback(request: web.Request) -> web.Response:
    """Linear redirects here after an admin authorizes the actor=app install.
    We store one token per workspace; it is then used for all mutations."""
    code = request.query.get("code")
    error = request.query.get("error")
    if error:
        return web.Response(text=f"Authorization failed: {error}", status=400)
    if not code:
        return web.Response(text="missing code", status=400)

    token_data = await exchange_code(code)
    access_token = token_data["access_token"]
    refresh = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")
    expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        if expires_in
        else None
    )
    # Diagnostics: how long does Linear say this token lasts, and did it give us a
    # refresh token? This tells us whether 401s are expiry (fixable by refresh) or
    # revocation (needs reconnect).
    log.info(
        "Linear token issued: expires_in=%s refresh_token=%s",
        expires_in, bool(refresh),
    )

    # Identify the workspace this token belongs to.
    client = LinearClient(access_token)
    viewer = await client.viewer()
    org = viewer["organization"]

    async with session_factory() as session:
        existing = await session.get(OAuthToken, org["id"])
        if existing:
            existing.access_token = access_token
            existing.scope = token_data.get("scope")
            existing.app_user_id = viewer["viewer"]["id"]
            existing.refresh_token = refresh
            existing.expires_at = expires_at
        else:
            session.add(
                OAuthToken(
                    workspace_id=org["id"],
                    workspace_name=org["name"],
                    access_token=access_token,
                    scope=token_data.get("scope"),
                    app_user_id=viewer["viewer"]["id"],
                    refresh_token=refresh,
                    expires_at=expires_at,
                )
            )
        await session.commit()

        # Pull projects right away so /task and /setlead work immediately.
        try:
            count = await sync_projects(session, client)
        except Exception:  # noqa: BLE001
            count = 0

    return web.Response(
        text=(
            f"✅ Linear workspace '{org['name']}' connected "
            f"({count} projects synced). You can close this tab."
        ),
        content_type="text/plain",
    )
