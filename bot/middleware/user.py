from typing import Any, Awaitable, Callable, cast, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User
from aiogram.types.base import UNSET

from service import UserService


class CurrentUserMiddleware(BaseMiddleware):
    def __init__(self, user_service: UserService):
        self.user_service = user_service
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        update: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        update = cast(Update, update)

        user: Optional[User] = None

        if update.message and update.message.from_user is not UNSET:
            user = update.message.from_user
        elif update.callback_query and update.callback_query.from_user is not UNSET:
            user = update.callback_query.from_user

        if not user:
            return await handler(update, data)

        username = user.username or user.full_name or user.first_name or f"user_{user.id}"

        current_user = await self.user_service.get_or_create(id=str(user.id), username=username)
        if not current_user:
            return await handler(update, data)

        if current_user.username != username:
            current_user = await self.user_service.update_username(current_user.id, username)

        data["current_user"] = current_user
        return await handler(update, data)


__all__ = ["CurrentUserMiddleware"]
