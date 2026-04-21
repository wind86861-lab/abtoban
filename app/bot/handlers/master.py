from datetime import datetime
from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters import RoleFilter
from app.bot.i18n import t, ALL_BUTTON_TEXTS
from app.bot.i18n.core import location_link
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu, get_skip_keyboard
from app.bot.keyboards.order import (
    get_asphalt_keyboard,
    get_confirm_summary_keyboard,
    get_keep_address_keyboard,
    get_master_confirmed_order_keyboard,
    get_master_order_detail_keyboard,
    get_order_confirm_keyboard,
    get_orders_list_keyboard,
    get_regions_keyboard,
    get_tumanlar_keyboard,
    get_viloyatlar_keyboard,
)
from app.bot.keyboards.finance import (
    get_expense_type_keyboard,
    get_master_orders_for_expense_keyboard,
)
from app.bot.keyboards.usta import (
    get_usta_assignment_orders_keyboard,
    get_ustas_for_assignment_keyboard,
    get_ustas_for_reassignment_keyboard,
)
from app.bot.states.finance import ExpenseAddStates
from app.bot.states.order import MasterConfirmStates, MasterOrderCreateStates
from app.db.models import ORDER_STATUS_LABELS, OrderStatus, User, UserRole
from app.services.expense_service import EXPENSE_LABELS, ExpenseService
from app.services.asphalt_service import AsphaltService
from app.services.order_service import OrderService
from app.services.usta_service import UstaService
from app.services.user_service import UserService

router = Router()
router.message.filter(RoleFilter(UserRole.MASTER))


def _parse_decimal(raw: str) -> Decimal | None:
    cleaned = raw.strip().replace(" ", "").replace(",", ".")
    try:
        val = Decimal(cleaned)
        return val if val >= 0 else None
    except InvalidOperation:
        return None


def _parse_date(raw: str) -> datetime | None:
    for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw.strip(), fmt)
        except ValueError:
            continue
    return None


# ── New orders list ───────────────────────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_new_orders", set()) | ALL_BUTTON_TEXTS.get("btn_confirm_order", set())))
async def new_orders(message: Message, session, lang: str) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_new_orders()
    if not orders:
        await message.answer(t("no_new_orders", lang))
        return
    await message.answer(
        t("new_orders_list", lang, count=len(orders)),
        reply_markup=get_orders_list_keyboard(orders, prefix="master_view_new"),
    )


