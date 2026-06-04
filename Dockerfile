FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./

EXPOSE 8080

# Apply migrations, then start the web app (Telegram + Linear webhooks).
CMD ["sh", "-c", "alembic upgrade head && python -m bot.main"]
