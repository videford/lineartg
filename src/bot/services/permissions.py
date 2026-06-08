from __future__ import annotations

import enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import ProjectLead, Role, User


class Action(str, enum.Enum):
    """Global (non-project) capabilities."""

    BIND_CHAT = "bind_chat"          # connect Linear / bind chats / sync
    MANAGE_ROLES = "manage_roles"    # change users' global role
    MANAGE_LEADS = "manage_leads"    # assign project leads


# Global actions are admin/PM only.
_GLOBAL: dict[Role, set[Action]] = {
    Role.member: set(),
    Role.lead: set(),
    Role.admin: set(Action),
}


def can(role: Role, action: Action) -> bool:
    return action in _GLOBAL.get(role, set())


# ── project-scoped checks ────────────────────────────────────


def is_admin(user: User) -> bool:
    return user.role == Role.admin


async def is_lead_of(session: AsyncSession, telegram_id: int, project_id: str) -> bool:
    if not project_id:
        return False
    row = await session.scalar(
        select(ProjectLead).where(
            ProjectLead.telegram_id == telegram_id,
            ProjectLead.project_id == project_id,
        )
    )
    return row is not None


async def is_any_lead(session: AsyncSession, telegram_id: int) -> bool:
    row = await session.scalar(
        select(ProjectLead).where(ProjectLead.telegram_id == telegram_id)
    )
    return row is not None


def is_owner_of(user: User, owner_labels: list[str]) -> bool:
    """True if one of the issue's labels matches the user's owner label."""
    return bool(user.linear_label) and user.linear_label in owner_labels


async def can_manage_task(
    session: AsyncSession, user: User, project_id: str | None
) -> bool:
    """Create/edit/status/assign/close — admin globally, or lead of the project."""
    if is_admin(user):
        return True
    return await is_lead_of(session, user.telegram_id, project_id or "")


async def can_create_in(session: AsyncSession, user: User, project_id: str) -> bool:
    """Create a task in a project: admins anywhere; leads/members in projects they
    belong to. Guests cannot create anything."""
    if user.role == Role.guest:
        return False
    if is_admin(user):
        return True
    from bot.services.projects import is_project_team

    return await is_project_team(session, user.telegram_id, project_id or "")


async def can_set_status(
    session: AsyncSession, user: User, project_id: str | None, owner_labels: list[str]
) -> bool:
    """Change a task's workflow state: admins/leads (manage) or the task's own
    assignee (a member moving their own task forward)."""
    if await can_manage_task(session, user, project_id):
        return True
    return is_owner_of(user, owner_labels)


async def can_comment(
    session: AsyncSession,
    user: User,
    project_id: str | None,
    owner_labels: list[str],
) -> bool:
    """Comment — admin, project lead, or the task's owner (member on own task)."""
    if await can_manage_task(session, user, project_id):
        return True
    return is_owner_of(user, owner_labels)
