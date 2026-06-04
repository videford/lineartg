import asyncio

from bot.db.session import session_factory
from bot.services import workspace

TEST_LABEL = "tg:test-bot"


async def main() -> None:
    async with session_factory() as s:
        c = await workspace.get_client(s)
    teams = await c.teams()
    team_id = teams[0]["id"]
    label_id = await c.ensure_label(team_id, TEST_LABEL)
    print("label_id:", label_id)

    issue = await c.create_issue(
        title="[TEST] linearTG connectivity check — safe to delete",
        team_id=team_id,
        label_ids=[label_id],
        actor_name="linearTG test",
    )
    print("CREATED:", issue["identifier"], issue["url"])

    found = await c.issues_by_label(TEST_LABEL)
    print("ISSUES_BY_LABEL:", [(i["identifier"], i["state"]["name"]) for i in found])


asyncio.run(main())
