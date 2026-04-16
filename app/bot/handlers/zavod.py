from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters import RoleFilter
from app.bot.i18n import t, ALL_BUTTON_TEXTS
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
    order_num = req.order.order_number if req.order else "?"
    usta_name = req.usta.full_name or str(req.usta.telegram_id) if req.usta else "?"
    await callback.message.edit_text(
        t("material_request_detail", lang,
          id=req.id,
          order=order_num,
          usta=usta_name,
          amount=req.amount_tonnes,
          notes=req.notes or '—',
          date=req.created_at.strftime('%d.%m.%Y %H:%M')),
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
