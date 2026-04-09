from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters import RoleFilter
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu
from app.bot.keyboards.order import (
    get_asphalt_keyboard,
    get_order_confirm_keyboard,
    get_regions_keyboard,
)
from app.bot.states.order import KlientOrderStates, PriceCalculatorStates
from app.db.models import ORDER_STATUS_LABELS, User, UserRole
from app.services.asphalt_service import AsphaltService
from app.services.order_service import OrderService
from app.services.user_service import UserService

router = Router()
router.message.filter(RoleFilter(UserRole.KLIENT))


# ── Order creation ────────────────────────────────────────────────────────────

@router.message(F.text == "📝 Zakaz qoldirish")
async def order_create_start(message: Message, state: FSMContext, user: User, session) -> None:
    if not user.phone:
        await message.answer(
            "❗ Avval telefon raqamingizni ro'yxatdan o'tkazing.\n"
            "Buning uchun /start buyrug'ini yuboring."
        )
        return
    from app.services.user_service import UserService
    user_svc = UserService(session)
    regions = await user_svc.get_regions()
    if not regions:
        await message.answer("⚠️ Viloyatlar hali sozlanmagan. Admin bilan bog'laning.")
        return
    await state.set_state(KlientOrderStates.selecting_region)
    await message.answer(
        "� <b>Zakaz qoldirish</b>\n\n"
        "1️⃣ Viloyatni tanlang:",
        reply_markup=get_regions_keyboard(regions),
    )


@router.callback_query(KlientOrderStates.selecting_region, F.data.startswith("region:"))
async def handle_region_select(callback: CallbackQuery, state: FSMContext) -> None:
    region_id = int(callback.data.split(":")[1])
    await state.update_data(region_id=region_id)
    await state.set_state(KlientOrderStates.entering_district)
    await callback.message.edit_text("✅ Viloyat tanlandi\n\n2️⃣ Tumanni kiriting:")
    await callback.answer()


