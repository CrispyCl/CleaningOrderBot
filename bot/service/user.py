from logging import Logger
from typing import Optional

from sqlalchemy.exc import IntegrityError, NoResultFound

from models import User
from repository import UserRepository


class UserService:
    """User Service class"""

    def __init__(
        self,
        repository: UserRepository,
        logger: Logger,
    ):
        self.repo = repository
        self.log = logger

    async def create(self, id: str, username: str, is_staff: bool = False) -> str:
        try:
            return await self.repo.create(user_id=id, username=username, is_staff=is_staff)

        except IntegrityError as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)

        return "-1"

    async def get_one(self, id: str) -> Optional[User]:
        try:
            return await self.repo.get_one(id)

        except NoResultFound as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)

        return None

    async def get_or_create(self, id: str, username: str) -> Optional[User]:
        try:
            try:
                return await self.repo.get_one(id)

            except NoResultFound:
                try:
                    id = await self.create(id, username)
                    return await self.repo.get_one(id)
                except Exception as e:
                    self.log.error("UserRepository: %s" % e)

            return None

        except IntegrityError as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)

        return None

    async def get_by_username(self, username: str) -> Optional[User]:
        try:
            return await self.repo.get_by_username(username)

        except NoResultFound as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)

        return None

    async def get(self) -> list[User]:
        try:
            return await self.repo.get()

        except Exception as e:
            self.log.error("UserRepository: %s" % e)

        return []

    async def update_username(self, id: str, username: str) -> Optional[User]:
        try:
            return await self.repo.update_username(id, username)

        except NoResultFound as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)

        return None

    async def update_role(self, id: str, is_staff: bool) -> Optional[User]:
        try:
            return await self.repo.update_role(id, is_staff)

        except NoResultFound as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)

        return None

    async def update_phone_number(self, id: str, phone_number: str) -> Optional[User]:
        try:
            return await self.repo.update_phone_number(id, phone_number)

        except NoResultFound as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)

        return None

    async def is_admin(self, id: str) -> bool:
        try:
            user = await self.repo.get_one(id)
            return user.is_staff

        except NoResultFound as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)

        return False

    async def is_super_admin(self, id: str) -> bool:
        try:
            user = await self.repo.get_one(id)
            if not user:
                raise NoResultFound(f"User with id={id} does not exist")
            return user.is_superuser
        except NoResultFound as e:
            self.log.warning("UserRepository: %s" % e)
        except Exception as e:
            self.log.error("UserRepository: %s" % e)
        return False


__all__ = ["UserService"]
