"""
Telegram bot handlers for online marketplace (shop) — opens WebApp
"""
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

from app.bot.i18n import ALL_BUTTON_TEXTS
from app.config import settings

logger = logging.getLogger(__name__)
router = Router()

# Derive shop URL from WEB_URL (replace /tma-admin with /shop)
SHOP_URL = settings.WEB_URL.replace("/tma-admin", "/shop")


def get_shop_keyboard():
    """Keyboard with WebApp button to open the shop."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🛍 Do'konni ochish",
            web_app=WebAppInfo(url=SHOP_URL),
        )],
    ])


@router.message(Command("shop"))
async def cmd_shop(message: Message, state: FSMContext):
    """Open online shop via WebApp."""
    await state.clear()
    await message.answer(
        "🛍 <b>Avtoban Online Do'kon</b>\n\n"
        "Mahsulotlarni ko'rish, savatga qo'shish va buyurtma berish uchun "
        "quyidagi tugmani bosing:",
        reply_markup=get_shop_keyboard(),
        parse_mode="HTML",
    )


@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_shop", set())))
async def btn_shop(message: Message, state: FSMContext):
    """Open shop from main menu button."""
    await state.clear()
    await message.answer(
        "🛍 <b>Avtoban Online Do'kon</b>\n\n"
        "Mahsulotlarni ko'rish, savatga qo'shish va buyurtma berish uchun "
        "quyidagi tugmani bosing:",
        reply_markup=get_shop_keyboard(),
        parse_mode="HTML",
    )
