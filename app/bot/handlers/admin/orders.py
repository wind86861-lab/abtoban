from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.filters import RoleFilter
from app.bot.i18n.core import location_link
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu
from app.bot.keyboards.order import (
    get_admin_order_detail_keyboard,
    get_asphalt_categories_keyboard,
    get_asphalt_keyboard,
    get_asphalt_subcategories_keyboard,
    get_order_confirm_keyboard,
    get_regions_keyboard,
    get_status_selection_keyboard,
    get_tumanlar_keyboard,
    get_viloyatlar_keyboard,
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
from app.services.usta_service import UstaService
from app.services.user_service import UserService
from app.bot.keyboards.finance import get_payment_update_keyboard
from app.bot.keyboards.usta import get_ustas_for_reassignment_keyboard
from app.bot.states.finance import PaymentUpdateStates

router = Router()

PER_PAGE = 10


def _fmt_order_detail(order, viewer_role=None) -> str:
    """Format order detail for admin view (full info with all contacts)."""
    from app.bot.handlers._order_view import format_order_full
    from app.db.models import UserRole
    role = viewer_role or UserRole.ADMIN
    return format_order_full(order, role, "uz_lat")


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

    # Notify client about status change
    if order_full and order_full.client:
        from app.bot.loader import bot
        from app.bot.i18n import get_lang as _gl, t
        try:
            cl = _gl(order_full.client)
            await bot.send_message(
                order_full.client.telegram_id,
                t("client_status_changed_notify", cl,
                  number=order_full.order_number,
                  status=status_label),
            )
        except Exception:
            pass

    await callback.message.edit_text(
        _fmt_order_detail(order_full),
        reply_markup=get_admin_order_detail_keyboard(order_id),
    )


# ── Change usta (admin) ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("change_usta:"), RoleFilter(*MANAGEMENT_ROLES))
async def admin_change_usta_prompt(callback: CallbackQuery, user: User, session) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await callback.answer("❌ Zakaz topilmadi", show_alert=True)
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


@router.callback_query(F.data.startswith("reassign_usta:"), RoleFilter(*MANAGEMENT_ROLES))
async def admin_do_reassign_usta(callback: CallbackQuery, user: User, session) -> None:
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
    from app.bot.i18n import get_lang as _gl, t
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


@router.callback_query(F.data.startswith("back_order_detail:"), RoleFilter(*MANAGEMENT_ROLES))
async def admin_back_to_order_detail(callback: CallbackQuery, session) -> None:
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
        user_svc2 = UserService(session)
        viloyatlar = await user_svc2.get_viloyatlar()
        if viloyatlar:
            await state.set_state(AdminOrderCreateStates.selecting_viloyat)
            await message.answer(
                f"✅ Klient topildi: <b>{found_user.full_name or 'Nomsiz'}</b>\n\n"
                f"2/6 — Viloyatni tanlang:",
                reply_markup=get_viloyatlar_keyboard(viloyatlar),
            )
        else:
            await state.set_state(AdminOrderCreateStates.entering_address)
            await message.answer(
                f"✅ Klient topildi: <b>{found_user.full_name or 'Nomsiz'}</b>\n\n"
                f"3/6 — Manzilni kiriting:",
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
    user_svc2 = UserService(session)
    viloyatlar = await user_svc2.get_viloyatlar()
    if viloyatlar:
        await state.set_state(AdminOrderCreateStates.selecting_viloyat)
        await message.answer(
            f"✅ Klient yaratildi: <b>{name}</b>\n\n"
            f"2/6 — Viloyatni tanlang:",
            reply_markup=get_viloyatlar_keyboard(viloyatlar),
        )
    else:
        await state.set_state(AdminOrderCreateStates.entering_address)
        await message.answer(
            f"✅ Klient yaratildi: <b>{name}</b>\n\n"
            f"3/6 — Manzilni kiriting:",
            reply_markup=get_cancel_keyboard(),
        )


@router.callback_query(AdminOrderCreateStates.selecting_viloyat, F.data.startswith("viloyat:"), RoleFilter(*MANAGEMENT_ROLES))
async def admin_order_viloyat(callback: CallbackQuery, state: FSMContext, session) -> None:
    try:
        viloyat_id = int(callback.data.split(":")[1])
        await state.update_data(viloyat_id=viloyat_id)
        user_svc = UserService(session)
        tumanlar = await user_svc.get_tumanlar(viloyat_id)
        if not tumanlar:
            await state.set_state(AdminOrderCreateStates.entering_address)
            await callback.message.edit_text(
                "✅ Viloyat tanlandi!\n\n"
                "3/6 — Manzilni kiriting:",
            )
        else:
            await state.set_state(AdminOrderCreateStates.selecting_tuman)
            await callback.message.edit_text(
                "✅ Viloyat tanlandi!\n\n🏘 Tumanni tanlang:",
                reply_markup=get_tumanlar_keyboard(tumanlar),
            )
        await callback.answer()
    except Exception as e:
        print(f"Error in admin viloyat select: {e}")
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)


@router.callback_query(AdminOrderCreateStates.selecting_tuman, F.data.startswith("tuman:"), RoleFilter(*MANAGEMENT_ROLES))
async def admin_order_tuman(callback: CallbackQuery, state: FSMContext) -> None:
    tuman_id = int(callback.data.split(":")[1])
    await state.update_data(tuman_id=tuman_id)
    await state.set_state(AdminOrderCreateStates.entering_address)
    await callback.message.edit_text(
        "✅ Tuman tanlandi!\n\n"
        "3/6 — Manzilni kiriting:",
    )
    await callback.answer()


@router.message(AdminOrderCreateStates.entering_address, RoleFilter(*MANAGEMENT_ROLES))
async def admin_order_address(message: Message, state: FSMContext) -> None:
    address = (message.text or "").strip()
    if len(address) < 5:
        await message.answer("❌ Manzil juda qisqa:")
        return
    await state.update_data(address=address)
    await state.set_state(AdminOrderCreateStates.entering_area)
    await message.answer(
        "4/6 — Maydon hajmini kiriting (m²):\nMisol: <code>500</code>",
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
    from app.services.category_service import CategoryService
    cat_svc = CategoryService(session)
    categories = await cat_svc.get_all_categories()
    if categories:
        await state.set_state(AdminOrderCreateStates.selecting_asphalt_category)
        await message.answer("5/6 — Kategoriyani tanlang:", reply_markup=get_asphalt_categories_keyboard(categories))
    else:
        asphalt_svc = AsphaltService(session)
        types = await asphalt_svc.get_all_active()
        if not types:
            await message.answer("⚠️ Asfalt turlari yo'q. Avval sozlamalarda qo'shing.")
            await state.clear()
            return
        await state.set_state(AdminOrderCreateStates.selecting_asphalt)
        await message.answer("5/6 — Asfalt turini tanlang:", reply_markup=get_asphalt_keyboard(types))


@router.callback_query(AdminOrderCreateStates.selecting_asphalt_category, F.data.startswith("asfcat:"))
async def admin_order_select_category(callback: CallbackQuery, state: FSMContext, session) -> None:
    category_id = int(callback.data.split(":")[1])
    from app.services.category_service import CategoryService
    cat_svc = CategoryService(session)
    subcategories = await cat_svc.get_subcategories_by_category(category_id)
    if subcategories:
        await state.set_state(AdminOrderCreateStates.selecting_asphalt_subcategory)
        await callback.message.edit_text("Sub-kategoriyani tanlang:", reply_markup=get_asphalt_subcategories_keyboard(subcategories, category_id))
    else:
        asphalt_svc = AsphaltService(session)
        types = await asphalt_svc.get_all_active()
        await state.set_state(AdminOrderCreateStates.selecting_asphalt)
        await callback.message.edit_text("Asfalt turini tanlang:", reply_markup=get_asphalt_keyboard(types))
    await callback.answer()


@router.callback_query(AdminOrderCreateStates.selecting_asphalt_subcategory, F.data.startswith("asfsubcat:"))
async def admin_order_select_subcategory(callback: CallbackQuery, state: FSMContext, session) -> None:
    subcategory_id = int(callback.data.split(":")[1])
    from app.services.category_service import CategoryService
    cat_svc = CategoryService(session)
    materials = await cat_svc.get_materials_by_subcategory(subcategory_id)
    if not materials:
        await callback.answer("⚠️ Bu sub-kategoriyada material yo'q", show_alert=True)
        return
    await state.set_state(AdminOrderCreateStates.selecting_asphalt)
    await callback.message.edit_text("Asfalt turini tanlang:", reply_markup=get_asphalt_keyboard(materials))
    await callback.answer()


@router.callback_query(AdminOrderCreateStates.selecting_asphalt_subcategory, F.data.startswith("asfcat_back:"))
async def admin_order_back_to_categories(callback: CallbackQuery, state: FSMContext, session) -> None:
    from app.services.category_service import CategoryService
    cat_svc = CategoryService(session)
    categories = await cat_svc.get_all_categories()
    await state.set_state(AdminOrderCreateStates.selecting_asphalt_category)
    await callback.message.edit_text("Kategoriyani tanlang:", reply_markup=get_asphalt_categories_keyboard(categories))
    await callback.answer()


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
        f"{location_link(data.get('latitude'), data.get('longitude'))}"
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
        region_id=data.get("region_id"),
        viloyat_id=data.get("viloyat_id"),
        tuman_id=data.get("tuman_id"),
    )

    # Notify group
    from app.bot.loader import bot
    from app.bot.utils.group_notify import notify_new_order
    await notify_new_order(bot, order)

    # Notify masters
    user_svc = UserService(session)
    masters = await user_svc.get_all(role=UserRole.MASTER)
    notify_text = (
        f"🆕 <b>Yangi zakaz (admin tomonidan)!</b>\n\n"
        f"🔢 #{order.order_number}\n"
        f"👤 {data['client_name']} | {data['client_phone']}\n"
        f"📍 {order.address}\n"
        f"{location_link(order.latitude, order.longitude)}"
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
        f"📍 Manzil: {order.address}\n"
        f"{location_link(order.latitude, order.longitude)}"
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


@router.callback_query(F.data.startswith("admin_close_order:"), RoleFilter(*MANAGEMENT_ROLES))
async def admin_close_order(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await callback.answer("❌ Zakaz topilmadi.", show_alert=True)
        return
    if order.status == OrderStatus.DONE:
        await callback.answer("✅ Zakaz allaqachon yopilgan.", show_alert=True)
        return
    await order_svc.update_status(order_id, OrderStatus.DONE, user.id)
    order = await order_svc.get_by_id_full(order_id)
    from app.bot.loader import bot as _bot
    from app.bot.utils.group_notify import notify_order_done
    await notify_order_done(_bot, order)
    await callback.message.edit_text(
        callback.message.text + "\n\n🔒 <b>Zakaz yopildi!</b>",
    )
    await callback.answer("✅ Zakaz yopildi!")


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
