from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.filters import RoleFilter
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu
from app.bot.keyboards.order import (
    get_admin_order_detail_keyboard,
    get_asphalt_keyboard,
    get_order_confirm_keyboard,
    get_status_selection_keyboard,
)
from app.bot.states.order import AdminOrderCreateStates
from app.db.models import (
    MANAGEMENT_ROLES,
    ORDER_STATUS_LABELS,
    User,
    UserRole,
    OrderStatus,
)
from app.services.asphalt_service import AsphaltService
from app.services.expense_service import EXPENSE_LABELS, ExpenseService
from app.services.order_service import OrderService
from app.services.user_service import UserService
from app.bot.keyboards.finance import get_payment_update_keyboard
from app.bot.states.finance import PaymentUpdateStates

router = Router()

PER_PAGE = 10


def _fmt_order_detail(order) -> str:
    status_label = ORDER_STATUS_LABELS.get(order.status, order.status.value)
    asphalt = order.asphalt_type.name if order.asphalt_type else "—"
    master = order.master.full_name if order.master else "Tayinlanmagan"
    usta = order.usta.full_name if order.usta else "Tayinlanmagan"
    price = f"{float(order.total_price):,.0f} so'm" if order.total_price else "—"
    advance = f"{float(order.advance_paid):,.0f}" if order.advance_paid else "0"
    debt = f"{float(order.debt):,.0f}" if order.debt else "0"
    work_date = order.work_date.strftime("%d.%m.%Y") if order.work_date else "—"
    return (
        f"📋 <b>Zakaz: {order.order_number}</b>\n\n"
        f"👤 Klient: <b>{order.client_name}</b>\n"
        f"📱 Tel: <b>{order.client_phone}</b>\n"
        f"📍 Manzil: <b>{order.address or '—'}</b>\n"
        f"📐 Maydon: <b>{order.area_m2 or '?'} m²</b>\n"
        f"🏗 Asfalt: <b>{asphalt}</b>\n"
        f"💰 Summa: <b>{price}</b>\n"
        f"💵 Zaklad: <b>{advance}</b>\n"
        f"💳 Qarz: <b>{debt}</b>\n"
        f"📅 Ish sanasi: <b>{work_date}</b>\n"
        f"👷 Master: <b>{master}</b>\n"
        f"🔨 Usta: <b>{usta}</b>\n"
        f"📊 Holat: <b>{status_label}</b>\n"
        f"🕐 Yaratildi: <b>{order.created_at.strftime('%d.%m.%Y %H:%M')}</b>"
    )


# ── All orders list ────────────────────────────────────────────────────────────

@router.message(F.text == "📋 Barcha zakazlar", RoleFilter(*MANAGEMENT_ROLES))
async def all_orders(message: Message, session) -> None:
    await _render_orders_list(message, session, page=0, as_new=True)


@router.callback_query(F.data.startswith("admin_orders_list:"), RoleFilter(*MANAGEMENT_ROLES))
async def orders_list_page(callback: CallbackQuery, session) -> None:
    parts = callback.data.split(":")
    page = int(parts[1])
    status_val = parts[2] if len(parts) > 2 else ""
    status = OrderStatus(status_val) if status_val else None
    await _render_orders_list(callback, session, page=page, status=status)
    await callback.answer()


