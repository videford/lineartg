"""Team dashboard, usable in group chats via /board: who's working on what,
burning deadlines, unassigned tasks, and all open tasks.

The section buttons stay at the bottom in every view (details shown above), so
you can switch sections without re-running /board. Task-list sections show
numbered buttons that open the full task card as a new message below.
"""
from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.dates import fmt_date
from bot.db import ChatBinding, User
from bot.services import workspace
from bot.services.permissions import Action, can
from bot.services.users import OWNER_PREFIX, list_members

router = Router(name="board")

CLOSED = {"completed", "canceled"}
PAGE = 10  # tasks per page (each gets a numbered open-button)


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


def _kb(i18n: I18nContext, open_count: int = 0, page: int = 0, total_pages: int = 1):
    kb = InlineKeyboardBuilder()
    row: list[InlineKeyboardButton] = []
    start = page * PAGE  # so button labels match the continuous numbering in the text
    for n in range(open_count):
        row.append(InlineKeyboardButton(text=str(start + n + 1), callback_data=f"li:open:{n}"))
        if len(row) == 5:
            kb.row(*row)
            row = []
    if row:
        kb.row(*row)
    # Pagination row (only when there's more than one page).
    if total_pages > 1:
        nav: list[InlineKeyboardButton] = []
        if page > 0:
            nav.append(InlineKeyboardButton(text=i18n.get("list-prev"), callback_data=f"board:pg:{page-1}"))
        nav.append(InlineKeyboardButton(
            text=i18n.get("list-page", page=page + 1, total=total_pages), callback_data="li:noop"
        ))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton(text=i18n.get("list-next"), callback_data=f"board:pg:{page+1}"))
        kb.row(*nav)
    _section_rows(kb, i18n)
    return kb.as_markup()


@router.message(Command("board"))
async def cmd_board(
    message: Message, user: User, session: AsyncSession, i18n: I18nContext
) -> None:
    if message.chat.type != "private":
        binding = await session.get(ChatBinding, message.chat.id)
        if binding is None:
            # Unauthorized group — only a bot admin can enable it via /bind.
            if can(user.role, Action.BIND_CHAT):
                await message.answer(i18n.get("board-bind-first"))
            return
        # If bound to a specific topic, ignore /board in any other topic.
        if binding.thread_id is not None and message.message_thread_id != binding.thread_id:
            return
    await message.answer(
        i18n.get("board-title"),
        reply_markup=_kb(i18n),
        disable_notification=message.chat.type != "private",
    )


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


def _section_title(i18n: I18nContext, section: str) -> str:
    return {
        "due": i18n.get("board-due"),
        "free": i18n.get("board-free"),
        "open": i18n.get("board-open"),
    }.get(section, i18n.get("board-open"))


async def _section_issues(session: AsyncSession, section: str):
    """Return (issues, label→name map) for a board section, filtered/sorted."""
    issues = await _issues(session)
    names = await _label_map(session)
    if section == "due":
        data = sorted(
            (i for i in issues if _is_open(i) and i.get("dueDate")),
            key=lambda i: i["dueDate"],
        )
    elif section == "free":
        data = [i for i in issues if _is_open(i) and not _owner_labels(i)]
    else:  # "open"
        data = [i for i in issues if _is_open(i)]
    return data, names


async def _show_tasks(call, state, i18n, section: str, issues: list[dict], names, page: int = 0):
    """Render one page of a task list with numbered open-buttons + nav + menu."""
    total_pages = max(1, (len(issues) + PAGE - 1) // PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE
    shown = issues[start : start + PAGE]
    # Number buttons index into this page's slice, so store exactly the slice.
    await state.update_data(
        list_view_ids=[i["id"] for i in shown], board_section=section, board_page=page
    )
    lines = [f"<b>{_section_title(i18n, section)}</b> — {i18n.get('list-count', n=len(issues))}"]
    if not shown:
        lines.append(i18n.get("board-empty"))
    for n, i in enumerate(shown, start=start + 1):  # continuous numbering across pages
        state_name = (i.get("state") or {}).get("name", "")
        due = f" · ⏰{fmt_date(i['dueDate'])}" if i.get("dueDate") else ""
        lines.append(
            f"{n}. {_short(i)} — {html.escape(state_name)}{due} · {html.escape(_assignee_names(i, names))}"
        )
    await call.message.edit_text(
        "\n".join(lines), reply_markup=_kb(i18n, len(shown), page, total_pages)
    )
    await call.answer()


async def _who_pairs(session: AsyncSession) -> list[tuple[str, dict]]:
    """Started tasks grouped by assignee, flattened to ordered (name, issue) pairs
    so they can be numbered and paginated like the other sections."""
    issues = await _issues(session)
    names = await _label_map(session)
    started = [i for i in issues if (i.get("state") or {}).get("type") == "started"]
    by_owner: dict[str, list[dict]] = {}
    for i in started:
        # Only assigned tasks here — unassigned ones live in "Без исполнителя".
        for lb in _owner_labels(i):
            by_owner.setdefault(names.get(lb, lb), []).append(i)
    pairs: list[tuple[str, dict]] = []
    for who in sorted(by_owner):
        for issue in by_owner[who]:
            pairs.append((who, issue))
    return pairs


async def _render_who(call, state, i18n, pairs: list[tuple[str, dict]], page: int = 0):
    """Render one page of the who's-busy view with per-person headers and
    numbered open-buttons (the number matches the open-button label)."""
    total_pages = max(1, (len(pairs) + PAGE - 1) // PAGE)
    page = max(0, min(page, total_pages - 1))
    start = page * PAGE
    shown = pairs[start : start + PAGE]
    await state.update_data(
        list_view_ids=[issue["id"] for _, issue in shown],
        board_section="who",
        board_page=page,
    )
    lines = [f"<b>{i18n.get('board-who')}</b> — {i18n.get('list-count', n=len(pairs))}"]
    if not shown:
        lines.append(i18n.get("board-empty"))
    last_who = None
    for offset, (who, issue) in enumerate(shown):
        if who != last_who:
            lines.append(f"• <b>{html.escape(who)}</b>:")
            last_who = who
        lines.append(f"   {start + offset + 1}. {_short(issue)}")
    await call.message.edit_text(
        "\n".join(lines), reply_markup=_kb(i18n, len(shown), page, total_pages)
    )
    await call.answer()


@router.callback_query(F.data == "board:who")
async def board_who(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    pairs = await _who_pairs(session)
    await _render_who(call, state, i18n, pairs, page=0)


@router.callback_query(F.data == "board:due")
async def board_due(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issues, names = await _section_issues(session, "due")
    await _show_tasks(call, state, i18n, "due", issues, names, page=0)


@router.callback_query(F.data == "board:free")
async def board_free(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issues, names = await _section_issues(session, "free")
    await _show_tasks(call, state, i18n, "free", issues, names, page=0)


@router.callback_query(F.data == "board:open")
async def board_open(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issues, names = await _section_issues(session, "open")
    await _show_tasks(call, state, i18n, "open", issues, names, page=0)


@router.callback_query(F.data.startswith("board:pg:"))
async def board_page(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    page = int(call.data.split(":", 2)[2])
    section = (await state.get_data()).get("board_section", "open")
    if section == "who":
        pairs = await _who_pairs(session)
        await _render_who(call, state, i18n, pairs, page=page)
        return
    issues, names = await _section_issues(session, section)
    await _show_tasks(call, state, i18n, section, issues, names, page=page)
