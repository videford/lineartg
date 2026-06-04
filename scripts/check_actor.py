import asyncio
import sys

from bot.linear import LinearClient

QUERY = """
query Recent {
  issues(first: 8, orderBy: createdAt) {
    nodes {
      identifier
      title
      createdAt
      creator { name }
      botActor { name type userDisplayName }
    }
  }
}
"""


async def main() -> None:
    c = LinearClient(sys.argv[1])
    data = await c._execute(QUERY)
    for n in data["issues"]["nodes"]:
        bot = n.get("botActor") or {}
        print(
            f"{n['identifier']:8} | {(n['title'] or '')[:40]:40} | "
            f"creator={ (n.get('creator') or {}).get('name','-') } | "
            f"botActor={bot.get('name','-')} | as={bot.get('userDisplayName','-')}"
        )


asyncio.run(main())
