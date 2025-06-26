from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from config import ADMINS
from db import get_order_by_id

from db import get_user_by_telegram_id, get_free_orders, get_orders_by_worker, assign_order_to_worker, set_order_status, delete_done_orders, get_user_by_id
from keyboards import get_order_inline_kb
from utils import format_order

router = Router()

@router.message(Command("workorders"))
async def cmd_workorders(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user or user[3] != "worker":
        await message.answer("Эта команда только для исполнителей.")
        return
    orders = get_free_orders()
    if not orders:
        await message.answer("Нет доступных заказов.")
    else:
        for order in orders:
            await message.answer(
                format_order(order),
                parse_mode="HTML",
                reply_markup=get_order_inline_kb(order[0], user[3], order[6])
            )

@router.message(Command("myorders"))
async def cmd_myorders(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user or user[3] != "worker":
        await message.answer("Эта команда только для исполнителей.")
        return
    orders = get_orders_by_worker(user[0])
    if not orders:
        await message.answer("У вас пока нет взятых заказов.")
    else:
        for order in orders:
            await message.answer(
                format_order(order),
                parse_mode="HTML",
                reply_markup=get_order_inline_kb(order[0], user[3], order[6])
            )

@router.callback_query(lambda c: c.data.startswith("take_"))
async def process_take_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    user = get_user_by_telegram_id(callback.from_user.id)
    success = assign_order_to_worker(order_id, user[0])
    if success:
        await callback.message.edit_text("Вы взяли заказ!", parse_mode="HTML")
    else:
        await callback.answer("Не удалось взять заказ.", show_alert=True)

@router.callback_query(lambda c: c.data.startswith("done_"))
async def process_done_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    user = get_user_by_telegram_id(callback.from_user.id)
    set_order_status(order_id, "done")
    order = get_order_by_id(order_id)
    # Получаем telegram_id заказчика
    customer = get_user_by_id(order[1])
    telegram_id = customer[1]  # (id, telegram_id, ...)
    await callback.message.edit_text("Заказ завершён и отправлен на проверку заказчику!", parse_mode="HTML")
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить выполнение", callback_data=f"confirm_{order_id}")]
    ])
    await callback.bot.send_message(
        telegram_id,
        f"Ваш заказ №{order_id} выполнен исполнителем!\nПроверьте результат и подтвердите выполнение.",
        reply_markup=confirm_kb
    )
    # Уведомляем админа
    for admin_id in ADMINS:
        await callback.bot.send_message(
            admin_id,
            f"Заказ №{order_id} отмечен исполнителем как выполненный и отправлен заказчику на подтверждение."
        )