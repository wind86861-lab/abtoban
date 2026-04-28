"""TMA admin API routes — Hududlar, Zavodlar, Orders, Users, Materials."""
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from app.config import settings
from app.db.models import (
    ROLE_LABELS, AsphaltCategory, AsphaltSubCategory, AsphaltType,
    MaterialRequest, MaterialRequestStatus, Order, OrderLineItem, OrderStatus,
    Region, Tuman, User, UserRole, Viloyat, Zavod, zavod_hududlar, user_hududlar,
)
from app.db.session import async_session_maker

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _line_item_cost(li) -> float:
    """Return effective cost price per m²: use snapshot if available, else current asphalt type cost."""
    snapshot = float(li.cost_price_per_m2 or 0)
    if snapshot > 0:
        return snapshot
    if li.asphalt_type:
        return float(li.asphalt_type.cost_price_per_m2 or 0)
    return 0.0


def _material_cost(o) -> float:
    """Material cost from line items, or fallback to order's main asphalt type × area."""
    if o.line_items:
        return sum(_line_item_cost(li) * float(li.area_m2 or 0) for li in o.line_items)
    if o.asphalt_type and o.area_m2:
        cost = float(o.asphalt_type.cost_price_per_m2 or 0)
        if cost > 0:
            return cost * float(o.area_m2)
    return 0.0


# ─────────────────────────────────────────────────────────────
# TMA AUTH — Login / Logout
# ─────────────────────────────────────────────────────────────

@router.get("/tma-login", response_class=HTMLResponse)
async def tma_login_page(request: Request):
    return templates.TemplateResponse("tma_login.html", {"request": request, "error": None})


@router.post("/tma-login")
async def tma_login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    next_url = request.query_params.get("next", "/tma-admin")

    # 1) Static admin credentials from settings
    if username.strip() == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        request.session["tma_token"] = "admin_ok"
        request.session["tma_role"] = "admin"
        return RedirectResponse(url=next_url, status_code=303)

    # 2) Super admin: phone + password_hash from DB
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(
                User.phone == username.strip(),
                User.role == UserRole.SUPER_ADMIN,
                User.is_active.is_(True),
            )
        )
        user = result.scalar_one_or_none()
        if user and user.password_hash and user.password_hash == _hash(password):
            request.session["tma_token"] = "superadmin_ok"
            request.session["tma_role"] = "super_admin"
            request.session["tma_user_id"] = user.id
            return RedirectResponse(url=next_url, status_code=303)

    return templates.TemplateResponse(
        "tma_login.html",
        {"request": request, "error": "Foydalanuvchi nomi yoki parol noto'g'ri"},
        status_code=401,
    )


@router.get("/tma-logout")
async def tma_logout(request: Request):
    request.session.pop("tma_token", None)
    request.session.pop("tma_role", None)
    request.session.pop("tma_user_id", None)
    return RedirectResponse(url="/tma-login", status_code=303)


@router.get("/tma-admin", response_class=HTMLResponse)
async def tma_admin_page(request: Request):
    """Lightweight admin dashboard for Telegram Mini App."""
    role = request.session.get("tma_role", "admin")
    response = templates.TemplateResponse("tma_admin.html", {"request": request, "tma_role": role})
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.get("/shop", response_class=HTMLResponse)
async def tma_shop_page(request: Request):
    """Online marketplace web app for clients."""
    return templates.TemplateResponse("tma_shop_new.html", {"request": request})


