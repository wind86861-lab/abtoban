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
from app.services.asphalt_service import AsphaltService, CategoryService

router = Router()


@router.message(F.text == "🔧 Sozlamalar", RoleFilter(*ADMIN_ROLES))
async def settings_menu(message: Message) -> None:
    builder = InlineKeyboardBuilder()
    builder.button(text="📁 Kategoriyalar", callback_data="category_list")
    builder.adjust(1)
    await message.answer(
        "🔧 <b>Sozlamalar</b>\n\nBoshqarish uchun tanlang:",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "category_list", RoleFilter(*ADMIN_ROLES))
async def category_list(callback: CallbackQuery, session) -> None:
    cat_svc = CategoryService(session)
    categories = await cat_svc.get_all_categories()
    
    builder = InlineKeyboardBuilder()
    if categories:
        for cat in categories:
            builder.button(text=f"📁 {cat.name}", callback_data=f"view_category:{cat.id}")
    builder.button(text="➕ Yangi kategoriya", callback_data="add_category")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "📁 <b>Kategoriyalar</b>\n\nTanlang:",
        reply_markup=builder.as_markup(),
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
    await state.set_state(AdminSettingsStates.entering_asphalt_cost_price)
    await message.answer(
        f"� <b>{name}</b> uchun tannarxini kiriting (so'm/m²):\n"
        f"Misol: <code>65000</code>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(AdminSettingsStates.entering_asphalt_cost_price, RoleFilter(*ADMIN_ROLES))
async def handle_asphalt_cost_price(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip().replace(" ", "").replace(",", "")
    try:
        cost_price = Decimal(raw)
        if cost_price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Noto'g'ri narx. Raqam kiriting (masalan: 65000):")
        return
    
    data = await state.get_data()
    await state.update_data(asphalt_cost_price=cost_price)
    await state.set_state(AdminSettingsStates.entering_asphalt_price)
    await message.answer(
        f"💰 <b>{data['asphalt_name']}</b> uchun sotish narxini kiriting (so'm/m²):\n"
        f"Tannarxi: <b>{float(cost_price):,.0f} so'm/m²</b>\n\n"
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
    cost_price = data.get("asphalt_cost_price", Decimal("0"))
    await state.clear()

    svc = AsphaltService(session)
    at = await svc.create(
        name=data["asphalt_name"], 
        cost_price_per_m2=cost_price,
        price_per_m2=price
    )
    
    profit_per_m2 = price - cost_price

    await message.answer(
        f"✅ Asfalt turi qo'shildi!\n\n"
        f"🏗 Nom: <b>{at.name}</b>\n"
        f"� Tannarxi: <b>{float(cost_price):,.0f} so'm/m²</b>\n"
        f"💰 Sotish narxi: <b>{float(price):,.0f} so'm/m²</b>\n"
        f"💎 Foyda: <b>{float(profit_per_m2):,.0f} so'm/m²</b>",
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
    
    cost_price = at.cost_price_per_m2 or Decimal("0")
    selling_price = at.price_per_m2
    profit_per_m2 = selling_price - cost_price
    
    status = "🟢 Faol" if at.is_active else "🔴 O'chirilgan"
    await callback.message.edit_text(
        f"🏗 <b>{at.name}</b>\n\n"
        f"� Tannarxi: <b>{float(cost_price):,.0f} so'm/m²</b>\n"
        f"💰 Sotish narxi: <b>{float(selling_price):,.0f} so'm/m²</b>\n"
        f"💎 Foyda: <b>{float(profit_per_m2):,.0f} so'm/m²</b>\n\n"
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
