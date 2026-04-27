from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters import RoleFilter
from app.bot.i18n import t, ALL_BUTTON_TEXTS
from app.bot.keyboards.finance import (
    get_pending_requests_keyboard,
    get_priced_requests_keyboard,
    get_shofer_narxi_confirm_keyboard,
    get_shofer_narxi_requests_keyboard,
    get_zavod_confirm_keyboard,
    get_zavod_request_detail_keyboard,
)
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu
from app.bot.states.finance import ZavodPriceStates, ZavodShoferNarxiStates
from app.bot.states.payment import ZavodPaymentStates
from app.db.models import MaterialRequest, User, UserRole
from app.services.material_service import MaterialService
from app.services.order_service import OrderService
from app.services.payment_transfer_service import PaymentTransferService
from app.services.user_service import UserService

router = Router()
router.message.filter(RoleFilter(UserRole.ZAVOD))


# ── Pending requests ───────────────────────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_material_requests", set()) | ALL_BUTTON_TEXTS.get("btn_set_price", set())))
async def material_requests(message: Message, user: User, session, lang: str) -> None:
    mat_svc = MaterialService(session)
    if user.zavod_id:
        pending = await mat_svc.get_pending_for_zavod(user.zavod_id)
    else:
        pending = await mat_svc.get_pending(region_id=user.region_id)
    if not pending:
        await message.answer(t("no_pending_requests", lang))
        return
    await message.answer(
        t("pending_requests_list", lang, count=len(pending)),
        reply_markup=get_pending_requests_keyboard(pending),
    )


@router.callback_query(F.data == "zavod_pending_list")
async def zavod_pending_list(callback: CallbackQuery, user: User, session, lang: str) -> None:
    mat_svc = MaterialService(session)
    if user.zavod_id:
        pending = await mat_svc.get_pending_for_zavod(user.zavod_id)
    else:
        pending = await mat_svc.get_pending(region_id=user.region_id)
    if not pending:
        await callback.message.edit_text(t("no_pending_requests", lang))
    else:
        await callback.message.edit_text(
            t("pending_requests_list", lang, count=len(pending)),
            reply_markup=get_pending_requests_keyboard(pending),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("zavod_view_req:"))
async def view_request(callback: CallbackQuery, session, lang: str) -> None:
    req_id = int(callback.data.split(":")[1])
    mat_svc = MaterialService(session)
    req = await mat_svc.get_by_id(req_id)
    if not req:
        await callback.answer(t("request_not_found", lang), show_alert=True)
        return

    from app.bot.i18n.core import location_link
    order = req.order
    order_num = order.order_number if order else "?"

    # Order location info
    address = order.address if order and order.address else "—"
    viloyat = order.viloyat.name if order and order.viloyat else None
    tuman = order.tuman_rel.name if order and order.tuman_rel else None
    loc_parts = [p for p in (viloyat, tuman) if p]
    loc_str = ", ".join(loc_parts) if loc_parts else "—"
    loc_link = location_link(order.latitude, order.longitude) if order else ""

    # Usta info
    usta = req.usta
    usta_name = (usta.full_name or str(usta.telegram_id)) if usta else "—"
    usta_phone = (usta.phone or "—") if usta else "—"

    # Master info (so zavod can call master with questions)
    master = order.master if order else None
    master_name = (master.full_name or "—") if master else "—"
    master_phone = (master.phone or "—") if master else "—"

    text = (
        f"📦 <b>Material so'rovi #{req.id}</b>\n\n"
        f"🔢 Zakaz: <b>{order_num}</b>\n"
        f"🗺 Viloyat/Tuman: <b>{loc_str}</b>\n"
        f"📍 Manzil: <b>{address}</b>\n"
        f"{loc_link}"
        f"\n"
        f"📦 Miqdor: <b>{req.amount_tonnes} tonna</b>\n"
        f"📝 Izoh: <i>{req.notes or '—'}</i>\n"
        f"📅 Sana: {req.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"<b>👥 Aloqa:</b>\n"
        f"🔨 Usta: <b>{usta_name}</b>\n"
        f"   📱 <code>{usta_phone}</code>\n"
        f"👷 Master: <b>{master_name}</b>\n"
        f"   📱 <code>{master_phone}</code>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_zavod_request_detail_keyboard(req_id),
    )
    await callback.answer()


