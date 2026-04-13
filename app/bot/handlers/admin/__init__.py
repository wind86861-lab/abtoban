from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.filters import RoleFilter
from app.bot.i18n import t, ALL_BUTTON_TEXTS
from app.bot.keyboards.finance import get_admin_material_requests_keyboard
from app.bot.keyboards.menus import get_main_menu
from app.config import settings
from app.db.models import MANAGEMENT_ROLES, User, UserRole
from app.services.material_service import MaterialService

from .export import router as export_router
from .materials import router as materials_router
from .orders import router as orders_router
from .reports import router as reports_router
from .role_management import router as role_mgmt_router
from .settings import router as settings_router

router = Router()


@router.message(
    F.text.in_(ALL_BUTTON_TEXTS.get("btn_web_panel", set())),
    RoleFilter(*MANAGEMENT_ROLES),
)
async def web_panel_link(message: Message, user: User, lang: str) -> None:
    from aiogram.types import WebAppInfo
    url = f"{settings.WEB_URL}/admin"
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Admin Panel", web_app=WebAppInfo(url=url))
    await message.answer(
        f"🌐 <b>Web Admin Panel</b>\n\n"
        f" Login: <code>{settings.ADMIN_USERNAME}</code>\n"
        f"🔑 Parol: <code>{settings.ADMIN_PASSWORD}</code>\n\n"
        f"ℹ️ Quyidagi tugmani bosing — Telegram ichida ochiladi.",
        reply_markup=builder.as_markup(),
    )


@router.message(F.text.contains("Material so"), RoleFilter(*MANAGEMENT_ROLES))
async def admin_material_requests_entry(message: Message, user: User, session, lang: str) -> None:
    """Entry point for admin material requests - on parent router for reliable matching."""
    mat_svc = MaterialService(session)
    region_id = None if user.role == UserRole.SUPER_ADMIN else user.region_id
    requests = await mat_svc.get_admin_pending(region_id=region_id)

    if not requests:
        await message.answer(
            "📦 <b>Material so'rovlar</b>\n\n"
            "Tasdiqlash kutayotgan so'rovlar yo'q.",
            reply_markup=get_main_menu(user.role, lang),
        )
        return

    await message.answer(
        f"📦 <b>Material so'rovlar</b> ({len(requests)} ta)\n\n"
        f"Tasdiqlash kerak:",
        reply_markup=get_admin_material_requests_keyboard(requests),
    )


router.include_router(role_mgmt_router)
router.include_router(orders_router)
router.include_router(materials_router)
router.include_router(settings_router)
router.include_router(reports_router)
router.include_router(export_router)