@router.get("/tma-api/stats")
async def tma_stats():
    """Get dashboard statistics with chart data."""
    from datetime import datetime, timedelta
    from app.db.models import UserRole

    async with async_session_maker() as session:
        # ── Basic counts ──
        total_orders = (await session.execute(select(func.count(Order.id)))).scalar_one()
        new_orders = (await session.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.NEW)
        )).scalar_one()
        confirmed = (await session.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.CONFIRMED)
        )).scalar_one()
        in_work = (await session.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.IN_WORK)
        )).scalar_one()
        done = (await session.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.DONE)
        )).scalar_one()
        cancelled = (await session.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.CANCELLED)
        )).scalar_one()

        total_users = (await session.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )).scalar_one()

        # ── Revenue ──
        revenue = (await session.execute(
            select(func.sum(Order.total_price)).where(Order.status != OrderStatus.CANCELLED)
        )).scalar_one() or 0
        advance = (await session.execute(
            select(func.sum(Order.advance_paid)).where(Order.status != OrderStatus.CANCELLED)
        )).scalar_one() or 0
        debt = (await session.execute(
            select(func.sum(Order.debt)).where(Order.status != OrderStatus.CANCELLED)
        )).scalar_one() or 0

        # ── Monthly orders (last 6 months) ──
        months = []
        now = datetime.utcnow()
        for i in range(5, -1, -1):
            start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = (start + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            label = start.strftime("%b %Y")
            cnt = (await session.execute(
                select(func.count(Order.id)).where(
                    Order.created_at >= start, Order.created_at < end
                )
            )).scalar_one()
            rev = (await session.execute(
                select(func.coalesce(func.sum(Order.total_price), 0)).where(
                    Order.created_at >= start, Order.created_at < end,
                    Order.status != OrderStatus.CANCELLED,
                )
            )).scalar_one()
            months.append({"label": label, "orders": cnt, "revenue": float(rev)})

        # ── User role breakdown ──
        role_counts = {}
        for role in UserRole:
            role_counts[role.value] = (await session.execute(
                select(func.count(User.id)).where(User.role == role, User.is_active == True)
            )).scalar_one()

    return {
        "total_orders": total_orders,
        "new_orders": new_orders,
        "confirmed": confirmed,
        "in_work": in_work,
        "done": done,
        "cancelled": cancelled,
        "total_users": total_users,
        "revenue": float(revenue),
        "advance": float(advance),
        "debt": float(debt),
        "months": months,
        "role_counts": role_counts,
    }


@router.get("/tma-api/orders")
async def tma_orders(limit: int = 10, status: Optional[str] = None, viloyat_id: Optional[int] = None):
    """Get orders with optional status and viloyat filter."""
    async with async_session_maker() as session:
        q = (
            select(Order)
            .options(
                selectinload(Order.viloyat), selectinload(Order.tuman_rel),
                selectinload(Order.master), selectinload(Order.usta),
                selectinload(Order.asphalt_type),
                selectinload(Order.line_items).selectinload(OrderLineItem.asphalt_type), selectinload(Order.material_requests),
            )
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        if status:
            q = q.where(Order.status == status)
        if viloyat_id:
            q = q.where(Order.viloyat_id == viloyat_id)
        result = await session.execute(q)
        orders = result.scalars().all()
    
    return [
        {
            "id": o.id,
            "number": o.order_number,
            "client": o.client_name,
            "phone": o.client_phone,
            "address": o.address,
            "area": float(o.area_m2) if o.area_m2 else None,
            "total": float(o.total_price) if o.total_price else None,
            "advance": float(o.advance_paid) if o.advance_paid else 0,
            "debt": float(o.debt) if o.debt else 0,
            "usta_wage": float(o.usta_wage) if o.usta_wage else None,
            "master_commission": float(o.master_commission) if o.master_commission else None,
            "material_cost": _material_cost(o),
            "delivery_cost": sum(float(mr.delivery_price or 0) for mr in o.material_requests) if o.material_requests else 0,
            "zavod_cost": _material_cost(o) + (sum(float(mr.delivery_price or 0) for mr in o.material_requests) if o.material_requests else 0),
            "status": o.status.value,
            "latitude": o.latitude,
            "longitude": o.longitude,
            "viloyat_id": o.viloyat_id,
            "viloyat_name": o.viloyat.name if o.viloyat else None,
            "tuman_name": o.tuman_rel.name if o.tuman_rel else None,
            "master_name": o.master.full_name if o.master else None,
            "usta_name": o.usta.full_name if o.usta else None,
            "asphalt": o.asphalt_type.name if o.asphalt_type else None,
            "work_date": o.work_date.strftime("%d.%m.%Y") if o.work_date else None,
            "created_at": o.created_at.strftime("%d.%m.%Y %H:%M") if o.created_at else None,
            "notes": o.notes,
        }
        for o in orders
    ]


class UpdateStatusRequest(BaseModel):
    status: str


@router.patch("/tma-api/orders/{order_id}/status")
async def update_order_status(order_id: int, body: UpdateStatusRequest):
    """Update order status."""
    async with async_session_maker() as session:
        result = await session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            return {"ok": False, "error": "Order not found"}
        order.status = body.status
        if body.status == "done":
            order.completed_at = datetime.utcnow()
        await session.commit()
    return {"ok": True}


@router.get("/tma-api/orders/{order_id}/expenses")
async def tma_order_expenses(order_id: int):
    """Get all extra expenses for a given order with creator names."""
    from app.db.models import Expense, ExpenseType, User
    async with async_session_maker() as session:
        result = await session.execute(
            select(Expense, User.full_name)
            .outerjoin(User, User.id == Expense.created_by)
            .where(Expense.order_id == order_id)
            .order_by(Expense.created_at.asc())
        )
        rows = result.all()
        total = sum(float(e.amount) for e, _ in rows)
        return {
            "order_id": order_id,
            "total": total,
            "count": len(rows),
            "items": [
                {
                    "id": e.id,
                    "type": e.expense_type.value,
                    "amount": float(e.amount),
                    "description": e.description or "—",
                    "created_at": e.created_at.strftime("%d.%m.%Y %H:%M") if e.created_at else "—",
                    "created_by_name": name or f"#{e.created_by}",
                }
                for e, name in rows
            ],
        }


# ─────────────────────────────────────────────────────────────
# CREATE ORDER (Admin / Super-admin from TMA panel)
# ─────────────────────────────────────────────────────────────

class CreateOrderRequest(BaseModel):
    client_name: str
    client_phone: str
    address: str
    viloyat_id: Optional[int] = None
    tuman_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    area_m2: Optional[float] = None
    asphalt_type_id: Optional[int] = None
    total_price: Optional[float] = None
    advance_paid: Optional[float] = None
    usta_wage: Optional[float] = None
    master_commission: Optional[float] = None
    work_date: Optional[str] = None  # YYYY-MM-DD
    notes: Optional[str] = None
    master_id: Optional[int] = None
    usta_id: Optional[int] = None


@router.post("/tma-api/orders")
async def create_order_admin(body: CreateOrderRequest, request: Request):
    """Admin creates a new order from the web panel."""
    from decimal import Decimal
    role = request.session.get("tma_role")
    if role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")

    # Validate phone
    phone = (body.client_phone or "").replace("+", "").replace(" ", "").replace("-", "")
    if not phone.isdigit() or len(phone) < 9:
        raise HTTPException(status_code=400, detail="Noto'g'ri telefon raqam")
    if not body.client_name or len(body.client_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Klient ismini kiriting")
    if not body.address or len(body.address.strip()) < 3:
        raise HTTPException(status_code=400, detail="Manzilni kiriting")

    async with async_session_maker() as session:
        # Generate order number
        today = datetime.now().strftime("%Y%m%d")
        cnt_res = await session.execute(
            select(func.count(Order.id)).where(Order.order_number.like(f"AVT-{today}-%"))
        )
        count = cnt_res.scalar_one() + 1
        order_number = f"AVT-{today}-{count:04d}"

        # Resolve client_id by phone
        existing = (await session.execute(
            select(User).where(User.phone == phone, User.role == UserRole.KLIENT)
        )).scalar_one_or_none()
        client_id = existing.id if existing else None

        # If no klient match, fall back to current admin user_id (or any user)
        if client_id is None:
            admin_uid = request.session.get("tma_user_id")
            if admin_uid:
                client_id = admin_uid
            else:
                # Fall back to first super_admin in DB
                fallback = (await session.execute(
                    select(User).where(User.role == UserRole.SUPER_ADMIN).limit(1)
                )).scalar_one_or_none()
                if not fallback:
                    raise HTTPException(status_code=500, detail="Klient topilmadi")
                client_id = fallback.id

        # Parse work_date
        work_dt = None
        if body.work_date:
            try:
                work_dt = datetime.strptime(body.work_date, "%Y-%m-%d")
            except ValueError:
                pass

        # Compute debt
        total = Decimal(str(body.total_price)) if body.total_price else Decimal("0")
        advance = Decimal(str(body.advance_paid)) if body.advance_paid else Decimal("0")
        debt = total - advance if total > advance else Decimal("0")

        order = Order(
            order_number=order_number,
            client_id=client_id,
            client_name=body.client_name.strip(),
            client_phone=phone,
            address=body.address.strip(),
            latitude=body.latitude,
            longitude=body.longitude,
            viloyat_id=body.viloyat_id,
            tuman_id=body.tuman_id,
            asphalt_type_id=body.asphalt_type_id,
            area_m2=Decimal(str(body.area_m2)) if body.area_m2 else None,
            total_price=total if total > 0 else None,
            advance_paid=advance,
            debt=debt,
            usta_wage=Decimal(str(body.usta_wage)) if body.usta_wage else None,
            master_commission=Decimal(str(body.master_commission)) if body.master_commission else None,
            status=OrderStatus.CONFIRMED if total > 0 else OrderStatus.NEW,
            work_date=work_dt,
            notes=body.notes,
            master_id=body.master_id,
            usta_id=body.usta_id,
            discount=Decimal("0"),
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)

    return {"ok": True, "id": order.id, "number": order.order_number}


@router.get("/tma-api/users")
async def tma_users(limit: int = 100, role: Optional[str] = None, viloyat_id: Optional[int] = None):
    """Get users with optional role and viloyat filter."""
    from sqlalchemy import case, or_
    async with async_session_maker() as session:
        q = (
            select(User)
            .options(
                selectinload(User.region), selectinload(User.zavod),
                selectinload(User.hududlar), selectinload(User.viloyat),
                selectinload(User.tuman_rel),
            )
            .order_by(User.created_at.desc())
            .limit(limit)
        )
        if role:
            q = q.where(User.role == role)
        if viloyat_id:
            q = q.where(User.viloyat_id == viloyat_id)
        result = await session.execute(q)
        users = result.scalars().all()

        # Gather order stats for all users in one query
        user_ids = [u.id for u in users]
        stats_map = {}
        if user_ids:
            stats_q = await session.execute(
                select(
                    Order.client_id, Order.master_id, Order.usta_id,
                    func.count(Order.id).label("total"),
                    func.sum(case((Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.IN_WORK]), 1), else_=0)).label("active"),
                    func.sum(case((Order.status == OrderStatus.DONE, 1), else_=0)).label("done"),
                    func.coalesce(func.sum(Order.total_price), 0).label("total_price"),
                    func.coalesce(func.sum(Order.usta_wage), 0).label("total_wage"),
                )
                .where(or_(
                    Order.client_id.in_(user_ids),
                    Order.master_id.in_(user_ids),
                    Order.usta_id.in_(user_ids),
                ))
                .group_by(Order.client_id, Order.master_id, Order.usta_id)
            )
            for row in stats_q.all():
                for uid in [row.client_id, row.master_id, row.usta_id]:
                    if uid and uid in user_ids:
                        if uid not in stats_map:
                            stats_map[uid] = {"total": 0, "active": 0, "done": 0, "total_price": 0, "total_wage": 0}
                        stats_map[uid]["total"] += row.total
                        stats_map[uid]["active"] += row.active
                        stats_map[uid]["done"] += row.done
                        stats_map[uid]["total_price"] += float(row.total_price)
                        stats_map[uid]["total_wage"] += float(row.total_wage)

    return [
        {
            "id": u.id,
            "telegram_id": u.telegram_id,
            "name": u.full_name or u.username or str(u.telegram_id),
            "phone": u.phone,
            "role": u.role.value,
            "role_label": ROLE_LABELS.get(u.role, u.role.value),
            "region": u.region.name if u.region else None,
            "region_id": u.region_id,
            "viloyat_id": u.viloyat_id,
            "viloyat_name": u.viloyat.name if u.viloyat else None,
            "tuman_name": u.tuman_rel.name if u.tuman_rel else None,
            "zavod_id": u.zavod_id,
            "zavod_name": u.zavod.name if u.zavod else None,
            "hududlar": [{"id": h.id, "viloyat": h.viloyat or h.name, "tuman": h.tuman or ""} for h in u.hududlar],
            "is_active": u.is_active,
            "total_orders": stats_map.get(u.id, {}).get("total", 0),
            "active_orders": stats_map.get(u.id, {}).get("active", 0),
            "done_orders": stats_map.get(u.id, {}).get("done", 0),
            "total_price": stats_map.get(u.id, {}).get("total_price", 0),
            "total_wage": stats_map.get(u.id, {}).get("total_wage", 0),
        }
        for u in users
    ]


class UpdateUserHududlarRequest(BaseModel):
    hudud_ids: List[int]


@router.get("/tma-api/users/{user_id}/hududlar")
async def get_user_hududlar(user_id: int):
    async with async_session_maker() as session:
        user = (await session.execute(
            select(User).options(selectinload(User.hududlar)).where(User.id == user_id)
        )).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
        return [{"id": h.id, "viloyat": h.viloyat or h.name, "tuman": h.tuman or ""} for h in user.hududlar]


@router.put("/tma-api/users/{user_id}/hududlar")
async def set_user_hududlar(user_id: int, body: UpdateUserHududlarRequest):
    """Replace all hudud assignments for a user."""
    async with async_session_maker() as session:
        user = (await session.execute(
            select(User).options(selectinload(User.hududlar)).where(User.id == user_id)
        )).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
        await session.execute(
            delete(user_hududlar).where(user_hududlar.c.user_id == user_id)
        )
        if body.hudud_ids:
            hududlar = (await session.execute(
                select(Region).where(Region.id.in_(body.hudud_ids))
            )).scalars().all()
            user.hududlar = hududlar
            # Also set primary region_id to first selected
            user.region_id = hududlar[0].id if hududlar else None
        else:
            user.hududlar = []
            user.region_id = None
        await session.commit()
    return {"ok": True}


class UpdateRoleRequest(BaseModel):
    role: str


@router.patch("/tma-api/users/{user_id}/role")
async def update_user_role(user_id: int, body: UpdateRoleRequest):
    """Update user role."""
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return {"ok": False, "error": "User not found"}
        user.role = body.role
        await session.commit()
    return {"ok": True}


@router.get("/tma-api/ustalar")
async def tma_ustalar():
    """Get all ustas with order statistics."""
    async with async_session_maker() as session:
        ustas = (await session.execute(
            select(User)
            .options(selectinload(User.viloyat), selectinload(User.tuman_rel))
            .where(User.role == UserRole.USTA)
            .order_by(User.full_name.asc())
        )).scalars().all()

        usta_ids = [u.id for u in ustas]
        if usta_ids:
            # Total orders per usta
            total_q = (await session.execute(
                select(Order.usta_id, func.count(Order.id).label("cnt"))
                .where(Order.usta_id.in_(usta_ids))
                .group_by(Order.usta_id)
            )).all()
            total_map = {r[0]: r[1] for r in total_q}

            # Active orders
            active_q = (await session.execute(
                select(Order.usta_id, func.count(Order.id).label("cnt"))
                .where(Order.usta_id.in_(usta_ids))
                .where(Order.status.in_([OrderStatus.CONFIRMED, OrderStatus.IN_WORK]))
                .group_by(Order.usta_id)
            )).all()
            active_map = {r[0]: r[1] for r in active_q}

            # Completed orders
            done_q = (await session.execute(
                select(Order.usta_id, func.count(Order.id).label("cnt"))
                .where(Order.usta_id.in_(usta_ids))
                .where(Order.status == OrderStatus.DONE)
                .group_by(Order.usta_id)
            )).all()
            done_map = {r[0]: r[1] for r in done_q}

            # Total usta_wage earned
            wage_q = (await session.execute(
                select(Order.usta_id, func.sum(Order.usta_wage).label("total_wage"))
                .where(Order.usta_id.in_(usta_ids))
                .where(Order.status == OrderStatus.DONE)
                .group_by(Order.usta_id)
            )).all()
            wage_map = {r[0]: float(r[1]) if r[1] else 0 for r in wage_q}
        else:
            total_map = active_map = done_map = wage_map = {}

    return [
        {
            "id": u.id,
            "name": u.full_name or str(u.telegram_id),
            "phone": u.phone,
            "is_active": u.is_active,
            "viloyat_name": u.viloyat.name if u.viloyat else None,
            "tuman_name": u.tuman_rel.name if u.tuman_rel else None,
            "total_orders": total_map.get(u.id, 0),
            "active_orders": active_map.get(u.id, 0),
            "done_orders": done_map.get(u.id, 0),
            "total_wage": wage_map.get(u.id, 0),
        }
        for u in ustas
    ]


@router.get("/tma-api/ustalar/{usta_id}/orders")
async def tma_usta_orders(usta_id: int):
    """Get all orders for a specific usta with full details."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Order)
            .options(
                selectinload(Order.master), selectinload(Order.usta),
                selectinload(Order.asphalt_type), selectinload(Order.client),
                selectinload(Order.viloyat), selectinload(Order.tuman_rel),
                selectinload(Order.line_items).selectinload(OrderLineItem.asphalt_type), selectinload(Order.material_requests),
            )
            .where(Order.usta_id == usta_id)
            .order_by(Order.created_at.desc())
        )
        orders = result.scalars().all()

    return [
        {
            "id": o.id,
            "number": o.order_number,
            "client": o.client_name,
            "phone": o.client_phone,
            "address": o.address,
            "area": float(o.area_m2) if o.area_m2 else None,
            "total": float(o.total_price) if o.total_price else None,
            "advance": float(o.advance_paid) if o.advance_paid else 0,
            "debt": float(o.debt) if o.debt else 0,
            "usta_wage": float(o.usta_wage) if o.usta_wage else None,
            "master_commission": float(o.master_commission) if o.master_commission else None,
            "material_cost": _material_cost(o),
            "delivery_cost": sum(float(mr.delivery_price or 0) for mr in o.material_requests) if o.material_requests else 0,
            "zavod_cost": _material_cost(o) + (sum(float(mr.delivery_price or 0) for mr in o.material_requests) if o.material_requests else 0),
            "status": o.status.value,
            "master_name": o.master.full_name if o.master else None,
            "usta_name": o.usta.full_name if o.usta else None,
            "asphalt": o.asphalt_type.name if o.asphalt_type else None,
            "work_date": o.work_date.strftime("%d.%m.%Y") if o.work_date else None,
            "created_at": o.created_at.strftime("%d.%m.%Y %H:%M") if o.created_at else None,
            "viloyat_name": o.viloyat.name if o.viloyat else None,
            "tuman_name": o.tuman_rel.name if o.tuman_rel else None,
        }
        for o in orders
    ]


@router.get("/tma-api/users/{user_id}/orders")
async def tma_user_orders(user_id: int):
    """Get all orders related to a user based on their role."""
    from sqlalchemy import or_
    async with async_session_maker() as session:
        user = (await session.execute(
            select(User).where(User.id == user_id)
        )).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Build filter based on role
        if user.role == UserRole.KLIENT:
            filt = Order.client_id == user_id
        elif user.role == UserRole.MASTER:
            filt = Order.master_id == user_id
        elif user.role == UserRole.USTA:
            filt = Order.usta_id == user_id
        elif user.role in (UserRole.ZAVOD, UserRole.SHOFER):
            filt = Order.zavod_id == user_id
        else:
            # Admin roles — show orders they touched (as master or usta) or all
            filt = or_(
                Order.master_id == user_id,
                Order.usta_id == user_id,
                Order.client_id == user_id,
            )

        result = await session.execute(
            select(Order)
            .options(
                selectinload(Order.master), selectinload(Order.usta),
                selectinload(Order.asphalt_type), selectinload(Order.client),
                selectinload(Order.viloyat), selectinload(Order.tuman_rel),
                selectinload(Order.line_items).selectinload(OrderLineItem.asphalt_type), selectinload(Order.material_requests),
            )
            .where(filt)
            .order_by(Order.created_at.desc())
            .limit(50)
        )
        orders = result.scalars().all()

    role_label = ROLE_LABELS.get(user.role, user.role.value)
    return {
        "role": user.role.value,
        "role_label": role_label,
        "orders": [
            {
                "id": o.id,
                "number": o.order_number,
                "client": o.client_name,
                "phone": o.client_phone,
                "address": o.address,
                "area": float(o.area_m2) if o.area_m2 else None,
                "total": float(o.total_price) if o.total_price else None,
                "advance": float(o.advance_paid) if o.advance_paid else 0,
                "debt": float(o.debt) if o.debt else 0,
                "usta_wage": float(o.usta_wage) if o.usta_wage else None,
                "master_commission": float(o.master_commission) if o.master_commission else None,
                "material_cost": _material_cost(o),
                "delivery_cost": sum(float(mr.delivery_price or 0) for mr in o.material_requests) if o.material_requests else 0,
                "zavod_cost": _material_cost(o) + (sum(float(mr.delivery_price or 0) for mr in o.material_requests) if o.material_requests else 0),
                "status": o.status.value,
                "master_name": o.master.full_name if o.master else None,
                "usta_name": o.usta.full_name if o.usta else None,
                "client_name": o.client.full_name if o.client else None,
                "asphalt": o.asphalt_type.name if o.asphalt_type else None,
                "work_date": o.work_date.strftime("%d.%m.%Y") if o.work_date else None,
                "created_at": o.created_at.strftime("%d.%m.%Y %H:%M") if o.created_at else None,
                "viloyat_name": o.viloyat.name if o.viloyat else None,
                "tuman_name": o.tuman_rel.name if o.tuman_rel else None,
            }
            for o in orders
        ],
    }


class UpdateRegionRequest(BaseModel):
    region_id: Optional[int]


@router.patch("/tma-api/users/{user_id}/region")
async def update_user_region(user_id: int, body: UpdateRegionRequest):
    """Update user region."""
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return {"ok": False, "error": "User not found"}
        user.region_id = body.region_id
        await session.commit()
    return {"ok": True}


class UpdateViloyatRequest(BaseModel):
    viloyat_id: Optional[int]
    tuman_id: Optional[int]


@router.patch("/tma-api/users/{user_id}/viloyat")
async def update_user_viloyat(user_id: int, body: UpdateViloyatRequest):
    """Update user viloyat and tuman."""
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.viloyat_id = body.viloyat_id
        user.tuman_id = body.tuman_id
        await session.commit()
    return {"ok": True}


@router.patch("/tma-api/users/{user_id}/toggle")
async def toggle_user(user_id: int):
    """Toggle user active status."""
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return {"ok": False, "error": "User not found"}
        user.is_active = not user.is_active
        await session.commit()
        return {"ok": True, "is_active": user.is_active}


@router.get("/tma-api/materials")
async def tma_materials():
    """Get pending material requests."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(MaterialRequest)
            .options(
                selectinload(MaterialRequest.order).selectinload(Order.region),
                selectinload(MaterialRequest.usta),
            )
            .where(MaterialRequest.status == MaterialRequestStatus.ADMIN_PENDING)
            .order_by(MaterialRequest.created_at.asc())
        )
        reqs = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "order_number": r.order.order_number if r.order else "—",
            "region": r.order.region.name if r.order and r.order.region else "—",
            "usta": r.usta.full_name if r.usta else "—",
            "tonnes": float(r.amount_tonnes),
            "notes": r.notes or "—",
            "created_at": r.created_at.strftime("%d.%m.%Y %H:%M") if r.created_at else "—",
        }
        for r in reqs
    ]