# ── Price setting FSM ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("zavod_price:"))
async def start_price_fsm(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    req_id = int(callback.data.split(":")[1])
    await state.update_data(req_id=req_id)
    await state.set_state(ZavodPriceStates.entering_material_price)
    await callback.message.edit_text(t("price_step_material", lang))
    await callback.answer()


@router.message(ZavodPriceStates.entering_material_price)
async def price_material(message: Message, state: FSMContext, lang: str) -> None:
    raw = (message.text or "").strip().replace(" ", "").replace(",", "")
    try:
        price = Decimal(raw)
        if price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer(t("invalid_price", lang))
        return
    await state.update_data(material_price=str(price))
    await state.set_state(ZavodPriceStates.entering_delivery_price)
    await message.answer(
        t("price_step_delivery", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(ZavodPriceStates.entering_delivery_price)
async def price_delivery(message: Message, state: FSMContext, lang: str) -> None:
    raw = (message.text or "").strip().replace(" ", "").replace(",", "")
    try:
        price = Decimal(raw)
        if price < 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(delivery_price=str(price))
    await state.set_state(ZavodPriceStates.entering_extra_cost)
    await message.answer(
        t("price_step_extra", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(ZavodPriceStates.entering_extra_cost)
async def price_extra(message: Message, state: FSMContext, lang: str) -> None:
    raw = (message.text or "").strip().replace(" ", "").replace(",", "")
    try:
        extra = Decimal(raw)
        if extra < 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(extra_cost=str(extra))
    await state.set_state(ZavodPriceStates.confirming)
    data = await state.get_data()
    mat_price = float(Decimal(data["material_price"]))
    del_price = float(Decimal(data["delivery_price"]))
    total = mat_price + del_price + float(extra)
    await message.answer(
        t("price_summary", lang,
          material=f"{mat_price:,.0f}",
          delivery=f"{del_price:,.0f}",
          extra=f"{float(extra):,.0f}",
          total=f"{total:,.0f}"),
        reply_markup=get_zavod_confirm_keyboard(),
    )


@router.callback_query(ZavodPriceStates.confirming, F.data == "zavod_price_confirm")
async def price_submit(callback: CallbackQuery, state: FSMContext, user: User, session, lang: str) -> None:
    data = await state.get_data()
    await state.clear()

    mat_svc = MaterialService(session)
    req = await mat_svc.price(
        req_id=data["req_id"],
        zavod_id=user.id,
        material_price=Decimal(data["material_price"]),
        delivery_price=Decimal(data["delivery_price"]),
        extra_cost=Decimal(data["extra_cost"]),
    )
    if not req:
        await callback.message.edit_text(t("price_error", lang))
        await callback.answer()
        return

    req_full = await mat_svc.get_by_id(req.id)
    total = (
        float(req.material_price or 0)
        + float(req.delivery_price or 0)
        + float(req.extra_cost or 0)
    )

    # Notify usta
    from app.bot.loader import bot
    user_svc = UserService(session)
    if req_full and req_full.usta:
        try:
            ul = _gl(req_full.usta)
            await bot.send_message(
                req_full.usta.telegram_id,
                t("material_price_set_notify", ul,
                  amount=req.amount_tonnes,
                  material=f"{float(req.material_price or 0):,.0f}",
                  delivery=f"{float(req.delivery_price or 0):,.0f}",
                  extra=f"{float(req.extra_cost or 0):,.0f}",
                  total=f"{total:,.0f}"),
            )
        except Exception:
            pass

    # Notify shofers
    shofers = await user_svc.get_all(role=UserRole.SHOFER)
    for shofer in shofers:
        try:
            sl = _gl(shofer)
            await bot.send_message(
                shofer.telegram_id,
                t("delivery_task_notify", sl,
                  amount=req.amount_tonnes,
                  order=req_full.order.order_number if req_full and req_full.order else '?'),
                reply_markup=get_shofer_delivery_keyboard(req.id),
            )
        except Exception:
            pass

    await callback.message.edit_text(
        t("price_set_success", lang,
          amount=req.amount_tonnes,
          total=f"{total:,.0f}"),
    )
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.ZAVOD, lang))
    await callback.answer()


@router.callback_query(ZavodPriceStates.confirming, F.data == "zavod_price_cancel")
async def price_cancel(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await callback.message.edit_text(t("action_cancelled", lang))
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.ZAVOD, lang))
    await callback.answer()


# ── Delivery confirm (by zavod) ────────────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_zavod_history", set())))
async def history(message: Message, user: User, session, lang: str) -> None:
    mat_svc = MaterialService(session)
    if user.zavod_id:
        priced = await mat_svc.get_priced_for_zavod(user.zavod_id)
    else:
        priced = await mat_svc.get_priced(region_id=user.region_id)
    if not priced:
        await message.answer(t("no_priced_requests", lang))
        return
    await message.answer(
        t("priced_requests_list", lang, count=len(priced)),
        reply_markup=get_priced_requests_keyboard(priced),
    )


@router.callback_query(F.data.startswith("zavod_deliver:"))
async def zavod_deliver(callback: CallbackQuery, user: User, session, lang: str) -> None:
    req_id = int(callback.data.split(":")[1])
    mat_svc = MaterialService(session)
    req = await mat_svc.deliver(req_id)
    if not req:
        await callback.answer(t("deliver_error", lang), show_alert=True)
        return

    req_full = await mat_svc.get_by_id(req_id)

    # Notify usta
    from app.bot.loader import bot
    if req_full and req_full.usta:
        try:
            ul = _gl(req_full.usta)
            await bot.send_message(
                req_full.usta.telegram_id,
                t("material_delivered_notify", ul, amount=req.amount_tonnes),
            )
        except Exception:
            pass

    await callback.answer(t("delivered_marked", lang))
    await callback.message.edit_text(
        t("delivered_success", lang, amount=req.amount_tonnes)
    )


# ── Shofer Narxi (per-request delivery price) ────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_shofer_narxi", set())))
async def shofer_narxi_start(message: Message, user: User, session, state: FSMContext, lang: str) -> None:
    """Step 1: show active material requests so user picks which project to price."""
    if not user.zavod_id:
        await message.answer(t("shofer_narxi_no_zavod", lang))
        return

    mat_svc = MaterialService(session)
    requests = await mat_svc.get_priced_for_zavod(user.zavod_id)
    if not requests:
        requests = await mat_svc.get_pending_for_zavod(user.zavod_id)

    if not requests:
        await message.answer(t("shofer_narxi_no_requests", lang))
        return

    await state.set_state(ZavodShoferNarxiStates.selecting_request)
    await message.answer(
        t("shofer_narxi_select_request", lang, count=len(requests)),
        reply_markup=get_shofer_narxi_requests_keyboard(requests, lang),
    )


@router.callback_query(ZavodShoferNarxiStates.selecting_request, F.data.startswith("shofer_req:"))
async def shofer_narxi_request_selected(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    """Step 2: user selected a request — ask for the driver price."""
    req_id = int(callback.data.split(":")[1])
    mat_svc = MaterialService(session)
    req = await mat_svc.get_by_id(req_id)

    if not req:
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    order_num = req.order.order_number if req.order else f"#{req.order_id}"
    usta_name = (req.usta.full_name or req.usta.phone) if req.usta else "?"
    current = f"{float(req.delivery_price):,.0f} so'm" if req.delivery_price else t("shofer_narxi_not_set", lang)

    await state.update_data(req_id=req_id, order_num=order_num, usta_name=usta_name)
    await state.set_state(ZavodShoferNarxiStates.entering_price)

    await callback.message.edit_text(
        t("shofer_narxi_current_req", lang,
          order=order_num, usta=usta_name, price=current),
    )
    await callback.answer()


@router.message(ZavodShoferNarxiStates.entering_price)
async def shofer_narxi_enter(message: Message, state: FSMContext, lang: str) -> None:
    """Step 3: receive price, ask for confirmation."""
    raw = (message.text or "").strip().replace(" ", "").replace(",", "").replace("'", "")
    try:
        from decimal import Decimal, InvalidOperation
        price = Decimal(raw)
        if price < 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer(t("shofer_narxi_invalid", lang))
        return

    data = await state.get_data()
    await state.update_data(price=str(price))
    await state.set_state(ZavodShoferNarxiStates.confirming)

    order_num = data.get("order_num", "?")
    usta_name = data.get("usta_name", "?")

    await message.answer(
        t("shofer_narxi_confirm_req", lang,
          order=order_num, usta=usta_name, price=f"{float(price):,.0f}"),
        reply_markup=get_shofer_narxi_confirm_keyboard(lang),
    )


@router.callback_query(ZavodShoferNarxiStates.confirming, F.data == "shofer_narxi_save")
async def shofer_narxi_save(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    """Step 4: save delivery_price to the specific MaterialRequest."""
    from decimal import Decimal
    from sqlalchemy import select

    data = await state.get_data()
    req_id = data.get("req_id")
    price_str = data.get("price")

    if not req_id or not price_str:
        await state.clear()
        await callback.answer(t("error_occurred", lang), show_alert=True)
        return

    req = (await session.execute(
        select(MaterialRequest).where(MaterialRequest.id == req_id)
    )).scalar_one_or_none()

    if not req:
        await state.clear()
        await callback.answer(t("not_found", lang), show_alert=True)
        return

    req.delivery_price = Decimal(price_str)
    await session.commit()
    await state.clear()

    order_num = data.get("order_num", f"#{req_id}")
    await callback.message.edit_text(
        t("shofer_narxi_saved_req", lang,
          order=order_num, price=f"{float(req.delivery_price):,.0f}")
    )
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.ZAVOD, lang))
    await callback.answer()


@router.callback_query(F.data == "shofer_narxi_cancel")
async def shofer_narxi_cancel(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    """Cancel at any step."""
    await state.clear()
    await callback.message.edit_text(t("shofer_narxi_cancelled", lang))
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.ZAVOD, lang))
    await callback.answer()


# ── Payment confirmation flow ───────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_zavod_payments", set())))
async def zavod_payments_list(message: Message, user: User, session, lang: str) -> None:
    from sqlalchemy import select as _select
    from app.db.models import PaymentTransfer, Order, User as _User

    result = await session.execute(
        _select(PaymentTransfer).where(
            PaymentTransfer.status == "usta_submitted"
        ).order_by(PaymentTransfer.usta_submitted_at.desc())
    )
    transfers = result.scalars().all()

    if not transfers:
        await message.answer("✅ Tasdiqlash kutayotgan to'lov yo'q.")
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for tr in transfers:
        order_result = await session.execute(
            _select(Order).where(Order.id == tr.order_id)
        )
        order = order_result.scalar_one_or_none()
        order_num = order.order_number if order else f"#{tr.order_id}"
        buttons.append([InlineKeyboardButton(
            text=f"💸 {order_num} — {float(tr.usta_sent):,.0f} so'm",
            callback_data=f"zavod_confirm_payment:{tr.id}",
        )])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        f"💸 <b>Tasdiqlash kutayotgan to'lovlar ({len(transfers)} ta):</b>\n\n"
        f"<i>Tasdiqlash uchun bosing:</i>",
        reply_markup=kb,
    )

