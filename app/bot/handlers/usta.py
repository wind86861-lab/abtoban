from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.filters import RoleFilter
from app.bot.i18n import t, ALL_BUTTON_TEXTS
from app.bot.i18n.core import location_link
from app.bot.keyboards.finance import (
    get_active_orders_for_material_keyboard,
    get_exp_mat_categories_keyboard,
    get_exp_mat_subcategories_keyboard,
    get_exp_mat_types_keyboard,
    get_mat_req_categories_keyboard,
    get_mat_req_subcategories_keyboard,
    get_mat_req_types_keyboard,
    get_material_confirm_keyboard,
    get_skip_notes_keyboard,
    get_usta_expense_type_keyboard,
    get_usta_orders_for_expense_keyboard,
)
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu
from app.bot.keyboards.usta import (
    get_usta_complete_confirm_keyboard,
    get_usta_my_orders_keyboard,
    get_usta_notification_keyboard,
    get_usta_order_detail_keyboard,
)
from app.bot.states.finance import ExpenseAddStates, MaterialRequestStates
from app.db.models import ORDER_STATUS_LABELS, OrderStatus, User, UserRole
from app.services.expense_service import EXPENSE_LABELS, ExpenseService
from app.services.asphalt_service import AsphaltService
from app.services.category_service import CategoryService
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
    # Filter out completed/cancelled
    orders = [o for o in orders if o.status not in (OrderStatus.DONE, OrderStatus.CANCELLED)]

    if not orders:
        await message.answer(t("usta_no_orders", lang))
        return

    await message.answer(
        t("usta_orders_list", lang, count=len(orders)),
        reply_markup=get_usta_my_orders_keyboard(orders),
    )


