# linearTG

Telegram bot that lets a whole team work in **Linear.app** without occupying paid
Linear seats. Only product managers and team leads have real Linear accounts; the
rest of the team creates tasks, changes statuses and comments through the bot.

## How seat-less members work

The bot authorizes against Linear with **`actor=app` OAuth**, so every mutation is
performed by the application — which **does not consume a Linear seat**. Each action
carries `createAsUser` (the Telegram member's name) so it still shows up in Linear's
history as *"Ivan Petrov (via Bot)"*. A member's "assignee" is represented by a
label `tg:<name>` (custom fields require a paid plan), which the `/my` command
filters on.

> ⚠️ **Free-plan ceiling:** Linear Free allows 2 teams and **250 active issues**.
> Funnelling the whole team through the bot will hit the issue cap before it hits
> any seat limit — plan to archive/close issues or upgrade to Standard.

## Architecture

```
Telegram (groups + DM) ─webhook─►  aiohttp + aiogram  ─GraphQL─►  Linear API
Linear ─────────────────webhook─►  (this service)     ◄─events──  Linear Webhooks
                                          │
                                     PostgreSQL  (users, roles, bindings, issue links)
```

## Roles (enforced in the bot, not in Linear)

| Action                | member | lead | admin/PM |
|-----------------------|:------:|:----:|:--------:|
| create task           | ✅ | ✅ | ✅ |
| assign to others      | ❌ | ✅ | ✅ |
| status of own task    | ✅ | ✅ | ✅ |
| status of any task    | ❌ | ✅ | ✅ |
| comment               | ✅ | ✅ | ✅ |
| close / archive       | ❌ | ✅ | ✅ |
| bind chat / settings  | ❌ | ❌ | ✅ |
| manage roles          | ❌ | ❌ | ✅ |

## Commands

- `/start` — register & choose language (ru / uz / en)
- `/task` — create a task (pick project → text)
- `/my` — list tasks assigned to you
- `/assign` — lead/admin: pick project → member → text; member is DM'd
- `/connect` — admin: start Linear `actor=app` OAuth
- `/bind` — admin: bind the current group chat for notifications
- `/setrole` — admin: change a user's role

## Local setup

```bash
python -m venv .venv && . .venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cp .env.example .env                                # fill in tokens

# Postgres + Redis (e.g. via docker), then:
alembic revision --autogenerate -m "init"
alembic upgrade head

# Telegram & Linear both need a public HTTPS URL. For local dev:
#   cloudflared tunnel --url http://localhost:8080      (or ngrok http 8080)
# put the public URL into PUBLIC_BASE_URL / LINEAR_REDIRECT_URI

python -m bot.main        # run with PYTHONPATH=src, or: cd src && python -m bot.main
```

### Linear setup

1. Create an OAuth app at https://linear.app/settings/api/applications
   - Redirect URI: `${PUBLIC_BASE_URL}/linear/oauth/callback`
   - Enable **actor authorization** (the bot requests `actor=app`).
2. Create a webhook pointing at `${PUBLIC_BASE_URL}/linear/webhook` for
   *Issues* and *Comments*; copy its signing secret into `LINEAR_WEBHOOK_SECRET`.
3. In Telegram, an admin runs `/connect` and authorizes the app.

## Status

Phase 1 scaffold — happy-path flows implemented. Known TODOs are marked in code:
ownership check on status changes, chat→team binding used for project filtering,
webhook retries, and reply-to-notification → Linear comment.

## Layout

```
src/bot/
  config.py          settings (env)
  db/                SQLAlchemy models + session
  linear/            OAuth + GraphQL client + queries
  handlers/          start, tasks, assign, my, admin
  keyboards/         inline keyboards
  middlewares/       db session + user, i18n locale manager
  services/          permissions, users, workspace
  webhooks/          Linear webhook + OAuth callback
  main.py            entrypoint (aiohttp web app)
src/locales/{ru,uz,en}/messages.ftl
migrations/          Alembic
```