@router.post("/tma-api/materials/{req_id}/approve")
async def approve_material(req_id: int):
    """Approve material request."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(MaterialRequest).where(MaterialRequest.id == req_id)
        )
        req = result.scalar_one_or_none()
        if not req or req.status != MaterialRequestStatus.ADMIN_PENDING:
            return {"ok": False, "error": "Request not found or already processed"}
        req.status = MaterialRequestStatus.PENDING
        await session.commit()
    return {"ok": True}


@router.post("/tma-api/materials/{req_id}/reject")
async def reject_material(req_id: int):
    """Reject material request."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(MaterialRequest).where(MaterialRequest.id == req_id)
        )
        req = result.scalar_one_or_none()
        if not req or req.status != MaterialRequestStatus.ADMIN_PENDING:
            return {"ok": False, "error": "Request not found or already processed"}
        await session.delete(req)
        await session.commit()
    return {"ok": True}


@router.get("/tma-api/viloyatlar")
async def tma_viloyatlar():
    """Get all active viloyats with their tumans."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Viloyat)
            .options(selectinload(Viloyat.tumans))
            .where(Viloyat.is_active == True)
            .order_by(Viloyat.name)
        )
        viloyats = result.scalars().all()
    return [
        {
            "id": v.id,
            "name": v.name,
            "tumans": [
                {"id": t.id, "name": t.name}
                for t in sorted(v.tumans, key=lambda x: x.name)
                if t.is_active
            ],
        }
        for v in viloyats
    ]


@router.get("/tma-api/roles")
async def tma_roles():
    """Get all user roles."""
    return [{"value": r.value, "label": ROLE_LABELS[r]} for r in UserRole]


# ─────────────────────────────────────────────────────────────
# VILOYATLAR / TUMANLAR CRUD
# ─────────────────────────────────────────────────────────────

class ViloyatRequest(BaseModel):
    name: str

class TumanRequest(BaseModel):
    name: str
    viloyat_id: int

@router.post("/tma-api/viloyatlar")
async def create_viloyat(body: ViloyatRequest):
    async with async_session_maker() as session:
        v = Viloyat(name=body.name.strip())
        session.add(v)
        await session.commit()
        await session.refresh(v)
    return {"ok": True, "id": v.id, "name": v.name}

@router.patch("/tma-api/viloyatlar/{vid}")
async def update_viloyat(vid: int, body: ViloyatRequest):
    async with async_session_maker() as session:
        v = (await session.execute(select(Viloyat).where(Viloyat.id == vid))).scalar_one_or_none()
        if not v:
            raise HTTPException(status_code=404, detail="Viloyat topilmadi")
        v.name = body.name.strip()
        await session.commit()
    return {"ok": True}

@router.delete("/tma-api/viloyatlar/{vid}")
async def delete_viloyat(vid: int):
    async with async_session_maker() as session:
        await session.execute(delete(Viloyat).where(Viloyat.id == vid))
        await session.commit()
    return {"ok": True}

@router.post("/tma-api/tumanlar")
async def create_tuman(body: TumanRequest):
    async with async_session_maker() as session:
        t = Tuman(name=body.name.strip(), viloyat_id=body.viloyat_id)
        session.add(t)
        await session.commit()
        await session.refresh(t)
    return {"ok": True, "id": t.id, "name": t.name}

@router.patch("/tma-api/tumanlar/{tid}")
async def update_tuman(tid: int, body: TumanRequest):
    async with async_session_maker() as session:
        t = (await session.execute(select(Tuman).where(Tuman.id == tid))).scalar_one_or_none()
        if not t:
            raise HTTPException(status_code=404, detail="Tuman topilmadi")
        t.name = body.name.strip()
        t.viloyat_id = body.viloyat_id
        await session.commit()
    return {"ok": True}

@router.delete("/tma-api/tumanlar/{tid}")
async def delete_tuman(tid: int):
    async with async_session_maker() as session:
        await session.execute(delete(Tuman).where(Tuman.id == tid))
        await session.commit()
    return {"ok": True}


# ─────────────────────────────────────────────────────────────
# ASFALT KATEGORIYALARI CRUD
# ─────────────────────────────────────────────────────────────

class AsphaltCategoryRequest(BaseModel):
    name: str

class AsphaltSubCategoryRequest(BaseModel):
    name: str
    category_id: int

class AsphaltMaterialRequest(BaseModel):
    name: str
    subcategory_id: int
    price_per_m2: float
    cost_price_per_m2: Optional[float] = None

class AsphaltMaterialUpdateRequest(BaseModel):
    name: Optional[str] = None
    price_per_m2: Optional[float] = None
    cost_price_per_m2: Optional[float] = None

@router.get("/tma-api/asphalt-categories")
async def get_asphalt_categories():
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
    return [
        {
            "id": c.id, "name": c.name, "is_active": c.is_active,
            "subcategories": [
                {
                    "id": s.id, "name": s.name, "is_active": s.is_active,
                    "materials": [
                        {"id": m.id, "name": m.name,
                         "price_per_m2": float(m.price_per_m2),
                         "cost_price_per_m2": float(m.cost_price_per_m2) if m.cost_price_per_m2 else 0,
                         "is_active": m.is_active}
                        for m in sorted(s.asphalt_types, key=lambda x: x.name)
                    ]
                }
                for s in sorted(c.subcategories, key=lambda x: x.name)
            ]
        }
        for c in cats
    ]

@router.post("/tma-api/asphalt-categories")
async def create_asphalt_category(body: AsphaltCategoryRequest):
    async with async_session_maker() as session:
        c = AsphaltCategory(name=body.name.strip())
        session.add(c)
        await session.commit()
        await session.refresh(c)
    return {"ok": True, "id": c.id}

@router.patch("/tma-api/asphalt-categories/{cid}")
async def update_asphalt_category(cid: int, body: AsphaltCategoryRequest):
    async with async_session_maker() as session:
        c = (await session.execute(select(AsphaltCategory).where(AsphaltCategory.id == cid))).scalar_one_or_none()
        if not c:
            raise HTTPException(status_code=404, detail="Topilmadi")
        c.name = body.name.strip()
        await session.commit()
    return {"ok": True}

@router.delete("/tma-api/asphalt-categories/{cid}")
async def delete_asphalt_category(cid: int):
    async with async_session_maker() as session:
        await session.execute(delete(AsphaltCategory).where(AsphaltCategory.id == cid))
        await session.commit()
    return {"ok": True}

@router.post("/tma-api/asphalt-subcategories")
async def create_asphalt_subcategory(body: AsphaltSubCategoryRequest):
    async with async_session_maker() as session:
        s = AsphaltSubCategory(name=body.name.strip(), category_id=body.category_id)
        session.add(s)
        await session.commit()
        await session.refresh(s)
    return {"ok": True, "id": s.id}

@router.patch("/tma-api/asphalt-subcategories/{sid}")
async def update_asphalt_subcategory(sid: int, body: AsphaltSubCategoryRequest):
    async with async_session_maker() as session:
        s = (await session.execute(select(AsphaltSubCategory).where(AsphaltSubCategory.id == sid))).scalar_one_or_none()
        if not s:
            raise HTTPException(status_code=404, detail="Topilmadi")
        s.name = body.name.strip()
        s.category_id = body.category_id
        await session.commit()
    return {"ok": True}

@router.delete("/tma-api/asphalt-subcategories/{sid}")
async def delete_asphalt_subcategory(sid: int):
    async with async_session_maker() as session:
        await session.execute(delete(AsphaltSubCategory).where(AsphaltSubCategory.id == sid))
        await session.commit()
    return {"ok": True}

@router.post("/tma-api/asphalt-materials")
async def create_asphalt_material(body: AsphaltMaterialRequest):
    from decimal import Decimal
    async with async_session_maker() as session:
        m = AsphaltType(
            name=body.name.strip(),
            subcategory_id=body.subcategory_id,
            price_per_m2=Decimal(str(body.price_per_m2)),
            cost_price_per_m2=Decimal(str(body.cost_price_per_m2 or 0)),
        )
        session.add(m)
        await session.commit()
        await session.refresh(m)
    return {"ok": True, "id": m.id}

@router.patch("/tma-api/asphalt-materials/{mid}")
async def update_asphalt_material(mid: int, body: AsphaltMaterialUpdateRequest):
    from decimal import Decimal
    async with async_session_maker() as session:
        m = (await session.execute(select(AsphaltType).where(AsphaltType.id == mid))).scalar_one_or_none()
        if not m:
            raise HTTPException(status_code=404, detail="Topilmadi")
        if body.name is not None:
            m.name = body.name.strip()
        if body.price_per_m2 is not None:
            m.price_per_m2 = Decimal(str(body.price_per_m2))
        if body.cost_price_per_m2 is not None:
            m.cost_price_per_m2 = Decimal(str(body.cost_price_per_m2))
        await session.commit()
    return {"ok": True}

@router.patch("/tma-api/asphalt-materials/{mid}/toggle")
async def toggle_asphalt_material(mid: int):
    async with async_session_maker() as session:
        m = (await session.execute(select(AsphaltType).where(AsphaltType.id == mid))).scalar_one_or_none()
        if not m:
            raise HTTPException(status_code=404, detail="Topilmadi")
        m.is_active = not m.is_active
        await session.commit()
    return {"ok": True, "is_active": m.is_active}

@router.delete("/tma-api/asphalt-materials/{mid}")
async def delete_asphalt_material(mid: int):
    async with async_session_maker() as session:
        await session.execute(delete(AsphaltType).where(AsphaltType.id == mid))
        await session.commit()
    return {"ok": True}


# ─────────────────────────────────────────────────────────────
# HUDUDLAR (Regions) CRUD
# ─────────────────────────────────────────────────────────────

class HududCreateRequest(BaseModel):
    viloyat: str
    tuman: str
    tafsif: Optional[str] = None


@router.get("/tma-api/hududlar")
async def list_hududlar():
    async with async_session_maker() as session:
        result = await session.execute(select(Region).order_by(Region.viloyat, Region.tuman))
        hududlar = result.scalars().all()
    return [
        {
            "id": h.id,
            "name": h.name,
            "viloyat": h.viloyat or h.name,
            "tuman": h.tuman or "",
            "tafsif": h.tafsif or "",
            "is_active": h.is_active,
        }
        for h in hududlar
    ]


@router.post("/tma-api/hududlar")
async def create_hudud(body: HududCreateRequest):
    name = f"{body.viloyat} — {body.tuman}"
    async with async_session_maker() as session:
        existing = (await session.execute(
            select(Region).where(Region.name == name)
        )).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Bu hudud allaqachon mavjud")
        hudud = Region(name=name, viloyat=body.viloyat, tuman=body.tuman, tafsif=body.tafsif)
        session.add(hudud)
        await session.commit()
        await session.refresh(hudud)
    return {"ok": True, "id": hudud.id, "name": hudud.name}


@router.patch("/tma-api/hududlar/{hudud_id}")
async def update_hudud(hudud_id: int, body: HududCreateRequest):
    async with async_session_maker() as session:
        hudud = (await session.execute(
            select(Region).where(Region.id == hudud_id)
        )).scalar_one_or_none()
        if not hudud:
            raise HTTPException(status_code=404, detail="Hudud topilmadi")
        hudud.viloyat = body.viloyat
        hudud.tuman = body.tuman
        hudud.tafsif = body.tafsif
        hudud.name = f"{body.viloyat} — {body.tuman}"
        await session.commit()
    return {"ok": True}


@router.patch("/tma-api/hududlar/{hudud_id}/toggle")
async def toggle_hudud(hudud_id: int):
    async with async_session_maker() as session:
        hudud = (await session.execute(
            select(Region).where(Region.id == hudud_id)
        )).scalar_one_or_none()
        if not hudud:
            raise HTTPException(status_code=404, detail="Hudud topilmadi")
        hudud.is_active = not hudud.is_active
        await session.commit()
        return {"ok": True, "is_active": hudud.is_active}


@router.delete("/tma-api/hududlar/{hudud_id}")
async def delete_hudud(hudud_id: int):
    async with async_session_maker() as session:
        await session.execute(delete(Region).where(Region.id == hudud_id))
        await session.commit()
    return {"ok": True}


# ─────────────────────────────────────────────────────────────
# ZAVODLAR CRUD
# ─────────────────────────────────────────────────────────────

class ZavodCreateRequest(BaseModel):
    name: str
    tafsif: Optional[str] = None


@router.get("/tma-api/zavodlar")
async def list_zavodlar():
    async with async_session_maker() as session:
        result = await session.execute(
            select(Zavod)
            .options(selectinload(Zavod.hududlar), selectinload(Zavod.users))
            .order_by(Zavod.name)
        )
        zavodlar = result.scalars().all()
    return [
        {
            "id": z.id,
            "name": z.name,
            "tafsif": z.tafsif or "",
            "shofer_narxi": float(z.shofer_narxi) if z.shofer_narxi is not None else None,
            "is_active": z.is_active,
            "hududlar": [
                {"id": h.id, "name": h.name, "viloyat": h.viloyat or "", "tuman": h.tuman or ""}
                for h in z.hududlar
            ],
            "user_count": len(z.users),
        }
        for z in zavodlar
    ]


@router.post("/tma-api/zavodlar")
async def create_zavod(body: ZavodCreateRequest):
    async with async_session_maker() as session:
        existing = (await session.execute(
            select(Zavod).where(Zavod.name == body.name)
        )).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Bu nomli zavod allaqachon mavjud")
        zavod = Zavod(name=body.name, tafsif=body.tafsif)
        session.add(zavod)
        await session.commit()
        await session.refresh(zavod)
    return {"ok": True, "id": zavod.id}


@router.patch("/tma-api/zavodlar/{zavod_id}")
async def update_zavod(zavod_id: int, body: ZavodCreateRequest):
    async with async_session_maker() as session:
        zavod = (await session.execute(
            select(Zavod).where(Zavod.id == zavod_id)
        )).scalar_one_or_none()
        if not zavod:
            raise HTTPException(status_code=404, detail="Zavod topilmadi")
        zavod.name = body.name
        zavod.tafsif = body.tafsif
        await session.commit()
    return {"ok": True}


class ShoferNarxiRequest(BaseModel):
    shofer_narxi: Optional[float] = None


@router.patch("/tma-api/zavodlar/{zavod_id}/shofer-narxi")
async def set_shofer_narxi(zavod_id: int, body: ShoferNarxiRequest):
    """Set/update the shofer narxi for a zavod. Called by zavod users or admin."""
    async with async_session_maker() as session:
        zavod = (await session.execute(
            select(Zavod).where(Zavod.id == zavod_id)
        )).scalar_one_or_none()
        if not zavod:
            raise HTTPException(status_code=404, detail="Zavod topilmadi")
        zavod.shofer_narxi = body.shofer_narxi
        await session.commit()
    return {"ok": True, "shofer_narxi": float(body.shofer_narxi) if body.shofer_narxi is not None else None}


@router.patch("/tma-api/zavodlar/{zavod_id}/toggle")
async def toggle_zavod(zavod_id: int):
    async with async_session_maker() as session:
        zavod = (await session.execute(
            select(Zavod).where(Zavod.id == zavod_id)
        )).scalar_one_or_none()
        if not zavod:
            raise HTTPException(status_code=404, detail="Zavod topilmadi")
        zavod.is_active = not zavod.is_active
        await session.commit()
        return {"ok": True, "is_active": zavod.is_active}


class ZavodHududRequest(BaseModel):
    hudud_ids: List[int]


@router.put("/tma-api/zavodlar/{zavod_id}/hududlar")
async def set_zavod_hududlar(zavod_id: int, body: ZavodHududRequest):
    """Replace all hudud assignments for a zavod."""
    async with async_session_maker() as session:
        zavod = (await session.execute(
            select(Zavod).options(selectinload(Zavod.hududlar)).where(Zavod.id == zavod_id)
        )).scalar_one_or_none()
        if not zavod:
            raise HTTPException(status_code=404, detail="Zavod topilmadi")
        # Remove existing assignments
        await session.execute(
            delete(zavod_hududlar).where(zavod_hududlar.c.zavod_id == zavod_id)
        )
        # Add new ones
        if body.hudud_ids:
            hududlar = (await session.execute(
                select(Region).where(Region.id.in_(body.hudud_ids))
            )).scalars().all()
            zavod.hududlar = hududlar
        else:
            zavod.hududlar = []
        await session.commit()
    return {"ok": True}


class UpdateZavodRequest(BaseModel):
    zavod_id: Optional[int]


@router.patch("/tma-api/users/{user_id}/zavod")
async def update_user_zavod(user_id: int, body: UpdateZavodRequest):
    zavod_id = body.zavod_id
    async with async_session_maker() as session:
        user = (await session.execute(
            select(User).where(User.id == user_id)
        )).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
        user.zavod_id = zavod_id
        await session.commit()
    return {"ok": True}


@router.get("/tma-api/zavodlar/{zavod_id}/orders")
async def zavod_orders(zavod_id: int):
    """Get all orders linked to a zavod (via assigned users or material requests)."""
    from sqlalchemy import or_
    async with async_session_maker() as session:
        # Users that belong to this zavod
        user_ids = [
            u for u in (await session.execute(
                select(User.id).where(User.zavod_id == zavod_id)
            )).scalars().all()
        ]

        order_ids_from_mr = [
            r for r in (await session.execute(
                select(MaterialRequest.order_id).where(MaterialRequest.assigned_zavod_id == zavod_id)
            )).scalars().all()
        ]

        filters = []
        if user_ids:
            filters.append(Order.zavod_id.in_(user_ids))
        if order_ids_from_mr:
            filters.append(Order.id.in_(order_ids_from_mr))

        if not filters:
            return {"zavod_id": zavod_id, "users": [], "orders": []}

        result = await session.execute(
            select(Order)
            .options(
                selectinload(Order.viloyat), selectinload(Order.tuman_rel),
                selectinload(Order.master), selectinload(Order.usta),
                selectinload(Order.asphalt_type),
                selectinload(Order.line_items).selectinload(OrderLineItem.asphalt_type),
                selectinload(Order.material_requests),
            )
            .where(or_(*filters))
            .order_by(Order.created_at.desc())
            .limit(100)
        )
        orders = result.scalars().all()

        # Get zavod users for display
        users_result = await session.execute(
            select(User).where(User.zavod_id == zavod_id)
        )
        zavod_users = users_result.scalars().all()

    return {
        "zavod_id": zavod_id,
        "users": [
            {"id": u.id, "name": u.full_name, "phone": u.phone, "role": u.role.value}
            for u in zavod_users
        ],
        "orders": [
            {
                "id": o.id,
                "number": o.order_number,
                "client": o.client_name,
                "phone": o.client_phone,
                "address": o.address,
                "area": float(o.area_m2) if o.area_m2 else None,
                "total": float(o.total_price) if o.total_price else None,
                "advance": float(o.advance_paid) if o.advance_paid else 0,
                "debt": float(o.debt) if o.debt else 0,
                "usta_wage": float(o.usta_wage) if o.usta_wage else None,
                "master_commission": float(o.master_commission) if o.master_commission else None,
                "material_cost": _material_cost(o),
                "delivery_cost": sum(float(mr.delivery_price or 0) for mr in o.material_requests) if o.material_requests else 0,
                "zavod_cost": _material_cost(o) + (sum(float(mr.delivery_price or 0) for mr in o.material_requests) if o.material_requests else 0),
                "status": o.status.value,
                "master_name": o.master.full_name if o.master else None,
                "usta_name": o.usta.full_name if o.usta else None,
                "asphalt": o.asphalt_type.name if o.asphalt_type else None,
                "work_date": o.work_date.strftime("%d.%m.%Y") if o.work_date else None,
                "created_at": o.created_at.strftime("%d.%m.%Y %H:%M") if o.created_at else None,
                "viloyat_name": o.viloyat.name if o.viloyat else None,
                "tuman_name": o.tuman_rel.name if o.tuman_rel else None,
            }
            for o in orders
        ],
    }


# ─────────────────────────────────────────────────────────────
# BOT SETTINGS (menu button)
# ─────────────────────────────────────────────────────────────

class SetMenuButtonRequest(BaseModel):
    shop_url: str


@router.post("/tma-api/set-menu-button")
async def set_menu_button(body: SetMenuButtonRequest):
    """Set/update the bot's menu button for all private chats."""
    from aiogram.types import MenuButtonWebApp, WebAppInfo
    from app.bot.loader import bot

    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Web Do'kon",
                web_app=WebAppInfo(url=body.shop_url),
            )
        )
        return {"ok": True, "url": body.shop_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tma-api/bot-info")
async def get_bot_info():
    """Get current bot info and WEB_URL setting."""
    from app.config import settings
    base_url = settings.WEB_URL.rsplit("/", 1)[0]
    return {"shop_url": f"{base_url}/shop", "web_url": settings.WEB_URL}


# ─────────────────────────────────────────────────────────────
# APP SETTINGS (consultation / about company / etc.)
# ─────────────────────────────────────────────────────────────

@router.get("/tma-api/app-settings")
async def tma_get_app_settings():
    """Return all editable app settings, merged with defaults."""
    from app.services.app_settings_service import get_all_settings
    return await get_all_settings()


class UpdateAppSettingsRequest(BaseModel):
    settings: Dict[str, str]


@router.put("/tma-api/app-settings")
async def tma_update_app_settings(body: UpdateAppSettingsRequest):
    """Bulk-upsert app settings."""
    from app.services.app_settings_service import set_settings
    await set_settings(body.settings or {})
    return {"ok": True, "count": len(body.settings or {})}
