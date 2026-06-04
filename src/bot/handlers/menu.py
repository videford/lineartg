"""Button-driven UI: a persistent reply-keyboard main menu plus inline
submenus. Menu buttons are matched by their leading emoji so routing is
language-independent. Most buttons delegate to the existing command handlers.
"""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import User
from bot.handlers import admin as admin_h
from bot.handlers import assign as assign_h
from bot.handlers import my as my_h
from bot.handlers import tasks as tasks_h
from bot.keyboards.inline import open_card_button
from bot.keyboards.menu import (
    EMOJI_ADMIN,
    EMOJI_ASSIGN,
    EMOJI_CREATE,
    EMOJI_HELP,
    EMOJI_MY,
    EMOJI_SEARCH,
    EMOJI_SETTINGS,
    admin_menu,
    main_menu,
    settings_menu,
)
from bot.keyboards.inline import lang_keyboard
from bot.services import workspace
from bot.services.permissions import Action, can
from bot.services.projects import sync_projects
from bot.services.users import list_members  # noqa: F401  (kept for parity)
from bot.states import Search

router = Router(name="menu")
log = logging.getLogger(__name__)


async def show_menu(message: Message, user: User, session: AsyncSession, i18n: I18nContext) -> None:
    if message.chat.type != "private":
        # Reply keyboards are per-chat and noisy in groups — keep menu in DM.
        await message.answer(i18n.get("menu-group-hint"))
        return
    from bot.services.permissions import Action as _A  # local to avoid cycle noise

    is_admin = can(user.role, _A.MANAGE_LEADS)
    from bot.services.permissions import is_any_lead

    is_lead = await is_any_lead(session, user.telegram_id)
    await message.answer(
        i18n.get("menu-title"),
        reply_markup=main_menu(i18n, is_admin=is_admin, is_lead=is_lead),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, user: User, session: AsyncSession, i18n: I18nContext) -> None:
    await show_menu(message, user, session, i18n)


# ── top-level buttons (only when not mid-flow) ───────────────


@router.message(StateFilter(None), F.text.startswith(EMOJI_MY))
async def btn_my(message: Message, user: User, session: AsyncSession, i18n: I18nContext) -> None:
    await my_h.cmd_my(message, user, session, i18n)


@router.message(StateFilter(None), F.text.startswith(EMOJI_CREATE))
async def btn_create(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    await tasks_h.cmd_task(message, user, session, state, i18n)


@router.message(StateFilter(None), F.text.startswith(EMOJI_ASSIGN))
async def btn_assign(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    await assign_h.cmd_assign(message, user, session, state, i18n)


@router.message(StateFilter(None), F.text.startswith(EMOJI_SEARCH))
async def btn_search(message: Message, state: FSMContext, i18n: I18nContext) -> None:
    await state.set_state(Search.waiting_query)
    await message.answer(i18n.get("search-prompt"))


@router.message(StateFilter(None), F.text.startswith(EMOJI_SETTINGS))
async def btn_settings(message: Message, i18n: I18nContext) -> None:
    await message.answer(i18n.get("settings-title"), reply_markup=settings_menu(i18n))


@router.message(StateFilter(None), F.text.startswith(EMOJI_HELP))
async def btn_help(message: Message, user: User, i18n: I18nContext) -> None:
    await message.answer(i18n.get("help-body", role=user.role.value))


@router.message(StateFilter(None), F.text.startswith(EMOJI_ADMIN))
async def btn_admin(message: Message, user: User, i18n: I18nContext) -> None:
    if not can(user.role, Action.MANAGE_LEADS):
        await message.answer(i18n.get("err-no-permission"))
        return
    await message.answer(i18n.get("admin-title"), reply_markup=admin_menu(i18n))


# ── search flow ──────────────────────────────────────────────


@router.message(Search.waiting_query)
async def search_received(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    await state.clear()
    term = (message.text or "").strip()
    if not term:
        await message.answer(i18n.get("search-prompt"))
        return
    try:
        client = await workspace.get_client(session)
    except workspace.WorkspaceNotConnected:
        await message.answer(i18n.get("err-no-workspace"))
        return
    results = await client.search_issues(term)
    if not results:
        await message.answer(i18n.get("search-empty"))
        return
    for issue in results:
        text = i18n.get(
            "my-issue-line",
            identifier=issue["identifier"],
            title=issue["title"],
            state=issue["state"]["name"],
            project=(issue.get("project") or {}).get("name", "—"),
        )
        await message.answer(text, reply_markup=open_card_button(issue["id"]))


# ── settings submenu ─────────────────────────────────────────


@router.callback_query(F.data == "set:lang")
async def set_lang_menu(call: CallbackQuery, i18n: I18nContext) -> None:
    await call.message.answer(i18n.get("start-choose-lang"), reply_markup=lang_keyboard())
    await call.answer()


@router.callback_query(F.data == "set:profile")
async def set_profile(call: CallbackQuery, user: User, i18n: I18nContext) -> None:
    await call.message.answer(
        i18n.get("whoami", name=user.display_name, role=user.role.value)
    )
    await call.answer()


# ── admin submenu (delegate to command handlers) ─────────────


@router.callback_query(F.data == "adm:connect")
async def adm_connect(call: CallbackQuery, user: User, i18n: I18nContext) -> None:
    await admin_h.cmd_connect(call.message, user, i18n)
    await call.answer()


@router.callback_query(F.data == "adm:sync")
async def adm_sync(call: CallbackQuery, user: User, session: AsyncSession, i18n: I18nContext) -> None:
    if not can(user.role, Action.BIND_CHAT):
        await call.answer(i18n.get("err-no-permission"), show_alert=True)
        return
    try:
        client = await workspace.get_client(session)
    except workspace.WorkspaceNotConnected:
        await call.message.answer(i18n.get("err-no-workspace"))
        await call.answer()
        return
    count = await sync_projects(session, client)
    await call.message.answer(i18n.get("sync-done", count=count))
    await call.answer()


@router.callback_query(F.data == "adm:setlead")
async def adm_setlead(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    await admin_h.cmd_setlead(call.message, user, session, state, i18n)
    await call.answer()


@router.callback_query(F.data == "adm:leads")
async def adm_leads(call: CallbackQuery, user: User, session: AsyncSession, i18n: I18nContext) -> None:
    await admin_h.cmd_leads(call.message, user, session, i18n)
    await call.answer()


# ── fallbacks (registered LAST so specific handlers win) ─────


@router.message(StateFilter(None))
async def fallback_message(
    message: Message, user: User, session: AsyncSession, i18n: I18nContext
) -> None:
    """Any idle message that matched nothing — guide the user to the menu so the
    bot always responds instead of silently dropping the update."""
    log.info("fallback: unhandled idle message from %s: %r", user.telegram_id, message.text)
    if message.chat.type != "private":
        return  # stay quiet in groups to avoid noise
    await show_menu(message, user, session, i18n)


@router.callback_query()
async def fallback_callback(call: CallbackQuery, i18n: I18nContext) -> None:
    """Acknowledge any stale/unknown callback so the button stops spinning."""
    log.info("fallback: unhandled callback %r", call.data)
    await call.answer()
