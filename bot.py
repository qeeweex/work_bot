import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import logging
import sqlite3

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

# FSM для выбора роли
class RegStates(StatesGroup):
    choosing_role = State()

role_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Я заказчик")],
        [KeyboardButton(text="Я исполнитель")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    if user:
        await message.answer("Вы уже зарегистрированы.\nИспользуйте /help для списка команд.")
        return
    await message.answer("Выберите вашу роль:", reply_markup=role_kb)
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
        await message.answer(f"Ваша роль изменена на {'заказчик' if role == 'customer' else 'исполнитель'}!", reply_markup=types.ReplyKeyboardRemove())
    else:
        add_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            role=role
        )
        await message.answer(f"Вы зарегистрированы как {'заказчик' if role == 'customer' else 'исполнитель'}!", reply_markup=types.ReplyKeyboardRemove())
    await state.clear()

# FSM для создания заказа
class OrderStates(StatesGroup):
    waiting_for_platform = State()
    waiting_for_quantity = State()
    waiting_for_deadline = State()

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
            "/profile — ваш профиль\n"
            "/orders — ваши заказы\n"
            "/addorder — добавить заказ\n"
            "/deleteorder <id> — удалить заказ\n"
            "/changerole — сменить роль"
        )
    elif user[3] == "worker":
        await message.answer(
            "/profile — ваш профиль\n"
            "/orders — ваши заказы\n"
            "/workorders — доступные заказы\n"
            "/myorders — ваши взятые заказы\n"
            "/takeorder <id> — взять заказ\n"
            "/done <id> — завершить заказ\n"
            "/changerole — сменить роль"
        )
    else:
        await message.answer("Неизвестная роль пользователя.")

@dp.message(Command("profile"))
async def cmd_profile(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if user:
        await message.answer(f"Ваш профиль:\nID: {user[0]}\nUsername: {user[2]}\nРоль: {user[3]}")
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
        text = "Ваши заказы:\n"
        for order in orders:
            text += f"ID: {order[0]}, Площадка: {order[3]}, Кол-во: {order[4]}, Статус: {order[6]}\n"
        await message.answer(text)

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
        text = "Доступные заказы:\n"
        for order in orders:
            text += f"ID: {order[0]}, Площадка: {order[3]}, Кол-во: {order[4]}, Дедлайн: {order[5]}\n"
        await message.answer(text)

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
        text = "Ваши заказы:\n"
        for order in orders:
            text += f"ID: {order[0]}, Площадка: {order[3]}, Кол-во: {order[4]}, Статус: {order[6]}\n"
        await message.answer(text)

@dp.message(Command("takeorder"))
async def cmd_takeorder(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user or user[3] != "worker":
        await message.answer("Эта команда только для исполнителей.")
        return

    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используйте команду так: /takeorder <id_заказа>")
        return

    order_id = int(parts[1])
    success = assign_order_to_worker(order_id, user[0])
    if success:
        await message.answer(f"Вы взяли заказ №{order_id} в работу!")
    else:
        await message.answer("Не удалось взять заказ. Возможно, его уже взяли или он не существует.")

@dp.message(Command("done"))
async def cmd_done(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user or user[3] != "worker":
        await message.answer("Эта команда только для исполнителей.")
        return

    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используйте команду так: /done <id_заказа>")
        return

    order_id = int(parts[1])

    # Проверяем, что заказ действительно принадлежит этому исполнителю и в работе
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM orders WHERE id = ? AND worker_id = ? AND status = 'in_progress'",
        (order_id, user[0])
    )
    order = cursor.fetchone()
    conn.close()

    if not order:
        await message.answer("Вы не можете завершить этот заказ (он не ваш или не в работе).")
        return

    set_order_status(order_id, "done")
    delete_done_orders()
    await message.answer(f"Заказ №{order_id} отмечен как выполненный и удалён из базы!")

@dp.message(Command("deleteorder"))
async def cmd_deleteorder(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user or user[3] != "customer":
        await message.answer("Эта команда только для заказчиков.")
        return

    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используйте команду так: /deleteorder <id_заказа>")
        return

    order_id = int(parts[1])
    success = delete_order(order_id, user[0])
    if success:
        await message.answer(f"Заказ №{order_id} удалён.")
    else:
        await message.answer("Не удалось удалить заказ. Можно удалять только свои новые заказы.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())