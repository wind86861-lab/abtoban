from aiogram.types import (
    InlineKeyboardMarkup, KeyboardButton,
    ReplyKeyboardMarkup, ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.bot.i18n import t
from app.db.models import ROLE_LABELS, UserRole


def get_language_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 O'zbekcha (Lotin)", callback_data="set_lang:uz_lat")
    builder.button(text="🇺🇿 Ўзбекча (Кирилл)", callback_data="set_lang:uz_cyr")
    builder.button(text="🇷🇺 Русский", callback_data="set_lang:ru")
    builder.adjust(1)
    return builder.as_markup()


def get_main_menu(role: UserRole, lang: str = "uz_lat") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    if role == UserRole.KLIENT:
        builder.row(
            KeyboardButton(text=t("btn_order_create", lang)),
            KeyboardButton(text=t("btn_my_orders", lang)),
        )
        builder.row(
            KeyboardButton(text=t("btn_shop", lang)),
            KeyboardButton(text=t("btn_calc_price", lang)),
        )
        builder.row(
            KeyboardButton(text=t("btn_consultation", lang)),
            KeyboardButton(text=t("btn_about", lang)),
        )

    elif role in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
        builder.row(
            KeyboardButton(text=t("btn_all_orders", lang)),
            KeyboardButton(text=t("btn_add_order", lang)),
        )
        builder.row(
            KeyboardButton(text=t("btn_users", lang)),
            KeyboardButton(text=t("btn_reports", lang)),
        )
        builder.row(
            KeyboardButton(text=t("btn_materials", lang)),
            KeyboardButton(text=t("btn_finance", lang)),
        )
        builder.row(
            KeyboardButton(text=t("btn_settings", lang)),
            KeyboardButton(text=t("btn_web_panel", lang)),
        )

    elif role == UserRole.HELPER_ADMIN:
        builder.row(
            KeyboardButton(text=t("btn_all_orders", lang)),
            KeyboardButton(text=t("btn_add_order", lang)),
        )
        builder.row(
            KeyboardButton(text=t("btn_users", lang)),
            KeyboardButton(text=t("btn_reports", lang)),
        )

    elif role == UserRole.MASTER:
        builder.row(
            KeyboardButton(text=t("btn_new_orders", lang)),
            KeyboardButton(text=t("btn_master_my_orders", lang)),
        )
        builder.row(
            KeyboardButton(text=t("btn_add_order", lang)),
            KeyboardButton(text=t("btn_confirm_order", lang)),
        )
        builder.row(
            KeyboardButton(text=t("btn_assign_usta", lang)),
            KeyboardButton(text=t("btn_add_expense", lang)),
        )

    elif role == UserRole.USTA:
        builder.row(
            KeyboardButton(text=t("btn_usta_my_orders", lang)),
        )
        builder.row(
            KeyboardButton(text=t("btn_request_material", lang)),
            KeyboardButton(text=t("btn_add_expense", lang)),
        )
        builder.row(
            KeyboardButton(text=t("btn_work_history", lang)),
        )

    elif role == UserRole.ZAVOD:
        builder.row(
            KeyboardButton(text=t("btn_zavod_materials", lang)),
            KeyboardButton(text=t("btn_zavod_price", lang)),
        )
        builder.row(KeyboardButton(text=t("btn_zavod_history", lang)))

    elif role == UserRole.SHOFER:
        builder.row(
            KeyboardButton(text=t("btn_my_deliveries", lang)),
            KeyboardButton(text=t("btn_update_status", lang)),
        )

    # Always add language change button at the bottom
    builder.row(KeyboardButton(text=t("btn_change_language", lang)))

    return builder.as_markup(resize_keyboard=True)


def get_phone_keyboard(lang: str = "uz_lat") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text=t("send_phone", lang), request_contact=True)
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def get_cancel_keyboard(lang: str = "uz_lat") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=t("btn_cancel", lang)))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def get_users_menu_keyboard(lang: str = "uz_lat") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("search_by_id", lang), callback_data="user_search_by_id")
    builder.button(text=t("all_users", lang), callback_data="user_list:0")
    builder.adjust(1)
    return builder.as_markup()


def get_role_selection_keyboard(exclude_super_admin: bool = True, lang: str = "uz_lat") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    _ROLE_KEY_MAP = {
        UserRole.KLIENT: "role_klient",
        UserRole.MASTER: "role_master",
        UserRole.USTA: "role_usta",
        UserRole.ZAVOD: "role_zavod",
        UserRole.SHOFER: "role_shofer",
        UserRole.HELPER_ADMIN: "role_helper_admin",
        UserRole.ADMIN: "role_admin",
        UserRole.SUPER_ADMIN: "role_super_admin",
    }
    roles = [
        UserRole.KLIENT, UserRole.MASTER, UserRole.USTA,
        UserRole.ZAVOD, UserRole.SHOFER, UserRole.HELPER_ADMIN, UserRole.ADMIN,
    ]
    if not exclude_super_admin:
        roles.append(UserRole.SUPER_ADMIN)
    for role in roles:
        builder.button(text=t(_ROLE_KEY_MAP[role], lang), callback_data=f"set_role:{role.value}")
    builder.adjust(2)
    return builder.as_markup()


def get_user_action_keyboard(user_id: int, is_active: bool, lang: str = "uz_lat") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔄 " + t("change_role", lang) if lang == "uz_lat" else "🔄 Rol",
        callback_data=f"change_role:{user_id}",
    )
    builder.button(
        text="📍 " + t("select_region", lang),
        callback_data=f"change_region:{user_id}",
    )
    toggle_text = "🔴 " + t("blocked", lang) if is_active else "🟢 " + t("active", lang)
    builder.button(
        text=toggle_text,
        callback_data=f"toggle_active:{user_id}",
    )
    builder.button(text=t("btn_back", lang), callback_data="user_list:0")
    builder.adjust(1)
    return builder.as_markup()


def get_back_keyboard(callback_data: str = "back", lang: str = "uz_lat") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=t("btn_back", lang), callback_data=callback_data)
    return builder.as_markup()


def get_skip_keyboard(lang: str = "uz_lat") -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=t("btn_skip", lang)))
    builder.add(KeyboardButton(text=t("btn_cancel", lang)))
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
