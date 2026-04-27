from aiogram.fsm.state import State, StatesGroup


class KlientOrderStates(StatesGroup):
    selecting_viloyat = State()     # Viloyat
    selecting_tuman = State()       # Tuman
    entering_street = State()       # Ko'cha
    entering_target = State()       # Orientir/mo'ljal
    sharing_location = State()      # GPS lokatsiya
    entering_area = State()
    selecting_asphalt_category = State()
    selecting_asphalt_subcategory = State()
    selecting_asphalt = State()
    confirming = State()


class PriceCalculatorStates(StatesGroup):
    entering_area = State()
    selecting_asphalt_category = State()
    selecting_asphalt_subcategory = State()
    selecting_asphalt = State()


class MasterConfirmStates(StatesGroup):
    entering_area = State()
    selecting_main_category = State()
    selecting_main_subcategory = State()
    selecting_main_material = State()
    adding_extras = State()
    selecting_extra_category = State()
    selecting_extra_subcategory = State()
    selecting_extra_material = State()
    entering_extra_area = State()
    entering_sum = State()
    entering_advance = State()
    entering_address = State()
    entering_date = State()
    entering_usta_wage = State()
    entering_commission = State()
    entering_notes = State()
    selecting_usta = State()
    confirming = State()


class AdminOrderCreateStates(StatesGroup):
    entering_client_phone = State()
    entering_client_name = State()
    selecting_viloyat = State()
    selecting_tuman = State()
    entering_address = State()
    entering_area = State()
    selecting_asphalt_category = State()
    selecting_asphalt_subcategory = State()
    selecting_asphalt = State()
    confirming = State()


class MasterOrderCreateStates(StatesGroup):
    entering_client_phone = State()
    entering_client_name = State()
    selecting_viloyat = State()
    selecting_tuman = State()
    entering_address = State()
    sharing_location = State()


class AdminSettingsStates(StatesGroup):
    # Category states
    entering_category_name = State()
    # SubCategory states
    entering_subcategory_name = State()
    # Material states
    entering_material_name = State()
    entering_material_cost_price = State()
    entering_material_price = State()
    updating_material_price = State()
    # Legacy states (kept for backward compatibility)
    entering_asphalt_name = State()
    entering_asphalt_cost_price = State()
    entering_asphalt_price = State()
    updating_asphalt_price = State()
    updating_asphalt_cost_price = State()
