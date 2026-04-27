from aiogram.fsm.state import State, StatesGroup


class UstaPaymentStates(StatesGroup):
    entering_collected = State()
    confirming = State()


class ZavodPaymentStates(StatesGroup):
    entering_received = State()
