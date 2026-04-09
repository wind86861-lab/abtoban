from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters import RoleFilter
from app.bot.keyboards.finance import (
    get_pending_requests_keyboard,
    get_priced_requests_keyboard,
    get_zavod_confirm_keyboard,
    get_zavod_request_detail_keyboard,
)
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu
from app.bot.states.finance import ZavodPriceStates
from app.db.models import User, UserRole
from app.services.material_service import MaterialService
from app.services.user_service import UserService

router = Router()
router.message.filter(RoleFilter(UserRole.ZAVOD))


# ── Pending requests ───────────────────────────────────────────────────────────

@router.message(F.text.in_({"\ud83d\udce6 Material so'rovlar", "\u2705 Narx kiritish"}))
async def material_requests(message: Message, session) -> None:
    mat_svc = MaterialService(session)
    pending = await mat_svc.get_pending()
    if not pending:
        await message.answer(
            "\ud83d\udce6 <b>Kelgan so'rovlar</b>\n\nHozircha yangi so'rov yo'q."
        )
        return
    await message.answer(
        f"\ud83d\udce6 <b>Kelgan so'rovlar</b> ({len(pending)} ta)\n\nTanlang:",
        reply_markup=get_pending_requests_keyboard(pending),
    )


@router.callback_query(F.data == "zavod_pending_list")
async def zavod_pending_list(callback: CallbackQuery, session) -> None:
    mat_svc = MaterialService(session)
    pending = await mat_svc.get_pending()
    if not pending:
        await callback.message.edit_text("\ud83d\udce6 Yangi so'rov yo'q.")
    else:
        await callback.message.edit_text(
            f"\ud83d\udce6 <b>Kelgan so'rovlar</b> ({len(pending)} ta):",
            reply_markup=get_pending_requests_keyboard(pending),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("zavod_view_req:"))
async def view_request(callback: CallbackQuery, session) -> None:
    req_id = int(callback.data.split(":")[1])
    mat_svc = MaterialService(session)
    req = await mat_svc.get_by_id(req_id)
    if not req:
        await callback.answer("\u274c So'rov topilmadi", show_alert=True)
        return
    order_num = req.order.order_number if req.order else "?"
    usta_name = req.usta.full_name or str(req.usta.telegram_id) if req.usta else "?"
    await callback.message.edit_text(
        f"\ud83d\udce6 <b>Material so'rov #{req.id}</b>\n\n"
        f"\ud83d\udd22 Zakaz: {order_num}\n"
        f"\ud83d\udc77 Usta: {usta_name}\n"
        f"\ud83d\udce6 Miqdor: <b>{req.amount_tonnes} tonna</b>\n"
        f"\ud83d\udcdd Izoh: {req.notes or '\u2014'}\n"
        f"\ud83d\udcc5 Sana: {req.created_at.strftime('%d.%m.%Y %H:%M')}",
        reply_markup=get_zavod_request_detail_keyboard(req_id),
    )
    await callback.answer()


# ── Price setting FSM ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("zavod_price:"))
async def start_price_fsm(callback: CallbackQuery, state: FSMContext) -> None:
    req_id = int(callback.data.split(":")[1])
    await state.update_data(req_id=req_id)
    await state.set_state(ZavodPriceStates.entering_material_price)
    await callback.message.edit_text(
        "1/3 \u2014 Material narxini kiriting (so'm):\nMisol: <code>8500000</code>"
    )
    await callback.answer()


