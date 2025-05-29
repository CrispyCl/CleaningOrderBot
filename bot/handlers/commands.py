from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from keyboards import MainUserKeyboard, ToMainMenuKeyboard
from models import User

router = Router()


@router.callback_query(F.data == "to_main")
async def to_main_menu(callback: CallbackQuery, state: FSMContext, current_user: User):
    await state.clear()
    await process_start_command(callback.message, state, current_user=current_user)
    await callback.answer()


@router.message(CommandStart())
@router.message(F.text == "🏠 Главное меню")
async def process_start_command(message: Message, state: FSMContext, current_user: User) -> None:
    await state.clear()

    welcome_text = (
        "👋 <b>Добро пожаловать в нашего бота!</b>\n\n"
        "🧹 Мы предоставляем качественные услуги уборки.\n"
        "Оставьте заявку, и мы свяжемся с вами в ближайшее время!\n\n"
        "Нажмите кнопку ниже, чтобы оформить заказ:"
    )

    keyboard = MainUserKeyboard()(is_admin=current_user.is_staff)

    await message.answer(welcome_text, reply_markup=keyboard)


@router.message(Command("help"))
async def process_help_command(message: Message) -> None:
    help_text = (
        "ℹ️ <b>Помощь</b>\n\n"
        "Доступные команды:\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/order - Быстрое оформление заказа\n\n"
        "📝 <b>Как оформить заказ:</b>\n"
        "1. Нажмите 'Оформить заказ'\n"
        "2. Введите адрес\n"
        "3. Выберите дату и время\n"
        "4. Подтвердите заказ"
    )

    keyboard = ToMainMenuKeyboard()()

    await message.answer(help_text, reply_markup=keyboard)


@router.message(F.text == "ℹ️ Помощь")
async def help_callback(message: Message, current_user: User) -> None:
    help_text = (
        "ℹ️ <b>Помощь</b>\n\n"
        "📝 <b>Как оформить заказ:</b>\n"
        "1. Нажмите 'Оформить заказ'\n"
        "2. Введите адрес уборки\n"
        "3. Выберите удобную дату\n"
        "4. Выберите время\n"
        "5. Подтвердите заказ\n\n"
        "💡 <b>Полезная информация:</b>\n"
        "• Мы работаем ежедневно с 8:00 до 22:00\n"
        "• Заказ можно отменить до начала работ\n"
        "• Оплата производится после выполнения услуг"
    )

    keyboard = MainUserKeyboard()(is_admin=current_user.is_staff)

    await message.answer(help_text, reply_markup=keyboard)


__all__ = ["router"]
