from aiogram.fsm.state import State, StatesGroup


class MaterialRequestStates(StatesGroup):
    selecting_order = State()
    entering_tonnes = State()
    entering_notes = State()
    confirming = State()


class ZavodPriceStates(StatesGroup):
    entering_material_price = State()
    entering_delivery_price = State()
    entering_extra_cost = State()
    confirming = State()


class ExpenseAddStates(StatesGroup):
    selecting_order = State()
    selecting_type = State()
    entering_amount = State()
    entering_description = State()


class PaymentUpdateStates(StatesGroup):
    entering_amount = State()
