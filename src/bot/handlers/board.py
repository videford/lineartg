"""Team dashboard, usable in group chats via /board: who's working on what,
burning deadlines, unassigned tasks, and all open tasks.

The section buttons stay at the bottom in every view (details shown above), so
you can switch sections without re-running /board. Task-list sections show
numbered buttons that open the full task card as a new message below.
"""
from __future__ import annotations

import html
from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import ChatBinding
from bot.services import workspace
from bot.services.users import OWNER_PREFIX, list_members

router = Router(name="board")

CLOSED = {"completed", "canceled"}
MAX_OPEN = 10  # how many tasks get a numbered open-button


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


def _section_rows(kb: InlineKeyboardBuilder, i18n: I18nContext) -> None:
    kb.row(
        InlineKeyboardButton(text=i18n.get("board-who"), callback_data="board:who"),
        InlineKeyboardButton(text=i18n.get("board-due"), callback_data="board:due"),
    )
    kb.row(
        InlineKeyboardButton(text=i18n.get("board-free"), callback_data="board:free"),
        InlineKeyboardButton(text=i18n.get("board-open"), callback_data="board:open"),
    )


def _kb(i18n: I18nContext, open_count: int = 0):
    kb = InlineKeyboardBuilder()
    row: list[InlineKeyboardButton] = []
    for n in range(open_count):
        row.append(InlineKeyboardButton(text=str(n + 1), callback_data=f"li:open:{n}"))
        if len(row) == 5:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)
    _section_rows(kb, i18n)
    return kb.as_markup()


@router.message(Command("board"))
async def cmd_board(message: Message, session: AsyncSession, i18n: I18nContext) -> None:
    if message.chat.type != "private":
        binding = await session.get(ChatBinding, message.chat.id)
        # If bound to a specific topic, ignore /board in any other topic.
        if (
            binding is not None
            and binding.thread_id is not None
            and message.message_thread_id != binding.thread_id
        ):
            return
    await message.answer(i18n.get("board-title"), reply_markup=_kb(i18n))


async def _label_map(session: AsyncSession) -> dict[str, str]:
    return {u.linear_label: u.display_name for u in await list_members(session) if u.linear_label}


async def _issues(session: AsyncSession):
    client = await workspace.get_client(session)
    return await client.all_issues()


def _assignee_names(issue: dict, names: dict[str, str]) -> str:
    labels = _owner_labels(issue)
    if not labels:
        return "—"
    return ", ".join(names.get(lb, lb[len(OWNER_PREFIX):]) for lb in labels)


async def _show_tasks(call, state, i18n, title: str, issues: list[dict], names: dict[str, str]):
    """Render a task list with numbered open-buttons + the section menu."""
    shown = issues[:MAX_OPEN]
    await state.update_data(list_view_ids=[i["id"] for i in shown])
    lines = [f"<b>{title}</b>"]
    if not shown:
        lines.append(i18n.get("board-empty"))
    for n, i in enumerate(shown, start=1):
        state_name = (i.get("state") or {}).get("name", "")
        due = f" · ⏰{i['dueDate']}" if i.get("dueDate") else ""
        lines.append(f"{n}. {_short(i)} — {html.escape(state_name)}{due} · {html.escape(_assignee_names(i, names))}")
    if len(issues) > MAX_OPEN:
        lines.append(i18n.get("board-more", n=len(issues) - MAX_OPEN))
    await call.message.edit_text("\n".join(lines), reply_markup=_kb(i18n, len(shown)))
    await call.answer()


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
    await call.message.edit_text("\n".join(lines), reply_markup=_kb(i18n))
    await call.answer()


@router.callback_query(F.data == "board:due")
async def board_due(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issues = await _issues(session)
    names = await _label_map(session)
    dated = sorted(
        (i for i in issues if _is_open(i) and i.get("dueDate")),
        key=lambda i: i["dueDate"],
    )
    await _show_tasks(call, state, i18n, i18n.get("board-due"), dated, names)


@router.callback_query(F.data == "board:free")
async def board_free(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issues = await _issues(session)
    names = await _label_map(session)
    free = [i for i in issues if _is_open(i) and not _owner_labels(i)]
    await _show_tasks(call, state, i18n, i18n.get("board-free"), free, names)


@router.callback_query(F.data == "board:open")
async def board_open(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issues = await _issues(session)
    names = await _label_map(session)
    open_issues = [i for i in issues if _is_open(i)]
    await _show_tasks(call, state, i18n, i18n.get("board-open"), open_issues, names)
