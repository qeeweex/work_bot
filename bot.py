import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import logging

from db import add_user, get_user_by_telegram_id, add_order, get_orders_by_customer

API_TOKEN = "7985036267:AAHl2fN-aN216zwgmCspvo1s2GOypZ-U-1k"  # Замените на свой токен

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    # Добавляем пользователя в базу при первом запуске
    add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        role="customer"  # или "worker", если реализуете выбор роли
    )
    await message.answer("Привет! Вы зарегистрированы в системе.\nИспользуйте /help для списка команд.")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "/start — начать работу\n"
        "/help — список команд\n"
        "/profile — ваш профиль\n"
        "/orders — ваши заказы\n"
        "/addorder — добавить тестовый заказ"
    )

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
    orders = get_orders_by_customer(user[0])
    if not orders:
        await message.answer("У вас пока нет заказов.")
    else:
        text = "Ваши заказы:\n"
        for order in orders:
            text += f"ID: {order[0]}, Площадка: {order[3]}, Кол-во: {order[4]}, Статус: {order[6]}\n"
        await message.answer(text)

# Пример добавления заказа (можно сделать отдельной командой)
@dp.message(Command("addorder"))
async def cmd_addorder(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала зарегистрируйтесь через /start.")
        return
    # Пример: добавляем тестовый заказ
    add_order(
        customer_id=user[0],
        platform="VK",
        quantity=10,
        deadline="2025-07-01"
    )
    await message.answer("Заказ добавлен!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())