from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import DefaultDatabase
from models import Order, OrderStatus


class OrderRepository:
    """Order Repository class"""

    def __init__(self, database: DefaultDatabase):
        self.db = database

    async def create(self, author_id: str, address: str, time: datetime, status: OrderStatus) -> int:
        async with self.db.get_session() as session:
            session: AsyncSession
            order = Order(author_id=author_id, address=address, time=time, status=status)
            session.add(order)
            try:
                await session.commit()
                return order.id

            except IntegrityError as e:
                await session.rollback()
                raise IntegrityError(
                    statement=e.statement,
                    params=e.params,
                    orig=Exception("Order already exists"),
                )

            except Exception as e:
                await session.rollback()
                raise e

    async def get_one(self, id: int) -> Order:
        async with self.db.get_session() as session:
            session: AsyncSession
            try:
                order = await session.get(Order, id)
                if not order:
                    raise NoResultFound(f"Order with id={id} does not exist")
                return order
            except Exception as e:
                await session.rollback()
                raise e

    async def get(self) -> List[Order]:
        async with self.db.get_session() as session:
            session: AsyncSession
            try:
                stmt = select(Order).order_by(Order.id)
                result = await session.execute(stmt)

                return list(result.scalars().all())
            except Exception as e:
                await session.rollback()
                raise e

    async def get_with_author(self) -> List[Order]:
        async with self.db.get_session() as session:
            session: AsyncSession
            try:
                stmt = select(Order).options(joinedload(Order.author)).order_by(Order.id)
                result = await session.execute(stmt)

                return list(result.scalars().all())

            except Exception as e:
                await session.rollback()
                raise e

    async def get_pending(self) -> List[Order]:
        async with self.db.get_session() as session:
            session: AsyncSession
            try:
                stmt = (
                    select(Order)
                    .filter(Order.status == OrderStatus.pending)
                    .options(joinedload(Order.author))
                    .order_by(Order.id)
                )
                result = await session.execute(stmt)

                return list(result.scalars().all())

            except Exception as e:
                await session.rollback()
                raise e

    async def get_by_author(self, author_id: str) -> List[Order]:
        async with self.db.get_session() as session:
            session: AsyncSession
            try:
                stmt = select(Order).filter(Order.author_id == author_id).order_by(Order.id)
                result = await session.execute(stmt)

                return list(result.scalars().all())

            except Exception as e:
                await session.rollback()
                raise e

    async def update_status(self, id: int, status: OrderStatus) -> Order:
        async with self.db.get_session() as session:
            session: AsyncSession
            try:
                order = await session.get(Order, id)
                if not order:
                    raise NoResultFound(f"Order with id={id} does not exist")

                order.status = status
                await session.commit()
                await session.refresh(order)

                return order

            except Exception as e:
                await session.rollback()
                raise e


__all__ = ["OrderRepository"]
