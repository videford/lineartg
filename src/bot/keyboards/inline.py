from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Callback data namespaces (compact: tg callback_data is capped at 64 bytes)
#   lang:<code>
#   proj:<project_id>
#   asgn:<telegram_id>
#   issue:<issue_id>            -> open issue actions
#   st:<issue_id>:<state_id>    -> set workflow state
#   cmt:<issue_id>              -> start commenting


def lang_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🇷🇺 Русский", callback_data="lang:ru")
    kb.button(text="🇺🇿 Oʻzbek", callback_data="lang:uz")
    kb.button(text="🇬🇧 English", callback_data="lang:en")
    kb.adjust(1)
    return kb.as_markup()


def projects_keyboard(projects: list, prefix: str = "proj") -> InlineKeyboardMarkup:
    """Accepts either dicts ({id,name}) or ORM Project objects (.id/.name)."""
    kb = InlineKeyboardBuilder()
    for p in projects:
        pid = p["id"] if isinstance(p, dict) else p.id
        name = p["name"] if isinstance(p, dict) else p.name
        kb.button(text=name, callback_data=f"{prefix}:{pid}")
    kb.adjust(1)
    return kb.as_markup()


def members_keyboard(members: list, prefix: str = "asgn") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for m in members:
        kb.button(text=m.display_name, callback_data=f"{prefix}:{m.telegram_id}")
    kb.adjust(2)
    return kb.as_markup()


# Issue IDs are UUIDs (36 chars); two of them exceed Telegram's 64-byte
# callback_data limit. So the active card's issue_id lives in FSM state and
# action buttons below carry only the short secondary value.

PRIORITIES = [(1, "🔴 Urgent"), (2, "🟠 High"), (3, "🟡 Medium"), (4, "🟢 Low"), (0, "⚪ None")]
ESTIMATES = [0, 1, 2, 3, 5, 8]


def open_card_button(issue_id: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔎 Открыть", callback_data=f"card:{issue_id}")
    return kb.as_markup()


def card_keyboard(
    url: str, *, can_manage: bool, can_comment: bool
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if can_manage:
        kb.button(text="🔁 Статус", callback_data="act:status")
        kb.button(text="✏️ Изменить", callback_data="act:edit")
        kb.button(text="👤 Назначить", callback_data="act:assign")
    if can_comment:
        kb.button(text="💬 Комментарий", callback_data="act:comment")
    kb.button(text="🔄 Обновить", callback_data="act:refresh")
    kb.button(text="↗️ В Linear", url=url)
    kb.adjust(2)
    return kb.as_markup()


def edit_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Заголовок", callback_data="ed:title")
    kb.button(text="🧾 Описание", callback_data="ed:desc")
    kb.button(text="⚑ Приоритет", callback_data="ed:prio")
    kb.button(text="📅 Дедлайн", callback_data="ed:due")
    kb.button(text="🔢 Оценка", callback_data="ed:est")
    kb.button(text="🏷 Метки", callback_data="ed:lbl")
    kb.button(text="⬅️ Назад", callback_data="act:refresh")
    kb.adjust(2)
    return kb.as_markup()


def states_keyboard(states: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for s in states:
        kb.button(text=s["name"], callback_data=f"st:{s['id']}")
    kb.button(text="⬅️ Назад", callback_data="act:refresh")
    kb.adjust(2)
    return kb.as_markup()


def priority_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for value, label in PRIORITIES:
        kb.button(text=label, callback_data=f"pr:{value}")
    kb.button(text="⬅️ Назад", callback_data="act:edit")
    kb.adjust(2)
    return kb.as_markup()


def estimate_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for value in ESTIMATES:
        kb.button(text=str(value), callback_data=f"es:{value}")
    kb.button(text="✖ Снять", callback_data="es:none")
    kb.button(text="⬅️ Назад", callback_data="act:edit")
    kb.adjust(3)
    return kb.as_markup()


def due_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Сегодня", callback_data="du:0")
    kb.button(text="Завтра", callback_data="du:1")
    kb.button(text="+3 дня", callback_data="du:3")
    kb.button(text="+7 дней", callback_data="du:7")
    kb.button(text="✖ Снять", callback_data="du:none")
    kb.button(text="⬅️ Назад", callback_data="act:edit")
    kb.adjust(2)
    return kb.as_markup()


def labels_keyboard(labels: list[dict], selected: set[str]) -> InlineKeyboardMarkup:
    """Owner labels (prefix tg:) are managed via Assign, so hidden here."""
    kb = InlineKeyboardBuilder()
    for lb in labels:
        if lb["name"].startswith("tg:"):
            continue
        mark = "☑️ " if lb["id"] in selected else "▫️ "
        kb.button(text=mark + lb["name"], callback_data=f"lb:{lb['id']}")
    kb.button(text="✅ Готово", callback_data="act:refresh")
    kb.adjust(2)
    return kb.as_markup()
