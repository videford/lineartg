"""Draft task creation with a preview card.

Flow: pick project → enter title → enter description (skippable) → a preview
card where due date, priority, assignee and subscribers can be set. Nothing is
created in Linear until the user presses Publish, so a stray message can never
become an orphan task (the previous flow created the issue on first text).

The whole draft lives in FSM data (no DB/Linear writes); the preview message id
is kept so text-input edits (title/description/custom date) can refresh it in
place. Callback namespaces are draft-specific (dft:/dpr:/ddu:/dasg:/dsub:/dproj:)
so they never collide with the live-card editor in card.py.
"""
from __future__ import annotations

import html
from datetime import date, datetime, timedelta

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import IssueLink, User
from bot.keyboards.inline import (
    PRIORITIES,
    draft_due_keyboard,
    draft_preview_keyboard,
    draft_priority_keyboard,
    projects_keyboard,
)
from bot.services import workspace
from bot.services.permissions import can_create_in
from bot.services.projects import get_project, manageable_projects, project_team
from bot.services.subscriptions import subscribe
from bot.states import DraftTask

router = Router(name="draft")

_PRIO_LABELS = dict(PRIORITIES)
DESC_PREVIEW_MAX = 500


# ── entry ────────────────────────────────────────────────────


async def start_draft(
    message: Message,
    user: User,
    session: AsyncSession,
    state: FSMContext,
    i18n: I18nContext,
) -> None:
    """Public entry used by the menu button and /task, /assign commands."""
    try:
        await workspace.get_token(session)
    except workspace.WorkspaceNotConnected:
        await message.answer(i18n.get("err-no-workspace"))
        return
    projects = await manageable_projects(session, user)
    if not projects:
        await message.answer(i18n.get("err-no-permission"))
        return
    await state.clear()
    await state.set_state(DraftTask.waiting_project)
    await message.answer(
        i18n.get("task-choose-project"),
        reply_markup=projects_keyboard(projects, prefix="dproj"),
    )


@router.callback_query(DraftTask.waiting_project, F.data.startswith("dproj:"))
async def draft_project_chosen(
    call: CallbackQuery,
    user: User,
    session: AsyncSession,
    state: FSMContext,
    i18n: I18nContext,
) -> None:
    project_id = call.data.split(":", 1)[1]
    if not await can_create_in(session, user, project_id):
        await call.answer(i18n.get("err-no-permission"), show_alert=True)
        return
    project = await get_project(session, project_id)
    if project is None or not project.team_id:
        await call.answer(i18n.get("err-no-projects"), show_alert=True)
        return
    await state.update_data(
        draft_project_id=project_id,
        draft_team_id=project.team_id,
        draft_project_name=project.name,
        draft_title=None,
        draft_desc=None,
        draft_priority=None,
        draft_due=None,
        draft_assignee=None,
        draft_subs=[],
        editing=False,
    )
    await state.set_state(DraftTask.waiting_title)
    await call.message.edit_text(i18n.get("draft-send-title"))
    await call.answer()


# ── title / description text input ───────────────────────────


