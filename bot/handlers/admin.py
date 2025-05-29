import asyncio
import csv
from datetime import datetime
import io
from logging import Logger
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from filters import IsAdminFilter
from keyboards import ToMainMenuKeyboard
from models import Order
from service import OrderService, UserService

router = Router()
router.message.filter(IsAdminFilter())


class AdminStates(StatesGroup):
    viewing_orders = State()
    order_details = State()


ORDERS_PER_PAGE = 5


@router.message(F.text == "🔐 Панель администратора")
async def show_admin_panel(message: Message, state: FSMContext):
    """Отображение главной панели администратора"""
    await state.clear()

    text = "👨‍💼 <b>Панель администратора</b>"
    await message.answer(text, reply_markup=ToMainMenuKeyboard()())

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Новые заявки", callback_data="admin_new_orders")],
            [InlineKeyboardButton(text="📝 Все заявки", callback_data="admin_all_orders")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main")],
        ],
    )

    await message.answer("Выберите действие:", reply_markup=keyboard)


@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery, state: FSMContext):
    """Возврат в панель администратора"""
    await state.clear()

    text = "👨‍💼 <b>Панель администратора</b>"
    await callback.message.answer(text, reply_markup=ToMainMenuKeyboard()())  # type: ignore

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Новые заявки", callback_data="admin_new_orders")],
            [InlineKeyboardButton(text="📝 Все заявки", callback_data="admin_all_orders")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main")],
        ],
    )

    await callback.message.answer("Выберите действие:", reply_markup=keyboard)  # type: ignore
    await callback.answer()


@router.callback_query(F.data == "admin_new_orders")
async def show_new_orders(callback: CallbackQuery, state: FSMContext, order_service: OrderService):
    """Показать новые заявки (статус pending)"""
    await state.set_state(AdminStates.viewing_orders)
    await state.update_data(filter_status="pending", page=0)

    await show_orders_page(callback, state, order_service, status_filter="pending")


@router.callback_query(F.data == "admin_all_orders")
async def show_all_orders(callback: CallbackQuery, state: FSMContext, order_service: OrderService):
    """Показать все заявки"""
    await state.set_state(AdminStates.viewing_orders)
    await state.update_data(filter_status=None, page=0)

    await show_orders_page(callback, state, order_service)


async def show_orders_page(
    callback: CallbackQuery,
    state: FSMContext,
    order_service: OrderService,
    status_filter: Optional[str] = None,
    page: int = 0,
    delete_message: bool = True,
):
    if delete_message:
        await callback.message.delete()  # type: ignore
    """Отображение страницы с заявками"""
    if status_filter == "pending":
        orders = await order_service.get_pending()
        title = "📋 Новые заявки"
    else:
        orders = await order_service.get(with_author=True)
        title = "📝 Все заявки"

    if not orders:
        text = f"{title}\n\n❌ Заявки не найдены."
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]],
        )
        await callback.message.answer(text, reply_markup=keyboard)  # type: ignore
        await callback.answer()
        return UNHANDLED

    total_orders = len(orders)
    total_pages = (total_orders + ORDERS_PER_PAGE - 1) // ORDERS_PER_PAGE
    start_idx = page * ORDERS_PER_PAGE
    end_idx = min(start_idx + ORDERS_PER_PAGE, total_orders)
    page_orders = orders[start_idx:end_idx]

    text = f"{title}\n\n"

    for i, order in enumerate(page_orders, start=start_idx + 1):
        status_emoji = get_status_emoji(order.status.value)
        date_str = order.time.strftime("%d.%m.%Y %H:%M")

        author_info = f"ID: {order.author_id}"
        if hasattr(order, "author") and order.author:
            if order.author.username:
                author_info += f" (@{order.author.username})"
            if order.author.phone_number:
                author_info += f"\n📱 {order.author.phone_number}"

        text += (
            f"<b>{i}. Заказ #{order.id}</b> {status_emoji}\n"
            f"👤 {author_info}\n"
            f"📍 {order.address[:50]}{'...' if len(order.address) > 50 else ''}\n"
            f"📅 {date_str}\n"
            f"📊 Статус: {get_status_text(order.status.value)}\n\n"
        )

    keyboard = []

    for _, order in enumerate(page_orders, start=start_idx):
        keyboard.append([InlineKeyboardButton(text=f"📋 Заказ #{order.id}", callback_data=f"admin_order_{order.id}")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Пред.", callback_data=f"admin_page_{page-1}"))

    nav_buttons.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="ignore"))

    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="След. ▶️", callback_data=f"admin_page_{page+1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append(
        [
            InlineKeyboardButton(text="📤 Экспорт", callback_data=f"admin_export_{status_filter or 'all'}_{page}"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_refresh"),
            InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel"),
        ],
    )

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await callback.message.answer(text, reply_markup=markup)  # type: ignore
    await callback.answer()
    return UNHANDLED


