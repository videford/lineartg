from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser

from bot.db.session import session_factory
from bot.services.users import get_or_create_user


class DbSessionMiddleware(BaseMiddleware):
    """Opens a DB session per update and resolves the acting user.

    Injects into handler data:
      - `session`: AsyncSession
      - `user`: bot.db.User (created on first contact)
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with session_factory() as session:
            data["session"] = session
            tg_user: TgUser | None = data.get("event_from_user")
            if tg_user is not None and not tg_user.is_bot:
                data["user"] = await get_or_create_user(
                    session,
                    telegram_id=tg_user.id,
                    display_name=tg_user.full_name,
                    username=tg_user.username,
                )
            return await handler(event, data)
