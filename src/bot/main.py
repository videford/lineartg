from __future__ import annotations

import logging
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore
from aiohttp import web

from bot.config import settings
from bot.handlers import build_router
from bot.middlewares import DbSessionMiddleware, RegistrationGate, UserLocaleManager
from bot.webhooks import feedback_report, linear_webhook, oauth_callback

LOCALES_PATH = Path(__file__).resolve().parents[1] / "locales" / "{locale}"


def build_dispatcher(i18n_core: FluentRuntimeCore) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    # DB session + user must run before i18n so the locale manager sees `user`.
    db_mw = DbSessionMiddleware()
    dp.message.middleware(db_mw)
    dp.callback_query.middleware(db_mw)

    # Registration gate runs after the user is loaded.
    gate = RegistrationGate()
    dp.message.middleware(gate)
    dp.callback_query.middleware(gate)

    I18nMiddleware(
        core=i18n_core,
        manager=UserLocaleManager(),
        default_locale=settings.default_lang,
    ).setup(dispatcher=dp)

    dp.include_router(build_router())
    return dp


async def set_commands(bot: Bot) -> None:
    """Populate Telegram's command menu (the blue ☰ button)."""
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Старт / Start"),
            BotCommand(command="menu", description="Меню / Menu"),
            BotCommand(command="board", description="Дашборд команды / Team board"),
        ]
    )


async def on_startup(bot: Bot) -> None:
    await set_commands(bot)
    # Don't crash the service if the public URL isn't ready yet (e.g. domain
    # not generated on the very first deploy) — log and let a redeploy fix it.
    try:
        await bot.set_webhook(
            settings.telegram_webhook_url,
            secret_token=settings.telegram_webhook_secret,
            drop_pending_updates=True,
        )
        logging.info("Telegram webhook set to %s", settings.telegram_webhook_url)
    except Exception as exc:  # noqa: BLE001
        logging.warning(
            "Could not set Telegram webhook to %s: %s. "
            "Set PUBLIC_BASE_URL / generate a domain and redeploy.",
            settings.telegram_webhook_url,
            exc,
        )


def create_app() -> web.Application:
    logging.basicConfig(level=settings.log_level)

    bot = Bot(
        settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    i18n_core = FluentRuntimeCore(path=str(LOCALES_PATH))
    dp = build_dispatcher(i18n_core)
    dp.startup.register(on_startup)

    # 20 MB body cap so base64 screenshots in /report aren't rejected (413).
    app = web.Application(client_max_size=20 * 1024 * 1024)
    app["bot"] = bot
    app["i18n_core"] = i18n_core

    # Telegram updates
    SimpleRequestHandler(
        dispatcher=dp, bot=bot, secret_token=settings.telegram_webhook_secret
    ).register(app, path=settings.telegram_webhook_path)
    setup_application(app, dp, bot=bot)

    # Linear integration endpoints
    app.router.add_post("/linear/webhook", linear_webhook)
    app.router.add_get("/linear/oauth/callback", oauth_callback)
    app.router.add_get("/healthz", lambda _: web.Response(text="ok"))
    # Website feedback → Linear task
    app.router.add_post("/report", feedback_report)

    return app


def main() -> None:
    app = create_app()
    web.run_app(app, host=settings.web_host, port=settings.bind_port)


if __name__ == "__main__":
    main()