@router.callback_query(F.data.startswith("admin_export_"))
async def export_orders(callback: CallbackQuery, state: FSMContext, order_service: OrderService):
    parts = str(callback.data).split("_")
    page = int(parts[3])
    status_filter = parts[2]

    if status_filter == "pending":
        orders = await order_service.get_pending()
        filename = "pending_orders_"
    else:
        orders = await order_service.get(with_author=True)
        filename = "all_orders_<"
    filename += datetime.now().strftime("%d-%m-%Y") + ">.csv"

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    writer.writerow(["ID", "User ID", "Username", "Phone", "Address", "Order Time", "Status", "Created At"])

    for order in orders:
        username = f"@{order.author.username}" if order.author and order.author.username else ""
        phone = order.author.phone_number if order.author and order.author.phone_number else ""

        order_time = order.time.strftime("%Y-%m-%d %H:%M:%S")
        created_at = order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else ""

        writer.writerow(
            [order.id, order.author_id, username, phone, order.address, order_time, order.status.value, created_at],
        )

    csv_data = buffer.getvalue().encode("utf-8")
    file = BufferedInputFile(csv_data, filename=filename)

    await callback.message.answer_document(  # type: ignore
        document=file,
        caption=f"Экспорт заказов ({'ожидают ответа' if status_filter == 'pending' else 'все'})",
    )
    await callback.answer("📤 Файл экспортирован")

    await asyncio.sleep(5)
    await show_orders_page(callback, state, order_service, status_filter, page, False)


@router.callback_query(F.data.startswith("admin_page_"))
async def handle_page_navigation(callback: CallbackQuery, state: FSMContext, order_service: OrderService):
    """Обработка навигации по страницам"""
    page = int(str(callback.data).split("_")[2])
    data = await state.get_data()

    await state.update_data(page=page)
    await show_orders_page(callback, state, order_service, data.get("filter_status"), page)


@router.callback_query(F.data == "admin_refresh")
async def refresh_orders(callback: CallbackQuery, state: FSMContext, order_service: OrderService):
    """Обновление списка заявок"""
    data = await state.get_data()
    page = data.get("page", 0)
    status_filter = data.get("filter_status")

    await show_orders_page(callback, state, order_service, status_filter, page)


