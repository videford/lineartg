import asyncio

from bot.db import User
from bot.db.session import session_factory
from bot.services.projects import (
    add_project_member,
    is_project_team,
    list_projects,
    project_team,
    remove_project_member,
)
from bot.services.users import get_or_create_user

TG = 999000001  # synthetic test user


async def main() -> None:
    async with session_factory() as s:
        projects = await list_projects(s)
        if not projects:
            print("no projects cached; run check_card.py to sync first")
            return
        pid = projects[0].id
        await get_or_create_user(s, telegram_id=TG, display_name="Team Tester")

        print("before:", [u.display_name for u in await project_team(s, pid)])
        added = await add_project_member(s, TG, pid)
        print("added:", added)
        print("is_team:", await is_project_team(s, TG, pid))
        print("after add:", [u.display_name for u in await project_team(s, pid)])
        await remove_project_member(s, TG, pid)
        print("is_team after remove:", await is_project_team(s, TG, pid))

        # cleanup synthetic user
        u = await s.get(User, TG)
        if u:
            await s.delete(u)
            await s.commit()


asyncio.run(main())
