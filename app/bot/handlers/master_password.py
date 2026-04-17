"""Master password management handlers"""
import hashlib
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.filters import RoleFilter
from app.bot.i18n import t
from app.bot.keyboards.menus import get_cancel_keyboard, get_main_menu
from app.bot.states.master_password import MasterPasswordStates
from app.db.models import User, UserRole
from app.db.session import async_session_maker

router = Router()
router.message.filter(RoleFilter(UserRole.MASTER))


def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


@router.message(F.text.in_({"⚙️ Parolni O'zgartirish", "⚙️ Паролни Ўзгартириш", "⚙️ Изменить Пароль"}))
async def start_password_change(message: Message, state: FSMContext, user: User, lang: str) -> None:
    """Start password change process"""
    await state.set_state(MasterPasswordStates.entering_new_password)
    
    await message.answer(
        "🔐 <b>Web Panel uchun parol o'rnatish</b>\n\n"
        "Yangi parolni kiriting:\n"
        "• Kamida 6 ta belgi\n"
        "• Eslab qolish oson bo'lsin\n\n"
        "Parolni kiriting:",
        reply_markup=get_cancel_keyboard(lang)
    )


@router.message(MasterPasswordStates.entering_new_password)
async def process_new_password(message: Message, state: FSMContext, lang: str) -> None:
    """Process new password input"""
    password = message.text.strip()
    
    # Validate password
    if len(password) < 6:
        await message.answer(
            "❌ Parol juda qisqa!\n\n"
            "Kamida 6 ta belgi bo'lishi kerak.\n"
            "Qaytadan kiriting:",
            reply_markup=get_cancel_keyboard(lang)
        )
        return
    
    if len(password) > 50:
        await message.answer(
            "❌ Parol juda uzun!\n\n"
            "Maksimal 50 ta belgi.\n"
            "Qaytadan kiriting:",
            reply_markup=get_cancel_keyboard(lang)
        )
        return
    
    # Save password temporarily
    await state.update_data(new_password=password)
    await state.set_state(MasterPasswordStates.confirming_password)
    
    await message.answer(
        "✅ Parol qabul qilindi!\n\n"
        "Tasdiqlash uchun parolni qayta kiriting:",
        reply_markup=get_cancel_keyboard(lang)
    )


@router.message(MasterPasswordStates.confirming_password)
async def confirm_password(message: Message, state: FSMContext, user: User, lang: str) -> None:
    """Confirm password and save to database"""
    confirm_password = message.text.strip()
    
    data = await state.get_data()
    new_password = data.get("new_password")
    
    if confirm_password != new_password:
        await message.answer(
            "❌ Parollar mos kelmadi!\n\n"
            "Qaytadan tasdiqlang:",
            reply_markup=get_cancel_keyboard(lang)
        )
        return
    
    # Hash and save password
    password_hash = hash_password(new_password)
    
    async with async_session_maker() as session:
        db_user = await session.get(User, user.id)
        if db_user:
            db_user.password_hash = password_hash
            await session.commit()
    
    await state.clear()
    
    await message.answer(
        "✅ <b>Parol muvaffaqiyatli o'rnatildi!</b>\n\n"
        "Endi siz Web Panelga kirish uchun:\n"
        f"📱 Telefon: <code>{user.phone}</code>\n"
        f"🔐 Parol: <code>{new_password}</code>\n\n"
        "⚠️ Parolni eslab qoling yoki saqlang!\n\n"
        "Web Panelga kirish uchun '🌐 Web Panel' tugmasini bosing.",
        reply_markup=get_main_menu(user.role, lang)
    )