async def _render_orders_list(event, session, page: int = 0, status=None, as_new: bool = False):
    order_svc = OrderService(session)
    orders = await order_svc.get_all(status=status, limit=PER_PAGE, offset=page * PER_PAGE)
    total = await order_svc.count_all(status=status)

    filter_label = ORDER_STATUS_LABELS.get(status, "Barcha") if status else "Barcha"
    header = f"📋 <b>Zakazlar ({filter_label})</b> — {total} ta\nSahifa {page + 1}/{max(1, -(-total // PER_PAGE))}\n"

    if not orders:
        text = header + "\nZakazlar topilmadi."
        kb = _build_filter_keyboard(page, status)
        if as_new:
            await event.answer(text, reply_markup=kb)
        else:
            await event.message.edit_text(text, reply_markup=kb)
        return

    lines = [header]
    for o in orders:
        st = ORDER_STATUS_LABELS.get(o.status, o.status.value)
        lines.append(
            f"• <code>{o.order_number}</code> — {st}\n"
            f"  👤 {o.client_name}  📐 {o.area_m2 or '?'} m²"
        )

    builder = InlineKeyboardBuilder()
    for o in orders:
        st = ORDER_STATUS_LABELS.get(o.status, "")
        builder.button(
            text=f"{o.order_number} | {st}",
            callback_data=f"admin_view_order:{o.id}",
        )
    builder.adjust(1)

    # Filter row
    for status_item, label in [
        ("", "📋 Barchasi"),
        (OrderStatus.NEW.value, "🆕 Yangi"),
        (OrderStatus.CONFIRMED.value, "✅ Tasdiqlangan"),
        (OrderStatus.IN_WORK.value, "🔧 Ishda"),
    ]:
        builder.button(
            text=f"{'▶ ' if (status_item == (status.value if status else '')) else ''}{label}",
            callback_data=f"admin_orders_list:{page}:{status_item}",
        )
    builder.adjust(1, repeat=True)

    # Pagination
    nav = []
    if page > 0:
        nav.append(("⬅️", f"admin_orders_list:{page - 1}:{status.value if status else ''}"))
    if (page + 1) * PER_PAGE < total:
        nav.append(("➡️", f"admin_orders_list:{page + 1}:{status.value if status else ''}"))
    for text_btn, cbd in nav:
        builder.button(text=text_btn, callback_data=cbd)
    if nav:
        builder.adjust(*([1] * (len(orders) + 4)), len(nav))

    text = "\n".join(lines)
    if as_new:
        await event.answer(text, reply_markup=builder.as_markup())
    else:
        await event.message.edit_text(text, reply_markup=builder.as_markup())


def _build_filter_keyboard(page: int, status):
    builder = InlineKeyboardBuilder()
    for status_item, label in [
        ("", "📋 Barchasi"),
        (OrderStatus.NEW.value, "🆕 Yangi"),
        (OrderStatus.CONFIRMED.value, "✅ Tasdiqlangan"),
        (OrderStatus.IN_WORK.value, "🔧 Ishda"),
    ]:
        builder.button(text=label, callback_data=f"admin_orders_list:{page}:{status_item}")
    builder.adjust(2)
    return builder.as_markup()


