from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.filters import RoleFilter
from app.bot.keyboards.menus import (
    get_back_keyboard,
    get_pagination_keyboard,
    get_role_selection_keyboard,
    get_user_action_keyboard,
    get_users_menu_keyboard,
)
from app.bot.keyboards.order import get_regions_keyboard
from app.bot.states.registration import AdminRoleStates
from app.db.models import MANAGEMENT_ROLES, ROLE_LABELS, User, UserRole
from app.services.user_service import UserService

router = Router()

PER_PAGE = 10


@router.message(
    F.text == "👥 Foydalanuvchilar",
    RoleFilter(*MANAGEMENT_ROLES),
)
async def users_menu(message: Message, user: User) -> None:
    await message.answer(
        "👥 <b>Foydalanuvchilarni boshqarish</b>\n\nNimani qilmoqchisiz?",
        reply_markup=get_users_menu_keyboard(),
    )


@router.callback_query(F.data == "user_search_by_id", RoleFilter(*MANAGEMENT_ROLES))
async def ask_telegram_id(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminRoleStates.waiting_for_telegram_id)
    await callback.message.edit_text(
        "🔍 Foydalanuvchining <b>Telegram ID</b> sini yuboring:\n\n"
        "<i>ID ni olish uchun foydalanuvchi @userinfobot ga /start yozsin.</i>"
    )
    await callback.answer()


@router.message(AdminRoleStates.waiting_for_telegram_id, RoleFilter(*MANAGEMENT_ROLES))
async def handle_telegram_id_input(
    message: Message,
    state: FSMContext,
    user: User,
    session,
) -> None:
    raw = message.text.strip() if message.text else ""

    if not raw.isdigit():
        await message.answer(
            "❌ Noto'g'ri format. Faqat raqam kiriting (masalan: <code>123456789</code>):"
        )
        return

    tg_id = int(raw)
    user_service = UserService(session)
    target = await user_service.get_by_telegram_id(tg_id)

    if not target:
        await message.answer(
            "❌ Bu Telegram ID bilan foydalanuvchi topilmadi.\n"
            "Foydalanuvchi botga /start bosgan bo'lishi kerak.",
            reply_markup=get_back_keyboard("user_list:0"),
        )
        await state.clear()
        return

    await state.clear()
    await _show_user_detail(message, target)


async def _show_user_detail(event: Message | CallbackQuery, target: User) -> None:
    role_label = ROLE_LABELS.get(target.role, target.role.value)
    status_icon = "🟢" if target.is_active else "🔴"
    region_name = target.region.name if target.region else "—"
    text = (
        f"👤 <b>Foydalanuvchi ma'lumotlari</b>\n\n"
        f"🆔 TG ID: <code>{target.telegram_id}</code>\n"
        f"👤 Ism: <b>{target.full_name or '—'}</b>\n"
        f"📱 Tel: <b>{target.phone or '—'}</b>\n"
        f"👥 Rol: <b>{role_label}</b>\n"
        f"📍 Viloyat: <b>{region_name}</b>\n"
        f"Holat: {status_icon} {'Faol' if target.is_active else 'Bloklangan'}\n"
        f"📅 Ro'yxat: <b>{target.created_at.strftime('%d.%m.%Y')}</b>"
    )
    kb = get_user_action_keyboard(target.id, target.is_active)

    if isinstance(event, Message):
        await event.answer(text, reply_markup=kb)
    else:
        await event.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data.startswith("change_role:"), RoleFilter(*MANAGEMENT_ROLES))
