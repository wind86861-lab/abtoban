import logging

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, MenuButtonWebApp, Message, WebAppInfo

from app.bot.i18n import t, ALL_BUTTON_TEXTS
from app.bot.keyboards.menus import get_language_keyboard, get_main_menu, get_phone_keyboard
from app.bot.loader import bot
from app.bot.states.registration import LanguageStates, RegistrationStates
from app.config import settings
from app.db.models import User
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

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


# ── /start ────────────────────────────────────────────────────────────────────

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, user: User, lang: str) -> None:
    await state.clear()

    # Set per-chat menu button → Web Do'kon
    try:
        base_url = settings.WEB_URL.rsplit("/", 1)[0]
        shop_url = f"{base_url}/shop"
        await bot.set_chat_menu_button(
            chat_id=message.chat.id,
            menu_button=MenuButtonWebApp(
                text="Web Do'kon",
                web_app=WebAppInfo(url=shop_url),
            )
        )
    except Exception as e:
        logger.warning("Menu button error: %s", e)

    # First time: no language set → ask language
    if not user.language:
        await state.set_state(LanguageStates.choosing_language)
        await message.answer(
            t("choose_language", "uz_lat"),
            reply_markup=get_language_keyboard(),
        )
        return

    # No phone → registration
    if not user.phone:
        await state.set_state(RegistrationStates.waiting_for_phone)
        await message.answer(
            t("welcome", lang),
            reply_markup=get_phone_keyboard(lang),
        )
        return

    # Returning user
    role_label = _role_label(user, lang)
    await message.answer(
        t("welcome_back", lang, name=user.full_name or message.from_user.full_name, role=role_label),
        reply_markup=get_main_menu(user.role, lang),
    )


# ── Language selection callback ───────────────────────────────────────────────

@router.callback_query(F.data.startswith("set_lang:"))
async def handle_language_selection(
    callback: CallbackQuery, state: FSMContext, user: User, session
) -> None:
    lang_code = callback.data.split(":")[1]
    if lang_code not in ("uz_lat", "uz_cyr", "ru"):
        await callback.answer("❌", show_alert=True)
        return

    # Save language to user
    user_svc = UserService(session)
    await user_svc.update_language(user.id, lang_code)

    await state.clear()
    await callback.message.edit_text(t("language_set", lang_code))

    # If no phone → go to registration
    if not user.phone:
        await state.set_state(RegistrationStates.waiting_for_phone)
        await callback.message.answer(
            t("welcome", lang_code),
            reply_markup=get_phone_keyboard(lang_code),
        )
    else:
        role_label = _role_label(user, lang_code)
        await callback.message.answer(
            t("welcome_back", lang_code, name=user.full_name or "?", role=role_label),
            reply_markup=get_main_menu(user.role, lang_code),
        )
    await callback.answer()


# ── Language change button (from menu) ────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_change_language", set())))
async def change_language_btn(message: Message, state: FSMContext) -> None:
    await state.set_state(LanguageStates.choosing_language)
    await message.answer(
        t("choose_language", "uz_lat"),
        reply_markup=get_language_keyboard(),
    )


# ── /menu ─────────────────────────────────────────────────────────────────────

@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext, user: User, lang: str) -> None:
    await state.clear()
    role_label = _role_label(user, lang)
    await message.answer(
        t("your_role", lang, role=role_label),
        reply_markup=get_main_menu(user.role, lang),
    )


# ── /help ─────────────────────────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message, user: User, lang: str) -> None:
    await message.answer(
        t("help_text", lang),
        reply_markup=get_main_menu(user.role, lang),
    )


# ── /cancel ───────────────────────────────────────────────────────────────────

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, user: User, lang: str) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            t("no_action_to_cancel", lang),
            reply_markup=get_main_menu(user.role, lang),
        )
        return

    await state.clear()
    await message.answer(
        t("action_cancelled", lang),
        reply_markup=get_main_menu(user.role, lang),
    )


# ── Cancel button (all languages) ────────────────────────────────────────────

@router.message(StateFilter("*"), F.text.in_(ALL_BUTTON_TEXTS.get("btn_cancel", set())))
async def cancel_button(message: Message, state: FSMContext, user: User, lang: str) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            t("no_action_to_cancel", lang),
            reply_markup=get_main_menu(user.role, lang),
        )
        return
    await state.clear()
    await message.answer(t("action_cancelled", lang), reply_markup=get_main_menu(user.role, lang))
