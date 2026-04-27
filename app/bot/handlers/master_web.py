"""Master web panel handler - opens web app for Masters"""
import time

from aiogram import F, Router
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.filters import RoleFilter
from app.bot.i18n import t
from app.config import settings
from app.db.models import UserRole

router = Router()
router.message.filter(RoleFilter(UserRole.MASTER))


@router.message(F.text.in_({"🌐 Web Panel", "🌐 Веб Панель"}))
async def master_web_panel(message: Message, lang: str) -> None:
    """Send Master web panel link"""
    
    # Build web panel URL - extract base domain from WEB_URL
    # WEB_URL format: https://domain.com/tma-admin
    # We need: https://domain.com/master-panel/admin
    base_url = settings.WEB_URL.rsplit("/", 1)[0]  # Remove last path segment
    # Append timestamp to bypass Telegram WebApp caching
    web_url = f"{base_url}/master-panel/admin/dashboard?t={int(time.time())}"
    
    # Create inline keyboard with web app button
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🌐 Master Panel Ochish",
        web_app=WebAppInfo(url=web_url)
    )
    
    await message.answer(
        "🏗 <b>Avtoban Stroy - Master Panel</b>\n\n"
        "Web panelda siz quyidagilarni qila olasiz:\n\n"
        "📊 <b>Dashboard</b> - Umumiy statistika\n"
        "📋 <b>Zakazlar</b> - Barcha zakazlarni boshqarish\n"
        "   • Yangi zakaz yaratish\n"
        "   • Zakazlarni tahrirlash\n"
        "   • Qidirish va filtrlash\n\n"
        "👥 <b>Klientlar</b> - Klientlar ro'yxati\n"
        "   • Har bir klient bo'yicha statistika\n"
        "   • Zakaz tarixi\n\n"
        "💰 <b>Komissiya</b> - To'liq hisobotlar\n"
        "   • Jami komissiya\n"
        "   • Oylik va haftalik statistika\n"
        "   • Holat bo'yicha taqsimot\n\n"
        "Quyidagi tugmani bosing:",
        reply_markup=builder.as_markup()
    )
