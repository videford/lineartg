"""Test-mode entrypoint using long polling — no public HTTPS / tunnel needed.

Use this to verify the bot works at all (commands, DB, i18n, roles, and — once a
Linear token is seeded — task creation). Linear *webhooks* (status/comment
notifications pushed back into Telegram) require the webhook server in
`bot.main` and a public URL; everything else works under polling.
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram_i18n.cores import FluentRuntimeCore

from bot.config import settings
from bot.main import LOCALES_PATH, build_dispatcher


async def _run() -> None:
    logging.basicConfig(level=settings.log_level)
    bot = Bot(
        settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    i18n_core = FluentRuntimeCore(path=str(LOCALES_PATH))
    dp = build_dispatcher(i18n_core)

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Starting polling… open Telegram and send /start")
    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