@router.message(DraftTask.waiting_title)
async def draft_title_received(
    message: Message, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer(i18n.get("draft-send-title"))
        return
    data = await state.get_data()
    await state.update_data(draft_title=title)
    if data.get("editing"):
        await state.update_data(editing=False)
        await _refresh_preview(message.bot, session, state, i18n)
        return
    # Initial flow: ask for a description next (skippable).
    await state.set_state(DraftTask.waiting_desc)
    kb = InlineKeyboardBuilder()
    kb.button(text=i18n.get("draft-desc-skip"), callback_data="dft:skipdesc")
    await message.answer(i18n.get("draft-send-desc"), reply_markup=kb.as_markup())


@router.callback_query(DraftTask.waiting_desc, F.data == "dft:skipdesc")
async def draft_skip_desc(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    await state.update_data(draft_desc="")
    await _open_preview_new(call.message, session, state, i18n)
    await call.answer()


@router.message(DraftTask.waiting_desc)
async def draft_desc_received(
    message: Message, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    data = await state.get_data()
    await state.update_data(draft_desc=(message.text or "").strip())
    if data.get("editing"):
        await state.update_data(editing=False)
        await _refresh_preview(message.bot, session, state, i18n)
        return
    await _open_preview_new(message, session, state, i18n)


# ── preview rendering ────────────────────────────────────────


async def _build_preview(session: AsyncSession, state: FSMContext, i18n: I18nContext):
    data = await state.get_data()
    title = (data.get("draft_title") or "").strip() or "—"
    desc = (data.get("draft_desc") or "").strip()
    if len(desc) > DESC_PREVIEW_MAX:
        desc = desc[:DESC_PREVIEW_MAX] + "…"
    prio = data.get("draft_priority")
    prio_label = _PRIO_LABELS.get(prio) if prio is not None else "—"
    due = data.get("draft_due") or "—"

    assignee = "—"
    if data.get("draft_assignee"):
        u = await session.get(User, data["draft_assignee"])
        assignee = u.display_name if u else "—"

    sub_ids = data.get("draft_subs") or []
    subs = "—"
    if sub_ids:
        rows = {
            u.telegram_id: u.display_name
            for u in await session.scalars(
                select(User).where(User.telegram_id.in_(sub_ids))
            )
        }
        subs = ", ".join(rows.get(s, str(s)) for s in sub_ids)

    lines = [
        f"<b>{i18n.get('draft-title')}</b>",
        f"{i18n.get('draft-f-title')}: <b>{html.escape(title)}</b>",
        f"{i18n.get('card-f-project')}: {html.escape(data.get('draft_project_name') or '—')} · "
        f"{i18n.get('card-f-assignee')}: {html.escape(assignee)}",
        f"{i18n.get('card-f-priority')}: {prio_label} · {i18n.get('card-f-due')}: {due}",
        f"{i18n.get('card-f-subscribers')}: {html.escape(subs)}",
        "─────────",
        f"{i18n.get('draft-f-desc')}:",
        html.escape(desc) if desc else "—",
        "─────────",
        i18n.get("draft-hint"),
    ]
    return "\n".join(lines), draft_preview_keyboard(i18n)


async def _open_preview_new(
    message: Message, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    text, kb = await _build_preview(session, state, i18n)
    sent = await message.answer(text, reply_markup=kb, disable_web_page_preview=True)
    await state.update_data(preview_chat=sent.chat.id, preview_msg=sent.message_id)
    await state.set_state(DraftTask.preview)


async def _refresh_preview(
    bot: Bot, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    """Edit the stored preview message in place (used after text input)."""
    text, kb = await _build_preview(session, state, i18n)
    data = await state.get_data()
    await state.set_state(DraftTask.preview)
    try:
        await bot.edit_message_text(
            text,
            chat_id=data["preview_chat"],
            message_id=data["preview_msg"],
            reply_markup=kb,
            disable_web_page_preview=True,
        )
    except Exception:  # noqa: BLE001 — message gone/unchanged; nothing to do
        pass


async def _edit_preview(call: CallbackQuery, session, state, i18n) -> None:
    text, kb = await _build_preview(session, state, i18n)
    await state.set_state(DraftTask.preview)
    await call.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)


@router.callback_query(F.data == "dft:back")
async def draft_back(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    if not (await state.get_data()).get("draft_project_id"):
        await call.answer()
        return
    await _edit_preview(call, session, state, i18n)
    await call.answer()


# ── edit title / description from the preview ────────────────


@router.callback_query(F.data == "dft:title")
async def draft_edit_title(call: CallbackQuery, state: FSMContext, i18n: I18nContext) -> None:
    await state.update_data(editing=True)
    await state.set_state(DraftTask.waiting_title)
    await call.message.answer(i18n.get("draft-send-title"))
    await call.answer()


@router.callback_query(F.data == "dft:desc")
async def draft_edit_desc(call: CallbackQuery, state: FSMContext, i18n: I18nContext) -> None:
    await state.update_data(editing=True)
    await state.set_state(DraftTask.waiting_desc)
    await call.message.answer(i18n.get("draft-send-desc"))
    await call.answer()


# ── priority ─────────────────────────────────────────────────


@router.callback_query(F.data == "dft:prio")
async def draft_show_priority(call: CallbackQuery, i18n: I18nContext) -> None:
    await call.message.edit_reply_markup(reply_markup=draft_priority_keyboard(i18n))
    await call.answer()


@router.callback_query(F.data.startswith("dpr:"))
async def draft_set_priority(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    await state.update_data(draft_priority=int(call.data.split(":", 1)[1]))
    await _edit_preview(call, session, state, i18n)
    await call.answer(i18n.get("toast-saved"))


# ── due date ─────────────────────────────────────────────────


@router.callback_query(F.data == "dft:due")
async def draft_show_due(call: CallbackQuery, i18n: I18nContext) -> None:
    await call.message.edit_reply_markup(reply_markup=draft_due_keyboard(i18n))
    await call.answer()


@router.callback_query(F.data.startswith("ddu:"))
async def draft_set_due(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    raw = call.data.split(":", 1)[1]
    if raw == "custom":
        await state.set_state(DraftTask.waiting_due)
        await call.message.answer(i18n.get("due-prompt"))
        await call.answer()
        return
    value = None if raw == "none" else (date.today() + timedelta(days=int(raw))).isoformat()
    await state.update_data(draft_due=value)
    await _edit_preview(call, session, state, i18n)
    await call.answer(i18n.get("toast-saved"))


def _parse_date(text: str) -> str | None:
    text = (text or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


@router.message(DraftTask.waiting_due)
async def draft_due_received(
    message: Message, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    iso = _parse_date(message.text or "")
    if iso is None:
        await message.answer(i18n.get("due-invalid"))
        return
    await state.update_data(draft_due=iso)
    await _refresh_preview(message.bot, session, state, i18n)


# ── assignee ─────────────────────────────────────────────────


@router.callback_query(F.data == "dft:asg")
async def draft_show_assignee(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    data = await state.get_data()
    team = await project_team(session, data.get("draft_project_id"))
    if not team:
        await call.answer(i18n.get("assign-no-team"), show_alert=True)
        return
    kb = InlineKeyboardBuilder()
    for m in team:
        kb.button(text=m.display_name, callback_data=f"dasg:{m.telegram_id}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text=i18n.get("assign-none"), callback_data="dasg:none"))
    kb.row(InlineKeyboardButton(text=i18n.get("nav-back"), callback_data="dft:back"))
    await call.message.edit_reply_markup(reply_markup=kb.as_markup())
    await call.answer()


@router.callback_query(F.data.startswith("dasg:"))
async def draft_set_assignee(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    raw = call.data.split(":", 1)[1]
    await state.update_data(draft_assignee=None if raw == "none" else int(raw))
    await _edit_preview(call, session, state, i18n)
    await call.answer(i18n.get("toast-saved"))


# ── subscribers (multi-toggle) ───────────────────────────────


async def _sub_keyboard(session, state, i18n):
    data = await state.get_data()
    team = await project_team(session, data.get("draft_project_id"))
    selected = set(data.get("draft_subs") or [])
    kb = InlineKeyboardBuilder()
    for m in team:
        mark = "☑️ " if m.telegram_id in selected else "▫️ "
        kb.button(text=mark + m.display_name, callback_data=f"dsub:{m.telegram_id}")
    kb.adjust(2)
    kb.row(InlineKeyboardButton(text=i18n.get("btn-done"), callback_data="dft:back"))
    return kb.as_markup()


@router.callback_query(F.data == "dft:sub")
async def draft_show_subs(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    team = await project_team(session, (await state.get_data()).get("draft_project_id"))
    if not team:
        await call.answer(i18n.get("assign-no-team"), show_alert=True)
        return
    await call.message.edit_reply_markup(reply_markup=await _sub_keyboard(session, state, i18n))
    await call.answer()


@router.callback_query(F.data.startswith("dsub:"))
async def draft_toggle_sub(
    call: CallbackQuery, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    tg_id = int(call.data.split(":", 1)[1])
    data = await state.get_data()
    subs = list(data.get("draft_subs") or [])
    if tg_id in subs:
        subs.remove(tg_id)
    else:
        subs.append(tg_id)
    await state.update_data(draft_subs=subs)
    await call.message.edit_reply_markup(reply_markup=await _sub_keyboard(session, state, i18n))
    await call.answer()


# ── cancel / publish ─────────────────────────────────────────


@router.callback_query(F.data == "dft:cancel")
async def draft_cancel(call: CallbackQuery, state: FSMContext, i18n: I18nContext) -> None:
    await state.clear()
    await call.message.edit_text(i18n.get("draft-canceled"))
    await call.answer()


@router.callback_query(F.data == "dft:publish")
async def draft_publish(
    call: CallbackQuery,
    user: User,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    i18n: I18nContext,
) -> None:
    data = await state.get_data()
    project_id = data.get("draft_project_id")
    title = (data.get("draft_title") or "").strip()
    if not project_id or not title:
        await call.answer(i18n.get("draft-send-title"), show_alert=True)
        return
    if not await can_create_in(session, user, project_id):
        await call.answer(i18n.get("err-no-permission"), show_alert=True)
        return
    project = await get_project(session, project_id)
    if project is None or not project.team_id:
        await call.answer(i18n.get("err-no-projects"), show_alert=True)
        return

    client = await workspace.get_client(session)
    assignee = (
        await session.get(User, data["draft_assignee"]) if data.get("draft_assignee") else None
    )
    label_ids = None
    if assignee is not None and assignee.linear_label:
        label_ids = [await client.ensure_label(project.team_id, assignee.linear_label)]

    issue = await client.create_issue(
        title=title,
        team_id=project.team_id,
        description=(data.get("draft_desc") or "").strip() or None,
        project_id=project_id,
        label_ids=label_ids,
        actor_name=user.display_name,
        actor_icon=user.avatar_url,
    )
    # priority/dueDate aren't part of issueCreate input here — set them after.
    extra: dict = {}
    if data.get("draft_priority") is not None:
        extra["priority"] = data["draft_priority"]
    if data.get("draft_due"):
        extra["dueDate"] = data["draft_due"]
    if extra:
        await client.update_issue(issue["id"], **extra)

    session.add(
        IssueLink(
            linear_issue_id=issue["id"],
            linear_issue_identifier=issue["identifier"],
            telegram_chat_id=call.message.chat.id,
            telegram_message_id=call.message.message_id,
        )
    )

    # Subscriptions: assignee auto-follows, plus everyone explicitly added.
    sub_ids = set(data.get("draft_subs") or [])
    if assignee is not None:
        sub_ids.add(assignee.telegram_id)
    for sub_id in sub_ids:
        await subscribe(session, sub_id, issue["id"])
    await session.commit()
    await state.clear()

    await call.message.edit_text(
        i18n.get("task-created", identifier=issue["identifier"], url=issue["url"]),
        disable_web_page_preview=True,
    )
    await call.answer()

    # Notify assignee + subscribers in their own language.
    if assignee is not None:
        await _notify(
            bot, assignee, i18n,
            key="assigned-dm", identifier=issue["identifier"], title=title, by=user.display_name,
        )
    for sub_id in sub_ids:
        if assignee is not None and sub_id == assignee.telegram_id:
            continue
        target = await session.get(User, sub_id)
        if target is not None:
            await _notify(
                bot, target, i18n,
                key="sub-added-dm", identifier=issue["identifier"], by=user.display_name,
            )


async def _notify(bot: Bot, target: User, i18n: I18nContext, *, key: str, **kw) -> None:
    try:
        await bot.send_message(target.telegram_id, i18n.get(key, locale=target.lang, **kw))
    except Exception:  # noqa: BLE001 — user hasn't opened the bot, etc.
        pass
