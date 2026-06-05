# linearTG — Telegram bot bridge for Linear.app

Lets a whole team work in Linear via Telegram so only PMs/leads keep paid Linear
seats. The rest interact through the bot (seat-less via Linear OAuth `actor=app`).

## Run / test
- Stack: Python 3.12, aiogram 3, SQLAlchemy async + Postgres, aiogram-i18n (Fluent), Alembic.
- Always run with `PYTHONPATH=src`. Local DB via `docker compose up -d db`.
- Test bot locally (polling, no tunnel): `python -m bot.run_test` (DB + web for OAuth/webhooks).
- Prod entrypoint: `python -m bot.main` (webhook mode).
- Validate after edits: `python -m py_compile` over `src`; import modules; run
  `scripts/check_keys.py` and `scripts/check_emoji.py` (need DB up / a Linear token for some).
- i18n: every user-facing string lives in `src/locales/{ru,en,uz}/messages.ftl` — add a
  key to ALL THREE. Card/menu buttons are localized via `i18n` passed into keyboard builders.

## Deploy
- GitHub `videford/lineartg` → Railway (service + Postgres), domain
  `lineartg-production.up.railway.app`. **Push to `main` auto-deploys.** Migrations run on
  container start (`alembic upgrade head`). Commit/push is the normal workflow here.

## Architecture (detail in project memory: project-architecture.md)
- `src/bot/handlers/`: start, menu (reply-keyboard, DM-only), card (task card + edits),
  tasklist (paginated lists), browse, people, board (group dashboard), team, assign, admin.
- `src/bot/linear/`: GraphQL client + queries (actor=app, createAsUser).
- `src/bot/middlewares/`: db (loads User), gate (registration), i18n (locale; group→en).
- `src/bot/webhooks/`: Linear webhook (announcements/notifications) + OAuth callback.
- Seat-less assignee = label `tg:<slug>` (stable, never recomputed on rename).

## Conventions / gotchas
- Callback data ≤ 64 bytes: never put two Linear UUIDs in one callback — keep the active
  id in FSM data (see card.py / tasklist.py).
- Linear collection filters like `workflowStates(filter:{team...})` 400 — use
  `team(id){ states/labels/projects }`.
- `createAsUser` needs an OAuth actor=app token (not a personal `lin_api_` key) and a
  non-null `displayIconUrl`; build mutation inputs dynamically (omit, don't send null).
- `message.answer()` already forwards the source forum topic — do NOT pass
  `message_thread_id` to it (only to `bot.send_message`).
- Groups: English UI, silent messages (except new-task announcements), management is
  DM-only, `/board` only in admin-bound groups.

## Working memory
The project memory file (`project-architecture.md`, auto-loaded) holds the full decision
log and per-round change history. Update it when you make architectural changes.
