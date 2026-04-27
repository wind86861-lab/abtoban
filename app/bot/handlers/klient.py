from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters import RoleFilter
from app.bot.i18n import t, ALL_BUTTON_TEXTS
from app.bot.i18n.core import location_link
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu
from app.bot.keyboards.order import (
    get_asphalt_categories_keyboard,
    get_asphalt_keyboard,
    get_asphalt_subcategories_keyboard,
    get_order_confirm_keyboard,
    get_regions_keyboard,
    get_tumanlar_keyboard,
    get_viloyatlar_keyboard,
)
from app.bot.states.order import KlientOrderStates, PriceCalculatorStates
from app.db.models import ORDER_STATUS_LABELS, Order, User, UserRole
from app.services.asphalt_service import AsphaltService
from app.services.order_service import OrderService
from app.services.user_service import UserService

router = Router()


# ── Order creation ────────────────────────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_order_create", set())), RoleFilter(UserRole.KLIENT))
async def order_create_start(message: Message, state: FSMContext, user: User, session, lang: str) -> None:
    if not user.phone:
        await message.answer(t("order_no_phone", lang))
        return
    user_svc = UserService(session)
    viloyatlar = await user_svc.get_viloyatlar()
    if not viloyatlar:
        await message.answer(t("no_regions", lang))
        return
    await state.set_state(KlientOrderStates.selecting_viloyat)
    await message.answer(
        t("order_start", lang),
        reply_markup=get_viloyatlar_keyboard(viloyatlar),
    )


