from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Клавиатура для выбора роли
role_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Я заказчик")],
        [KeyboardButton(text="Я исполнитель")]
    ],
    resize_keyboard=True
)

# Можно добавить другие клавиатуры по мере необходимости