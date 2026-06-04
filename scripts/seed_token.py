"""Seed a Linear token without the full OAuth round-trip — for TEST mode only.

For a quick connectivity test you can use a Linear *personal API key*
(Settings → Security & access → Personal API keys) instead of setting up an
OAuth application + public callback. Paste it here:

    python scripts/seed_token.py lin_api_xxx

Caveat: a personal API key acts as YOUR Linear user (it consumes your seat and
`createAsUser` attribution is ignored). It only proves the GraphQL plumbing
works. For real seat-less operation you still need the actor=app OAuth flow
(/connect). Run with PYTHONPATH=src.
"""
from __future__ import annotations

import asyncio
import sys

from bot.db import OAuthToken
from bot.db.session import session_factory
from bot.linear import LinearClient


async def main(token: str) -> None:
    client = LinearClient(token)
    data = await client.viewer()
    org = data["organization"]
    print(f"Connected as workspace: {org['name']} ({org['id']})")

    async with session_factory() as session:
        existing = await session.get(OAuthToken, org["id"])
        if existing:
            existing.access_token = token
        else:
            session.add(
                OAuthToken(
                    workspace_id=org["id"],
                    workspace_name=org["name"],
                    access_token=token,
                    app_user_id=data["viewer"]["id"],
                )
            )
        await session.commit()
    print("Token seeded. You can now use /task, /my, /assign in the bot.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python scripts/seed_token.py <LINEAR_TOKEN>")
        raise SystemExit(1)
    asyncio.run(main(sys.argv[1]))
