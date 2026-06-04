from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import ChatBinding, Project, ProjectLead, Role, User
from bot.keyboards.inline import members_keyboard, projects_keyboard
from bot.linear.oauth import build_authorize_url
from bot.services import workspace
from bot.services.permissions import Action, can
from bot.services.projects import get_project, list_projects, sync_projects
from bot.services.users import list_members
from bot.states import SetLead

router = Router(name="admin")


@router.message(Command("connect"))
async def cmd_connect(message: Message, user: User, i18n: I18nContext) -> None:
    if not can(user.role, Action.BIND_CHAT):
        await message.answer(i18n.get("err-no-permission"))
        return
    url = build_authorize_url(state=str(user.telegram_id))
    await message.answer(i18n.get("connect-link", url=url), disable_web_page_preview=True)


@router.message(Command("syncprojects"))
async def cmd_syncprojects(
    message: Message, user: User, session: AsyncSession, i18n: I18nContext
) -> None:
    if not can(user.role, Action.BIND_CHAT):
        await message.answer(i18n.get("err-no-permission"))
        return
    try:
        client = await workspace.get_client(session)
    except workspace.WorkspaceNotConnected:
        await message.answer(i18n.get("err-no-workspace"))
        return
    count = await sync_projects(session, client)
    await message.answer(i18n.get("sync-done", count=count))


@router.message(Command("bind"))
async def cmd_bind(
    message: Message, user: User, session: AsyncSession, i18n: I18nContext
) -> None:
    if not can(user.role, Action.BIND_CHAT):
        await message.answer(i18n.get("err-no-permission"))
        return
    binding = await session.get(ChatBinding, message.chat.id)
    if binding is None:
        binding = ChatBinding(telegram_chat_id=message.chat.id, title=message.chat.title)
        session.add(binding)
    else:
        binding.title = message.chat.title
    await session.commit()
    await message.answer(i18n.get("bind-ok"))


@router.message(Command("setrole"))
async def cmd_setrole(
    message: Message,
    user: User,
    session: AsyncSession,
    command: CommandObject,
    i18n: I18nContext,
) -> None:
    if not can(user.role, Action.MANAGE_ROLES):
        await message.answer(i18n.get("err-no-permission"))
        return
    args = (command.args or "").split()
    target_id: int | None = None
    role_str: str | None = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        role_str = args[0] if args else None
    elif len(args) == 2:
        target_id, role_str = int(args[0]), args[1]
    if target_id is None or role_str not in Role.__members__:
        await message.answer(i18n.get("setrole-usage"))
        return
    target = await session.get(User, target_id)
    if target is None:
        await message.answer(i18n.get("err-unknown-member"))
        return
    target.role = Role[role_str]
    await session.commit()
    await message.answer(i18n.get("setrole-ok", name=target.display_name, role=role_str))


# ── project lead management ──────────────────────────────────


@router.message(Command("setlead"))
async def cmd_setlead(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    if not can(user.role, Action.MANAGE_LEADS):
        await message.answer(i18n.get("err-no-permission"))
        return
    projects = await list_projects(session)
    if not projects:
        await message.answer(i18n.get("leads-no-projects"))
        return
    await state.set_state(SetLead.waiting_project)
    await message.answer(
        i18n.get("setlead-choose-project"),
        reply_markup=projects_keyboard(projects, prefix="slproj"),
    )


@router.callback_query(SetLead.waiting_project, F.data.startswith("slproj:"))
async def setlead_project(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    await state.update_data(project_id=call.data.split(":", 1)[1])
    await state.set_state(SetLead.waiting_member)
    members = await list_members(session)
    await call.message.edit_text(
        i18n.get("setlead-choose-member"),
        reply_markup=members_keyboard(members, prefix="slmem"),
    )
    await call.answer()


@router.callback_query(SetLead.waiting_member, F.data.startswith("slmem:"))
async def setlead_member(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    data = await state.get_data()
    project_id = data["project_id"]
    remove = data.get("remove", False)
    tg_id = int(call.data.split(":", 1)[1])
    target = await session.get(User, tg_id)
    project = await get_project(session, project_id)
    if target is None or project is None:
        await call.message.edit_text(i18n.get("err-unknown-member"))
        await state.clear()
        return

    exists = await session.scalar(
        select(ProjectLead).where(
            ProjectLead.telegram_id == tg_id, ProjectLead.project_id == project_id
        )
    )
    if remove:
        if exists is not None:
            await session.delete(exists)
            # Demote global role if no longer leading anything.
            still_lead = await session.scalar(
                select(ProjectLead).where(ProjectLead.telegram_id == tg_id)
            )
            if still_lead is None and target.role == Role.lead:
                target.role = Role.member
            await session.commit()
        await state.clear()
        await call.message.edit_text(
            i18n.get("unsetlead-ok", name=target.display_name, project=project.name)
        )
        await call.answer()
        return

    if exists is None:
        session.add(ProjectLead(telegram_id=tg_id, project_id=project_id))
        if target.role == Role.member:
            target.role = Role.lead
        await session.commit()
    await state.clear()
    await call.message.edit_text(
        i18n.get("setlead-ok", name=target.display_name, project=project.name)
    )
    await call.answer()


@router.message(Command("leads"))
async def cmd_leads(
    message: Message, user: User, session: AsyncSession, i18n: I18nContext
) -> None:
    if not can(user.role, Action.MANAGE_LEADS):
        await message.answer(i18n.get("err-no-permission"))
        return
    rows = await session.execute(
        select(User.display_name, Project.name)
        .join(ProjectLead, ProjectLead.telegram_id == User.telegram_id)
        .join(Project, Project.id == ProjectLead.project_id)
        .order_by(Project.name)
    )
    lines = [f"• {proj}: {name}" for name, proj in rows]
    await message.answer(
        i18n.get("leads-list", body="\n".join(lines)) if lines else i18n.get("leads-empty")
    )


@router.message(Command("unsetlead"))
async def cmd_unsetlead(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    if not can(user.role, Action.MANAGE_LEADS):
        await message.answer(i18n.get("err-no-permission"))
        return
    # Reuse the setlead picker but in removal mode.
    projects = await list_projects(session)
    if not projects:
        await message.answer(i18n.get("leads-no-projects"))
        return
    await state.set_state(SetLead.waiting_project)
    await state.update_data(remove=True)
    await message.answer(
        i18n.get("unsetlead-choose-project"),
        reply_markup=projects_keyboard(projects, prefix="slproj"),
    )
