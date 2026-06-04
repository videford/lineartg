from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import IssueLink, User
from bot.keyboards.inline import projects_keyboard
from bot.services import workspace
from bot.services.permissions import can_create_in
from bot.services.projects import get_project, manageable_projects
from bot.states import CreateTask

router = Router(name="tasks")


@router.message(Command("task"))
async def cmd_task(
    message: Message,
    user: User,
    session: AsyncSession,
    state: FSMContext,
    i18n: I18nContext,
) -> None:
    try:
        await workspace.get_token(session)
    except workspace.WorkspaceNotConnected:
        await message.answer(i18n.get("err-no-workspace"))
        return

    projects = await manageable_projects(session, user)
    if not projects:
        # No projects to manage -> not a lead/admin, or cache empty.
        await message.answer(i18n.get("err-no-permission"))
        return

    seed = message.reply_to_message.text if message.reply_to_message else None
    await state.set_state(CreateTask.waiting_project)
    await state.update_data(seed_title=seed, source_chat=message.chat.id)
    await message.answer(
        i18n.get("task-choose-project"),
        reply_markup=projects_keyboard(projects, prefix="ctproj"),
    )


@router.callback_query(CreateTask.waiting_project, F.data.startswith("ctproj:"))
async def task_project_chosen(
    call: CallbackQuery,
    user: User,
    session: AsyncSession,
    state: FSMContext,
    i18n: I18nContext,
) -> None:
    project_id = call.data.split(":", 1)[1]
    if not await can_create_in(session, user, project_id):
        await call.answer(i18n.get("err-no-permission"), show_alert=True)
        return
    data = await state.get_data()
    await state.update_data(project_id=project_id)
    await state.set_state(CreateTask.waiting_title)
    msg = "task-send-title-seeded" if data.get("seed_title") else "task-send-title"
    await call.message.edit_text(i18n.get(msg))
    await call.answer()


@router.message(CreateTask.waiting_title)
async def task_title_received(
    message: Message,
    user: User,
    session: AsyncSession,
    state: FSMContext,
    i18n: I18nContext,
) -> None:
    data = await state.get_data()
    title = (message.text or data.get("seed_title") or "").strip()
    if not title:
        await message.answer(i18n.get("task-send-title"))
        return

    project_id = data["project_id"]
    if not await can_create_in(session, user, project_id):
        await message.answer(i18n.get("err-no-permission"))
        await state.clear()
        return

    project = await get_project(session, project_id)
    if project is None or not project.team_id:
        await message.answer(i18n.get("err-no-projects"))
        await state.clear()
        return

    client = await workspace.get_client(session)
    issue = await client.create_issue(
        title=title,
        team_id=project.team_id,
        project_id=project_id,
        actor_name=user.display_name,
        actor_icon=user.avatar_url,
    )

    sent = await message.answer(
        i18n.get("task-created", identifier=issue["identifier"], url=issue["url"])
    )
    session.add(
        IssueLink(
            linear_issue_id=issue["id"],
            linear_issue_identifier=issue["identifier"],
            telegram_chat_id=message.chat.id,
            telegram_message_id=sent.message_id,
        )
    )
    await session.commit()
    await state.clear()