async def prompt_role_selection(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
) -> None:
    target_id = int(callback.data.split(":")[1])

    can_assign_super_admin = user.role == UserRole.SUPER_ADMIN
    await state.update_data(target_user_id=target_id)
    await state.set_state(AdminRoleStates.selecting_role)

    await callback.message.edit_text(
        "👥 Yangi rol tanlang:",
        reply_markup=get_role_selection_keyboard(
            exclude_super_admin=not can_assign_super_admin
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_role:"), AdminRoleStates.selecting_role)
async def assign_role(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session,
) -> None:
    data = await state.get_data()
    target_user_id = data.get("target_user_id")

    if not target_user_id:
        await callback.answer("❌ Xatolik yuz berdi. Qaytadan urinib ko'ring.", show_alert=True)
        await state.clear()
        return

    new_role = UserRole(callback.data.split(":")[1])

    if new_role == UserRole.SUPER_ADMIN and user.role != UserRole.SUPER_ADMIN:
        await callback.answer("❌ Siz super admin tayinlay olmaysiz!", show_alert=True)
        return

    user_service = UserService(session)
    updated = await user_service.update_role(
        user_id=target_user_id,
        new_role=new_role,
        changed_by_id=user.id,
    )

    await state.clear()

    if not updated:
        await callback.answer("❌ Foydalanuvchi topilmadi.", show_alert=True)
        return

    role_label = ROLE_LABELS.get(new_role, new_role.value)
    await callback.message.edit_text(
        f"✅ Rol muvaffaqiyatli o'zgartirildi!\n\n"
        f"👤 <b>{updated.full_name or 'Nomsiz'}</b>\n"
        f"👥 Yangi rol: <b>{role_label}</b>",
        reply_markup=get_back_keyboard("user_list:0"),
    )
    await callback.answer()

    # Notify the user about their role change
    from app.bot.loader import bot
    from app.bot.keyboards.menus import get_main_menu
    from app.bot.i18n import get_lang as _gl
    try:
        target_lang = _gl(updated)
        await bot.send_message(
            updated.telegram_id,
            f"🔔 <b>Rolingiz o'zgartirildi!</b>\n\n"
            f"👥 Yangi rol: <b>{role_label}</b>\n\n"
            f"Yangi menyu yuklandi.",
            reply_markup=get_main_menu(new_role, target_lang),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("change_region:"), RoleFilter(*MANAGEMENT_ROLES))
async def prompt_region_selection(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session,
) -> None:
    target_id = int(callback.data.split(":")[1])
    await state.update_data(target_user_id=target_id)
    await state.set_state(AdminRoleStates.selecting_region)
    user_svc = UserService(session)
    regions = await user_svc.get_regions()
    if not regions:
        await callback.answer("⚠️ Viloyatlar hali sozlanmagan.", show_alert=True)
        await state.clear()
        return
    await callback.message.edit_text(
        "📍 Viloyatni tanlang:",
        reply_markup=get_regions_keyboard(regions),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("region:"), AdminRoleStates.selecting_region)
async def assign_region(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    session,
) -> None:
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    if not target_user_id:
        await callback.answer("❌ Xatolik yuz berdi.", show_alert=True)
        await state.clear()
        return

    region_id = int(callback.data.split(":")[1])
    user_svc = UserService(session)
    updated = await user_svc.update_region(
        user_id=target_user_id,
        region_id=region_id,
        changed_by_id=user.id,
    )
    await state.clear()

    if not updated:
        await callback.answer("❌ Foydalanuvchi topilmadi.", show_alert=True)
        return

    # Reload user with region relationship
    updated = await user_svc.get_by_id(target_user_id)
    await _show_user_detail(callback, updated)
    await callback.answer("✅ Viloyat o'zgartirildi!")


@router.callback_query(F.data.startswith("toggle_active:"), RoleFilter(*MANAGEMENT_ROLES))
async def toggle_user_active(
    callback: CallbackQuery,
    user: User,
    session,
) -> None:
    target_id = int(callback.data.split(":")[1])

    if target_id == user.id:
        await callback.answer("❌ O'zingizni bloklashingiz mumkin emas!", show_alert=True)
        return

    user_service = UserService(session)
    target = await user_service.get_by_id(target_id)

    if not target:
        await callback.answer("❌ Foydalanuvchi topilmadi.", show_alert=True)
        return

    if target.role == UserRole.SUPER_ADMIN and user.role != UserRole.SUPER_ADMIN:
        await callback.answer("❌ Super adminni bloklay olmaysiz!", show_alert=True)
        return

    updated = await user_service.set_active(
        user_id=target_id,
        is_active=not target.is_active,
        changed_by_id=user.id,
    )
    await _show_user_detail(callback, updated)
    status_text = "faollashtirildi" if updated.is_active else "bloklandi"
    await callback.answer(f"✅ Foydalanuvchi {status_text}.")


@router.callback_query(F.data.startswith("user_list:"), RoleFilter(*MANAGEMENT_ROLES))
async def show_user_list(
    callback: CallbackQuery,
    session,
) -> None:
    page = int(callback.data.split(":")[1])
    user_service = UserService(session)

    users = await user_service.get_all(limit=PER_PAGE, offset=page * PER_PAGE)
    total = await user_service.count_all()

    if not users:
        await callback.message.edit_text(
            "👥 Foydalanuvchilar topilmadi.",
            reply_markup=get_back_keyboard("back_main"),
        )
        await callback.answer()
        return

    lines = [f"👥 <b>Foydalanuvchilar</b> (sahifa {page + 1})\n"]
    for u in users:
        role_label = ROLE_LABELS.get(u.role, u.role.value)
        status = "🟢" if u.is_active else "🔴"
        lines.append(
            f"{status} <code>{u.telegram_id}</code> — "
            f"<b>{u.full_name or 'Nomsiz'}</b> [{role_label}]"
        )

    builder = InlineKeyboardBuilder()

    for u in users:
        builder.button(
            text=f"{u.full_name or u.telegram_id}",
            callback_data=f"view_user:{u.id}",
        )
    builder.adjust(1)

    nav_kb = get_pagination_keyboard(page, total, PER_PAGE, "user_list")
    for row in nav_kb.inline_keyboard:
        builder.row(*row)

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("view_user:"), RoleFilter(*MANAGEMENT_ROLES))
async def view_user(
    callback: CallbackQuery,
    session,
) -> None:
    target_id = int(callback.data.split(":")[1])
    user_service = UserService(session)
    target = await user_service.get_by_id(target_id)

    if not target:
        await callback.answer("❌ Foydalanuvchi topilmadi.", show_alert=True)
        return

    await _show_user_detail(callback, target)
    await callback.answer()
