from datetime import datetime, timezone
from typing import List, Optional, Tuple

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
    now = datetime.now(timezone.utc)
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
        loc = f" 📍{usta.viloyat.name}" if usta.viloyat else ""
        builder.button(
            text=f"👷 {name}{loc}  ({count} faol zakaz)",
            callback_data=f"assign_usta_to_order:{order_id}:{usta.id}",
        )
    builder.button(text="⬅️ Orqaga", callback_data="back_usta_orders")
    builder.adjust(1)
    return builder.as_markup()


def get_ustas_for_reassignment_keyboard(
    ustas_with_count: List[Tuple[User, int]],
    order_id: int,
    current_usta_id: Optional[int] = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for usta, count in ustas_with_count:
        name = usta.full_name or str(usta.telegram_id)
        loc = f" 📍{usta.viloyat.name}" if usta.viloyat else ""
        marker = " ✅" if usta.id == current_usta_id else ""
        builder.button(
            text=f"👷 {name}{loc}  ({count} faol zakaz){marker}",
            callback_data=f"reassign_usta:{order_id}:{usta.id}",
        )
    builder.button(text="⬅️ Orqaga", callback_data=f"back_order_detail:{order_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_usta_order_detail_keyboard(
    order_id: int,
    status: Optional[str] = None,
    payment_done: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Material so'rash", callback_data=f"request_material:{order_id}")
    if status in ("confirmed", "in_work"):
        if payment_done:
            builder.button(
                text="✅ To'lov tasdiqlandi ✓",
                callback_data=f"usta_payment_view:{order_id}",
            )
        else:
            builder.button(
                text="💸 Summani tasdiqlash",
                callback_data=f"usta_payment:{order_id}",
            )
        builder.button(text="✅ Ishni tugatish", callback_data=f"usta_complete:{order_id}")
    builder.button(text="⬅️ Orqaga", callback_data="usta_my_orders")
    builder.adjust(1)
    return builder.as_markup()


def get_usta_payment_confirm_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"usta_payment_confirm:{order_id}")
    builder.button(text="✏️ Qayta kiritish", callback_data=f"usta_payment:{order_id}")
    builder.button(text="❌ Bekor", callback_data=f"usta_view_mine:{order_id}")
    builder.adjust(2, 1)
    return builder.as_markup()


def get_usta_my_orders_keyboard(orders: List[Order]) -> InlineKeyboardMarkup:
    """Inline list of usta's own orders \u2014 each row opens that order's detail."""
    builder = InlineKeyboardBuilder()
    for o in orders:
        addr = (o.address or "\u2014").strip()
        if len(addr) > 35:
            addr = addr[:32] + "\u2026"
        builder.button(
            text=f"🔢 {o.order_number} | {addr}",
            callback_data=f"usta_view_mine:{o.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def get_usta_complete_confirm_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="\u2705 Ha, tugatish", callback_data=f"usta_complete_confirm:{order_id}")
    builder.button(text="\u274c Bekor qilish", callback_data=f"usta_view_mine:{order_id}")
    builder.adjust(1)
    return builder.as_markup()
