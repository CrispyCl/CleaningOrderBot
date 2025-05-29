import calendar
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    MaybeInaccessibleMessageUnion,
    Message,
)

from keyboards import RequestPhoneNumberKeyboard, ToMainMenuKeyboard, ToMainOrOrderKeyboard
from models import User
from service import OrderService, UserService

router = Router()


class OrderStates(StatesGroup):
    waiting_for_address = State()
    waiting_for_date = State()
    waiting_for_time = State()
    confirmation = State()


async def phone_required(event, current_user: User) -> bool:
    if current_user and not current_user.phone_number:
        # Получаем message или callback из аргументов
        if event:
            await request_phone_number(event)
            return True

    return False


async def request_phone_number(event):
    """Запрос номера телефона у пользователя"""
    text = (
        "📱 <b>Требуется номер телефона</b>\n\n"
        "Для оформления заказа необходимо предоставить ваш номер телефона.\n"
        "Нажмите кнопку ниже, чтобы поделиться номером:"
    )

    keyboard = RequestPhoneNumberKeyboard()()

    if isinstance(event, Message):
        await event.answer(text, reply_markup=keyboard)
    elif isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=keyboard)  # type: ignore
        await event.answer("Необходимо предоставить номер телефона")


@router.message(F.contact)
async def process_contact(message: Message, current_user: User, user_service: UserService):
    """Обработка полученного контакта"""
    if message.contact and str(message.contact.user_id) == current_user.id:
        await user_service.update_phone_number(current_user.id, message.contact.phone_number)

        await message.answer(
            "✅ <b>Спасибо!</b>\n\n" "Ваш номер телефона сохранен. Теперь вы можете пользоваться всеми функциями бота.",
            reply_markup=ToMainMenuKeyboard()(),
        )
    else:
        await message.answer(
            "❌ Пожалуйста, поделитесь своим номером телефона, используя кнопку ниже.",
            reply_markup=RequestPhoneNumberKeyboard()(),
        )


@router.message(F.text == "🛒 Оформить заказ")
async def start_order_hander(message: Message, state: FSMContext, current_user: User):
    if await phone_required(message, current_user):
        return
    await start_order_process(message, state, edit_message=False)


async def start_order_process(message: MaybeInaccessibleMessageUnion, state: FSMContext, edit_message: bool = False):
    """Начало процесса оформления заказа"""
    await state.set_state(OrderStates.waiting_for_address)

    text = (
        "📍 <b>Шаг 1 из 3: Адрес</b>\n\n"
        "Пожалуйста, введите адрес, где необходимо выполнить уборку:\n\n"
        "Например: <i>г. Москва, ул. Ленина, д. 10, кв. 25</i>"
    )

    keyboard = ToMainMenuKeyboard()()

    if edit_message:
        await message.answer(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "back_to_address")
async def back_to_address(callback: CallbackQuery, state: FSMContext):
    await start_order_process(callback.message, state, edit_message=False)  # type: ignore
    await callback.answer()


