from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.filters import RoleFilter
from app.bot.i18n import t, get_lang as _gl, ALL_BUTTON_TEXTS
from app.bot.keyboards.menus import get_main_menu
from app.db.models import MaterialRequestStatus, User, UserRole
from app.services.material_service import MaterialService

router = Router()
router.message.filter(RoleFilter(UserRole.SHOFER))


# ── Active deliveries ───────────────────────────────────────────────────────────

@router.message(F.text.in_(ALL_BUTTON_TEXTS.get("btn_my_deliveries", set()) | ALL_BUTTON_TEXTS.get("btn_update_status", set())))
async def my_deliveries(message: Message, session, lang: str) -> None:
    mat_svc = MaterialService(session)
    priced = await mat_svc.get_priced()
    if not priced:
        await message.answer(t("no_deliveries", lang))
        return
    lines = [t("active_deliveries", lang, count=len(priced))]
    for req in priced:
        order_num = req.order.order_number if req.order else "?"
        usta_name = req.usta.full_name or str(req.usta.telegram_id) if req.usta else "?"
        total = (
            float(req.material_price or 0)
            + float(req.delivery_price or 0)
            + float(req.extra_cost or 0)
        )
        lines.append(
            f"\n🔢 #{req.id}  |  {t('order', lang)} {order_num}\n"
            f"  👷 {t('usta', lang)}: {usta_name}\n"
            f"  📦 {req.amount_tonnes} t  |  💰 {total:,.0f}"
        )
    await message.answer("\n".join(lines))


# ── Confirm delivery callback (sent by zavod price_submit) ─────────────────────

@router.callback_query(F.data.startswith("shofer_delivered:"))
async def shofer_confirm_delivery(callback: CallbackQuery, user: User, session, lang: str) -> None:
    req_id = int(callback.data.split(":")[1])
    mat_svc = MaterialService(session)
    req_full = await mat_svc.get_by_id(req_id)

    if not req_full:
        await callback.answer(t("request_not_found", lang), show_alert=True)
        return
    if req_full.status == MaterialRequestStatus.DELIVERED:
        await callback.answer(t("already_delivered", lang), show_alert=True)
        return
    if req_full.status != MaterialRequestStatus.PRICED:
        await callback.answer(t("not_priced_yet", lang), show_alert=True)
        return

    req = await mat_svc.deliver(req_id)
    if not req:
        await callback.answer(t("error_occurred", lang), show_alert=True)
        return

    # Notify usta
    from app.bot.loader import bot
    if req_full.usta:
        try:
            ul = _gl(req_full.usta)
            await bot.send_message(
                req_full.usta.telegram_id,
                t("material_delivered_notify", ul, amount=req.amount_tonnes),
            )
        except Exception:
            pass

    await callback.message.edit_text(
        t("delivery_confirmed", lang, amount=req.amount_tonnes)
    )
    await callback.message.answer(t("main_menu", lang), reply_markup=get_main_menu(UserRole.SHOFER, lang))
    await callback.answer(t("delivered_marked", lang))
