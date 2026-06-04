from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

import httpx

from bot.linear import queries

log = logging.getLogger(__name__)

LINEAR_GRAPHQL_URL = "https://api.linear.app/graphql"


def _resolve_icon(actor_name: str | None, actor_icon: str | None) -> str | None:
    """Linear requires displayIconUrl to be non-null whenever createAsUser is
    set. Fall back to a generated initials avatar when the member has none."""
    if actor_icon:
        return actor_icon
    if actor_name:
        return f"https://api.dicebear.com/9.x/initials/svg?seed={quote(actor_name)}"
    return None


class LinearError(RuntimeError):
    pass


class LinearClient:
    """Thin async GraphQL client for the Linear API.

    `access_token` is the workspace OAuth token obtained with actor=app.
    `actor_name` / `actor_icon` are passed as createAsUser / displayIconUrl so
    the seat-less Telegram member is shown as the actor in Linear."""

    def __init__(self, access_token: str, app_actor: bool | None = None) -> None:
        self._token = access_token
        # createAsUser/displayIconUrl only work with OAuth actor=app tokens.
        # Personal API keys (prefix "lin_api_") must omit them.
        if app_actor is None:
            app_actor = not access_token.startswith("lin_api_")
        self._app_actor = app_actor

    async def _execute(self, document: str, variables: dict[str, Any] | None = None) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                LINEAR_GRAPHQL_URL,
                json={"query": document, "variables": variables or {}},
                headers={
                    "Authorization": self._token,
                    "Content-Type": "application/json",
                },
            )
        resp.raise_for_status()
        payload = resp.json()
        if "errors" in payload:
            log.error("Linear GraphQL error: %s", payload["errors"])
            raise LinearError(str(payload["errors"]))
        return payload["data"]

    # ── reads ────────────────────────────────────────────────
    async def viewer(self) -> dict:
        return await self._execute(queries.VIEWER)

    async def teams(self) -> list[dict]:
        data = await self._execute(queries.TEAMS)
        return data["teams"]["nodes"]

    async def projects(self, team_id: str) -> list[dict]:
        data = await self._execute(queries.PROJECTS, {"teamId": team_id})
        team = data.get("team") or {}
        return (team.get("projects") or {}).get("nodes", [])

    async def all_projects(self) -> list[dict]:
        """All projects across teams, each annotated with a `team_id`
        (first associated team) for caching."""
        data = await self._execute(queries.ALL_PROJECTS)
        out = []
        for node in data["projects"]["nodes"]:
            teams = (node.get("teams") or {}).get("nodes", [])
            out.append(
                {
                    "id": node["id"],
                    "name": node["name"],
                    "state": node.get("state"),
                    "team_id": teams[0]["id"] if teams else None,
                }
            )
        return out

    async def workflow_states(self, team_id: str) -> list[dict]:
        data = await self._execute(queries.WORKFLOW_STATES, {"teamId": team_id})
        team = data.get("team") or {}
        nodes = (team.get("states") or {}).get("nodes", [])
        return sorted(nodes, key=lambda s: s["position"])

    async def issues_by_label(self, label: str) -> list[dict]:
        data = await self._execute(queries.ISSUES_BY_LABEL, {"label": label})
        return data["issues"]["nodes"]

    async def search_issues(self, term: str) -> list[dict]:
        data = await self._execute(queries.ISSUE_SEARCH, {"term": term})
        return data["issues"]["nodes"]

    async def issues_by_project(self, project_id: str) -> list[dict]:
        data = await self._execute(queries.ISSUES_BY_PROJECT, {"projectId": project_id})
        project = data.get("project") or {}
        return (project.get("issues") or {}).get("nodes", [])

    async def get_issue(self, issue_id: str) -> dict | None:
        data = await self._execute(queries.ISSUE_DETAIL, {"id": issue_id})
        return data.get("issue")

    # ── label helpers (seat-less assignee representation) ─────
    async def labels(self, team_id: str) -> list[dict]:
        data = await self._execute(queries.LABELS, {"teamId": team_id})
        team = data.get("team") or {}
        return (team.get("labels") or {}).get("nodes", [])

    async def ensure_label(self, team_id: str, name: str) -> str:
        data = await self._execute(queries.LABELS, {"teamId": team_id})
        team = data.get("team") or {}
        for node in (team.get("labels") or {}).get("nodes", []):
            if node["name"] == name:
                return node["id"]
        created = await self._execute(
            queries.LABEL_CREATE, {"name": name, "teamId": team_id}
        )
        return created["issueLabelCreate"]["issueLabel"]["id"]

    # ── writes ───────────────────────────────────────────────
    async def create_issue(
        self,
        *,
        title: str,
        team_id: str,
        description: str | None = None,
        project_id: str | None = None,
        assignee_id: str | None = None,
        label_ids: list[str] | None = None,
        actor_name: str | None = None,
        actor_icon: str | None = None,
    ) -> dict:
        issue_input: dict[str, Any] = {"title": title, "teamId": team_id}
        if description:
            issue_input["description"] = description
        if project_id:
            issue_input["projectId"] = project_id
        if assignee_id:
            issue_input["assigneeId"] = assignee_id
        if label_ids:
            issue_input["labelIds"] = label_ids
        if self._app_actor and actor_name:
            issue_input["createAsUser"] = actor_name
            issue_input["displayIconUrl"] = _resolve_icon(actor_name, actor_icon)

        data = await self._execute(queries.ISSUE_CREATE, {"input": issue_input})
        result = data["issueCreate"]
        if not result["success"]:
            raise LinearError("issueCreate failed")
        return result["issue"]

    async def update_issue(self, issue_id: str, **fields: Any) -> dict:
        """Generic issueUpdate. Pass any of: stateId, title, description,
        priority (int), dueDate ("YYYY-MM-DD" or None to clear), estimate (int),
        labelIds (list), assigneeId. None values are sent (to clear) only for
        dueDate/estimate/assigneeId; omit a field entirely to leave unchanged."""
        clearable = {"dueDate", "estimate", "assigneeId"}
        issue_input: dict[str, Any] = {}
        for key, value in fields.items():
            if value is None and key not in clearable:
                continue
            issue_input[key] = value
        data = await self._execute(
            queries.ISSUE_UPDATE, {"id": issue_id, "input": issue_input}
        )
        result = data["issueUpdate"]
        if not result["success"]:
            raise LinearError("issueUpdate failed")
        return result["issue"]

    async def update_issue_state(self, issue_id: str, state_id: str) -> dict:
        return await self.update_issue(issue_id, stateId=state_id)

    async def create_comment(
        self,
        *,
        issue_id: str,
        body: str,
        actor_name: str | None = None,
        actor_icon: str | None = None,
    ) -> dict:
        comment_input: dict[str, Any] = {"issueId": issue_id, "body": body}
        if self._app_actor and actor_name:
            comment_input["createAsUser"] = actor_name
            comment_input["displayIconUrl"] = _resolve_icon(actor_name, actor_icon)

        data = await self._execute(queries.COMMENT_CREATE, {"input": comment_input})
        result = data["commentCreate"]
        if not result["success"]:
            raise LinearError("commentCreate failed")
        return result["comment"]
