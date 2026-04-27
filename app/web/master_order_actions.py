"""
Master Order Actions: confirm new orders and change order status.
Mirrors the Telegram bot's master confirm flow.
"""
import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation

from sqladmin import BaseView, expose
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.db.models import (
    AuditLog, AsphaltType, AsphaltCategory, AsphaltSubCategory,
    Order, OrderLineItem, OrderStatus, User, UserRole, Viloyat, Tuman,
)
from app.db.session import async_session_maker


def _d(raw: str) -> Decimal | None:
    """Parse a decimal from user input."""
    cleaned = (raw or "").strip().replace(" ", "").replace(",", ".")
    try:
        val = Decimal(cleaned)
        return val if val >= 0 else None
    except (InvalidOperation, ValueError):
        return None


async def _load_categories_json() -> str:
    """Load the full Category → SubCategory → Material tree as JSON for the frontend."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(AsphaltCategory)
            .options(
                selectinload(AsphaltCategory.subcategories)
                .selectinload(AsphaltSubCategory.asphalt_types)
            )
            .order_by(AsphaltCategory.name)
        )
        cats = result.scalars().all()

    tree = []
    for c in cats:
        if not c.is_active:
            continue
        subs = []
        for s in sorted(c.subcategories, key=lambda x: x.name):
            if not s.is_active:
                continue
            materials = []
            for m in sorted(s.asphalt_types, key=lambda x: x.name):
                if not m.is_active:
                    continue
                materials.append({
                    "id": m.id,
                    "name": m.name,
                    "price": float(m.price_per_m2),
                    "cost": float(m.cost_price_per_m2 or 0),
                })
            if materials:
                subs.append({"id": s.id, "name": s.name, "materials": materials})
        if subs:
            tree.append({"id": c.id, "name": c.name, "subs": subs})
    return json.dumps(tree, ensure_ascii=False)


class MasterOrderActionsView(BaseView):
    name = "Zakazlarni Boshqarish"
    icon = "fa-solid fa-clipboard-check"

    # ── helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def _master_id(request: Request) -> int | None:
        return request.session.get("user_id") or request.session.get("master_user_id")

    # ── main page ────────────────────────────────────────────────────────────
    @expose("/order-actions", methods=["GET"])
    async def order_actions_page(self, request: Request):
        uid = self._master_id(request)
        if not uid:
            return RedirectResponse(url="/master-panel/admin/login", status_code=302)

        msg = request.query_params.get("msg", "")

        categories_json = await _load_categories_json()

        async with async_session_maker() as session:
            # New orders (available to confirm)
            new_q = await session.execute(
                select(Order)
                .options(
                    selectinload(Order.viloyat),
                    selectinload(Order.tuman_rel),
                    selectinload(Order.asphalt_type),
                    selectinload(Order.client),
                )
                .where(Order.status == OrderStatus.NEW)
                .order_by(Order.created_at.desc())
                .limit(50)
            )
            new_orders = new_q.scalars().all()

            # Master's active orders (for status change)
            my_q = await session.execute(
                select(Order)
                .options(
                    selectinload(Order.viloyat),
                    selectinload(Order.tuman_rel),
                    selectinload(Order.usta),
                    selectinload(Order.asphalt_type),
                    selectinload(Order.line_items),
                )
                .where(
                    Order.master_id == uid,
                    Order.status.in_([
                        OrderStatus.CONFIRMED,
                        OrderStatus.IN_WORK,
                    ]),
                )
                .order_by(Order.created_at.desc())
                .limit(50)
            )
            my_orders = my_q.scalars().all()

            # Ustas for confirm form
            ustas_q = await session.execute(
                select(User).where(
                    User.role == UserRole.USTA,
                    User.is_active.is_(True),
                )
            )
            ustas = ustas_q.scalars().all()

        return await self.templates.TemplateResponse(
            request,
            "master_order_actions.html",
            context={
                "new_orders": new_orders,
                "my_orders": my_orders,
                "ustas": ustas,
                "msg": msg,
                "categories_json": categories_json,
            },
        )

    # ── confirm order (POST) ─────────────────────────────────────────────────
    @expose("/order-actions/confirm", methods=["POST"])
    async def confirm_order(self, request: Request):
        uid = self._master_id(request)
        if not uid:
            return RedirectResponse(url="/master-panel/admin/login", status_code=302)

        form = await request.form()
        order_id = int(form.get("order_id") or 0)
        area = _d(form.get("area_m2", ""))
        agreed_total = _d(form.get("total_price", ""))
        advance = _d(form.get("advance_paid", ""))
        address = (form.get("address") or "").strip()
        work_date_str = (form.get("work_date") or "").strip()
        usta_wage = _d(form.get("usta_wage", ""))
        commission = _d(form.get("master_commission", ""))
        notes = (form.get("notes") or "").strip() or None
        usta_id = form.get("usta_id", "")

        # Parse line items JSON from hidden field
        line_items_raw = form.get("line_items_json", "[]")
        try:
            line_items_data = json.loads(line_items_raw)
        except (json.JSONDecodeError, TypeError):
            line_items_data = []

        base = "/master-panel/admin/order-actions"

        if not order_id or area is None or agreed_total is None or advance is None or not address:
            return RedirectResponse(url=f"{base}?msg=error_fields", status_code=303)

        # parse date
        work_date = None
        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
            try:
                work_date = datetime.strptime(work_date_str, fmt)
                break
            except ValueError:
                continue
        if not work_date:
            return RedirectResponse(url=f"{base}?msg=error_date", status_code=303)

        async with async_session_maker() as session:
            result = await session.execute(
                select(Order).where(Order.id == order_id, Order.status == OrderStatus.NEW)
            )
            order = result.scalar_one_or_none()
            if not order:
                return RedirectResponse(url=f"{base}?msg=error_order", status_code=303)

            now = datetime.now(timezone.utc)
            order.master_id = uid
            order.area_m2 = area
            order.total_price = agreed_total
            order.advance_paid = advance
            order.debt = max(Decimal("0"), agreed_total - advance)
            order.address = address
            order.work_date = work_date
            order.usta_wage = usta_wage or Decimal("0")
            order.master_commission = commission or Decimal("0")
            order.notes = notes
            order.status = OrderStatus.CONFIRMED
            order.confirmed_at = now
            order.usta_assignment_deadline = now + timedelta(minutes=30)

            if usta_id:
                order.usta_id = int(usta_id)

            # Create line items and compute calculated_total
            calc_total = Decimal("0")
            main_asphalt_set = False
            for idx, item in enumerate(line_items_data):
                at_id = int(item.get("asphalt_type_id") or 0) or None
                item_area = _d(str(item.get("area_m2", ""))) or area
                item_price = _d(str(item.get("price_per_m2", ""))) or Decimal("0")
                item_cost = _d(str(item.get("cost_price_per_m2", ""))) or Decimal("0")
                item_desc = (item.get("description") or "").strip() or None
                is_main = bool(item.get("is_main", False))
                sub = item_area * item_price

                li = OrderLineItem(
                    order_id=order_id,
                    asphalt_type_id=at_id,
                    description=item_desc,
                    area_m2=item_area,
                    price_per_m2=item_price,
                    cost_price_per_m2=item_cost,
                    subtotal=sub,
                    is_main=is_main,
                )
                session.add(li)
                calc_total += sub

                # Set the main asphalt type on the order for backward compat
                if is_main and at_id and not main_asphalt_set:
                    order.asphalt_type_id = at_id
                    main_asphalt_set = True

            order.calculated_total = calc_total

            log = AuditLog(
                user_id=uid,
                action="order_confirmed",
                entity_type="order",
                entity_id=order_id,
                old_value=OrderStatus.NEW.value,
                new_value=OrderStatus.CONFIRMED.value,
            )
            session.add(log)
            await session.commit()

        return RedirectResponse(url=f"{base}?msg=confirmed", status_code=303)

    # ── change status (GET → redirect, POST → save) ────────────────────────
    @expose("/order-actions/status", methods=["GET"])
    async def change_status_get(self, request: Request):
        return RedirectResponse(url="/master-panel/admin/order-actions", status_code=302)

    @expose("/order-actions/status-save", methods=["GET", "POST"])
    async def change_status(self, request: Request):
        if request.method == "GET":
            return RedirectResponse(url="/master-panel/admin/order-actions", status_code=302)
        uid = self._master_id(request)
        if not uid:
            return RedirectResponse(url="/master-panel/admin/login", status_code=302)

        form = await request.form()
        order_id = int(form.get("order_id") or 0)
        new_status_val = form.get("new_status", "")
        base = "/master-panel/admin/order-actions"

        allowed = {
            "in_work": OrderStatus.IN_WORK,
            "done": OrderStatus.DONE,
        }
        new_status = allowed.get(new_status_val)
        if not new_status:
            return RedirectResponse(url=f"{base}?msg=error_status", status_code=303)

        async with async_session_maker() as session:
            result = await session.execute(
                select(Order).where(
                    Order.id == order_id,
                    Order.master_id == uid,
                )
            )
            order = result.scalar_one_or_none()
            if not order:
                return RedirectResponse(url=f"{base}?msg=error_order", status_code=303)

            old_status = order.status
            order.status = new_status
            if new_status == OrderStatus.DONE:
                order.completed_at = datetime.now(timezone.utc)

            log = AuditLog(
                user_id=uid,
                action="status_change",
                entity_type="order",
                entity_id=order_id,
                old_value=old_status.value,
                new_value=new_status.value,
            )
            session.add(log)
            await session.commit()

        return RedirectResponse(url=f"{base}?msg=status_ok", status_code=303)
