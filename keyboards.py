from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

role_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Я заказчик")],
        [KeyboardButton(text="Я исполнитель")]
    ],
    resize_keyboard=True
)

# Клавиатура для заказчика
customer_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/profile"), KeyboardButton(text="/orders")],
        [KeyboardButton(text="/addorder"), KeyboardButton(text="/deleteorder")],
        [KeyboardButton(text="/changerole")]
    ],
    resize_keyboard=True
)

# Клавиатура для исполнителя
worker_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/profile"), KeyboardButton(text="/orders")],
        [KeyboardButton(text="/workorders"), KeyboardButton(text="/myorders")],
        [KeyboardButton(text="/takeorder"), KeyboardButton(text="/done")],
        [KeyboardButton(text="/changerole")]
    ],
    resize_keyboard=True
)