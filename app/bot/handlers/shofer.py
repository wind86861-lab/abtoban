from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.filters import RoleFilter
from app.bot.keyboards.menus import get_main_menu
from app.db.models import MaterialRequestStatus, User, UserRole
from app.services.material_service import MaterialService

router = Router()
router.message.filter(RoleFilter(UserRole.SHOFER))


# ── Active deliveries ───────────────────────────────────────────────────────────

@router.message(F.text.in_({"\ud83d\ude97 Mening yetkazilmalarim", "\u2705 Status yangilash"}))
async def my_deliveries(message: Message, session) -> None:
    mat_svc = MaterialService(session)
    priced = await mat_svc.get_priced()
    if not priced:
        await message.answer(
            "\ud83d\ude97 <b>Mening yetkazilmalarim</b>\n\nHozircha yetkazish kerak bo'lgan material yo'q."
        )
        return
    lines = [f"\ud83d\ude97 <b>Faol topshiriqlar</b> ({len(priced)} ta):\n"]
    for req in priced:
        order_num = req.order.order_number if req.order else "?"
        usta_name = req.usta.full_name or str(req.usta.telegram_id) if req.usta else "?"
        total = (
            float(req.material_price or 0)
            + float(req.delivery_price or 0)
            + float(req.extra_cost or 0)
        )
        lines.append(
            f"\n\ud83d\udd22 So'rov #{req.id}  |  Zakaz {order_num}\n"
            f"  \ud83d\udc77 Usta: {usta_name}\n"
            f"  \ud83d\udce6 {req.amount_tonnes} tonna  |  \ud83d\udcb0 {total:,.0f} so'm"
        )
    await message.answer("\n".join(lines))


# ── Confirm delivery callback (sent by zavod price_submit) ─────────────────────

@router.callback_query(F.data.startswith("shofer_delivered:"))
async def shofer_confirm_delivery(callback: CallbackQuery, user: User, session) -> None:
    req_id = int(callback.data.split(":")[1])
    mat_svc = MaterialService(session)
    req_full = await mat_svc.get_by_id(req_id)

    if not req_full:
        await callback.answer("\u274c So'rov topilmadi.", show_alert=True)
        return
    if req_full.status == MaterialRequestStatus.DELIVERED:
        await callback.answer("\u2139\ufe0f Bu allaqachon yetkazilgan.", show_alert=True)
        return
    if req_full.status != MaterialRequestStatus.PRICED:
        await callback.answer("\u274c Narx hali belgilanmagan.", show_alert=True)
        return

    req = await mat_svc.deliver(req_id)
    if not req:
        await callback.answer("\u274c Xatolik yuz berdi.", show_alert=True)
        return

    # Notify usta
    from app.bot.loader import bot
    if req_full.usta:
        try:
            await bot.send_message(
                req_full.usta.telegram_id,
                f"\ud83d\udce6 <b>Material yetkazildi!</b>\n\n"
                f"\ud83d\udce6 {req.amount_tonnes} tonna\n"
                f"Ish boshlashingiz mumkin!",
            )
        except Exception:
            pass

    await callback.message.edit_text(
        f"\u2705 <b>Yetkazildi deb tasdiqlandi!</b>\n\n"
        f"\ud83d\udce6 {req.amount_tonnes} tonna material\n"
        f"Usta xabardor qilindi."
    )
    await callback.message.answer("Asosiy menyu:", reply_markup=get_main_menu(UserRole.SHOFER))
    await callback.answer("\u2705 Tasdiqlandi!")
