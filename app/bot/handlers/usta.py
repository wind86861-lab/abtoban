from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters import RoleFilter
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

@router.message(F.text.in_({"📋 Mening zakazlarim", "✅ Zakazni qabul qilish"}))
async def my_orders(message: Message, user: User, session) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_usta(user.id)

    if not orders:
        await message.answer(
            "📋 <b>Mening zakazlarim</b>\n\n"
            "Sizga hali zakaz biriktirilmagan.\n"
            "Bildirishnoma kelganda avtomatik ko'rinadi."
        )
        return

    lines = [f"📋 <b>Mening zakazlarim</b> ({len(orders)} ta):\n"]
    for o in orders:
        status_label = ORDER_STATUS_LABELS.get(o.status, o.status.value)
        asphalt = o.asphalt_type.name if o.asphalt_type else "—"
        wage = f"{float(o.usta_wage):,.0f} so'm" if o.usta_wage else "—"
        lines.append(
            f"\n🔢 <code>{o.order_number}</code> — {status_label}\n"
            f"  📍 {o.address or '—'}\n"
            f"  📐 {o.area_m2 or '?'} m²  🏗 {asphalt}\n"
            f"  💰 Haqi: {wage}"
        )
    await message.answer("\n".join(lines))


@router.callback_query(F.data == "usta_my_orders")
async def usta_my_orders_cb(callback: CallbackQuery, user: User, session) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_usta(user.id)
    if not orders:
        await callback.message.edit_text("📋 Sizga biriktirilgan zakazlar yo'q.")
    else:
        lines = [f"📋 <b>Mening zakazlarim</b> ({len(orders)} ta):\n"]
        for o in orders:
            st = ORDER_STATUS_LABELS.get(o.status, o.status.value)
            lines.append(f"• <code>{o.order_number}</code> — {st}")
        await callback.message.edit_text("\n".join(lines))
    await callback.answer()


# ── Accept assignment ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("accept_assignment:"))
async def accept_assignment(callback: CallbackQuery, user: User, session) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)

    if not order:
        await callback.answer("❌ Zakaz topilmadi.", show_alert=True)
        return
    if order.usta_id != user.id:
        await callback.answer(
            "❌ Bu zakaz sizga tayinlanmagan yoki allaqachon boshqa usta qabul qildi.",
            show_alert=True,
        )
        return

    asphalt = order.asphalt_type.name if order.asphalt_type else "—"
    wage = float(order.usta_wage) if order.usta_wage else 0
    work_date = order.work_date.strftime("%d.%m.%Y") if order.work_date else "—"

    await callback.message.edit_text(
        f"✅ <b>Zakaz qabul qilindi!</b>\n\n"
        f"🔢 #{order.order_number}\n"
        f"📍 {order.address or '—'}\n"
        f"📐 {order.area_m2} m²  🏗 {asphalt}\n"
        f"📅 Ish sanasi: {work_date}\n"
        f"💰 Usta haqi: {wage:,.0f} so'm",
        reply_markup=get_usta_order_detail_keyboard(order_id),
    )
    await callback.message.answer(
        "Asosiy menyu:", reply_markup=get_main_menu(UserRole.USTA)
    )
    await callback.answer("✅ Zakaz qabul qilindi!")

    # Notify master
    from app.bot.loader import bot as _bot
    if order.master:
        try:
            await _bot.send_message(
                order.master.telegram_id,
                f"✅ <b>Usta zakazni qabul qildi!</b>\n\n"
                f"Zakaz: #{order.order_number}\n"
                f"👷 Usta: {user.full_name or str(user.telegram_id)}",
            )
        except Exception:
            pass


# ── Decline assignment ────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("decline_assignment:"))
async def decline_assignment(callback: CallbackQuery, user: User, session) -> None:
    order_id = int(callback.data.split(":")[1])
    usta_svc = UstaService(session)
    order = await usta_svc.release_usta(order_id, user.id)

    if not order:
        await callback.answer(
            "❌ Zakaz topilmadi yoki sizga tegishli emas.", show_alert=True
        )
        return

    await callback.message.edit_text("❌ Zakaz rad etildi.")
    await callback.message.answer(
        "Asosiy menyu:", reply_markup=get_main_menu(UserRole.USTA)
    )
    await callback.answer("❌ Zakaz rad etildi.")

    # Notify master to re-assign
    from app.bot.loader import bot as _bot
    from app.services.order_service import OrderService as OS
    order_full = await OS(session).get_by_id_full(order_id)
    if order_full and order_full.master:
        try:
            await _bot.send_message(
                order_full.master.telegram_id,
                f"❌ <b>Usta zakazni rad etdi!</b>\n\n"
                f"Zakaz: #{order_full.order_number}\n"
                f"👷 {user.full_name or str(user.telegram_id)} rad etdi.\n\n"
                f"Yangi usta tayinlang: '👷 Usta tayinlash'",
            )
        except Exception:
            pass


# ── Material request FSM ──────────────────────────────────────────────────────

