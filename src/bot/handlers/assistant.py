"""Free-text AI assistant (DM only).

Any plain message in DM that no command / menu button / active flow handled is
routed here. The assistant can answer questions about tasks (read-only tools) and
propose new tasks. Crucially, creating a task does NOT write to Linear directly —
it seeds the existing draft preview, so the user still reviews and presses
Publish. All tools run through our own functions with the same permission checks,
so the model can never bypass roles.
"""
from __future__ import annotations

import json
import logging
from datetime import date

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.ai import run_agent
from bot.config import settings
from bot.dates import fmt_date, parse_date
from bot.db import User
from bot.handlers import draft as draft_h
from bot.services import workspace
from bot.services.permissions import can_create_in, can_manage_task
from bot.services.projects import creatable_projects
from bot.services.users import OWNER_PREFIX, list_members

log = logging.getLogger(__name__)

MAX_HISTORY = 8  # remembered messages (≈4 exchanges) for conversation context
MAX_BUTTONS = 12  # open-buttons attached under a task-listing answer
CLOSED = {"completed", "canceled"}
_PRIORITY_WORDS = {
    "urgent": 1, "срочно": 1, "срочный": 1, "shoshilinch": 1,
    "high": 2, "высокий": 2, "yuqori": 2,
    "medium": 3, "средний": 3, "oʻrta": 3, "orta": 3,
    "low": 4, "низкий": 4, "past": 4,
    "none": 0, "нет": 0, "yoʻq": 0,
}

TOOLS = [
    {
        "name": "search_tasks",
        "description": "Full-text search for tasks/issues by a keyword or phrase.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search text"}},
            "required": ["query"],
        },
    },
    {
        "name": "list_tasks",
        "description": (
            "List tasks filtered by assignee and status. Use this for questions "
            "like 'what am I working on', 'open tasks of <person>', 'unassigned tasks'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "assignee": {
                    "type": "string",
                    "description": "'me', a person's name, 'unassigned', or 'any'",
                },
                "status": {
                    "type": "string",
                    "enum": ["open", "in_progress", "todo", "done", "any"],
                    "description": "Status filter; default 'open'",
                },
            },
        },
    },
    {
        "name": "create_task",
        "description": (
            "Propose a NEW task. This opens a preview card for the user to review "
            "and publish — it does not create the task immediately. Only call when "
            "the user clearly wants to create/add a task."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "assignee": {"type": "string", "description": "'me', 'none', or a person's name"},
                "due": {"type": "string", "description": "Due date as DD.MM.YYYY"},
                "priority": {"type": "string", "description": "urgent/high/medium/low/none"},
                "project": {"type": "string", "description": "Project name (optional)"},
            },
            "required": ["title"],
        },
    },
]


def _owner_labels(issue: dict) -> list[str]:
    return [
        lb["name"]
        for lb in (issue.get("labels") or {}).get("nodes", [])
        if lb["name"].startswith(OWNER_PREFIX)
    ]


def _brief(issue: dict, label_to_name: dict[str, str]) -> dict:
    owners = [label_to_name.get(lb, lb[len(OWNER_PREFIX):]) for lb in _owner_labels(issue)]
    return {
        "identifier": issue.get("identifier"),
        "title": issue.get("title"),
        "status": (issue.get("state") or {}).get("name"),
        "assignee": ", ".join(owners) or "unassigned",
        "due": fmt_date(issue["dueDate"]) if issue.get("dueDate") else None,
        "url": issue.get("url"),
    }


def _keep_status(issue: dict, status: str) -> bool:
    t = (issue.get("state") or {}).get("type")
    if status == "in_progress":
        return t == "started"
    if status == "todo":
        return t in ("unstarted", "backlog", "triage")
    if status == "done":
        return t == "completed"
    if status == "any":
        return True
    return t not in CLOSED  # "open" (default)