@router.callback_query(F.data.startswith("admin_order_"))
async def show_order_details(
    callback: CallbackQuery,
    state: FSMContext,
    order_service: OrderService,
    user_service: UserService,
    order_id: int = -1,
    delete_message: bool = False,
):
    """Показать детали заявки"""
    if delete_message:
        await callback.message.delete()  # type: ignore
    if order_id == -1:
        order_id = int(str(callback.data).split("_")[2])

    order = await order_service.get_one(order_id)
    if not order:
        await callback.answer("Заявка не найдена")
        return

    author = await user_service.get_one(order.author_id)

    await state.set_state(AdminStates.order_details)
    await state.update_data(order_id=order_id)

    status_emoji = get_status_emoji(order.status.value)
    date_str = order.time.strftime("%d.%m.%Y %H:%M")
    created_str = order.created_at.strftime("%d.%m.%Y %H:%M")

    author_info = f"ID: {order.author_id}"
    if author:
        if author.username:
            author_info += f" (@{author.username})"
        author_info += f"\n📱 {author.phone_number or 'Не указан'}"

    text = (
        f"📋 <b>Заказ #{order.id}</b> {status_emoji}\n\n"
        f"👤 <b>Клиент:</b>\n{author_info}\n\n"
        f"📍 <b>Адрес:</b>\n{order.address}\n\n"
        f"📅 <b>Дата и время:</b> {date_str}\n"
        f"📊 <b>Статус:</b> {get_status_text(order.status.value)}\n"
        f"🕐 <b>Создан:</b> {created_str}\n\n"
        "Выберите действие:"
    )

    keyboard = []

    if order.status.value == "pending":
        keyboard.extend(
            [
                [InlineKeyboardButton(text="✅ Принять", callback_data=f"admin_accept_{order_id}")],
                [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_{order_id}")],
            ],
        )
    elif order.status.value == "accepted":
        keyboard.extend(
            [
                [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"admin_complete_{order_id}")],
                [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_{order_id}")],
            ],
        )
    elif order.status.value in ["completed", "rejected"]:
        keyboard.append([InlineKeyboardButton(text="🔄 Вернуть в работу", callback_data=f"admin_reopen_{order_id}")])

    """
    keyboard.append([InlineKeyboardButton(text="📝 Изменить статус", callback_data=f"admin_change_status_{order_id}")])
    """

    keyboard.extend(
        [
            [InlineKeyboardButton(text="◀️ К списку", callback_data="admin_back_to_list")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main")],
        ],
    )

    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await callback.message.answer(text, reply_markup=markup)  # type: ignore
    await callback.answer()


@router.callback_query(F.data.startswith("admin_accept_"))
async def accept_order(
    callback: CallbackQuery,
    order_service: OrderService,
    user_service: UserService,
    bot: Bot,
    logger: Logger,
    state: FSMContext,
):
    """Принять заявку"""
    order_id = int(str(callback.data).split("_")[2])

    order = await order_service.update_status(order_id, "accepted")

    if order is not None:
        await notify_client(bot, logger, order, user_service, "accepted")

        await callback.answer("✅ Заявка принята")
        await show_order_details(callback, state, order_service, user_service, delete_message=True)
    else:
        await callback.answer("❌ Ошибка при обновлении статуса")


@router.callback_query(F.data.startswith("admin_reject_"))
async def reject_order(
    callback: CallbackQuery,
    order_service: OrderService,
    user_service: UserService,
    bot: Bot,
    logger: Logger,
    state: FSMContext,
):
    """Отклонить заявку"""
    order_id = int(str(callback.data).split("_")[2])

    order = await order_service.update_status(order_id, "rejected")

    if order is not None:
        await notify_client(bot, logger, order, user_service, "rejected")

        await callback.answer("❌ Заявка отклонена")
        await show_order_details(callback, state, order_service, user_service, delete_message=True)
    else:
        await callback.answer("❌ Ошибка при обновлении статуса")


@router.callback_query(F.data.startswith("admin_complete_"))
async def complete_order(
    callback: CallbackQuery,
    order_service: OrderService,
    user_service: UserService,
    bot: Bot,
    logger: Logger,
    state: FSMContext,
):
    """Отметить заявку как выполненную"""
    order_id = int(str(callback.data).split("_")[2])

    order = await order_service.update_status(order_id, "completed")

    if order is not None:
        await notify_client(bot, logger, order, user_service, "completed")

        await callback.answer("✅ Заказ выполнен")
        await show_order_details(callback, state, order_service, user_service, delete_message=True)
    else:
        await callback.answer("❌ Ошибка при обновлении статуса")


@router.callback_query(F.data.startswith("admin_reopen_"))
async def reopen_order(
    callback: CallbackQuery,
    order_service: OrderService,
    user_service: UserService,
    bot: Bot,
    logger: Logger,
    state: FSMContext,
):
    """Вернуть заявку в работу"""
    order_id = int(str(callback.data).split("_")[2])

    order = await order_service.update_status(order_id, "pending")

    if order is not None:
        await notify_client(bot, logger, order, user_service, "reopen")

        await callback.answer("🔄 Заказ возвращен в работу")
        await show_order_details(callback, state, order_service, user_service, delete_message=True)
    else:
        await callback.answer("❌ Ошибка при обновлении статуса")


@router.callback_query(F.data.startswith("admin_change_status_"))
async def show_status_change_menu(callback: CallbackQuery, state: FSMContext):
    """Показать меню изменения статуса"""
    order_id = int(str(callback.data).split("_")[3])

    text = "📝 <b>Изменение статуса заказа</b>\n\nВыберите новый статус:"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏳ В ожидании", callback_data=f"admin_set_status_{order_id}_pending")],
            [InlineKeyboardButton(text="✅ Принята", callback_data=f"admin_set_status_{order_id}_accepted")],
            [InlineKeyboardButton(text="🎉 Выполнена", callback_data=f"admin_set_status_{order_id}_completed")],
            [InlineKeyboardButton(text="❌ Отклонена", callback_data=f"admin_set_status_{order_id}_rejected")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data=f"admin_order_{order_id}")],
        ],
    )

    await callback.message.answer(text, reply_markup=keyboard)  # type: ignore
    await callback.answer()


