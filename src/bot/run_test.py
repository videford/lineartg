"""Test-mode runner: Telegram long polling + a small web server for Linear's
OAuth callback and webhooks.

Why both: actor=app OAuth and Linear webhooks need a public HTTPS endpoint,
but Telegram can stay on polling (no public URL needed for Telegram itself).
Expose this process's WEB_PORT via one tunnel (cloudflared/ngrok) and set
PUBLIC_BASE_URL / LINEAR_REDIRECT_URI to that URL.

Run with PYTHONPATH=src:  python -m bot.run_test
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram_i18n.cores import FluentRuntimeCore
from aiohttp import web

from bot.config import settings
from bot.main import LOCALES_PATH, build_dispatcher, set_commands
from bot.webhooks import feedback_report, linear_webhook, oauth_callback


async def _run() -> None:
    logging.basicConfig(level=settings.log_level)
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    i18n_core = FluentRuntimeCore(path=str(LOCALES_PATH))
    dp = build_dispatcher(i18n_core)

    # Web server for Linear OAuth callback + webhooks.
    app = web.Application(client_max_size=20 * 1024 * 1024)
    app["bot"] = bot
    app["i18n_core"] = i18n_core
    app.router.add_post("/linear/webhook", linear_webhook)
    app.router.add_get("/linear/oauth/callback", oauth_callback)
    app.router.add_get("/healthz", lambda _: web.Response(text="ok"))
    app.router.add_post("/report", feedback_report)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.web_host, settings.bind_port)
    await site.start()
    logging.info(
        "Web server on %s:%s  (expose via tunnel -> %s)",
        settings.web_host,
        settings.bind_port,
        settings.base_url,
    )

    await bot.delete_webhook(drop_pending_updates=True)
    await set_commands(bot)
    logging.info("Starting polling… send /start in Telegram")
    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
