from logging import Logger

from aiogram import Dispatcher

from middleware.logging import LoggingMiddleware
from middleware.user import CurrentUserMiddleware
from service import UserService


def setup(dispatcher: Dispatcher, logger: Logger, user_service: UserService):
    dispatcher.update.middleware(CurrentUserMiddleware(user_service=user_service))
    dispatcher.update.middleware(LoggingMiddleware(logger))


__all__ = ["setup"]
