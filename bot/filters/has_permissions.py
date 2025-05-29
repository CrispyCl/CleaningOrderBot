from typing import Any, Optional

from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from models import User


class IsAdminFilter(BaseFilter):
    """Is admin filter."""

    async def __call__(self, obj: TelegramObject, **data: Any) -> bool:
        user: Optional[User] = data.get("current_user")
        if not user:
            return False

        return user.is_staff


class IsSuperAdminFilter(BaseFilter):
    """Is super admin filter."""

    async def __call__(self, obj: TelegramObject, **data: Any) -> bool:
        user: Optional[User] = data.get("current_user")
        if not user:
            return False

        return user.is_superuser


__all__ = ["IsAdminFilter", "IsSuperAdminFilter"]
