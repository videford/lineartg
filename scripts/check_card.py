import asyncio

from bot.db.session import session_factory
from bot.services import workspace
from bot.services.projects import list_projects, sync_projects


async def main() -> None:
    async with session_factory() as s:
        c = await workspace.get_client(s)
        n = await sync_projects(s, c)
        print("synced projects:", n)
        projects = await list_projects(s)
        print("cached:", [(p.name, bool(p.team_id)) for p in projects][:3], "...")

    found = await c.issues_by_label("tg:test-bot")
    if not found:
        print("no test issue; run check_write.py first")
        return
    iid = found[0]["id"]
    issue = await c.get_issue(iid)
    print("DETAIL:", issue["identifier"], "| prio:", issue.get("priorityLabel"),
          "| due:", issue.get("dueDate"), "| est:", issue.get("estimate"))

    await c.update_issue(iid, priority=2, estimate=3, dueDate="2026-06-30")
    issue2 = await c.get_issue(iid)
    print("AFTER :", issue2["identifier"], "| prio:", issue2.get("priorityLabel"),
          "| due:", issue2.get("dueDate"), "| est:", issue2.get("estimate"))


asyncio.run(main())
