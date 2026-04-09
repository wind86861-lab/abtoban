from datetime import datetime
from typing import List, Tuple

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.models import Order, User


def get_usta_notification_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Qabul qilish", callback_data=f"accept_assignment:{order_id}")
    builder.button(text="❌ Rad etish", callback_data=f"decline_assignment:{order_id}")
    builder.adjust(2)
    return builder.as_markup()


def get_usta_assignment_orders_keyboard(orders: List[Order]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    now = datetime.utcnow()
    for order in orders:
        if order.usta_assignment_deadline:
            secs = (order.usta_assignment_deadline - now).total_seconds()
            timer = f"⏰ {int(secs // 60)} daq" if secs > 0 else "⌛ Muddati o'tgan"
        else:
            timer = ""
        builder.button(
            text=f"🔢 {order.order_number}  {timer}",
            callback_data=f"master_pick_order_for_usta:{order.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def get_ustas_for_assignment_keyboard(
    ustas_with_count: List[Tuple[User, int]],
    order_id: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for usta, count in ustas_with_count:
        name = usta.full_name or str(usta.telegram_id)
        builder.button(
            text=f"👷 {name}  [{count}/2 zakaz]",
            callback_data=f"assign_usta_to_order:{order_id}:{usta.id}",
        )
    builder.button(text="⬅️ Orqaga", callback_data="back_usta_orders")
    builder.adjust(1)
    return builder.as_markup()


def get_usta_order_detail_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Material so'rash", callback_data=f"request_material:{order_id}")
    builder.button(text="⬅️ Orqaga", callback_data="usta_my_orders")
    builder.adjust(1)
    return builder.as_markup()
