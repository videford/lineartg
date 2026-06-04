import asyncio

from bot.db.session import session_factory
from bot.services import workspace


async def main() -> None:
    async with session_factory() as s:
        c = await workspace.get_client(s)
    teams = await c.teams()
    print("TEAMS:", [(t["name"], t["key"]) for t in teams])
    if teams:
        projects = await c.projects(teams[0]["id"])
        print("PROJECTS:", [p["name"] for p in projects])
        states = await c.workflow_states(teams[0]["id"])
        print("STATES(team0):", [st["name"] for st in states])


asyncio.run(main())
