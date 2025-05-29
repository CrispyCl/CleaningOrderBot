from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from models import User

router = Router()


@router.callback_query(F.data == "to_main")
async def to_main_menu(callback: CallbackQuery, state: FSMContext, current_user: User):
    await state.clear()
    await process_start_command(callback.message, state, current_user=current_user)
    await callback.answer()


@router.message(CommandStart())
@router.message(F.text == "🏠 На главную")
async def process_start_command(message: Message, state: FSMContext) -> None:
    await state.clear()

    welcome_text = "👋 <b>Добро пожаловать в нашего бота!</b>\n\n"

    await message.answer(welcome_text)


__all__ = ["router"]
