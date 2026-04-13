from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters import RoleFilter
from app.bot.i18n import t, ALL_BUTTON_TEXTS
from app.bot.keyboards.finance import (
    get_active_orders_for_material_keyboard,
    get_material_confirm_keyboard,
    get_skip_notes_keyboard,
)
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu
from app.bot.keyboards.usta import get_usta_notification_keyboard, get_usta_order_detail_keyboard
from app.bot.states.finance import MaterialRequestStates
from app.db.models import ORDER_STATUS_LABELS, OrderStatus, User, UserRole
from app.services.material_service import MaterialService
from app.services.order_service import OrderService
from app.services.usta_service import UstaService

router = Router()
router.message.filter(RoleFilter(UserRole.USTA))


# ── My orders ─────────────────────────────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_usta_my_orders", set())))
async def my_orders(message: Message, user: User, session, lang: str) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_usta(user.id)

    if not orders:
        await message.answer(t("usta_no_orders", lang))
        return

    lines = [t("usta_orders_list", lang, count=len(orders))]
    for o in orders:
        status_label = ORDER_STATUS_LABELS.get(o.status, o.status.value)
        asphalt = o.asphalt_type.name if o.asphalt_type else "—"
        wage = f"{float(o.usta_wage):,.0f}" if o.usta_wage else "—"
        lines.append(
            f"\n🔢 <code>{o.order_number}</code> — {status_label}\n"
            f"  📍 {o.address or '—'}\n"
            f"  📐 {o.area_m2 or '?'} m²  🏗 {asphalt}\n"
            f"  💰 {wage}"
        )
    await message.answer("\n".join(lines))


