"""Send notifications to the EVRO_ASFALT Telegram group."""

import logging

logger = logging.getLogger(__name__)

GROUP_CHAT_ID = "-1003980849177"


async def notify_new_order(bot, order) -> None:
    """Send new order notification to group."""
    try:
        asphalt = order.asphalt_type.name if order.asphalt_type else "—"
        viloyat = order.viloyat.name if order.viloyat else "—"
        text = (
            f"🆕 <b>Yangi zakaz!</b>\n\n"
            f"📋 {order.order_number}\n"
            f"📍 {order.address or '—'} ({viloyat})\n"
            f"🏗 Asfalt: {asphalt} | {float(order.area_m2 or 0):,.1f} m²\n"
            f"👤 Klient: {order.client_name or '—'}"
        )
        await bot.send_message(GROUP_CHAT_ID, text)
        logger.info(f"New order notification sent to {GROUP_CHAT_ID}")
    except Exception as exc:
        logger.error(f"Failed to send new order notification to group {GROUP_CHAT_ID}: {exc!r}")
        logger.error(f"Please verify the bot is a member/admin in {GROUP_CHAT_ID}")


async def notify_order_done(bot, order, session=None) -> None:
    """Send full completion report to group."""
    try:
        logger.info(f"Sending order done notification to group {GROUP_CHAT_ID}, order={order.order_number}")
        asphalt = order.asphalt_type.name if order.asphalt_type else "—"
        viloyat = order.viloyat.name if order.viloyat else "—"
        usta_name = order.usta.full_name if order.usta else "—"
        master_name = order.master.full_name if order.master else "—"
        zavod_name = order.zavod.full_name if order.zavod else "—"
        completed = (
            order.completed_at.strftime("%d.%m.%Y %H:%M")
            if order.completed_at
            else "—"
        )
        total = float(order.total_price or 0)
        advance = float(order.advance_paid or 0)

        # Payment transfer data
        p_collected = p_wage = p_sent = zavod_recv = material_cost = expenses_total = 0
        if session:
            from sqlalchemy import select
            from app.db.models import PaymentTransfer, Expense
            from app.services.expense_service import EXPENSE_LABELS

            # Payment
            r = await session.execute(
                select(PaymentTransfer).where(PaymentTransfer.order_id == order.id)
            )
            pt = r.scalar_one_or_none()
            if pt:
                p_collected = float(pt.usta_collected or 0)
                p_wage = float(pt.usta_wage_taken or 0)
                p_sent = float(pt.usta_sent or 0)
                zavod_recv = float(pt.zavod_received or 0)

            # Material cost
            material_cost = sum(
                float(item.cost_price_per_m2 or 0) * float(item.area_m2 or 0)
                for item in (order.line_items or [])
            )

            # Expenses
            r = await session.execute(
                select(Expense).where(Expense.order_id == order.id)
            )
            expenses = r.scalars().all()
            expenses_total = sum(float(e.amount) for e in expenses)
            expenses_detail = ""
            if expenses:
                lines = [f"    • {EXPENSE_LABELS.get(e.expense_type, e.expense_type)}: {float(e.amount):,.0f}" for e in expenses]
                expenses_detail = "\n" + "\n".join(lines)

        master_kom = float(order.master_commission or 0)
        foyda = total - p_wage - master_kom - material_cost - expenses_total

        text = (
            f"✅ <b>Zakaz yakunlandi!</b>\n\n"
            f"📋 {order.order_number}\n"
            f"📍 {order.address or '—'} ({viloyat})\n"
            f"🏗 Asfalt: {asphalt} | {float(order.area_m2 or 0):,.1f} m²\n"
            f"📅 {completed}\n\n"
            f"👥 Ishtirokchilar:\n"
            f"  👤 Klient: {order.client_name or '—'}\n"
            f"  👷 Usta: {usta_name}\n"
            f"  🧑‍💼 Master: {master_name}\n"
            f"  🏭 Zavod: {zavod_name}\n\n"
            f"� Moliyaviy hisobot:\n"
            f"  📄 Shartnoma: {total:,.0f} so'm\n"
            f"  ✅ Avans: {advance:,.0f} so'm\n"
            f"  💰 Klientdan olingan: {p_collected:,.0f} so'm\n\n"
            f"  📤 Zavodga yuborilgan: {p_sent:,.0f} so'm\n"
            f"  📥 Zavod qabul qildi: {zavod_recv:,.0f} so'm\n\n"
            f"📉 Harajatlar:\n"
            f"  🔧 Usta haqi: {p_wage:,.0f} so'm\n"
            f"  🧑‍💼 Master komissiya: {master_kom:,.0f} so'm\n"
            f"  🏭 Material (tan narxi): {material_cost:,.0f} so'm\n"
            f"  📦 Qo'shimcha: {expenses_total:,.0f} so'm{expenses_detail}\n\n"
            f"📈 <b>Umumiy foyda: {foyda:,.0f} so'm</b>"
        )
        await bot.send_message(GROUP_CHAT_ID, text)
        logger.info(f"Order done notification sent to {GROUP_CHAT_ID}")
    except Exception as exc:
        logger.error(f"Failed to send order done notification to group {GROUP_CHAT_ID}: {exc!r}")
        logger.error(f"Please verify the bot is a member/admin in {GROUP_CHAT_ID}")
