from datetime import datetime
from logging import Logger
from typing import List, Optional

from sqlalchemy.exc import NoResultFound

from models import Order, OrderStatus
from repository import OrderRepository


class OrderService:
    """Order Service class"""

    def __init__(
        self,
        repository: OrderRepository,
        logger: Logger,
    ):
        self.repo = repository
        self.log = logger

    async def create(self, author_id: str, address: str, time: datetime, status: str = "pending") -> Optional[int]:
        try:
            return await self.repo.create(author_id, address, time, OrderStatus(status))

        except Exception as e:
            self.log.error("OrderRepository: %s" % e)

        return None

    async def get_one(self, id: int) -> Optional[Order]:
        try:
            return await self.repo.get_one(id)

        except NoResultFound as e:
            self.log.warning("OrderRepository: %s" % e)
        except Exception as e:
            self.log.error("OrderRepository: %s" % e)

        return None

    async def get(self, with_author=False) -> List[Order]:
        try:
            if with_author:
                return await self.repo.get_with_author()
            return await self.repo.get()

        except Exception as e:
            self.log.error("OrderRepository: %s" % e)

        return []

    async def get_pending(self) -> List[Order]:
        try:
            return await self.repo.get_pending()

        except Exception as e:
            self.log.error("OrderRepository: %s" % e)

        return []

    async def get_by_author(self, author_id: str) -> List[Order]:
        try:
            return await self.repo.get_by_author(author_id)

        except Exception as e:
            self.log.error("OrderRepository: %s" % e)

        return []

    async def update_status(self, id: int, status: str) -> Optional[Order]:
        try:
            return await self.repo.update_status(id, OrderStatus(status))

        except NoResultFound as e:
            self.log.warning("OrderRepository: %s" % e)
        except Exception as e:
            self.log.error("OrderRepository: %s" % e)

        return None

    async def check_pending(self) -> bool:
        try:
            return bool(await self.repo.get_pending())

        except Exception as e:
            self.log.error("OrderRepository: %s" % e)

        return False


__all__ = ["OrderService"]
