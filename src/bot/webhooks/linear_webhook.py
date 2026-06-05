from __future__ import annotations

import hashlib
import hmac
import json
import logging

from aiohttp import web
from sqlalchemy import select

from bot.config import settings
from bot.db import ChatBinding, IssueLink, User, WebhookDedup
from bot.db.session import session_factory
from bot.keyboards.inline import open_card_button
from bot.middlewares.i18n import SUPPORTED_LOCALES
from bot.services.subscriptions import subscriber_ids

log = logging.getLogger(__name__)


async def _chat_locale(session, chat_id: int) -> str:
    """Group chats (negative id) always use English; a private chat id equals the
    user's Telegram id, so we render in that user's chosen language."""
    if chat_id < 0:
        return "en"
    user = await session.get(User, chat_id)
    if user is not None and user.lang in SUPPORTED_LOCALES:
        return user.lang
    return settings.default_lang


def _verify_signature(raw_body: bytes, signature: str | None) -> bool:
    if not settings.linear_webhook_secret:
        return True  # not configured (dev) — skip
    if not signature:
        return False
    digest = hmac.new(
        settings.linear_webhook_secret.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(digest, signature)


async def linear_webhook(request: web.Request) -> web.Response:
    """Handles Linear data-change events and forwards relevant ones to Telegram.

    Routing relies on IssueLink: an event about an issue we created from
    Telegram is echoed back into the originating chat."""
    raw = await request.read()
    if not _verify_signature(raw, request.headers.get("Linear-Signature")):
        return web.Response(status=401, text="bad signature")

    payload = json.loads(raw)
    delivery_id = str(payload.get("webhookId", "")) + str(payload.get("createdAt", ""))

    async with session_factory() as session:
        # Idempotency: drop duplicate deliveries.
        if delivery_id:
            if await session.get(WebhookDedup, delivery_id):
                return web.Response(text="dup")
            session.add(WebhookDedup(delivery_id=delivery_id))
            await session.commit()

        bot = request.app["bot"]
        i18n = request.app["i18n_core"]
        await _route_event(session, bot, i18n, payload)

    return web.Response(text="ok")


async def _announce_new_issue(session, bot, i18n, issue_id: str, data: dict) -> None:
    identifier = data.get("identifier", "")
    title = data.get("title", "")
    kb = open_card_button(issue_id, new=True)

    bindings = list(await session.scalars(select(ChatBinding)))
    for b in bindings:
        # Skip if this issue was already posted to this chat (e.g. bot created it here).
        exists = await session.scalar(
            select(IssueLink).where(
                IssueLink.linear_issue_id == issue_id,
                IssueLink.telegram_chat_id == b.telegram_chat_id,
            )
        )
        if exists is not None:
            continue
        if not b.announce:
            continue  # this group muted the bot
        locale = await _chat_locale(session, b.telegram_chat_id)
        text = i18n.get("notify-new-task", locale, identifier=identifier, title=title)
        try:
            sent = await bot.send_message(
                b.telegram_chat_id, text, reply_markup=kb, message_thread_id=b.thread_id
            )
        except Exception:  # noqa: BLE001
            log.warning("failed to announce new issue to %s", b.telegram_chat_id)
            continue
        session.add(
            IssueLink(
                linear_issue_id=issue_id,
                linear_issue_identifier=identifier,
                telegram_chat_id=b.telegram_chat_id,
                telegram_message_id=sent.message_id,
            )
        )
    await session.commit()


async def _route_event(session, bot, i18n, payload: dict) -> None:
    action = payload.get("action")
    entity_type = payload.get("type")
    data = payload.get("data", {})

    issue_id = data.get("issueId") if entity_type == "Comment" else data.get("id")
    if not issue_id:
        return

    # New task → announce to every bound group chat.
    if entity_type == "Issue" and action == "create":
        await _announce_new_issue(session, bot, i18n, issue_id, data)
        return

    if entity_type == "Comment" and action == "create":
        body = data.get("body", "")
        user = (data.get("user") or {}).get("name", "Linear")
        render = lambda loc: i18n.get("notify-comment", loc, user=user, body=body)  # noqa: E731
    elif entity_type == "Issue" and action == "update":
        state = (data.get("state") or {}).get("name", "?")
        ident = data.get("identifier", "")
        render = lambda loc: i18n.get("notify-status", loc, identifier=ident, state=state)  # noqa: E731
    else:
        return

    seen_chats: set[int] = set()

    # 1) Echo into the chat(s) where the issue was created from.
    links = list(
        await session.scalars(
            select(IssueLink).where(IssueLink.linear_issue_id == issue_id)
        )
    )
    for link in links:
        if link.telegram_chat_id in seen_chats:
            continue
        seen_chats.add(link.telegram_chat_id)
        if link.telegram_chat_id < 0:
            binding = await session.get(ChatBinding, link.telegram_chat_id)
            if binding is not None and not binding.announce:
                continue  # this group muted the bot
        locale = await _chat_locale(session, link.telegram_chat_id)
        try:
            await bot.send_message(
                link.telegram_chat_id, render(locale), reply_to_message_id=link.telegram_message_id
            )
        except Exception:  # noqa: BLE001
            log.warning("failed to deliver Linear event to %s", link.telegram_chat_id)

    # 2) DM every subscriber of this issue (a private chat id == the user id),
    #    each in their own chosen language.
    for tg_id in await subscriber_ids(session, issue_id):
        if tg_id in seen_chats:
            continue
        seen_chats.add(tg_id)
        try:
            await bot.send_message(tg_id, render(await _chat_locale(session, tg_id)))
        except Exception:  # noqa: BLE001
            log.warning("failed to deliver Linear event to subscriber %s", tg_id)
