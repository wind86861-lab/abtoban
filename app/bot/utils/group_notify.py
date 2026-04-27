"""Send notifications to the EVRO_ASFALT Telegram group."""

GROUP_CHAT_ID = "@EVRO_ASFALT"


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
    except Exception:
        pass


async def notify_order_done(bot, order) -> None:
    """Send order completion notification to group."""
    try:
        asphalt = order.asphalt_type.name if order.asphalt_type else "—"
        viloyat = order.viloyat.name if order.viloyat else "—"
        usta_name = order.usta.full_name if order.usta else "—"
        completed = (
            order.completed_at.strftime("%d.%m.%Y %H:%M")
            if order.completed_at
            else "—"
        )
        text = (
            f"✅ <b>Zakaz yakunlandi!</b>\n\n"
            f"📋 {order.order_number}\n"
            f"📍 {order.address or '—'} ({viloyat})\n"
            f"🏗 Asfalt: {asphalt} | {float(order.area_m2 or 0):,.1f} m²\n"
            f"👤 Klient: {order.client_name or '—'}\n"
            f"👷 Usta: {usta_name}\n"
            f"📅 {completed}"
        )
        await bot.send_message(GROUP_CHAT_ID, text)
    except Exception:
        pass