@router.callback_query(F.data == "usta_my_orders")
async def usta_my_orders_cb(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_usta(user.id)
    if not orders:
        await callback.message.edit_text(t("usta_no_orders", lang))
    else:
        lines = [t("usta_orders_list", lang, count=len(orders))]
        for o in orders:
            st = ORDER_STATUS_LABELS.get(o.status, o.status.value)
            lines.append(f"• <code>{o.order_number}</code> — {st}")
        await callback.message.edit_text("\n".join(lines))
    await callback.answer()


# ── Accept assignment ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("accept_assignment:"))
async def accept_assignment(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)

    if not order:
        await callback.answer(t("order_not_found", lang), show_alert=True)
        return
    if order.usta_id != user.id:
        await callback.answer(t("assignment_not_yours", lang), show_alert=True)
        return

    asphalt = order.asphalt_type.name if order.asphalt_type else "—"
    wage = float(order.usta_wage) if order.usta_wage else 0
    work_date = order.work_date.strftime("%d.%m.%Y") if order.work_date else "—"

    await callback.message.edit_text(
        t("usta_accepted", lang,
          number=order.order_number,
          address=order.address or "—",
          area=order.area_m2,
          asphalt=asphalt,
          date=work_date,
          wage=f"{wage:,.0f}"),
        reply_markup=get_usta_order_detail_keyboard(order_id),
    )
    await callback.message.answer(
        t("main_menu", lang), reply_markup=get_main_menu(UserRole.USTA, lang)
    )
    await callback.answer()

    # Notify master
    from app.bot.loader import bot as _bot
    from app.bot.i18n import get_lang as _gl
    if order.master:
        try:
            ml = _gl(order.master)
            await _bot.send_message(
                order.master.telegram_id,
                t("usta_accepted_notify", ml,
                  number=order.order_number,
                  usta=user.full_name or str(user.telegram_id)),
            )
        except Exception:
            pass


# ── Decline assignment ────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("decline_assignment:"))
async def decline_assignment(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    usta_svc = UstaService(session)
    order = await usta_svc.release_usta(order_id, user.id)

    if not order:
        await callback.answer(t("order_not_found", lang), show_alert=True)
        return

    await callback.message.edit_text(t("usta_declined", lang))
    await callback.message.answer(
        t("main_menu", lang), reply_markup=get_main_menu(UserRole.USTA, lang)
    )
    await callback.answer()

    # Notify master to re-assign
    from app.bot.loader import bot as _bot
    from app.bot.i18n import get_lang as _gl
    from app.services.order_service import OrderService as OS
    order_full = await OS(session).get_by_id_full(order_id)
    if order_full and order_full.master:
        try:
            ml = _gl(order_full.master)
            await _bot.send_message(
                order_full.master.telegram_id,
                t("usta_declined_notify", ml,
                  number=order_full.order_number,
                  usta=user.full_name or str(user.telegram_id)),
            )
        except Exception:
            pass


# ── Material request FSM ──────────────────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_request_material", set())))
async def material_request_start(message: Message, state: FSMContext, user: User, session, lang: str) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_usta(user.id, status=None)
    active = [o for o in orders if o.status in (OrderStatus.CONFIRMED, OrderStatus.IN_WORK)]
    if not active:
        await message.answer(t("material_no_active", lang))
        return
    await state.set_state(MaterialRequestStates.selecting_order)
    await message.answer(
        t("material_start", lang),
        reply_markup=get_active_orders_for_material_keyboard(active),
    )


@router.callback_query(MaterialRequestStates.selecting_order, F.data.startswith("material_pick_order:"))
async def material_pick_order(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(MaterialRequestStates.entering_tonnes)
    await callback.message.edit_text(t("material_enter_tonnes", lang))
    await callback.answer()


@router.message(MaterialRequestStates.entering_tonnes)
async def material_enter_tonnes(message: Message, state: FSMContext, lang: str) -> None:
    raw = (message.text or "").strip().replace(",", ".")
    try:
        tonnes = Decimal(raw)
        if tonnes <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer(t("material_invalid_tonnes", lang))
        return
    await state.update_data(amount_tonnes=str(tonnes))
    await state.set_state(MaterialRequestStates.entering_notes)
    await message.answer(
        t("material_enter_notes", lang),
        reply_markup=get_skip_notes_keyboard(),
    )


@router.message(MaterialRequestStates.entering_notes)
async def material_enter_notes(message: Message, state: FSMContext, lang: str) -> None:
    text = message.text or ""
    notes = None if text.startswith("⏩") else text.strip()
    await state.update_data(notes=notes)
    await state.set_state(MaterialRequestStates.confirming)
    data = await state.get_data()
    await message.answer(
        t("material_summary", lang, tonnes=data['amount_tonnes'], notes=notes or '—'),
        reply_markup=get_material_confirm_keyboard(),
    )


@router.callback_query(MaterialRequestStates.confirming, F.data == "material_confirm")
async def material_submit(callback: CallbackQuery, state: FSMContext, user: User, session, lang: str) -> None:
    data = await state.get_data()
    await state.clear()

    mat_svc = MaterialService(session)
    req = await mat_svc.create(
        order_id=data["order_id"],
        usta_id=user.id,
        amount_tonnes=Decimal(data["amount_tonnes"]),
        notes=data.get("notes"),
    )

    # Notify admins — region-filtered: SUPER_ADMIN always, ADMIN only if same region
    from app.bot.loader import bot
    from app.bot.i18n import get_lang as _gl
    from app.services.user_service import UserService
    user_svc = UserService(session)
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(data["order_id"])

    region_name = order.region.name if order and order.region else "—"
    order_region_id = order.region_id if order else None

    super_admins = await user_svc.get_all(role=UserRole.SUPER_ADMIN)
    if order_region_id:
        region_admins = await user_svc.get_by_role_and_region(UserRole.ADMIN, order_region_id)
        region_admins += await user_svc.get_by_role_and_region(UserRole.HELPER_ADMIN, order_region_id)
        if not region_admins:
            # fallback: all admins if no one assigned to this region
            region_admins = await user_svc.get_all(role=UserRole.ADMIN)
    else:
        region_admins = await user_svc.get_all(role=UserRole.ADMIN)

    notify_targets = {u.id: u for u in super_admins + region_admins}.values()

    for admin in notify_targets:
        try:
            al = _gl(admin)
            await bot.send_message(
                admin.telegram_id,
                t("material_new_notify", al,
                  id=req.id, region=region_name,
                  usta=user.full_name or str(user.telegram_id),
                  tonnes=req.amount_tonnes, notes=req.notes or "—"),
            )
        except Exception:
            pass

    await callback.message.edit_text(
        t("material_submitted", lang, tonnes=req.amount_tonnes)
    )
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.USTA, lang))
    await callback.answer()


@router.callback_query(MaterialRequestStates.confirming, F.data == "material_cancel")
async def material_cancel(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await callback.message.edit_text(t("material_cancelled", lang))
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.USTA, lang))
    await callback.answer()


@router.callback_query(F.data.startswith("request_material:"))
async def request_material_cb(callback: CallbackQuery, state: FSMContext, user: User, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(MaterialRequestStates.entering_tonnes)
    await callback.message.edit_text(t("material_enter_tonnes", lang))
    await callback.answer()


# ── Work history ─────────────────────────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_work_history", set())))
async def work_history(message: Message, user: User, session, lang: str) -> None:
    order_svc = OrderService(session)
    from app.db.models import OrderStatus
    orders = await order_svc.get_by_usta(user.id, status=OrderStatus.DONE)
    if not orders:
        await message.answer(t("no_work_history", lang))
        return
    lines = [t("work_history_header", lang, count=len(orders))]
    for o in orders:
        date = o.completed_at.strftime("%d.%m.%Y") if o.completed_at else "—"
        wage = f"{float(o.usta_wage):,.0f}" if o.usta_wage else "—"
        lines.append(
            f"\n🔢 <code>{o.order_number}</code>\n"
            f"  📅 {date}  💰 {wage}"
        )
    await message.answer("\n".join(lines))
