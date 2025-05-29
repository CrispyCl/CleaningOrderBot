import asyncio

from config import Config, load_config
from database import PostgresDatabase
from logger import get_logger
from repository import UserRepository
from service import UserService


async def make_user_admin(username: str, make_admin: bool = True) -> None:
    config: Config = load_config()
    logger = get_logger("main", config.logger)

    db = PostgresDatabase(config=config.postgres)
    user_service = UserService(UserRepository(db), logger=logger)
    user = await user_service.get_by_username(username=username)
    if not user:
        logger.error(f"User with username '{username}' not found.\nPlease ask the user to send a message to the bot!")
        return
    if await user_service.update_role(user.id, make_admin):
        action = "now an admin" if make_admin else "no longer an admin"
        logger.info(
            f'User with username "{username}" is {action}.\n'
            'Please ask the user to restart the bot with the command "/start"',
        )
    else:
        action = "make admin" if make_admin else "revoke admin rights from"
        logger.error(
            f'Failed to {action} user with username "{username}"".\n'
            'Please ask the user to restart the bot with the command "/start"',
        )


if __name__ == "__main__":
    choice = input("Choose action:\n1. Make user admin\n2. Revoke admin rights\n\nEnter choice (1/2): ")
    username = input("Enter username: ")

    asyncio.run(make_user_admin(username, choice == "1"))


__all__ = []
