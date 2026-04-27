from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.filters import RoleFilter
from app.bot.i18n import ALL_BUTTON_TEXTS
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu
from app.bot.states.order import AdminSettingsStates
from app.db.models import ADMIN_ROLES, User
from app.services.category_service import CategoryService

router = Router()


@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_settings", set())), RoleFilter(*ADMIN_ROLES))
async def settings_menu(message: Message) -> None:
    builder = InlineKeyboardBuilder()
    builder.button(text="📁 Kategoriyalar", callback_data="category_list")
    builder.adjust(1)
    await message.answer(
        "🔧 <b>Sozlamalar</b>\n\nBoshqarish uchun tanlang:",
        reply_markup=builder.as_markup(),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CATEGORY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

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


@router.callback_query(F.data.startswith("view_category:"), RoleFilter(*ADMIN_ROLES))
async def view_category(callback: CallbackQuery, session) -> None:
    category_id = int(callback.data.split(":")[1])
    cat_svc = CategoryService(session)
    category = await cat_svc.get_category_by_id(category_id)
    
    if not category:
        await callback.answer("❌ Kategoriya topilmadi", show_alert=True)
        return
    
    subcategories = await cat_svc.get_subcategories_by_category(category_id)
    
    builder = InlineKeyboardBuilder()
    if subcategories:
        for subcat in subcategories:
            builder.button(
                text=f"📂 {subcat.name}", 
                callback_data=f"view_subcategory:{subcat.id}"
            )
    builder.button(text="➕ Yangi sub-kategoriya", callback_data=f"add_subcategory:{category_id}")
    builder.button(text="� Kategoriyani o'chirish", callback_data=f"delete_category:{category_id}")
    builder.button(text="� Orqaga", callback_data="category_list")
    builder.adjust(1)
    
    await callback.message.edit_text(
        f"📁 <b>{category.name}</b>\n\n"
        f"Sub-kategoriyalar:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data == "add_category", RoleFilter(*ADMIN_ROLES))
async def start_add_category(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminSettingsStates.entering_category_name)
    await callback.message.edit_text(
        "📁 Yangi kategoriya nomini kiriting:\n"
        "Misol: <code>Issiq asfalt</code>, <code>Sovuq asfalt</code>"
    )
    await callback.answer()


@router.message(AdminSettingsStates.entering_category_name, RoleFilter(*ADMIN_ROLES))
async def handle_category_name(message: Message, state: FSMContext, session, user: User, lang: str) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("❌ Nom juda qisqa. Qaytadan kiriting:")
        return
    
    cat_svc = CategoryService(session)
    category = await cat_svc.create_category(name=name)
    await state.clear()
    
    await message.answer(
        f"✅ Kategoriya qo'shildi!\n\n"
        f"📁 <b>{category.name}</b>",
        reply_markup=get_main_menu(user.role, lang),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SUBCATEGORY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("add_subcategory:"), RoleFilter(*ADMIN_ROLES))
async def start_add_subcategory(callback: CallbackQuery, state: FSMContext) -> None:
    category_id = int(callback.data.split(":")[1])
    await state.update_data(category_id=category_id)
    await state.set_state(AdminSettingsStates.entering_subcategory_name)
    await callback.message.edit_text(
        "📂 Yangi sub-kategoriya nomini kiriting:\n"
        "Misol: <code>Zich asfalt</code>, <code>Ochiq asfalt</code>"
    )
    await callback.answer()


@router.message(AdminSettingsStates.entering_subcategory_name, RoleFilter(*ADMIN_ROLES))
async def handle_subcategory_name(message: Message, state: FSMContext, session, user: User, lang: str) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("❌ Nom juda qisqa. Qaytadan kiriting:")
        return
    
    data = await state.get_data()
    category_id = data["category_id"]
    
    cat_svc = CategoryService(session)
    subcategory = await cat_svc.create_subcategory(category_id=category_id, name=name)
    await state.clear()
    
    await message.answer(
        f"✅ Sub-kategoriya qo'shildi!\n\n"
        f"📂 <b>{subcategory.name}</b>",
        reply_markup=get_main_menu(user.role, lang),
    )


@router.callback_query(F.data.startswith("view_subcategory:"), RoleFilter(*ADMIN_ROLES))
async def view_subcategory(callback: CallbackQuery, session) -> None:
    subcategory_id = int(callback.data.split(":")[1])
    cat_svc = CategoryService(session)
    subcategory = await cat_svc.get_subcategory_by_id(subcategory_id)
    
    if not subcategory:
        await callback.answer("❌ Sub-kategoriya topilmadi", show_alert=True)
        return
    
    materials = await cat_svc.get_materials_by_subcategory(subcategory_id)
    
    builder = InlineKeyboardBuilder()
    if materials:
        for material in materials:
            price_text = f"{float(material.price_per_m2):,.0f} so'm/m²"
            builder.button(
                text=f"📄 {material.name} — {price_text}",
                callback_data=f"view_material:{material.id}"
            )
    builder.button(text="➕ Yangi material", callback_data=f"add_material:{subcategory_id}")
    builder.button(text="🗑 Sub-kategoriyani o'chirish", callback_data=f"delete_subcategory:{subcategory_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"view_category:{subcategory.category_id}")
    builder.adjust(1)
    
    await callback.message.edit_text(
        f"📂 <b>{subcategory.name}</b>\n\n"
        f"Materiallar:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════════
# MATERIAL MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("add_material:"), RoleFilter(*ADMIN_ROLES))
async def start_add_material(callback: CallbackQuery, state: FSMContext) -> None:
    subcategory_id = int(callback.data.split(":")[1])
    await state.update_data(subcategory_id=subcategory_id)
    await state.set_state(AdminSettingsStates.entering_material_name)
    await callback.message.edit_text(
        "📄 Yangi material nomini kiriting:\n"
        "Misol: <code>AC-16</code>, <code>Polimer asfalt</code>"
    )
    await callback.answer()


@router.message(AdminSettingsStates.entering_material_name, RoleFilter(*ADMIN_ROLES))
async def handle_material_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("❌ Nom juda qisqa. Qaytadan kiriting:")
        return
    
    await state.update_data(material_name=name)
    await state.set_state(AdminSettingsStates.entering_material_cost_price)
    await message.answer(
        f"💵 <b>{name}</b> uchun tannarxini kiriting (so'm/m²):\n"
        f"Misol: <code>65000</code>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(AdminSettingsStates.entering_material_cost_price, RoleFilter(*ADMIN_ROLES))
async def handle_material_cost_price(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip().replace(" ", "").replace(",", "")
    try:
        cost_price = Decimal(raw)
        if cost_price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Noto'g'ri narx. Raqam kiriting (masalan: 65000):")
        return
    
    data = await state.get_data()
    await state.update_data(material_cost_price=str(cost_price))
    await state.set_state(AdminSettingsStates.entering_material_price)
    await message.answer(
        f"💰 <b>{data['material_name']}</b> uchun sotish narxini kiriting (so'm/m²):\n"
        f"Tannarxi: <b>{float(cost_price):,.0f} so'm/m²</b>\n\n"
        f"Misol: <code>85000</code>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(AdminSettingsStates.entering_material_price, RoleFilter(*ADMIN_ROLES))
async def handle_material_price(message: Message, state: FSMContext, session, user: User, lang: str) -> None:
    raw = (message.text or "").strip().replace(" ", "").replace(",", "")
    try:
        price = Decimal(raw)
        if price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Noto'g'ri narx. Raqam kiriting (masalan: 85000):")
        return

    data = await state.get_data()
    cost_price = Decimal(str(data.get("material_cost_price", "0")))
    subcategory_id = data["subcategory_id"]
    
    cat_svc = CategoryService(session)
    material = await cat_svc.create_material(
        subcategory_id=subcategory_id,
        name=data["material_name"],
        cost_price_per_m2=cost_price,
        price_per_m2=price
    )
    
    await state.clear()
    
    profit_per_m2 = price - cost_price
    
    await message.answer(
        f"✅ Material qo'shildi!\n\n"
        f"📄 Nom: <b>{material.name}</b>\n"
        f"💵 Tannarxi: <b>{float(cost_price):,.0f} so'm/m²</b>\n"
        f"💰 Sotish narxi: <b>{float(price):,.0f} so'm/m²</b>\n"
        f"💎 Foyda: <b>{float(profit_per_m2):,.0f} so'm/m²</b>",
        reply_markup=get_main_menu(user.role, lang),
    )


@router.callback_query(F.data.startswith("view_material:"), RoleFilter(*ADMIN_ROLES))
async def view_material(callback: CallbackQuery, session) -> None:
    material_id = int(callback.data.split(":")[1])
    
    from app.services.asphalt_service import AsphaltService
    asphalt_svc = AsphaltService(session)
    material = await asphalt_svc.get_by_id(material_id)
    
    if not material:
        await callback.answer("❌ Material topilmadi", show_alert=True)
        return
    
    cost_price = material.cost_price_per_m2 or Decimal("0")
    selling_price = material.price_per_m2
    profit_per_m2 = selling_price - cost_price
    
    status = "🟢 Faol" if material.is_active else "🔴 O'chirilgan"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Narxni o'zgartirish", callback_data=f"edit_material_price:{material_id}")
    toggle_text = "🔴 O'chirish" if material.is_active else "🟢 Faollashtirish"
    builder.button(text=toggle_text, callback_data=f"toggle_material:{material_id}")
    builder.button(text="🗑 O'chirish", callback_data=f"delete_material:{material_id}")
    if material.subcategory_id:
        builder.button(text="🔙 Orqaga", callback_data=f"view_subcategory:{material.subcategory_id}")
    builder.adjust(1)
    
    await callback.message.edit_text(
        f"📄 <b>{material.name}</b>\n\n"
        f"💵 Tannarxi: <b>{float(cost_price):,.0f} so'm/m²</b>\n"
        f"💰 Sotish narxi: <b>{float(selling_price):,.0f} so'm/m²</b>\n"
        f"💎 Foyda: <b>{float(profit_per_m2):,.0f} so'm/m²</b>\n\n"
        f"Holat: {status}",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_material:"), RoleFilter(*ADMIN_ROLES))
async def toggle_material(callback: CallbackQuery, session) -> None:
    material_id = int(callback.data.split(":")[1])
    
    from app.services.asphalt_service import AsphaltService
    asphalt_svc = AsphaltService(session)
    material = await asphalt_svc.toggle_active(material_id)
    
    if not material:
        await callback.answer("❌ Topilmadi", show_alert=True)
        return
    
    status_word = "faollashtirildi" if material.is_active else "o'chirildi"
    await callback.answer(f"✅ {material.name} {status_word}")
    
    # Refresh the view
    callback.data = f"view_material:{material_id}"
    await view_material(callback, session)


@router.callback_query(F.data.startswith("edit_material_price:"), RoleFilter(*ADMIN_ROLES))
async def start_edit_material_price(callback: CallbackQuery, state: FSMContext) -> None:
    material_id = int(callback.data.split(":")[1])
    await state.update_data(material_id=material_id)
    await state.set_state(AdminSettingsStates.updating_material_price)
    await callback.message.edit_text(
        "💰 Yangi narxni kiriting (so'm/m²):\nMisol: <code>90000</code>"
    )
    await callback.answer()


@router.message(AdminSettingsStates.updating_material_price, RoleFilter(*ADMIN_ROLES))
async def handle_material_price_update(message: Message, state: FSMContext, session, user: User, lang: str) -> None:
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

    from app.services.asphalt_service import AsphaltService
    asphalt_svc = AsphaltService(session)
    material = await asphalt_svc.update_price(data["material_id"], price)
    
    if not material:
        await message.answer("❌ Material topilmadi.")
        return

    await message.answer(
        f"✅ Narx yangilandi!\n\n"
        f"📄 {material.name}: <b>{float(material.price_per_m2):,.0f} so'm/m²</b>",
        reply_markup=get_main_menu(user.role, lang),
    )


@router.callback_query(F.data.startswith("delete_category:"), RoleFilter(*ADMIN_ROLES))
async def delete_category(callback: CallbackQuery, session) -> None:
    category_id = int(callback.data.split(":")[1])
    cat_svc = CategoryService(session)
    category = await cat_svc.get_category_by_id(category_id)
    if not category:
        await callback.answer("❌ Topilmadi", show_alert=True)
        return
    name = category.name
    await cat_svc.delete_category(category_id)
    await callback.answer(f"✅ '{name}' o'chirildi", show_alert=True)
    await category_list(callback, session)


@router.callback_query(F.data.startswith("delete_subcategory:"), RoleFilter(*ADMIN_ROLES))
async def delete_subcategory(callback: CallbackQuery, session) -> None:
    subcategory_id = int(callback.data.split(":")[1])
    cat_svc = CategoryService(session)
    subcategory = await cat_svc.get_subcategory_by_id(subcategory_id)
    if not subcategory:
        await callback.answer("❌ Topilmadi", show_alert=True)
        return
    category_id = subcategory.category_id
    name = subcategory.name
    await cat_svc.delete_subcategory(subcategory_id)
    await callback.answer(f"✅ '{name}' o'chirildi", show_alert=True)
    callback.data = f"view_category:{category_id}"
    await view_category(callback, session)


@router.callback_query(F.data.startswith("delete_material:"), RoleFilter(*ADMIN_ROLES))
async def delete_material_handler(callback: CallbackQuery, session) -> None:
    material_id = int(callback.data.split(":")[1])
    from app.services.asphalt_service import AsphaltService
    asphalt_svc = AsphaltService(session)
    material = await asphalt_svc.get_by_id(material_id)
    if not material:
        await callback.answer("❌ Topilmadi", show_alert=True)
        return
    subcategory_id = material.subcategory_id
    name = material.name
    cat_svc = CategoryService(session)
    await cat_svc.delete_material(material_id)
    await callback.answer(f"✅ '{name}' o'chirildi", show_alert=True)
    if subcategory_id:
        callback.data = f"view_subcategory:{subcategory_id}"
        await view_subcategory(callback, session)
    else:
        await category_list(callback, session)
