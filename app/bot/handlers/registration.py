from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.i18n import t
from app.bot.keyboards.menus import get_main_menu, get_phone_keyboard
from app.bot.states.registration import RegistrationStates
from app.db.models import User
from app.services.user_service import UserService

router = Router()


def _role_label(user: User, lang: str) -> str:
    _MAP = {
        "super_admin": "role_super_admin",
        "admin": "role_admin",
        "helper_admin": "role_helper_admin",
        "master": "role_master",
        "usta": "role_usta",
        "zavod": "role_zavod",
        "shofer": "role_shofer",
        "klient": "role_klient",
    }
    key = _MAP.get(user.role.value, "role_klient")
    return t(key, lang)


@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def handle_phone_contact(
    message: Message,
    state: FSMContext,
    user: User,
    session,
    lang: str,
) -> None:
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = f"+{phone}"

    user_service = UserService(session)
    updated_user = await user_service.update_phone(user.id, phone)

    await state.clear()

    role_label = _role_label(updated_user, lang)
    await message.answer(
        t("registration_success", lang,
          name=updated_user.full_name or t("nameless", lang),
          phone=phone,
          role=role_label),
        reply_markup=get_main_menu(updated_user.role, lang),
    )


@router.message(RegistrationStates.waiting_for_phone)
async def handle_phone_wrong_type(message: Message, lang: str) -> None:
    await message.answer(
        t("phone_wrong_type", lang),
        reply_markup=get_phone_keyboard(lang),
    )