async def handle(
    message: Message, user: User, session: AsyncSession, state: FSMContext, i18n: I18nContext
) -> bool:
    """Try to answer with the AI assistant. Returns True if handled (so the caller
    skips its own fallback), False if the assistant is disabled/unavailable."""
    if not settings.ai_enabled:
        return False
    text = (message.text or "").strip()
    if not text:
        return False
    try:
        client = await workspace.get_client(session)
    except workspace.WorkspaceNotConnected:
        return False  # nothing useful to do without Linear; fall back to menu

    members = await list_members(session)
    label_to_name = {m.linear_label: m.display_name for m in members if m.linear_label}
    projects = await creatable_projects(session, user)

    ctx: dict = {"draft": None, "shown": [], "shown_ids": set()}

    def _record(issues: list[dict]) -> None:
        for i in issues:
            iid = i.get("id")
            if iid and iid not in ctx["shown_ids"]:
                ctx["shown_ids"].add(iid)
                ctx["shown"].append((iid, i.get("identifier") or "?"))

    async def execute(name: str, args: dict) -> str:
        try:
            if name == "search_tasks":
                issues = (await client.search_issues(args.get("query", "")))[:20]
                _record(issues)
                return json.dumps([_brief(i, label_to_name) for i in issues], ensure_ascii=False)

            if name == "list_tasks":
                issues = await _list_tasks_issues(client, user, members, args)
                if issues is None:
                    return json.dumps({"error": f"no person matching '{args.get('assignee')}'"})
                issues = issues[:30]
                _record(issues)
                return json.dumps([_brief(i, label_to_name) for i in issues], ensure_ascii=False)

            if name == "create_task":
                return await _prepare_draft(session, user, projects, ctx, args)
        except Exception as exc:  # noqa: BLE001
            log.exception("AI tool %s failed", name)
            return json.dumps({"error": str(exc)})
        return json.dumps({"error": f"unknown tool {name}"})

    system = _system_prompt(user, projects, members)
    try:
        await message.bot.send_chat_action(message.chat.id, "typing")
    except Exception:  # noqa: BLE001
        pass

    history = (await state.get_data()).get("ai_history") or []
    answer = await run_agent(system, text, TOOLS, execute, history=history)

    # A task was proposed → open the existing draft preview for confirmation.
    if ctx["draft"]:
        await _remember(state, history, text, "(подготовил черновик задачи)")
        await state.update_data(**ctx["draft"])
        await draft_h._open_preview_new(message, session, state, i18n)
        return True

    if answer:
        # Open-buttons for the tasks surfaced by the tools (numbered text + jump).
        kb = None
        if ctx["shown"]:
            builder = InlineKeyboardBuilder()
            for iid, ident in ctx["shown"][:MAX_BUTTONS]:
                builder.button(text=ident, callback_data=f"ocard:{iid}")
            builder.adjust(3)
            kb = builder.as_markup()
        await _remember(state, history, text, answer)
        # parse_mode=None: the model replies in plain text, so Markdown like **x**
        # isn't rendered literally by the HTML default parser.
        await message.answer(answer, reply_markup=kb, parse_mode=None, disable_web_page_preview=True)
        return True
    # Errored or produced nothing (e.g. a 429/quota) — fall back to the menu
    # (caller shows it) just like before the assistant existed.
    return False


async def _remember(state: FSMContext, history: list[dict], user_text: str, reply: str) -> None:
    new_history = (
        history + [{"role": "user", "content": user_text}, {"role": "assistant", "content": reply}]
    )[-MAX_HISTORY:]
    await state.update_data(ai_history=new_history)


async def _list_tasks_issues(client, user, members, args) -> list[dict] | None:
    """Return matching issues (status-filtered), or None if a named person had no
    match. Serialization happens in the caller so it can also record ids."""
    assignee = (args.get("assignee") or "any").strip()
    status = (args.get("status") or "open").strip()
    low = assignee.lower()

    if low == "me":
        issues = await client.issues_by_label(user.linear_label) if user.linear_label else []
    elif low in ("", "any"):
        issues = await client.all_issues()
    elif low == "unassigned":
        issues = [i for i in await client.all_issues() if not _owner_labels(i)]
    else:
        match = next(
            (m for m in members if m.linear_label and low in m.display_name.lower()), None
        )
        if match is None:
            return None
        issues = await client.issues_by_label(match.linear_label)

    return [i for i in issues if _keep_status(i, status)]


