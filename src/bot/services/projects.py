from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db import Project, ProjectLead, User
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
