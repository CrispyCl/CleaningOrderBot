from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class AdminPanelKeyboard:
    def __call__(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📋 Новые заявки", callback_data="admin_new_orders"),
                    InlineKeyboardButton(text="📝 Все заявки", callback_data="admin_all_orders"),
                ],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main")],
            ],
            resize_keyboard=True,
        )


__all__ = ["AdminPanelKeyboard"]
