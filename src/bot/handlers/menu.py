"""Button-driven UI: a persistent reply-keyboard main menu plus inline
submenus. Menu buttons are matched by their leading emoji so routing is
language-independent. Most buttons delegate to the existing command handlers.
"""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import User
from bot.handlers import admin as admin_h
from bot.handlers import assign as assign_h
from bot.handlers import browse as browse_h
from bot.handlers import my as my_h
from bot.handlers import team as team_h
from bot.keyboards.inline import open_card_button
from bot.keyboards.menu import (
    EMOJI_ADMIN,
    EMOJI_BROWSE,
    EMOJI_CREATE,
    EMOJI_MY,
    EMOJI_PROJECTS,
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
from bot.services.status import describe_status
from bot.services.users import slug_label
from bot.states import Profile, Search

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
async def cmd_menu(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    await state.clear()  # /menu also escapes any half-finished flow
    await show_menu(message, user, session, i18n)


# ── top-level buttons ────────────────────────────────────────
# No state filter: menu buttons work anytime and reset any half-finished flow
# (a stuck FSM state must never lock the user out). Active text-input flows
# live in earlier routers, so legitimate input is still caught there first.


@router.message(F.text.startswith(EMOJI_MY))
async def btn_my(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    await state.clear()
    await my_h.cmd_my(message, user, session, i18n)


@router.message(F.text.startswith(EMOJI_CREATE))
async def btn_create(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    # Creating a task always goes through assignment — no orphan tasks.
    await state.clear()
    await assign_h.cmd_assign(message, user, session, state, i18n)


@router.message(F.text.startswith(EMOJI_BROWSE))
async def btn_browse(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    await state.clear()
    await browse_h.cmd_browse(message, user, session, state, i18n)


@router.message(F.text.startswith(EMOJI_SEARCH))
async def btn_search(message: Message, state: FSMContext, i18n: I18nContext) -> None:
    await state.clear()
    await state.set_state(Search.waiting_query)
    await message.answer(i18n.get("search-prompt"))


@router.message(F.text.startswith(EMOJI_PROJECTS))
async def btn_projects(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    await state.clear()
    await team_h.cmd_projects(message, user, session, state, i18n)


@router.message(F.text.startswith(EMOJI_SETTINGS))
async def btn_settings(message: Message, state: FSMContext, i18n: I18nContext) -> None:
    await state.clear()
    await message.answer(i18n.get("settings-title"), reply_markup=settings_menu(i18n))


@router.message(F.text.startswith(EMOJI_ADMIN))
async def btn_admin(message: Message, user: User, state: FSMContext, i18n: I18nContext) -> None:
    await state.clear()
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
    await call.message.edit_text(
        i18n.get("start-choose-lang"), reply_markup=lang_keyboard(with_back=True)
    )
    await call.answer()


@router.callback_query(F.data == "set:profile")
async def set_profile(
    call: CallbackQuery, user: User, session: AsyncSession, i18n: I18nContext
) -> None:
    status = await describe_status(session, user, i18n)
    kb = InlineKeyboardBuilder()
    kb.button(text=i18n.get("profile-change-name"), callback_data="set:name")
    kb.button(text=i18n.get("nav-back"), callback_data="nav:settings")
    kb.adjust(1)
    await call.message.edit_text(
        i18n.get("profile-card", name=user.display_name, status=status),
        reply_markup=kb.as_markup(),
    )
    await call.answer()


@router.callback_query(F.data == "nav:settings")
async def nav_settings(call: CallbackQuery, i18n: I18nContext) -> None:
    await call.message.edit_text(i18n.get("settings-title"), reply_markup=settings_menu(i18n))
    await call.answer()


@router.callback_query(F.data == "nav:close")
async def nav_close(call: CallbackQuery) -> None:
    try:
        await call.message.delete()
    except Exception:  # noqa: BLE001
        await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()


@router.callback_query(F.data == "set:name")
async def set_name_start(call: CallbackQuery, state: FSMContext, i18n: I18nContext) -> None:
    await state.set_state(Profile.waiting_name)
    await call.message.answer(i18n.get("profile-send-name"))
    await call.answer()


@router.message(Profile.waiting_name)
async def set_name_received(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    raw = (message.text or "").strip()
    if len(raw.split()) < 2 or len(raw) > 100:
        await message.answer(i18n.get("reg-name-invalid"))
        return
    # Keep linear_label fixed: it is the stable owner marker on existing tasks.
    # Changing it would orphan all previously assigned issues from /my.
    if not user.linear_label:
        user.linear_label = slug_label(raw, user.telegram_id)
    user.display_name = raw
    await session.commit()
    await state.clear()
    await message.answer(i18n.get("profile-name-updated", name=raw))


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


@router.message()
async def fallback_message(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    """Last-resort handler: any message not caught by a command, a menu button,
    or an active text-input flow (those live in earlier routers). Resets a
    possibly-stuck flow and shows the menu so the bot always responds."""
    log.info("fallback: unhandled message from %s: %r", user.telegram_id, message.text)
    if message.chat.type != "private":
        return  # stay quiet in groups to avoid noise
    await state.clear()
    await show_menu(message, user, session, i18n)


@router.callback_query()
async def fallback_callback(call: CallbackQuery, i18n: I18nContext) -> None:
    """Acknowledge any stale/unknown callback so the button stops spinning."""
    log.info("fallback: unhandled callback %r", call.data)
    await call.answer()
