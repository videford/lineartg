"""Project team management: add/remove members of a project. Available to the
project's lead and to admins. Only project team members can be assigned tasks.

The selected project id lives in FSM data (`team_project`) so callbacks stay
within Telegram's 64-byte limit (project ids are UUIDs).
"""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import ProjectLead, User
from bot.keyboards.inline import projects_keyboard
from bot.services.permissions import can_manage_task
from bot.services.projects import (
    add_project_member,
    get_project,
    manageable_projects,
    project_team,
    remove_project_member,
)
from bot.services.users import list_members

router = Router(name="team")


async def cmd_projects(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    """Entry: list projects the user may manage the team of."""
    projects = await manageable_projects(session, user)
    if not projects:
        await message.answer(i18n.get("team-no-projects"))
        return
    await message.answer(
        i18n.get("team-choose-project"),
        reply_markup=projects_keyboard(projects, prefix="tmproj"),
    )


async def _led_ids(session: AsyncSession, project_id: str) -> set[int]:
    return set(
        await session.scalars(
            select(ProjectLead.telegram_id).where(ProjectLead.project_id == project_id)
        )
    )


async def _render_team(
    call: CallbackQuery, session: AsyncSession, project_id: str, i18n: I18nContext
) -> None:
    project = await get_project(session, project_id)
    team = await project_team(session, project_id)
    leads = await _led_ids(session, project_id)

    kb = InlineKeyboardBuilder()
    for u in team:
        if u.telegram_id in leads:
            # Leads are managed via 👑 Назначить лида, not removable here.
            kb.button(text=f"👑 {u.display_name}", callback_data="tmnoop")
        else:
            kb.button(text=f"❌ {u.display_name}", callback_data=f"tmrm:{u.telegram_id}")
    kb.button(text=i18n.get("team-add-btn"), callback_data="tmadd")
    kb.adjust(1)

    names = ", ".join(u.display_name for u in team) or "—"
    text = i18n.get("team-view", project=project.name if project else "—", members=names)
    await call.message.edit_text(text, reply_markup=kb.as_markup())


@router.callback_query(F.data.startswith("tmproj:"))
async def team_project_chosen(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    project_id = call.data.split(":", 1)[1]
    if not await can_manage_task(session, user, project_id):
        await call.answer(i18n.get("err-no-permission"), show_alert=True)
        return
    await state.update_data(team_project=project_id)
    await _render_team(call, session, project_id, i18n)
    await call.answer()


@router.callback_query(F.data == "tmnoop")
async def team_noop(call: CallbackQuery, i18n: I18nContext) -> None:
    await call.answer(i18n.get("team-lead-hint"), show_alert=True)


@router.callback_query(F.data == "tmadd")
async def team_add_list(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    data = await state.get_data()
    project_id = data.get("team_project")
    if not project_id or not await can_manage_task(session, user, project_id):
        await call.answer(i18n.get("err-no-permission"), show_alert=True)
        return
    team_ids = {u.telegram_id for u in await project_team(session, project_id)}
    candidates = [u for u in await list_members(session) if u.telegram_id not in team_ids]
    if not candidates:
        await call.answer(i18n.get("team-no-candidates"), show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    for u in candidates:
        kb.button(text=u.display_name, callback_data=f"tmaddu:{u.telegram_id}")
    kb.button(text=i18n.get("team-back"), callback_data="tmback")
    kb.adjust(1)
    await call.message.edit_text(i18n.get("team-add-choose"), reply_markup=kb.as_markup())
    await call.answer()


@router.callback_query(F.data.startswith("tmaddu:"))
async def team_add_user(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    data = await state.get_data()
    project_id = data.get("team_project")
    if not project_id or not await can_manage_task(session, user, project_id):
        await call.answer(i18n.get("err-no-permission"), show_alert=True)
        return
    tg_id = int(call.data.split(":", 1)[1])
    await add_project_member(session, tg_id, project_id)
    await _render_team(call, session, project_id, i18n)
    await call.answer(i18n.get("team-added"))


@router.callback_query(F.data.startswith("tmrm:"))
async def team_remove_user(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    data = await state.get_data()
    project_id = data.get("team_project")
    if not project_id or not await can_manage_task(session, user, project_id):
        await call.answer(i18n.get("err-no-permission"), show_alert=True)
        return
    tg_id = int(call.data.split(":", 1)[1])
    await remove_project_member(session, tg_id, project_id)
    await _render_team(call, session, project_id, i18n)
    await call.answer(i18n.get("team-removed"))


@router.callback_query(F.data == "tmback")
async def team_back(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    data = await state.get_data()
    project_id = data.get("team_project")
    if project_id:
        await _render_team(call, session, project_id, i18n)
    await call.answer()
