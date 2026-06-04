"""Team dashboard, usable in group chats via /board: who's working on what,
burning deadlines, unassigned tasks, and all open tasks. Read-only.
"""
from __future__ import annotations

import html
from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services import workspace
from bot.services.users import OWNER_PREFIX, list_members

router = Router(name="board")

CLOSED = {"completed", "canceled"}
MAX_LINES = 25


def _owner_labels(issue: dict) -> list[str]:
    return [
        lb["name"]
        for lb in (issue.get("labels") or {}).get("nodes", [])
        if lb["name"].startswith(OWNER_PREFIX)
    ]


def _is_open(issue: dict) -> bool:
    return (issue.get("state") or {}).get("type") not in CLOSED


def _short(issue: dict) -> str:
    return f"<b>{html.escape(issue['identifier'])}</b> · {html.escape(issue['title'])}"


def _menu_kb(i18n: I18nContext):
    kb = InlineKeyboardBuilder()
    kb.button(text=i18n.get("board-who"), callback_data="board:who")
    kb.button(text=i18n.get("board-due"), callback_data="board:due")
    kb.button(text=i18n.get("board-free"), callback_data="board:free")
    kb.button(text=i18n.get("board-open"), callback_data="board:open")
    kb.adjust(2)
    return kb.as_markup()


def _back_kb(i18n: I18nContext):
    kb = InlineKeyboardBuilder()
    kb.button(text=i18n.get("nav-back"), callback_data="board:menu")
    return kb.as_markup()


@router.message(Command("board"))
async def cmd_board(message: Message, i18n: I18nContext) -> None:
    await message.answer(i18n.get("board-title"), reply_markup=_menu_kb(i18n))


@router.callback_query(F.data == "board:menu")
async def board_menu(call: CallbackQuery, i18n: I18nContext) -> None:
    await call.message.edit_text(i18n.get("board-title"), reply_markup=_menu_kb(i18n))
    await call.answer()


async def _label_map(session: AsyncSession) -> dict[str, str]:
    return {
        u.linear_label: u.display_name
        for u in await list_members(session)
        if u.linear_label
    }


async def _issues(session: AsyncSession):
    client = await workspace.get_client(session)
    return await client.all_issues()


def _assignee_names(issue: dict, names: dict[str, str]) -> str:
    labels = _owner_labels(issue)
    if not labels:
        return "—"
    return ", ".join(names.get(lb, lb[len(OWNER_PREFIX):]) for lb in labels)


@router.callback_query(F.data == "board:who")
async def board_who(call: CallbackQuery, session: AsyncSession, i18n: I18nContext) -> None:
    issues = await _issues(session)
    names = await _label_map(session)
    started = [i for i in issues if (i.get("state") or {}).get("type") == "started"]

    by_owner: dict[str, list[str]] = {}
    for i in started:
        for lb in _owner_labels(i) or ["—"]:
            by_owner.setdefault(names.get(lb, lb), []).append(i["identifier"])

    lines = [f"<b>{i18n.get('board-who')}</b>"]
    if not by_owner:
        lines.append(i18n.get("board-empty"))
    for who, ids in sorted(by_owner.items()):
        lines.append(f"• <b>{html.escape(who)}</b>: {', '.join(ids)}")
    await call.message.edit_text("\n".join(lines[:MAX_LINES]), reply_markup=_back_kb(i18n))
    await call.answer()


@router.callback_query(F.data == "board:due")
async def board_due(call: CallbackQuery, session: AsyncSession, i18n: I18nContext) -> None:
    issues = await _issues(session)
    names = await _label_map(session)
    today = date.today().isoformat()
    dated = sorted(
        (i for i in issues if _is_open(i) and i.get("dueDate")),
        key=lambda i: i["dueDate"],
    )
    lines = [f"<b>{i18n.get('board-due')}</b>"]
    if not dated:
        lines.append(i18n.get("board-empty"))
    for i in dated[:MAX_LINES]:
        mark = "🔴" if i["dueDate"] < today else "🟡"
        lines.append(f"{mark} {i['dueDate']} · {_short(i)} — {html.escape(_assignee_names(i, names))}")
    await call.message.edit_text("\n".join(lines), reply_markup=_back_kb(i18n))
    await call.answer()


@router.callback_query(F.data == "board:free")
async def board_free(call: CallbackQuery, session: AsyncSession, i18n: I18nContext) -> None:
    issues = await _issues(session)
    free = [i for i in issues if _is_open(i) and not _owner_labels(i)]
    lines = [f"<b>{i18n.get('board-free')}</b>"]
    if not free:
        lines.append(i18n.get("board-empty"))
    for i in free[:MAX_LINES]:
        state = (i.get("state") or {}).get("name", "")
        lines.append(f"• {_short(i)} — {html.escape(state)}")
    await call.message.edit_text("\n".join(lines), reply_markup=_back_kb(i18n))
    await call.answer()


@router.callback_query(F.data == "board:open")
async def board_open(call: CallbackQuery, session: AsyncSession, i18n: I18nContext) -> None:
    issues = await _issues(session)
    names = await _label_map(session)
    open_issues = [i for i in issues if _is_open(i)]
    lines = [f"<b>{i18n.get('board-open')}</b> — {len(open_issues)}"]
    if not open_issues:
        lines.append(i18n.get("board-empty"))
    for i in open_issues[:MAX_LINES]:
        state = (i.get("state") or {}).get("name", "")
        lines.append(f"• {_short(i)} — {html.escape(state)} · {html.escape(_assignee_names(i, names))}")
    await call.message.edit_text("\n".join(lines), reply_markup=_back_kb(i18n))
    await call.answer()
