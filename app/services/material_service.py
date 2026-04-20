from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import MaterialRequest, MaterialRequestStatus, Order, User


class MaterialService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        order_id: int,
        usta_id: int,
        amount_tonnes: Decimal,
        notes: Optional[str] = None,
    ) -> MaterialRequest:
        req = MaterialRequest(
            order_id=order_id,
            usta_id=usta_id,
            amount_tonnes=amount_tonnes,
            status=MaterialRequestStatus.ADMIN_PENDING,
            notes=notes,
        )
        self.session.add(req)
        await self.session.flush()
        return req

    async def get_by_id(self, req_id: int) -> Optional[MaterialRequest]:
        result = await self.session.execute(
            select(MaterialRequest)
            .options(
                selectinload(MaterialRequest.order).selectinload(Order.region),
                selectinload(MaterialRequest.usta).selectinload(User.region),
                selectinload(MaterialRequest.zavod),
                selectinload(MaterialRequest.assigned_zavod),
            )
            .where(MaterialRequest.id == req_id)
        )
        return result.scalar_one_or_none()

    async def get_admin_pending(self, region_id: Optional[int] = None) -> List[MaterialRequest]:
        """Get material requests waiting for admin approval, optionally filtered by region."""
        query = (
            select(MaterialRequest)
            .options(
                selectinload(MaterialRequest.order).selectinload(Order.region),
                selectinload(MaterialRequest.usta).selectinload(User.region),
            )
            .where(MaterialRequest.status == MaterialRequestStatus.ADMIN_PENDING)
        )
        if region_id:
            query = query.join(Order).where(Order.region_id == region_id)
        query = query.order_by(MaterialRequest.created_at.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending(self, region_id: Optional[int] = None) -> List[MaterialRequest]:
        """Get material requests approved by admin and ready for zavod pricing."""
        query = (
            select(MaterialRequest)
            .options(
                selectinload(MaterialRequest.order).selectinload(Order.region),
                selectinload(MaterialRequest.usta),
            )
            .where(MaterialRequest.status == MaterialRequestStatus.PENDING)
        )
        if region_id:
            query = query.join(Order).where(Order.region_id == region_id)
        query = query.order_by(MaterialRequest.created_at.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_priced(self, region_id: Optional[int] = None) -> List[MaterialRequest]:
        query = (
            select(MaterialRequest)
            .options(
                selectinload(MaterialRequest.order).selectinload(Order.region),
                selectinload(MaterialRequest.usta),
            )
            .where(MaterialRequest.status == MaterialRequestStatus.PRICED)
        )
        if region_id:
            query = query.join(Order).where(Order.region_id == region_id)
        query = query.order_by(MaterialRequest.created_at.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_usta(self, usta_id: int) -> List[MaterialRequest]:
        result = await self.session.execute(
            select(MaterialRequest)
            .options(selectinload(MaterialRequest.order))
            .where(MaterialRequest.usta_id == usta_id)
            .order_by(MaterialRequest.created_at.desc())
        )
        return list(result.scalars().all())

    async def assign_zavod(self, req_id: int, zavod_id: int) -> Optional[MaterialRequest]:
        result = await self.session.execute(
            select(MaterialRequest).where(MaterialRequest.id == req_id)
        )
        req = result.scalar_one_or_none()
        if not req:
            return None
        req.assigned_zavod_id = zavod_id
        await self.session.flush()
        return req

    async def get_pending_for_zavod(self, zavod_id: int) -> List[MaterialRequest]:
        """Get PENDING material requests assigned to a specific zavod entity."""
        query = (
            select(MaterialRequest)
            .options(
                selectinload(MaterialRequest.order).selectinload(Order.region),
                selectinload(MaterialRequest.usta),
            )
            .where(
                MaterialRequest.status == MaterialRequestStatus.PENDING,
                MaterialRequest.assigned_zavod_id == zavod_id,
            )
            .order_by(MaterialRequest.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_priced_for_zavod(self, zavod_id: int) -> List[MaterialRequest]:
        """Get PRICED material requests assigned to a specific zavod entity."""
        query = (
            select(MaterialRequest)
            .options(
                selectinload(MaterialRequest.order).selectinload(Order.region),
                selectinload(MaterialRequest.usta),
            )
            .where(
                MaterialRequest.status == MaterialRequestStatus.PRICED,
                MaterialRequest.assigned_zavod_id == zavod_id,
            )
            .order_by(MaterialRequest.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_active(self) -> List[MaterialRequest]:
        result = await self.session.execute(
            select(MaterialRequest)
            .options(selectinload(MaterialRequest.order), selectinload(MaterialRequest.usta))
            .where(MaterialRequest.status != MaterialRequestStatus.DELIVERED)
            .order_by(MaterialRequest.created_at.asc())
        )
        return list(result.scalars().all())

    async def price(
        self,
        req_id: int,
        zavod_id: int,
        material_price: Decimal,
        delivery_price: Decimal,
        extra_cost: Optional[Decimal] = None,
    ) -> Optional[MaterialRequest]:
        result = await self.session.execute(
            select(MaterialRequest).where(MaterialRequest.id == req_id)
        )
        req = result.scalar_one_or_none()
        if not req or req.status != MaterialRequestStatus.PENDING:
            return None
        req.zavod_id = zavod_id
        req.material_price = material_price
        req.delivery_price = delivery_price
        req.extra_cost = extra_cost or Decimal("0")
        req.status = MaterialRequestStatus.PRICED
        await self.session.flush()
        return req

    async def approve(self, req_id: int) -> Optional[MaterialRequest]:
        """Admin approves material request, forwarding it to zavod."""
        result = await self.session.execute(
            select(MaterialRequest)
            .options(
                selectinload(MaterialRequest.order).selectinload(Order.region),
                selectinload(MaterialRequest.usta).selectinload(User.region),
            )
            .where(MaterialRequest.id == req_id)
        )
        req = result.scalar_one_or_none()
        if not req or req.status != MaterialRequestStatus.ADMIN_PENDING:
            return None
        req.status = MaterialRequestStatus.PENDING
        await self.session.flush()
        return req

    async def reject(self, req_id: int) -> Optional[MaterialRequest]:
        """Admin rejects material request."""
        result = await self.session.execute(
            select(MaterialRequest)
            .options(selectinload(MaterialRequest.usta))
            .where(MaterialRequest.id == req_id)
        )
        req = result.scalar_one_or_none()
        if not req or req.status != MaterialRequestStatus.ADMIN_PENDING:
            return None
        await self.session.delete(req)
        await self.session.flush()
        return req

    async def deliver(self, req_id: int) -> Optional[MaterialRequest]:
        result = await self.session.execute(
            select(MaterialRequest).where(MaterialRequest.id == req_id)
        )
        req = result.scalar_one_or_none()
        if not req or req.status != MaterialRequestStatus.PRICED:
            return None
        req.status = MaterialRequestStatus.DELIVERED
        await self.session.flush()
        return req
