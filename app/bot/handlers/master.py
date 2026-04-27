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
    get_asphalt_categories_keyboard,
    get_asphalt_keyboard,
    get_asphalt_subcategories_keyboard,
    get_confirm_summary_keyboard,
    get_extras_keyboard,
    get_keep_address_keyboard,
    get_master_my_order_keyboard,
    get_master_order_detail_keyboard,
    get_order_confirm_keyboard,
    get_orders_list_keyboard,
    get_regions_keyboard,
    get_tumanlar_keyboard,
    get_ustas_for_confirm_keyboard,
    get_viloyatlar_keyboard,
)
from app.bot.keyboards.finance import (
    get_exp_mat_categories_keyboard,
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
from app.services.category_service import CategoryService
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
async def view_new_order(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await callback.answer(t("order_not_found", lang), show_alert=True)
        return

    from app.bot.handlers._order_view import format_order_full
    text = format_order_full(order, user.role, lang)
    text += f"\n\n<i>{t('press_to_confirm', lang)}</i>"
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
# Flow: phone → name → viloyat → tuman → address → location → CREATE order →
#       transition to MasterConfirmStates for full details (area, asphalt,
#       extras, sum, advance, date, wage, commission, notes, usta).

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_add_order", set())))
async def master_create_order_start(message: Message, state: FSMContext, lang: str) -> None:
    from app.bot.keyboards.menus import get_share_contact_keyboard
    await state.set_state(MasterOrderCreateStates.entering_client_phone)
    await message.answer(
        t("master_order_start", lang),
        reply_markup=get_share_contact_keyboard(lang),
    )


@router.message(MasterOrderCreateStates.entering_client_phone)
async def master_order_client_phone(message: Message, state: FSMContext, lang: str) -> None:
    if message.text and message.text in ALL_BUTTON_TEXTS.get("btn_cancel", set()):
        await state.clear()
        await message.answer(t("action_cancelled", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
        return

    # Accept shared contact (gives phone + maybe name)
    if message.contact:
        phone = (message.contact.phone_number or "").replace("+", "").replace(" ", "").replace("-", "")
        contact_name = " ".join(filter(None, [message.contact.first_name, message.contact.last_name])).strip()
        if not phone or len(phone) < 9:
            await message.answer(t("invalid_phone", lang))
            return
        update = {"client_phone": phone}
        if contact_name:
            update["client_name"] = contact_name
        await state.update_data(**update)
        # Move to name step (let master confirm/edit name)
        await state.set_state(MasterOrderCreateStates.entering_client_name)
        prefill = f"\n\n<i>Avtomatik: {contact_name}</i>" if contact_name else ""
        await message.answer(
            t("enter_client_name", lang) + prefill,
            reply_markup=get_cancel_keyboard(lang),
        )
        return

    # Text input fallback
    text = (message.text or "").strip()
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
            await state.set_state(MasterOrderCreateStates.entering_address)
            await callback.message.edit_text(t("region_selected", lang))
            await callback.message.answer(
                t("master_create_address", lang),
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
    await state.set_state(MasterOrderCreateStates.entering_address)
    await callback.message.edit_text(t("region_selected", lang))
    await callback.message.answer(
        t("master_create_address", lang),
        reply_markup=get_cancel_keyboard(lang),
    )
    await callback.answer()


@router.message(MasterOrderCreateStates.entering_address)
async def master_order_address(message: Message, state: FSMContext, lang: str) -> None:
    from app.bot.keyboards.menus import get_share_location_keyboard
    text = (message.text or "").strip()
    if text in ALL_BUTTON_TEXTS.get("btn_cancel", set()):
        await state.clear()
        await message.answer(t("action_cancelled", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
        return
    if len(text) < 5:
        await message.answer(t("address_too_short", lang))
        return
    await state.update_data(address=text)
    await state.set_state(MasterOrderCreateStates.sharing_location)
    await message.answer(
        t("master_create_location", lang),
        reply_markup=get_share_location_keyboard(lang),
    )


@router.message(MasterOrderCreateStates.sharing_location, F.location)
async def master_order_location(message: Message, state: FSMContext, user: User, session, lang: str) -> None:
    await state.update_data(
        latitude=message.location.latitude,
        longitude=message.location.longitude,
    )
    await _master_create_finalize(message, state, user, session, lang)


@router.message(MasterOrderCreateStates.sharing_location)
async def master_order_location_text(message: Message, state: FSMContext, user: User, session, lang: str) -> None:
    text = (message.text or "").strip()
    if text in ALL_BUTTON_TEXTS.get("btn_cancel", set()):
        await state.clear()
        await message.answer(t("action_cancelled", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
        return
    if text in ALL_BUTTON_TEXTS.get("btn_skip", set()):
        await _master_create_finalize(message, state, user, session, lang)
        return
    # Anything else: prompt again
    from app.bot.keyboards.menus import get_share_location_keyboard
    await message.answer(
        t("master_create_location", lang),
        reply_markup=get_share_location_keyboard(lang),
    )


async def _master_create_finalize(message: Message, state: FSMContext, user: User, session, lang: str) -> None:
    """Create order skeleton, then transition into MasterConfirmStates for full details."""
    data = await state.get_data()
    order_svc = OrderService(session)
    order = await order_svc.create_by_master(
        master_id=user.id,
        client_name=data.get("client_name", ""),
        client_phone=data.get("client_phone", ""),
        address=data.get("address", ""),
        viloyat_id=data.get("viloyat_id"),
        tuman_id=data.get("tuman_id"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
    )
    await session.commit()

    # Show skeleton confirmation
    await message.answer(
        t("master_create_done", lang,
          number=order.order_number,
          name=data.get("client_name", "—"),
          phone=data.get("client_phone", "—"),
          address=data.get("address", "—")),
    )

    # Transition to confirm flow on the new order
    await state.clear()
    await state.update_data(
        order_id=order.id,
        existing_address=order.address or "",
        order_number=order.order_number,
    )
    await state.set_state(MasterConfirmStates.entering_area)
    await message.answer(
        t("confirm_step_area", lang, number=order.order_number),
        reply_markup=get_cancel_keyboard(lang),
    )


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
async def view_my_order(callback: CallbackQuery, user: User, session, lang: str) -> None:
    order_id = int(callback.data.split(":")[1])
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id)
    if not order:
        await callback.answer(t("order_not_found", lang), show_alert=True)
        return

    from app.bot.handlers._order_view import format_order_full
    text = format_order_full(order, user.role, lang)
    await callback.message.edit_text(
        text, reply_markup=get_master_my_order_keyboard(order_id, order.status.value)
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
async def confirm_area(message: Message, state: FSMContext, session, lang: str) -> None:
    val = _parse_decimal(message.text or "")
    if val is None or val <= 0:
        await message.answer(t("invalid_area", lang))
        return
    await state.update_data(area_m2=str(val))
    # Go to main asphalt category selection (use light query for speed)
    cat_svc = CategoryService(session)
    categories = await cat_svc.get_categories_light()
    if not categories:
        await message.answer("❌ Kategoriyalar mavjud emas. Admin bilan bog'laning.")
        return
    await state.set_state(MasterConfirmStates.selecting_main_category)
    await message.answer(
        t("confirm_step_main_cat", lang),
        reply_markup=get_asphalt_categories_keyboard(categories),
    )


# ─── Main asphalt selection handlers ───
@router.callback_query(MasterConfirmStates.selecting_main_category, F.data.startswith("asfcat:"))
async def confirm_main_cat(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    cat_id = int(callback.data.split(":")[1])
    cat_svc = CategoryService(session)
    subcats = await cat_svc.get_subcategories_light(cat_id)
    await state.update_data(main_cat_id=cat_id)
    await state.set_state(MasterConfirmStates.selecting_main_subcategory)
    await callback.message.edit_text(
        t("confirm_step_main_subcat", lang),
        reply_markup=get_asphalt_subcategories_keyboard(subcats, cat_id),
    )
    await callback.answer()


@router.callback_query(MasterConfirmStates.selecting_main_subcategory, F.data.startswith("asfsubcat:"))
async def confirm_main_subcat(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    sub_id = int(callback.data.split(":")[1])
    cat_svc = CategoryService(session)
    materials = await cat_svc.get_materials_by_subcategory(sub_id)
    if not materials:
        await callback.answer("❌ Materiallar mavjud emas", show_alert=True)
        return
    await state.update_data(main_sub_id=sub_id)
    await state.set_state(MasterConfirmStates.selecting_main_material)
    await callback.message.edit_text(
        t("confirm_step_main_mat", lang),
        reply_markup=get_asphalt_keyboard(materials, subcat_id=sub_id),
    )
    await callback.answer()


@router.callback_query(MasterConfirmStates.selecting_main_material, F.data.startswith("asfsubcat_back:"))
async def confirm_main_back_to_subcat(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    """Go back from material to subcategory selection for main asphalt."""
    data = await state.get_data()
    cat_id = data.get("main_cat_id")
    if not cat_id:
        await callback.answer("❌ Xatolik", show_alert=True)
        return
    cat_svc = CategoryService(session)
    subcats = await cat_svc.get_subcategories_light(cat_id)
    await state.set_state(MasterConfirmStates.selecting_main_subcategory)
    await callback.message.edit_text(
        t("confirm_step_main_subcat", lang),
        reply_markup=get_asphalt_subcategories_keyboard(subcats, cat_id),
    )
    await callback.answer()


@router.callback_query(MasterConfirmStates.selecting_main_subcategory, F.data.startswith("asfcat_back:"))
async def confirm_main_back_to_cat(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    """Go back from subcategory to category selection for main asphalt."""
    cat_svc = CategoryService(session)
    categories = await cat_svc.get_categories_light()
    await state.set_state(MasterConfirmStates.selecting_main_category)
    await callback.message.edit_text(
        t("confirm_step_main_cat", lang),
        reply_markup=get_asphalt_categories_keyboard(categories),
    )
    await callback.answer()


@router.callback_query(MasterConfirmStates.selecting_main_material, F.data.startswith("asphalt:"))
async def confirm_main_material(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    mat_id = int(callback.data.split(":")[1])
    cat_svc = CategoryService(session)
    material = await cat_svc.get_material_by_id(mat_id)
    if not material:
        await callback.answer(t("asphalt_not_found", lang), show_alert=True)
        return

    data = await state.get_data()
    area = Decimal(data["area_m2"])
    subtotal = area * material.price_per_m2

    # Store main asphalt info
    await state.update_data(
        main_asphalt_id=mat_id,
        main_asphalt_name=material.name,
        main_asphalt_price=str(material.price_per_m2),
        main_asphalt_cost=str(material.cost_price_per_m2 or 0),
        main_subtotal=str(subtotal),
    )
    # Initialize extras list
    await state.update_data(extras=[], extras_total="0")

    await state.set_state(MasterConfirmStates.adding_extras)
    await _show_extras_step(callback.message, state, lang, edit=True)
    await callback.answer()


async def _show_extras_step(message, state: FSMContext, lang: str, edit: bool = False) -> None:
    data = await state.get_data()
    area = Decimal(data["area_m2"])
    main_name = data.get("main_asphalt_name", "—")
    main_sub = float(data.get("main_subtotal", 0))
    extras = data.get("extras", [])
    extras_total = sum(float(e.get("subtotal", 0)) for e in extras)
    calc_total = main_sub + extras_total

    extras_text = ""
    for i, e in enumerate(extras, 1):
        extras_text += f"➕ {i}. {e['name']}: {e.get('area_m2', area)} m² × {e['price_per_m2']:,.0f} = {float(e['subtotal']):,.0f} so'm\n"

    text = t("confirm_step_extras", lang,
             area=area,
             main_name=main_name,
             main_sub=f"{main_sub:,.0f}",
             extras_text=extras_text,
             calc_total=f"{calc_total:,.0f}")

    if edit:
        await message.edit_text(text, reply_markup=get_extras_keyboard())
    else:
        await message.answer(text, reply_markup=get_extras_keyboard())


# ─── Extra services handlers ───
@router.callback_query(MasterConfirmStates.adding_extras, F.data == "add_extra_service")
async def add_extra_service(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    data = await state.get_data()
    cat_svc = CategoryService(session)
    categories = await cat_svc.get_categories_light()
    await state.set_state(MasterConfirmStates.selecting_extra_category)
    await callback.message.edit_text(
        t("confirm_step_extra_cat", lang, area=data.get("area_m2", "—")),
        reply_markup=get_asphalt_categories_keyboard(categories),
    )
    await callback.answer()


@router.callback_query(MasterConfirmStates.adding_extras, F.data == "extras_done")
async def extras_done(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    extras = data.get("extras", [])
    extras_total = sum(float(e.get("subtotal", 0)) for e in extras)
    main_sub = float(data.get("main_subtotal", 0))
    calc_total = main_sub + extras_total

    await state.set_state(MasterConfirmStates.entering_sum)
    await callback.message.edit_text(
        t("confirm_step_sum", lang, calc_total=f"{calc_total:,.0f}"),
    )
    await callback.answer()


@router.callback_query(MasterConfirmStates.selecting_extra_category, F.data.startswith("asfcat:"))
async def confirm_extra_cat(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    cat_id = int(callback.data.split(":")[1])
    cat_svc = CategoryService(session)
    subcats = await cat_svc.get_subcategories_light(cat_id)
    await state.update_data(extra_cat_id=cat_id)
    await state.set_state(MasterConfirmStates.selecting_extra_subcategory)
    await callback.message.edit_text(
        t("confirm_step_extra_subcat", lang),
        reply_markup=get_asphalt_subcategories_keyboard(subcats, cat_id),
    )
    await callback.answer()


@router.callback_query(MasterConfirmStates.selecting_extra_subcategory, F.data.startswith("asfsubcat:"))
async def confirm_extra_subcat(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    sub_id = int(callback.data.split(":")[1])
    cat_svc = CategoryService(session)
    materials = await cat_svc.get_materials_by_subcategory(sub_id)
    if not materials:
        await callback.answer("❌ Materiallar mavjud emas", show_alert=True)
        return
    await state.update_data(extra_sub_id=sub_id)
    await state.set_state(MasterConfirmStates.selecting_extra_material)
    await callback.message.edit_text(
        t("confirm_step_extra_mat", lang),
        reply_markup=get_asphalt_keyboard(materials, subcat_id=sub_id),
    )
    await callback.answer()


@router.callback_query(MasterConfirmStates.selecting_extra_material, F.data.startswith("asfsubcat_back:"))
async def confirm_extra_back_to_subcat(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    """Go back from material to subcategory for extra services."""
    data = await state.get_data()
    cat_id = data.get("extra_cat_id")
    if not cat_id:
        await callback.answer("❌ Xatolik", show_alert=True)
        return
    cat_svc = CategoryService(session)
    subcats = await cat_svc.get_subcategories_light(cat_id)
    await state.set_state(MasterConfirmStates.selecting_extra_subcategory)
    await callback.message.edit_text(
        t("confirm_step_extra_subcat", lang),
        reply_markup=get_asphalt_subcategories_keyboard(subcats, cat_id),
    )
    await callback.answer()


@router.callback_query(MasterConfirmStates.selecting_extra_subcategory, F.data.startswith("asfcat_back:"))
async def confirm_extra_back_to_cat(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    """Go back from extra subcategory to category selection."""
    data = await state.get_data()
    cat_svc = CategoryService(session)
    categories = await cat_svc.get_categories_light()
    await state.set_state(MasterConfirmStates.selecting_extra_category)
    await callback.message.edit_text(
        t("confirm_step_extra_cat", lang, area=data.get("area_m2", "—")),
        reply_markup=get_asphalt_categories_keyboard(categories),
    )
    await callback.answer()


@router.callback_query(MasterConfirmStates.selecting_extra_material, F.data.startswith("asphalt:"))
async def confirm_extra_material(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    mat_id = int(callback.data.split(":")[1])
    cat_svc = CategoryService(session)
    material = await cat_svc.get_material_by_id(mat_id)
    if not material:
        await callback.answer(t("asphalt_not_found", lang), show_alert=True)
        return

    data = await state.get_data()
    # Store pending extra and ask for area
    await state.update_data(
        pending_extra_id=mat_id,
        pending_extra_name=material.name,
        pending_extra_price=str(material.price_per_m2),
        pending_extra_cost=str(material.cost_price_per_m2 or 0),
    )

    await state.set_state(MasterConfirmStates.entering_extra_area)
    await callback.message.edit_text(
        t("confirm_step_extra_area", lang),
    )
    await callback.answer()


@router.message(MasterConfirmStates.entering_extra_area)
async def confirm_extra_area(message: Message, state: FSMContext, lang: str) -> None:
    val = _parse_decimal(message.text or "")
    if val is None or val <= 0:
        await message.answer(t("invalid_area", lang))
        return

    data = await state.get_data()
    area = val
    price = float(data.get("pending_extra_price", 0))
    subtotal = float(area) * price

    # Add to extras
    extras = data.get("extras", [])
    extras.append({
        "asphalt_type_id": data.get("pending_extra_id"),
        "name": data.get("pending_extra_name"),
        "price_per_m2": price,
        "cost_price_per_m2": float(data.get("pending_extra_cost", 0)),
        "area_m2": float(area),
        "subtotal": subtotal,
    })
    await state.update_data(extras=extras)

    # Clear pending extra
    await state.update_data(
        pending_extra_id=None,
        pending_extra_name=None,
        pending_extra_price=None,
        pending_extra_cost=None,
    )

    await state.set_state(MasterConfirmStates.adding_extras)
    await _show_extras_step(message, state, lang, edit=False)


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
async def confirm_notes(message: Message, state: FSMContext, session, lang: str) -> None:
    text = message.text or ""
    notes = None if text.startswith("⏩") else text.strip()
    await state.update_data(notes=notes)

    # Step 9 — select usta
    data = await state.get_data()
    order_id = data.get("order_id")
    usta_svc = UstaService(session)
    order_svc = OrderService(session)
    order = await order_svc.get_by_id_full(order_id) if order_id else None
    viloyat_id = order.viloyat_id if order else None
    region_id = order.region_id if order else None
    ustas = await usta_svc.get_available_ustas(region_id=region_id, viloyat_id=viloyat_id)

    await state.set_state(MasterConfirmStates.selecting_usta)
    await message.answer(
        f"9/9 — Ustani tanlang yoki o'tkazib yuboring:",
        reply_markup=get_ustas_for_confirm_keyboard(ustas),
    )


@router.callback_query(MasterConfirmStates.selecting_usta, F.data.startswith("confirm_usta:"))
async def confirm_select_usta(callback: CallbackQuery, state: FSMContext, session, lang: str) -> None:
    val = callback.data.split(":")[1]
    if val == "skip":
        await state.update_data(selected_usta_id=None, selected_usta_name=None)
    else:
        usta_id = int(val)
        from app.db.models import User as UserModel
        from sqlalchemy import select as sa_select
        from app.db.session import async_session_maker
        result = await session.execute(sa_select(UserModel).where(UserModel.id == usta_id))
        usta = result.scalar_one_or_none()
        name = usta.full_name if usta else str(usta_id)
        await state.update_data(selected_usta_id=usta_id, selected_usta_name=name)
    await _show_confirm_summary(callback.message, state, lang)
    await callback.answer()


async def _show_confirm_summary(message, state: FSMContext, lang: str) -> None:
    data = await state.get_data()
    await state.set_state(MasterConfirmStates.confirming)
    work_date = datetime.fromisoformat(data["work_date"]).strftime("%d.%m.%Y")
    debt = max(Decimal("0"), Decimal(data["total_price"]) - Decimal(data["advance_paid"]))
    usta_name = data.get("selected_usta_name") or "—"

    # Build line items text
    extras = data.get("extras", [])
    extras_total = sum(float(e.get("subtotal", 0)) for e in extras)
    main_sub = float(data.get("main_subtotal", 0))
    calc_total = main_sub + extras_total
    main_area = float(data.get('area_m2', 0))

    line_items_text = f"🏗 {data.get('main_asphalt_name', '—')}: {main_area:,.0f} m² = {main_sub:,.0f} so'm\n"
    for i, e in enumerate(extras, 1):
        line_items_text += f"➕ {i}. {e['name']}: {e.get('area_m2', main_area):,.0f} m² × {e['price_per_m2']:,.0f} = {float(e['subtotal']):,.0f} so'm\n"

    await message.answer(
        t("confirm_summary", lang,
          number=data['order_number'],
          area=data['area_m2'],
          line_items_text=line_items_text,
          calc_total=f"{calc_total:,.0f}",
          total=f"{float(Decimal(data['total_price'])):,.0f}",
          advance=f"{float(Decimal(data['advance_paid'])):,.0f}",
          debt=f"{float(debt):,.0f}",
          address=data['address'],
          date=work_date,
          wage=f"{float(Decimal(data['usta_wage'])):,.0f}",
          commission=f"{float(Decimal(data['master_commission'])):,.0f}",
          notes=data.get('notes') or '—') + f"\n👷 Usta: <b>{usta_name}</b>",
        reply_markup=get_confirm_summary_keyboard(),
    )


@router.callback_query(MasterConfirmStates.confirming, F.data == "submit_confirm")
async def submit_confirmation(callback: CallbackQuery, state: FSMContext, user: User, session, lang: str) -> None:
    data = await state.get_data()
    await state.clear()

    # Build line items for DB
    extras = data.get("extras", [])
    extras_total = sum(float(e.get("subtotal", 0)) for e in extras)
    main_sub = float(data.get("main_subtotal", 0))
    calc_total = main_sub + extras_total

    line_items = []
    # Main asphalt
    if data.get("main_asphalt_id"):
        line_items.append({
            "asphalt_type_id": int(data["main_asphalt_id"]),
            "description": data.get("main_asphalt_name", ""),
            "area_m2": float(data["area_m2"]),
            "price_per_m2": float(data.get("main_asphalt_price", 0)),
            "cost_price_per_m2": float(data.get("main_asphalt_cost", 0)),
            "is_main": True,
        })
    # Extras (use individual area for each extra)
    for e in extras:
        line_items.append({
            "asphalt_type_id": e["asphalt_type_id"],
            "description": e["name"],
            "area_m2": e.get("area_m2", float(data["area_m2"])),
            "price_per_m2": e["price_per_m2"],
            "cost_price_per_m2": e["cost_price_per_m2"],
            "is_main": False,
        })

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
        line_items=line_items,
        calculated_total=Decimal(str(calc_total)),
    )

    if not order:
        await callback.message.edit_text(t("confirm_error", lang))
        await callback.answer()
        return

    # Assign usta if selected
    selected_usta_id = data.get("selected_usta_id")
    if selected_usta_id:
        usta_svc = UstaService(session)
        await usta_svc.assign_usta_to_order(
            order_id=order.id,
            usta_id=selected_usta_id,
            assigned_by_id=user.id,
        )
        await session.commit()

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
            reply_markup=get_master_my_order_keyboard(order.id, new_status.value),
        )

        # On completion, dispatch comprehensive notifications to admins, master, klient
        if new_status == OrderStatus.DONE:
            try:
                from app.bot.handlers.usta import _send_completion_notifications
                await _send_completion_notifications(session, order)
            except Exception:
                pass


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

    from app.bot.handlers._order_view import format_order_full
    text = format_order_full(order, user.role, lang)
    await callback.message.edit_text(
        text, reply_markup=get_master_my_order_keyboard(order_id, order.status.value)
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
    from app.db.models import ExpenseType
    order_id = int(callback.data.split(":")[1])
    # Simplified flow: no type/category selection — always EXTRA,
    # ask amount first, then require a description.
    await state.update_data(order_id=order_id, expense_type=ExpenseType.EXTRA.value)
    await state.set_state(ExpenseAddStates.entering_amount)
    await callback.message.edit_text(t("expense_enter_amount", lang))
    await callback.answer()


@router.message(ExpenseAddStates.entering_mat_volume)
async def master_expense_mat_volume(message: Message, state: FSMContext, lang: str) -> None:
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
        reply_markup=get_main_menu(UserRole.MASTER, lang),
    )


@router.callback_query(ExpenseAddStates.selecting_type, F.data == "expense_cancel")
async def expense_cancel(callback: CallbackQuery, state: FSMContext, lang: str) -> None:
    await state.clear()
    await callback.message.edit_text(t("expense_cancelled", lang))
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.MASTER, lang))
    await callback.answer()