@router.message(ZavodPriceStates.entering_material_price)
async def price_material(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip().replace(" ", "").replace(",", "")
    try:
        price = Decimal(raw)
        if price <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("\u274c Noto'g'ri narx. Raqam kiriting:")
        return
    await state.update_data(material_price=str(price))
    await state.set_state(ZavodPriceStates.entering_delivery_price)
    await message.answer(
        "2/3 \u2014 Dostavka narxini kiriting (so'm):\nMisol: <code>500000</code>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(ZavodPriceStates.entering_delivery_price)
async def price_delivery(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip().replace(" ", "").replace(",", "")
    try:
        price = Decimal(raw)
        if price < 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("\u274c Noto'g'ri narx. Raqam kiriting (0 bo'lishi mumkin):")
        return
    await state.update_data(delivery_price=str(price))
    await state.set_state(ZavodPriceStates.entering_extra_cost)
    await message.answer(
        "3/3 \u2014 Qo'shimcha xarajat (so'm). Yo'q bo'lsa 0 kiriting:",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(ZavodPriceStates.entering_extra_cost)
async def price_extra(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip().replace(" ", "").replace(",", "")
    try:
        extra = Decimal(raw)
        if extra < 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("\u274c Noto'g'ri. Raqam kiriting (0 bo'lishi mumkin):")
        return
    await state.update_data(extra_cost=str(extra))
    await state.set_state(ZavodPriceStates.confirming)
    data = await state.get_data()
    mat_price = float(Decimal(data["material_price"]))
    del_price = float(Decimal(data["delivery_price"]))
    total = mat_price + del_price + float(extra)
    await message.answer(
        f"\ud83d\udcb0 <b>Narx xulosasi</b>\n\n"
        f"\ud83c\udfd7 Material: <b>{mat_price:,.0f} so'm</b>\n"
        f"\ud83d\ude9a Dostavka: <b>{del_price:,.0f} so'm</b>\n"
        f"\u2795 Qo'shimcha: <b>{float(extra):,.0f} so'm</b>\n"
        f"\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n"
        f"\ud83d\udcb0 Jami: <b>{total:,.0f} so'm</b>\n\n"
        f"Tasdiqlaysizmi?",
        reply_markup=get_zavod_confirm_keyboard(),
    )


@router.callback_query(ZavodPriceStates.confirming, F.data == "zavod_price_confirm")
async def price_submit(callback: CallbackQuery, state: FSMContext, user: User, session) -> None:
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
        await callback.message.edit_text(
            "\u274c Xatolik: so'rov allaqachon narxlangan yoki topilmadi."
        )
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
            await bot.send_message(
                req_full.usta.telegram_id,
                f"\ud83d\udcb0 <b>Material narxi belgilandi!</b>\n\n"
                f"\ud83d\udce6 {req.amount_tonnes} tonna\n"
                f"\ud83c\udfd7 Material: {float(req.material_price or 0):,.0f} so'm\n"
                f"\ud83d\ude9a Dostavka: {float(req.delivery_price or 0):,.0f} so'm\n"
                f"\u2795 Qo'shimcha: {float(req.extra_cost or 0):,.0f} so'm\n"
                f"\ud83d\udcb0 Jami: {total:,.0f} so'm\n\n"
                f"Yetkazib berish tashkil etilmoqda.",
            )
        except Exception:
            pass

    # Notify shofers
    shofers = await user_svc.get_all(role=UserRole.SHOFER)
    from app.bot.keyboards.finance import get_shofer_delivery_keyboard
    for shofer in shofers:
        try:
            await bot.send_message(
                shofer.telegram_id,
                f"\ud83d\ude9a <b>Yetkazish topshirig'i!</b>\n\n"
                f"\ud83d\udce6 {req.amount_tonnes} tonna material\n"
                f"\ud83d\udcdd Zakaz: {req_full.order.order_number if req_full and req_full.order else '?'}\n\n"
                f"Yetkazib berdingizmi?",
                reply_markup=get_shofer_delivery_keyboard(req.id),
            )
        except Exception:
            pass

    await callback.message.edit_text(
        f"\u2705 <b>Narx belgilandi!</b>\n\n"
        f"\ud83d\udce6 {req.amount_tonnes} tonna \u2014 {total:,.0f} so'm\n"
        f"Usta va shoferlar xabardor qilindi."
    )
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(UserRole.ZAVOD))
    await callback.answer()


@router.callback_query(ZavodPriceStates.confirming, F.data == "zavod_price_cancel")
async def price_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("\u274c Bekor qilindi.")
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(UserRole.ZAVOD))
    await callback.answer()


# ── Delivery confirm (by zavod) ────────────────────────────────────────────────

@router.message(F.text == "\ud83d\udccb Tarixi")
async def history(message: Message, session) -> None:
    mat_svc = MaterialService(session)
    priced = await mat_svc.get_priced()
    if not priced:
        await message.answer("\ud83d\udccb Yetkazish kutilayotgan so'rovlar yo'q.")
        return
    await message.answer(
        f"\ud83d\ude9a <b>Yetkazish kutilayotganlar</b> ({len(priced)} ta):",
        reply_markup=get_priced_requests_keyboard(priced),
    )


@router.callback_query(F.data.startswith("zavod_deliver:"))
async def zavod_deliver(callback: CallbackQuery, user: User, session) -> None:
    req_id = int(callback.data.split(":")[1])
    mat_svc = MaterialService(session)
    req = await mat_svc.deliver(req_id)
    if not req:
        await callback.answer(
            "\u274c So'rov topilmadi yoki allaqachon yetkazilgan.", show_alert=True
        )
        return

    req_full = await mat_svc.get_by_id(req_id)

    # Notify usta
    from app.bot.loader import bot
    if req_full and req_full.usta:
        try:
            await bot.send_message(
                req_full.usta.telegram_id,
                f"\ud83d\udce6 <b>Material yetkazildi!</b>\n\n"
                f"\ud83d\udce6 {req.amount_tonnes} tonna\n"
                f"Ish boshlashingiz mumkin!",
            )
        except Exception:
            pass

    await callback.answer("\u2705 Yetkazildi deb belgilandi!")
    await callback.message.edit_text(
        f"\u2705 <b>Yetkazildi!</b>\n\n"
        f"\ud83d\udce6 {req.amount_tonnes} tonna\n"
        f"Usta xabardor qilindi."
    )