@router.message(F.text == "📦 Material so'rash")
async def material_request_start(message: Message, state: FSMContext, user: User, session) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_usta(user.id, status=None)
    active = [o for o in orders if o.status in (OrderStatus.CONFIRMED, OrderStatus.IN_WORK)]
    if not active:
        await message.answer(
            "📦 <b>Material so'rash</b>\n\n"
            "Faol zakaz yo'q. Avval zakazni qabul qiling."
        )
        return
    await state.set_state(MaterialRequestStates.selecting_order)
    await message.answer(
        "📦 <b>Material so'rash</b>\n\nQaysi zakaz uchun so'raysiz?",
        reply_markup=get_active_orders_for_material_keyboard(active),
    )


@router.callback_query(MaterialRequestStates.selecting_order, F.data.startswith("material_pick_order:"))
async def material_pick_order(callback: CallbackQuery, state: FSMContext) -> None:
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(MaterialRequestStates.entering_tonnes)
    await callback.message.edit_text(
        "📦 Kerakli material miqdorini kiriting (<b>tonna</b>):\n"
        "Misol: <code>12.5</code>"
    )
    await callback.answer()


@router.message(MaterialRequestStates.entering_tonnes)
async def material_enter_tonnes(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip().replace(",", ".")
    try:
        tonnes = Decimal(raw)
        if tonnes <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer("❌ Noto'g'ri miqdor. Musbat raqam kiriting (masalan: 12.5):")
        return
    await state.update_data(amount_tonnes=str(tonnes))
    await state.set_state(MaterialRequestStates.entering_notes)
    await message.answer(
        "📝 Izoh yoki qo'shimcha ma'lumot (ixtiyoriy):",
        reply_markup=get_skip_notes_keyboard(),
    )


@router.message(MaterialRequestStates.entering_notes)
async def material_enter_notes(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    notes = None if text.startswith("⏩") else text.strip()
    await state.update_data(notes=notes)
    await state.set_state(MaterialRequestStates.confirming)
    data = await state.get_data()
    await message.answer(
        f"📦 <b>Material so'rov xulosasi</b>\n\n"
        f"📐 Miqdor: <b>{data['amount_tonnes']} tonna</b>\n"
        f"📝 Izoh: {notes or '—'}\n\n"
        f"Yuborasizmi?",
        reply_markup=get_material_confirm_keyboard(),
    )


@router.callback_query(MaterialRequestStates.confirming, F.data == "material_confirm")
async def material_submit(callback: CallbackQuery, state: FSMContext, user: User, session) -> None:
    data = await state.get_data()
    await state.clear()

    mat_svc = MaterialService(session)
    req = await mat_svc.create(
        order_id=data["order_id"],
        usta_id=user.id,
        amount_tonnes=Decimal(data["amount_tonnes"]),
        notes=data.get("notes"),
    )

    # Notify all zavod users
    from app.bot.loader import bot
    from app.services.user_service import UserService
    user_svc = UserService(session)
    zavods = await user_svc.get_all(role=UserRole.ZAVOD)
    notify_text = (
        f"📦 <b>Yangi material so'rov!</b>\n\n"
        f"🔢 So'rov #{req.id}\n"
        f"👷 Usta: {user.full_name or str(user.telegram_id)}\n"
        f"📦 Miqdor: <b>{req.amount_tonnes} tonna</b>\n"
        f"📝 Izoh: {req.notes or '—'}"
    )
    for zavod in zavods:
        try:
            await bot.send_message(zavod.telegram_id, notify_text)
        except Exception:
            pass

    await callback.message.edit_text(
        f"✅ <b>So'rov yuborildi!</b>\n\n"
        f"📦 {req.amount_tonnes} tonna\n"
        f"Zavod narx belgilaydi va xabar beradi."
    )
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(UserRole.USTA))
    await callback.answer()


@router.callback_query(MaterialRequestStates.confirming, F.data == "material_cancel")
async def material_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("❌ So'rov bekor qilindi.")
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(UserRole.USTA))
    await callback.answer()


@router.callback_query(F.data.startswith("request_material:"))
async def request_material_cb(callback: CallbackQuery, state: FSMContext, user: User, session) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    orders = await order_svc.get_by_usta(user.id)
    active = [o for o in orders if o.status in (OrderStatus.CONFIRMED, OrderStatus.IN_WORK)]
    await state.update_data(order_id=order_id)
    await state.set_state(MaterialRequestStates.entering_tonnes)
    await callback.message.edit_text(
        "📦 Kerakli material miqdorini kiriting (<b>tonna</b>):\nMisol: <code>12.5</code>"
    )
    await callback.answer()


# ── Work history ─────────────────────────────────────────────────────────────

@router.message(F.text == "📊 Ish tarixi")
async def work_history(message: Message, user: User, session) -> None:
    order_svc = OrderService(session)
    from app.db.models import OrderStatus
    orders = await order_svc.get_by_usta(user.id, status=OrderStatus.DONE)
    if not orders:
        await message.answer("📊 <b>Ish tarixi</b>\n\nHali yakunlangan ish yo'q.")
        return
    lines = [f"📊 <b>Ish tarixi</b> ({len(orders)} ta):\n"]
    for o in orders:
        date = o.completed_at.strftime("%d.%m.%Y") if o.completed_at else "—"
        wage = f"{float(o.usta_wage):,.0f} so'm" if o.usta_wage else "—"
        lines.append(
            f"\n🔢 <code>{o.order_number}</code>\n"
            f"  📅 {date}  💰 {wage}"
        )
    await message.answer("\n".join(lines))
