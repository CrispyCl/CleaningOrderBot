from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


class MainUserKeyboard:
    def __call__(self, is_admin: bool) -> ReplyKeyboardMarkup:
        buttons: list[list[KeyboardButton]] = [
            [KeyboardButton(text="🛒 Оформить заказ"), KeyboardButton(text="ℹ️ Помощь")],
        ]
        if is_admin:
            buttons.append([KeyboardButton(text="🔐 Панель администратора")])
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


class ToMainMenuKeyboard:
    def __call__(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🏠 Главное меню")]],
            resize_keyboard=True,
        )


class ToMainOrOrderKeyboard:
    def __call__(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🏠 Главное меню")],
                [KeyboardButton(text="🛒 Оформить заказ")],
            ],
            resize_keyboard=True,
        )


class RequestPhoneNumberKeyboard:
    def __call__(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Поделиться номером", request_contact=True)],
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )


__all__ = ["MainUserKeyboard", "ToMainMenuKeyboard", "ToMainOrOrderKeyboard", "RequestPhoneNumberKeyboard"]
