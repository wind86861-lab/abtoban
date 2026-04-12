from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

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
    region_name = req.order.region.name if req.order and req.order.region else "—"
    
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
    
    # Notify only zavod users in the order's region
    from app.bot.loader import bot
    user_svc = UserService(session)
    
    usta_name = req_full.usta.full_name if req_full and req_full.usta else "?"
    order_region_id = req_full.order.region_id if req_full and req_full.order else None
    region_name = req_full.order.region.name if req_full and req_full.order and req_full.order.region else "—"
    
    notify_text = (
        f"📦 <b>Yangi material so'rov!</b>\n\n"
        f"🔢 So'rov #{req.id}\n"
        f"📍 Viloyat: {region_name}\n"
        f"👷 Usta: {usta_name}\n"
        f"📦 Miqdor: <b>{req.amount_tonnes} tonna</b>\n"
        f"📝 Izoh: {req.notes or '—'}"
    )
    
    # Find zavod users matching the order's region
    if order_region_id:
        zavods = await user_svc.get_by_role_and_region(UserRole.ZAVOD, order_region_id)
    else:
        zavods = await user_svc.get_all(role=UserRole.ZAVOD)
    
    notified_count = 0
    for zavod in zavods:
        try:
            await bot.send_message(zavod.telegram_id, notify_text)
            notified_count += 1
        except Exception:
            pass
    
    if notified_count == 0 and order_region_id:
        # No regional zavod found, notify all zavods as fallback
        all_zavods = await user_svc.get_all(role=UserRole.ZAVOD)
        for zavod in all_zavods:
            try:
                await bot.send_message(zavod.telegram_id, notify_text)
            except Exception:
                pass
    
    await callback.message.edit_text(
        f"✅ <b>So'rov tasdiqlandi!</b>\n\n"
        f"📦 {req.amount_tonnes} tonna\n"
        f"📍 Viloyat: {region_name}\n"
        f"Zavod xabardor qilindi ({notified_count} ta)."
    )
    await callback.answer("✅ Tasdiqlandi va zavodga yuborildi!")


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
