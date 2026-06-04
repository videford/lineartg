import asyncio
import sys

from bot.linear import LinearClient

QUERY_PROJECTS = """
query { projects(first: 50) { nodes { id name } } }
"""


async def main() -> None:
    c = LinearClient(sys.argv[1])
    data = await c._execute(QUERY_PROJECTS)
    projects = data["projects"]["nodes"]
    print("projects:", len(projects))
    for p in projects[:3]:
        issues = await c.issues_by_project(p["id"])
        print(f"  {p['name']}: {len(issues)} issues", [i["identifier"] for i in issues[:5]])


asyncio.run(main())
