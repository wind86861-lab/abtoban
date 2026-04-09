from datetime import datetime
from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters import RoleFilter
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu, get_skip_keyboard
from app.bot.keyboards.order import (
    get_confirm_summary_keyboard,
    get_keep_address_keyboard,
    get_master_confirmed_order_keyboard,
    get_master_order_detail_keyboard,
    get_orders_list_keyboard,
)
from app.bot.keyboards.finance import (
    get_expense_type_keyboard,
    get_master_orders_for_expense_keyboard,
)
from app.bot.keyboards.usta import (
    get_usta_assignment_orders_keyboard,
    get_ustas_for_assignment_keyboard,
)
from app.bot.states.finance import ExpenseAddStates
from app.bot.states.order import MasterConfirmStates
from app.db.models import ORDER_STATUS_LABELS, OrderStatus, User, UserRole
from app.services.expense_service import EXPENSE_LABELS, ExpenseService
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

@router.message(F.text.in_({"🆕 Yangi zakazlar", "✅ Zakaz tasdiqlash"}))
async def new_orders(message: Message, session) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_new_orders()
    if not orders:
        await message.answer("🆕 <b>Yangi zakazlar</b>\n\nHozircha yangi zakazlar yo'q.")
        return
    await message.answer(
        f"🆕 <b>Yangi zakazlar</b> ({len(orders)} ta)\n\nBatafsil ko'rish uchun tanlang:",
        reply_markup=get_orders_list_keyboard(orders, prefix="master_view_new"),
    )


@router.callback_query(F.data.startswith("master_view_new:"))
async def view_new_order(callback: CallbackQuery, session) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await callback.answer("❌ Zakaz topilmadi", show_alert=True)
        return
    asphalt = order.asphalt_type.name if order.asphalt_type else "—"
    text = (
        f"📋 <b>Zakaz: {order.order_number}</b>\n\n"
        f"👤 Klient: <b>{order.client_name}</b>\n"
        f"📱 Tel: <b>{order.client_phone}</b>\n"
        f"📍 Manzil: <b>{order.address or '—'}</b>\n"
        f"📐 Taxminiy maydon: <b>{order.area_m2 or '?'} m²</b>\n"
        f"🏗 Asfalt: <b>{asphalt}</b>\n"
        f"📅 Yaratildi: <b>{order.created_at.strftime('%d.%m.%Y %H:%M')}</b>\n\n"
        f"<i>Tasdiqlash uchun tugmani bosing.</i>"
    )
    await callback.message.edit_text(text, reply_markup=get_master_order_detail_keyboard(order_id))
    await callback.answer()


@router.callback_query(F.data == "back_new_orders")
async def back_to_new_orders(callback: CallbackQuery, session) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_new_orders()
    if not orders:
        await callback.message.edit_text("🆕 Hozircha yangi zakazlar yo'q.")
    else:
        await callback.message.edit_text(
            f"🆕 <b>Yangi zakazlar</b> ({len(orders)} ta):",
            reply_markup=get_orders_list_keyboard(orders, prefix="master_view_new"),
        )
    await callback.answer()


# ── My (confirmed) orders ─────────────────────────────────────────────────────

@router.message(F.text == "📋 Mening zakazlarim")
async def my_orders(message: Message, user: User, session) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_master(user.id)
    if not orders:
        await message.answer("📋 <b>Mening zakazlarim</b>\n\nSizga biriktirilgan zakazlar yo'q.")
        return
    await message.answer(
        f"📋 <b>Mening zakazlarim</b> ({len(orders)} ta):",
        reply_markup=get_orders_list_keyboard(orders, prefix="master_view_mine"),
    )


@router.callback_query(F.data.startswith("master_view_mine:"))
async def view_my_order(callback: CallbackQuery, session) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await callback.answer("❌ Zakaz topilmadi", show_alert=True)
        return
    status_label = ORDER_STATUS_LABELS.get(order.status, order.status.value)
    asphalt = order.asphalt_type.name if order.asphalt_type else "—"
    usta_name = order.usta.full_name if order.usta else "Tayinlanmagan"
    text = (
        f"📋 <b>Zakaz: {order.order_number}</b>\n\n"
        f"👤 Klient: <b>{order.client_name}</b> | {order.client_phone}\n"
        f"📍 Manzil: <b>{order.address or '—'}</b>\n"
        f"📐 Maydon: <b>{order.area_m2 or '?'} m²</b>\n"
        f"🏗 Asfalt: <b>{asphalt}</b>\n"
        f"💰 Summa: <b>{float(order.total_price):,.0f} so'm</b>\n"
        f"💵 Zaklad: <b>{float(order.advance_paid):,.0f}</b>\n"
        f"💳 Qarz: <b>{float(order.debt):,.0f}</b>\n"
        f"👷 Usta: <b>{usta_name}</b>\n"
        f"📅 Holat: <b>{status_label}</b>"
    )
    await callback.message.edit_text(
        text, reply_markup=get_master_confirmed_order_keyboard(order_id)
    )
    await callback.answer()


