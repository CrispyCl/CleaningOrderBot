from typing import List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from database import DefaultDatabase
from models import User


class UserRepository:
    """User Repository class"""

    def __init__(self, database: DefaultDatabase):
        self.db = database

    async def create(self, user_id: str, username: str, is_staff: bool = False, is_superuser: bool = False) -> str:
        async with self.db.get_session() as session:
            session: AsyncSession
            user = User(
                id=user_id,
                username=username,
                is_staff=is_staff,
                is_superuser=is_superuser,
            )
            session.add(user)
            try:
                await session.commit()
                return user.id

            except IntegrityError as e:
                await session.rollback()
                raise IntegrityError(
                    statement=e.statement,
                    params=e.params,
                    orig=Exception("User already exists"),
                )

            except Exception as e:
                await session.rollback()
                raise e

    async def get_one(self, id: str) -> User:
        async with self.db.get_session() as session:
            session: AsyncSession
            try:
                user = await session.get(User, id)
                if not user:
                    raise NoResultFound(f"User with id={id} does not exist")
                return user
            except Exception as e:
                raise e

    async def get_by_username(self, username: str) -> User:
        async with self.db.get_session() as session:
            session: AsyncSession
            try:
                user = (await session.execute(select(User).filter(User.username == username))).scalar_one()
                if not user:
                    raise NoResultFound(f"User with username={username} does not exist")
                return user
            except Exception as e:
                raise e

    async def get(self) -> List[User]:
        async with self.db.get_session() as session:
            session: AsyncSession
            try:
                result = (await session.execute(select(User).order_by(User.id))).scalars().all()
                return list(result)
            except Exception as e:
                raise e

    async def update_username(self, id: str, username: str) -> User:
        async with self.db.get_session() as session:
            session: AsyncSession
            try:
                user = await session.get(User, id)
                if user is None:
                    raise NoResultFound(f"User with id={id} does not exist")
                user.username = username
                await session.commit()
                await session.refresh(user)
                return user

            except Exception as e:
                await session.rollback()
                raise e

    async def update_role(self, id: str, is_staff: bool) -> User:
        async with self.db.get_session() as session:
            session: AsyncSession
            try:
                user = await session.get(User, id)
                if user is None:
                    raise NoResultFound(f"User with id={id} does not exist")
                user.is_staff = is_staff
                await session.commit()
                await session.refresh(user)
                return user

            except Exception as e:
                await session.rollback()
                raise e

    async def update_phone_number(self, id: str, phone_number: str) -> User:
        async with self.db.get_session() as session:
            session: AsyncSession
            try:
                user = await session.get(User, id)
                if user is None:
                    raise NoResultFound(f"User with id={id} does not exist")
                user.phone_number = phone_number
                await session.commit()
                await session.refresh(user)
                return user

            except Exception as e:
                await session.rollback()
                raise e


__all__ = ["UserRepository"]
