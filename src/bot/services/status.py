from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import Role, User
from bot.services.projects import led_projects


async def describe_status(session: AsyncSession, user: User, i18n) -> str:
    """Human-readable role/project status, e.g. 'Администратор',
    'Лид проектов: A, B' or 'Участник'. `i18n` is any object with .get()."""
    if user.role == Role.admin:
        return i18n.get("status-admin")
    if user.role == Role.guest:
        return i18n.get("status-guest")
    led = await led_projects(session, user.telegram_id)
    if led:
        return i18n.get("status-lead", projects=", ".join(p.name for p in led))
    return i18n.get("status-member")
