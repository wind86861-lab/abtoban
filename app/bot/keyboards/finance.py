from typing import List

from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.db.models import AsphaltCategory, AsphaltSubCategory, AsphaltType, ExpenseType, MaterialRequest, Order
from app.services.expense_service import EXPENSE_LABELS


def get_mat_req_categories_keyboard(categories: List[AsphaltCategory], lang: str = "uz_lat") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for c in categories:
        builder.button(text=f"📁 {c.name}", callback_data=f"mat_cat:{c.id}")
    cancel_text = "❌ Bekor qilish" if lang == "uz_lat" else ("❌ Отмена" if lang == "ru" else "❌ Бекор қилиш")
    builder.button(text=cancel_text, callback_data="mat_req_cancel")
    builder.adjust(1)
    return builder.as_markup()


def get_mat_req_subcategories_keyboard(subcategories: List[AsphaltSubCategory], category_id: int, lang: str = "uz_lat") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in subcategories:
        builder.button(text=f"📂 {s.name}", callback_data=f"mat_subcat:{s.id}")
    builder.button(text="🔙 Orqaga", callback_data=f"mat_cat_back:{category_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_mat_req_types_keyboard(types: List[AsphaltType], subcategory_id: int, lang: str = "uz_lat") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for at in types:
        price = f" — {float(at.price_per_m2):,.0f} so'm/m²" if at.price_per_m2 else ""
        builder.button(text=f"🏗 {at.name}{price}", callback_data=f"mat_type:{at.id}")
    builder.button(text="🔙 Orqaga", callback_data=f"mat_subcat_back:{subcategory_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_exp_mat_categories_keyboard(categories: List[AsphaltCategory], lang: str = "uz_lat") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for c in categories:
        builder.button(text=f"📁 {c.name}", callback_data=f"exp_mat_cat:{c.id}")
    cancel_text = "❌ Bekor qilish" if lang == "uz_lat" else ("❌ Отмена" if lang == "ru" else "❌ Бекор қилиш")
    builder.button(text=cancel_text, callback_data="exp_mat_cancel")
    builder.adjust(1)
    return builder.as_markup()


def get_exp_mat_subcategories_keyboard(subcats: List[AsphaltSubCategory], category_id: int, lang: str = "uz_lat") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in subcats:
        builder.button(text=f"📂 {s.name}", callback_data=f"exp_mat_subcat:{s.id}")
    builder.button(text="🔙 Orqaga", callback_data=f"exp_mat_cat_back:{category_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_exp_mat_types_keyboard(types: List[AsphaltType], subcategory_id: int, lang: str = "uz_lat") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for at in types:
        price = f" — {float(at.price_per_m2):,.0f} so'm/m²" if at.price_per_m2 else ""
        builder.button(text=f"🏗 {at.name}{price}", callback_data=f"exp_mat_type:{at.id}")
    builder.button(text="🔙 Orqaga", callback_data=f"exp_mat_subcat_back:{subcategory_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_active_orders_for_material_keyboard(orders: List[Order]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for o in orders:
        builder.button(
            text=f"🔢 {o.order_number} | {o.address or '—'}",
            callback_data=f"material_pick_order:{o.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def get_material_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yuborish", callback_data="material_confirm")
    builder.button(text="❌ Bekor qilish", callback_data="material_cancel")
    builder.adjust(2)
    return builder.as_markup()


def get_pending_requests_keyboard(requests: List[MaterialRequest]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for req in requests:
        order_num = req.order.order_number if req.order else "?"
        usta_name = req.usta.full_name or str(req.usta.telegram_id) if req.usta else "?"
        builder.button(
            text=f"📦 {order_num} | {float(req.amount_tonnes)} t | {usta_name}",
            callback_data=f"zavod_view_req:{req.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def get_priced_requests_keyboard(requests: List[MaterialRequest]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for req in requests:
        order_num = req.order.order_number if req.order else "?"
        builder.button(
            text=f"🚚 {order_num} | {float(req.amount_tonnes)} t — Yetkazish kutilmoqda",
            callback_data=f"zavod_deliver:{req.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def get_zavod_request_detail_keyboard(req_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Narx belgilash", callback_data=f"zavod_price:{req_id}")
    builder.button(text="⬅️ Orqaga", callback_data="zavod_pending_list")
    builder.adjust(1)
    return builder.as_markup()


def get_zavod_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data="zavod_price_confirm")
    builder.button(text="❌ Bekor qilish", callback_data="zavod_price_cancel")
    builder.adjust(2)
    return builder.as_markup()


def get_shofer_delivery_keyboard(req_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yetkazdim", callback_data=f"shofer_delivered:{req_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_expense_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for exp_type, label in EXPENSE_LABELS.items():
        builder.button(text=label, callback_data=f"expense_type:{exp_type.value}")
    builder.button(text="❌ Bekor qilish", callback_data="expense_cancel")
    builder.adjust(2)
    return builder.as_markup()


def get_master_orders_for_expense_keyboard(orders: List[Order]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for o in orders:
        builder.button(
            text=f"🔢 {o.order_number} | {o.address or '—'}",
            callback_data=f"expense_pick_order:{o.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def get_usta_orders_for_expense_keyboard(orders: List[Order]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for o in orders:
        builder.button(
            text=f"🔢 {o.order_number} | {o.address or '—'}",
            callback_data=f"usta_exp_order:{o.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def get_usta_expense_type_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for exp_type, label in EXPENSE_LABELS.items():
        builder.button(text=label, callback_data=f"usta_exp_type:{exp_type.value}")
    builder.button(text="❌ Bekor qilish", callback_data="usta_exp_cancel")
    builder.adjust(2)
    return builder.as_markup()


def get_payment_update_keyboard(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💵 To'lov kiritish", callback_data=f"payment_enter:{order_id}")
    builder.button(text="🏁 To'liq to'landi", callback_data=f"payment_full:{order_id}")
    builder.button(text="⬅️ Orqaga", callback_data=f"admin_view_order:{order_id}")
    builder.adjust(2)
    return builder.as_markup()


def get_skip_notes_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="⏩ Izohsiz yuborish"))
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_admin_material_requests_keyboard(requests: List[MaterialRequest]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for req in requests:
        order_num = req.order.order_number if req.order else "?"
        region_name = req.order.region.name if req.order and req.order.region else "—"
        usta_name = req.usta.full_name or str(req.usta.telegram_id) if req.usta else "?"
        builder.button(
            text=f"📦 {order_num} | {region_name}\n{float(req.amount_tonnes)} t | {usta_name}",
            callback_data=f"admin_view_material:{req.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


def get_admin_material_detail_keyboard(req_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data=f"admin_approve_material:{req_id}")
    builder.button(text="❌ Rad etish", callback_data=f"admin_reject_material:{req_id}")
    builder.button(text="⬅️ Orqaga", callback_data="back_admin_materials")
    builder.adjust(2)
    return builder.as_markup()


def get_shofer_narxi_requests_keyboard(requests: List[MaterialRequest], lang: str = "uz_lat") -> InlineKeyboardMarkup:
    """Inline keyboard listing material requests for shofer narxi selection."""
    builder = InlineKeyboardBuilder()
    for req in requests:
        order_num = req.order.order_number if req.order else f"#{req.order_id}"
        usta_name = (req.usta.full_name or req.usta.phone) if req.usta else "?"
        current = f" | 🚛{float(req.delivery_price):,.0f}" if req.delivery_price else ""
        label = f"📦 {order_num} | {usta_name} | {req.amount_tonnes}t{current}"
        builder.button(text=label, callback_data=f"shofer_req:{req.id}")
    cancel_text = "❌ Bekor qilish" if lang == "uz_lat" else ("❌ Отмена" if lang == "ru" else "❌ Бекор қилиш")
    builder.button(text=cancel_text, callback_data="shofer_narxi_cancel")
    builder.adjust(1)
    return builder.as_markup()


def get_shofer_narxi_confirm_keyboard(lang: str = "uz_lat") -> InlineKeyboardMarkup:
    """Confirmation keyboard for shofer narxi update."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Saqlash" if lang == "uz_lat" else ("✅ Сохранить" if lang == "ru" else "✅ Сақлаш"), callback_data="shofer_narxi_save")
    builder.button(text="❌ Bekor qilish" if lang == "uz_lat" else ("❌ Отмена" if lang == "ru" else "❌ Бекор қилиш"), callback_data="shofer_narxi_cancel")
    builder.adjust(2)
    return builder.as_markup()
