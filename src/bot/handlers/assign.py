from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import User
from bot.keyboards.inline import projects_keyboard
from bot.services import workspace
from bot.services.permissions import can_create_in
from bot.services.projects import get_project, manageable_projects, project_team
from bot.services.subscriptions import subscribe
from bot.states import AssignTask

router = Router(name="assign")


@router.message(Command("assign"))
async def cmd_assign(
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
        await message.answer(i18n.get("err-no-permission"))
        return
    await state.set_state(AssignTask.waiting_project)
    await message.answer(
        i18n.get("task-choose-project"),
        reply_markup=projects_keyboard(projects, prefix="asproj"),
    )


@router.callback_query(AssignTask.waiting_project, F.data.startswith("asproj:"))
async def assign_project_chosen(
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
    await state.update_data(project_id=project_id)
    team = await project_team(session, project_id)
    await state.set_state(AssignTask.waiting_assignee)
    # Team members + an explicit "no assignee" option (task can wait for an owner).
    kb = InlineKeyboardBuilder()
    for m in team:
        kb.button(text=m.display_name, callback_data=f"asgn:{m.telegram_id}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text=i18n.get("assign-none"), callback_data="asgn:none"))
    await call.message.edit_text(i18n.get("assign-choose-member"), reply_markup=kb.as_markup())
    await call.answer()


@router.callback_query(AssignTask.waiting_assignee, F.data.startswith("asgn:"))
async def assign_member_chosen(
    call: CallbackQuery, state: FSMContext, i18n: I18nContext
) -> None:
    raw = call.data.split(":", 1)[1]
    await state.update_data(assignee_tg_id=None if raw == "none" else int(raw))
    await state.set_state(AssignTask.waiting_title)
    await call.message.edit_text(i18n.get("task-send-title"))
    await call.answer()


@router.message(AssignTask.waiting_title)
async def assign_title_received(
    message: Message,
    user: User,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    i18n: I18nContext,
) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer(i18n.get("task-send-title"))
        return
    data = await state.get_data()
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

    assignee_id = data.get("assignee_tg_id")
    assignee = await session.get(User, assignee_id) if assignee_id else None

    client = await workspace.get_client(session)
    label_ids = None
    if assignee is not None:
        label_ids = [await client.ensure_label(project.team_id, assignee.linear_label)]
    issue = await client.create_issue(
        title=title,
        team_id=project.team_id,
        project_id=project_id,
        label_ids=label_ids,
        actor_name=user.display_name,
        actor_icon=user.avatar_url,
    )
    await state.clear()
    await message.answer(
        i18n.get("task-created", identifier=issue["identifier"], url=issue["url"])
    )

    if assignee is None:
        return  # unassigned task — nobody to subscribe/notify
    await subscribe(session, assignee.telegram_id, issue["id"])
    try:
        await bot.send_message(
            assignee.telegram_id,
            i18n.get(
                "assigned-dm",
                identifier=issue["identifier"],
                title=title,
                by=user.display_name,
                locale=assignee.lang,
            ),
        )
    except Exception:  # noqa: BLE001
        await message.answer(i18n.get("assign-dm-failed", name=assignee.display_name))
