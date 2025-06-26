from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

role_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Я заказчик")],
        [KeyboardButton(text="Я исполнитель")]
    ],
    resize_keyboard=True
)

# Клавиатура для заказчика (без /deleteorder)
customer_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/profile"), KeyboardButton(text="/orders")],
        [KeyboardButton(text="/addorder")],
        [KeyboardButton(text="/changerole")]
    ],
    resize_keyboard=True
)

# Клавиатура для исполнителя (без /takeorder и /done)
worker_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/profile"), KeyboardButton(text="/orders")],
        [KeyboardButton(text="/workorders"), KeyboardButton(text="/myorders")],
        [KeyboardButton(text="/changerole")]
    ],
    resize_keyboard=True
)


def get_order_inline_kb(order_id, role, status):
    buttons = []
    if role == "worker" and status == "new":
        buttons.append([InlineKeyboardButton(text="Взять заказ", callback_data=f"take_{order_id}")])
    if role == "worker" and status == "in_progress":
        buttons.append([InlineKeyboardButton(text="Завершить", callback_data=f"done_{order_id}")])
    if role == "customer" and status == "new":
        buttons.append([InlineKeyboardButton(text="Удалить", callback_data=f"delete_{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)