@router.callback_query(F.data.startswith("zavod_confirm_payment:"))
async def zavod_confirm_payment_start(
    callback: CallbackQuery, user: User, session, state: FSMContext, lang: str
) -> None:
    transfer_id = int(callback.data.split(":")[1])
    payment_svc = PaymentTransferService(session)
    transfer = await payment_svc.get_by_id(transfer_id)

    if not transfer:
        await callback.answer("To'lov topilmadi", show_alert=True)
        return
    if transfer.status == "zavod_confirmed":
        await callback.answer("✅ Allaqachon tasdiqlangan", show_alert=True)
        return

    await state.update_data(transfer_id=transfer_id)
    await state.set_state(ZavodPaymentStates.entering_received)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text=f"✅ To'liq qabul ({float(transfer.usta_sent):,.0f} so'm)",
            callback_data=f"zavod_payment_full:{transfer_id}",
        )
    ]])

    await callback.message.edit_text(
        f"💸 <b>Shofyordan qabul qilingan summani tasdiqlang</b>\n\n"
        f"🏭 Usta yuborgan: <b>{float(transfer.usta_sent):,.0f} so'm</b>\n\n"
        f"Nechta pul qabul qildingiz?\n"
        f"<i>To'liq summani tasdiqlash uchun pastdagi tugmani bosing,\n"
        f"yoki boshqa miqdor kiriting:</i>",
        reply_markup=kb,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("zavod_payment_full:"))
