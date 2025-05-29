import asyncio
from logging import Logger
from typing import Any, Awaitable, Callable, cast, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.types import TelegramObject, Update, User


class LoggingMiddleware(BaseMiddleware):
    def __init__(self, logger: Logger):
        self.logger = logger
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        update: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        update = cast(Update, update)

        loop = asyncio.get_running_loop()
        start_time = loop.time()
        handled = False
        try:
            result = await handler(update, data)
            handled = result is not UNHANDLED
            return result

        except Exception as e:
            self.logger.error("<%d> %-7s: %s", update.update_id, "error", str(e))

        finally:
            duration = (loop.time() - start_time) * 1000
            format_string = '<%d> %-7s: "%s" from user %s. Duration %d ms'
            text = ""
            user_id = 0

            def get_user(obj: Any) -> Optional[User]:
                return getattr(obj, "from_user", None)

            if update.message:
                user = get_user(update.message)
                user_id = user.id if user else 0
                text = update.message.text
            elif update.callback_query:
                text = update.callback_query.data
                user_id = update.callback_query.from_user.id

            if handled:
                self.logger.info(
                    format_string,
                    update.update_id,
                    "request",
                    text,
                    user_id,
                    duration,
                )
            else:
                format_string = '<%d> %-7s: "%s" from user %s. NOT HANDLED'
                self.logger.debug(
                    format_string,
                    update.update_id,
                    "request",
                    text,
                    user_id,
                )


__all__ = ["LoggingMiddleware"]
