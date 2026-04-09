from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards.menus import get_main_menu, get_phone_keyboard
from app.bot.states.registration import RegistrationStates
from app.db.models import ROLE_LABELS, User

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, user: User) -> None:
    await state.clear()

    if not user.phone:
        await state.set_state(RegistrationStates.waiting_for_phone)
        await message.answer(
            "👋 <b>Avtoban Stroy</b> botiga xush kelibsiz!\n\n"
            "Ro'yxatdan o'tish uchun telefon raqamingizni yuboring:",
            reply_markup=get_phone_keyboard(),
        )
        return

    role_label = ROLE_LABELS.get(user.role, user.role.value)
    await message.answer(
        f"👋 Xush kelibsiz, <b>{user.full_name or message.from_user.full_name}</b>!\n"
        f"👤 Rolingiz: <b>{role_label}</b>",
        reply_markup=get_main_menu(user.role),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, user: User) -> None:
    await state.clear()
    role_label = ROLE_LABELS.get(user.role, user.role.value)
    await message.answer(
        f"👤 Rolingiz: <b>{role_label}</b>\n"
        f"Asosiy menyu:",
        reply_markup=get_main_menu(user.role),
    )


@router.message(Command("help"))
async def cmd_help(message: Message, user: User) -> None:
    await message.answer(
        "ℹ️ <b>Avtoban Stroy Bot</b>\n\n"
        "Mavjud buyruqlar:\n"
        "/start — Botni ishga tushirish\n"
        "/menu — Asosiy menyu\n"
        "/help — Yordam\n"
        "/cancel — Amalni bekor qilish\n\n"
        "Muammo bo'lsa: @avtoban_support",
        reply_markup=get_main_menu(user.role),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, user: User) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "Bekor qilish uchun hech qanday amal yo'q.",
            reply_markup=get_main_menu(user.role),
        )
        return

    await state.clear()
    await message.answer(
        "❌ Amal bekor qilindi.",
        reply_markup=get_main_menu(user.role),
    )


@router.message(StateFilter("*"), F.text == "❌ Bekor qilish")
async def cancel_button(message: Message, state: FSMContext, user: User) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "Bekor qilish uchun hech qanday amal yo'q.",
            reply_markup=get_main_menu(user.role),
        )
        return
    await state.clear()
    await message.answer("❌ Amal bekor qilindi.", reply_markup=get_main_menu(user.role))
