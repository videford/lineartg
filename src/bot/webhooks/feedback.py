"""Website feedback → Linear task.

The colleague's site forwards structured feedback here (the same contract their
"report bot" already speaks): POST /report, header X-API-Token, JSON body
{ type, project, user{name,role?}, page, filters, env, message, tags[], photo? }.

We create a Linear issue from it (in the configured feedback project, with a
type label and the screenshot uploaded as an inline image). The existing Linear
webhook then announces the new issue to bound Telegram groups — so the task is
"published" automatically, no extra posting here.
"""
from __future__ import annotations

import base64
import binascii
import logging

from aiohttp import web
from sqlalchemy import func, select

from bot.config import settings
from bot.db import Project
from bot.db.session import session_factory
from bot.services import workspace

log = logging.getLogger(__name__)

# Feedback type → Linear label name.
TYPE_LABELS = {
    "bug": "bug",
    "idea": "idea",
    "improve": "improvement",
    "question": "question",
    "feedback": "feedback",
    "other": "feedback",
}
# Feedback type → title emoji (mirrors the colleague's registry).
TYPE_EMOJI = {
    "bug": "🐞", "idea": "💡", "improve": "💡",
    "question": "❓", "feedback": "💬", "other": "📋",
}


def _decode_photo(raw: str) -> tuple[bytes, str] | None:
    """Return (bytes, content_type) from a base64 / data-URL string, or None."""
    data = raw.strip()
    content_type = "image/png"
    if data.startswith("data:"):
        head, _, rest = data.partition(",")
        if ";" in head:
            content_type = head[5 : head.index(";")] or content_type
        data = rest
    try:
        decoded = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError):
        return None
    return (decoded, content_type) if decoded else None


def _build_description(payload: dict, message: str, screenshot_url: str | None) -> str:
    lines = [message, "", "──────────"]
    lines.append(f"Тип: {payload.get('type', 'other')}")
    if payload.get("project"):
        lines.append(f"Проект: {payload['project']}")
    if payload.get("page"):
        lines.append(f"Страница: {payload['page']}")
    filters = payload.get("filters")
    if isinstance(filters, dict) and filters:
        lines.append("Фильтры: " + ", ".join(f"{k}={v}" for k, v in filters.items()))
    env = payload.get("env")
    if isinstance(env, dict) and env:
        lines.append("Окружение: " + ", ".join(f"{k}={v}" for k, v in env.items()))
    user = payload.get("user")
    if isinstance(user, dict) and user.get("name"):
        who = user["name"] + (f" ({user['role']})" if user.get("role") else "")
        lines.append(f"Отправитель: {who}")
    tags = payload.get("tags")
    if isinstance(tags, list) and tags:
        lines.append("Теги: " + " ".join(f"#{str(t).lstrip('#')}" for t in tags))
    if screenshot_url:
        lines += ["", f"![screenshot]({screenshot_url})"]
    return "\n".join(lines)


async def feedback_report(request: web.Request) -> web.Response:
    if not settings.feedback_api_token:
        return web.json_response({"error": "feedback endpoint not configured"}, status=503)
    if request.headers.get("X-API-Token") != settings.feedback_api_token:
        return web.json_response({"error": "invalid X-API-Token"}, status=401)
    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        return web.json_response({"error": "invalid json"}, status=400)

    message = str(payload.get("message") or "").strip()
    if not message:
        return web.json_response({"error": "empty message"}, status=400)

    async with session_factory() as session:
        try:
            client = await workspace.get_client(session)
        except workspace.WorkspaceNotConnected:
            return web.json_response({"error": "linear not connected"}, status=503)

        # Destination: the configured feedback project (fallback: no project).
        proj = await session.scalar(
            select(Project).where(
                func.lower(Project.name) == settings.feedback_project_name.lower(),
                Project.is_active.is_(True),
            )
        )
        project_id = proj.id if proj and proj.team_id else None
        team_id = proj.team_id if proj and proj.team_id else None
        if team_id is None:
            teams = await client.teams()
            if not teams:
                return web.json_response({"error": "no Linear team"}, status=502)
            team_id = teams[0]["id"]

        # Screenshot → upload to Linear, embed as an inline image.
        screenshot_url = None
        photo_raw = payload.get("photo")
        if isinstance(photo_raw, str) and photo_raw:
            decoded = _decode_photo(photo_raw)
            if decoded:
                content, content_type = decoded
                try:
                    screenshot_url = await client.upload_file(
                        content,
                        filename=payload.get("photo_name") or "screenshot.png",
                        content_type=content_type,
                    )
                except Exception:  # noqa: BLE001 — never fail the report over a screenshot
                    log.warning("feedback screenshot upload failed", exc_info=True)

        rtype = str(payload.get("type") or "other").lower()
        title = f"{TYPE_EMOJI.get(rtype, '📋')} {message.splitlines()[0][:100]}"
        description = _build_description(payload, message, screenshot_url)

        label_ids: list[str] = []
        try:
            label_ids.append(await client.ensure_label(team_id, TYPE_LABELS.get(rtype, "feedback")))
        except Exception:  # noqa: BLE001
            log.warning("feedback label ensure failed", exc_info=True)

        reporter = None
        if isinstance(payload.get("user"), dict):
            reporter = payload["user"].get("name")

        try:
            issue = await client.create_issue(
                title=title,
                team_id=team_id,
                description=description,
                project_id=project_id,
                label_ids=label_ids or None,
                actor_name=reporter or "Website feedback",
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("feedback issue create failed")
            return web.json_response({"error": f"linear: {exc}"}, status=502)

    log.info("feedback → created %s", issue.get("identifier"))
    return web.json_response(
        {"ok": True, "identifier": issue["identifier"], "url": issue["url"], "message_id": 0}
    )
