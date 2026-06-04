from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.db import Role, User


OWNER_PREFIX = "tg:"


def slug_label(display_name: str, telegram_id: int) -> str:
    """Build the stable assignee label, e.g. 'tg:ivan-petrov'. Falls back to the
    Telegram id when the name has no usable latin/cyrillic characters."""
    base = re.sub(r"\s+", "-", display_name.strip().lower())
    base = re.sub(r"[^\w\-]", "", base, flags=re.UNICODE)
    base = base.strip("-")
    return f"{OWNER_PREFIX}{base or telegram_id}"


async def get_or_create_user(
    session: AsyncSession,
    *,
    telegram_id: int,
    display_name: str,
    username: str | None = None,
) -> User:
    user = await session.get(User, telegram_id)
    if user is None:
        role = Role.admin if telegram_id in settings.admin_ids else Role.member
        user = User(
            telegram_id=telegram_id,
            display_name=display_name,
            username=username,
            lang=settings.default_lang,
            role=role,
            linear_label=slug_label(display_name, telegram_id),
        )
        session.add(user)
        await session.commit()
        return user

    # Auto-heal: bootstrap admins are always admin (can't accidentally lose it).
    changed = False
    if telegram_id in settings.admin_ids and user.role != Role.admin:
        user.role = Role.admin
        changed = True
    # Keep the Telegram @username fresh for profile deep-links.
    if username and user.username != username:
        user.username = username
        changed = True
    if changed:
        await session.commit()
    return user


async def list_members(session: AsyncSession) -> list[User]:
    result = await session.scalars(
        select(User).where(User.is_active.is_(True)).order_by(User.display_name)
    )
    return list(result)
