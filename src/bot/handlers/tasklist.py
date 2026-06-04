"""Paginated task list: one message with up to 10 numbered items and 1–10
inline buttons; tapping a number opens that task's card as a new message below.
Supports filtering by status and sorting by priority. Shared by browse, /my and
search.

The list state lives in FSM data (list_all/list_filter/list_page/list_view_ids)
so number buttons carry only a small index, not issue UUIDs.
"""
from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import User
from bot.handlers import card as card_h

router = Router(name="tasklist")

PAGE = 10

# (callback type, i18n label key, Linear state.type matched). "all" = no filter.
FILTERS = [
    ("all", "list-f-all", None),
    ("unstarted", "list-f-todo", "unstarted"),
    ("started", "list-f-inprogress", "started"),
    ("completed", "list-f-done", "completed"),
    ("backlog", "list-f-backlog", "backlog"),
]


def _small(issue: dict) -> dict:
    state = issue.get("state") or {}
    return {
        "id": issue["id"],
        "identifier": issue["identifier"],
        "title": issue["title"],
        "state_name": state.get("name", ""),
        "state_type": state.get("type", ""),
        "priority": issue.get("priority") or 0,
    }


def _prio_key(item: dict) -> int:
    # Urgent(1) → Low(4) first; None(0) last.
    p = item["priority"]
    return p if p and p > 0 else 100


async def show_list(
    message: Message,
    *,
    state: FSMContext,
    i18n: I18nContext,
    title: str,
    issues: list[dict],
) -> None:
    await state.update_data(
        list_all=[_small(i) for i in issues],
        list_filter="all",
        list_page=0,
        list_title=title,
    )
    await _render(message, state, i18n, edit=False)


async def _render(
    message: Message, state: FSMContext, i18n: I18nContext, *, edit: bool
) -> None:
    data = await state.get_data()
    items: list[dict] = data.get("list_all", [])
    flt: str = data.get("list_filter", "all")
    page: int = data.get("list_page", 0)
    title: str = data.get("list_title", "")

    view = [it for it in items if flt == "all" or it["state_type"] == flt]
    view.sort(key=_prio_key)
    await state.update_data(list_view_ids=[it["id"] for it in view])

    total_pages = max(1, (len(view) + PAGE - 1) // PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE
    chunk = view[start : start + PAGE]

    lines = [f"<b>{html.escape(title)}</b> — {i18n.get('list-count', n=len(view))}"]
    if not chunk:
        lines.append(i18n.get("list-empty"))
    for n, it in enumerate(chunk, start=1):
        lines.append(
            f"{n}. <b>{html.escape(it['identifier'])}</b> · "
            f"{html.escape(it['title'])} — {html.escape(it['state_name'])}"
        )
    text = "\n".join(lines)

    kb = InlineKeyboardBuilder()
    # number buttons (rows of 5)
    row: list[InlineKeyboardButton] = []
    for n, _ in enumerate(chunk, start=1):
        row.append(InlineKeyboardButton(text=str(n), callback_data=f"li:open:{start + n - 1}"))
        if len(row) == 5:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)
    # filter row
    kb.row(
        *[
            InlineKeyboardButton(
                text=("• " if flt == key else "") + i18n.get(label),
                callback_data=f"li:flt:{key}",
            )
            for key, label, _ in FILTERS
        ]
    )
    # pagination row
    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(text=i18n.get("list-prev"), callback_data=f"li:pg:{page-1}"))
        nav.append(
            InlineKeyboardButton(
                text=i18n.get("list-page", page=page + 1, total=total_pages),
                callback_data="li:noop",
            )
        )
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton(text=i18n.get("list-next"), callback_data=f"li:pg:{page+1}"))
        kb.row(*nav)

    markup = kb.as_markup()
    if edit:
        try:
            await message.edit_text(text, reply_markup=markup)
        except Exception:  # noqa: BLE001
            await message.answer(text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("li:flt:"))
async def list_filter(call: CallbackQuery, state: FSMContext, i18n: I18nContext) -> None:
    await state.update_data(list_filter=call.data.split(":", 2)[2], list_page=0)
    await _render(call.message, state, i18n, edit=True)
    await call.answer()


@router.callback_query(F.data.startswith("li:pg:"))
async def list_page(call: CallbackQuery, state: FSMContext, i18n: I18nContext) -> None:
    await state.update_data(list_page=int(call.data.split(":", 2)[2]))
    await _render(call.message, state, i18n, edit=True)
    await call.answer()


@router.callback_query(F.data == "li:noop")
async def list_noop(call: CallbackQuery) -> None:
    await call.answer()


@router.callback_query(F.data.startswith("li:open:"))
async def list_open(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    idx = int(call.data.split(":", 2)[2])
    data = await state.get_data()
    ids: list[str] = data.get("list_view_ids", [])
    if idx >= len(ids):
        await call.answer()
        return
    await card_h.open_issue_card(
        call.message, ids[idx], user=user, session=session, state=state, i18n=i18n
    )
    await call.answer()
