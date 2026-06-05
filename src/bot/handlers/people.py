"""Company people directory: browse all members, open a member's profile with
their current task, recently completed tasks, tasks they follow (but don't own),
and a Telegram deep-link to message them.
"""
from __future__ import annotations

import html

import httpx
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import User
from bot.services import workspace
from bot.services.status import describe_status
from bot.services.subscriptions import subscriptions_of
from bot.services.users import OWNER_PREFIX, list_members

router = Router(name="people")

MAX_SUBS = 10


async def cmd_people(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> None:
    await _render_list(message, session, i18n, edit=False)


async def _render_list(
    target: Message, session: AsyncSession, i18n: I18nContext, *, edit: bool
) -> None:
    members = await list_members(session)
    kb = InlineKeyboardBuilder()
    for m in members:
        kb.button(text=m.display_name, callback_data=f"ppl:{m.telegram_id}")
    kb.adjust(2)
    text = i18n.get("people-title", n=len(members))
    if edit:
        await target.edit_text(text, reply_markup=kb.as_markup())
    else:
        await target.answer(text, reply_markup=kb.as_markup())


@router.callback_query(F.data == "ppl:list")
async def people_back(call: CallbackQuery, session: AsyncSession, i18n: I18nContext) -> None:
    await _render_list(call.message, session, i18n, edit=True)
    await call.answer()


def _tg_link(target: User) -> str:
    if target.username:
        return f'<a href="https://t.me/{target.username}">✍️ {target.display_name}</a>'
    return f'<a href="tg://user?id={target.telegram_id}">✍️ {target.display_name}</a>'


def _line(issue: dict) -> str:
    state = (issue.get("state") or {}).get("name", "")
    return f"• <b>{html.escape(issue['identifier'])}</b> · {html.escape(issue['title'])} — {html.escape(state)}"


@router.callback_query(F.data.startswith("ppl:"))
async def people_profile(
    call: CallbackQuery, session: AsyncSession, i18n: I18nContext
) -> None:
    tg_id = int(call.data.split(":", 1)[1])
    target = await session.get(User, tg_id)
    if target is None:
        await call.answer(i18n.get("err-unknown-member"), show_alert=True)
        return

    status = await describe_status(session, target, i18n)
    lines = [f"<b>{html.escape(target.display_name)}</b>", status, _tg_link(target)]

    try:
        client = await workspace.get_client(session)
        own = await client.issues_by_label(target.linear_label) if target.linear_label else []
        current = [i for i in own if (i.get("state") or {}).get("type") == "started"]

        # Followed-but-not-owner: subscriptions where target isn't the assignee.
        followed: list[dict] = []
        for issue_id in (await subscriptions_of(session, tg_id))[:MAX_SUBS]:
            issue = await client.get_issue(issue_id)
            if not issue:
                continue
            owner_labels = [
                lb["name"]
                for lb in (issue.get("labels") or {}).get("nodes", [])
                if lb["name"].startswith(OWNER_PREFIX)
            ]
            if target.linear_label and target.linear_label in owner_labels:
                continue
            followed.append(issue)
    except (workspace.WorkspaceNotConnected, httpx.HTTPError):
        # Linear unreachable or token expired/revoked — show profile basics only.
        lines.append("─────────")
        lines.append(i18n.get("people-linear-unavailable"))
        kb = InlineKeyboardBuilder()
        kb.button(text=i18n.get("nav-back"), callback_data="ppl:list")
        await call.message.edit_text(
            "\n".join(lines), reply_markup=kb.as_markup(), disable_web_page_preview=True
        )
        await call.answer()
        return

    lines.append("─────────")
    lines.append("<b>" + i18n.get("people-current") + "</b>")
    lines += [_line(i) for i in current] or ["—"]
    lines.append("<b>" + i18n.get("people-following") + "</b>")
    lines += [_line(i) for i in followed] or ["—"]

    kb = InlineKeyboardBuilder()
    # one openable button per listed task (opens the card as a new message)
    for issue in [*current, *followed]:
        kb.button(
            text=f"📋 {issue['identifier']} · {issue['title']}"[:60],
            callback_data=f"ocard:{issue['id']}",
        )
    kb.adjust(1)
    kb.button(text=i18n.get("nav-back"), callback_data="ppl:list")
    await call.message.edit_text(
        "\n".join(lines), reply_markup=kb.as_markup(), disable_web_page_preview=True
    )
    await call.answer()
