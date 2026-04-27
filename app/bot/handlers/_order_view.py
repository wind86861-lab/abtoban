"""Unified order detail formatter for all roles.

Each role sees the appropriate information:
- KLIENT: order details + master contact + usta contact (their service team)
- MASTER: order details + client contact + usta contact + commission
- USTA: order details + client contact + master contact + wage
- ADMIN/BOSH_MASTER: full info with all contacts and costs
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Optional

from app.bot.i18n.core import location_link
from app.db.models import ORDER_STATUS_LABELS, Order, UserRole


def _money(value) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return "—"


def _date(dt) -> str:
    return dt.strftime("%d.%m.%Y") if dt else "—"


def _datetime(dt) -> str:
    return dt.strftime("%d.%m.%Y %H:%M") if dt else "—"


def _contact(label: str, user, fallback: str = "Tayinlanmagan") -> str:
    if not user:
        return f"{label}: <b>{fallback}</b>\n"
    name = user.full_name or "—"
    phone = user.phone or "—"
    return f"{label}: <b>{name}</b>\n   📱 <code>{phone}</code>\n"


def _line_items(order: Order) -> str:
    items = getattr(order, "line_items", None) or []
    if not items:
        asphalt = order.asphalt_type.name if order.asphalt_type else "—"
        return f"🏗 <b>{asphalt}</b>: {order.area_m2 or '?'} m²\n"
    text = ""
    for i, li in enumerate(items, 1):
        marker = "🏗" if li.is_main else "➕"
        name = li.description or (li.asphalt_type.name if li.asphalt_type else "—")
        text += (
            f"{marker} {i}. <b>{name}</b>\n"
            f"   {float(li.area_m2):,.0f} m² × {_money(li.price_per_m2)} = "
            f"<b>{_money(li.subtotal)} so'm</b>\n"
        )
    return text


def format_order_full(order: Order, viewer_role: UserRole, lang: str = "uz_lat") -> str:
    """Format complete order details based on viewer role."""
    status_label = ORDER_STATUS_LABELS.get(order.status, str(order.status))

    # Location
    viloyat = getattr(order, "viloyat", None)
    tuman = getattr(order, "tuman_rel", None)
    loc_parts = []
    if viloyat:
        loc_parts.append(viloyat.name)
    if tuman:
        loc_parts.append(tuman.name)
    loc_str = ", ".join(loc_parts) if loc_parts else "—"
    loc_link = location_link(order.latitude, order.longitude)

    text = (
        f"📋 <b>Zakaz: {order.order_number}</b>\n"
        f"📊 Holat: <b>{status_label}</b>\n\n"
        f"🗺 Viloyat/Tuman: <b>{loc_str}</b>\n"
        f"📍 Manzil: <b>{order.address or '—'}</b>\n"
        f"{loc_link}"
    )

    # Line items
    text += "\n" + _line_items(order)

    # Dates
    text += (
        f"\n📅 Ish sanasi: <b>{_date(order.work_date)}</b>\n"
        f"🗓 Yaratildi: <b>{_datetime(order.created_at)}</b>\n"
    )

    # Role-specific contacts & financials
    is_admin = viewer_role in (UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.HELPER_ADMIN)

    text += "\n👥 <b>Aloqa:</b>\n"
    if is_admin or viewer_role == UserRole.MASTER or viewer_role == UserRole.USTA:
        text += _contact("👤 Klient", getattr(order, "client", None))
    if is_admin or viewer_role == UserRole.USTA or viewer_role == UserRole.KLIENT:
        text += _contact("👷‍♂️ Mutaxassis", getattr(order, "master", None))
    if is_admin or viewer_role == UserRole.MASTER or viewer_role == UserRole.KLIENT:
        text += _contact("🔨 Master", getattr(order, "usta", None))

    # Financial section
    text += "\n💰 <b>Moliyaviy:</b>\n"
    text += f"💵 Umumiy: <b>{_money(order.total_price)} so'm</b>\n"
    if is_admin or viewer_role == UserRole.KLIENT or viewer_role == UserRole.MASTER:
        text += f"💳 Avans: <b>{_money(order.advance_paid)} so'm</b>\n"
        text += f"📉 Qarz: <b>{_money(order.debt)} so'm</b>\n"
    if is_admin or viewer_role == UserRole.USTA:
        text += f"🔨 Master haqi: <b>{_money(order.usta_wage)} so'm</b>\n"
    if is_admin or viewer_role == UserRole.MASTER:
        text += f"🎯 Mutaxassis komissiyasi: <b>{_money(order.master_commission)} so'm</b>\n"

    if order.notes:
        text += f"\n📝 Izoh: <i>{order.notes}</i>\n"

    return text


def _format_duration(start, end) -> str:
    if not start or not end:
        return "—"
    delta = end - start
    days = delta.days
    hours = delta.seconds // 3600
    if days > 0:
        return f"{days} kun {hours} soat"
    minutes = (delta.seconds % 3600) // 60
    return f"{hours} soat {minutes} daq"


def format_order_completion_report(
    order: Order,
    viewer_role: UserRole,
    expenses: Optional[Iterable] = None,
) -> str:
    """Comprehensive report sent on task completion to admin/master/client.

    - ADMIN: full info — all parties, all costs, expenses breakdown, profit.
    - MASTER: order info + usta + commission + duration.
    - KLIENT: friendly summary — area, price, duration, address.
    """
    expenses = list(expenses or [])
    is_admin = viewer_role in (UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.HELPER_ADMIN)

    # Common header
    viloyat = getattr(order, "viloyat", None)
    tuman = getattr(order, "tuman_rel", None)
    loc_parts = [v.name for v in (viloyat, tuman) if v]
    loc_str = ", ".join(loc_parts) if loc_parts else "—"

    duration = _format_duration(
        order.confirmed_at or order.created_at,
        order.completed_at or datetime.now(timezone.utc),
    )

    if viewer_role == UserRole.KLIENT:
        text = (
            f"🎉 <b>Zakaz yakunlandi!</b>\n\n"
            f"🔢 #{order.order_number}\n"
            f"📍 Manzil: <b>{order.address or '—'}</b>\n"
            f"🗺 {loc_str}\n"
            f"📐 Maydon: <b>{order.area_m2 or '?'} m²</b>\n"
            f"💵 Narxi: <b>{_money(order.total_price)} so'm</b>\n"
            f"💳 Avans: <b>{_money(order.advance_paid)} so'm</b>\n"
            f"📉 Qarz: <b>{_money(order.debt)} so'm</b>\n"
            f"⏱ Muddati: <b>{duration}</b>\n"
            f"📅 Tugatildi: <b>{_datetime(order.completed_at)}</b>\n\n"
            f"Bizni tanlaganingiz uchun rahmat! 🙏"
        )
        return text

    if viewer_role == UserRole.MASTER:
        usta_name = order.usta.full_name if order.usta else "—"
        text = (
            f"✅ <b>Master ishni tugatdi!</b>\n\n"
            f"🔢 #{order.order_number}\n"
            f"🔨 Master: <b>{usta_name}</b>\n"
            f"📍 {order.address or '—'}\n"
            f"📐 {order.area_m2 or '?'} m²\n"
            f"💵 Umumiy: <b>{_money(order.total_price)} so'm</b>\n"
            f"🎯 Sizning komissiyangiz: <b>{_money(order.master_commission)} so'm</b>\n"
            f"⏱ Muddati: <b>{duration}</b>\n"
            f"📅 Tugatildi: <b>{_datetime(order.completed_at)}</b>\n"
        )
        return text

    # ADMIN / SUPER_ADMIN / HELPER_ADMIN — full report
    client_name = order.client.full_name if order.client else "—"
    client_phone = order.client.phone if order.client else "—"
    master_name = order.master.full_name if order.master else "—"
    master_phone = order.master.phone if order.master else "—"
    usta_name = order.usta.full_name if order.usta else "—"
    usta_phone = order.usta.phone if order.usta else "—"

    expenses_total = sum((float(e.amount) for e in expenses), 0.0)
    expenses_block = ""
    if expenses:
        expenses_block = "\n💸 <b>Qo'shimcha harajatlar:</b>\n"
        for e in expenses:
            try:
                from app.services.expense_service import EXPENSE_LABELS
                label = EXPENSE_LABELS.get(e.expense_type, str(e.expense_type))
            except Exception:
                label = getattr(e, "expense_type", "—")
            desc = f" — {e.description}" if getattr(e, "description", None) else ""
            expenses_block += f"  • {label}: <b>{_money(e.amount)} so'm</b>{desc}\n"
        expenses_block += f"  ➖ Jami harajat: <b>{_money(expenses_total)} so'm</b>\n"

    # Profit calculation
    total = float(order.total_price or 0)
    usta_wage = float(order.usta_wage or 0)
    master_comm = float(order.master_commission or 0)
    profit = total - usta_wage - master_comm - expenses_total

    text = (
        f"🎉 <b>ZAKAZ YAKUNLANDI</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🔢 #{order.order_number}\n"
        f"📅 Tugatildi: <b>{_datetime(order.completed_at)}</b>\n"
        f"⏱ Muddati: <b>{duration}</b>\n\n"
        f"📍 <b>Joylashuv:</b>\n"
        f"   🗺 {loc_str}\n"
        f"   📍 {order.address or '—'}\n\n"
        f"📐 <b>Ish hajmi:</b>\n"
        + _line_items(order)
        + f"\n👥 <b>Ishtirokchilar:</b>\n"
        f"   👤 Klient: <b>{client_name}</b>\n"
        f"      📱 <code>{client_phone}</code>\n"
        f"   👷‍♂️ Mutaxassis: <b>{master_name}</b>\n"
        f"      📱 <code>{master_phone}</code>\n"
        f"   🔨 Master: <b>{usta_name}</b>\n"
        f"      📱 <code>{usta_phone}</code>\n\n"
        f"💰 <b>Moliya:</b>\n"
        f"   💵 Umumiy narx: <b>{_money(order.total_price)} so'm</b>\n"
        f"   💳 Avans: <b>{_money(order.advance_paid)} so'm</b>\n"
        f"   📉 Qarz: <b>{_money(order.debt)} so'm</b>\n"
        f"   🔨 Master haqi: <b>{_money(order.usta_wage)} so'm</b>\n"
        f"   🎯 Mutaxassis komissiya: <b>{_money(order.master_commission)} so'm</b>\n"
        f"{expenses_block}"
        f"\n📊 <b>Sof foyda: {_money(profit)} so'm</b>\n"
    )
    if order.notes:
        text += f"\n📝 Izoh: <i>{order.notes}</i>\n"
    return text
