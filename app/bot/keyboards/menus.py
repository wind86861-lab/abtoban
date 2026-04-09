from aiogram.types import (
    InlineKeyboardMarkup, KeyboardButton,
    ReplyKeyboardMarkup, ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.db.models import ROLE_LABELS, UserRole


def get_main_menu(role: UserRole) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    if role == UserRole.KLIENT:
        builder.row(
            KeyboardButton(text="📝 Zakaz qoldirish"),
            KeyboardButton(text="📋 Mening zakazlarim"),
        )
        builder.row(
            KeyboardButton(text="🧮 Narx hisoblash"),
            KeyboardButton(text="📞 Konsultatsiya"),
        )
        builder.row(KeyboardButton(text="ℹ️ Kompaniya haqida"))

    elif role in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
        builder.row(
            KeyboardButton(text="📋 Barcha zakazlar"),
            KeyboardButton(text="➕ Zakaz qo'shish"),
        )
        builder.row(
            KeyboardButton(text="👥 Foydalanuvchilar"),
            KeyboardButton(text="📊 Hisobotlar"),
        )
        builder.row(
            KeyboardButton(text="💰 Moliya"),
            KeyboardButton(text="🔧 Sozlamalar"),
        )

    elif role == UserRole.HELPER_ADMIN:
        builder.row(
            KeyboardButton(text="📋 Barcha zakazlar"),
            KeyboardButton(text="➕ Zakaz qo'shish"),
        )
        builder.row(
            KeyboardButton(text="👥 Foydalanuvchilar"),
            KeyboardButton(text="📊 Hisobotlar"),
        )

    elif role == UserRole.MASTER:
        builder.row(
            KeyboardButton(text="🆕 Yangi zakazlar"),
            KeyboardButton(text="📋 Mening zakazlarim"),
        )
        builder.row(
            KeyboardButton(text="✅ Zakaz tasdiqlash"),
            KeyboardButton(text="👷 Usta tayinlash"),
        )

    elif role == UserRole.USTA:
        builder.row(
            KeyboardButton(text="📋 Mening zakazlarim"),
            KeyboardButton(text="✅ Zakazni qabul qilish"),
        )
        builder.row(
            KeyboardButton(text="📦 Material so'rash"),
            KeyboardButton(text="📊 Ish tarixi"),
        )

    elif role == UserRole.ZAVOD:
        builder.row(
            KeyboardButton(text="📦 Material so'rovlar"),
            KeyboardButton(text="✅ Narx kiritish"),
        )
        builder.row(KeyboardButton(text="📋 Tarixi"))

    elif role == UserRole.SHOFER:
        builder.row(
            KeyboardButton(text="🚗 Mening yetkazilmalarim"),
            KeyboardButton(text="✅ Status yangilash"),
        )

    return builder.as_markup(resize_keyboard=True)


def get_phone_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def get_users_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 ID bo'yicha qidirish", callback_data="user_search_by_id")
    builder.button(text="📋 Barcha foydalanuvchilar", callback_data="user_list:0")
    builder.adjust(1)
    return builder.as_markup()


def get_role_selection_keyboard(exclude_super_admin: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    roles = [
        UserRole.KLIENT, UserRole.MASTER, UserRole.USTA,
        UserRole.ZAVOD, UserRole.SHOFER, UserRole.HELPER_ADMIN, UserRole.ADMIN,
    ]
    if not exclude_super_admin:
        roles.append(UserRole.SUPER_ADMIN)
    for role in roles:
        builder.button(text=ROLE_LABELS[role], callback_data=f"set_role:{role.value}")
    builder.adjust(2)
    return builder.as_markup()


def get_user_action_keyboard(user_id: int, is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔄 Rol o'zgartirish",
        callback_data=f"change_role:{user_id}",
    )
    toggle_text = "🔴 Bloklash" if is_active else "🟢 Faollashtirish"
    builder.button(
        text=toggle_text,
        callback_data=f"toggle_active:{user_id}",
    )
    builder.button(text="⬅️ Orqaga", callback_data="user_list:0")
    builder.adjust(1)
    return builder.as_markup()


def get_back_keyboard(callback_data: str = "back") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Orqaga", callback_data=callback_data)
    return builder.as_markup()


def get_skip_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="⏩ O'tkazib yuborish"))
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_pagination_keyboard(
    page: int, total: int, per_page: int, prefix: str
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if page > 0:
        builder.button(text="⬅️", callback_data=f"{prefix}:{page - 1}")
    if (page + 1) * per_page < total:
        builder.button(text="➡️", callback_data=f"{prefix}:{page + 1}")
    builder.adjust(2)
    return builder.as_markup()