@router.callback_query(F.data.startswith("master_view_new:"))
async def view_new_order(callback: CallbackQuery, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await callback.answer(t("order_not_found", lang), show_alert=True)
        return
    asphalt = order.asphalt_type.name if order.asphalt_type else "—"
    loc = location_link(order.latitude, order.longitude)
    text = (
        f"📋 <b>{t('order', lang)}: {order.order_number}</b>\n\n"
        f"👤 {t('client', lang)}: <b>{order.client_name}</b>\n"
        f"📱 {t('phone', lang)}: <b>{order.client_phone}</b>\n"
        f"📍 {t('address', lang)}: <b>{order.address or '—'}</b>\n"
        f"{loc}"
        f"📐 {t('area', lang)}: <b>{order.area_m2 or '?'} m²</b>\n"
        f"🏗 {t('asphalt', lang)}: <b>{asphalt}</b>\n"
        f"📅 {t('created', lang)}: <b>{order.created_at.strftime('%d.%m.%Y %H:%M')}</b>\n\n"
        f"<i>{t('press_to_confirm', lang)}</i>"
    )
    await callback.message.edit_text(text, reply_markup=get_master_order_detail_keyboard(order_id))
    await callback.answer()


@router.callback_query(F.data == "back_new_orders")
async def back_to_new_orders(callback: CallbackQuery, session, lang: str) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_new_orders()
    if not orders:
        await callback.message.edit_text(t("no_new_orders", lang))
    else:
        await callback.message.edit_text(
            t("new_orders_list", lang, count=len(orders)),
            reply_markup=get_orders_list_keyboard(orders, prefix="master_view_new"),
        )
    await callback.answer()


# ── Master order creation ─────────────────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_add_order", set())))
async def master_create_order_start(message: Message, state: FSMContext, lang: str) -> None:
    await state.set_state(MasterOrderCreateStates.entering_client_phone)
    await message.answer(
        t("master_order_start", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(MasterOrderCreateStates.entering_client_phone)
async def master_order_client_phone(message: Message, state: FSMContext, lang: str) -> None:
    text = (message.text or "").strip()
    if text in ALL_BUTTON_TEXTS.get("btn_cancel", set()):
        await state.clear()
        await message.answer(t("action_cancelled", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
        return
    phone = text.replace("+", "").replace(" ", "").replace("-", "")
    if not phone.isdigit() or len(phone) < 9:
        await message.answer(t("invalid_phone", lang))
        return
    await state.update_data(client_phone=phone)
    await state.set_state(MasterOrderCreateStates.entering_client_name)
    await message.answer(
        t("enter_client_name", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(MasterOrderCreateStates.entering_client_name)
async def master_order_client_name(message: Message, state: FSMContext, session, lang: str) -> None:
    text = (message.text or "").strip()
    if text in ALL_BUTTON_TEXTS.get("btn_cancel", set()):
        await state.clear()
        await message.answer(t("action_cancelled", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
        return
    if len(text) < 2:
        await message.answer(t("name_too_short", lang))
        return
    await state.update_data(client_name=text)
    user_svc = UserService(session)
    viloyatlar = await user_svc.get_viloyatlar()
    if not viloyatlar:
        await message.answer(t("no_regions", lang))
        await state.clear()
        return
    await state.set_state(MasterOrderCreateStates.selecting_viloyat)
    await message.answer(
        t("select_region", lang),
        reply_markup=get_viloyatlar_keyboard(viloyatlar),
    )


@router.callback_query(MasterOrderCreateStates.selecting_viloyat, F.data.startswith("viloyat:"))
async def master_order_viloyat(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    try:
        viloyat_id = int(callback.data.split(":")[1])
        await state.update_data(viloyat_id=viloyat_id)
        user_svc = UserService(session)
        tumanlar = await user_svc.get_tumanlar(viloyat_id)
        if not tumanlar:
            await state.set_state(MasterOrderCreateStates.entering_street)
            await callback.message.edit_text(t("region_selected", lang))
            await callback.message.answer(
                t("enter_street", lang),
                reply_markup=get_cancel_keyboard(lang),
            )
        else:
            await state.set_state(MasterOrderCreateStates.selecting_tuman)
            await callback.message.edit_text(
                "✅ Viloyat tanlandi!\n\n🏘 Tumanni tanlang:",
                reply_markup=get_tumanlar_keyboard(tumanlar),
            )
        await callback.answer()
    except Exception as e:
        print(f"Error in master viloyat select: {e}")
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(MasterOrderCreateStates.selecting_tuman, F.data.startswith("tuman:"))
async def master_order_tuman(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    tuman_id = int(callback.data.split(":")[1])
    await state.update_data(tuman_id=tuman_id)
    await state.set_state(MasterOrderCreateStates.entering_street)
    await callback.message.edit_text(t("region_selected", lang))
    await callback.answer()


@router.message(MasterOrderCreateStates.entering_street)
async def master_order_street(message: Message, state: FSMContext, lang: str) -> None:
    text = (message.text or "").strip()
    if text in ALL_BUTTON_TEXTS.get("btn_cancel", set()):
        await state.clear()
        await message.answer(t("action_cancelled", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
        return
    if len(text) < 3:
        await message.answer(t("street_too_short", lang))
        return
    await state.update_data(street=text)
    await state.set_state(MasterOrderCreateStates.entering_target)
    await message.answer(
        t("enter_target", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(MasterOrderCreateStates.entering_target)
async def master_order_target(message: Message, state: FSMContext, lang: str) -> None:
    text = (message.text or "").strip()
    if text in ALL_BUTTON_TEXTS.get("btn_cancel", set()):
        await state.clear()
        await message.answer(t("action_cancelled", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
        return
    if len(text) < 3:
        await message.answer(t("target_too_short", lang))
        return
    data = await state.get_data()
    full_address = f"{data.get('district', '')}, {data.get('street', '')}, {text}"
    await state.update_data(address=full_address, target=text)
    await state.set_state(MasterOrderCreateStates.entering_area)
    await message.answer(
        t("enter_area", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(MasterOrderCreateStates.entering_area)
async def master_order_area(message: Message, state: FSMContext, session, lang: str) -> None:
    text = (message.text or "").strip()
    if text in ALL_BUTTON_TEXTS.get("btn_cancel", set()):
        await state.clear()
        await message.answer(t("action_cancelled", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
        return
    raw = text.replace(",", ".")
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
        await message.answer(t("no_asphalt_types", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
        await state.clear()
        return
    await state.set_state(MasterOrderCreateStates.selecting_asphalt)
    await message.answer(t("select_asphalt", lang), reply_markup=get_asphalt_keyboard(asphalt_types))


@router.callback_query(MasterOrderCreateStates.selecting_asphalt, F.data.startswith("asphalt:"))
async def master_order_asphalt(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    asphalt_id = int(callback.data.split(":")[1])
    asphalt_svc = AsphaltService(session)
    asphalt = await asphalt_svc.get_by_id(asphalt_id)
    if not asphalt:
        await callback.answer(t("asphalt_not_found", lang), show_alert=True)
        return
    data = await state.get_data()
    area = Decimal(data["area_m2"])
    estimated = area * asphalt.price_per_m2
    await state.update_data(asphalt_type_id=asphalt_id, asphalt_name=asphalt.name, estimated_price=str(estimated))
    await state.set_state(MasterOrderCreateStates.confirming)
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


@router.callback_query(MasterOrderCreateStates.confirming, F.data == "confirm_order")
async def master_order_submit(callback: CallbackQuery, state: FSMContext, user: User, session, lang: str) -> None:
    data = await state.get_data()
    await state.clear()
    order_svc = OrderService(session)
    order = await order_svc.create_by_master(
        master_id=user.id,
        client_name=data["client_name"],
        client_phone=data["client_phone"],
        address=data["address"],
        area_m2=Decimal(data["area_m2"]),
        region_id=data.get("region_id"),
        asphalt_type_id=data.get("asphalt_type_id"),
        viloyat_id=data.get("viloyat_id"),
        tuman_id=data.get("tuman_id"),
    )
    await callback.message.edit_text(
        t("master_order_created", lang,
          number=order.order_number,
          name=data['client_name'],
          address=data['address'],
          location_link=location_link(data.get('latitude'), data.get('longitude')),
          area=data['area_m2']),
    )
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
    await callback.answer()


@router.callback_query(MasterOrderCreateStates.confirming, F.data == "cancel_order")
async def master_order_cancel(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await callback.message.edit_text(t("order_cancelled", lang))
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
    await callback.answer()


# ── My (confirmed) orders ─────────────────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_master_my_orders", set())))
async def my_orders(message: Message, user: User, session, lang: str) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_master(user.id)
    if not orders:
        await message.answer(t("master_no_orders", lang))
        return
    await message.answer(
        t("master_orders_list", lang, count=len(orders)),
        reply_markup=get_orders_list_keyboard(orders, prefix="master_view_mine"),
    )


@router.callback_query(F.data.startswith("master_view_mine:"))
async def view_my_order(callback: CallbackQuery, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await callback.answer(t("order_not_found", lang), show_alert=True)
        return
    status_label = ORDER_STATUS_LABELS.get(order.status, order.status.value)
    asphalt = order.asphalt_type.name if order.asphalt_type else "—"
    usta_name = order.usta.full_name if order.usta else t("not_assigned", lang)
    loc = location_link(order.latitude, order.longitude)
    text = (
        f"📋 <b>{t('order', lang)}: {order.order_number}</b>\n\n"
        f"👤 {t('client', lang)}: <b>{order.client_name}</b> | {order.client_phone}\n"
        f"📍 {t('address', lang)}: <b>{order.address or '—'}</b>\n"
        f"{loc}"
        f"📐 {t('area', lang)}: <b>{order.area_m2 or '?'} m²</b>\n"
        f"🏗 {t('asphalt', lang)}: <b>{asphalt}</b>\n"
        f"💰 {t('total', lang)}: <b>{float(order.total_price):,.0f}</b>\n"
        f"💵 {t('advance', lang)}: <b>{float(order.advance_paid):,.0f}</b>\n"
        f"💳 {t('debt', lang)}: <b>{float(order.debt):,.0f}</b>\n"
        f"👷 {t('usta', lang)}: <b>{usta_name}</b>\n"
        f"📅 {t('status', lang)}: <b>{status_label}</b>"
    )
    await callback.message.edit_text(
        text, reply_markup=get_master_confirmed_order_keyboard(order_id)
    )
    await callback.answer()


@router.callback_query(F.data == "back_my_orders")
async def back_to_my_orders(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_master(user.id)
    if not orders:
        await callback.message.edit_text(t("master_no_orders", lang))
    else:
        await callback.message.edit_text(
            t("master_orders_list", lang, count=len(orders)),
            reply_markup=get_orders_list_keyboard(orders, prefix="master_view_mine"),
        )
    await callback.answer()


# ── Confirmation FSM (9 steps) ────────────────────────────────────────────────

@router.callback_query(F.data.startswith("start_confirm:"))
async def start_confirm_fsm(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id(order_id)

    if not order:
        await callback.answer(t("order_not_found", lang), show_alert=True)
        return
    from app.db.models import OrderStatus
    if order.status != OrderStatus.NEW:
        await callback.answer(t("already_confirmed", lang), show_alert=True)
        return

    await state.update_data(
        order_id=order_id,
        existing_address=order.address or "",
        order_number=order.order_number,
    )
    await state.set_state(MasterConfirmStates.entering_area)
    await callback.message.edit_text(
        t("confirm_step_area", lang, number=order.order_number)
    )
    await callback.answer()


@router.message(MasterConfirmStates.entering_area)
async def confirm_area(message: Message, state: FSMContext, lang: str) -> None:
    val = _parse_decimal(message.text or "")
    if val is None or val <= 0:
        await message.answer(t("invalid_area", lang))
        return
    await state.update_data(area_m2=str(val))
    await state.set_state(MasterConfirmStates.entering_sum)
    await message.answer(
        t("confirm_step_sum", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(MasterConfirmStates.entering_sum)
async def confirm_sum(message: Message, state: FSMContext, lang: str) -> None:
    val = _parse_decimal(message.text or "")
    if val is None or val <= 0:
        await message.answer(t("invalid_sum", lang))
        return
    await state.update_data(total_price=str(val))
    await state.set_state(MasterConfirmStates.entering_advance)
    await message.answer(
        t("confirm_step_advance", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(MasterConfirmStates.entering_advance)
async def confirm_advance(message: Message, state: FSMContext, lang: str) -> None:
    val = _parse_decimal(message.text or "")
    if val is None:
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(advance_paid=str(val))
    data = await state.get_data()
    await state.set_state(MasterConfirmStates.entering_address)
    existing = data.get("existing_address", "")
    await message.answer(
        t("confirm_step_address", lang, address=existing or '—'),
        reply_markup=get_keep_address_keyboard(existing) if existing else get_cancel_keyboard(lang),
    )


@router.message(MasterConfirmStates.entering_address)
async def confirm_address(message: Message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    existing = data.get("existing_address", "")
    text = message.text or ""
    if text.startswith("📍 Saqlash:") or text.startswith(f"📍 Saqlash: {existing[:40]}"):
        address = existing
    else:
        address = text.strip()
        if len(address) < 5:
            await message.answer(t("address_too_short", lang))
            return
    await state.update_data(address=address)
    await state.set_state(MasterConfirmStates.entering_date)
    await message.answer(
        t("confirm_step_date", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(MasterConfirmStates.entering_date)
async def confirm_date(message: Message, state: FSMContext, lang: str) -> None:
    dt = _parse_date(message.text or "")
    if dt is None:
        await message.answer(t("invalid_date", lang))
        return
    await state.update_data(work_date=dt.isoformat())
    await state.set_state(MasterConfirmStates.entering_usta_wage)
    await message.answer(
        t("confirm_step_usta_wage", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(MasterConfirmStates.entering_usta_wage)
async def confirm_usta_wage(message: Message, state: FSMContext, lang: str) -> None:
    val = _parse_decimal(message.text or "")
    if val is None:
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(usta_wage=str(val))
    await state.set_state(MasterConfirmStates.entering_commission)
    await message.answer(
        t("confirm_step_commission", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(MasterConfirmStates.entering_commission)
async def confirm_commission(message: Message, state: FSMContext, lang: str) -> None:
    val = _parse_decimal(message.text or "")
    if val is None:
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(master_commission=str(val))
    await state.set_state(MasterConfirmStates.entering_notes)
    await message.answer(
        t("confirm_step_notes", lang),
        reply_markup=get_skip_keyboard(lang),
    )


@router.message(MasterConfirmStates.entering_notes)
async def confirm_notes(message: Message, state: FSMContext, lang: str) -> None:
    text = message.text or ""
    notes = None if text.startswith("⏩") else text.strip()
    await state.update_data(notes=notes)
    await state.set_state(MasterConfirmStates.confirming)

    data = await state.get_data()
    work_date = datetime.fromisoformat(data["work_date"]).strftime("%d.%m.%Y")
    debt = max(Decimal("0"), Decimal(data["total_price"]) - Decimal(data["advance_paid"]))

    await message.answer(
        t("confirm_summary", lang,
          number=data['order_number'],
          area=data['area_m2'],
          total=f"{float(Decimal(data['total_price'])):,.0f}",
          advance=f"{float(Decimal(data['advance_paid'])):,.0f}",
          debt=f"{float(debt):,.0f}",
          address=data['address'],
          date=work_date,
          wage=f"{float(Decimal(data['usta_wage'])):,.0f}",
          commission=f"{float(Decimal(data['master_commission'])):,.0f}",
          notes=data.get('notes') or '—'),
        reply_markup=get_confirm_summary_keyboard(),
    )


@router.callback_query(MasterConfirmStates.confirming, F.data == "submit_confirm")
async def submit_confirmation(callback: CallbackQuery, state: FSMContext, user: User, session, lang: str) -> None:
    data = await state.get_data()
    await state.clear()

    order_svc = OrderService(session)
    order = await order_svc.confirm(
        order_id=data["order_id"],
        master_id=user.id,
        area_m2=Decimal(data["area_m2"]),
        total_price=Decimal(data["total_price"]),
        advance_paid=Decimal(data["advance_paid"]),
        address=data["address"],
        work_date=datetime.fromisoformat(data["work_date"]),
        usta_wage=Decimal(data["usta_wage"]),
        master_commission=Decimal(data["master_commission"]),
        notes=data.get("notes"),
    )

    if not order:
        await callback.message.edit_text(t("confirm_error", lang))
        await callback.answer()
        return

    # Notify admins
    from app.bot.loader import bot
    from app.bot.i18n import get_lang as _gl
    user_svc = UserService(session)
    admins = await user_svc.get_all(role=UserRole.ADMIN)
    super_admins = await user_svc.get_all(role=UserRole.SUPER_ADMIN)
    for admin in admins + super_admins:
        try:
            al = _gl(admin)
            await bot.send_message(
                admin.telegram_id,
                t("order_confirmed_notify", al,
                  number=order.order_number,
                  master=user.full_name or str(user.telegram_id),
                  total=f"{float(order.total_price):,.0f}"),
            )
        except Exception:
            pass

    # Notify client
    order_full = await order_svc.get_by_id_full(order.id)
    if order_full and order_full.client:
        try:
            cl = _gl(order_full.client)
            asphalt_name = order_full.asphalt_type.name if order_full.asphalt_type else "—"
            work_date_str = order_full.work_date.strftime("%d.%m.%Y") if order_full.work_date else "—"
            debt_val = float(order_full.debt) if order_full.debt else 0
            await bot.send_message(
                order_full.client.telegram_id,
                t("client_order_confirmed_notify", cl,
                  number=order_full.order_number,
                  master=user.full_name or str(user.telegram_id),
                  address=order_full.address or "—",
                  area=order_full.area_m2,
                  asphalt=asphalt_name,
                  date=work_date_str,
                  total=f"{float(order_full.total_price):,.0f}",
                  advance=f"{float(order_full.advance_paid):,.0f}",
                  debt=f"{debt_val:,.0f}"),
            )
        except Exception:
            pass

    # Schedule Celery auto-assign task at deadline
    try:
        from app.tasks import auto_assign_usta
        auto_assign_usta.apply_async(
            args=[order.id],
            eta=order.usta_assignment_deadline,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Celery schedule failed: %s", e)

    await callback.message.edit_text(
        t("order_confirmed_success", lang, number=order.order_number)
    )
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
    await callback.answer()


@router.callback_query(MasterConfirmStates.confirming, F.data == "cancel_confirm")
async def cancel_confirmation(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await callback.message.edit_text(t("confirm_cancelled", lang))
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
    await callback.answer()


# ── Status update (in-work) from order detail ─────────────────────────────────

@router.callback_query(F.data.startswith("set_status:"), RoleFilter(UserRole.MASTER))
async def master_set_status(callback: CallbackQuery, user: User, session, lang: str) -> None:
    parts = callback.data.split(":")
    order_id, new_status_val = int(parts[1]), parts[2]
    from app.db.models import OrderStatus
    try:
        new_status = OrderStatus(new_status_val)
    except ValueError:
        await callback.answer(t("invalid_status", lang), show_alert=True)
        return
    order_svc = OrderService(session)
    await order_svc.update_status(order_id, new_status, user.id)
    await callback.answer(t("status_updated", lang))
    order = await order_svc.get_by_id_full(order_id)
    if order:
        asphalt = order.asphalt_type.name if order.asphalt_type else "—"
        usta_name = order.usta.full_name if order.usta else t("not_assigned", lang)
        status_label = ORDER_STATUS_LABELS.get(order.status, order.status.value)
        work_date = order.work_date.strftime("%d.%m.%Y") if order.work_date else "—"

        # Notify client about status change
        if order.client:
            from app.bot.loader import bot
            from app.bot.i18n import get_lang as _gl
            try:
                cl = _gl(order.client)
                await bot.send_message(
                    order.client.telegram_id,
                    t("client_status_changed_notify", cl,
                      number=order.order_number,
                      status=status_label),
                )
            except Exception:
                pass

        await callback.message.edit_text(
            f"📋 <b>{t('order', lang)}: {order.order_number}</b>\n\n"
            f"📐 {t('area', lang)}: {order.area_m2} m²\n"
            f"🏗 {t('asphalt', lang)}: {asphalt}\n"
            f"💰 {t('total', lang)}: {float(order.total_price):,.0f}\n"
            f"📅 {t('work_date', lang)}: {work_date}\n"
            f"👷 {t('usta', lang)}: {usta_name}\n"
            f"📊 {t('status', lang)}: {status_label}",
            reply_markup=get_master_order_detail_keyboard(order),
        )


# ── Usta tayinlash ────────────────────────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_assign_usta", set())))
async def assign_usta_menu(message: Message, user: User, session, lang: str) -> None:
    usta_svc = UstaService(session)
    orders = await usta_svc.get_pending_usta_orders(user.id)
    if not orders:
        await message.answer(t("no_usta_pending", lang))
        return
    await message.answer(
        t("usta_assign_list", lang, count=len(orders)),
        reply_markup=get_usta_assignment_orders_keyboard(orders),
    )


@router.callback_query(F.data.startswith("master_pick_order_for_usta:"))
async def pick_order_for_usta(callback: CallbackQuery, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await callback.answer(t("order_not_found", lang), show_alert=True)
        return

    usta_svc = UstaService(session)
    ustas_with_count = await usta_svc.get_available_ustas(region_id=order.region_id, viloyat_id=order.viloyat_id)
    if not ustas_with_count:
        await callback.message.edit_text(t("no_ustas_available", lang))
        await callback.answer()
        return

    asphalt = order.asphalt_type.name if order.asphalt_type else "—"
    await callback.message.edit_text(
        t("select_usta", lang,
          number=order.order_number,
          area=order.area_m2,
          asphalt=asphalt,
          count=len(ustas_with_count)),
        reply_markup=get_ustas_for_assignment_keyboard(ustas_with_count, order_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("assign_usta_to_order:"))
async def do_assign_usta(callback: CallbackQuery, user: User, session, lang: str) -> None:
    parts = callback.data.split(":")
    order_id, usta_id = int(parts[1]), int(parts[2])

    usta_svc = UstaService(session)
    order = await usta_svc.assign_usta_to_order(
        order_id=order_id, usta_id=usta_id, assigned_by_id=user.id
    )
    if not order:
        await callback.answer(t("order_not_found", lang), show_alert=True)
        return

    user_svc = UserService(session)
    usta = await user_svc.get_by_id(usta_id)
    order_full = await OrderService(session).get_by_id_full(order_id)

    # Notify usta
    from app.bot.loader import bot
    from app.bot.i18n import get_lang as _gl
    from app.bot.keyboards.usta import get_usta_notification_keyboard
    asphalt = order_full.asphalt_type.name if order_full.asphalt_type else "—"
    wage = float(order_full.usta_wage) if order_full.usta_wage else 0
    work_date = (
        order_full.work_date.strftime("%d.%m.%Y") if order_full.work_date else "—"
    )
    try:
        ul = _gl(usta)
        await bot.send_message(
            usta.telegram_id,
            t("usta_assignment_notify", ul,
              number=order_full.order_number,
              address=order_full.address or "—",
              area=order_full.area_m2,
              asphalt=asphalt,
              date=work_date,
              wage=f"{wage:,.0f}"),
            reply_markup=get_usta_notification_keyboard(order_id),
        )
    except Exception:
        pass

    usta_name = usta.full_name or str(usta.telegram_id)

    # Notify client about usta assignment
    if order_full.client:
        try:
            cl = _gl(order_full.client)
            await bot.send_message(
                order_full.client.telegram_id,
                t("client_usta_assigned_notify", cl,
                  number=order_full.order_number,
                  usta=usta_name,
                  date=work_date),
            )
        except Exception:
            pass

    await callback.message.edit_text(
        t("usta_assigned_success", lang,
          number=order_full.order_number,
          usta=usta_name),
    )
    await callback.answer()


@router.callback_query(F.data == "back_usta_orders")
async def back_to_usta_orders(callback: CallbackQuery, user: User, session, lang: str) -> None:
    usta_svc = UstaService(session)
    orders = await usta_svc.get_pending_usta_orders(user.id)
    if not orders:
        await callback.message.edit_text(t("no_usta_pending", lang))
    else:
        await callback.message.edit_text(
            t("usta_assign_list", lang, count=len(orders)),
            reply_markup=get_usta_assignment_orders_keyboard(orders),
        )
    await callback.answer()


# ── Change usta on order ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("change_usta:"))
async def change_usta_prompt(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await callback.answer(t("order_not_found", lang), show_alert=True)
        return

    usta_svc = UstaService(session)
    ustas_with_count = await usta_svc.get_available_ustas(region_id=order.region_id, viloyat_id=order.viloyat_id)
    if not ustas_with_count:
        await callback.answer("⚠️ Mavjud ustalar yo'q", show_alert=True)
        return

    current_usta = order.usta.full_name if order.usta else "Tayinlanmagan"
    asphalt = order.asphalt_type.name if order.asphalt_type else "—"
    await callback.message.edit_text(
        f"👷 <b>Usta o'zgartirish</b>\n\n"
        f"📋 Zakaz: #{order.order_number}\n"
        f"📐 {order.area_m2} m² · 🏗 {asphalt}\n"
        f"👷 Hozirgi usta: <b>{current_usta}</b>\n\n"
        f"Yangi ustani tanlang ({len(ustas_with_count)} ta mavjud):",
        reply_markup=get_ustas_for_reassignment_keyboard(
            ustas_with_count, order_id, order.usta_id
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("reassign_usta:"))
async def do_reassign_usta(callback: CallbackQuery, user: User, session, lang: str) -> None:
    parts = callback.data.split(":")
    order_id, new_usta_id = int(parts[1]), int(parts[2])

    usta_svc = UstaService(session)
    order = await usta_svc.reassign_usta(
        order_id=order_id, new_usta_id=new_usta_id, assigned_by_id=user.id
    )
    if not order:
        await callback.answer("❌ Xatolik: zakaz topilmadi yoki usta noto'g'ri", show_alert=True)
        return

    user_svc = UserService(session)
    new_usta = await user_svc.get_by_id(new_usta_id)
    order_full = await OrderService(session).get_by_id_full(order_id)

    # Notify new usta
    from app.bot.loader import bot
    from app.bot.i18n import get_lang as _gl
    from app.bot.keyboards.usta import get_usta_notification_keyboard
    asphalt = order_full.asphalt_type.name if order_full.asphalt_type else "—"
    wage = float(order_full.usta_wage) if order_full.usta_wage else 0
    work_date = order_full.work_date.strftime("%d.%m.%Y") if order_full.work_date else "—"
    try:
        ul = _gl(new_usta)
        await bot.send_message(
            new_usta.telegram_id,
            t("usta_assignment_notify", ul,
              number=order_full.order_number,
              address=order_full.address or "—",
              area=order_full.area_m2,
              asphalt=asphalt,
              date=work_date,
              wage=f"{wage:,.0f}"),
            reply_markup=get_usta_notification_keyboard(order_id),
        )
    except Exception:
        pass

    usta_name = new_usta.full_name or str(new_usta.telegram_id)

    # Notify client about usta reassignment
    if order_full.client:
        try:
            cl = _gl(order_full.client)
            await bot.send_message(
                order_full.client.telegram_id,
                t("client_usta_assigned_notify", cl,
                  number=order_full.order_number,
                  usta=usta_name,
                  date=work_date),
            )
        except Exception:
            pass

    await callback.message.edit_text(
        f"✅ <b>Usta o'zgartirildi!</b>\n\n"
        f"📋 Zakaz: #{order_full.order_number}\n"
        f"👷 Yangi usta: {usta_name}\n\n"
        f"Usta bildirishnoma oldi."
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back_order_detail:"))
async def back_to_order_detail(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await callback.message.edit_text(t("order_not_found", lang))
        await callback.answer()
        return
    status_label = ORDER_STATUS_LABELS.get(order.status, order.status.value)
    asphalt = order.asphalt_type.name if order.asphalt_type else "—"
    usta_name = order.usta.full_name if order.usta else t("not_assigned", lang)
    loc = location_link(order.latitude, order.longitude)
    text = (
        f"📋 <b>{t('order', lang)}: {order.order_number}</b>\n\n"
        f"👤 {t('client', lang)}: <b>{order.client_name}</b> | {order.client_phone}\n"
        f"📍 {t('address', lang)}: <b>{order.address or '—'}</b>\n"
        f"{loc}"
        f"📐 {t('area', lang)}: <b>{order.area_m2 or '?'} m²</b>\n"
        f"🏗 {t('asphalt', lang)}: <b>{asphalt}</b>\n"
        f"💰 {t('total', lang)}: <b>{float(order.total_price):,.0f}</b>\n"
        f"💵 {t('advance', lang)}: <b>{float(order.advance_paid):,.0f}</b>\n"
        f"💳 {t('debt', lang)}: <b>{float(order.debt):,.0f}</b>\n"
        f"👷 {t('usta', lang)}: <b>{usta_name}</b>\n"
        f"📅 {t('status', lang)}: <b>{status_label}</b>"
    )
    await callback.message.edit_text(
        text, reply_markup=get_master_confirmed_order_keyboard(order_id)
    )
    await callback.answer()


# ── Expense entry FSM ──────────────────────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_add_expense", set())))
async def expense_start(message: Message, user: User, session, lang: str) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_master(user.id, limit=20)
    active = [o for o in orders if o.status in (OrderStatus.CONFIRMED, OrderStatus.IN_WORK)]
    if not active:
        await message.answer(t("expense_no_active", lang))
        return
    await message.answer(
        t("expense_start", lang),
        reply_markup=get_master_orders_for_expense_keyboard(active),
    )


@router.callback_query(F.data.startswith("expense_pick_order:"))
async def expense_pick_order(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(ExpenseAddStates.selecting_type)
    await callback.message.edit_text(
        t("expense_select_type", lang),
        reply_markup=get_expense_type_keyboard(),
    )
    await callback.answer()


@router.callback_query(ExpenseAddStates.selecting_type, F.data.startswith("expense_type:"))
async def expense_pick_type(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    exp_type = callback.data.split(":")[1]
    await state.update_data(expense_type=exp_type)
    await state.set_state(ExpenseAddStates.entering_amount)
    await callback.message.edit_text(t("expense_enter_amount", lang))
    await callback.answer()


@router.message(ExpenseAddStates.entering_amount)
async def expense_amount(message: Message, state: FSMContext, lang: str) -> None:
    raw = (message.text or "").strip().replace(" ", "").replace(",", "")
    try:
        amount = Decimal(raw)
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer(t("invalid_sum", lang))
        return
    await state.update_data(amount=str(amount))
    await state.set_state(ExpenseAddStates.entering_description)
    await message.answer(
        t("expense_enter_desc", lang),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(ExpenseAddStates.entering_description)
async def expense_description(
    message: Message, state: FSMContext, user: User, session, lang: str
) -> None:
    text = message.text or ""
    description = None if text.startswith("⏩") else text.strip() or None
    data = await state.get_data()
    await state.clear()

    from app.db.models import ExpenseType
    exp_svc = ExpenseService(session)
    expense = await exp_svc.add(
        order_id=data["order_id"],
        expense_type=ExpenseType(data["expense_type"]),
        amount=Decimal(data["amount"]),
        created_by=user.id,
        description=description,
    )
    label = EXPENSE_LABELS.get(ExpenseType(data["expense_type"]), data["expense_type"])
    await message.answer(
        t("expense_added", lang,
          label=label,
          amount=f"{float(expense.amount):,.0f}",
          desc=description or '—'),
        reply_markup=get_main_menu(UserRole.MASTER, lang),
    )


@router.callback_query(ExpenseAddStates.selecting_type, F.data == "expense_cancel")
async def expense_cancel(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await callback.message.edit_text(t("expense_cancelled", lang))
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
    await callback.answer()
