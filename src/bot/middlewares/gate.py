from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.states import Registration

# Bilingual on purpose: shown before we know the user's language preference.
PROMPT = (
    "Пожалуйста, зарегистрируйтесь: откройте бота в личке (@flott_task_bot) и нажмите /start.\n"
    "Please register first: open the bot in DM (@flott_task_bot) and press /start."
)


class RegistrationGate(BaseMiddleware):
    """Blocks unregistered users from using the bot, prompting them to /start in
    DM first. Lets /start and the registration step itself through."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("user")
        if user is None or user.registered:
            return await handler(event, data)

        if isinstance(event, Message):
            if (event.text or "").startswith("/start"):
                return await handler(event, data)
            state = data.get("state")
            current = await state.get_state() if state else None
            if current == Registration.waiting_full_name.state:
                return await handler(event, data)
            await event.answer(PROMPT)
            return None

        if isinstance(event, CallbackQuery):
            # The language picker is part of registration itself — let it through
            # while the user is choosing a language, even though they're not yet
            # registered. Everything else is blocked until /start completes.
            state = data.get("state")
            current = await state.get_state() if state else None
            if current == Registration.waiting_lang.state and (event.data or "").startswith("lang:"):
                return await handler(event, data)
            await event.answer(PROMPT, show_alert=True)
            return None

        return await handler(event, data)
