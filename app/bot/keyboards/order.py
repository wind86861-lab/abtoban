from typing import List

from aiogram.types import (
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.db.models import ORDER_STATUS_LABELS, AsphaltType, Order, OrderStatus, Region


def get_regions_keyboard(regions: List[Region]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for region in regions:
        builder.button(
            text=f"📍 {region.name}",
            callback_data=f"region:{region.id}",
        )
    builder.adjust(2)
    return builder.as_markup()


def get_asphalt_keyboard(asphalt_types: List[AsphaltType]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for at in asphalt_types:
        builder.button(
            text=f"🏗 {at.name} — {float(at.price_per_m2):,.0f} so'm/m²",
            callback_data=f"asphalt:{at.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def get_order_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data="confirm_order")
    builder.button(text="❌ Bekor qilish", callback_data="cancel_order")
    builder.adjust(2)
    return builder.as_markup()


def get_orders_list_keyboard(orders: List[Order], prefix: str = "view_order") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for order in orders:
        status_icon = {
            OrderStatus.NEW: "🆕",
            OrderStatus.CONFIRMED: "✅",
            OrderStatus.IN_WORK: "🔧",
            OrderStatus.DONE: "🏁",
            OrderStatus.CANCELLED: "❌",
        }.get(order.status, "📋")
        
        status_label = ORDER_STATUS_LABELS.get(order.status, order.status.value)
        area = f"{float(order.area_m2):.0f}" if order.area_m2 else "—"
        debt = float(order.debt) if order.debt else 0
        
        # Multi-line button text with proper formatting
        button_text = (
            f"{status_icon} {order.order_number}\n"
            f"📐 {area} m²  |  💰 Qarz: {debt:,.0f} so'm"
        )
        
        builder.button(
            text=button_text,
            callback_data=f"{prefix}:{order.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def get_master_order_detail_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Tasdiqlashni boshlash",
        callback_data=f"start_confirm:{order_id}",
    )
    builder.button(text="⬅️ Orqaga", callback_data="back_new_orders")
    builder.adjust(1)
    return builder.as_markup()


def get_master_confirmed_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔧 Ishga olish", callback_data=f"set_status:{order_id}:in_work")
    builder.button(text="⬅️ Orqaga", callback_data="back_my_orders")
    builder.adjust(1)
    return builder.as_markup()


def get_confirm_summary_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data="submit_confirm")
    builder.button(text="❌ Bekor qilish", callback_data="cancel_confirm")
    builder.adjust(2)
    return builder.as_markup()


def get_keep_address_keyboard(address: str) -> ReplyKeyboardMarkup:
    short = address[:40] + "..." if len(address) > 40 else address
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=f"📍 Saqlash: {short}"))
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def get_skip_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="⏩ O'tkazib yuborish"))
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_status_selection_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    statuses = [
        (OrderStatus.CONFIRMED, "✅ Tasdiqlangan"),
        (OrderStatus.IN_WORK, "🔧 Ishda"),
        (OrderStatus.DONE, "🏁 Tugagan"),
        (OrderStatus.CANCELLED, "❌ Bekor qilingan"),
    ]
    for status, label in statuses:
        builder.button(
            text=label,
            callback_data=f"set_status:{order_id}:{status.value}",
        )
    builder.button(text="⬅️ Orqaga", callback_data=f"admin_view_order:{order_id}")
    builder.adjust(2)
    return builder.as_markup()


def get_admin_order_detail_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔄 Status o'zgartirish",
        callback_data=f"order_change_status:{order_id}",
    )
    builder.button(text="💵 To'lov", callback_data=f"order_payment:{order_id}")
    builder.button(text="💸 Xarajatlar", callback_data=f"view_expenses:{order_id}")
    builder.button(text="⬅️ Orqaga", callback_data="admin_orders_list:0")
    builder.adjust(2)
    return builder.as_markup()


def get_asphalt_manage_keyboard(asphalt_types: List[AsphaltType]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for at in asphalt_types:
        icon = "🟢" if at.is_active else "🔴"
        builder.button(
            text=f"{icon} {at.name} — {float(at.price_per_m2):,.0f} so'm/m²",
            callback_data=f"manage_asphalt:{at.id}",
        )
    builder.button(text="➕ Yangi qo'shish", callback_data="add_asphalt_type")
    builder.adjust(1)
    return builder.as_markup()


def get_asphalt_actions_keyboard(asphalt_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✏️ Narxni o'zgartirish",
        callback_data=f"edit_asphalt_price:{asphalt_id}",
    )
    toggle_text = "🔴 O'chirish" if is_active else "🟢 Yoqish"
    builder.button(text=toggle_text, callback_data=f"toggle_asphalt:{asphalt_id}")
    builder.button(text="⬅️ Orqaga", callback_data="asphalt_list")
    builder.adjust(1)
    return builder.as_markup()