@router.callback_query(F.data == "back_my_orders")
async def back_to_my_orders(callback: CallbackQuery, user: User, session) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_master(user.id)
    if not orders:
        await callback.message.edit_text("📋 Sizga biriktirilgan zakazlar yo'q.")
    else:
        await callback.message.edit_text(
            f"📋 <b>Mening zakazlarim</b> ({len(orders)} ta):",
            reply_markup=get_orders_list_keyboard(orders, prefix="master_view_mine"),
        )
    await callback.answer()


# ── Confirmation FSM (9 steps) ────────────────────────────────────────────────

@router.callback_query(F.data.startswith("start_confirm:"))
async def start_confirm_fsm(callback: CallbackQuery, state: FSMContext, session) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id(order_id)

    if not order:
        await callback.answer("❌ Zakaz topilmadi", show_alert=True)
        return
    from app.db.models import OrderStatus
    if order.status != OrderStatus.NEW:
        await callback.answer("❌ Bu zakaz allaqachon tasdiqlangan!", show_alert=True)
        return

    await state.update_data(
        order_id=order_id,
        existing_address=order.address or "",
        order_number=order.order_number,
    )
    await state.set_state(MasterConfirmStates.entering_area)
    await callback.message.edit_text(
        f"✅ <b>Zakaz tasdiqlash: {order.order_number}</b>\n\n"
        f"1/8 — Aniq maydon hajmini kiriting (m²):"
    )
    await callback.answer()


