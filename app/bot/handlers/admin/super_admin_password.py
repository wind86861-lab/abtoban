"""Super Admin web-panel password management handlers."""
import hashlib

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.bot.filters import RoleFilter
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu
from app.db.models import User, UserRole
from app.db.session import async_session_maker

router = Router()
router.message.filter(RoleFilter(UserRole.SUPER_ADMIN))


class SuperAdminPasswordStates(StatesGroup):
    entering_new_password = State()
    confirming_password = State()


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


@router.message(F.text.in_({"🔐 Admin Parolni O'zgartirish", "🔐 Parolni O'zgartirish"}))
async def start_password_change(message: Message, state: FSMContext, user: User) -> None:
    await state.set_state(SuperAdminPasswordStates.entering_new_password)
    await message.answer(
        "🔐 <b>Admin Web Panel uchun parol o'rnatish</b>\n\n"
        "Yangi parolni kiriting (kamida 6 ta belgi):",
        reply_markup=get_cancel_keyboard("uz"),
    )


@router.message(SuperAdminPasswordStates.entering_new_password)
async def process_new_password(message: Message, state: FSMContext) -> None:
    password = (message.text or "").strip()
    if len(password) < 6:
        await message.answer("❌ Parol kamida 6 ta belgi bo'lishi kerak. Qaytadan kiriting:")
        return
    if len(password) > 50:
        await message.answer("❌ Parol 50 ta belgidan oshmasin. Qaytadan kiriting:")
        return
    await state.update_data(new_password=password)
    await state.set_state(SuperAdminPasswordStates.confirming_password)
    await message.answer(
        "✅ Qabul qilindi!\n\nTasdiqlash uchun parolni qayta kiriting:",
        reply_markup=get_cancel_keyboard("uz"),
    )


@router.message(SuperAdminPasswordStates.confirming_password)
async def confirm_password(message: Message, state: FSMContext, user: User) -> None:
    confirm = (message.text or "").strip()
    data = await state.get_data()
    new_password = data.get("new_password")

    if confirm != new_password:
        await message.answer("❌ Parollar mos kelmadi! Qaytadan tasdiqlang:")
        return

    async with async_session_maker() as session:
        db_user = await session.get(User, user.id)
        if db_user:
            db_user.password_hash = _hash(new_password)
            await session.commit()

    await state.clear()
    await message.answer(
        "✅ <b>Parol muvaffaqiyatli o'rnatildi!</b>\n\n"
        f"📱 Telefon: <code>{user.phone}</code>\n"
        f"🔐 Parol: <code>{new_password}</code>\n\n"
        "⚠️ Parolni eslab qoling!\n\n"
        "Admin panelga kirish: /tma-admin yoki veb sayt orqali.",
        reply_markup=get_main_menu(user.role, "uz"),
    )
