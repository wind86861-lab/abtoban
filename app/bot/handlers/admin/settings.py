from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.filters import RoleFilter
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu
from app.bot.keyboards.order import (
    get_asphalt_actions_keyboard,
    get_asphalt_manage_keyboard,
)
from app.bot.states.order import AdminSettingsStates
from app.db.models import ADMIN_ROLES, User
from app.services.asphalt_service import AsphaltService

router = Router()


@router.message(F.text == "🔧 Sozlamalar", RoleFilter(*ADMIN_ROLES))
async def settings_menu(message: Message) -> None:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏗 Asfalt turlari", callback_data="asphalt_list")
    builder.adjust(1)
    await message.answer(
        "🔧 <b>Sozlamalar</b>\n\nNimani sozlamoqchisiz?",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "asphalt_list", RoleFilter(*ADMIN_ROLES))
async def asphalt_list(callback: CallbackQuery, session) -> None:
    svc = AsphaltService(session)
    types = await svc.get_all()
    if not types:
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ Yangi qo'shish", callback_data="add_asphalt_type")
        await callback.message.edit_text(
            "🏗 Asfalt turlari yo'q.\nYangi qo'shing:",
            reply_markup=builder.as_markup(),
        )
    else:
        await callback.message.edit_text(
            "🏗 <b>Asfalt turlari</b>\nBoshqarish uchun tanlang:",
            reply_markup=get_asphalt_manage_keyboard(types),
        )
    await callback.answer()


@router.callback_query(F.data == "add_asphalt_type", RoleFilter(*ADMIN_ROLES))
async def start_add_asphalt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminSettingsStates.entering_asphalt_name)
    await callback.message.edit_text(
        "🏗 Yangi asfalt turi nomini kiriting:\n"
        "Misol: <code>Issiq asfalt</code>, <code>Sovuq asfalt</code>"
    )
    await callback.answer()


@router.message(AdminSettingsStates.entering_asphalt_name, RoleFilter(*ADMIN_ROLES))
async def handle_asphalt_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("❌ Ism juda qisqa. Qaytadan kiriting:")
        return
    await state.update_data(asphalt_name=name)
    await state.set_state(AdminSettingsStates.entering_asphalt_price)
    await message.answer(
        f"💰 <b>{name}</b> uchun m² narxini kiriting (so'm):\n"
        f"Misol: <code>85000</code>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(AdminSettingsStates.entering_asphalt_price, RoleFilter(*ADMIN_ROLES))
async def handle_asphalt_price(message: Message, state: FSMContext, user: User, session, lang: str) -> None:
    raw = (message.text or "").strip().replace(" ", "").replace(",", "")
    try:
        price = Decimal(raw)
        if price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Noto'g'ri narx. Raqam kiriting (masalan: 85000):")
        return

    data = await state.get_data()
    await state.clear()

    svc = AsphaltService(session)
    at = await svc.create(name=data["asphalt_name"], price_per_m2=price)

    await message.answer(
        f"✅ Asfalt turi qo'shildi!\n\n"
        f"🏗 Nom: <b>{at.name}</b>\n"
        f"💰 Narx: <b>{float(at.price_per_m2):,.0f} so'm/m²</b>",
        reply_markup=get_main_menu(user.role, lang),
    )


@router.callback_query(F.data.startswith("manage_asphalt:"), RoleFilter(*ADMIN_ROLES))
async def manage_asphalt_item(callback: CallbackQuery, session) -> None:
    asphalt_id = int(callback.data.split(":")[1])
    svc = AsphaltService(session)
    at = await svc.get_by_id(asphalt_id)
    if not at:
        await callback.answer("❌ Topilmadi", show_alert=True)
        return
    status = "🟢 Faol" if at.is_active else "🔴 O'chirilgan"
    await callback.message.edit_text(
        f"🏗 <b>{at.name}</b>\n"
        f"💰 Narx: <b>{float(at.price_per_m2):,.0f} so'm/m²</b>\n"
        f"Holat: {status}",
        reply_markup=get_asphalt_actions_keyboard(at.id, at.is_active),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_asphalt:"), RoleFilter(*ADMIN_ROLES))
async def toggle_asphalt(callback: CallbackQuery, session) -> None:
    asphalt_id = int(callback.data.split(":")[1])
    svc = AsphaltService(session)
    at = await svc.toggle_active(asphalt_id)
    if not at:
        await callback.answer("❌ Topilmadi", show_alert=True)
        return
    status_word = "faollashtirildi" if at.is_active else "o'chirildi"
    await callback.answer(f"✅ {at.name} {status_word}")
    # Refresh the same item view
    callback.data = f"manage_asphalt:{asphalt_id}"
    await manage_asphalt_item(callback, session)


@router.callback_query(F.data.startswith("edit_asphalt_price:"), RoleFilter(*ADMIN_ROLES))
async def start_edit_price(callback: CallbackQuery, state: FSMContext) -> None:
    asphalt_id = int(callback.data.split(":")[1])
    await state.update_data(asphalt_id=asphalt_id)
    await state.set_state(AdminSettingsStates.updating_asphalt_price)
    await callback.message.edit_text(
        "💰 Yangi narxni kiriting (so'm):\nMisol: <code>90000</code>"
    )
    await callback.answer()


@router.message(AdminSettingsStates.updating_asphalt_price, RoleFilter(*ADMIN_ROLES))
async def handle_price_update(message: Message, state: FSMContext, user: User, session, lang: str) -> None:
    raw = (message.text or "").strip().replace(" ", "").replace(",", "")
    try:
        price = Decimal(raw)
        if price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Noto'g'ri narx. Raqam kiriting:")
        return

    data = await state.get_data()
    await state.clear()

    svc = AsphaltService(session)
    at = await svc.update_price(data["asphalt_id"], price)
    if not at:
        await message.answer("❌ Asfalt turi topilmadi.")
        return

    await message.answer(
        f"✅ Narx yangilandi!\n\n"
        f"🏗 {at.name}: <b>{float(at.price_per_m2):,.0f} so'm/m²</b>",
        reply_markup=get_main_menu(user.role, lang),
    )
