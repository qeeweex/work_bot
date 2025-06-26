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


def get_order_inline_kb(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Взять заказ", callback_data=f"take_{order_id}"),
            InlineKeyboardButton(text="Подробнее", callback_data=f"details_{order_id}")
        ],
        [
            InlineKeyboardButton(text="Готово", callback_data=f"done_{order_id}"),
            InlineKeyboardButton(text="Отменить", callback_data=f"cancel_{order_id}")
        ]
    ])