# ── Order detail ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin_view_order:"), RoleFilter(*MANAGEMENT_ROLES))
async def view_order_detail(callback: CallbackQuery, session) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await callback.answer("❌ Zakaz topilmadi", show_alert=True)
        return
    await callback.message.edit_text(
        _fmt_order_detail(order),
        reply_markup=get_admin_order_detail_keyboard(order_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order_change_status:"), RoleFilter(*MANAGEMENT_ROLES))
async def change_status_prompt(callback: CallbackQuery, session) -> None:
    order_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "🔄 Yangi statusni tanlang:",
        reply_markup=get_status_selection_keyboard(order_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_status:"), RoleFilter(*MANAGEMENT_ROLES))
async def set_order_status(callback: CallbackQuery, user: User, session) -> None:
    parts = callback.data.split(":")
    order_id, new_status_val = int(parts[1]), parts[2]
    try:
        new_status = OrderStatus(new_status_val)
    except ValueError:
        await callback.answer("❌ Noto'g'ri status", show_alert=True)
        return
    order_svc = OrderService(session)
    order = await order_svc.update_status(order_id, new_status, user.id)
    if not order:
        await callback.answer("❌ Zakaz topilmadi", show_alert=True)
        return
    status_label = ORDER_STATUS_LABELS.get(new_status, new_status.value)
    await callback.answer(f"✅ Status: {status_label}")
    # Refresh detail view
    order_full = await order_svc.get_by_id_full(order_id)
    await callback.message.edit_text(
        _fmt_order_detail(order_full),
        reply_markup=get_admin_order_detail_keyboard(order_id),
    )


# ── Manual order creation ──────────────────────────────────────────────────────

@router.message(F.text == "➕ Zakaz qo'shish", RoleFilter(*MANAGEMENT_ROLES))
async def admin_order_create_start(message: Message, state: FSMContext) -> None:
    await state.set_state(AdminOrderCreateStates.entering_client_phone)
    await message.answer(
        "➕ <b>Yangi zakaz qo'shish</b>\n\n"
        "1/5 — Klientning telefon raqamini kiriting:\n"
        "Misol: <code>+998901234567</code>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(AdminOrderCreateStates.entering_client_phone, RoleFilter(*MANAGEMENT_ROLES))
async def admin_order_phone(message: Message, state: FSMContext, session) -> None:
    phone = (message.text or "").strip()
    if len(phone) < 7:
        await message.answer("❌ Noto'g'ri raqam. Qaytadan kiriting:")
        return

    user_svc = UserService(session)
    existing = await user_svc.get_by_telegram_id(0)  # won't match
    # Try find by phone
    from sqlalchemy import select
    from app.db.models import User as UserModel
    result = await session.execute(
        select(UserModel).where(UserModel.phone == phone)
    )
    found_user = result.scalar_one_or_none()

    if found_user:
        await state.update_data(
            client_id=found_user.id,
            client_phone=phone,
            client_name=found_user.full_name or "Nomsiz",
        )
        await state.set_state(AdminOrderCreateStates.entering_address)
        await message.answer(
            f"✅ Klient topildi: <b>{found_user.full_name or 'Nomsiz'}</b>\n\n"
            f"2/5 — Manzilni kiriting:",
            reply_markup=get_cancel_keyboard(),
        )
    else:
        await state.update_data(client_phone=phone)
        await state.set_state(AdminOrderCreateStates.entering_client_name)
        await message.answer(
            "⚠️ Bu raqam bilan foydalanuvchi topilmadi.\n\n"
            "1.5/5 — Klient ismini kiriting:",
            reply_markup=get_cancel_keyboard(),
        )


@router.message(AdminOrderCreateStates.entering_client_name, RoleFilter(*MANAGEMENT_ROLES))
async def admin_order_name(message: Message, state: FSMContext, session) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("❌ Ism juda qisqa:")
        return

    data = await state.get_data()
    # Create a minimal user record with a placeholder telegram_id.
    # We use a temporary value (0) then update to -id after flush to stay unique.
    from app.db.models import User as UserModel
    new_user = UserModel(
        telegram_id=0,
        full_name=name,
        phone=data["client_phone"],
        role=UserRole.KLIENT,
    )
    session.add(new_user)
    await session.flush()
    new_user.telegram_id = -new_user.id
    await session.flush()

    await state.update_data(client_id=new_user.id, client_name=name)
    await state.set_state(AdminOrderCreateStates.entering_address)
    await message.answer(
        f"✅ Klient yaratildi: <b>{name}</b>\n\n"
        f"2/5 — Manzilni kiriting:",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(AdminOrderCreateStates.entering_address, RoleFilter(*MANAGEMENT_ROLES))
async def admin_order_address(message: Message, state: FSMContext) -> None:
    address = (message.text or "").strip()
    if len(address) < 5:
        await message.answer("❌ Manzil juda qisqa:")
        return
    await state.update_data(address=address)
    await state.set_state(AdminOrderCreateStates.entering_area)
    await message.answer(
        "3/5 — Maydon hajmini kiriting (m²):\nMisol: <code>500</code>",
        reply_markup=get_cancel_keyboard(),
    )


@router.message(AdminOrderCreateStates.entering_area, RoleFilter(*MANAGEMENT_ROLES))
async def admin_order_area(message: Message, state: FSMContext, session) -> None:
    raw = (message.text or "").strip().replace(",", ".")
    try:
        area = Decimal(raw)
        if area <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Noto'g'ri format. Raqam kiriting:")
        return

    await state.update_data(area_m2=str(area))
    asphalt_svc = AsphaltService(session)
    types = await asphalt_svc.get_all_active()
    if not types:
        await message.answer("⚠️ Asfalt turlari yo'q. Avval sozlamalarda qo'shing.")
        await state.clear()
        return
    await state.set_state(AdminOrderCreateStates.selecting_asphalt)
    await message.answer("4/5 — Asfalt turini tanlang:", reply_markup=get_asphalt_keyboard(types))


@router.callback_query(AdminOrderCreateStates.selecting_asphalt, F.data.startswith("asphalt:"))
async def admin_order_asphalt(callback: CallbackQuery, state: FSMContext, session) -> None:
    asphalt_id = int(callback.data.split(":")[1])
    asphalt_svc = AsphaltService(session)
    asphalt = await asphalt_svc.get_by_id(asphalt_id)
    if not asphalt:
        await callback.answer("❌ Topilmadi", show_alert=True)
        return

    data = await state.get_data()
    area = Decimal(data["area_m2"])
    estimated = area * asphalt.price_per_m2
    await state.update_data(asphalt_type_id=asphalt_id, asphalt_name=asphalt.name)
    await state.set_state(AdminOrderCreateStates.confirming)

    await callback.message.edit_text(
        f"📋 <b>Yangi zakaz xulosasi</b>\n\n"
        f"👤 Klient: <b>{data['client_name']}</b>\n"
        f"📱 Tel: <b>{data['client_phone']}</b>\n"
        f"📍 Manzil: {data['address']}\n"
        f"📐 Maydon: <b>{area} m²</b>\n"
        f"🏗 Asfalt: <b>{asphalt.name}</b>\n"
        f"💰 Taxminiy: <b>{float(estimated):,.0f} so'm</b>\n\n"
        f"Tasdiqlaysizmi?",
        reply_markup=get_order_confirm_keyboard(),
    )
    await callback.answer()


@router.callback_query(AdminOrderCreateStates.confirming, F.data == "confirm_order")
async def admin_order_submit(callback: CallbackQuery, state: FSMContext, user: User, session, lang: str) -> None:
    data = await state.get_data()
    await state.clear()

    order_svc = OrderService(session)
    order = await order_svc.create_by_admin(
        admin_id=user.id,
        client_id=data["client_id"],
        client_name=data["client_name"],
        client_phone=data["client_phone"],
        address=data["address"],
        area_m2=Decimal(data["area_m2"]),
        asphalt_type_id=data.get("asphalt_type_id"),
    )

    # Notify masters
    from app.bot.loader import bot
    user_svc = UserService(session)
    masters = await user_svc.get_all(role=UserRole.MASTER)
    notify_text = (
        f"🆕 <b>Yangi zakaz (admin tomonidan)!</b>\n\n"
        f"🔢 #{order.order_number}\n"
        f"👤 {data['client_name']} | {data['client_phone']}\n"
        f"📍 {order.address}\n"
        f"📐 {order.area_m2} m²"
    )
    for master in masters:
        try:
            await bot.send_message(master.telegram_id, notify_text)
        except Exception:
            pass

    await callback.message.edit_text(
        f"✅ <b>Zakaz yaratildi!</b>\n\n"
        f"🔢 Raqam: <code>{order.order_number}</code>\n"
        f"👤 Klient: {data['client_name']}\n"
        f"📍 Manzil: {order.address}"
    )
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(user.role, lang))
    await callback.answer()


@router.callback_query(AdminOrderCreateStates.confirming, F.data == "cancel_order")
async def admin_order_cancel(callback: CallbackQuery, state: FSMContext, user: User, lang: str) -> None:
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(user.role, lang))
    await callback.answer()


# ── Expense view ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("view_expenses:"), RoleFilter(*MANAGEMENT_ROLES))
async def view_expenses(callback: CallbackQuery, session) -> None:
    order_id = int(callback.data.split(":")[1])
    exp_svc = ExpenseService(session)
    expenses = await exp_svc.get_by_order(order_id)
    total = await exp_svc.total_by_order(order_id)
    if not expenses:
        await callback.answer("📋 Bu zakaz uchun xarajat kiritilmagan.", show_alert=True)
        return
    lines = [f"💸 <b>Xarajatlar</b> (jami: {float(total):,.0f} so'm):\n"]
    from app.db.models import ExpenseType
    for e in expenses:
        label = EXPENSE_LABELS.get(e.expense_type, e.expense_type.value)
        date = e.created_at.strftime("%d.%m")
        lines.append(f"• {label}: <b>{float(e.amount):,.0f}</b>  [{date}]{' — ' + e.description if e.description else ''}")
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    back = InlineKeyboardBuilder()
    back.button(text="⬅️ Orqaga", callback_data=f"admin_view_order:{order_id}")
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=back.as_markup()
    )
    await callback.answer()


# ── Payment update FSM ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("order_payment:"), RoleFilter(*MANAGEMENT_ROLES))
async def payment_menu(callback: CallbackQuery) -> None:
    order_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "💵 <b>To'lovni yangilash</b>\n\nNimani qilmoqchisiz?",
        reply_markup=get_payment_update_keyboard(order_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("payment_enter:"), RoleFilter(*MANAGEMENT_ROLES))
async def payment_enter_start(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(PaymentUpdateStates.entering_amount)
    await callback.message.edit_text(
        "💵 To'lov summasini kiriting (so'm):\nMisol: <code>5000000</code>"
    )
    await callback.answer()


@router.message(PaymentUpdateStates.entering_amount, RoleFilter(*MANAGEMENT_ROLES))
async def payment_amount(message: Message, state: FSMContext, user: User, session, lang: str) -> None:
    raw = (message.text or "").strip().replace(" ", "").replace(",", "")
    try:
        amount = Decimal(raw)
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Noto'g'ri summa. Raqam kiriting:")
        return

    data = await state.get_data()
    await state.clear()
    order_id = data["order_id"]

    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await message.answer("❌ Zakaz topilmadi.")
        return

    order.advance_paid = (order.advance_paid or Decimal("0")) + amount
    if order.total_price:
        order.debt = max(Decimal("0"), order.total_price - order.advance_paid)
    await session.flush()

    await message.answer(
        f"✅ <b>To'lov kiritildi!</b>\n\n"
        f"Zakaz: #{order.order_number}\n"
        f"💵 Qo'shildi: {float(amount):,.0f} so'm\n"
        f"💰 Jami to'langan: {float(order.advance_paid):,.0f} so'm\n"
        f"💳 Qarz: {float(order.debt):,.0f} so'm",
        reply_markup=get_main_menu(user.role, lang),
    )


@router.callback_query(F.data.startswith("payment_full:"), RoleFilter(*MANAGEMENT_ROLES))
async def payment_full(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await callback.answer("❌ Zakaz topilmadi.", show_alert=True)
        return
    if order.total_price:
        order.advance_paid = order.total_price
        order.debt = Decimal("0")
    await order_svc.update_status(order_id, OrderStatus.DONE, user.id)
    await callback.message.edit_text(
        f"✅ <b>To'liq to'landi va yakunlandi!</b>\n\n"
        f"Zakaz: #{order.order_number}\n"
        f"💰 {float(order.total_price or 0):,.0f} so'm to'liq qabul qilindi."
    )
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(user.role, lang))
    await callback.answer("✅ Yakunlandi!")
