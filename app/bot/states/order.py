from aiogram.fsm.state import State, StatesGroup


class KlientOrderStates(StatesGroup):
    selecting_region = State()      # Viloyat
    entering_district = State()     # Tuman
    entering_street = State()       # Ko'cha
    entering_target = State()       # Orientir/mo'ljal
    entering_area = State()
    selecting_asphalt = State()
    confirming = State()


class PriceCalculatorStates(StatesGroup):
    entering_area = State()
    selecting_asphalt = State()


class MasterConfirmStates(StatesGroup):
    entering_area = State()
    entering_sum = State()
    entering_advance = State()
    entering_address = State()
    entering_date = State()
    entering_usta_wage = State()
    entering_commission = State()
    entering_notes = State()
    confirming = State()


class AdminOrderCreateStates(StatesGroup):
    entering_client_phone = State()
    entering_client_name = State()
    entering_address = State()
    entering_area = State()
    selecting_asphalt = State()
    confirming = State()


class MasterOrderCreateStates(StatesGroup):
    entering_client_phone = State()
    entering_client_name = State()
    selecting_region = State()
    entering_district = State()
    entering_street = State()
    entering_target = State()
    entering_area = State()
    selecting_asphalt = State()
    confirming = State()


class AdminSettingsStates(StatesGroup):
    entering_asphalt_name = State()
    entering_asphalt_price = State()
    updating_asphalt_price = State()