@router.message(OrderStates.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    """Обработка введенного адреса"""
    address = str(message.text).strip()

    if len(address) < 10:
        await message.answer(
            "❌ Пожалуйста, введите полный адрес (минимум 10 символов).\n"
            "Например: г. Москва, ул. Ленина, д. 10, кв. 25",
        )
        return

    await state.update_data(address=address)
    await state.set_state(OrderStates.waiting_for_date)

    # Создаем календарь для выбора даты
    today = datetime.now()
    keyboard = create_calendar_keyboard(today.year, today.month)

    await message.answer(
        "📅 <b>Шаг 2 из 3: Дата</b>\n\n" f"Адрес: <i>{address}</i>\n\n" "Выберите удобную дату для уборки:",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "back_to_date")
async def back_to_date(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору даты"""
    await state.set_state(OrderStates.waiting_for_date)

    data = await state.get_data()
    today = datetime.now()
    keyboard = create_calendar_keyboard(today.year, today.month)

    await callback.message.answer(  # type: ignore
        "📅 <b>Шаг 2 из 3: Дата</b>\n\n" f"Адрес: <i>{data['address']}</i>\n\n" "Выберите удобную дату для уборки:",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("calendar_"))
async def handle_calendar_navigation(callback: CallbackQuery, state: FSMContext):
    """Обработка навигации по календарю"""
    action = str(callback.data).split("_")[1]
    year = int(str(callback.data).split("_")[2])
    month = int(str(callback.data).split("_")[3])

    if action == "prev":
        # Переход к предыдущему месяцу
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1
    elif action == "next":
        # Переход к следующему месяцу
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1

    # Ограничиваем навигацию (не позволяем уходить в прошлое дальше текущего месяца)
    today = datetime.now()
    target_date = datetime(year, month, 1)
    current_month = datetime(today.year, today.month, 1)

    if target_date < current_month:
        await callback.answer("❌ Нельзя выбрать прошедший месяц")
        return UNHANDLED

    keyboard = create_calendar_keyboard(year, month)

    data = await state.get_data()
    await callback.message.answer(  # type: ignore
        "📅 <b>Шаг 2 из 3: Дата</b>\n\n" f"Адрес: <i>{data['address']}</i>\n\n" "Выберите удобную дату для уборки:",
        reply_markup=keyboard,
    )
    await callback.answer()
    return UNHANDLED


def create_calendar_keyboard(year: int, month: int):
    """Создание клавиатуры-календаря для указанного месяца и года"""
    today = datetime.now()
    keyboard = []

    # Заголовок с месяцем и годом
    month_names = {
        1: "Январь",
        2: "Февраль",
        3: "Март",
        4: "Апрель",
        5: "Май",
        6: "Июнь",
        7: "Июль",
        8: "Август",
        9: "Сентябрь",
        10: "Октябрь",
        11: "Ноябрь",
        12: "Декабрь",
    }
    month_year = f"{month_names[month]} {year}"

    # Кнопки навигации по месяцам
    nav_row = []

    # Кнопка "предыдущий месяц" (показываем только если это не текущий месяц)
    current_month_date = datetime(today.year, today.month, 1)
    target_month_date = datetime(year, month, 1)

    if target_month_date > current_month_date:
        nav_row.append(InlineKeyboardButton(text="◀️", callback_data=f"calendar_prev_{year}_{month}"))
    else:
        nav_row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    nav_row.append(InlineKeyboardButton(text=f"📅 {month_year}", callback_data="ignore"))

    # Кнопка "следующий месяц" (ограничиваем 6 месяцами)
    max_date = current_month_date + timedelta(days=180)
    if target_month_date < max_date:
        nav_row.append(InlineKeyboardButton(text="▶️", callback_data=f"calendar_next_{year}_{month}"))
    else:
        nav_row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    keyboard.append(nav_row)

    # Дни недели
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    keyboard.append([InlineKeyboardButton(text=day, callback_data="ignore") for day in weekdays])

    # Получаем календарь указанного месяца
    cal = calendar.monthcalendar(year, month)

    for week in cal:
        week_buttons = []
        for day in week:
            if day == 0:
                week_buttons.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                date_obj = datetime(year, month, day)

                # Проверяем, что дата не в прошлом
                if date_obj.date() > today.date() and date_obj.date() <= today.date() + timedelta(days=180):
                    week_buttons.append(
                        InlineKeyboardButton(text=str(day), callback_data=f"date_{date_obj.strftime('%Y-%m-%d')}"),
                    )
                else:
                    week_buttons.append(InlineKeyboardButton(text="❌", callback_data="ignore"))
        keyboard.append(week_buttons)

    # Кнопки навигации и отмены
    keyboard.append(
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_address"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order"),
        ],
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data.startswith("date_"))
async def process_date_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты"""
    date_str = str(callback.data).split("_")[1]
    selected_date = datetime.strptime(date_str, "%Y-%m-%d")

    await state.update_data(date=date_str, date_formatted=selected_date.strftime("%d.%m.%Y"))
    await state.set_state(OrderStates.waiting_for_time)

    # Создаем клавиатуру для выбора времени
    keyboard = create_time_keyboard()

    data = await state.get_data()
    await callback.message.answer(  # type: ignore
        "🕐 <b>Шаг 3 из 3: Время</b>\n\n"
        f"Адрес: <i>{data['address']}</i>\n"
        f"Дата: <i>{data['date_formatted']}</i>\n\n"
        "Выберите удобное время для уборки:",
        reply_markup=keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_time")
async def back_to_time(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору времени"""
    await state.set_state(OrderStates.waiting_for_time)

    data = await state.get_data()
    keyboard = create_time_keyboard()

    await callback.message.answer(  # type: ignore
        "🕐 <b>Шаг 3 из 3: Время</b>\n\n"
        f"Адрес: <i>{data['address']}</i>\n"
        f"Дата: <i>{data['date_formatted']}</i>\n\n"
        "Выберите удобное время для уборки:",
        reply_markup=keyboard,
    )
    await callback.answer()


def create_time_keyboard():
    """Создание клавиатуры для выбора времени"""
    times = [
        "08:00",
        "09:00",
        "10:00",
        "11:00",
        "12:00",
        "13:00",
        "14:00",
        "15:00",
        "16:00",
        "17:00",
        "18:00",
        "19:00",
        "20:00",
        "21:00",
        "22:00",
    ]

    keyboard = []
    row = []
    for i, time in enumerate(times):
        row.append(InlineKeyboardButton(text=time, callback_data=f"time_{time}"))
        if (i + 1) % 3 == 0:  # По 3 кнопки в ряд
            keyboard.append(row)
            row = []

    if row:  # Добавляем оставшиеся кнопки
        keyboard.append(row)

    # Кнопки навигации
    keyboard.append(
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_date"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order"),
        ],
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data.startswith("time_"))
async def process_time_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    time_str = str(callback.data).split("_")[1]
    await state.update_data(time=time_str)
    await state.set_state(OrderStates.confirmation)

    # Показываем подтверждение заказа
    data = await state.get_data()

    confirmation_text = (
        "✅ <b>Подтверждение заказа</b>\n\n"
        f"📍 <b>Адрес:</b> {data['address']}\n"
        f"📅 <b>Дата:</b> {data['date_formatted']}\n"
        f"🕐 <b>Время:</b> {time_str}\n\n"
        "Подтвердите заказ или вернитесь для изменения данных:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="confirm_order")],
            [InlineKeyboardButton(text="◀️ Изменить время", callback_data="back_to_time")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_order")],
        ],
    )

    await callback.message.answer(confirmation_text, reply_markup=keyboard)  # type: ignore
    await callback.answer()


@router.callback_query(F.data == "confirm_order")
async def confirm_order(callback: CallbackQuery, state: FSMContext, current_user: User, order_service: OrderService):
    """Подтверждение и сохранение заказа"""
    data = await state.get_data()

    # Создание заказа
    date_obj = datetime.strptime(data["date"] + " " + data["time"], "%Y-%m-%d %H:%M")
    order_id = await order_service.create(
        author_id=current_user.id,
        address=data["address"],
        time=date_obj,
    )

    if order_id == -1:
        error_text = (
            "❌ <b>Ошибка!</b>\n\n" "Извините, произошла ошибка при создании заказа. Пожалуйста, попробуйте еще раз."
        )
        await callback.message.answer(error_text, reply_markup=ToMainOrOrderKeyboard()())  # type: ignore
        return

    # Уведомление пользователя
    success_text = (
        "🎉 <b>Спасибо! Ваш заказ принят.</b>\n\n"
        f"📍 <b>Адрес:</b> {data['address']}\n"
        f"📅 <b>Дата:</b> {data['date_formatted']}\n"
        f"🕐 <b>Время:</b> {data['time']}\n\n"
        "✅ Мы свяжемся с вами в ближайшее время для уточнения деталей."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main")],
            [InlineKeyboardButton(text="❌ Отменить заказ", callback_data="cancel_this_order")],
        ],
    )

    await callback.message.answer(success_text, reply_markup=keyboard)  # type: ignore

    await state.clear()
    await callback.answer("Заказ успешно оформлен!")


@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    """Отмена оформления заказа"""
    await state.clear()

    text = (
        "❌ <b>Заказ отменен</b>\n\n"
        "Вы можете оформить новый заказ в любое время.\n"
        "Нажмите кнопку ниже, чтобы вернуться в главное меню:"
    )

    keyboard = ToMainOrOrderKeyboard()()

    await callback.message.answer(text, reply_markup=keyboard)  # type: ignore
    await callback.answer("Заказ отменен")


@router.callback_query(F.data == "cancel_this_order")
async def cancel_existing_order(callback: CallbackQuery, current_user: User, order_service: OrderService):
    """Отмена уже оформленного заказа"""
    # Здесь будет логика отмены заказа в базе данных

    orders = await order_service.get_by_author(current_user.id)
    if not orders:
        text = "У вас нет активных заказов."
        keyboard = ToMainMenuKeyboard()()
        await callback.message.answer("У вас нет активных заказов.", reply_markup=keyboard)  # type: ignore
        await callback.answer()
        return

    last_order = orders[-1]
    await order_service.update_status(last_order.id, "canceled")

    text = "❌ <b>Заказ отменен</b>\n\n" "Ваш заказ успешно отменен."

    keyboard = ToMainOrOrderKeyboard()()

    await callback.message.answer(text, reply_markup=keyboard)  # type: ignore
    await callback.answer("Заказ отменен")


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    """Игнорирование нажатий на неактивные кнопки"""
    await callback.answer()
    return UNHANDLED


__all__ = ["router", "start_order_hander"]
