from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.filters import RoleFilter
from app.db.models import ADMIN_ROLES, MANAGEMENT_ROLES
from app.services.report_service import ReportService

router = Router()

_PERIOD_LABELS = {
    "today": "Bugun",
    "week": "Bu hafta",
    "month": "Bu oy",
    "all": "Hammasi",
}


def _period_keyboard(prefix: str) -> object:
    builder = InlineKeyboardBuilder()
    for key, label in _PERIOD_LABELS.items():
        builder.button(text=label, callback_data=f"{prefix}:{key}")
    builder.adjust(2)
    return builder.as_markup()


# ── Dashboard ──────────────────────────────────────────────────────────────────

@router.message(F.text == "📊 Statistika", RoleFilter(*MANAGEMENT_ROLES))
async def dashboard(message: Message, session) -> None:
    svc = ReportService(session)
    s = await svc.get_summary()
    await message.answer(
        f"📊 <b>Umumiy statistika</b>\n\n"
        f"📦 Jami zakazlar: <b>{s.total}</b>\n"
        f"  🆕 Yangi: {s.new}\n"
        f"  ✅ Tasdiqlangan: {s.confirmed}\n"
        f"  🔧 Ishda: {s.in_work}\n"
        f"  🏁 Yakunlangan: {s.done}\n"
        f"  ❌ Bekor: {s.cancelled}\n\n"
        f"💰 Jami tushum: <b>{float(s.revenue):,.0f} so'm</b>\n"
        f"💵 Yig'ilgan: <b>{float(s.collected):,.0f} so'm</b>\n"
        f"💳 Umumiy qarz: <b>{float(s.debt):,.0f} so'm</b>\n\n"
        f"📅 <b>Bu oy:</b>\n"
        f"  Zakazlar: <b>{s.month_total}</b>\n"
        f"  Tushum: <b>{float(s.month_revenue):,.0f} so'm</b>"
    )


# ── Master report ──────────────────────────────────────────────────────────────

@router.message(F.text == "👷 Master hisoboti", RoleFilter(*ADMIN_ROLES))
async def master_report_menu(message: Message) -> None:
    await message.answer(
        "👷 <b>Master hisoboti</b>\n\nDavrni tanlang:",
        reply_markup=_period_keyboard("master_report"),
    )


@router.callback_query(F.data.startswith("master_report:"), RoleFilter(*ADMIN_ROLES))
async def master_report(callback: CallbackQuery, session) -> None:
    period = callback.data.split(":")[1]
    start, end = ReportService.period_bounds(period)
    svc = ReportService(session)
    stats = await svc.get_master_stats(start, end)

    period_label = _PERIOD_LABELS.get(period, period)
    if not stats:
        await callback.message.edit_text(
            f"👷 <b>Master hisoboti</b> — {period_label}\n\nMa'lumot yo'q."
        )
        await callback.answer()
        return

    lines = [f"👷 <b>Master hisoboti</b> — {period_label}\n"]
    for i, st in enumerate(stats, 1):
        name = st.master.full_name or str(st.master.telegram_id)
        lines.append(
            f"\n{i}. <b>{name}</b>\n"
            f"   📦 Zakazlar: {st.order_count}\n"
            f"   💰 Tushum: {float(st.total_revenue):,.0f} so'm\n"
            f"   💼 Komissiya: {float(st.total_commission):,.0f} so'm"
        )

    builder = InlineKeyboardBuilder()
    for key, label in _PERIOD_LABELS.items():
        builder.button(text=label, callback_data=f"master_report:{key}")
    builder.adjust(2)
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=builder.as_markup()
    )
    await callback.answer()


# ── Usta report ───────────────────────────────────────────────────────────────

@router.message(F.text == "🔨 Usta hisoboti", RoleFilter(*ADMIN_ROLES))
async def usta_report_menu(message: Message) -> None:
    await message.answer(
        "🔨 <b>Usta hisoboti</b>\n\nDavrni tanlang:",
        reply_markup=_period_keyboard("usta_report"),
    )


@router.callback_query(F.data.startswith("usta_report:"), RoleFilter(*ADMIN_ROLES))
async def usta_report(callback: CallbackQuery, session) -> None:
    period = callback.data.split(":")[1]
    start, end = ReportService.period_bounds(period)
    svc = ReportService(session)
    stats = await svc.get_usta_stats(start, end)

    period_label = _PERIOD_LABELS.get(period, period)
    if not stats:
        await callback.message.edit_text(
            f"🔨 <b>Usta hisoboti</b> — {period_label}\n\nMa'lumot yo'q."
        )
        await callback.answer()
        return

    lines = [f"🔨 <b>Usta hisoboti</b> — {period_label}\n"]
    for i, st in enumerate(stats, 1):
        name = st.usta.full_name or str(st.usta.telegram_id)
        lines.append(
            f"\n{i}. <b>{name}</b>\n"
            f"   📦 Zakazlar: {st.order_count}\n"
            f"   💰 Ish haqi: {float(st.total_wage):,.0f} so'm"
        )

    builder = InlineKeyboardBuilder()
    for key, label in _PERIOD_LABELS.items():
        builder.button(text=label, callback_data=f"usta_report:{key}")
    builder.adjust(2)
    await callback.message.edit_text(
        "\n".join(lines), reply_markup=builder.as_markup()
    )
    await callback.answer()
