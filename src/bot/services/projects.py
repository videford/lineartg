from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import Project, ProjectLead, ProjectMember, User
from bot.linear import LinearClient


async def sync_projects(session: AsyncSession, client: LinearClient) -> int:
    """Refresh the local Project cache from Linear. Returns the count."""
    remote = await client.all_projects()
    remote_ids = {p["id"] for p in remote}

    existing = {p.id: p for p in await session.scalars(select(Project))}
    for p in remote:
        row = existing.get(p["id"])
        if row is None:
            session.add(
                Project(
                    id=p["id"],
                    name=p["name"],
                    team_id=p["team_id"],
                    is_active=True,
                )
            )
        else:
            row.name = p["name"]
            row.team_id = p["team_id"]
            row.is_active = True

    # Mark projects no longer returned as inactive (kept for historical links).
    for pid, row in existing.items():
        if pid not in remote_ids:
            row.is_active = False

    await session.commit()
    return len(remote)


async def list_projects(session: AsyncSession) -> list[Project]:
    return list(
        await session.scalars(
            select(Project).where(Project.is_active.is_(True)).order_by(Project.name)
        )
    )


async def get_project(session: AsyncSession, project_id: str) -> Project | None:
    return await session.get(Project, project_id)


async def led_projects(session: AsyncSession, telegram_id: int) -> list[Project]:
    """Projects this user is a lead of (regardless of admin status)."""
    led_ids = list(
        await session.scalars(
            select(ProjectLead.project_id).where(
                ProjectLead.telegram_id == telegram_id
            )
        )
    )
    if not led_ids:
        return []
    return list(
        await session.scalars(
            select(Project)
            .where(Project.id.in_(led_ids), Project.is_active.is_(True))
            .order_by(Project.name)
        )
    )


async def project_team(session: AsyncSession, project_id: str) -> list[User]:
    """Users who can be assigned tasks in a project: its members plus its leads."""
    member_ids = set(
        await session.scalars(
            select(ProjectMember.telegram_id).where(
                ProjectMember.project_id == project_id
            )
        )
    )
    member_ids |= set(
        await session.scalars(
            select(ProjectLead.telegram_id).where(
                ProjectLead.project_id == project_id
            )
        )
    )
    if not member_ids:
        return []
    return list(
        await session.scalars(
            select(User)
            .where(User.telegram_id.in_(member_ids), User.is_active.is_(True))
            .order_by(User.display_name)
        )
    )


async def is_project_team(session: AsyncSession, telegram_id: int, project_id: str) -> bool:
    in_members = await session.scalar(
        select(ProjectMember).where(
            ProjectMember.telegram_id == telegram_id,
            ProjectMember.project_id == project_id,
        )
    )
    if in_members is not None:
        return True
    in_leads = await session.scalar(
        select(ProjectLead).where(
            ProjectLead.telegram_id == telegram_id,
            ProjectLead.project_id == project_id,
        )
    )
    return in_leads is not None


async def add_project_member(
    session: AsyncSession, telegram_id: int, project_id: str
) -> bool:
    exists = await session.scalar(
        select(ProjectMember).where(
            ProjectMember.telegram_id == telegram_id,
            ProjectMember.project_id == project_id,
        )
    )
    if exists is not None:
        return False
    session.add(ProjectMember(telegram_id=telegram_id, project_id=project_id))
    await session.commit()
    return True


async def remove_project_member(
    session: AsyncSession, telegram_id: int, project_id: str
) -> None:
    row = await session.scalar(
        select(ProjectMember).where(
            ProjectMember.telegram_id == telegram_id,
            ProjectMember.project_id == project_id,
        )
    )
    if row is not None:
        await session.delete(row)
        await session.commit()


async def manageable_projects(session: AsyncSession, user: User) -> list[Project]:
    """Projects the user may create/manage in: all for admin, led ones for leads."""
    from bot.db import Role

    if user.role == Role.admin:
        return await list_projects(session)
    led_ids = list(
        await session.scalars(
            select(ProjectLead.project_id).where(
                ProjectLead.telegram_id == user.telegram_id
            )
        )
    )
    if not led_ids:
        return []
    return list(
        await session.scalars(
            select(Project)
            .where(Project.id.in_(led_ids), Project.is_active.is_(True))
            .order_by(Project.name)
        )
    )
