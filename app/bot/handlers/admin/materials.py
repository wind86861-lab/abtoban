from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.filters import RoleFilter
from app.bot.keyboards.finance import get_admin_material_requests_keyboard, get_admin_material_detail_keyboard
from app.bot.keyboards.menus import get_main_menu
from app.db.models import MANAGEMENT_ROLES, User, UserRole
from app.services.material_service import MaterialService
from app.services.user_service import UserService

router = Router()


@router.callback_query(F.data.startswith("admin_view_material:"), RoleFilter(*MANAGEMENT_ROLES))
async def admin_view_material(callback: CallbackQuery, session) -> None:
    req_id = int(callback.data.split(":")[1])
    mat_svc = MaterialService(session)
    req = await mat_svc.get_by_id(req_id)
    
    if not req:
        await callback.answer("❌ So'rov topilmadi", show_alert=True)
        return
    
    order_num = req.order.order_number if req.order else "?"
    usta_name = req.usta.full_name or str(req.usta.telegram_id) if req.usta else "?"
    # Fallback to usta's region if order.region is NULL (old orders)
    if req.order and req.order.region:
        region_name = req.order.region.name
    elif req.usta and req.usta.region:
        region_name = req.usta.region.name
    else:
        region_name = "—"
    
    await callback.message.edit_text(
        f"📦 <b>Material so'rov #{req.id}</b>\n\n"
        f"🔢 Zakaz: {order_num}\n"
        f"📍 Viloyat: {region_name}\n"
        f"👷 Usta: {usta_name}\n"
        f"📦 Miqdor: <b>{req.amount_tonnes} tonna</b>\n"
        f"📝 Izoh: {req.notes or '—'}\n"
        f"📅 Sana: {req.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Tasdiqlaysizmi?",
        reply_markup=get_admin_material_detail_keyboard(req_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_approve_material:"), RoleFilter(*MANAGEMENT_ROLES))
async def admin_approve_material(callback: CallbackQuery, session) -> None:
    req_id = int(callback.data.split(":")[1])
    mat_svc = MaterialService(session)
    req = await mat_svc.approve(req_id)

    if not req:
        await callback.answer("❌ So'rov allaqachon tasdiqlangan yoki topilmadi", show_alert=True)
        return

    req_full = await mat_svc.get_by_id(req_id)
    # Use order region if available, fallback to usta region for old orders
    if req_full and req_full.order and req_full.order.region_id:
        order_region_id = req_full.order.region_id
        region_name = req_full.order.region.name
    elif req_full and req_full.usta and req_full.usta.region_id:
        order_region_id = req_full.usta.region_id
        region_name = req_full.usta.region.name if req_full.usta.region else "—"
    else:
        order_region_id = None
        region_name = "—"

    # Get zavods filtered by order region
    user_svc = UserService(session)
    if order_region_id:
        zavods = await user_svc.get_zavods_by_region(order_region_id)
    else:
        zavods = await user_svc.get_zavods()

    builder = InlineKeyboardBuilder()
    for z in zavods:
        builder.button(
            text=f"🏭 {z.name}",
            callback_data=f"mat_zavod:{req_id}:{z.id}",
        )
    builder.adjust(2)
    if order_region_id:
        builder.row()
        builder.button(text="📋 Barcha zavodlar", callback_data=f"mat_zavod_all:{req_id}")
    builder.row()
    builder.button(text="⬅️ Orqaga", callback_data="back_admin_materials")

    await callback.message.edit_text(
        f"✅ <b>So'rov tasdiqlandi!</b>\n\n"
        f"📦 {req.amount_tonnes} tonna\n"
        f"📍 Viloyat: {region_name}\n\n"
        f"🏭 Qaysi zavodga yuborish kerak?",
        reply_markup=builder.as_markup(),
    )
    await callback.answer("✅ Tasdiqlandi! Zavodni tanlang.")


@router.callback_query(F.data.startswith("mat_zavod_all:"), RoleFilter(*MANAGEMENT_ROLES))
async def show_all_zavods_for_material(callback: CallbackQuery, session) -> None:
    req_id = int(callback.data.split(":")[1])
    mat_svc = MaterialService(session)
    req_full = await mat_svc.get_by_id(req_id)
    if not req_full:
        await callback.answer("❌ So'rov topilmadi", show_alert=True)
        return

    # Fallback to usta region if order region is NULL
    if req_full.order and req_full.order.region:
        region_name = req_full.order.region.name
    elif req_full.usta and req_full.usta.region:
        region_name = req_full.usta.region.name
    else:
        region_name = "—"

    user_svc = UserService(session)
    zavods = await user_svc.get_zavods()

    builder = InlineKeyboardBuilder()
    for z in zavods:
        builder.button(
            text=f"🏭 {z.name}",
            callback_data=f"mat_zavod:{req_id}:{z.id}",
        )
    builder.adjust(2)
    builder.row()
    builder.button(text="⬅️ Orqaga", callback_data="back_admin_materials")

    await callback.message.edit_text(
        f"� So'rov #{req_full.id} | {req_full.amount_tonnes} tonna\n"
        f"📍 Viloyat: {region_name}\n\n"
        f"🏭 <b>Barcha zavodlar</b> — tanlang:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mat_zavod:"), RoleFilter(*MANAGEMENT_ROLES))
async def pick_zavod_for_material(callback: CallbackQuery, session) -> None:
    parts = callback.data.split(":")
    req_id = int(parts[1])
    zavod_id = int(parts[2])

    mat_svc = MaterialService(session)
    req_full = await mat_svc.get_by_id(req_id)
    if not req_full:
        await callback.answer("❌ So'rov topilmadi", show_alert=True)
        return

    # Assign the zavod entity to the material request
    await mat_svc.assign_zavod(req_id, zavod_id)

    usta_name = req_full.usta.full_name if req_full.usta else "?"
    # Fallback to usta region if order region is NULL
    if req_full.order and req_full.order.region:
        region_name = req_full.order.region.name
    elif req_full.usta and req_full.usta.region:
        region_name = req_full.usta.region.name
    else:
        region_name = "—"

    # Get the selected zavod entity
    user_svc = UserService(session)
    from app.db.models import Zavod
    from sqlalchemy import select as sa_select
    result = await user_svc.session.execute(
        sa_select(Zavod).where(Zavod.id == zavod_id)
    )
    zavod = result.scalar_one_or_none()
    zavod_name = zavod.name if zavod else "?"

    notify_text = (
        f"📦 <b>Yangi material so'rov!</b>\n\n"
        f"🔢 So'rov #{req_full.id}\n"
        f"📍 Viloyat: {region_name}\n"
        f"👷 Usta: {usta_name}\n"
        f"📦 Miqdor: <b>{req_full.amount_tonnes} tonna</b>\n"
        f"📝 Izoh: {req_full.notes or '—'}"
    )

    # Notify users linked to the selected zavod
    from app.bot.loader import bot
    zavod_users = await user_svc.get_all(role=UserRole.ZAVOD)
    notified_count = 0
    for u in zavod_users:
        if u.zavod_id == zavod_id:
            try:
                await bot.send_message(u.telegram_id, notify_text)
                notified_count += 1
            except Exception:
                pass

    await callback.message.edit_text(
        f"✅ <b>Zavod tanlandi!</b>\n\n"
        f"🏭 Zavod: <b>{zavod_name}</b>\n"
        f"📦 {req_full.amount_tonnes} tonna\n"
        f"📍 Viloyat: {region_name}\n"
        f"Zavod xabardor qilindi ({notified_count} ta)."
    )
    await callback.answer("✅ Zavodga yuborildi!")


@router.callback_query(F.data.startswith("admin_reject_material:"), RoleFilter(*MANAGEMENT_ROLES))
async def admin_reject_material(callback: CallbackQuery, session) -> None:
    req_id = int(callback.data.split(":")[1])
    mat_svc = MaterialService(session)
    req = await mat_svc.reject(req_id)
    
    if not req:
        await callback.answer("❌ So'rov topilmadi", show_alert=True)
        return
    
    # Notify usta
    from app.bot.loader import bot
    if req.usta:
        try:
            await bot.send_message(
                req.usta.telegram_id,
                f"❌ <b>Material so'rov rad etildi</b>\n\n"
                f"📦 {req.amount_tonnes} tonna\n"
                f"Admin tomonidan rad etildi."
            )
        except Exception:
            pass
    
    await callback.message.edit_text(
        f"❌ <b>So'rov rad etildi</b>\n\n"
        f"Usta xabardor qilindi."
    )
    await callback.answer("❌ Rad etildi!")


@router.callback_query(F.data == "back_admin_materials", RoleFilter(*MANAGEMENT_ROLES))
async def back_admin_materials(callback: CallbackQuery, user: User, session) -> None:
    mat_svc = MaterialService(session)
    region_id = None if user.role == UserRole.SUPER_ADMIN else user.region_id
    requests = await mat_svc.get_admin_pending(region_id=region_id)
    
    if not requests:
        await callback.message.edit_text("📦 Tasdiqlash kutayotgan so'rovlar yo'q.")
    else:
        await callback.message.edit_text(
            f"📦 <b>Material so'rovlar</b> ({len(requests)} ta):",
            reply_markup=get_admin_material_requests_keyboard(requests),
        )
    await callback.answer()
