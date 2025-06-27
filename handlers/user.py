from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from db import (
    get_user_by_telegram_id, add_user, update_user_role, add_order,
    set_order_status, delete_done_orders
)
from keyboards import role_kb, customer_kb, worker_kb
from states import RegStates, OrderStates
from utils import is_valid_date
from config import ADMINS

router = Router()

@router.message(Command("start"))
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

@router.message(Command("help"))
async def cmd_help(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала зарегистрируйтесь через /start.")
        return
    if user[3] == "worker":
        await message.answer(
            "<b>Доступные команды для исполнителя:</b>\n"
            "/profile — ваш профиль\n"
            "/workorders — доступные заказы\n"
            "/myorders — мои заказы\n"
            "/changerole — сменить роль\n"
            "❗️ Для работы с заказами используйте кнопки под сообщениями.",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "<b>Доступные команды для заказчика:</b>\n"
            "/profile — ваш профиль\n"
            "/orders — ваши заказы\n"
            "/addorder — добавить заказ\n"
            "/changerole — сменить роль\n"
            "❗️ Для работы с заказами используйте кнопки под сообщениями.",
            parse_mode="HTML"
        )

@router.message(Command("changerole"))
async def cmd_changerole(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала зарегистрируйтесь через /start.")
        return
    await message.answer("Выберите новую роль:", reply_markup=role_kb)
    await state.set_state(RegStates.choosing_role)

@router.message(RegStates.choosing_role)
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

@router.message(Command("profile"))
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

@router.message(Command("addorder"))
async def start_add_order(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user or user[3] != "customer":
        await message.answer("Эта команда только для заказчиков.")
        return
    await message.answer("Введите площадку (например, VK, Telegram, Instagram):")
    await state.set_state(OrderStates.waiting_for_platform)

@router.message(OrderStates.waiting_for_platform)
async def order_platform(message: Message, state: FSMContext):
    await state.update_data(platform=message.text)
    await message.answer("Введите количество:")
    await state.set_state(OrderStates.waiting_for_quantity)

@router.message(OrderStates.waiting_for_quantity)
async def order_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число.")
        return
    await state.update_data(quantity=int(message.text))
    await message.answer("Введите дедлайн (например, 2025-07-01):")
    await state.set_state(OrderStates.waiting_for_deadline)

@router.message(OrderStates.waiting_for_deadline)
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

@router.callback_query(lambda c: c.data.startswith("confirm_"))
async def process_confirm_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    set_order_status(order_id, "Выполнен")
    delete_done_orders()
    await callback.message.edit_text(
        "👍 <b>Вы подтвердили выполнение заказа!</b>\n"
        "Администратор уведомлён.",
        parse_mode="HTML"
    )
    for admin_id in ADMINS:
        await callback.bot.send_message(
            admin_id,
            f"💸 <b>Заказ №{order_id} подтверждён заказчиком!</b>\n"
            "Можно начислить деньги исполнителю.",
            parse_mode="HTML"
        )
