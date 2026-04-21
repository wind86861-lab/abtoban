"""TMA admin API routes — Hududlar, Zavodlar, Orders, Users, Materials."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from app.db.models import (
    ROLE_LABELS, MaterialRequest, MaterialRequestStatus, Order, OrderStatus,
    Region, Tuman, User, UserRole, Viloyat, Zavod, zavod_hududlar, user_hududlar,
)
from app.db.session import async_session_maker

router = APIRouter()
templates = Jinja2Templates(directory="app/web/templates")


@router.get("/tma-admin", response_class=HTMLResponse)
async def tma_admin_page(request: Request):
    """Lightweight admin dashboard for Telegram Mini App."""
    return templates.TemplateResponse("tma_admin.html", {"request": request})


@router.get("/shop", response_class=HTMLResponse)
async def tma_shop_page(request: Request):
    """Online marketplace web app for clients."""
    return templates.TemplateResponse("tma_shop_new.html", {"request": request})


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
async def tma_orders(limit: int = 10, status: Optional[str] = None, viloyat_id: Optional[int] = None):
    """Get orders with optional status and viloyat filter."""
    async with async_session_maker() as session:
        q = (
            select(Order)
            .options(
                selectinload(Order.viloyat), selectinload(Order.tuman_rel),
                selectinload(Order.master), selectinload(Order.usta),
                selectinload(Order.asphalt_type),
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


@router.get("/tma-api/users")
async def tma_users(limit: int = 100, role: Optional[str] = None, viloyat_id: Optional[int] = None):
    """Get users with optional role and viloyat filter."""
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
