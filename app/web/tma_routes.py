"""Simple API routes for Telegram Mini App admin dashboard."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from starlette.requests import Request

from app.db.models import Order, OrderStatus, User
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
async def tma_orders(limit: int = 10):
    """Get recent orders."""
    async with async_session_maker() as session:
        result = await session.execute(
            select(Order)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        orders = result.scalars().all()
    
    return [
        {
            "id": o.id,
            "number": o.order_number,
            "client": o.client_name,
            "address": o.address,
            "area": float(o.area_m2) if o.area_m2 else None,
            "total": float(o.total_price) if o.total_price else None,
            "status": o.status.value,
        }
        for o in orders
    ]
