from __future__ import annotations

from urllib.parse import urlencode

import httpx

from bot.config import settings

AUTHORIZE_URL = "https://linear.app/oauth/authorize"
TOKEN_URL = "https://api.linear.app/oauth/token"

# Scopes we need: read data, write issues/comments. `app:assignable` /
# `app:mentionable` enable richer agent behaviour but are optional for MVP.
SCOPES = "read,write,issues:create,comments:create"


def build_authorize_url(state: str) -> str:
    """Authorization URL with actor=app so all mutations are performed by the
    application (no Linear seat consumed) rather than by an end user."""
    params = {
        "client_id": settings.linear_client_id,
        "redirect_uri": settings.redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
        "actor": "app",
        "prompt": "consent",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> dict:
    """Exchange an authorization code for an access token."""
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.linear_client_id,
                "client_secret": settings.linear_client_secret,
                "redirect_uri": settings.redirect_uri,
                "code": code,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Exchange a refresh token for a fresh access token (when Linear issues
    expiring tokens). Returns the token payload (access_token, maybe a new
    refresh_token and expires_in)."""
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.linear_client_id,
                "client_secret": settings.linear_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()
