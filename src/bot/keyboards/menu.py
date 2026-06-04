from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Stable leading emojis — menu buttons are matched by these, so routing is
# independent of the user's interface language.
EMOJI_MY = "📋"
EMOJI_CREATE = "➕"
EMOJI_ASSIGN = "👥"
EMOJI_SEARCH = "🔎"
EMOJI_SETTINGS = "⚙️"
EMOJI_HELP = "❓"
EMOJI_ADMIN = "🛠"


def main_menu(i18n, *, is_admin: bool, is_lead: bool) -> ReplyKeyboardMarkup:
    rows = [[KeyboardButton(text=i18n.get("menu-my")), KeyboardButton(text=i18n.get("menu-create"))]]
    if is_admin or is_lead:
        rows.append(
            [KeyboardButton(text=i18n.get("menu-assign")), KeyboardButton(text=i18n.get("menu-search"))]
        )
    else:
        rows.append([KeyboardButton(text=i18n.get("menu-search"))])
    rows.append(
        [KeyboardButton(text=i18n.get("menu-settings")), KeyboardButton(text=i18n.get("menu-help"))]
    )
    if is_admin:
        rows.append([KeyboardButton(text=i18n.get("menu-admin"))])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True, is_persistent=True)


def settings_menu(i18n) -> "InlineKeyboardMarkup":  # noqa: F821
    kb = InlineKeyboardBuilder()
    kb.button(text=i18n.get("settings-language"), callback_data="set:lang")
    kb.button(text=i18n.get("settings-profile"), callback_data="set:profile")
    kb.adjust(1)
    return kb.as_markup()


def admin_menu(i18n) -> "InlineKeyboardMarkup":  # noqa: F821
    kb = InlineKeyboardBuilder()
    kb.button(text=i18n.get("admin-connect"), callback_data="adm:connect")
    kb.button(text=i18n.get("admin-sync"), callback_data="adm:sync")
    kb.button(text=i18n.get("admin-setlead"), callback_data="adm:setlead")
    kb.button(text=i18n.get("admin-leads"), callback_data="adm:leads")
    kb.adjust(1)
    return kb.as_markup()