@router.message(MasterConfirmStates.entering_area)
async def confirm_area(message: Message, state: FSMContext) -> None:
    val = _parse_decimal(message.text or "")
    if val is None or val <= 0:
        await message.answer("❌ Noto'g'ri. Musbat raqam kiriting (masalan: 450):")
        return
    await state.update_data(area_m2=str(val))
    await state.set_state(MasterConfirmStates.entering_sum)
    await message.answer(
        "2/8 — Umumiy summani kiriting (so'm):\nMisol: <code>45000000</code>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(MasterConfirmStates.entering_sum)
async def confirm_sum(message: Message, state: FSMContext) -> None:
    val = _parse_decimal(message.text or "")
    if val is None or val <= 0:
        await message.answer("❌ Noto'g'ri summa. Musbat raqam kiriting:")
        return
    await state.update_data(total_price=str(val))
    await state.set_state(MasterConfirmStates.entering_advance)
    await message.answer(
        "3/8 — Zaklad (avans) miqdori (so'm):\nMisol: <code>10000000</code>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(MasterConfirmStates.entering_advance)
async def confirm_advance(message: Message, state: FSMContext) -> None:
    val = _parse_decimal(message.text or "")
    if val is None:
        await message.answer("❌ Noto'g'ri. Raqam kiriting (0 bo'lishi mumkin):")
        return
    await state.update_data(advance_paid=str(val))
    data = await state.get_data()
    await state.set_state(MasterConfirmStates.entering_address)
    existing = data.get("existing_address", "")
    await message.answer(
        f"4/8 — Manzilni tasdiqlang yoki o'zgartiring:\n"
        f"Joriy manzil: <b>{existing or '—'}</b>\n\n"
        f"Yangi manzil kiriting yoki 'Saqlash' tugmasini bosing:",
        reply_markup=get_keep_address_keyboard(existing) if existing else get_cancel_keyboard(),
    )


@router.message(MasterConfirmStates.entering_address)
async def confirm_address(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    existing = data.get("existing_address", "")
    text = message.text or ""
    if text.startswith("📍 Saqlash:") or text.startswith(f"📍 Saqlash: {existing[:40]}"):
        address = existing
    else:
        address = text.strip()
        if len(address) < 5:
            await message.answer("❌ Manzil juda qisqa. Aniqroq yozing:")
            return
    await state.update_data(address=address)
    await state.set_state(MasterConfirmStates.entering_date)
    await message.answer(
        "5/8 — Ish sanasini kiriting (KK.OO.YYYY):\nMisol: <code>25.04.2026</code>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(MasterConfirmStates.entering_date)
async def confirm_date(message: Message, state: FSMContext) -> None:
    dt = _parse_date(message.text or "")
    if dt is None:
        await message.answer("❌ Noto'g'ri sana. Format: KK.OO.YYYY  (masalan: 25.04.2026):")
        return
    await state.update_data(work_date=dt.isoformat())
    await state.set_state(MasterConfirmStates.entering_usta_wage)
    await message.answer(
        "6/8 — Usta ish haqi (so'm):\nMisol: <code>5000000</code>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(MasterConfirmStates.entering_usta_wage)
async def confirm_usta_wage(message: Message, state: FSMContext) -> None:
    val = _parse_decimal(message.text or "")
    if val is None:
        await message.answer("❌ Noto'g'ri. Raqam kiriting:")
        return
    await state.update_data(usta_wage=str(val))
    await state.set_state(MasterConfirmStates.entering_commission)
    await message.answer(
        "7/8 — Sizning komissiyangiz (so'm):\nMisol: <code>2000000</code>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(MasterConfirmStates.entering_commission)
async def confirm_commission(message: Message, state: FSMContext) -> None:
    val = _parse_decimal(message.text or "")
    if val is None:
        await message.answer("❌ Noto'g'ri. Raqam kiriting:")
        return
    await state.update_data(master_commission=str(val))
    await state.set_state(MasterConfirmStates.entering_notes)
    await message.answer(
        "8/8 — Izoh (ixtiyoriy). Qo'shimcha ma'lumot yozing yoki o'tkazib yuboring:",
        reply_markup=get_skip_keyboard(),
    )


@router.message(MasterConfirmStates.entering_notes)
async def confirm_notes(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    notes = None if text.startswith("⏩") else text.strip()
    await state.update_data(notes=notes)
    await state.set_state(MasterConfirmStates.confirming)

    data = await state.get_data()
    work_date = datetime.fromisoformat(data["work_date"]).strftime("%d.%m.%Y")
    debt = max(Decimal("0"), Decimal(data["total_price"]) - Decimal(data["advance_paid"]))

    await message.answer(
        f"📋 <b>Tasdiqlash xulosasi — {data['order_number']}</b>\n\n"
        f"📐 Maydon: <b>{data['area_m2']} m²</b>\n"
        f"💰 Summa: <b>{float(Decimal(data['total_price'])):,.0f} so'm</b>\n"
        f"💵 Zaklad: <b>{float(Decimal(data['advance_paid'])):,.0f} so'm</b>\n"
        f"💳 Qarz: <b>{float(debt):,.0f} so'm</b>\n"
        f"📍 Manzil: {data['address']}\n"
        f"📅 Ish sanasi: {work_date}\n"
        f"👷 Usta haqi: <b>{float(Decimal(data['usta_wage'])):,.0f} so'm</b>\n"
        f"💼 Komissiya: <b>{float(Decimal(data['master_commission'])):,.0f} so'm</b>\n"
        f"📝 Izoh: {data.get('notes') or '—'}\n\n"
        f"Tasdiqlaysizmi?",
        reply_markup=get_confirm_summary_keyboard(),
    )


@router.callback_query(MasterConfirmStates.confirming, F.data == "submit_confirm")
async def submit_confirmation(callback: CallbackQuery, state: FSMContext, user: User, session) -> None:
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
        await callback.message.edit_text(
            "❌ Xatolik: zakaz allaqachon boshqasi tomonidan tasdiqlangan yoki topilmadi."
        )
        await callback.answer()
        return

    # Notify admins
    from app.bot.loader import bot
    user_svc = UserService(session)
    admins = await user_svc.get_all(role=UserRole.ADMIN)
    super_admins = await user_svc.get_all(role=UserRole.SUPER_ADMIN)
    notify_text = (
        f"✅ <b>Zakaz tasdiqlandi!</b>\n\n"
        f"🔢 #{order.order_number}\n"
        f"👷 Master: {user.full_name or user.telegram_id}\n"
        f"💰 Summa: {float(order.total_price):,.0f} so'm\n"
        f"⏰ Usta tayinlash muddati: 30 daqiqa"
    )
    for admin in admins + super_admins:
        try:
            await bot.send_message(admin.telegram_id, notify_text)
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
        f"✅ <b>Zakaz muvaffaqiyatli tasdiqlandi!</b>\n\n"
        f"🔢 #{order.order_number}\n"
        f"⏰ Usta tayinlash uchun 30 daqiqa vaqtingiz bor.\n"
        f"'👷 Usta tayinlash' tugmasini bosing."
    )
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(UserRole.MASTER))
    await callback.answer()


@router.callback_query(MasterConfirmStates.confirming, F.data == "cancel_confirm")
async def cancel_confirmation(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Tasdiqlash bekor qilindi.")
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(UserRole.MASTER))
    await callback.answer()


# ── Status update (in-work) from order detail ─────────────────────────────────

@router.callback_query(F.data.startswith("set_status:"), RoleFilter(UserRole.MASTER))
async def master_set_status(callback: CallbackQuery, user: User, session) -> None:
    parts = callback.data.split(":")
    order_id, new_status_val = int(parts[1]), parts[2]
    from app.db.models import OrderStatus
    try:
        new_status = OrderStatus(new_status_val)
    except ValueError:
        await callback.answer("❌ Noto'g'ri status", show_alert=True)
        return
    order_svc = OrderService(session)
    await order_svc.update_status(order_id, new_status, user.id)
    await callback.answer(f"✅ Status yangilandi")
    # Refresh view
    callback.data = f"master_view_mine:{order_id}"
    await view_my_order(callback, session)


# ── Usta tayinlash ────────────────────────────────────────────────────────────

@router.message(F.text == "👷 Usta tayinlash")
async def assign_usta_menu(message: Message, user: User, session) -> None:
    usta_svc = UstaService(session)
    orders = await usta_svc.get_pending_usta_orders(user.id)
    if not orders:
        await message.answer(
            "👷 <b>Usta tayinlash</b>\n\n"
            "Hozircha usta tayin qilinishi kerak bo'lgan zakazlar yo'q.\n"
            "(Yangi zakazni tasdiqlagandan so'ng shu yerda ko'rinadi)"
        )
        return
    await message.answer(
        f"👷 <b>Usta tayinlash</b>\n\n"
        f"{len(orders)} ta zakaz usta kutmoqda.\n"
        f"Tanlang:",
        reply_markup=get_usta_assignment_orders_keyboard(orders),
    )


@router.callback_query(F.data.startswith("master_pick_order_for_usta:"))
async def pick_order_for_usta(callback: CallbackQuery, session) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await callback.answer("❌ Zakaz topilmadi", show_alert=True)
        return

    usta_svc = UstaService(session)
    ustas_with_count = await usta_svc.get_available_ustas()
    if not ustas_with_count:
        await callback.message.edit_text(
            "⚠️ <b>Mavjud usta yo'q</b>\n\n"
            "Barcha ustalar band (2/2 zakaz) yoki faol emas.\n"
            "30 daqiqa o'tsa avtomatik tayinlanadi."
        )
        await callback.answer()
        return

    asphalt = order.asphalt_type.name if order.asphalt_type else "—"
    await callback.message.edit_text(
        f"👷 <b>Usta tanlang</b>\n\n"
        f"Zakaz: #{order.order_number}\n"
        f"📐 {order.area_m2} m²  🏗 {asphalt}\n\n"
        f"Mavjud ustalar ({len(ustas_with_count)} ta):",
        reply_markup=get_ustas_for_assignment_keyboard(ustas_with_count, order_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("assign_usta_to_order:"))
async def do_assign_usta(callback: CallbackQuery, user: User, session) -> None:
    parts = callback.data.split(":")
    order_id, usta_id = int(parts[1]), int(parts[2])

    usta_svc = UstaService(session)
    order = await usta_svc.assign_usta_to_order(
        order_id=order_id, usta_id=usta_id, assigned_by_id=user.id
    )
    if not order:
        await callback.answer("❌ Zakaz topilmadi", show_alert=True)
        return

    user_svc = UserService(session)
    usta = await user_svc.get_by_id(usta_id)
    order_full = await OrderService(session).get_by_id_full(order_id)

    # Notify usta
    from app.bot.loader import bot
    from app.bot.keyboards.usta import get_usta_notification_keyboard
    asphalt = order_full.asphalt_type.name if order_full.asphalt_type else "—"
    wage = float(order_full.usta_wage) if order_full.usta_wage else 0
    work_date = (
        order_full.work_date.strftime("%d.%m.%Y") if order_full.work_date else "—"
    )
    try:
        await bot.send_message(
            usta.telegram_id,
            f"👷 <b>Sizga zakaz tayinlandi!</b>\n\n"
            f"🔢 #{order_full.order_number}\n"
            f"📍 {order_full.address or '—'}\n"
            f"📐 {order_full.area_m2} m²  🏗 {asphalt}\n"
            f"📅 Ish sanasi: {work_date}\n"
            f"💰 Usta haqi: {wage:,.0f} so'm\n\n"
            f"Qabul qilasizmi?",
            reply_markup=get_usta_notification_keyboard(order_id),
        )
    except Exception:
        pass

    usta_name = usta.full_name or str(usta.telegram_id)
    await callback.message.edit_text(
        f"✅ <b>Usta tayinlandi!</b>\n\n"
        f"Zakaz: #{order_full.order_number}\n"
        f"👷 Usta: {usta_name}\n\n"
        f"Usta bildirishnoma oldi."
    )
    await callback.answer(f"✅ {usta_name} tayinlandi!")


@router.callback_query(F.data == "back_usta_orders")
async def back_to_usta_orders(callback: CallbackQuery, user: User, session) -> None:
    usta_svc = UstaService(session)
    orders = await usta_svc.get_pending_usta_orders(user.id)
    if not orders:
        await callback.message.edit_text(
            "👷 Usta tayinlanishi kerak bo'lgan zakazlar yo'q."
        )
    else:
        await callback.message.edit_text(
            f"👷 <b>Usta tayinlash</b> — {len(orders)} ta zakaz:",
            reply_markup=get_usta_assignment_orders_keyboard(orders),
        )
    await callback.answer()


# ── Expense entry FSM ──────────────────────────────────────────────────────────

@router.message(F.text == "💸 Xarajat kiritish")
async def expense_start(message: Message, user: User, session) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_master(user.id, limit=20)
    active = [o for o in orders if o.status in (OrderStatus.CONFIRMED, OrderStatus.IN_WORK)]
    if not active:
        await message.answer(
            "💸 <b>Xarajat kiritish</b>\n\nFaol zakaz yo'q."
        )
        return
    await message.answer(
        "💸 <b>Xarajat kiritish</b>\n\nQaysi zakaz uchun?",
        reply_markup=get_master_orders_for_expense_keyboard(active),
    )


@router.callback_query(F.data.startswith("expense_pick_order:"))
async def expense_pick_order(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(ExpenseAddStates.selecting_type)
    await callback.message.edit_text(
        "💸 Xarajat turini tanlang:",
        reply_markup=get_expense_type_keyboard(),
    )
    await callback.answer()


@router.callback_query(ExpenseAddStates.selecting_type, F.data.startswith("expense_type:"))
async def expense_pick_type(callback: CallbackQuery, state: FSMContext) -> None:
    exp_type = callback.data.split(":")[1]
    await state.update_data(expense_type=exp_type)
    await state.set_state(ExpenseAddStates.entering_amount)
    await callback.message.edit_text(
        "💰 Summasini kiriting (so'm):\nMisol: <code>250000</code>"
    )
    await callback.answer()


@router.message(ExpenseAddStates.entering_amount)
async def expense_amount(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip().replace(" ", "").replace(",", "")
    try:
        amount = Decimal(raw)
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Noto'g'ri summa. Raqam kiriting:")
        return
    await state.update_data(amount=str(amount))
    await state.set_state(ExpenseAddStates.entering_description)
    await message.answer(
        "📝 Izoh kiriting (ixtiyoriy):\n'⏩' bosing o'tkazib yuborish uchun.",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(ExpenseAddStates.entering_description)
async def expense_description(
    message: Message, state: FSMContext, user: User, session
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
        f"✅ <b>Xarajat kiritildi!</b>\n\n"
        f"{label}: <b>{float(expense.amount):,.0f} so'm</b>\n"
        f"📝 {description or '—'}",
        reply_markup=get_main_menu(UserRole.MASTER),
    )


@router.callback_query(ExpenseAddStates.selecting_type, F.data == "expense_cancel")
async def expense_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Xarajat kiritish bekor qilindi.")
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(UserRole.MASTER))
    await callback.answer()
