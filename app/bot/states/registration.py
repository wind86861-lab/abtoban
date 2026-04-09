from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    waiting_for_phone = State()


class AdminRoleStates(StatesGroup):
    waiting_for_telegram_id = State()
    selecting_role = State()
