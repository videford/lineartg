from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import User
from bot.keyboards.inline import lang_keyboard
from bot.keyboards.menu import main_menu
from bot.middlewares.i18n import SUPPORTED_LOCALES
from bot.services.permissions import Action, can, is_any_lead
from bot.services.users import slug_label
from bot.states import Registration

router = Router(name="start")

MIN_NAME_PARTS = 2
MAX_NAME_LEN = 100


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    user: User,
    session: AsyncSession,
    state: FSMContext,
    i18n: I18nContext,
) -> None:
    await state.clear()  # escape any half-finished flow on /start
    # First contact (or not yet registered): collect the real first/last name.
    if not user.registered:
        await state.set_state(Registration.waiting_full_name)
        await message.answer(i18n.get("reg-ask-name"))
        return
    await _show_main(message, user, session, i18n)


@router.message(Registration.waiting_full_name)
async def reg_name_received(
    message: Message,
    user: User,
    session: AsyncSession,
    state: FSMContext,
    i18n: I18nContext,
) -> None:
    raw = (message.text or "").strip()
    # Require at least first + last name.
    if len(raw.split()) < MIN_NAME_PARTS or len(raw) > MAX_NAME_LEN:
        await message.answer(i18n.get("reg-name-invalid"))
        return

    user.display_name = raw
    user.linear_label = slug_label(raw, user.telegram_id)
    user.registered = True
    await session.commit()
    await state.clear()

    await message.answer(i18n.get("reg-done", name=raw))
    await message.answer(i18n.get("start-choose-lang"), reply_markup=lang_keyboard())


async def _show_main(
    message: Message, user: User, session: AsyncSession, i18n: I18nContext
) -> None:
    is_admin = can(user.role, Action.MANAGE_LEADS)
    is_lead = await is_any_lead(session, user.telegram_id)
    await message.answer(
        i18n.get("start-welcome", name=user.display_name, role=user.role.value),
        reply_markup=main_menu(i18n, is_admin=is_admin, is_lead=is_lead),
    )


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(
    call: CallbackQuery, user: User, session: AsyncSession, i18n: I18nContext
) -> None:
    code = call.data.split(":", 1)[1]
    if code not in SUPPORTED_LOCALES:
        await call.answer()
        return
    user.lang = code
    await session.commit()
    await i18n.set_locale(code, user=user)
    await call.message.edit_text(i18n.get("lang-set"))
    # Reveal the persistent button menu in the chosen language.
    is_admin = can(user.role, Action.MANAGE_LEADS)
    is_lead = await is_any_lead(session, user.telegram_id)
    await call.message.answer(
        i18n.get("menu-title"),
        reply_markup=main_menu(i18n, is_admin=is_admin, is_lead=is_lead),
    )
    await call.answer()


@router.message(Command("help"))
async def cmd_help(message: Message, user: User, i18n: I18nContext) -> None:
    await message.answer(i18n.get("help-body", role=user.role.value))


@router.message(Command("whoami"))
async def cmd_whoami(message: Message, user: User, i18n: I18nContext) -> None:
    await message.answer(
        i18n.get("whoami", name=user.display_name, role=user.role.value)
    )
