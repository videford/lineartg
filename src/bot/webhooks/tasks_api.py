"""Generic task-creation API for other internal services (e.g. DevOps).

POST /create/linear/task
  Header: X-API-Token: <secret>            (TASKS_API_TOKEN, or FEEDBACK_API_TOKEN)
  Body:   { "title": "...",                 (required)
            "description": "...",            (optional)
            "photo": "data:image/...;base64,..." | "<base64>",  (optional)
            "project": "Bugs",               (optional project name → its team)
            "labels": ["x", "y"],            (optional)
            "priority": "high" | 0-4,        (optional)
            "due": "DD.MM.YYYY",             (optional)
            "author": "CI" }                 (optional, shown as the actor)
  → { "ok": true, "identifier": "FLO-42", "url": "https://linear.app/..." }

The caller never touches Linear credentials — the bot creates the issue with its
own OAuth token. The Linear webhook then announces it to bound Telegram groups.
"""
from __future__ import annotations

import logging

from aiohttp import web
from sqlalchemy import func, select

from bot.config import settings
from bot.dates import parse_date
from bot.db import Project
from bot.db.session import session_factory
from bot.services import workspace
from bot.webhooks.feedback import _decode_photo

log = logging.getLogger(__name__)

_PRIORITY = {"urgent": 1, "high": 2, "medium": 3, "low": 4, "none": 0}


def _secret() -> str:
    # A dedicated token if set, otherwise reuse the feedback secret.
    return settings.tasks_api_token or settings.feedback_api_token


async def create_linear_task(request: web.Request) -> web.Response:
    secret = _secret()
    if not secret:
        return web.json_response({"error": "tasks endpoint not configured"}, status=503)
    if request.headers.get("X-API-Token") != secret:
        return web.json_response({"error": "invalid X-API-Token"}, status=401)
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        return web.json_response({"error": "invalid json"}, status=400)

    title = str(body.get("title") or "").strip()
    if not title:
        return web.json_response({"error": "title is required"}, status=400)

    async with session_factory() as session:
        try:
            client = await workspace.get_client(session)
        except workspace.WorkspaceNotConnected:
            return web.json_response({"error": "linear not connected"}, status=503)

        # Optional project (by name) → its team; otherwise a default team.
        project_id = team_id = None
        pname = str(body.get("project") or "").strip()
        if pname:
            proj = await session.scalar(
                select(Project).where(
                    func.lower(Project.name) == pname.lower(),
                    Project.is_active.is_(True),
                )
            )
            if proj and proj.team_id:
                project_id, team_id = proj.id, proj.team_id
        if team_id is None:
            teams = await client.teams()
            if not teams:
                return web.json_response({"error": "no Linear team"}, status=502)
            team_id = teams[0]["id"]

        description = str(body.get("description") or "").strip()

        # Optional screenshot → uploaded to Linear and embedded inline.
        photo_raw = body.get("photo")
        if isinstance(photo_raw, str) and photo_raw:
            decoded = _decode_photo(photo_raw)
            if decoded:
                content, content_type = decoded
                try:
                    url = await client.upload_file(
                        content,
                        filename=body.get("photo_name") or "image.png",
                        content_type=content_type,
                    )
                    if url:
                        description = (description + f"\n\n![image]({url})").strip()
                except Exception:  # noqa: BLE001
                    log.warning("task photo upload failed", exc_info=True)

        label_ids: list[str] = []
        labels = body.get("labels")
        if isinstance(labels, list):
            for name in labels[:10]:
                try:
                    label_ids.append(await client.ensure_label(team_id, str(name)))
                except Exception:  # noqa: BLE001
                    log.warning("ensure_label failed for %r", name, exc_info=True)

        try:
            issue = await client.create_issue(
                title=title,
                team_id=team_id,
                description=description or None,
                project_id=project_id,
                label_ids=label_ids or None,
                actor_name=str(body.get("author") or "API"),
            )
            # priority/dueDate aren't part of issueCreate input — set them after.
            extra: dict = {}
            prio = body.get("priority")
            if isinstance(prio, str):
                prio = _PRIORITY.get(prio.strip().lower())
            if isinstance(prio, int) and not isinstance(prio, bool) and 0 <= prio <= 4:
                extra["priority"] = prio
            due = parse_date(str(body.get("due") or "")) if body.get("due") else None
            if due:
                extra["dueDate"] = due
            if extra:
                await client.update_issue(issue["id"], **extra)
        except Exception as exc:  # noqa: BLE001
            log.exception("task create failed")
            return web.json_response({"error": f"linear: {exc}"}, status=502)

    log.info("API task created: %s", issue.get("identifier"))
    return web.json_response(
        {"ok": True, "identifier": issue["identifier"], "url": issue["url"]}
    )