async def zavod_payment_full(
    callback: CallbackQuery, user: User, session, state: FSMContext, lang: str
) -> None:
    transfer_id = int(callback.data.split(":")[1])
    payment_svc = PaymentTransferService(session)
    transfer = await payment_svc.get_by_id(transfer_id)
    if not transfer:
        await callback.answer("Topilmadi", show_alert=True)
        return

    received = transfer.usta_sent
    await _finalize_zavod_payment(callback, session, transfer, received, user)
    await state.clear()


@router.message(ZavodPaymentStates.entering_received)
async def zavod_payment_received(
    message: Message, user: User, session, state: FSMContext, lang: str
) -> None:
    raw = message.text.strip().replace(",", "").replace(" ", "").replace("_", "")
    try:
        received = Decimal(raw)
        if received <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Noto'g'ri miqdor. Raqam kiriting:")
        return

    data = await state.get_data()
    transfer_id = data["transfer_id"]
    payment_svc = PaymentTransferService(session)
    transfer = await payment_svc.get_by_id(transfer_id)
    if not transfer:
        await message.answer("❌ To'lov topilmadi")
        await state.clear()
        return

    await state.clear()
    await _finalize_zavod_payment(message, session, transfer, received, user)


async def _finalize_zavod_payment(event, session, transfer, received: Decimal, zavod_user) -> None:
    from app.bot.loader import bot as _bot
    from sqlalchemy import select as _select
    from app.db.models import User as _User

    payment_svc = PaymentTransferService(session)
    transfer = await payment_svc.confirm_by_zavod(
        transfer_id=transfer.id,
        zavod_user_id=zavod_user.id,
        received=received,
    )

    diff = float(received) - float(transfer.usta_sent)
    diff_text = ""
    if diff > 0:
        diff_text = f"\n➕ Farq: +{diff:,.0f} so'm"
    elif diff < 0:
        diff_text = f"\n➖ Farq: {diff:,.0f} so'm"

    confirm_text = (
        f"✅ <b>To'lov tasdiqlandi!</b>\n\n"
        f"💰 Qabul qilindi: <b>{float(received):,.0f} so'm</b>{diff_text}\n"
        f"🏭 Kutilgan: {float(transfer.usta_sent):,.0f} so'm\n\n"
        f"Usta va Adminga bildirishnoma yuborildi."
    )

    if hasattr(event, "message"):
        await event.message.edit_text(confirm_text)
        await event.answer("✅ Tasdiqlandi")
    else:
        await event.answer(confirm_text)

    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(transfer.order_id)
    if not order:
        return

    usta_text = (
        f"✅ <b>Zavod to'lovni tasdiqladi!</b>\n\n"
        f"📋 {order.order_number}\n"
        f"🏭 Zavod qabul qildi: <b>{float(received):,.0f} so'm</b>\n\n"
        f"Endi <b>✅ Ishni tugatish</b> tugmasini bosa olasiz."
    )
    if order.usta and order.usta.telegram_id:
        try:
            await _bot.send_message(order.usta.telegram_id, usta_text)
        except Exception:
            pass

    from app.services.expense_service import ExpenseService, EXPENSE_LABELS
    expense_svc = ExpenseService(session)
    expenses = await expense_svc.get_by_order(order.id)
    total_expenses = sum(float(e.amount) for e in expenses)
    expenses_detail = ""
    if expenses:
        lines = [f"  • {EXPENSE_LABELS.get(e.expense_type, e.expense_type)}: {float(e.amount):,.0f}" for e in expenses]
        expenses_detail = "\n" + "\n".join(lines)

    total = float(order.total_price or 0)
    advance = float(order.advance_paid or 0)
    usta_haqi = float(transfer.usta_wage_taken)
    master_kom = float(order.master_commission or 0)
    zavod_oldi = float(received)
    foyda = total - usta_haqi - master_kom - total_expenses - zavod_oldi

    master_name = order.master.full_name if order.master else "—"
    usta_name = order.usta.full_name if order.usta else "—"
    asphalt = order.asphalt_type.name if order.asphalt_type else "—"
    viloyat = order.viloyat.name if order.viloyat else "—"

    admin_text = (
        f"� <b>To'lov hisob-kitobi yakunlandi</b>\n\n"
        f"📋 <b>{order.order_number}</b>\n"
        f"� {order.address or '—'} ({viloyat})\n"
        f"🏗 Asfalt: {asphalt} | {float(order.area_m2 or 0):,.1f} m²\n\n"
        f"👥 <b>Ishtirokchilar:</b>\n"
        f"  👤 Klient: {order.client_name}\n"
        f"  👷 Usta: {usta_name}\n"
        f"  🧑‍💼 Master: {master_name}\n"
        f"  🏭 Zavod: {zavod_user.full_name or '—'}\n\n"
        f"� <b>Moliyaviy hisobot:</b>\n"
        f"  �💰 Klient jami: {total:,.0f} so'm\n"
        f"  ✅ Avans: {advance:,.0f} so'm\n"
        f"  💵 Klientdan olingan: {float(transfer.usta_collected):,.0f} so'm\n\n"
        f"  🔧 Usta haqi: {usta_haqi:,.0f} so'm\n"
        f"  🧑‍💼 Master komissiya: {master_kom:,.0f} so'm\n"
        f"  🏭 Zavodga ketdi: {zavod_oldi:,.0f} so'm\n"
        f"  📦 Qo'shimcha harajatlar: {total_expenses:,.0f} so'm{expenses_detail}\n\n"
        f"  � <b>Umumiy foyda: {foyda:,.0f} so'm</b>"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    close_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🔒 Zakazni yopish (DONE)",
            callback_data=f"admin_close_order:{order.id}",
        )
    ]])

    result = await session.execute(
        _select(_User).where(
            _User.role.in_(["admin", "super_admin"]),
            _User.is_active.is_(True),
        )
    )
    for admin in result.scalars().all():
        if admin.telegram_id:
            try:
                await _bot.send_message(admin.telegram_id, admin_text, reply_markup=close_kb)
            except Exception:
                pass
