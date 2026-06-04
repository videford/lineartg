import asyncio

from bot.db import User
from bot.db.session import session_factory
from bot.services.subscriptions import (
    is_subscribed,
    subscribe,
    subscriber_ids,
    unsubscribe,
)
from bot.services.users import get_or_create_user

TG = 999000002
ISSUE = "test-issue-uuid-123"


async def main() -> None:
    async with session_factory() as s:
        await get_or_create_user(s, telegram_id=TG, display_name="Sub Tester")
        print("before:", await is_subscribed(s, TG, ISSUE))
        print("subscribe:", await subscribe(s, TG, ISSUE))
        print("is:", await is_subscribed(s, TG, ISSUE))
        print("subscribers:", await subscriber_ids(s, ISSUE))
        await unsubscribe(s, TG, ISSUE)
        print("after unsub:", await is_subscribed(s, TG, ISSUE))
        u = await s.get(User, TG)
        if u:
            await s.delete(u)
            await s.commit()


asyncio.run(main())
