from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from db import get_user_by_telegram_id, add_user, update_user_role
from keyboards import role_kb, customer_kb, worker_kb
from states import RegStates

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