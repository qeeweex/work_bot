from aiogram.fsm.state import StatesGroup, State

# Состояния для регистрации пользователя (выбор роли)
class RegStates(StatesGroup):
    choosing_role = State()

# Состояния для создания заказа
class OrderStates(StatesGroup):
    waiting_for_platform = State()
    waiting_for_quantity = State()
    waiting_for_deadline = State()