from aiogram import Router

from bot.handlers import (
    admin,
    assign,
    browse,
    card,
    menu,
    my,
    people,
    start,
    tasklist,
    team,
)


def build_router() -> Router:
    root = Router(name="root")
    root.include_router(start.router)
    root.include_router(admin.router)
    root.include_router(assign.router)
    root.include_router(card.router)
    root.include_router(team.router)
    root.include_router(tasklist.router)
    root.include_router(browse.router)
    root.include_router(people.router)
    root.include_router(my.router)
    root.include_router(menu.router)
    return root


__all__ = ["build_router"]
