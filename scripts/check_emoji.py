import asyncio

from aiogram_i18n.cores import FluentRuntimeCore

from bot.keyboards import menu as mk
from bot.main import LOCALES_PATH

core = FluentRuntimeCore(path=str(LOCALES_PATH))
asyncio.run(core.startup())

pairs = [
    ("menu-my", mk.EMOJI_MY),
    ("menu-create", mk.EMOJI_CREATE),
    ("menu-assign", mk.EMOJI_ASSIGN),
    ("menu-search", mk.EMOJI_SEARCH),
    ("menu-settings", mk.EMOJI_SETTINGS),
    ("menu-help", mk.EMOJI_HELP),
    ("menu-admin", mk.EMOJI_ADMIN),
]
bad = 0
for lang in ("ru", "en", "uz"):
    for key, emo in pairs:
        label = core.get(key, lang)
        if not label.startswith(emo):
            bad += 1
            print(f"MISMATCH {lang} {key}: label={label!r} emoji={emo!r}")
print(f"done, mismatches={bad}")
