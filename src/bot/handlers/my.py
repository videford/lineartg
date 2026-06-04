from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import User
from bot.keyboards.inline import open_card_button
from bot.services import workspace

router = Router(name="my")


@router.message(Command("my"))
async def cmd_my(
    message: Message, user: User, session: AsyncSession, i18n: I18nContext
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
    if not issues:
        await message.answer(i18n.get("my-empty"))
        return
    for issue in issues:
        text = i18n.get(
            "my-issue-line",
            identifier=issue["identifier"],
            title=issue["title"],
            state=issue["state"]["name"],
            project=(issue.get("project") or {}).get("name", "—"),
        )
        await message.answer(text, reply_markup=open_card_button(issue["id"]))
