from aiogram import Bot
from aiogram.types import BotCommand


async def setup_menu(bot: Bot):
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Главное меню"),
            BotCommand(command="help", description="Информация о боте"),
            BotCommand(command="order", description="Сделать заказ"),
        ],
    )


__all__ = ["setup_menu"]
