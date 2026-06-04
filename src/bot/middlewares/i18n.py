from __future__ import annotations

from typing import Any

from aiogram.types import TelegramObject
from aiogram_i18n.managers import BaseManager

from bot.config import settings
from bot.db import User

SUPPORTED_LOCALES = ("ru", "uz", "en")


class UserLocaleManager(BaseManager):
    """Resolves the locale from the bot.db.User loaded by DbSessionMiddleware."""

    async def get_locale(self, event_from_user: TelegramObject | None = None, **kwargs: Any) -> str:
        user: User | None = kwargs.get("user")
        if user is not None and user.lang in SUPPORTED_LOCALES:
            return user.lang
        return settings.default_lang

    async def set_locale(self, locale: str, **kwargs: Any) -> None:
        # Persisted explicitly in the /settings handler; nothing to do here.
        return None
