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
