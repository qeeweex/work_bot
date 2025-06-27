from aiogram.fsm.context import FSMContext
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from config import ADMINS
from db import (
    get_order_by_id, get_user_by_id, get_user_by_telegram_id,
    get_free_orders, assign_order_to_worker,
    set_order_status, get_orders_by_worker_and_status, delete_done_orders
)
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
                reply_markup=get_order_inline_kb(order[0])
            )

@router.message(Command("myorders"))
async def my_orders_handler(message: types.Message):
    user = get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Вы не зарегистрированы.")
        return

    if user[3] != "worker":
        await message.answer("❌ Команда доступна только исполнителям. Используйте /changerole, чтобы сменить роль.")
        return

    orders = get_orders_by_worker_and_status(user[0], "in_progress")
    if not orders:
        await message.answer("📭 У вас нет активных заказов.")
        return

    for order in orders:
        text = format_order(order)
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Завершить", callback_data=f"done_{order[0]}")]
        ])
        await message.answer(text, parse_mode="HTML", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith("take_"))
async def process_take_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    user = get_user_by_telegram_id(callback.from_user.id)
    success = assign_order_to_worker(order_id, user[0])
    if success:
        await callback.message.edit_text("Вы взяли заказ!", parse_mode="HTML")
    else:
        await callback.answer("Не удалось взять заказ.", show_alert=True)

@router.callback_query(F.data.startswith("done_"))
async def done_order_handler(callback: types.CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    order = get_order_by_id(order_id)

    if not order:
        await callback.message.answer("❌ Заказ не найден.")
        await callback.answer()
        return

    set_order_status(order_id, "Выполнен")
    delete_done_orders()  # Удаляем завершённые заказы

    await callback.message.edit_reply_markup()
    await callback.message.answer(f"✅ Заказ #{order_id} отмечен как выполненный.")
    await callback.answer()

    # Уведомим заказчика и админа
    customer = get_user_by_id(order[1])
    telegram_id = customer[1]  # (id, telegram_id, ...)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить выполнение", callback_data=f"confirm_{order_id}")]
    ])
    await callback.bot.send_message(
        telegram_id,
        f"📝 <b>Ваш заказ №{order_id} выполнен!</b>\n"
        "Проверьте результат и подтвердите выполнение.",
        reply_markup=confirm_kb,
        parse_mode="HTML"
    )
    for admin_id in ADMINS:
        await callback.bot.send_message(
            admin_id,
            f"🔔 <b>Заказ №{order_id} завершён исполнителем</b>\n"
            "Ожидает подтверждения заказчиком.",
            parse_mode="HTML"
        )

@router.message(Command("testworker"))
async def test_handler(message: types.Message):
    print("✅ Обработчик из worker.py сработал!")
    await message.answer("✅ worker.py подключён и работает!")