@router.callback_query(F.data.startswith("admin_set_status_"))
async def set_order_status(
    callback: CallbackQuery,
    order_service: OrderService,
    user_service: UserService,
    bot: Bot,
    logger: Logger,
    state: FSMContext,
):
    """Установить новый статус заказа"""
    parts = str(callback.data).split("_")
    logger.debug(parts)
    order_id = int(parts[3])
    new_status = parts[4]

    order = await order_service.update_status(order_id, new_status)

    if order is not None:
        if new_status == "rejected":
            await notify_client(bot, logger, order, user_service, "rejected")

        status_text = get_status_text(new_status)
        await callback.answer(f"✅ Статус изменен на: {status_text}")

        await show_order_details(callback, state, order_service, user_service, order_id=order_id)
    else:
        await callback.answer("❌ Ошибка при обновлении статуса")


@router.callback_query(F.data == "admin_back_to_list")
async def back_to_orders_list(callback: CallbackQuery, state: FSMContext, order_service: OrderService):
    """Возврат к списку заявок"""
    data = await state.get_data()
    page = data.get("page", 0)
    status_filter = data.get("filter_status")

    await state.set_state(AdminStates.viewing_orders)
    await show_orders_page(callback, state, order_service, status_filter, page, delete_message=False)


async def notify_client(bot: Bot, logger: Logger, order: Order, user_service: UserService, status: str):
    """Уведомление клиента об изменении статуса заказа"""
    try:

        author = await user_service.get_one(order.author_id)
        if not author:
            return

        date_str = order.time.strftime("%d.%m.%Y %H:%M")

        if status == "accepted":
            text = (
                "✅ <b>Ваш заказ принят!</b>\n\n"
                f"📋 <b>Заказ #{order.id}</b>\n"
                f"📍 <b>Адрес:</b> {order.address}\n"
                f"📅 <b>Дата и время:</b> {date_str}\n\n"
                "Мы свяжемся с вами для уточнения деталей."
            )
        elif status == "completed":
            text = (
                "🎉 <b>Ваш заказ выполнен!</b>\n\n"
                f"📋 <b>Заказ #{order.id}</b>\n"
                f"📍 <b>Адрес:</b> {order.address}\n"
                f"📅 <b>Дата и время:</b> {date_str}\n\n"
                "Спасибо за использование наших услуг!"
            )
        elif status == "rejected":
            text = (
                "❌ <b>Ваш заказ отклонен</b>\n\n"
                f"📋 <b>Заказ #{order.id}</b>\n"
                f"📍 <b>Адрес:</b> {order.address}\n"
                f"📅 <b>Дата и время:</b> {date_str}\n\n"
                "К сожалению, мы не можем выполнить ваш заказ.\n"
                "Вы можете оформить новый заказ с другими параметрами."
            )
        elif status == "reopen":
            text = (
                "🔄 <b>Ваш заказ возвращен в работу</b>\n\n"
                f"📋 <b>Заказ #{order.id}</b>\n"
                f"📍 <b>Адрес:</b> {order.address}\n"
                f"📅 <b>Дата и время:</b> {date_str}\n\n"
                "Мы свяжемся с вами для уточнения деталей."
            )
        else:
            return

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Новый заказ", callback_data="start_order")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_main")],
            ],
        )

        await bot.send_message(chat_id=author.id, text=text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {e}")


def get_status_emoji(status: str) -> str:
    """Получить эмодзи для статуса"""
    status_emojis = {"pending": "⏳", "accepted": "✅", "completed": "🎉", "rejected": "❌", "canceled": "🚫"}
    return status_emojis.get(status, "❓")


def get_status_text(status: str) -> str:
    """Получить текстовое описание статуса"""
    status_texts = {
        "pending": "В ожидании",
        "accepted": "Принят",
        "completed": "Выполнен",
        "rejected": "Отклонён",
        "canceled": "Отменён",
    }
    return status_texts.get(status, "Неизвестно")


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    """Игнорирование нажатий на неактивные кнопки"""
    await callback.answer()
    return UNHANDLED


__all__ = ["router"]
