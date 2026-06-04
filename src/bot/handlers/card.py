"""Interactive task card: view + field editing, gated by project-scoped perms.

The active card's issue_id is stored in FSM data (`card_issue`) because Linear
issue IDs are UUIDs and two of them would blow Telegram's 64-byte callback
limit. Action callbacks therefore carry only short secondary values.
"""
from __future__ import annotations

import html
from datetime import date, timedelta

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import User
from bot.keyboards.inline import (
    card_keyboard,
    due_keyboard,
    edit_menu_keyboard,
    estimate_keyboard,
    labels_keyboard,
    members_keyboard,
    priority_keyboard,
    states_keyboard,
)
from bot.linear import LinearClient
from bot.services import workspace
from bot.services.permissions import can_manage_task
from bot.services.projects import is_project_team, project_team
from bot.services.subscriptions import is_subscribed, subscribe, unsubscribe
from bot.services.users import OWNER_PREFIX
from bot.states import Card

router = Router(name="card")


# ── helpers ──────────────────────────────────────────────────


def _owner_labels(issue: dict) -> list[str]:
    return [
        lb["name"]
        for lb in (issue.get("labels") or {}).get("nodes", [])
        if lb["name"].startswith(OWNER_PREFIX)
    ]


def _format_card(issue: dict) -> str:
    owners = ", ".join(o[len(OWNER_PREFIX):] for o in _owner_labels(issue)) or "—"
    other_labels = [
        lb["name"]
        for lb in (issue.get("labels") or {}).get("nodes", [])
        if not lb["name"].startswith(OWNER_PREFIX)
    ]
    desc = (issue.get("description") or "").strip()
    if len(desc) > 500:
        desc = desc[:500] + "…"

    lines = [
        f"<b>{html.escape(issue['identifier'])}</b> · {html.escape(issue['title'])}",
        f"Статус: {issue['state']['name']} · Приоритет: {issue.get('priorityLabel') or '—'}",
        f"Проект: {html.escape((issue.get('project') or {}).get('name', '—'))} · Owner: {html.escape(owners)}",
        f"Дедлайн: {issue.get('dueDate') or '—'} · Оценка: {issue.get('estimate') if issue.get('estimate') is not None else '—'}",
    ]
    if other_labels:
        lines.append("Метки: " + ", ".join(html.escape(x) for x in other_labels))
    if desc:
        lines.append("─────────")
        lines.append(html.escape(desc))
    comments = (issue.get("comments") or {}).get("nodes", [])
    if comments:
        lines.append("─────────")
        for c in comments:
            who = html.escape((c.get("user") or {}).get("name", "?"))
            body = html.escape((c.get("body") or "").strip())
            if len(body) > 200:
                body = body[:200] + "…"
            lines.append(f"💬 <b>{who}</b>: {body}")
    return "\n".join(lines)


