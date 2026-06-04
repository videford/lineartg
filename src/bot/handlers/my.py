from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import User
from bot.handlers import tasklist
from bot.services import workspace

router = Router(name="my")


@router.message(Command("my"))
async def cmd_my(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    if not user.linear_label:
        await message.answer(i18n.get("my-no-label"))
        return
    try:
        client = await workspace.get_client(session)
    except workspace.WorkspaceNotConnected:
        await message.answer(i18n.get("err-no-workspace"))
        return

    issues = await client.issues_by_label(user.linear_label)
    await tasklist.show_list(
        message, state=state, i18n=i18n, title=i18n.get("my-title"), issues=issues
    )
