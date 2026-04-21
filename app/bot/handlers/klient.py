from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters import RoleFilter
from app.bot.i18n import t, ALL_BUTTON_TEXTS
from app.bot.i18n.core import location_link
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu
from app.bot.keyboards.order import (
    get_asphalt_keyboard,
    get_order_confirm_keyboard,
    get_regions_keyboard,
    get_tumanlar_keyboard,
    get_viloyatlar_keyboard,
)
from app.bot.states.order import KlientOrderStates, PriceCalculatorStates
from app.db.models import ORDER_STATUS_LABELS, User, UserRole
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

    asphalt_svc = AsphaltService(session)
    asphalt_types = await asphalt_svc.get_all_active()

    if not asphalt_types:
        await message.answer(
            t("no_asphalt_types", lang),
            reply_markup=get_main_menu(UserRole.KLIENT, lang),
        )
        await state.clear()
        return

    await state.set_state(KlientOrderStates.selecting_asphalt)
    await message.answer(
        t("select_asphalt", lang),
        reply_markup=get_asphalt_keyboard(asphalt_types),
    )


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

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_my_orders", set())), RoleFilter(UserRole.KLIENT))
async def my_orders(message: Message, user: User, session, lang: str) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_client(user.id)

    if not orders:
        await message.answer(t("no_orders", lang))
        return

    lines = [t("my_orders_header", lang)]
    for o in orders:
        status_label = ORDER_STATUS_LABELS.get(o.status, o.status.value)
        price_str = f"{float(o.total_price):,.0f}" if o.total_price else "—"
        advance_str = f"{float(o.advance_paid):,.0f}" if o.advance_paid else "0"
        debt_str = f"{float(o.debt):,.0f}" if o.debt else "0"
        asphalt = o.asphalt_type.name if o.asphalt_type else "—"
        master_name = o.master.full_name if o.master else "—"
        usta_name = o.usta.full_name if o.usta else "—"
        work_date = o.work_date.strftime("%d.%m.%Y") if o.work_date else "—"
        loc = location_link(o.latitude, o.longitude)
        lines.append(
            f"\n🔢 <code>{o.order_number}</code> — {status_label}\n"
            f"  � {o.address or '—'}\n"
            f"  {loc}"
            f"  🏗 {asphalt}  �📐 {o.area_m2 or '?'} m²\n"
            f"  📅 Ish sanasi: {work_date}\n"
            f"  👷 Master: {master_name}\n"
            f"  � Usta: {usta_name}\n"
            f"  �💰 Narx: {price_str}  � Oldindan: {advance_str}\n"
            f"  �💳 Qarz: <b>{debt_str}</b>"
        )

    await message.answer("\n".join(lines))


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
    asphalt_svc = AsphaltService(session)
    types = await asphalt_svc.get_all_active()
    await state.set_state(PriceCalculatorStates.selecting_asphalt)
    await message.answer(t("select_asphalt", lang), reply_markup=get_asphalt_keyboard(types))


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
    await message.answer(t("consultation", lang))


@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_about", set())), RoleFilter(UserRole.KLIENT))
async def about_company(message: Message, lang: str) -> None:
    await message.answer(t("about_company", lang))