@router.message(KlientOrderStates.entering_district)
async def handle_district(message: Message, state: FSMContext) -> None:
    district = message.text.strip() if message.text else ""
    if len(district) < 2:
        await message.answer("❌ Tumanni to'liq kiriting:")
        return
    await state.update_data(district=district)
    await state.set_state(KlientOrderStates.entering_street)
    await message.answer(
        "3️⃣ Ko'cha nomini kiriting:\n<i>Masalan: Amir Temur ko'chasi</i>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(KlientOrderStates.entering_street)
async def handle_street(message: Message, state: FSMContext) -> None:
    street = message.text.strip() if message.text else ""
    if len(street) < 3:
        await message.answer("❌ Ko'cha nomini aniqroq yozing:")
        return
    await state.update_data(street=street)
    await state.set_state(KlientOrderStates.entering_target)
    await message.answer(
        "4️⃣ Mo'ljal/orientir kiriting:\n<i>Masalan: Maktab yonida, 45-uy</i>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(KlientOrderStates.entering_target)
async def handle_target(message: Message, state: FSMContext) -> None:
    target = message.text.strip() if message.text else ""
    if len(target) < 3:
        await message.answer("❌ Mo'ljalni aniqroq yozing:")
        return
    data = await state.get_data()
    # Build full address string
    full_address = f"{data.get('district', '')}, {data.get('street', '')}, {target}"
    await state.update_data(address=full_address, target=target)
    await state.set_state(KlientOrderStates.entering_area)
    await message.answer(
        "📐 Taxminiy maydon hajmini kiriting (<b>m²</b>):\n"
        "Misol: <code>500</code>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(KlientOrderStates.entering_area)
async def handle_order_area(message: Message, state: FSMContext, session) -> None:
    raw = (message.text or "").strip().replace(",", ".")
    try:
        area = Decimal(raw)
        if area <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Noto'g'ri format. Faqat musbat raqam kiriting (masalan: 500):")
        return

    await state.update_data(area_m2=str(area))

    asphalt_svc = AsphaltService(session)
    asphalt_types = await asphalt_svc.get_all_active()

    if not asphalt_types:
        await message.answer(
            "⚠️ Asfalt turlari hali sozlanmagan. Admin bilan bog'laning.",
            reply_markup=get_main_menu(UserRole.KLIENT),
        )
        await state.clear()
        return

    await state.set_state(KlientOrderStates.selecting_asphalt)
    await message.answer(
        "🏗 Asfalt turini tanlang:",
        reply_markup=get_asphalt_keyboard(asphalt_types),
    )


@router.callback_query(KlientOrderStates.selecting_asphalt, F.data.startswith("asphalt:"))
async def handle_asphalt_pick(callback: CallbackQuery, state: FSMContext, session) -> None:
    asphalt_id = int(callback.data.split(":")[1])
    asphalt_svc = AsphaltService(session)
    asphalt = await asphalt_svc.get_by_id(asphalt_id)
    if not asphalt:
        await callback.answer("❌ Asfalt turi topilmadi", show_alert=True)
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
        f"📋 <b>Zakaz ma'lumotlari</b>\n\n"
        f"📍 <b>Manzil:</b>\n"
        f"   Viloyat: {data.get('district', '—')}\n"
        f"   Ko'cha: {data.get('street', '—')}\n"
        f"   Mo'ljal: {data.get('target', '—')}\n\n"
        f"📐 Maydon: <b>{area} m²</b>\n"
        f"🏗 Asfalt: <b>{asphalt.name}</b>\n"
        f"💰 Taxminiy narx: <b>{float(estimated):,.0f} so'm</b>\n\n"
        f"Tasdiqlaysizmi?",
        reply_markup=get_order_confirm_keyboard(),
    )
    await callback.answer()


@router.callback_query(KlientOrderStates.confirming, F.data == "confirm_order")
async def submit_order(callback: CallbackQuery, state: FSMContext, user: User, session) -> None:
    data = await state.get_data()
    await state.clear()

    order_svc = OrderService(session)
    order = await order_svc.create(
        client=user,
        address=data["address"],
        area_m2=Decimal(data["area_m2"]),
        asphalt_type_id=data.get("asphalt_type_id"),
    )

    # Notify all masters
    from app.bot.loader import bot
    user_svc = UserService(session)
    masters = await user_svc.get_all(role=UserRole.MASTER)
    notify_text = (
        f"🆕 <b>Yangi zakaz!</b>\n\n"
        f"🔢 #{order.order_number}\n"
        f"👤 {user.full_name or 'Nomsiz'}\n"
        f"📱 {user.phone}\n"
        f"📍 {order.address}\n"
        f"📐 {order.area_m2} m²\n"
        f"🏗 {data.get('asphalt_name', '—')}"
    )
    for master in masters:
        try:
            await bot.send_message(master.telegram_id, notify_text)
        except Exception:
            pass

    await callback.message.edit_text(
        f"✅ <b>Zakaz qabul qilindi!</b>\n\n"
        f"🔢 Raqam: <code>{order.order_number}</code>\n"
        f"📍 Manzil: {order.address}\n"
        f"📐 Maydon: {order.area_m2} m²\n\n"
        f"Yaqin orada master siz bilan bog'lanadi."
    )
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(UserRole.KLIENT))
    await callback.answer()


@router.callback_query(KlientOrderStates.confirming, F.data == "cancel_order")
async def cancel_order_creation(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Zakaz bekor qilindi.")
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(UserRole.KLIENT))
    await callback.answer()


# ── My orders ─────────────────────────────────────────────────────────────────

@router.message(F.text == "📋 Mening zakazlarim")
async def my_orders(message: Message, user: User, session) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_client(user.id)

    if not orders:
        await message.answer(
            "📋 <b>Mening zakazlarim</b>\n\nSizda hali zakazlar yo'q.\n"
            "Zakaz qoldirish uchun 📝 tugmasini bosing."
        )
        return

    lines = ["📋 <b>Mening zakazlarim:</b>\n"]
    for o in orders:
        status_label = ORDER_STATUS_LABELS.get(o.status, o.status.value)
        price_str = f"{float(o.total_price):,.0f} so'm" if o.total_price else "—"
        debt_str = f"{float(o.debt):,.0f} so'm" if o.debt else "0"
        lines.append(
            f"\n🔢 <code>{o.order_number}</code> — {status_label}\n"
            f"  📐 {o.area_m2 or '?'} m²  💰 {price_str}  💳 Qarz: {debt_str}"
        )

    await message.answer("\n".join(lines))


# ── Price calculator ───────────────────────────────────────────────────────────

@router.message(F.text == "🧮 Narx hisoblash")
async def calculator_start(message: Message, state: FSMContext, session) -> None:
    asphalt_svc = AsphaltService(session)
    types = await asphalt_svc.get_all_active()
    if not types:
        await message.answer("⚠️ Asfalt turlari hali sozlanmagan.")
        return
    await state.set_state(PriceCalculatorStates.entering_area)
    await message.answer(
        "🧮 <b>Narx hisoblash</b>\n\n"
        "📐 Maydon hajmini kiriting (m²):\n"
        "Misol: <code>300</code>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(PriceCalculatorStates.entering_area)
async def calculator_area(message: Message, state: FSMContext, session) -> None:
    raw = (message.text or "").strip().replace(",", ".")
    try:
        area = Decimal(raw)
        if area <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Noto'g'ri format. Raqam kiriting:")
        return

    await state.update_data(calc_area=str(area))
    asphalt_svc = AsphaltService(session)
    types = await asphalt_svc.get_all_active()
    await state.set_state(PriceCalculatorStates.selecting_asphalt)
    await message.answer("🏗 Asfalt turini tanlang:", reply_markup=get_asphalt_keyboard(types))


@router.callback_query(PriceCalculatorStates.selecting_asphalt, F.data.startswith("asphalt:"))
async def calculator_result(callback: CallbackQuery, state: FSMContext, session) -> None:
    asphalt_id = int(callback.data.split(":")[1])
    data = await state.get_data()
    await state.clear()

    asphalt_svc = AsphaltService(session)
    asphalt = await asphalt_svc.get_by_id(asphalt_id)
    if not asphalt:
        await callback.answer("❌ Topilmadi", show_alert=True)
        return

    area = Decimal(data["calc_area"])
    total = area * asphalt.price_per_m2

    await callback.message.edit_text(
        f"🧮 <b>Hisob-kitob natijasi</b>\n\n"
        f"📐 Maydon: <b>{area} m²</b>\n"
        f"🏗 Asfalt: <b>{asphalt.name}</b>\n"
        f"💲 Narx: <b>{float(asphalt.price_per_m2):,.0f} so'm/m²</b>\n"
        f"─────────────────\n"
        f"💰 Taxminiy jami: <b>{float(total):,.0f} so'm</b>\n\n"
        f"<i>* Aniq narx master tomonidan belgilanadi</i>"
    )
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(UserRole.KLIENT))
    await callback.answer()


# ── Static pages ──────────────────────────────────────────────────────────────

@router.message(F.text == "📞 Konsultatsiya")
async def consultation(message: Message) -> None:
    await message.answer(
        "📞 <b>Konsultatsiya</b>\n\n"
        "Operatorimiz bilan bog'laning:\n"
        "📱 <b>+998 XX XXX XX XX</b>\n\n"
        "🕒 Ish vaqti: 09:00 — 18:00"
    )


@router.message(F.text == "ℹ️ Kompaniya haqida")
async def about_company(message: Message) -> None:
    await message.answer(
        "🏗 <b>Avtoban Stroy</b>\n\n"
        "Asfalt va yo'l qurilishi bo'yicha professional xizmat.\n\n"
        "📍 Manzil: Toshkent sh.\n"
        "📱 Tel: +998 XX XXX XX XX\n"
        "🕒 Ish vaqti: 09:00 — 18:00\n\n"
        "Ishonchli, tez va sifatli!"
    )