async def _prepare_draft(session, user, projects, ctx, args) -> str:
    title = (args.get("title") or "").strip()
    if not title:
        return json.dumps({"error": "title is required"})
    if not projects:
        return json.dumps({"error": "you cannot create tasks (ask an admin to add you to a project)"})

    # Resolve the project.
    name = (args.get("project") or "").strip().lower()
    if name:
        proj = next((p for p in projects if name in p.name.lower()), None)
    elif len(projects) == 1:
        proj = projects[0]
    else:
        proj = None
    if proj is None:
        return json.dumps(
            {"error": "which project?", "projects": [p.name for p in projects]}
        )
    if not proj.team_id or not await can_create_in(session, user, proj.id):
        return json.dumps({"error": "no permission to create in this project"})

    is_manager = await can_manage_task(session, user, proj.id)
    # Assignee: members may only assign themselves or leave it unassigned.
    raw_assignee = (args.get("assignee") or "").strip().lower()
    assignee_id = None
    if raw_assignee in ("me", "self", "я", "men"):
        assignee_id = user.telegram_id
    elif raw_assignee not in ("", "none", "no", "нет", "yoʻq"):
        if is_manager:
            members = await list_members(session)
            m = next((x for x in members if raw_assignee in x.display_name.lower()), None)
            assignee_id = m.telegram_id if m else None
        elif raw_assignee in user.display_name.lower():
            assignee_id = user.telegram_id

    due_iso = parse_date(args.get("due", "")) if args.get("due") else None
    prio_raw = (args.get("priority") or "").strip().lower()
    priority = _PRIORITY_WORDS.get(prio_raw)
    if priority is None and prio_raw.isdigit() and 0 <= int(prio_raw) <= 4:
        priority = int(prio_raw)

    ctx["draft"] = {
        "draft_project_id": proj.id,
        "draft_team_id": proj.team_id,
        "draft_project_name": proj.name,
        "draft_title": title,
        "draft_desc": (args.get("description") or "").strip(),
        "draft_priority": priority,
        "draft_due": due_iso,
        "draft_assignee": assignee_id,
        "draft_subs": [],
        "draft_state_id": None,
        "draft_state_name": None,
        "draft_label_ids": [],
        "draft_label_names": {},
        "editing": False,
    }
    return json.dumps({"ok": True, "note": "Draft prepared; the user will review and publish."})


def _system_prompt(user: User, projects, members) -> str:
    today = date.today().strftime("%d.%m.%Y")
    proj_names = ", ".join(p.name for p in projects) or "(none — user can't create tasks)"
    people = ", ".join(m.display_name for m in members) or "(none)"
    return (
        "You are a task assistant for a team that works in Linear via this Telegram bot.\n"
        f"Today is {today}. Dates use DD.MM.YYYY.\n"
        f"You are talking to {user.display_name} (role: {user.role.value}, language: {user.lang}).\n"
        f"Reply in the user's language ({user.lang}). Be concise and friendly.\n"
        f"Projects the user can create tasks in: {proj_names}.\n"
        f"Team members: {people}.\n\n"
        "Capabilities:\n"
        "- Answer questions about tasks using search_tasks / list_tasks. Only state facts "
        "returned by the tools; never invent task identifiers, names or numbers.\n"
        "- When the user wants to add/create a task, call create_task. It opens a preview the "
        "user must confirm — do NOT claim the task is created. After calling it, reply briefly "
        "that you've prepared a draft for review.\n"
        "If a request is ambiguous (e.g. which project), ask a short clarifying question instead "
        "of guessing.\n\n"
        "Formatting (IMPORTANT):\n"
        "- Reply in PLAIN TEXT only. Do NOT use Markdown or HTML — no **, *, #, _, backticks "
        "or <tags> (they are shown literally to the user).\n"
        "- When listing tasks, make a NUMBERED list, one task per line, like:\n"
        "  1. FLO-36 — парсинг данных — Рафаэль Шагиев · In Progress\n"
        "  2. FLO-40 — deploying the site — Otabek · In Progress\n"
        "  The bot automatically adds tap-to-open buttons under your message, so the user can "
        "open each task by its number — keep the order of your list matching the tasks you listed."
    )
