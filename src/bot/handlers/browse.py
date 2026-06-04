"""Browse all tasks by project — available to everyone. Any user can open a
card, read it, comment and subscribe (edit/status/assign stay manager-only).
"""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.fsm.context import FSMContext

from bot.db import User
from bot.handlers import tasklist
from bot.keyboards.inline import projects_keyboard
from bot.services import workspace
from bot.services.projects import get_project, list_projects

router = Router(name="browse")


async def cmd_browse(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    try:
        await workspace.get_token(session)
    except workspace.WorkspaceNotConnected:
        await message.answer(i18n.get("err-no-workspace"))
        return
    projects = await list_projects(session)
    if not projects:
        await message.answer(i18n.get("browse-no-projects"))
        return
    await message.answer(
        i18n.get("browse-choose-project"),
        reply_markup=projects_keyboard(projects, prefix="brproj"),
    )


@router.callback_query(F.data.startswith("brproj:"))
async def browse_project(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    project_id = call.data.split(":", 1)[1]
    client = await workspace.get_client(session)
    issues = await client.issues_by_project(project_id)
    project = await get_project(session, project_id)
    title = project.name if project else i18n.get("menu-browse")
    await tasklist.show_list(call.message, state=state, i18n=i18n, title=title, issues=issues)
    await call.answer()