@router.callback_query(KlientOrderStates.selecting_viloyat, F.data.startswith("viloyat:"))
async def handle_viloyat_select(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    try:
        viloyat_id = int(callback.data.split(":")[1])
        await state.update_data(viloyat_id=viloyat_id)
        user_svc = UserService(session)
        tumanlar = await user_svc.get_tumanlar(viloyat_id)
        
        if not tumanlar:
            await state.set_state(KlientOrderStates.entering_street)
            await callback.message.edit_text("✅ Viloyat tanlandi!\n\n📍 Ko'cha nomini kiriting:")
            await callback.message.answer(
                "📍 Ko'cha nomini kiriting:",
                reply_markup=get_cancel_keyboard(lang),
            )
        else:
            await state.set_state(KlientOrderStates.selecting_tuman)
            await callback.message.edit_text(
                "✅ Viloyat tanlandi!\n\n🏘 Tumanni tanlang:",
                reply_markup=get_tumanlar_keyboard(tumanlar),
            )
        await callback.answer()
    except Exception as e:
        print(f"Error in viloyat select: {e}")
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(KlientOrderStates.selecting_tuman, F.data.startswith("tuman:"))
async def handle_tuman_select(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    tuman_id = int(callback.data.split(":")[1])
    await state.update_data(tuman_id=tuman_id)
    await state.set_state(KlientOrderStates.entering_street)
    await callback.message.edit_text("✅ Tuman tanlandi!")
    await callback.message.answer(
        "📍 Ko'cha nomini kiriting:",
        reply_markup=get_cancel_keyboard(lang),
    )
    await callback.answer()


@router.message(KlientOrderStates.entering_street, RoleFilter(UserRole.KLIENT))
async def handle_street(message: Message, state: FSMContext, lang: str) -> None:
    street = message.text.strip() if message.text else ""
    if len(street) < 3:
        await message.answer(t("street_too_short", lang))
        return
    await state.update_data(street=street)
    await state.set_state(KlientOrderStates.entering_target)
    await message.answer(
        t("enter_target", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(KlientOrderStates.entering_target, RoleFilter(UserRole.KLIENT))
async def handle_target(message: Message, state: FSMContext, lang: str) -> None:
    target = message.text.strip() if message.text else ""
    if len(target) < 3:
        await message.answer(t("target_too_short", lang))
        return
    data = await state.get_data()
    full_address = f"{data.get('street', '')}, {target}"
    await state.update_data(address=full_address, target=target)
    await state.set_state(KlientOrderStates.sharing_location)
    await message.answer(
        t("share_location", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(KlientOrderStates.sharing_location, F.location, RoleFilter(UserRole.KLIENT))
async def handle_location(message: Message, state: FSMContext, lang: str) -> None:
    await state.update_data(
        latitude=message.location.latitude,
        longitude=message.location.longitude,
    )
    await state.set_state(KlientOrderStates.entering_area)
    await message.answer(
        t("enter_area", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(KlientOrderStates.sharing_location, RoleFilter(UserRole.KLIENT))
async def handle_invalid_location(message: Message, lang: str) -> None:
    await message.answer(t("invalid_location", lang))


@router.message(KlientOrderStates.entering_area, RoleFilter(UserRole.KLIENT))
async def handle_order_area(message: Message, state: FSMContext, session, lang: str) -> None:
    raw = (message.text or "").strip().replace(",", ".")
    try:
        area = Decimal(raw)
        if area <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer(t("invalid_area", lang))
        return

    await state.update_data(area_m2=str(area))

    from app.services.category_service import CategoryService
    cat_svc = CategoryService(session)
    categories = await cat_svc.get_all_categories()
    if categories:
        await state.set_state(KlientOrderStates.selecting_asphalt_category)
        await message.answer(t("select_asphalt", lang), reply_markup=get_asphalt_categories_keyboard(categories))
    else:
        asphalt_svc = AsphaltService(session)
        asphalt_types = await asphalt_svc.get_all_active()
        if not asphalt_types:
            await message.answer(t("no_asphalt_types", lang), reply_markup=get_main_menu(UserRole.KLIENT, lang))
            await state.clear()
            return
        await state.set_state(KlientOrderStates.selecting_asphalt)
        await message.answer(t("select_asphalt", lang), reply_markup=get_asphalt_keyboard(asphalt_types))


@router.callback_query(KlientOrderStates.selecting_asphalt_category, F.data.startswith("asfcat:"))
async def klient_select_category(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    category_id = int(callback.data.split(":")[1])
    from app.services.category_service import CategoryService
    cat_svc = CategoryService(session)
    subcategories = await cat_svc.get_subcategories_by_category(category_id)
    if subcategories:
        await state.set_state(KlientOrderStates.selecting_asphalt_subcategory)
        await callback.message.edit_text(t("select_asphalt", lang), reply_markup=get_asphalt_subcategories_keyboard(subcategories, category_id))
    else:
        asphalt_svc = AsphaltService(session)
        types = await asphalt_svc.get_all_active()
        await state.set_state(KlientOrderStates.selecting_asphalt)
        await callback.message.edit_text(t("select_asphalt", lang), reply_markup=get_asphalt_keyboard(types))
    await callback.answer()


@router.callback_query(KlientOrderStates.selecting_asphalt_subcategory, F.data.startswith("asfsubcat:"))
async def klient_select_subcategory(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    subcategory_id = int(callback.data.split(":")[1])
    from app.services.category_service import CategoryService
    cat_svc = CategoryService(session)
    materials = await cat_svc.get_materials_by_subcategory(subcategory_id)
    if not materials:
        await callback.answer(t("no_asphalt_types", lang), show_alert=True)
        return
    await state.set_state(KlientOrderStates.selecting_asphalt)
    await callback.message.edit_text(t("select_asphalt", lang), reply_markup=get_asphalt_keyboard(materials))
    await callback.answer()


@router.callback_query(KlientOrderStates.selecting_asphalt_subcategory, F.data.startswith("asfcat_back:"))
async def klient_back_to_categories(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    from app.services.category_service import CategoryService
    cat_svc = CategoryService(session)
    categories = await cat_svc.get_all_categories()
    await state.set_state(KlientOrderStates.selecting_asphalt_category)
    await callback.message.edit_text(t("select_asphalt", lang), reply_markup=get_asphalt_categories_keyboard(categories))
    await callback.answer()


@router.callback_query(KlientOrderStates.selecting_asphalt, F.data.startswith("asphalt:"))
async def handle_asphalt_pick(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    asphalt_id = int(callback.data.split(":")[1])
    asphalt_svc = AsphaltService(session)
    asphalt = await asphalt_svc.get_by_id(asphalt_id)
    if not asphalt:
        await callback.answer(t("asphalt_not_found", lang), show_alert=True)
        return

    data = await state.get_data()
    area = Decimal(data["area_m2"])
    estimated = area * asphalt.price_per_m2

    await state.update_data(
        asphalt_type_id=asphalt_id,
        asphalt_name=asphalt.name,
        estimated_price=str(estimated),
    )
    await state.set_state(KlientOrderStates.confirming)

    await callback.message.edit_text(
        t("order_summary", lang,
          district=data.get('district', '—'),
          street=data.get('street', '—'),
          target=data.get('target', '—'),
          location_link=location_link(data.get('latitude'), data.get('longitude')),
          area=area,
          asphalt=asphalt.name,
          price=f"{float(estimated):,.0f}"),
        reply_markup=get_order_confirm_keyboard(),
    )
    await callback.answer()


@router.callback_query(KlientOrderStates.confirming, F.data == "confirm_order")
async def submit_order(callback: CallbackQuery, state: FSMContext, user: User, session, lang: str) -> None:
    data = await state.get_data()
    await state.clear()

    order_svc = OrderService(session)
    order = await order_svc.create(
        client=user,
        address=data["address"],
        area_m2=Decimal(data["area_m2"]),
        asphalt_type_id=data.get("asphalt_type_id"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        region_id=data.get("region_id"),
        viloyat_id=data.get("viloyat_id"),
        tuman_id=data.get("tuman_id"),
    )

    # Notify all masters
    from app.bot.loader import bot
    from app.bot.i18n import get_lang as _gl
    user_svc = UserService(session)
    masters = await user_svc.get_all(role=UserRole.MASTER)
    for master in masters:
        try:
            ml = _gl(master)
            await bot.send_message(
                master.telegram_id,
                t("new_order_notify", ml,
                  number=order.order_number,
                  name=user.full_name or t("nameless", ml),
                  phone=user.phone,
                  address=order.address,
                  location_link=location_link(order.latitude, order.longitude),
                  area=order.area_m2,
                  asphalt=data.get('asphalt_name', '—')),
            )
        except Exception:
            pass

    await callback.message.edit_text(
        t("order_submitted", lang,
          number=order.order_number,
          address=order.address,
          location_link=location_link(order.latitude, order.longitude),
          area=order.area_m2),
    )
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.KLIENT, lang))
    await callback.answer()


@router.callback_query(KlientOrderStates.confirming, F.data == "cancel_order")
async def cancel_order_creation(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await callback.message.edit_text(t("order_cancelled", lang))
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.KLIENT, lang))
    await callback.answer()


# ── My orders ─────────────────────────────────────────────────────────────────

def _client_orders_keyboard(orders: list):
    from aiogram.types import InlineKeyboardMarkup
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for o in orders:
        status_label = ORDER_STATUS_LABELS.get(o.status, o.status.value)
        builder.button(
            text=f"📋 {o.order_number} — {status_label}",
            callback_data=f"klient_order:{o.id}",
        )
    builder.adjust(1)
    return builder.as_markup()


@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_my_orders", set())), RoleFilter(UserRole.KLIENT))
async def my_orders(message: Message, user: User, session, lang: str) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_client(user.id)

    if not orders:
        await message.answer(t("no_orders", lang))
        return

    await message.answer(
        t("my_orders_header", lang, count=len(orders)),
        reply_markup=_client_orders_keyboard(orders),
    )


@router.callback_query(F.data.startswith("klient_order:"))
async def klient_order_detail(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    o = await order_svc.get_by_id_full(order_id)
    if not o:
        await callback.answer(t("order_not_found", lang), show_alert=True)
        return

    from app.bot.handlers._order_view import format_order_full
    text = format_order_full(o, user.role, lang)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Orqaga", callback_data="klient_orders_back")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "klient_orders_back")
async def klient_orders_back(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_client(user.id)
    if not orders:
        await callback.message.edit_text(t("no_orders", lang))
    else:
        await callback.message.edit_text(
            t("my_orders_header", lang, count=len(orders)),
            reply_markup=_client_orders_keyboard(orders),
        )
    await callback.answer()


# ── Price calculator ───────────────────────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_calc_price", set())), RoleFilter(UserRole.KLIENT))
async def calculator_start(message: Message, state: FSMContext, session, lang: str) -> None:
    asphalt_svc = AsphaltService(session)
    types = await asphalt_svc.get_all_active()
    if not types:
        await message.answer(t("no_asphalt_types", lang))
        return
    await state.set_state(PriceCalculatorStates.entering_area)
    await message.answer(
        t("calc_start", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(PriceCalculatorStates.entering_area)
async def calculator_area(message: Message, state: FSMContext, session, lang: str) -> None:
    raw = (message.text or "").strip().replace(",", ".")
    try:
        area = Decimal(raw)
        if area <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer(t("calc_invalid", lang))
        return

    await state.update_data(calc_area=str(area))
    from app.services.category_service import CategoryService
    cat_svc = CategoryService(session)
    categories = await cat_svc.get_all_categories()
    if categories:
        await state.set_state(PriceCalculatorStates.selecting_asphalt_category)
        await message.answer(t("select_asphalt", lang), reply_markup=get_asphalt_categories_keyboard(categories))
    else:
        asphalt_svc = AsphaltService(session)
        types = await asphalt_svc.get_all_active()
        await state.set_state(PriceCalculatorStates.selecting_asphalt)
        await message.answer(t("select_asphalt", lang), reply_markup=get_asphalt_keyboard(types))


@router.callback_query(PriceCalculatorStates.selecting_asphalt_category, F.data.startswith("asfcat:"))
async def calc_select_category(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    category_id = int(callback.data.split(":")[1])
    from app.services.category_service import CategoryService
    cat_svc = CategoryService(session)
    subcategories = await cat_svc.get_subcategories_by_category(category_id)
    if subcategories:
        await state.set_state(PriceCalculatorStates.selecting_asphalt_subcategory)
        await callback.message.edit_text(t("select_asphalt", lang), reply_markup=get_asphalt_subcategories_keyboard(subcategories, category_id))
    else:
        asphalt_svc = AsphaltService(session)
        types = await asphalt_svc.get_all_active()
        await state.set_state(PriceCalculatorStates.selecting_asphalt)
        await callback.message.edit_text(t("select_asphalt", lang), reply_markup=get_asphalt_keyboard(types))
    await callback.answer()


@router.callback_query(PriceCalculatorStates.selecting_asphalt_subcategory, F.data.startswith("asfsubcat:"))
async def calc_select_subcategory(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    subcategory_id = int(callback.data.split(":")[1])
    from app.services.category_service import CategoryService
    cat_svc = CategoryService(session)
    materials = await cat_svc.get_materials_by_subcategory(subcategory_id)
    if not materials:
        await callback.answer(t("no_asphalt_types", lang), show_alert=True)
        return
    await state.set_state(PriceCalculatorStates.selecting_asphalt)
    await callback.message.edit_text(t("select_asphalt", lang), reply_markup=get_asphalt_keyboard(materials))
    await callback.answer()


@router.callback_query(PriceCalculatorStates.selecting_asphalt, F.data.startswith("asphalt:"))
async def calculator_result(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    asphalt_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    await state.clear()

    asphalt_svc = AsphaltService(session)
    asphalt = await asphalt_svc.get_by_id(asphalt_id)
    if not asphalt:
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    area = Decimal(data["calc_area"])
    total = area * asphalt.price_per_m2

    await callback.message.edit_text(
        t("calc_result", lang,
          area=area,
          asphalt=asphalt.name,
          price_per_m2=f"{float(asphalt.price_per_m2):,.0f}",
          total=f"{float(total):,.0f}"),
    )
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.KLIENT, lang))
    await callback.answer()


# ── Static pages ──────────────────────────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_consultation", set())), RoleFilter(UserRole.KLIENT))
async def consultation(message: Message, lang: str) -> None:
    from app.services.app_settings_service import get_setting, lang_key
    text = await get_setting(lang_key("consultation_text", lang), default=t("consultation", lang))
    await message.answer(text)


@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_about", set())), RoleFilter(UserRole.KLIENT))
async def about_company(message: Message, lang: str) -> None:
    from app.services.app_settings_service import get_setting, lang_key
    text = await get_setting(lang_key("about_text", lang), default=t("about_company", lang))
    await message.answer(text)