async def _render(
    *,
    call: CallbackQuery | None,
    message: Message | None,
    issue_id: str,
    user: User,
    session: AsyncSession,
    state: FSMContext,
    i18n: I18nContext,
    client: LinearClient | None = None,
) -> None:
    if client is None:
        client = await workspace.get_client(session)
    issue = await client.get_issue(issue_id)
    if issue is None:
        target = call.message if call else message
        await target.answer(i18n.get("card-not-found"))
        return

    project_id = (issue.get("project") or {}).get("id")
    manage = await can_manage_task(session, user, project_id)
    # Anyone can view a card, comment and subscribe; only managers edit/status/assign.

    await state.set_data(
        {
            "card_issue": issue_id,
            "card_team": (issue.get("team") or {}).get("id"),
            "card_project": project_id,
        }
    )
    await state.set_state(None)

    subscribed = await is_subscribed(session, user.telegram_id, issue_id)
    text = _format_card(issue)
    kb = card_keyboard(
        issue["url"], can_manage=manage, can_comment=True, subscribed=subscribed
    )
    if call is not None:
        try:
            await call.message.edit_text(text, reply_markup=kb)
        except Exception:  # noqa: BLE001 — message unchanged / not editable
            await call.message.answer(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


async def _active(state: FSMContext) -> tuple[str | None, str | None, str | None]:
    data = await state.get_data()
    return data.get("card_issue"), data.get("card_team"), data.get("card_project")


async def _guard_manage(
    call: CallbackQuery, session: AsyncSession, user: User, project_id: str | None, i18n
) -> bool:
    if await can_manage_task(session, user, project_id):
        return True
    await call.answer(i18n.get("err-no-permission"), show_alert=True)
    return False


# ── open / refresh ───────────────────────────────────────────


@router.callback_query(F.data.startswith("card:"))
async def open_card(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id = call.data.split(":", 1)[1]
    await _render(call=call, message=None, issue_id=issue_id, user=user, session=session, state=state, i18n=i18n)
    await call.answer()


@router.callback_query(F.data == "act:refresh")
async def refresh_card(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, _, _ = await _active(state)
    if not issue_id:
        await call.answer()
        return
    await _render(call=call, message=None, issue_id=issue_id, user=user, session=session, state=state, i18n=i18n)
    await call.answer()


# ── status ───────────────────────────────────────────────────


@router.callback_query(F.data == "act:status")
async def show_status(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, team_id, project_id = await _active(state)
    if not issue_id or not await _guard_manage(call, session, user, project_id, i18n):
        return
    client = await workspace.get_client(session)
    states = await client.workflow_states(team_id)
    await call.message.edit_reply_markup(reply_markup=states_keyboard(states))
    await call.answer()


@router.callback_query(F.data.startswith("st:"))
async def set_status(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, _, project_id = await _active(state)
    if not issue_id or not await _guard_manage(call, session, user, project_id, i18n):
        return
    state_id = call.data.split(":", 1)[1]
    client = await workspace.get_client(session)
    await client.update_issue_state(issue_id, state_id)
    await _render(call=call, message=None, issue_id=issue_id, user=user, session=session, state=state, i18n=i18n, client=client)
    await call.answer(i18n.get("toast-saved"))


# ── edit menu ────────────────────────────────────────────────


@router.callback_query(F.data == "act:edit")
async def edit_menu(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, _, project_id = await _active(state)
    if not issue_id or not await _guard_manage(call, session, user, project_id, i18n):
        return
    await call.message.edit_reply_markup(reply_markup=edit_menu_keyboard())
    await call.answer()


@router.callback_query(F.data == "ed:title")
async def edit_title(call: CallbackQuery, state: FSMContext, i18n: I18nContext) -> None:
    await state.set_state(Card.waiting_title)
    await call.message.answer(i18n.get("edit-send-title"))
    await call.answer()


@router.callback_query(F.data == "ed:desc")
async def edit_desc(call: CallbackQuery, state: FSMContext, i18n: I18nContext) -> None:
    await state.set_state(Card.waiting_desc)
    await call.message.answer(i18n.get("edit-send-desc"))
    await call.answer()


@router.message(Card.waiting_title)
async def title_received(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, _, project_id = await _active(state)
    if not issue_id or not await can_manage_task(session, user, project_id):
        await message.answer(i18n.get("err-no-permission"))
        return
    client = await workspace.get_client(session)
    await client.update_issue(issue_id, title=(message.text or "").strip())
    await _render(call=None, message=message, issue_id=issue_id, user=user, session=session, state=state, i18n=i18n, client=client)


@router.message(Card.waiting_desc)
async def desc_received(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, _, project_id = await _active(state)
    if not issue_id or not await can_manage_task(session, user, project_id):
        await message.answer(i18n.get("err-no-permission"))
        return
    client = await workspace.get_client(session)
    await client.update_issue(issue_id, description=message.text or "")
    await _render(call=None, message=message, issue_id=issue_id, user=user, session=session, state=state, i18n=i18n, client=client)


# ── priority / estimate / due ────────────────────────────────


@router.callback_query(F.data == "ed:prio")
async def show_priority(call: CallbackQuery, state: FSMContext, i18n: I18nContext) -> None:
    issue_id, _, _ = await _active(state)
    if not issue_id:
        await call.answer()
        return
    await call.message.edit_reply_markup(reply_markup=priority_keyboard())
    await call.answer()


@router.callback_query(F.data.startswith("pr:"))
async def set_priority(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, _, project_id = await _active(state)
    if not issue_id or not await _guard_manage(call, session, user, project_id, i18n):
        return
    client = await workspace.get_client(session)
    await client.update_issue(issue_id, priority=int(call.data.split(":", 1)[1]))
    await _render(call=call, message=None, issue_id=issue_id, user=user, session=session, state=state, i18n=i18n, client=client)
    await call.answer(i18n.get("toast-saved"))


@router.callback_query(F.data == "ed:est")
async def show_estimate(call: CallbackQuery, state: FSMContext, i18n: I18nContext) -> None:
    issue_id, _, _ = await _active(state)
    if not issue_id:
        await call.answer()
        return
    await call.message.edit_reply_markup(reply_markup=estimate_keyboard())
    await call.answer()


@router.callback_query(F.data.startswith("es:"))
async def set_estimate(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, _, project_id = await _active(state)
    if not issue_id or not await _guard_manage(call, session, user, project_id, i18n):
        return
    raw = call.data.split(":", 1)[1]
    value = None if raw == "none" else int(raw)
    client = await workspace.get_client(session)
    await client.update_issue(issue_id, estimate=value)
    await _render(call=call, message=None, issue_id=issue_id, user=user, session=session, state=state, i18n=i18n, client=client)
    await call.answer(i18n.get("toast-saved"))


@router.callback_query(F.data == "ed:due")
async def show_due(call: CallbackQuery, state: FSMContext, i18n: I18nContext) -> None:
    issue_id, _, _ = await _active(state)
    if not issue_id:
        await call.answer()
        return
    await call.message.edit_reply_markup(reply_markup=due_keyboard())
    await call.answer()


@router.callback_query(F.data.startswith("du:"))
async def set_due(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, _, project_id = await _active(state)
    if not issue_id or not await _guard_manage(call, session, user, project_id, i18n):
        return
    raw = call.data.split(":", 1)[1]
    value = None if raw == "none" else (date.today() + timedelta(days=int(raw))).isoformat()
    client = await workspace.get_client(session)
    await client.update_issue(issue_id, dueDate=value)
    await _render(call=call, message=None, issue_id=issue_id, user=user, session=session, state=state, i18n=i18n, client=client)
    await call.answer(i18n.get("toast-saved"))


# ── labels (multi-toggle) ────────────────────────────────────


@router.callback_query(F.data == "ed:lbl")
async def show_labels(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, team_id, project_id = await _active(state)
    if not issue_id or not await _guard_manage(call, session, user, project_id, i18n):
        return
    client = await workspace.get_client(session)
    issue = await client.get_issue(issue_id)
    team_labels = await client.labels(team_id)
    selected = {lb["id"] for lb in (issue.get("labels") or {}).get("nodes", [])}
    await call.message.edit_reply_markup(reply_markup=labels_keyboard(team_labels, selected))
    await call.answer()


@router.callback_query(F.data.startswith("lb:"))
async def toggle_label(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, team_id, project_id = await _active(state)
    if not issue_id or not await _guard_manage(call, session, user, project_id, i18n):
        return
    label_id = call.data.split(":", 1)[1]
    client = await workspace.get_client(session)
    issue = await client.get_issue(issue_id)
    current = {lb["id"] for lb in (issue.get("labels") or {}).get("nodes", [])}
    if label_id in current:
        current.discard(label_id)
    else:
        current.add(label_id)
    await client.update_issue(issue_id, labelIds=list(current))
    team_labels = await client.labels(team_id)
    await call.message.edit_reply_markup(reply_markup=labels_keyboard(team_labels, current))
    await call.answer(i18n.get("toast-saved"))


# ── reassign owner (label-based) ─────────────────────────────


@router.callback_query(F.data == "act:assign")
async def show_assign(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, _, project_id = await _active(state)
    if not issue_id or not await _guard_manage(call, session, user, project_id, i18n):
        return
    team = await project_team(session, project_id)
    if not team:
        await call.answer(i18n.get("assign-no-team"), show_alert=True)
        return
    await call.message.edit_reply_markup(reply_markup=members_keyboard(team, prefix="ra"))
    await call.answer()


@router.callback_query(F.data.startswith("ra:"))
async def reassign(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, team_id, project_id = await _active(state)
    if not issue_id or not await _guard_manage(call, session, user, project_id, i18n):
        return
    target = await session.get(User, int(call.data.split(":", 1)[1]))
    if target is None:
        await call.answer(i18n.get("err-unknown-member"), show_alert=True)
        return
    if not await is_project_team(session, target.telegram_id, project_id):
        await call.answer(i18n.get("assign-not-in-team"), show_alert=True)
        return
    client = await workspace.get_client(session)
    issue = await client.get_issue(issue_id)
    # Replace any existing owner labels with the new owner's label.
    kept = [
        lb["id"]
        for lb in (issue.get("labels") or {}).get("nodes", [])
        if not lb["name"].startswith(OWNER_PREFIX)
    ]
    new_owner = await client.ensure_label(team_id, target.linear_label)
    await client.update_issue(issue_id, labelIds=[*kept, new_owner])
    await _render(call=call, message=None, issue_id=issue_id, user=user, session=session, state=state, i18n=i18n, client=client)
    await call.answer(i18n.get("toast-saved"))


# ── subscriptions ────────────────────────────────────────────


@router.callback_query(F.data == "act:subtoggle")
async def toggle_subscription(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, _, _ = await _active(state)
    if not issue_id:
        await call.answer()
        return
    if await is_subscribed(session, user.telegram_id, issue_id):
        await unsubscribe(session, user.telegram_id, issue_id)
        toast = i18n.get("sub-off")
    else:
        await subscribe(session, user.telegram_id, issue_id)
        toast = i18n.get("sub-on")
    await _render(call=call, message=None, issue_id=issue_id, user=user, session=session, state=state, i18n=i18n)
    await call.answer(toast)


@router.callback_query(F.data == "act:subother")
async def subother_list(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, _, project_id = await _active(state)
    if not issue_id or not await _guard_manage(call, session, user, project_id, i18n):
        return
    team = await project_team(session, project_id)
    if not team:
        await call.answer(i18n.get("assign-no-team"), show_alert=True)
        return
    await call.message.edit_reply_markup(reply_markup=members_keyboard(team, prefix="subu"))
    await call.answer()


@router.callback_query(F.data.startswith("subu:"))
async def subscribe_other(
    call: CallbackQuery,
    user: User,
    session: AsyncSession,
    state: FSMContext,
    bot: Bot,
    i18n: I18nContext,
) -> None:
    issue_id, _, project_id = await _active(state)
    if not issue_id or not await _guard_manage(call, session, user, project_id, i18n):
        return
    target = await session.get(User, int(call.data.split(":", 1)[1]))
    if target is None:
        await call.answer(i18n.get("err-unknown-member"), show_alert=True)
        return
    added = await subscribe(session, target.telegram_id, issue_id)
    if added:
        issue = await (await workspace.get_client(session)).get_issue(issue_id)
        ident = issue["identifier"] if issue else ""
        try:
            await bot.send_message(
                target.telegram_id,
                i18n.get("sub-added-dm", identifier=ident, by=user.display_name, locale=target.lang),
            )
        except Exception:  # noqa: BLE001
            pass
    await _render(call=call, message=None, issue_id=issue_id, user=user, session=session, state=state, i18n=i18n)
    await call.answer(i18n.get("sub-other-done", name=target.display_name))


# ── comment ──────────────────────────────────────────────────


@router.callback_query(F.data == "act:comment")
async def start_comment(
    call: CallbackQuery, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, _, _ = await _active(state)
    if not issue_id:
        await call.answer()
        return
    # Anyone can comment.
    await state.set_state(Card.waiting_comment)
    await call.message.answer(i18n.get("comment-prompt"))
    await call.answer()


@router.message(Card.waiting_comment)
async def comment_received(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    issue_id, _, _ = await _active(state)
    if not issue_id:
        return
    client = await workspace.get_client(session)
    await client.create_comment(
        issue_id=issue_id,
        body=message.text or "",
        actor_name=user.display_name,
        actor_icon=user.avatar_url,
    )
    await message.answer(i18n.get("comment-added"))
    await _render(call=None, message=message, issue_id=issue_id, user=user, session=session, state=state, i18n=i18n, client=client)
