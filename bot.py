import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
import logging

API_TOKEN = "7985036267:AAHl2fN-aN216zwgmCspvo1s2GOypZ-U-1k"  # Замените на свой токен

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я бот для управления заказами.\nИспользуйте /help для списка команд.")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "/start — начать работу\n"
        "/help — список команд\n"
        "/profile — ваш профиль\n"
        "/orders — ваши заказы"
    )

@dp.message(Command("profile"))
async def cmd_profile(message: Message):
    # Здесь будет логика вывода профиля пользователя
    await message.answer("Ваш профиль: (здесь будет информация о пользователе)")

@dp.message(Command("orders"))
async def cmd_orders(message: Message):
    # Здесь будет логика вывода заказов пользователя
    await message.answer("Ваши заказы: (здесь будет список заказов)")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())