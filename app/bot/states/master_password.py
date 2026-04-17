"""FSM states for Master password management"""
from aiogram.fsm.state import State, StatesGroup


class MasterPasswordStates(StatesGroup):
    """States for Master setting/changing password"""
    entering_new_password = State()
    confirming_password = State()
