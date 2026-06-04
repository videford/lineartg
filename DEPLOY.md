# Деплой на Railway

Прод работает в **webhook-режиме** (`python -m bot.main`): один веб-сервис принимает
и Telegram-апдейты, и вебхуки/OAuth Linear. Туннель больше не нужен — у сервиса
постоянный домен `*.up.railway.app`.

Образ собирается из `Dockerfile`, который при старте делает `alembic upgrade head`
и запускает бота. Параметры (`PORT`, `DATABASE_URL` вида `postgres://`, домен) Railway
передаёт автоматически — код их понимает.

## Шаг 1. Код в GitHub
Запушь репозиторий на GitHub (см. раздел «Что нужно от тебя» — я подготовлю коммит).

## Шаг 2. Создать проект на Railway
1. https://railway.app → **New Project** → **Deploy from GitHub repo** → выбери репозиторий.
2. Railway сам найдёт `railway.json` + `Dockerfile` и начнёт сборку.

## Шаг 3. Добавить базу
В проекте: **New → Database → PostgreSQL**. Появится сервис Postgres.

## Шаг 4. Переменные сервиса бота (вкладка Variables)
```
BOT_TOKEN            = <токен из BotFather>
TELEGRAM_WEBHOOK_SECRET = <случайная строка, напр. 32 симв.>
LINEAR_CLIENT_ID     = <из Linear OAuth app>
LINEAR_CLIENT_SECRET = <из Linear OAuth app>
LINEAR_WEBHOOK_SECRET = <впишешь на шаге 7>
BOOTSTRAP_ADMIN_IDS  = 1256912867
DEFAULT_LANG         = ru
DATABASE_URL         = ${{Postgres.DATABASE_URL}}
```
`DATABASE_URL` вписывается именно как ссылка `${{Postgres.DATABASE_URL}}` — Railway
подставит реальный адрес базы.

> `PUBLIC_BASE_URL` указывать не нужно — он выводится из `RAILWAY_PUBLIC_DOMAIN`
> автоматически (шаг 5). `LINEAR_REDIRECT_URI` тоже выведется сам.

## Шаг 5. Сгенерировать домен
Сервис бота → **Settings → Networking → Generate Domain**. Получишь
`https://<имя>.up.railway.app`. После этого **Redeploy** (Deployments → Redeploy),
чтобы бот выставил Telegram-вебхук на новый домен.

## Шаг 6. Обновить Redirect URI в Linear
Linear → Settings → API → твоё OAuth-приложение → **Redirect URIs**:
```
https://<имя>.up.railway.app/linear/oauth/callback
```

## Шаг 7. Включить уведомления Linear → Telegram (вебхук)
Linear → Settings → API → **Webhooks → New webhook**:
- URL: `https://<имя>.up.railway.app/linear/webhook`
- подписки: **Issues**, **Comments**
- скопируй **Signing secret** → впиши в переменную `LINEAR_WEBHOOK_SECRET` на Railway → **Redeploy**.

## Шаг 8. Подключить Linear из бота
В Telegram: **🛠 Управление → 🔗 Подключить Linear** (или `/connect`) → авторизуй →
готово. Теперь действия подписываются именами (`actor=app`), а уведомления из Linear
прилетают в привязанные чаты (`/bind` в нужной группе).

## Обновления
Любой `git push` в подключённую ветку → Railway пересобирает и передеплоивает.
Миграции применяются автоматически при старте контейнера.

## Заметки
- FSM-состояния пока в памяти процесса — при передеплое незавершённые диалоги
  (ввод заголовка и т.п.) сбрасываются. Для устойчивости позже можно добавить Redis
  (`REDIS_URL`) и RedisStorage. Данные (токен, проекты, роли) — в Postgres, не теряются.
- Health-check: `/healthz`.
