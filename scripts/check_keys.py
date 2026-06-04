import asyncio

from aiogram_i18n.cores import FluentRuntimeCore

from bot.main import LOCALES_PATH

KEYS = [
    "start-welcome", "whoami",
    "status-admin", "status-lead", "status-member",
    "profile-card", "profile-change-name", "profile-send-name", "profile-name-updated",
    "menu-projects",
    "team-no-projects", "team-choose-project", "team-view", "team-add-btn",
    "team-add-choose", "team-back", "team-added", "team-removed",
    "team-no-candidates", "team-lead-hint",
    "assign-no-team", "assign-not-in-team",
    "nav-back", "nav-close",
    "sub-on", "sub-off", "sub-other-done", "sub-added-dm",
    "menu-browse", "browse-no-projects", "browse-choose-project",
    "browse-empty", "browse-list",
    "card-f-status", "card-f-priority", "card-f-project", "card-f-assignee",
    "card-f-due", "card-f-estimate", "card-f-labels",
    "due-prompt", "due-invalid",
    "my-title", "search-results", "list-count", "list-empty",
    "list-f-all", "list-f-todo", "list-f-inprogress", "list-f-done", "list-f-backlog",
    "list-prev", "list-next", "list-page",
]
ARGS = {
    "start-welcome": {"name": "X", "status": "Y"},
    "whoami": {"name": "X", "status": "Y"},
    "status-lead": {"projects": "A, B"},
    "profile-card": {"name": "X", "status": "Y"},
    "profile-name-updated": {"name": "X"},
    "team-view": {"project": "P", "members": "M"},
    "sub-other-done": {"name": "X"},
    "sub-added-dm": {"identifier": "FLO-1", "by": "Y"},
    "list-count": {"n": 3},
    "list-page": {"page": 1, "total": 2},
}

core = FluentRuntimeCore(path=str(LOCALES_PATH))
asyncio.run(core.startup())

bad = 0
for lang in ("ru", "en", "uz"):
    for k in KEYS:
        val = core.get(k, lang, **ARGS.get(k, {}))
        if not val or val == k:
            bad += 1
            print(f"MISSING {lang}: {k}")
print(f"done, missing={bad}")
