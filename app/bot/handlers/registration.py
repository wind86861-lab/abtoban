from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards.menus import get_main_menu, get_phone_keyboard
from app.bot.states.registration import RegistrationStates
from app.db.models import ROLE_LABELS, User
from app.services.user_service import UserService

router = Router()


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def handle_phone_contact(
    message: Message,
    state: FSMContext,
    user: User,
    session,
) -> None:
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = f"+{phone}"

    user_service = UserService(session)
    updated_user = await user_service.update_phone(user.id, phone)

    await state.clear()

    role_label = ROLE_LABELS.get(updated_user.role, updated_user.role.value)
    await message.answer(
        f"✅ Ro'yxatdan muvaffaqiyatli o'tdingiz!\n\n"
        f"👤 Ism: <b>{updated_user.full_name or 'Nomsiz'}</b>\n"
        f"📱 Tel: <b>{phone}</b>\n"
        f"👥 Rol: <b>{role_label}</b>",
        reply_markup=get_main_menu(updated_user.role),
    )


@router.message(RegistrationStates.waiting_for_phone)
async def handle_phone_wrong_type(message: Message) -> None:
    await message.answer(
        "❗ Iltimos, tugmani bosing va telefon raqamingizni yuboring.",
        reply_markup=get_phone_keyboard(),
    )
