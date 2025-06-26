from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from db import get_all_users, get_all_orders
from config import ADMINS

router = Router()

def is_admin(user_id):
    return str(user_id) in ADMINS

@router.message(Command("admin"))
async def cmd_admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён. Только для админов.")
        return
    await message.answer(
        "<b>Панель администратора</b>\n"
        "/users — список пользователей\n"
        "/orders — список всех заказов",
        parse_mode="HTML"
    )

@router.message(Command("users"))
async def cmd_users(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён. Только для админов.")
        return
    users = get_all_users()
    if not users:
        await message.answer("Пользователей нет.")
    else:
        text = "<b>Пользователи:</b>\n"
        for user in users:
            text += f"ID: <code>{user[0]}</code>, Username: @{user[2]}, Роль: {user[3]}\n"
        await message.answer(text, parse_mode="HTML")

@router.message(Command("orders"))
async def cmd_orders(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Доступ запрещён. Только для админов.")
        return
    orders = get_all_orders()
    if not orders:
        await message.answer("Заказов нет.")
    else:
        text = "<b>Все заказы:</b>\n"
        for order in orders:
            text += (
                f"ID: <code>{order[0]}</code>, "
                f"Площадка: {order[3]}, "
                f"Кол-во: {order[4]}, "
                f"Дедлайн: {order[5]}, "
                f"Статус: {order[6]}\n"
            )
        await message.answer(text, parse_mode="HTML")