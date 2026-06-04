import asyncio
import sys

from bot.linear import LinearClient


async def main() -> None:
    c = LinearClient(sys.argv[1])
    issues = await c.all_issues()
    print("all_issues:", len(issues))
    for i in issues[:5]:
        labels = [lb["name"] for lb in (i.get("labels") or {}).get("nodes", [])]
        print(
            f"  {i['identifier']} | {(i.get('state') or {}).get('type')} | "
            f"due={i.get('dueDate')} | labels={labels}"
        )


asyncio.run(main())
