"""Simple API routes for Telegram Mini App admin dashboard."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from app.db.models import (
    ROLE_LABELS, MaterialRequest, MaterialRequestStatus, Order, OrderStatus,
    Region, User, UserRole,
)
from app.db.session import async_session_maker

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/tma-admin", response_class=HTMLResponse)
async def tma_admin_page(request: Request):
    """Lightweight admin dashboard for Telegram Mini App."""
    return templates.TemplateResponse("tma_admin.html", {"request": request})


@router.get("/tma-api/stats")
async def tma_stats():
    """Get dashboard statistics."""
    async with async_session_maker() as session:
        total_orders = (await session.execute(select(func.count(Order.id)))).scalar_one()
        new_orders = (await session.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.NEW)
        )).scalar_one()
        in_work = (await session.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.IN_WORK)
        )).scalar_one()
        total_users = (await session.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )).scalar_one()
    
    return {
        "total_orders": total_orders,
        "new_orders": new_orders,
        "in_work": in_work,
        "total_users": total_users,
    }


@router.get("/tma-api/orders")
async def tma_orders(limit: int = 10, status: Optional[str] = None):
    """Get orders with optional status filter."""
    async with async_session_maker() as session:
        q = select(Order).order_by(Order.created_at.desc()).limit(limit)
        if status:
            q = q.where(Order.status == status)
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
            "status": o.status.value,
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


@router.get("/tma-api/users")
async def tma_users(limit: int = 50, role: Optional[str] = None):
    """Get users with optional role filter."""
    async with async_session_maker() as session:
        q = (
            select(User)
            .options(selectinload(User.region))
            .order_by(User.created_at.desc())
            .limit(limit)
        )
        if role:
            q = q.where(User.role == role)
        result = await session.execute(q)
        users = result.scalars().all()
    
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
            "is_active": u.is_active,
        }
        for u in users
    ]


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


@router.get("/tma-api/regions")
async def tma_regions():
    """Get all active regions."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Region).where(Region.is_active == True).order_by(Region.name)
        )
        regions = result.scalars().all()
    return [{"id": r.id, "name": r.name} for r in regions]


@router.get("/tma-api/roles")
async def tma_roles():
    """Get all user roles."""
    return [{"value": r.value, "label": ROLE_LABELS[r]} for r in UserRole]
