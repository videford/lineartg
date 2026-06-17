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

## Шаг 9 (опционально). ИИ-ассистент
Без этих переменных ассистент выключен, бот работает как обычно. Чтобы включить —
добавь в Variables один провайдер и ключ:
```
AI_PROVIDER       = anthropic          # anthropic | openai | gemini
ANTHROPIC_API_KEY = <ключ Anthropic>   # если anthropic
OPENAI_API_KEY    = <ключ OpenAI>      # если openai
GEMINI_API_KEY    = <ключ Google>      # если gemini
# AI_MODEL        = <необязательно; напр. gemini-2.0-flash-lite>
```
- Ключ Anthropic: https://console.anthropic.com → **API Keys**.
- Ключ OpenAI: https://platform.openai.com/api-keys (нужен баланс/биллинг).
- Ключ Gemini: https://aistudio.google.com/apikey (есть бесплатный тариф).
После сохранения — **Redeploy**. В личке с ботом любое свободное сообщение (не команда
и не кнопка) обрабатывает ассистент: отвечает по задачам и готовит черновики
(создание всегда через подтверждение в карточке-предпросмотре).

## Шаг 10 (опционально). Фидбэк с сайта → задача в Linear
Сайт коллеги шлёт `POST /report` (заголовок `X-API-Token`) с JSON фидбэка — бот
создаёт задачу в Linear, а привязанные группы получают анонс автоматически.
```
FEEDBACK_API_TOKEN    = <общий секрет с сайтом>
FEEDBACK_PROJECT_NAME = Bugs        # проект Linear, куда падают задачи
```
- Создай в Linear проект с этим именем (или поменяй переменную); если не найдётся —
  задача создастся без проекта.
- Коллеге: `FEEDBACK_BOT_URL = https://<домен>/report`, `FEEDBACK_BOT_TOKEN = <тот же секрет>`.
  Тело — как у его «report-бота» (type, message, page, filters, env, user, tags, photo).

## Шаг 11 (опционально). Generic API создания задач
Для других сервисов (CI/девопс): `POST /create/linear/task` (заголовок `X-API-Token`).
```
TASKS_API_TOKEN = <секрет для этого потребителя>   # если пусто — берётся FEEDBACK_API_TOKEN
```
Тело: `{ title (обяз.), description?, photo?(base64/dataURL), project?, labels?[], priority?(urgent|high|medium|low|none|0-4), due?(DD.MM.YYYY), author? }`
Ответ: `{ ok, identifier, url }`. Креды Linear потребителю не нужны — задачу создаёт бот.

## Обновления
Любой `git push` в подключённую ветку → Railway пересобирает и передеплоивает.
Миграции применяются автоматически при старте контейнера.

## Заметки
- FSM-состояния пока в памяти процесса — при передеплое незавершённые диалоги
  (ввод заголовка и т.п.) сбрасываются. Для устойчивости позже можно добавить Redis
  (`REDIS_URL`) и RedisStorage. Данные (токен, проекты, роли) — в Postgres, не теряются.
- Health-check: `/healthz`.
