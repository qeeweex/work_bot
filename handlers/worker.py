from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from config import ADMINS
from db import (
    get_order_by_id, get_user_by_id, get_user_by_telegram_id,
    get_free_orders, get_orders_by_worker, assign_order_to_worker,
    set_order_status, get_orders_by_worker_and_status
)
from keyboards import get_order_inline_kb, history_filter_kb
from utils import format_order
from aiogram.fsm.state import StateFilter

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
                reply_markup=get_order_inline_kb(order[0])
            )

@router.message(Command("myorders"))
async def cmd_myorders(message: Message, state: FSMContext):
    await message.answer("Выберите, какие заказы показать:", reply_markup=history_filter_kb)
    await state.set_state("waiting_for_worker_order_status")

@router.message(StateFilter("waiting_for_worker_order_status"), lambda m: m.text in ["Активные", "Выполненные", "Отменённые"])
async def show_worker_orders_by_status(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    status_map = {
        "Активные": "Активен",
        "Выполненные": "Выполнен",
        "Отменённые": "Отменён"
    }
    status = status_map[message.text]
    orders = get_orders_by_worker_and_status(user[0], status)
    if not orders:
        await message.answer("Нет заказов с таким статусом.")
    else:
        for order in orders:
            await message.answer(format_order(order), parse_mode="HTML")
    await state.clear()

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
    set_order_status(order_id, "Выполнен")
    order = get_order_by_id(order_id)
    customer = get_user_by_id(order[1])
    telegram_id = customer[1]  # (id, telegram_id, ...)
    await callback.message.edit_text(
        "✅ <b>Заказ отправлен на проверку!</b>\n"
        "Ваш заказ отправлен заказчику. Ожидайте подтверждения.",
        parse_mode="HTML"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить выполнение", callback_data=f"confirm_{order_id}")]
    ])
    await callback.bot.send_message(
        telegram_id,
        f"📝 <b>Ваш заказ №{order_id} выполнен!</b>\n"
        "Проверьте результат и, если всё хорошо, подтвердите выполнение заказа.",
        reply_markup=confirm_kb,
        parse_mode="HTML"
    )
    for admin_id in ADMINS:
        await callback.bot.send_message(
            admin_id,
            f"🔔 <b>Заказ №{order_id} выполнен исполнителем</b>\n"
            "Ожидает подтверждения заказчиком.",
            parse_mode="HTML"
        )