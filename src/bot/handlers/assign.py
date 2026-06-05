from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import User
from bot.handlers import draft as draft_h

router = Router(name="assign")


@router.message(Command("assign"))
async def cmd_assign(
    message: Message,
    user: User,
    session: AsyncSession,
    state: FSMContext,
    i18n: I18nContext,
) -> None:
    # Assignment is now part of the draft preview (set the assignee there before
    # publishing), so /assign just opens the same review-before-publish flow.
    await draft_h.start_draft(message, user, session, state, i18n)