@router.callback_query(F.data == "usta_my_orders")
async def usta_my_orders_cb(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_usta(user.id)
    orders = [o for o in orders if o.status not in (OrderStatus.DONE, OrderStatus.CANCELLED)]
    if not orders:
        await callback.message.edit_text(t("usta_no_orders", lang))
    else:
        await callback.message.edit_text(
            t("usta_orders_list", lang, count=len(orders)),
            reply_markup=get_usta_my_orders_keyboard(orders),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("usta_view_mine:"))
async def usta_view_mine(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order or order.usta_id != user.id:
        await callback.answer(t("order_not_found", lang), show_alert=True)
        return

    from app.bot.handlers._order_view import format_order_full
    text = format_order_full(order, user.role, lang)
    await callback.message.edit_text(
        text,
        reply_markup=get_usta_order_detail_keyboard(order_id, order.status.value),
    )
    await callback.answer()


# ── Complete task flow ────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("usta_complete:"))
async def usta_complete_prompt(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order or order.usta_id != user.id:
        await callback.answer(t("order_not_found", lang), show_alert=True)
        return
    if order.status not in (OrderStatus.CONFIRMED, OrderStatus.IN_WORK):
        await callback.answer(t("invalid_status", lang), show_alert=True)
        return

    text = (
        f"\u2705 <b>Ishni tugatishni tasdiqlang</b>\n\n"
        f"\ud83d\udd22 #{order.order_number}\n"
        f"\ud83d\udccd {order.address or '\u2014'}\n"
        f"\ud83d\udcd0 {order.area_m2 or '?'} m\u00b2\n"
        f"\ud83d\udcb0 Usta haqi: <b>{float(order.usta_wage or 0):,.0f} so'm</b>\n\n"
        f"Bu zakaz tugatilganini tasdiqlaysizmi?\n"
        f"<i>Tasdiqlasangiz Admin, Master va Klientga bildirishnoma yuboriladi.</i>"
    )
    await callback.message.edit_text(text, reply_markup=get_usta_complete_confirm_keyboard(order_id))
    await callback.answer()


@router.callback_query(F.data.startswith("usta_complete_confirm:"))
async def usta_complete_confirm(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order or order.usta_id != user.id:
        await callback.answer(t("order_not_found", lang), show_alert=True)
        return
    if order.status == OrderStatus.DONE:
        await callback.answer("\u26a0\ufe0f Allaqachon tugatilgan", show_alert=True)
        return
    if order.status not in (OrderStatus.CONFIRMED, OrderStatus.IN_WORK):
        await callback.answer(t("invalid_status", lang), show_alert=True)
        return

    # Update status
    await order_svc.update_status(order_id, OrderStatus.DONE, user.id)
    # Re-fetch with relationships
    order = await order_svc.get_by_id_full(order_id)

    # Acknowledge to usta
    await callback.message.edit_text(
        f"\u2705 <b>Zakaz tugatildi!</b>\n\n"
        f"\ud83d\udd22 #{order.order_number}\n"
        f"\ud83d\udcc5 {order.completed_at.strftime('%d.%m.%Y %H:%M') if order.completed_at else '\u2014'}\n\n"
        f"Admin, Master va Klientga bildirishnoma yuborildi."
    )
    await callback.answer("\u2705 Tugatildi")

    # Send comprehensive notifications
    await _send_completion_notifications(session, order)


async def _send_completion_notifications(session, order) -> None:
    """Send completion notification to admins (full report), master, and client."""
    from app.bot.loader import bot
    from app.bot.handlers._order_view import format_order_completion_report
    from app.services.expense_service import ExpenseService
    from app.services.user_service import UserService

    # Load expenses
    try:
        expenses = await ExpenseService(session).get_by_order(order.id)
    except Exception:
        expenses = []

    user_svc = UserService(session)
    super_admins = await user_svc.get_all(role=UserRole.SUPER_ADMIN)
    if order.region_id:
        region_admins = await user_svc.get_by_role_and_region(UserRole.ADMIN, order.region_id)
        region_admins += await user_svc.get_by_role_and_region(UserRole.HELPER_ADMIN, order.region_id)
        if not region_admins:
            region_admins = await user_svc.get_all(role=UserRole.ADMIN)
    else:
        region_admins = await user_svc.get_all(role=UserRole.ADMIN)
    admin_targets = list({u.id: u for u in list(super_admins) + list(region_admins)}.values())

    # Notify admins
    for admin in admin_targets:
        try:
            text = format_order_completion_report(order, UserRole.ADMIN, expenses)
            await bot.send_message(admin.telegram_id, text)
        except Exception:
            pass

    # Notify master
    if order.master:
        try:
            text = format_order_completion_report(order, UserRole.MASTER, expenses)
            await bot.send_message(order.master.telegram_id, text)
        except Exception:
            pass

    # Notify client
    if order.client:
        try:
            text = format_order_completion_report(order, UserRole.KLIENT, expenses)
            await bot.send_message(order.client.telegram_id, text)
        except Exception:
            pass


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

    from app.bot.handlers._order_view import format_order_full
    text = "✅ <b>Tayinlash qabul qilindi!</b>\n\n" + format_order_full(order, user.role, lang)

    await callback.message.edit_text(
        text,
        reply_markup=get_usta_order_detail_keyboard(order_id, order.status.value),
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
async def material_pick_order(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    await state.update_data(order_id=order_id)
    await state.set_state(MaterialRequestStates.selecting_category)

    cat_svc = CategoryService(session)
    categories = await cat_svc.get_all_categories()
    if not categories:
        # Skip category selection if none configured
        await state.set_state(MaterialRequestStates.entering_tonnes)
        await callback.message.edit_text(t("material_enter_tonnes", lang))
    else:
        await callback.message.edit_text(
            t("material_select_category", lang),
            reply_markup=get_mat_req_categories_keyboard(categories, lang),
        )
    await callback.answer()


@router.callback_query(MaterialRequestStates.selecting_category, F.data.startswith("mat_cat:"))
async def mat_req_pick_category(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    cat_id = int(callback.data.split(":")[1])
    await state.update_data(mat_category_id=cat_id)
    await state.set_state(MaterialRequestStates.selecting_subcategory)

    cat_svc = CategoryService(session)
    subcats = await cat_svc.get_subcategories_by_category(cat_id)
    if not subcats:
        # No subcategories — skip to type
        asphalt_svc = AsphaltService(session)
        types = await asphalt_svc.get_all_active()
        await state.set_state(MaterialRequestStates.selecting_type)
        await callback.message.edit_text(
            t("material_select_type", lang),
            reply_markup=get_mat_req_types_keyboard(types, 0, lang),
        )
    else:
        await callback.message.edit_text(
            t("material_select_subcategory", lang),
            reply_markup=get_mat_req_subcategories_keyboard(subcats, cat_id, lang),
        )
    await callback.answer()


@router.callback_query(MaterialRequestStates.selecting_subcategory, F.data.startswith("mat_subcat:"))
async def mat_req_pick_subcategory(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    subcat_id = int(callback.data.split(":")[1])
    await state.update_data(mat_subcategory_id=subcat_id)
    await state.set_state(MaterialRequestStates.selecting_type)

    cat_svc = CategoryService(session)
    types = await cat_svc.get_materials_by_subcategory(subcat_id)
    if not types:
        # No types in this subcategory
        await callback.answer(t("material_no_types", lang), show_alert=True)
        return
    await callback.message.edit_text(
        t("material_select_type", lang),
        reply_markup=get_mat_req_types_keyboard(types, subcat_id, lang),
    )
    await callback.answer()


@router.callback_query(MaterialRequestStates.selecting_type, F.data.startswith("mat_type:"))
async def mat_req_pick_type(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    type_id = int(callback.data.split(":")[1])
    asphalt_svc = AsphaltService(session)
    mat_type = await asphalt_svc.get_by_id(type_id)
    type_name = mat_type.name if mat_type else f"#{type_id}"
    await state.update_data(asphalt_type_id=type_id, asphalt_type_name=type_name)
    await state.set_state(MaterialRequestStates.entering_tonnes)
    await callback.message.edit_text(t("material_enter_tonnes", lang))
    await callback.answer()


@router.callback_query(F.data.startswith("mat_cat_back:"))
async def mat_req_cat_back(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    cat_svc = CategoryService(session)
    categories = await cat_svc.get_all_categories()
    await state.set_state(MaterialRequestStates.selecting_category)
    await callback.message.edit_text(
        t("material_select_category", lang),
        reply_markup=get_mat_req_categories_keyboard(categories, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mat_subcat_back:"))
async def mat_req_subcat_back(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    subcat_id = int(callback.data.split(":")[1])
    cat_svc = CategoryService(session)
    subcat = await cat_svc.get_subcategory_by_id(subcat_id)
    if subcat:
        await state.set_state(MaterialRequestStates.selecting_subcategory)
        subcats = await cat_svc.get_subcategories_by_category(subcat.category_id)
        await callback.message.edit_text(
            t("material_select_subcategory", lang),
            reply_markup=get_mat_req_subcategories_keyboard(subcats, subcat.category_id, lang),
        )
    await callback.answer()


@router.callback_query(F.data == "mat_req_cancel")
async def mat_req_cancel(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await callback.message.edit_text(t("cancelled", lang))
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
    mat_type = data.get('asphalt_type_name', '—')
    await message.answer(
        t("material_summary", lang,
          mat_type=mat_type,
          tonnes=data['amount_tonnes'],
          notes=notes or '—'),
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
        asphalt_type_id=data.get("asphalt_type_id"),
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


# ── Expense entry FSM (Qo'shimcha narx) ──────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_add_expense", set())))
async def usta_expense_start(message: Message, user: User, session, lang: str) -> None:
    order_svc = OrderService(session)
    orders = await order_svc.get_by_usta(user.id)
    active = [o for o in orders if o.status in (OrderStatus.CONFIRMED, OrderStatus.IN_WORK)]
    if not active:
        await message.answer(t("expense_no_active", lang))
        return
    await message.answer(
        t("expense_start", lang),
        reply_markup=get_usta_orders_for_expense_keyboard(active),
    )


@router.callback_query(F.data.startswith("usta_exp_order:"))
async def usta_expense_pick_order(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    from app.db.models import ExpenseType
    order_id = int(callback.data.split(":")[1])
    # Simplified flow: no type/category selection — always EXTRA,
    # ask amount first, then require a description.
    await state.update_data(order_id=order_id, expense_type=ExpenseType.EXTRA.value)
    await state.set_state(ExpenseAddStates.entering_amount)
    await callback.message.edit_text(t("expense_enter_amount", lang))
    await callback.answer()


# ── Shared expense-material category/subcategory/type callbacks ────────────────
# (No role filter on callbacks in aiogram 3, so these serve both usta and master)

@router.callback_query(ExpenseAddStates.selecting_mat_category, F.data.startswith("exp_mat_cat:"))
async def exp_mat_pick_category(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    cat_id = int(callback.data.split(":")[1])
    await state.update_data(exp_mat_category_id=cat_id)
    cat_svc = CategoryService(session)
    subcats = await cat_svc.get_subcategories_by_category(cat_id)
    if not subcats:
        asphalt_svc = AsphaltService(session)
        types = await asphalt_svc.get_all_active()
        await state.set_state(ExpenseAddStates.selecting_mat_type)
        await callback.message.edit_text(
            t("expense_mat_select_type", lang),
            reply_markup=get_exp_mat_types_keyboard(types, 0, lang),
        )
    else:
        await state.set_state(ExpenseAddStates.selecting_mat_subcategory)
        await callback.message.edit_text(
            t("expense_mat_select_subcategory", lang),
            reply_markup=get_exp_mat_subcategories_keyboard(subcats, cat_id, lang),
        )
    await callback.answer()


@router.callback_query(ExpenseAddStates.selecting_mat_subcategory, F.data.startswith("exp_mat_subcat:"))
async def exp_mat_pick_subcategory(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    subcat_id = int(callback.data.split(":")[1])
    await state.update_data(exp_mat_subcategory_id=subcat_id)
    cat_svc = CategoryService(session)
    types = await cat_svc.get_materials_by_subcategory(subcat_id)
    if not types:
        await callback.answer(t("material_no_types", lang), show_alert=True)
        return
    await state.set_state(ExpenseAddStates.selecting_mat_type)
    await callback.message.edit_text(
        t("expense_mat_select_type", lang),
        reply_markup=get_exp_mat_types_keyboard(types, subcat_id, lang),
    )
    await callback.answer()


@router.callback_query(ExpenseAddStates.selecting_mat_type, F.data.startswith("exp_mat_type:"))
async def exp_mat_pick_type(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    type_id = int(callback.data.split(":")[1])
    asphalt_svc = AsphaltService(session)
    mat_type = await asphalt_svc.get_by_id(type_id)
    type_name = mat_type.name if mat_type else f"#{type_id}"
    price_per_m2 = float(mat_type.price_per_m2) if mat_type and mat_type.price_per_m2 else 0
    await state.update_data(
        exp_mat_type_id=type_id,
        exp_mat_type_name=type_name,
        exp_mat_price_per_m2=str(price_per_m2),
    )
    await state.set_state(ExpenseAddStates.entering_mat_volume)
    await callback.message.edit_text(
        t("expense_mat_enter_volume", lang, name=type_name, price=f"{price_per_m2:,.0f}")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("exp_mat_cat_back:"))
async def exp_mat_cat_back(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    cat_svc = CategoryService(session)
    categories = await cat_svc.get_all_categories()
    await state.set_state(ExpenseAddStates.selecting_mat_category)
    await callback.message.edit_text(
        t("expense_mat_select_category", lang),
        reply_markup=get_exp_mat_categories_keyboard(categories, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("exp_mat_subcat_back:"))
async def exp_mat_subcat_back(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    subcat_id = int(callback.data.split(":")[1])
    cat_svc = CategoryService(session)
    subcat = await cat_svc.get_subcategory_by_id(subcat_id)
    if subcat:
        await state.set_state(ExpenseAddStates.selecting_mat_subcategory)
        subcats = await cat_svc.get_subcategories_by_category(subcat.category_id)
        await callback.message.edit_text(
            t("expense_mat_select_subcategory", lang),
            reply_markup=get_exp_mat_subcategories_keyboard(subcats, subcat.category_id, lang),
        )
    await callback.answer()


@router.callback_query(F.data == "exp_mat_cancel")
async def exp_mat_cancel(callback: CallbackQuery, state: FSMContext, user: User, lang: str) -> None:
    await state.clear()
    await callback.message.edit_text(t("expense_cancelled", lang))
    role = user.role if user else UserRole.USTA
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(role, lang))
    await callback.answer()


@router.message(ExpenseAddStates.entering_mat_volume)
async def usta_expense_mat_volume(message: Message, state: FSMContext, lang: str) -> None:
    raw = (message.text or "").strip().replace(",", ".").replace(" ", "")
    try:
        volume = Decimal(raw)
        if volume <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await message.answer(t("expense_mat_invalid_volume", lang))
        return
    data = await state.get_data()
    price_per_m2 = Decimal(str(data.get("exp_mat_price_per_m2", "0")))
    amount = price_per_m2 * volume
    type_name = data.get("exp_mat_type_name", "—")
    await state.update_data(amount=str(amount), exp_mat_volume=str(volume))
    await state.set_state(ExpenseAddStates.entering_description)
    await message.answer(
        t("expense_mat_auto_amount", lang,
          name=type_name,
          volume=volume,
          price=f"{float(price_per_m2):,.0f}",
          amount=f"{float(amount):,.0f}"),
        reply_markup=get_cancel_keyboard(lang),
    )


@router.message(ExpenseAddStates.entering_amount)
async def usta_expense_amount(message: Message, state: FSMContext, lang: str) -> None:
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
async def usta_expense_description(
    message: Message, state: FSMContext, user: User, session, lang: str
) -> None:
    text = (message.text or "").strip()
    # Description is required — reject empty or skip.
    if not text or text.startswith("⏩"):
        await message.answer(t("expense_desc_required", lang))
        return
    description = text
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
        reply_markup=get_main_menu(UserRole.USTA, lang),
    )


@router.callback_query(ExpenseAddStates.selecting_type, F.data == "usta_exp_cancel")
async def usta_expense_cancel(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await callback.message.edit_text(t("expense_cancelled", lang))
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.USTA, lang))
    await callback.answer()
