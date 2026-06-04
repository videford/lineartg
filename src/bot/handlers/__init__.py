from aiogram import Router

from bot.handlers import admin, assign, card, menu, my, start, team


def build_router() -> Router:
    root = Router(name="root")
    root.include_router(start.router)
    root.include_router(admin.router)
    root.include_router(assign.router)
    root.include_router(card.router)
    root.include_router(team.router)
    root.include_router(my.router)
    root.include_router(menu.router)
    return root


__all__ = ["build_router"]
