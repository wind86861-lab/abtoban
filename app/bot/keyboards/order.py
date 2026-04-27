from typing import List, Tuple

from aiogram.types import (
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.db.models import ORDER_STATUS_LABELS, AsphaltCategory, AsphaltSubCategory, AsphaltType, Order, OrderStatus, Region, Tuman, User, Viloyat


def get_regions_keyboard(regions: List[Region]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for region in regions:
        builder.button(
            text=f"📍 {region.name}",
            callback_data=f"region:{region.id}",
        )
    builder.adjust(2)
    return builder.as_markup()


def get_viloyatlar_keyboard(viloyatlar: List[Viloyat]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # Deduplicate by ID to avoid repeats
    seen_ids = set()
    for v in viloyatlar:
        if v.id not in seen_ids:
            seen_ids.add(v.id)
            builder.button(
                text=f"📍 {v.name}",
                callback_data=f"viloyat:{v.id}",
            )
    builder.adjust(2)
    return builder.as_markup()


def get_tumanlar_keyboard(tumanlar: List[Tuman]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for t in tumanlar:
        # Show only tuman name (viloyat already selected above)
        builder.button(
            text=f"📍 {t.name}",
            callback_data=f"tuman:{t.id}",
        )
    builder.adjust(2)
    return builder.as_markup()


def get_asphalt_categories_keyboard(categories: List[AsphaltCategory]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for c in categories:
        builder.button(text=f"📁 {c.name}", callback_data=f"asfcat:{c.id}")
    builder.adjust(1)
    return builder.as_markup()


def get_asphalt_subcategories_keyboard(subcategories: List[AsphaltSubCategory], category_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in subcategories:
        builder.button(text=f"📂 {s.name}", callback_data=f"asfsubcat:{s.id}")
    builder.button(text="🔙 Orqaga", callback_data=f"asfcat_back:{category_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_asphalt_keyboard(asphalt_types: List[AsphaltType], subcat_id: int | None = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for at in asphalt_types:
        builder.button(
            text=f"🏗 {at.name} — {float(at.price_per_m2):,.0f} so'm/m²",
            callback_data=f"asphalt:{at.id}",
        )
    if subcat_id is not None:
        builder.button(text="🔙 Orqaga", callback_data=f"asfsubcat_back:{subcat_id}")
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
    builder.button(text="👷 Usta o'zgartirish", callback_data=f"change_usta:{order_id}")
    builder.button(text="⬅️ Orqaga", callback_data="back_my_orders")
    builder.adjust(1)
    return builder.as_markup()


def get_master_my_order_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
    """Return action buttons for a master viewing their own order, based on status."""
    builder = InlineKeyboardBuilder()
    if status == "confirmed":
        builder.button(text="🔧 Ishga olish", callback_data=f"set_status:{order_id}:in_work")
        builder.button(text="👷 Usta o'zgartirish", callback_data=f"change_usta:{order_id}")
    elif status == "in_work":
        builder.button(text="✅ Ishni tugatish", callback_data=f"set_status:{order_id}:done")
    builder.button(text="⬅️ Orqaga", callback_data="back_my_orders")
    builder.adjust(1)
    return builder.as_markup()


def get_ustas_for_confirm_keyboard(ustas_with_count: List[Tuple[User, int]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for usta, count in ustas_with_count:
        name = usta.full_name or str(usta.telegram_id)
        loc = f" 📍{usta.viloyat.name}" if usta.viloyat else ""
        builder.button(
            text=f"👷 {name}{loc}  ({count} faol zakaz)",
            callback_data=f"confirm_usta:{usta.id}",
        )
    builder.button(text="⏩ O'tkazib yuborish", callback_data="confirm_usta:skip")
    builder.adjust(1)
    return builder.as_markup()


def get_extras_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown after main asphalt is selected — add extra or proceed."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Qo'shimcha xizmat qo'shish", callback_data="add_extra_service")
    builder.button(text="✅ Davom etish", callback_data="extras_done")
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
    builder.button(text="👷 Usta o'zgartirish", callback_data=f"change_usta:{order_id}")
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
