from abc import ABC, abstractmethod
from contextlib import _AsyncGeneratorContextManager
from typing import Any

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class DefaultDatabase(ABC):
    """Abstract Database class"""

    @abstractmethod
    async def init_db(self):
        """Creating all tables in the database."""

    @abstractmethod
    async def drop_db(self):
        """Deleting all tables from the database."""

    @abstractmethod
    def get_session(self) -> _AsyncGeneratorContextManager[Any, None]:
        """Context manager for sessions."""

    @abstractmethod
    async def close(self):
        """Close all database connections and cleanup."""


__all__ = ["Base", "DefaultDatabase"]
