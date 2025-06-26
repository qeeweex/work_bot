import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
import logging
import sqlite3

from states import RegStates, OrderStates
from keyboards import role_kb, customer_kb, worker_kb, get_order_inline_kb
from utils import format_order, is_valid_date

from config import API_TOKEN, DB_NAME, ADMINS
from db import (
    add_user, get_user_by_telegram_id, add_order, get_orders_by_customer,
    assign_order_to_worker, get_free_orders, set_order_status, get_orders_by_worker,
    delete_order, delete_done_orders
)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    if user:
        await message.answer(
            "👋 <b>Вы уже зарегистрированы!</b>\n"
            "ℹ️ Используйте /help для списка команд.",
            parse_mode="HTML"
        )
        return
    await message.answer(
        "👋 <b>Добро пожаловать в WorkBot!</b>\n\n"
        "📝 Здесь вы можете создавать и выполнять заказы.\n"
        "👇 Для начала выберите вашу роль:",
        reply_markup=role_kb,
        parse_mode="HTML"
    )
    await state.set_state(RegStates.choosing_role)

def update_user_role(telegram_id, new_role):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = ? WHERE telegram_id = ?", (new_role, telegram_id))
    conn.commit()
    conn.close()

@dp.message(Command("changerole"))
async def cmd_changerole(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала зарегистрируйтесь через /start.")
        return
    await message.answer("Выберите новую роль:", reply_markup=role_kb)
    await state.set_state(RegStates.choosing_role)

@dp.message(RegStates.choosing_role)
async def process_role(message: Message, state: FSMContext):
    if message.text == "Я заказчик":
        role = "customer"
    elif message.text == "Я исполнитель":
        role = "worker"
    else:
        await message.answer("Пожалуйста, выберите роль с помощью кнопок.")
        return

    user = get_user_by_telegram_id(message.from_user.id)
    if user:
        update_user_role(message.from_user.id, role)
        await message.answer(
            f"Ваша роль изменена на {'заказчик' if role == 'customer' else 'исполнитель'}!",
            reply_markup=customer_kb if role == "customer" else worker_kb
        )
    else:
        add_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            role=role
        )
        await message.answer(
            f"Вы зарегистрированы как {'заказчик' if role == 'customer' else 'исполнитель'}!",
            reply_markup=customer_kb if role == "customer" else worker_kb
        )
    await state.clear()

@dp.message(Command("addorder"))
async def start_add_order(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user or user[3] != "customer":
        await message.answer("Эта команда только для заказчиков.")
        return
    await message.answer("Введите площадку (например, VK, Telegram, Instagram):")
    await state.set_state(OrderStates.waiting_for_platform)

@dp.message(OrderStates.waiting_for_platform)
async def order_platform(message: Message, state: FSMContext):
    await state.update_data(platform=message.text)
    await message.answer("Введите количество:")
    await state.set_state(OrderStates.waiting_for_quantity)

@dp.message(OrderStates.waiting_for_quantity)
async def order_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число.")
        return
    await state.update_data(quantity=int(message.text))
    await message.answer("Введите дедлайн (например, 2025-07-01):")
    await state.set_state(OrderStates.waiting_for_deadline)

@dp.message(OrderStates.waiting_for_deadline)
async def order_deadline(message: Message, state: FSMContext):
    if not is_valid_date(message.text):
        await message.answer("Пожалуйста, введите дату в формате YYYY-MM-DD.")
        return
    data = await state.get_data()
    platform = data["platform"]
    quantity = data["quantity"]
    deadline = message.text

    user = get_user_by_telegram_id(message.from_user.id)
    add_order(
        customer_id=user[0],
        platform=platform,
        quantity=quantity,
        deadline=deadline
    )
    await message.answer(f"Заказ создан!\nПлощадка: {platform}\nКол-во: {quantity}\nДедлайн: {deadline}")
    await state.clear()

@dp.message(Command("help"))
async def cmd_help(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала зарегистрируйтесь через /start.")
        return
    if user[3] == "customer":
        await message.answer(
            "<b>Доступные команды:</b>\n"
            "/profile — ваш профиль\n"
            "/orders — ваши заказы\n"
            "/addorder — добавить заказ\n"
            "/changerole — сменить роль\n\n"
            "❗️ Для удаления заказа используйте кнопку <b>Удалить</b> под нужным заказом.",
            parse_mode="HTML",
            reply_markup=customer_kb
        )
    elif user[3] == "worker":
        await message.answer(
            "<b>Доступные команды:</b>\n"
            "/profile — ваш профиль\n"
            "/orders — ваши заказы\n"
            "/workorders — доступные заказы\n"
            "/myorders — ваши взятые заказы\n"
            "/changerole — сменить роль\n\n"
            "❗️ Для взятия или завершения заказа используйте кнопки <b>Взять заказ</b> и <b>Завершить</b> под заказом.",
            parse_mode="HTML",
            reply_markup=worker_kb
        )
    else:
        await message.answer("Неизвестная роль пользователя.")

@dp.message(Command("profile"))
async def cmd_profile(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if user:
        await message.answer(
            f"<b>Ваш профиль</b>\n"
            f"ID: <code>{user[0]}</code>\n"
            f"Username: @{user[2]}\n"
            f"Роль: <i>{user[3]}</i>",
            parse_mode="HTML"
        )
    else:
        await message.answer("Пользователь не найден.")

@dp.message(Command("orders"))
async def cmd_orders(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала зарегистрируйтесь через /start.")
        return
    if user[3] == "customer":
        orders = get_orders_by_customer(user[0])
    else:
        orders = get_orders_by_worker(user[0])
    if not orders:
        await message.answer("У вас пока нет заказов.")
    else:
        for order in orders:
            await message.answer(
                format_order(order),
                parse_mode="HTML",
                reply_markup=get_order_inline_kb(order[0], user[3], order[6])
            )

@dp.message(Command("workorders"))
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

@dp.message(Command("myorders"))
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

@dp.callback_query(lambda c: c.data.startswith("take_"))
async def process_take_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    user = get_user_by_telegram_id(callback.from_user.id)
    success = assign_order_to_worker(order_id, user[0])
    if success:
        await callback.message.edit_text("Вы взяли заказ!", parse_mode="HTML")
    else:
        await callback.answer("Не удалось взять заказ.", show_alert=True)

@dp.callback_query(lambda c: c.data.startswith("done_"))
async def process_done_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    user = get_user_by_telegram_id(callback.from_user.id)
    set_order_status(order_id, "done")
    delete_done_orders()
    await callback.message.edit_text("Заказ завершён и удалён!", parse_mode="HTML")

@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def process_delete_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    user = get_user_by_telegram_id(callback.from_user.id)
    success = delete_order(order_id, user[0])
    if success:
        await callback.message.edit_text("Заказ удалён!", parse_mode="HTML")
    else:
        await callback.answer("Не удалось удалить заказ.", show_alert=True)

@dp.message(Command("takeorder"))
async def cmd_takeorder(message: Message):
    await message.answer("Теперь заказы берутся через кнопки под каждым заказом!")

@dp.message(Command("done"))
async def cmd_done(message: Message):
    await message.answer("Теперь завершать заказы можно через кнопки под каждым заказом!")

@dp.message(Command("deleteorder"))
async def cmd_deleteorder(message: Message):
    await message.answer("Теперь удалять заказы можно через кнопки под каждым заказом!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())