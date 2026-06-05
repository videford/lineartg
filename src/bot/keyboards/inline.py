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


def lang_keyboard(with_back: bool = False) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🇷🇺 Русский", callback_data="lang:ru")
    kb.button(text="🇺🇿 Oʻzbek", callback_data="lang:uz")
    kb.button(text="🇬🇧 English", callback_data="lang:en")
    if with_back:
        kb.button(text="⬅️ Назад", callback_data="nav:settings")
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


def members_keyboard(
    members: list, prefix: str = "asgn", back: str | None = None
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for m in members:
        kb.button(text=m.display_name, callback_data=f"{prefix}:{m.telegram_id}")
    kb.adjust(2)
    if back:
        kb.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=back))
    return kb.as_markup()


# Issue IDs are UUIDs (36 chars); two of them exceed Telegram's 64-byte
# callback_data limit. So the active card's issue_id lives in FSM state and
# action buttons below carry only the short secondary value.

PRIORITIES = [(1, "🔴 Urgent"), (2, "🟠 High"), (3, "🟡 Medium"), (4, "🟢 Low"), (0, "⚪ None")]
ESTIMATES = [0, 1, 2, 3, 5, 8]


def open_card_button(issue_id: str, *, new: bool = False) -> InlineKeyboardMarkup:
    # new=True opens the card as a NEW message (for group/announcement messages
    # that shouldn't be replaced); otherwise edits the current message.
    prefix = "ocard" if new else "card"
    kb = InlineKeyboardBuilder()
    kb.button(text="🔎 Открыть", callback_data=f"{prefix}:{issue_id}")
    return kb.as_markup()


def card_keyboard(
    i18n, url: str, *, can_manage: bool, can_comment: bool, subscribed: bool, is_owner: bool = False
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if can_manage:
        kb.button(text=i18n.get("btn-status"), callback_data="act:status")
        kb.button(text=i18n.get("btn-edit"), callback_data="act:edit")
        kb.button(text=i18n.get("btn-assign"), callback_data="act:assign")
    if can_comment:
        kb.button(text=i18n.get("btn-comment"), callback_data="act:comment")
    if is_owner:
        kb.button(text=i18n.get("btn-owner"), callback_data="act:subowner")
    elif subscribed:
        kb.button(text=i18n.get("btn-unsubscribe"), callback_data="act:subtoggle")
    else:
        kb.button(text=i18n.get("btn-subscribe"), callback_data="act:subtoggle")
    if can_manage:
        kb.button(text=i18n.get("btn-subscribe-other"), callback_data="act:subother")
    kb.button(text=i18n.get("btn-refresh"), callback_data="act:refresh")
    kb.button(text=i18n.get("btn-open-linear"), url=url)
    kb.adjust(2)
    return kb.as_markup()


def edit_menu_keyboard(i18n) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=i18n.get("btn-title"), callback_data="ed:title")
    kb.button(text=i18n.get("btn-desc"), callback_data="ed:desc")
    kb.button(text=i18n.get("btn-priority"), callback_data="ed:prio")
    kb.button(text=i18n.get("btn-due"), callback_data="ed:due")
    kb.button(text=i18n.get("btn-labels"), callback_data="ed:lbl")
    kb.button(text=i18n.get("nav-back"), callback_data="act:refresh")
    kb.adjust(2)
    return kb.as_markup()


def states_keyboard(i18n, states: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for s in states:
        kb.button(text=s["name"], callback_data=f"st:{s['id']}")
    kb.button(text=i18n.get("nav-back"), callback_data="act:refresh")
    kb.adjust(2)
    return kb.as_markup()


def priority_keyboard(i18n) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for value, label in PRIORITIES:
        kb.button(text=label, callback_data=f"pr:{value}")
    kb.button(text=i18n.get("nav-back"), callback_data="act:edit")
    kb.adjust(2)
    return kb.as_markup()


def estimate_keyboard(i18n) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for value in ESTIMATES:
        kb.button(text=str(value), callback_data=f"es:{value}")
    kb.button(text=i18n.get("btn-clear"), callback_data="es:none")
    kb.button(text=i18n.get("nav-back"), callback_data="act:edit")
    kb.adjust(3)
    return kb.as_markup()


def due_keyboard(i18n) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=i18n.get("due-today"), callback_data="du:0")
    kb.button(text=i18n.get("due-tomorrow"), callback_data="du:1")
    kb.button(text=i18n.get("due-3d"), callback_data="du:3")
    kb.button(text=i18n.get("due-7d"), callback_data="du:7")
    kb.button(text=i18n.get("due-custom-btn"), callback_data="du:custom")
    kb.button(text=i18n.get("btn-clear"), callback_data="du:none")
    kb.button(text=i18n.get("nav-back"), callback_data="act:edit")
    kb.adjust(2)
    return kb.as_markup()


def draft_preview_keyboard(i18n) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=i18n.get("btn-title"), callback_data="dft:title")
    kb.button(text=i18n.get("btn-desc"), callback_data="dft:desc")
    kb.button(text=i18n.get("btn-priority"), callback_data="dft:prio")
    kb.button(text=i18n.get("btn-due"), callback_data="dft:due")
    kb.button(text=i18n.get("draft-btn-assignee"), callback_data="dft:asg")
    kb.button(text=i18n.get("draft-btn-sub"), callback_data="dft:sub")
    kb.button(text=i18n.get("draft-btn-publish"), callback_data="dft:publish")
    kb.button(text=i18n.get("draft-btn-cancel"), callback_data="dft:cancel")
    kb.adjust(2, 2, 2, 1, 1)
    return kb.as_markup()


def draft_priority_keyboard(i18n) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for value, label in PRIORITIES:
        kb.button(text=label, callback_data=f"dpr:{value}")
    kb.button(text=i18n.get("nav-back"), callback_data="dft:back")
    kb.adjust(2)
    return kb.as_markup()


def draft_due_keyboard(i18n) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text=i18n.get("due-today"), callback_data="ddu:0")
    kb.button(text=i18n.get("due-tomorrow"), callback_data="ddu:1")
    kb.button(text=i18n.get("due-3d"), callback_data="ddu:3")
    kb.button(text=i18n.get("due-7d"), callback_data="ddu:7")
    kb.button(text=i18n.get("due-custom-btn"), callback_data="ddu:custom")
    kb.button(text=i18n.get("btn-clear"), callback_data="ddu:none")
    kb.button(text=i18n.get("nav-back"), callback_data="dft:back")
    kb.adjust(2)
    return kb.as_markup()


def labels_keyboard(i18n, labels: list[dict], selected: set[str]) -> InlineKeyboardMarkup:
    """Owner labels (prefix tg:) are managed via Assign, so hidden here."""
    kb = InlineKeyboardBuilder()
    for lb in labels:
        if lb["name"].startswith("tg:"):
            continue
        mark = "☑️ " if lb["id"] in selected else "▫️ "
        kb.button(text=mark + lb["name"], callback_data=f"lb:{lb['id']}")
    kb.button(text=i18n.get("btn-done"), callback_data="act:refresh")
    kb.adjust(2)
    return kb.as_markup()
