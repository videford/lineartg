from __future__ import annotations

from typing import Any

from aiogram.types import TelegramObject
from aiogram_i18n.managers import BaseManager

from bot.config import settings
from bot.db import User
from bot.db.session import session_factory

SUPPORTED_LOCALES = ("ru", "uz", "en")


class UserLocaleManager(BaseManager):
    """Resolves the locale from the acting user's saved `lang`.

    The i18n middleware may run before the DB middleware has injected `user`,
    so when it's absent we look the language up directly by Telegram id. This is
    what makes en/uz actually stick across messages (not just button labels).
    """

    async def get_locale(
        self, event_from_user: TelegramObject | None = None, **kwargs: Any
    ) -> str:
        user: User | None = kwargs.get("user")
        if user is not None and user.lang in SUPPORTED_LOCALES:
            return user.lang

        tg_user = event_from_user or kwargs.get("event_from_user")
        tg_id = getattr(tg_user, "id", None)
        if tg_id is not None:
            async with session_factory() as session:
                db_user = await session.get(User, tg_id)
                if db_user is not None and db_user.lang in SUPPORTED_LOCALES:
                    return db_user.lang
        return settings.default_lang

    async def set_locale(self, locale: str, **kwargs: Any) -> None:
        # Persisted explicitly in the language handler; nothing to do here.
        return None
